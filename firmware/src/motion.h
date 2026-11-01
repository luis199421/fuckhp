// Two-axis stepper control from a fixed-rate interrupt (core0).
// Only one axis moves at a time; X moves can fire column triggers for the printhead.
#pragma once
#include <stdbool.h>
#include <stdint.h>

enum { AXIS_X = 0, AXIS_Y = 1 };
enum { STOP_NONE = 0, STOP_HOME_PRESSED, STOP_PAPER_PRESENT, STOP_PAPER_ABSENT };

extern volatile uint32_t g_col_target;   // number of column triggers passed (read by core1)

void motion_init(void);
void motion_enable(bool on);
bool motion_enabled(void);
void motion_configure(void);             // re-read steps/mm and direction params
// Start a move to an absolute position (um). Returns immediately.
void motion_move(int axis, float target_um, float speed_mm_s, float accel_mm_s2, int stop_on);
bool motion_busy(int axis);
bool motion_stopped_by_sensor(int axis); // last move ended because its stop condition fired
void motion_stop(void);                  // immediate stop of everything
float motion_pos_um(int axis);
void motion_set_pos_um(int axis, float um);
// Fire column triggers while X passes first_um, first_um + step_um, ... (count of them).
void motion_arm_triggers(float first_um, float step_um, int32_t count);
void motion_disarm_triggers(void);
float motion_accel_distance_um(float speed_mm_s, float accel_mm_s2);
