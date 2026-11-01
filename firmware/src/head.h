// HP 63/302 cartridge driver. Firing runs on core1 + PIO + DMA; core0 starts/monitors jobs.
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "compose.h"

void head_init(void);                 // call on core0; launches core1
void head_power(bool on);
bool head_powered(void);
void head_configure(int inkset);      // build nozzle tables for an ink set from the params
const fj_tables_t *head_tables(void);

// Start printing a pass. Core1 composes column j and fires it when g_col_target > j.
void head_start_pass(fj_pass_t *p);
// Fire every nozzle of a cartridge (0 black, 1 colour) `count` times, every period_us.
void head_start_spit(int cart, uint32_t count, uint32_t period_us);
bool head_busy(void);
int head_result(void);                // FJ_OK or FJ_E_* of the last job
void head_abort(void);
float head_column_time_us(void);      // worst-case time to fire one column
