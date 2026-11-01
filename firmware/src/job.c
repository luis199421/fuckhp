// Job queue and executor.
//
// Frames arrive in comm_task(). Status/param/abort requests are answered right
// away; everything that moves paper, carriage or ink is queued as an "op" and
// executed in order by job_run(). Long operations call service() while they
// wait, so USB keeps flowing (and STATUS/ABORT keep working) at all times.
#include "job.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "comm.h"
#include "compose.h"
#include "config.h"
#include "fj_proto.h"
#include "hardware/gpio.h"
#include "hardware/watchdog.h"
#include "head.h"
#include "motion.h"
#include "params.h"
#include "pico/bootrom.h"
#include "pico/time.h"
#include "ring.h"
#include "sensors.h"

typedef struct {
    uint8_t type, seq;
    int32_t a, b;
    fj_swath_begin_t sw;
    uint32_t plane_len[FJ_MAX_PLANES];
    uint32_t start;        // ring position of swath data
    bool ready;            // swath: all data received
} op_t;

static uint8_t ring_mem[RING_BYTES];
static fj_ring_t ring;
static op_t queue[OP_QUEUE_LEN];
static volatile uint32_t q_head, q_tail;     // q_head = next to execute
static op_t *rx_swath;                        // swath currently receiving data
static uint32_t rx_got;
static uint32_t ring_gen;                     // bumped whenever the queue is flushed

static uint8_t state = FJ_ST_IDLE, last_event;
static uint16_t last_error, pages_done;
static bool job_active, job_failed, roll_mode, homed, abort_req;
static int32_t paper_y_um, page_length_um;
static int job_planes = 1;
static int job_inkset = FJ_INK_K;
static bool tail_seen;                        // sheet: trailing edge has passed the sensor
static int32_t tail_y_um;
static uint32_t idle_since_ms;
static fj_pass_t pass;

static uint32_t now_ms(void) { return to_ms_since_boot(get_absolute_time()); }
static uint32_t q_len(void) { return q_tail - q_head; }
static op_t *q_at(uint32_t i) { return &queue[i % OP_QUEUE_LEN]; }

static void event(uint8_t code, uint16_t arg, int32_t value) {
    last_event = code;
    comm_event(code, arg, value);
}

// ------------------------------------------------------------------ frame intake
static bool is_queued_type(uint8_t t) {
    switch (t) {
    case FJ_JOB_BEGIN: case FJ_PAGE_BEGIN: case FJ_SWATH_BEGIN: case FJ_PAGE_END: case FJ_JOB_END:
    case FJ_FEED: case FJ_HOME: case FJ_PARK: case FJ_SPIT: case FJ_MOTORS_OFF: case FJ_MOVE_X:
    case FJ_NOZZLE_FIRE:
        return true;
    default:
        return false;
    }
}

bool job_accept(uint8_t type, uint32_t len) {
    if (type == FJ_SWATH_DATA) return job_failed || fj_ring_free(&ring) >= len;
    if (is_queued_type(type)) return q_len() < OP_QUEUE_LEN;
    return true;
}

static void send_status(void) {
    fj_status_t s = {0};
    s.state = state;
    s.flags = (homed ? FJ_FL_HOMED : 0) | (sensors_paper() ? FJ_FL_PAPER : 0) |
              FJ_FL_HEAD | (head_powered() ? FJ_FL_HEAD_POWER : 0) |
              (motion_enabled() ? FJ_FL_MOTORS : 0) | (job_active ? FJ_FL_JOB : 0) |
              (state == FJ_ST_WAIT_PAPER ? FJ_FL_WAIT_PAPER : 0) |
              (state == FJ_ST_WAIT_BUTTON ? FJ_FL_WAIT_BUTTON : 0);
    s.error = last_error;
    s.tsr = (uint16_t)PRM(CARTRIDGES);       // (field reused: cartridges fitted)
    s.vhd_mv = sensors_vhd_mv();
    s.ring_free = fj_ring_free(&ring);
    s.queue_len = (uint8_t)q_len();
    s.last_event = last_event;
    s.pages = pages_done;
    s.paper_y_um = paper_y_um;
    s.x_um = (int32_t)motion_pos_um(AXIS_X);
    comm_send(FJ_STATUS, &s, sizeof s);
}

static void send_info(void) {
    fj_info_t i = {0};
    i.proto = FJ_PROTO_VERSION;
    i.fw = FJ_FW_VERSION;
    strncpy(i.model, MODEL_NAME, sizeof i.model);
    i.ring_bytes = RING_BYTES;
    i.dpi = FJ_DPI;
    i.rows = FJ_ROWS_K;
    i.max_cols = (uint16_t)PRM(MAX_COLS);
    i.max_payload = FJ_MAX_PAYLOAD;
    comm_send(FJ_INFO, &i, sizeof i);
}

static void flush_queue(void) {
    ring_gen++;
    q_head = q_tail;
    rx_swath = NULL;
    fj_ring_reset(&ring);
}

void job_handle_frame(const fj_frame_t *f) {
    const uint8_t *p = f->payload;
    switch (f->type) {
    case FJ_HELLO: send_info(); return;
    case FJ_GET_STATUS: send_status(); return;
    case FJ_PARAM_GET: {
        if (f->len < 2) { comm_ack(f->seq, f->type, FJ_E_BAD_ARG); return; }
        uint16_t id = p[0] | p[1] << 8;
        int i = params_index(id);
        if (i < 0) { comm_ack(f->seq, f->type, FJ_E_UNKNOWN_PARAM); return; }
        fj_param_t r = {id, 0, g_param[i]};
        comm_send(FJ_PARAM, &r, sizeof r);
        return;
    }
    case FJ_PARAM_SET: {
        fj_param_t r;
        if (f->len < sizeof r) { comm_ack(f->seq, f->type, FJ_E_BAD_ARG); return; }
        memcpy(&r, p, sizeof r);
        bool busy = job_active || q_len() || head_busy();
        int code = busy ? FJ_E_BUSY : params_set(r.id, r.value);
        if (code == FJ_OK) { motion_configure(); head_configure(job_inkset); }
        comm_ack(f->seq, f->type, code);
        return;
    }
    case FJ_PARAM_SAVE:
        comm_ack(f->seq, f->type, job_active || q_len() || head_busy() ? FJ_E_BUSY :
                 params_save() ? FJ_OK : FJ_E_FLASH);
        return;
    case FJ_PARAM_DEFAULTS:
        if (job_active || q_len() || head_busy()) { comm_ack(f->seq, f->type, FJ_E_BUSY); return; }
        params_defaults(); motion_configure(); head_configure(job_inkset);
        comm_ack(f->seq, f->type, FJ_OK);
        return;
    case FJ_ABORT:
        abort_req = true;
        head_abort();
        flush_queue();
        job_failed = false;
        comm_ack(f->seq, f->type, FJ_OK);
        return;
    case FJ_BOOTSEL:
        comm_ack(f->seq, f->type, FJ_OK);
        head_power(false);
        motion_enable(false);
        sleep_ms(100);
        reset_usb_boot(0, 0);
        return;
    case FJ_SWATH_DATA:
        if (job_failed || !rx_swath) return;              // silently dropped
        if (rx_got + f->len > rx_swath->sw.data_len) { rx_swath = NULL; return; }
        fj_ring_write(&ring, p, f->len);
        rx_got += f->len;
        if (rx_got == rx_swath->sw.data_len) { rx_swath->ready = true; rx_swath = NULL; }
        return;
    default:
        break;
    }
    if (!is_queued_type(f->type)) { comm_ack(f->seq, f->type, FJ_E_UNKNOWN_CMD); return; }

    // ---- queued operations
    if (job_failed && f->type != FJ_JOB_BEGIN) { comm_ack(f->seq, f->type, FJ_E_ABORTED); return; }
    if (job_failed) { job_failed = false; }
    if (rx_swath) { comm_ack(f->seq, f->type, FJ_E_FRAME); return; }   // previous swath incomplete
    op_t *o = q_at(q_tail);
    memset(o, 0, sizeof *o);
    o->type = f->type;
    o->seq = f->seq;
    o->ready = true;
    memcpy(&o->a, p, f->len < 4 ? f->len : 4);
    if (f->len >= 8) memcpy(&o->b, p + 4, 4);
    if (f->type == FJ_JOB_BEGIN) job_planes = f->len > 1 && p[1] ? p[1] : 1;
    if (f->type == FJ_SWATH_BEGIN) {
        if (f->len < sizeof o->sw) { comm_ack(f->seq, f->type, FJ_E_BAD_ARG); return; }
        memcpy(&o->sw, p, sizeof o->sw);
        o->plane_len[0] = o->sw.data_len;
        if (job_planes > 1) {      // per-plane lengths follow the fixed header
            if (f->len < sizeof o->sw + 4u * job_planes) { comm_ack(f->seq, f->type, FJ_E_BAD_ARG); return; }
            memcpy(o->plane_len, p + sizeof o->sw, 4u * job_planes);
            uint32_t sum = 0;
            for (int i = 0; i < job_planes; i++) sum += o->plane_len[i];
            if (sum != o->sw.data_len) { comm_ack(f->seq, f->type, FJ_E_BAD_ARG); return; }
        }
        if (o->sw.data_len > RING_BYTES) { comm_ack(f->seq, f->type, FJ_E_SWATH_TOO_BIG); return; }
        if (o->sw.ncols == 0 || o->sw.x0 < 0 || o->sw.x0 + o->sw.ncols > PRM(MAX_COLS)) {
            comm_ack(f->seq, f->type, FJ_E_RANGE); return;
        }
        o->start = ring.head;
        o->ready = o->sw.data_len == 0;
        if (!o->ready) { rx_swath = o; rx_got = 0; }
    }
    q_tail++;
    comm_ack(f->seq, f->type, FJ_OK);
}

// ------------------------------------------------------------------ executor helpers
static void service(void) {
    comm_task();
    sensors_task();
    watchdog_update();
}

static int wait_motion(int axis) {
    while (motion_busy(axis)) {
        service();
        if (abort_req) { motion_stop(); return FJ_E_ABORTED; }
    }
    return FJ_OK;
}

static int move_x(float um, float speed) {
    if (um < 0 || um > PRM(X_TRAVEL_UM)) return FJ_E_RANGE;
    motion_move(AXIS_X, um, speed, PRM(X_ACCEL_MM_S2), STOP_NONE);
    return wait_motion(AXIS_X);
}

static int feed_to(float um, int stop_on) {
    motion_move(AXIS_Y, um, PRM(Y_SPEED_MM_S), PRM(Y_ACCEL_MM_S2), stop_on);
    return wait_motion(AXIS_Y);
}

static int feed_by(float um) { return feed_to(motion_pos_um(AXIS_Y) + um, STOP_NONE); }

static int home(void) {
    motion_enable(true);
    homed = false;
    if (!gpio_get(PIN_X_HOME_N)) {   // already on the switch: move off it first
        motion_set_pos_um(AXIS_X, 0);
        motion_move(AXIS_X, 15000, PRM(HOME_SPEED_MM_S), PRM(X_ACCEL_MM_S2), STOP_NONE);
        int e = wait_motion(AXIS_X);
        if (e) return e;
    }
    motion_set_pos_um(AXIS_X, PRM(X_TRAVEL_UM) + 30000.0f);
    motion_move(AXIS_X, 0, PRM(HOME_SPEED_MM_S), PRM(X_ACCEL_MM_S2), STOP_HOME_PRESSED);
    int e = wait_motion(AXIS_X);
    if (e) return e;
    if (!motion_stopped_by_sensor(AXIS_X)) return FJ_E_HOME_FAILED;
    motion_set_pos_um(AXIS_X, 0);
    homed = true;
    return move_x(PRM(HOME_BACKOFF_UM), PRM(HOME_SPEED_MM_S));
}

static int park(void) {
    if (!homed) return home();
    return move_x(PRM(HOME_BACKOFF_UM), PRM(X_TRAVEL_SPEED_MM_S));   // cap engages here
}

static bool cart_fitted(int cart) { return PRM(CARTRIDGES) & (1 << cart); }

// cart: -1 = every fitted cartridge, else 0 black / 1 colour. Each cartridge in turn is
// brought over the spittoon (the colour cartridge sits color_x + cmy_pitch to the right).
static int spit(int cart, uint32_t count) {
    if (!homed) { int e = home(); if (e) return e; }
    if (!head_powered()) return FJ_E_NO_VHD;
    for (int c = 0; c < 2; c++) {
        if (!cart_fitted(c) || (cart >= 0 && cart != c)) continue;
        float x = PRM(SPIT_X_UM) - (c ? (float)(PRM(COLOR_X_UM) + PRM(CMY_PITCH_UM)) : 0.0f);
        int e = move_x(x < 0 ? 0 : x, PRM(X_TRAVEL_SPEED_MM_S));
        if (e) return e;
        head_start_spit(c, count, 500);
        while (head_busy()) { service(); if (abort_req) head_abort(); }
        if ((e = head_result())) return e;
    }
    return FJ_OK;
}

static int power_up_head(void) {
    head_power(true);
    absolute_time_t until = make_timeout_time_ms(300);
    while (!time_reached(until)) service();
    if (sensors_vhd_mv() < PRM(VHD_MIN_MV)) { head_power(false); return FJ_E_NO_VHD; }
    return FJ_OK;
}

// Wait for the user to push a sheet in until it rests against the feed roller (the paper
// lever, just before the roller, reports it), then feed its edge to the nozzles.
static int load_sheet(void) {
    tail_seen = false;
    event(FJ_EV_PAPER_NEEDED, 0, 0);
    state = FJ_ST_WAIT_PAPER;
    uint32_t since = 0;
    for (;;) {                                  // paper present steadily for 0.8 s, or button
        service();
        if (abort_req) return FJ_E_ABORTED;
        if (!sensors_paper()) since = 0;
        else if (!since) since = now_ms();
        if ((since && now_ms() - since > 800) || (sensors_paper() && sensors_button_pressed())) break;
    }
    state = FJ_ST_PRINTING;
    int e = feed_by(PRM(SENSOR_TO_NOZZLE_UM));
    if (e) return e;
    paper_y_um = 0;
    event(FJ_EV_PAPER_LOADED, 0, 0);
    return FJ_OK;
}

static int eject_sheet(void) {
    if (sensors_paper()) {
        int e = feed_to(motion_pos_um(AXIS_Y) + 500000.0f, STOP_PAPER_ABSENT);
        if (e) return e;
        if (!motion_stopped_by_sensor(AXIS_Y)) return FJ_E_PAPER_JAM;
    }
    return feed_by(PRM(EJECT_UM));
}

static int do_swath(op_t *o) {
    uint32_t gen = ring_gen;
    while (!o->ready) {            // data still streaming in
        service();
        if (abort_req) return FJ_E_ABORTED;
    }
    const fj_swath_begin_t *s = &o->sw;
    if (s->y_um < paper_y_um) return FJ_E_BACKFEED;
    if (!head_powered()) return FJ_E_NO_VHD;
    int e;
    if (s->y_um > paper_y_um) {
        // single feed roller: once the sheet's tail has left the roller it no longer moves
        if (!roll_mode && tail_seen && s->y_um > tail_y_um + PRM(SHEET_TAIL_UM)) return FJ_E_SHEET_END;
        int32_t before = paper_y_um;
        e = feed_by((float)(s->y_um - paper_y_um));
        if (e) return e;
        paper_y_um = s->y_um;
        if (!roll_mode && !tail_seen && !sensors_paper()) { tail_seen = true; tail_y_um = before; }
    }
    const fj_tables_t *t = head_tables();
    uint32_t starts[FJ_MAX_PLANES], acc = o->start;
    for (int h = 0; h < t->planes; h++) { starts[h] = acc; acc += o->plane_len[h]; }
    fj_pass_setup(&pass, t, &ring, starts, o->plane_len, s->flags & FJ_SWATH_PACKBITS,
                  s->x0, s->ncols, s->dir);
    // never go faster than the head can fire a full column
    float speed = PRM(X_SPEED_MM_S);
    float vmax = FJ_UM_PER_COL / head_column_time_us() * 1000.0f * 0.85f;
    if (speed > vmax) speed = vmax;
    float bidir = s->dir ? PRM(BIDIR_OFFSET_UM) : 0;
    float first = PRM(COL0_X_UM) + fj_pass_ref_col(&pass, 0) * FJ_UM_PER_COL + bidir;
    float last = PRM(COL0_X_UM) + fj_pass_ref_col(&pass, pass.steps - 1) * FJ_UM_PER_COL + bidir;
    float run = motion_accel_distance_um(speed, PRM(X_ACCEL_MM_S2)) + 1500.0f;
    float sgn = s->dir ? -1.0f : 1.0f;
    float from = first - sgn * run, to = last + sgn * run;
    if (from < 0 || to < 0 || from > PRM(X_TRAVEL_UM) || to > PRM(X_TRAVEL_UM)) return FJ_E_RANGE;
    e = move_x(from, PRM(X_TRAVEL_SPEED_MM_S));
    if (e) return e;
    head_start_pass(&pass);
    motion_arm_triggers(first, sgn * FJ_UM_PER_COL, pass.steps);
    motion_move(AXIS_X, to, speed, PRM(X_ACCEL_MM_S2), STOP_NONE);
    e = wait_motion(AXIS_X);
    motion_disarm_triggers();
    if (e) head_abort();
    while (head_busy()) service();
    if (gen == ring_gen) fj_ring_release_to(&ring, o->start + s->data_len);
    if (e) return e;
    return head_result();
}

static int exec(op_t *o) {
    switch (o->type) {
    case FJ_JOB_BEGIN: {
        int planes = (o->a >> 8 & 0xFF) ? (o->a >> 8 & 0xFF) : 1;
        int inkset = o->a >> 16 & 0xFF;
        if (inkset > FJ_INK_KCMY || planes != fj_inkset_planes(inkset)) return FJ_E_BAD_ARG;
        // e.g. a colour job on a printer with only the black cartridge fitted
        if ((fj_inkset_uses(inkset, HP302_CART_BLACK) && !cart_fitted(HP302_CART_BLACK)) ||
            (fj_inkset_uses(inkset, HP302_CART_COLOR) && !cart_fitted(HP302_CART_COLOR))) return FJ_E_INKSET;
        job_inkset = inkset;
        head_configure(inkset);
        job_active = true;
        roll_mode = o->a & FJ_JOB_ROLL;
        pages_done = 0;
        state = FJ_ST_BUSY;
        motion_enable(true);
        int e = homed ? FJ_OK : home();
        if (!e) e = power_up_head();
        return e;
    }
    case FJ_PAGE_BEGIN: {
        if (!job_active) return FJ_E_NO_JOB;
        state = FJ_ST_PRINTING;
        page_length_um = o->a;
        int e = PRM(SPIT_COUNT) ? spit(-1, PRM(SPIT_COUNT)) : FJ_OK;
        if (e) return e;
        if (roll_mode) { paper_y_um = 0; return FJ_OK; }
        return load_sheet();
    }
    case FJ_SWATH_BEGIN:
        if (!job_active) return FJ_E_NO_JOB;
        state = FJ_ST_PRINTING;
        return do_swath(o);
    case FJ_PAGE_END: {
        int e = park();
        if (e) return e;
        if (roll_mode) {
            float to_cut = (float)page_length_um - paper_y_um + PRM(CUTTER_UM);
            if (to_cut > 0 && (e = feed_by(to_cut))) return e;
            if (o->a & FJ_PAGE_END_CUT_PAUSE) {
                event(FJ_EV_CUT_NOW, 0, 0);
                state = FJ_ST_WAIT_BUTTON;
                while (!sensors_button_pressed()) { service(); if (abort_req) return FJ_E_ABORTED; }
                state = FJ_ST_PRINTING;
            }
            if ((e = feed_by(-(float)PRM(CUTTER_UM)))) return e;   // roll: back up to the nozzles
        } else if ((e = eject_sheet())) {
            return e;
        }
        paper_y_um = 0;
        pages_done++;
        event(FJ_EV_PAGE_DONE, 0, pages_done);
        return FJ_OK;
    }
    case FJ_JOB_END:
        park();
        head_power(false);
        job_active = false;
        state = FJ_ST_IDLE;
        event(FJ_EV_JOB_DONE, 0, pages_done);
        return FJ_OK;
    case FJ_FEED:
        if (o->a < 0 && !roll_mode) return FJ_E_BACKFEED;
        motion_enable(true);
        return feed_by((float)o->a);
    case FJ_HOME: return home();
    case FJ_PARK: return park();
    case FJ_MOTORS_OFF: motion_enable(false); homed = false; return FJ_OK;
    case FJ_MOVE_X:
        if (!homed) { int e = home(); if (e) return e; }
        return move_x((float)o->a, PRM(X_TRAVEL_SPEED_MM_S));
    case FJ_SPIT: case FJ_NOZZLE_FIRE: {
        bool was = head_powered();
        int e = was ? FJ_OK : power_up_head();
        if (e) return e;
        int cart = -1;
        uint32_t count = o->a & 0xFFFF;
        if (o->type == FJ_NOZZLE_FIRE) {   // u16 cartridge (0 black, 1 colour, 0xFFFF both), u16 count
            cart = (o->a & 0xFFFF) == 0xFFFF ? -1 : (o->a & 1);
            count = (uint32_t)o->a >> 16;
        }
        e = spit(cart, count ? count : 100);
        if (!was && !job_active) head_power(false);
        if (!e) e = park();
        return e;
    }
    }
    return FJ_E_UNKNOWN_CMD;
}

static void fail(int code) {
    last_error = (uint16_t)code;
    motion_stop();
    head_abort();
    while (head_busy()) tight_loop_contents();
    flush_queue();
    if (code == FJ_E_ABORTED) {
        event(FJ_EV_ABORTED, code, 0);
        job_failed = false;
    } else {
        event(FJ_EV_ERROR, code, 0);
        job_failed = job_active;     // drop the rest of the job's frames
    }
    abort_req = false;
    park();
    head_power(false);
    job_active = false;
    state = code == FJ_E_ABORTED ? FJ_ST_IDLE : FJ_ST_ERROR;
}

// ------------------------------------------------------------------ public
void job_init(void) {
    fj_ring_init(&ring, ring_mem, RING_BYTES);
    idle_since_ms = now_ms();
}

void job_run(void) {
    for (;;) {
        service();
        led_set_mode(state == FJ_ST_ERROR ? 2 : state == FJ_ST_IDLE ? 1 : 3);
        if (abort_req) fail(FJ_E_ABORTED);
        if (q_len()) {
            op_t *o = q_at(q_head);
            if (o->type == FJ_SWATH_BEGIN && !o->ready) {
                if (job_active && now_ms() - comm_last_rx_ms() > (uint32_t)PRM(JOB_TIMEOUT_S) * 1000u)
                    fail(FJ_E_ABORTED);
                continue;
            }
            uint32_t idx = q_head;
            int e = exec(o);
            if (q_head == idx) q_head++;     // (an ABORT may have flushed the queue meanwhile)
            if (e) fail(e);
            idle_since_ms = now_ms();
            continue;
        }
        // idle housekeeping
        if (job_active && now_ms() - comm_last_rx_ms() > (uint32_t)PRM(JOB_TIMEOUT_S) * 1000u)
            fail(FJ_E_ABORTED);
        if (!job_active && motion_enabled() && PRM(IDLE_MOTOR_OFF_S) &&
            now_ms() - idle_since_ms > (uint32_t)PRM(IDLE_MOTOR_OFF_S) * 1000u) {
            motion_enable(false);
            homed = false;
        }
        if (!job_active && sensors_button_pressed()) {      // button: eject a sheet / clean
            motion_enable(true);
            if (sensors_paper()) eject_sheet();
            else if (power_up_head() == FJ_OK) { spit(-1, 300); park(); head_power(false); }
            idle_since_ms = now_ms();
        }
        if (state == FJ_ST_ERROR && !job_active && q_len() == 0 && sensors_button_held(1500))
            state = FJ_ST_IDLE;
    }
}
