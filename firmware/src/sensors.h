#pragma once
#include <stdbool.h>
#include <stdint.h>

void sensors_init(void);
void sensors_task(void);          // call often; debounces switches
uint16_t sensors_tsr_raw(void);   // 0..4095
uint16_t sensors_vhd_mv(void);
bool sensors_head_present(void);
bool sensors_paper(void);         // debounced
bool sensors_button_pressed(void);// true once per press (edge)
bool sensors_button_held(uint32_t ms);
void led_set_mode(int mode);      // 0 off, 1 on, 2 slow blink, 3 fast blink
