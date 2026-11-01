// HP45 printhead driver. Fire timing runs on core1; core0 only starts/monitors jobs.
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "compose.h"

void head_init(void);                 // call on core0; launches core1
void head_power(bool on);
bool head_powered(void);
void head_configure(void);            // re-read pulse/group/nozzle-order params
const fj_tables_t *head_tables(void);

// Start printing a pass. Core1 composes column j and fires it when g_col_target > j.
void head_start_pass(fj_pass_t *p);
// Fire `count` columns of the given nozzle (-1 = all) every period_us, in place.
void head_start_spit(int nozzle, uint32_t count, uint32_t period_us);
bool head_busy(void);
int head_result(void);                // FJ_OK or FJ_E_* of the last job
void head_abort(void);
// Worst-case time (us) to fire one full column with the current settings.
float head_column_time_us(void);
