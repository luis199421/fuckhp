#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "params_table.h"

#define FJ_P_ENUM(id, NAME, def, mn, mx) P_##NAME,
enum { FJ_PARAMS(FJ_P_ENUM) P_COUNT };

extern int32_t g_param[P_COUNT];
#define PRM(NAME) (g_param[P_##NAME])

void params_defaults(void);
int params_index(uint16_t id);             // -1 if unknown
int params_set(uint16_t id, int32_t value); // returns FJ_OK / FJ_E_*
bool params_load(void);                     // from flash; false = defaults used
bool params_save(void);
