#include "ring.h"
#include <string.h>

void fj_ring_write(fj_ring_t *r, const uint8_t *d, uint32_t n) {
    uint32_t off = r->head & (r->size - 1);
    uint32_t first = r->size - off < n ? r->size - off : n;
    memcpy(r->buf + off, d, first);
    memcpy(r->buf, d + first, n - first);
    r->head += n;
}
