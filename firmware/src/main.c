// FreeJet FJ-1 firmware entry point (Raspberry Pi Pico 2 / RP2350).
#include <stdio.h>
#include "comm.h"
#include "config.h"
#include "hardware/watchdog.h"
#include "head.h"
#include "job.h"
#include "motion.h"
#include "params.h"
#include "pico/stdlib.h"
#include "sensors.h"

int main(void) {
    // the head supply switch must be off before anything else happens
    gpio_init(PIN_HEAD_PWR);
    gpio_set_dir(PIN_HEAD_PWR, GPIO_OUT);
    gpio_put(PIN_HEAD_PWR, 0);

    stdio_init_all();   // no console: GP0/GP1 drive the TSR multiplexer
    bool stored = params_load();
    sensors_init();
    motion_init();
    head_init();        // also starts core1
    job_init();
    comm_init(job_accept, job_handle_frame);
    printf("FreeJet FJ-1 firmware %d.%d, params %s, watchdog reset: %s\n", 0, 1,
           stored ? "from flash" : "defaults", watchdog_caused_reboot() ? "yes" : "no");
    watchdog_enable(2000, true);
    job_run();
}
