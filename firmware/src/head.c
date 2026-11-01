#include "head.h"
#include <string.h>
#include "config.h"
#include "fj_proto.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/gpio.h"
#include "hardware/pio.h"
#include "motion.h"
#include "params.h"
#include "pico/multicore.h"
#include "wave.pio.h"

enum { CMD_PASS = 1, CMD_SPIT = 2 };

static PIO pio = pio0;
static uint sm;
static int dma_ch;
static fj_tables_t tables;
// two buffers: one plays while core1 prepares the next column (black + colour cycle)
static uint16_t wave[2][2 * HP302_CYCLE_SAMPLES + 4] __attribute__((aligned(4)));

static fj_pass_t *volatile cur_pass;
static volatile int spit_cart;
static volatile uint32_t spit_count, spit_period_us;
static volatile bool busy, abort_req;
static volatile int result;

// ---------------------------------------------------------------- waveform playback
static int __not_in_flash_func(build)(uint16_t *buf, const fj_nozdata_t nd) {
    memset(buf, 0, sizeof wave[0]);
    int n = hp302_cycle(buf, HP302_CART_BLACK, nd[0]);
    n += hp302_cycle(buf + n, HP302_CART_COLOR, nd[1]);
    if (n) n += 2;                          // end on idle samples, keep it even
    return n;
}

static void __not_in_flash_func(play)(const uint16_t *buf, int samples) {
    if (!samples) return;
    dma_channel_set_read_addr(dma_ch, buf, false);
    dma_channel_set_trans_count(dma_ch, (uint32_t)samples / 2, true);
}

static void __not_in_flash_func(wait_played)(void) {
    dma_channel_wait_for_finish_blocking(dma_ch);
    while (!pio_sm_is_tx_fifo_empty(pio, sm)) tight_loop_contents();
    busy_wait_us_32(2);                     // last word leaves the shift register
}

static void __not_in_flash_func(run_pass)(void) {
    fj_pass_t *p = cur_pass;
    static fj_nozdata_t nd;
    int cur = 0;
    result = FJ_OK;
    if (!fj_pass_compose(p, 0, nd)) { result = FJ_E_FRAME; return; }
    int n = build(wave[cur], nd);
    for (int32_t j = 0; j < p->steps; ) {
        int32_t t;
        while ((t = (int32_t)g_col_target) <= j) {
            if (abort_req) { result = FJ_E_ABORTED; return; }
        }
        if (t > j + 1) { result = FJ_E_UNDERRUN; return; }   // we fell a column behind
        play(wave[cur], n);
        cur ^= 1;
        if (++j < p->steps) {
            if (!fj_pass_compose(p, j, nd)) { wait_played(); result = FJ_E_FRAME; return; }
            n = build(wave[cur], nd);
        }
        wait_played();
    }
}

static void __not_in_flash_func(run_spit)(void) {
    static fj_nozdata_t nd;
    memset(nd, 0, sizeof nd);
    memcpy(nd[spit_cart], tables.spit[spit_cart], HP302_NOZDATA);
    int n = build(wave[0], nd);
    result = FJ_OK;
    for (uint32_t i = 0; i < spit_count && !abort_req; i++) {
        play(wave[0], n);
        wait_played();
        busy_wait_us_32(spit_period_us);
    }
    if (abort_req) result = FJ_E_ABORTED;
}

static void __not_in_flash_func(core1_main)(void) {
    multicore_lockout_victim_init();     // lets core0 pause us while writing flash
    for (;;) {
        uint32_t cmd = multicore_fifo_pop_blocking();
        if (cmd == CMD_PASS) run_pass();
        else if (cmd == CMD_SPIT) run_spit();
        busy = false;
    }
}

// ---------------------------------------------------------------- core0 API
void head_configure(int inkset) {
    fj_geom_t g = {
        .inkset = inkset,
        .flip = PRM(NOZZLE_FLIP),
        .k_row_gap_cols = (int32_t)(PRM(K_ROW_GAP_UM) / FJ_UM_PER_COL + (PRM(K_ROW_GAP_UM) >= 0 ? 0.5f : -0.5f)),
        .color_x_cols = (int32_t)(PRM(COLOR_X_UM) / FJ_UM_PER_COL + (PRM(COLOR_X_UM) >= 0 ? 0.5f : -0.5f)),
        .cmy_pitch_cols = (int32_t)(PRM(CMY_PITCH_UM) / FJ_UM_PER_COL + (PRM(CMY_PITCH_UM) >= 0 ? 0.5f : -0.5f)),
        .k_dy_rows = PRM(K_DY_ROWS),
    };
    fj_build_tables(&tables, &g);
}

const fj_tables_t *head_tables(void) { return &tables; }

void head_init(void) {
    gpio_init(PIN_HEAD_PWR);
    gpio_set_dir(PIN_HEAD_PWR, GPIO_OUT);
    gpio_put(PIN_HEAD_PWR, 0);
    sm = pio_claim_unused_sm(pio, true);
    uint offset = pio_add_program(pio, &fj_wave_program);
    fj_wave_program_init(pio, sm, offset, PIN_CART0,
                         (float)clock_get_hz(clk_sys) / (2.0f * HP302_SAMPLE_HZ));
    dma_ch = dma_claim_unused_channel(true);
    dma_channel_config c = dma_channel_get_default_config(dma_ch);
    channel_config_set_transfer_data_size(&c, DMA_SIZE_32);
    channel_config_set_read_increment(&c, true);
    channel_config_set_write_increment(&c, false);
    channel_config_set_dreq(&c, pio_get_dreq(pio, sm, true));
    dma_channel_configure(dma_ch, &c, &pio->txf[sm], wave[0], 0, false);
    head_configure(FJ_INK_K);
    multicore_launch_core1(core1_main);
}

void head_power(bool on) { gpio_put(PIN_HEAD_PWR, on); }
bool head_powered(void) { return gpio_get_out_level(PIN_HEAD_PWR); }

void head_start_pass(fj_pass_t *p) {
    cur_pass = p;
    abort_req = false;
    busy = true;
    multicore_fifo_push_blocking(CMD_PASS);
}

void head_start_spit(int cart, uint32_t count, uint32_t period_us) {
    spit_cart = cart ? 1 : 0;
    spit_count = count;
    spit_period_us = period_us;
    abort_req = false;
    busy = true;
    multicore_fifo_push_blocking(CMD_SPIT);
}

bool head_busy(void) { return busy; }
int head_result(void) { return result; }
void head_abort(void) { abort_req = true; }

float head_column_time_us(void) {
    // black cycle + colour cycle at 3.33 MHz, plus composing/DMA restart overhead
    return 2.0f * HP302_CYCLE_SAMPLES / (HP302_SAMPLE_HZ / 1e6f) + 15.0f;
}
