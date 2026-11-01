#include "packbits.h"

void fj_pb_init(fj_pb_t *c, const fj_ring_t *r, uint32_t start, uint32_t len, bool packed) {
    c->ring = r; c->pos = start; c->end = start + len; c->packed = packed;
    c->mode = 0; c->count = 0; c->value = 0;
}

bool fj_pb_read(fj_pb_t *c, uint8_t *out, uint32_t n) {
    if (!c->packed) {
        if ((int32_t)(c->end - c->pos) < (int32_t)n) return false;
        for (uint32_t i = 0; i < n; i++) out[i] = fj_ring_at(c->ring, c->pos++);
        return true;
    }
    uint32_t i = 0;
    while (i < n) {
        if (c->mode == 0) {
            if (c->pos == c->end) return false;
            uint8_t ctl = fj_ring_at(c->ring, c->pos++);
            if (ctl < 128) { c->mode = 1; c->count = ctl + 1; }
            else if (ctl > 128) {
                if (c->pos == c->end) return false;
                c->mode = 2; c->count = 257 - ctl; c->value = fj_ring_at(c->ring, c->pos++);
            }
            continue;   // 128 = no-op
        }
        if (c->mode == 1) {
            if (c->pos == c->end) return false;
            out[i++] = fj_ring_at(c->ring, c->pos++);
        } else {
            out[i++] = c->value;
        }
        if (--c->count == 0) c->mode = 0;
    }
    return true;
}
