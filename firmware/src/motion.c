#include "motion.h"
#include <math.h>
#include "config.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/irq.h"
#include "hardware/pwm.h"
#include "hardware/sync.h"
#include "params.h"

typedef struct {
    uint step_pin, dir_pin;
    volatile bool busy, hit;
    volatile int stop_on;
    float pos;            // commanded position, steps (continuous)
    int32_t steps;        // steps actually emitted
    float target;         // steps (integer valued)
    float v, vmax, a;     // steps/tick, steps/tick^2
    int dir;              // +1 / -1
    bool step_high;
    float steps_per_um;
    bool invert;
} axis_t;

static axis_t ax[2];
static uint tick_slice;
volatile uint32_t g_col_target;
static volatile int32_t trig_count;
static float trig_next, trig_step;

static inline bool sensor_hit(int stop_on) {
    switch (stop_on) {
    case STOP_HOME_PRESSED:  return !gpio_get(PIN_X_HOME_N);
    case STOP_PAPER_PRESENT: return !gpio_get(PIN_PAPER_N);
    case STOP_PAPER_ABSENT:  return gpio_get(PIN_PAPER_N);
    default: return false;
    }
}

static void __not_in_flash_func(axis_tick)(axis_t *a, bool is_x) {
    bool cleared = false;
    if (a->step_high) { gpio_put(a->step_pin, 0); a->step_high = false; cleared = true; }
    if (!a->busy) return;
    if (a->stop_on && sensor_hit(a->stop_on)) {
        a->hit = true;
        a->target = a->pos = (float)a->steps;
        a->v = 0;
        a->busy = false;
        return;
    }
    float rem = (a->target - a->pos) * (float)a->dir;
    if (rem > 0) {
        if (a->v * a->v >= 2.0f * a->a * rem) a->v -= a->a;
        else if (a->v < a->vmax) a->v += a->a;
        if (a->v > a->vmax) a->v = a->vmax;
        if (a->v < a->a) a->v = a->a;            // never stall short of the target
        float adv = a->v < rem ? a->v : rem;
        a->pos += (float)a->dir * adv;
        if (is_x && trig_count) {
            while (trig_count && (a->pos - trig_next) * trig_step >= 0) {
                g_col_target++;
                trig_next += trig_step;
                trig_count--;
            }
        }
    }
    int32_t want = (int32_t)floorf(a->pos + 0.5f);
    if (want != a->steps && !cleared) {
        gpio_put(a->step_pin, 1);
        a->step_high = true;
        a->steps += want > a->steps ? 1 : -1;
    }
    if (rem <= 0 && a->steps == (int32_t)a->target && !a->step_high) {
        a->busy = false;
        a->v = 0;
    }
}

static void __not_in_flash_func(tick_isr)(void) {
    pwm_clear_irq(tick_slice);
    axis_tick(&ax[AXIS_X], true);
    axis_tick(&ax[AXIS_Y], false);
}

void motion_configure(void) {
    ax[AXIS_X].steps_per_um = PRM(X_STEPS_PER_M) / 1e6f;
    ax[AXIS_Y].steps_per_um = PRM(Y_STEPS_PER_M) / 1e6f;
    ax[AXIS_X].invert = PRM(X_DIR_INVERT);
    ax[AXIS_Y].invert = PRM(Y_DIR_INVERT);
}

void motion_init(void) {
    const uint outs[] = {PIN_X_STEP, PIN_X_DIR, PIN_Y_STEP, PIN_Y_DIR, PIN_MOTOR_EN_N};
    for (unsigned i = 0; i < sizeof outs / sizeof outs[0]; i++) {
        gpio_init(outs[i]);
        gpio_set_dir(outs[i], GPIO_OUT);
        gpio_put(outs[i], outs[i] == PIN_MOTOR_EN_N);   // motors disabled
    }
    const uint ins[] = {PIN_X_HOME_N, PIN_PAPER_N};
    for (unsigned i = 0; i < 2; i++) { gpio_init(ins[i]); gpio_pull_up(ins[i]); }
    ax[AXIS_X].step_pin = PIN_X_STEP; ax[AXIS_X].dir_pin = PIN_X_DIR;
    ax[AXIS_Y].step_pin = PIN_Y_STEP; ax[AXIS_Y].dir_pin = PIN_Y_DIR;
    motion_configure();

    // a PWM slice whose pins are not routed to PWM serves as a precise tick source
    tick_slice = pwm_gpio_to_slice_num(PIN_A_SRCLK);
    pwm_config c = pwm_get_default_config();
    pwm_config_set_wrap(&c, clock_get_hz(clk_sys) / MOTION_TICK_HZ - 1);
    pwm_init(tick_slice, &c, false);
    pwm_clear_irq(tick_slice);
    pwm_set_irq_enabled(tick_slice, true);
    irq_set_exclusive_handler(PWM_DEFAULT_IRQ_NUM(), tick_isr);
    irq_set_priority(PWM_DEFAULT_IRQ_NUM(), 0);         // highest
    irq_set_enabled(PWM_DEFAULT_IRQ_NUM(), true);
    pwm_set_enabled(tick_slice, true);
}

void motion_enable(bool on) { gpio_put(PIN_MOTOR_EN_N, !on); }
bool motion_enabled(void) { return !gpio_get(PIN_MOTOR_EN_N); }

void motion_move(int i, float target_um, float speed_mm_s, float accel_mm_s2, int stop_on) {
    axis_t *a = &ax[i];
    while (a->busy) tight_loop_contents();
    float spu = a->steps_per_um;
    float target = roundf(target_um * spu);
    float vmax = speed_mm_s * 1000.0f * spu / MOTION_TICK_HZ;
    if (vmax > 0.5f) vmax = 0.5f;                       // one step per two ticks max
    float acc = accel_mm_s2 * 1000.0f * spu / ((float)MOTION_TICK_HZ * MOTION_TICK_HZ);
    if (acc < 1e-7f) acc = 1e-7f;
    uint32_t s = save_and_disable_interrupts();
    a->target = target;
    a->dir = target >= a->pos ? 1 : -1;
    gpio_put(a->dir_pin, (a->dir > 0) ^ a->invert);
    a->vmax = vmax;
    a->a = acc;
    a->v = 0;
    a->stop_on = stop_on;
    a->hit = false;
    a->busy = target != a->pos || a->steps != (int32_t)target;
    if (stop_on && sensor_hit(stop_on)) { a->hit = true; a->busy = false; }
    restore_interrupts(s);
}

bool motion_busy(int i) { return ax[i].busy; }
bool motion_stopped_by_sensor(int i) { return ax[i].hit; }

void motion_stop(void) {
    uint32_t s = save_and_disable_interrupts();
    for (int i = 0; i < 2; i++) {
        ax[i].pos = ax[i].target = (float)ax[i].steps;
        ax[i].busy = false;
        ax[i].v = 0;
    }
    trig_count = 0;
    restore_interrupts(s);
}

float motion_pos_um(int i) { return ax[i].steps / ax[i].steps_per_um; }

void motion_set_pos_um(int i, float um) {
    uint32_t s = save_and_disable_interrupts();
    ax[i].pos = ax[i].target = roundf(um * ax[i].steps_per_um);
    ax[i].steps = (int32_t)ax[i].pos;
    restore_interrupts(s);
}

void motion_arm_triggers(float first_um, float step_um, int32_t count) {
    uint32_t s = save_and_disable_interrupts();
    g_col_target = 0;
    trig_next = first_um * ax[AXIS_X].steps_per_um;
    trig_step = step_um * ax[AXIS_X].steps_per_um;
    trig_count = count;
    restore_interrupts(s);
}

void motion_disarm_triggers(void) { trig_count = 0; }

float motion_accel_distance_um(float speed_mm_s, float accel_mm_s2) {
    return speed_mm_s * speed_mm_s / (2.0f * accel_mm_s2) * 1000.0f;
}
