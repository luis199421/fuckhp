// Single-producer / single-consumer byte ring holding compressed swath data.
// Positions are free-running 32-bit counters; size must be a power of two.
#pragma once
#include <stdint.h>

typedef struct {
    uint8_t *buf;
    uint32_t size;
    volatile uint32_t head;   // total bytes ever written
    volatile uint32_t tail;   // total bytes ever released
} fj_ring_t;

static inline void fj_ring_init(fj_ring_t *r, uint8_t *buf, uint32_t size) {
    r->buf = buf; r->size = size; r->head = r->tail = 0;
}
static inline uint32_t fj_ring_used(const fj_ring_t *r) { return r->head - r->tail; }
static inline uint32_t fj_ring_free(const fj_ring_t *r) { return r->size - (r->head - r->tail); }
static inline uint8_t fj_ring_at(const fj_ring_t *r, uint32_t pos) { return r->buf[pos & (r->size - 1)]; }
void fj_ring_write(fj_ring_t *r, const uint8_t *d, uint32_t n);   // caller checks free space
static inline void fj_ring_release_to(fj_ring_t *r, uint32_t pos) { r->tail = pos; }
static inline void fj_ring_reset(fj_ring_t *r) { r->tail = r->head; }
