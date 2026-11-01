// Incremental frame parser + encoder (portable, unit-tested on the host).
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "fj_proto.h"

typedef struct {
    uint8_t buf[FJ_HEADER_SIZE + FJ_MAX_PAYLOAD + 2];
    uint32_t have;        // bytes in buf
    uint32_t need;        // total bytes of the current frame (0 = header not complete yet)
    uint32_t done;        // size of the frame handed out last time (dropped on next push)
    uint32_t crc_errors, sync_errors;
} fj_framer_t;

typedef struct { uint8_t type, seq; uint32_t len; const uint8_t *payload; } fj_frame_t;

uint16_t fj_crc16(const uint8_t *d, size_t n, uint16_t crc);
void fj_framer_init(fj_framer_t *f);
// How many more bytes the framer wants right now (never 0).
uint32_t fj_framer_want(const fj_framer_t *f);
// Header of the frame being received, if complete (lets the caller apply back-pressure
// before accepting a big payload). Returns false if the header isn't in yet.
bool fj_framer_peek(const fj_framer_t *f, uint8_t *type, uint32_t *len);
// Push bytes. Returns number of bytes consumed (<= n). If a complete, valid frame is
// available *out is filled and true is returned; the frame stays valid until the next push.
bool fj_framer_push(fj_framer_t *f, const uint8_t *data, uint32_t n, uint32_t *consumed, fj_frame_t *out);
// Encode a frame into dst (needs len + 10 bytes). Returns total length.
uint32_t fj_frame_encode(uint8_t *dst, uint8_t type, uint8_t seq, const void *payload, uint32_t len);
