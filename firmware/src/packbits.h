// Streaming PackBits decoder reading straight out of the swath ring.
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "ring.h"

typedef struct {
    const fj_ring_t *ring;
    uint32_t pos, end;   // absolute ring positions
    bool packed;         // false = raw bytes
    uint8_t mode;        // 0 = expect control byte, 1 = literal, 2 = run
    uint16_t count;
    uint8_t value;
} fj_pb_t;

void fj_pb_init(fj_pb_t *c, const fj_ring_t *r, uint32_t start, uint32_t len, bool packed);
// Decode exactly n bytes into out. Returns false if the stream ends early or is corrupt.
bool fj_pb_read(fj_pb_t *c, uint8_t *out, uint32_t n);
