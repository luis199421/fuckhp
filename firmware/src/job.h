#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "frame.h"

void job_init(void);
bool job_accept(uint8_t type, uint32_t len);   // back-pressure for comm
void job_handle_frame(const fj_frame_t *f);    // called from comm_task
void job_run(void);                            // main loop: never returns
