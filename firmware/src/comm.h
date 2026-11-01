// USB CDC transport: frames in, frames out.
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "frame.h"

typedef bool (*comm_accept_fn)(uint8_t type, uint32_t len);   // back-pressure check
typedef void (*comm_frame_fn)(const fj_frame_t *f);

void comm_init(comm_accept_fn accept, comm_frame_fn handle);
void comm_task(void);
void comm_send(uint8_t type, const void *payload, uint32_t len);
void comm_ack(uint8_t seq, uint8_t type, uint16_t code);
void comm_event(uint8_t code, uint16_t arg, int32_t value);
uint32_t comm_last_rx_ms(void);
bool comm_connected(void);
