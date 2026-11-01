#include "sensors.h"
#include "config.h"
#include "hardware/adc.h"
#include "hardware/gpio.h"
#include "params.h"
#include "pico/time.h"

static bool paper_state, btn_state, btn_edge;
static uint32_t paper_since, btn_since;
static int led_mode;

static uint8_t tsr_sel = 0xFF;

void sensors_init(void) {
    adc_init();
    for (uint p = PIN_TSR_SEL0; p <= PIN_TSR_SEL1; p++) { gpio_init(p); gpio_set_dir(p, GPIO_OUT); gpio_put(p, 0); }
    adc_gpio_init(PIN_ADC_TSR);
    adc_gpio_init(PIN_ADC_VHD);
    gpio_init(PIN_BUTTON_N);
    gpio_pull_up(PIN_BUTTON_N);
    gpio_init(PIN_LED);
    gpio_set_dir(PIN_LED, GPIO_OUT);
#ifdef PICO_DEFAULT_LED_PIN
    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
#endif
}

static uint16_t adc_avg(uint ch) {
    adc_select_input(ch);
    uint32_t s = 0;
    for (int i = 0; i < 16; i++) s += adc_read();
    return (uint16_t)(s / 16);
}

uint16_t sensors_tsr_raw(int head) {
    if (head != tsr_sel) {            // 74HC4051: route that cartridge's TSR to the ADC
        gpio_put(PIN_TSR_SEL0, head & 1);
        gpio_put(PIN_TSR_SEL1, head >> 1 & 1);
        tsr_sel = (uint8_t)head;
        busy_wait_us_32(30);
    }
    return adc_avg(ADC_CH_TSR);
}
uint16_t sensors_vhd_mv(void) { return (uint16_t)(adc_avg(ADC_CH_VHD) * 3300.0f / 4095.0f * VHD_DIVIDER); }

bool sensors_head_present(void) {     // every fitted cartridge must be there
    for (int h = 0; h < PRM(N_HEADS); h++) {
        uint16_t t = sensors_tsr_raw(h);
        if (t < PRM(TSR_MIN) || t > PRM(TSR_MAX)) return false;
    }
    return true;
}

void sensors_task(void) {
    uint32_t now = to_ms_since_boot(get_absolute_time());
    bool p = !gpio_get(PIN_PAPER_N);
    if (p == paper_state) paper_since = now;
    else if (now - paper_since > 30) paper_state = p;
    bool b = !gpio_get(PIN_BUTTON_N);
    if (b != btn_state) {
        if (now - btn_since > 30) { btn_state = b; if (b) btn_edge = true; btn_since = now; }
    } else if (!b) {
        btn_since = now;
    }
    bool on;
    switch (led_mode) {
    case 0: on = false; break;
    case 1: on = true; break;
    case 2: on = (now / 500) & 1; break;
    default: on = (now / 100) & 1; break;
    }
    gpio_put(PIN_LED, on);
#ifdef PICO_DEFAULT_LED_PIN
    gpio_put(PICO_DEFAULT_LED_PIN, on);
#endif
}

bool sensors_paper(void) { return paper_state; }

bool sensors_button_pressed(void) {
    bool e = btn_edge;
    btn_edge = false;
    return e;
}

bool sensors_button_held(uint32_t ms) {
    return btn_state && to_ms_since_boot(get_absolute_time()) - btn_since >= ms;
}

void led_set_mode(int mode) { led_mode = mode; }
