#include "head.h"
#include <string.h>
#include "config.h"
#include "fire.pio.h"
#include "fj_proto.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/pio.h"
#include "motion.h"
#include "params.h"
#include "pico/multicore.h"

enum { CMD_PASS = 1, CMD_SPIT = 2 };

static PIO pio = pio0;
static uint sm;
static fj_tables_t tables;
static uint16_t group_mask[4];
static int groups;
static uint32_t pulse_cycles;

static fj_pass_t *volatile cur_pass;
static volatile int spit_nozzle;
static volatile uint32_t spit_count, spit_period_us;
static volatile bool busy, abort_req;
static volatile int result;

// ---------------------------------------------------------------- address chain
static inline void __not_in_flash_func(pulse_pin)(uint pin) {
    gpio_put(pin, 1);
    busy_wait_at_least_cycles(20);
    gpio_put(pin, 0);
    busy_wait_at_least_cycles(20);
}

// Walk a single '1' through the 22-bit address chain: first=true starts at A1.
static inline void __not_in_flash_func(addr_step)(bool first) {
    gpio_put(PIN_A_SER, first);
    busy_wait_at_least_cycles(10);
    pulse_pin(PIN_A_SRCLK);
    pulse_pin(PIN_A_RCLK);
}

static void __not_in_flash_func(addr_clear)(void) {
    gpio_put(PIN_H_CLR_N, 0);
    busy_wait_at_least_cycles(30);
    pulse_pin(PIN_A_RCLK);
    gpio_put(PIN_H_CLR_N, 1);
}

// ---------------------------------------------------------------- firing
static void __not_in_flash_func(fire_column)(const uint16_t words[HP45_ADDRESSES]) {
    int last = -1;
    for (int a = 0; a < HP45_ADDRESSES; a++) if (words[a]) last = a;
    if (last < 0) return;
    for (int a = 0; a <= last; a++) {
        addr_step(a == 0);
        uint16_t m = words[a];
        if (!m) continue;
        int pushed = 0;
        for (int g = 0; g < groups; g++) {
            uint16_t sub = m & group_mask[g];
            if (!sub) continue;
            pio_sm_put_blocking(pio, sm, (uint32_t)sub << 16 | pulse_cycles);
            pushed++;
        }
        while (pushed--) (void)pio_sm_get_blocking(pio, sm);   // wait until pulses are over
    }
    addr_clear();
}

static void __not_in_flash_func(run_pass)(void) {
    fj_pass_t *p = cur_pass;
    uint16_t words[HP45_ADDRESSES];
    result = FJ_OK;
    if (!fj_pass_compose(p, 0, words)) { result = FJ_E_FRAME; return; }
    for (int32_t j = 0; j < p->steps; ) {
        int32_t t;
        while ((t = (int32_t)g_col_target) <= j) {
            if (abort_req) { result = FJ_E_ABORTED; return; }
        }
        if (t > j + 1) { result = FJ_E_UNDERRUN; return; }   // we fell a column behind
        fire_column(words);
        if (++j < p->steps && !fj_pass_compose(p, j, words)) { result = FJ_E_FRAME; return; }
    }
}

static void __not_in_flash_func(run_spit)(void) {
    uint16_t words[HP45_ADDRESSES];
    fj_words_for_nozzle(&tables, spit_nozzle, words);
    result = FJ_OK;
    for (uint32_t i = 0; i < spit_count && !abort_req; i++) {
        fire_column(words);
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
        addr_clear();
        busy = false;
    }
}

// ---------------------------------------------------------------- core0 API
void head_configure(void) {
    fj_compose_tables(&tables, PRM(NOZZLE0_DOWNSTREAM));
    groups = PRM(PRIM_GROUPS);
    if (groups < 1) groups = 1;
    if (groups > 4) groups = 4;
    for (int g = 0; g < 4; g++) group_mask[g] = 0;
    for (int p = 0; p < HP45_PRIMITIVES; p++) group_mask[p % groups] |= 1u << p;
    int32_t ns = PRM(PULSE_NS);
    if (ns > PULSE_NS_LIMIT) ns = PULSE_NS_LIMIT;
    int32_t c = (int32_t)((int64_t)ns * (PIO_FIRE_HZ / 1000000) / 1000) - 2;
    pulse_cycles = c < 1 ? 1 : (uint32_t)c;
}

const fj_tables_t *head_tables(void) { return &tables; }

void head_init(void) {
    const uint outs[] = {PIN_H_CLR_N, PIN_A_SER, PIN_A_SRCLK, PIN_A_RCLK, PIN_HEAD_PWR};
    for (unsigned i = 0; i < sizeof outs / sizeof outs[0]; i++) {
        gpio_init(outs[i]);
        gpio_set_dir(outs[i], GPIO_OUT);
        gpio_put(outs[i], 0);
    }
    sm = pio_claim_unused_sm(pio, true);
    uint offset = pio_add_program(pio, &fj_fire_program);
    fj_fire_program_init(pio, sm, offset, PIN_P_SER, PIN_P_SRCLK, PIN_P_RCLK,
                         (float)clock_get_hz(clk_sys) / PIO_FIRE_HZ);
    // clear both chains and latch zeros (FIRE is low, so primitives stay disabled anyway)
    gpio_put(PIN_H_CLR_N, 0);
    busy_wait_us_32(1);
    pulse_pin(PIN_A_RCLK);
    pio_sm_exec(pio, sm, pio_encode_set(pio_pins, 1));
    pio_sm_exec(pio, sm, pio_encode_set(pio_pins, 0));
    gpio_put(PIN_H_CLR_N, 1);
    head_configure();
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

void head_start_spit(int nozzle, uint32_t count, uint32_t period_us) {
    spit_nozzle = nozzle;
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
    float shift = 16 * 4 / 30.0f + 0.5f;                    // PIO shift + latch + settle
    float pulse = (pulse_cycles + 3) / 30.0f;               // pulse + overhead
    return HP45_ADDRESSES * (0.6f + groups * (shift + pulse + 0.4f)) + 2.0f;
}
