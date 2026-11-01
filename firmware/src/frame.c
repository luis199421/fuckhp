#include "frame.h"
#include <string.h>

uint16_t fj_crc16(const uint8_t *d, size_t n, uint16_t crc) {
    while (n--) {
        crc ^= (uint16_t)(*d++) << 8;
        for (int i = 0; i < 8; i++)
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
    }
    return crc;
}

void fj_framer_init(fj_framer_t *f) { memset(f, 0, sizeof *f); }

uint32_t fj_framer_want(const fj_framer_t *f) {
    uint32_t have = f->have - f->done;
    if (f->need) return f->need > have ? f->need - have : 1;
    return have < FJ_HEADER_SIZE ? FJ_HEADER_SIZE - have : 1;
}

bool fj_framer_peek(const fj_framer_t *f, uint8_t *type, uint32_t *len) {
    if (!f->need) return false;
    *type = f->buf[f->done + 2];
    *len = f->need - FJ_HEADER_SIZE - 2;
    return true;
}

static void drop(fj_framer_t *f, uint32_t k) {   // discard k bytes from the front
    memmove(f->buf, f->buf + k, f->have - k);
    f->have -= k;
    f->need = 0;
}

// Try to extract a frame from the bytes already buffered.
static bool process(fj_framer_t *f, fj_frame_t *out) {
    for (;;) {
        if (f->have >= 1 && f->buf[0] != 'F') { f->sync_errors++; drop(f, 1); continue; }
        if (f->have >= 2 && f->buf[1] != 'J') { f->sync_errors++; drop(f, 1); continue; }
        if (f->have < FJ_HEADER_SIZE) return false;
        if (!f->need) {
            uint32_t len = f->buf[4] | f->buf[5] << 8 | (uint32_t)f->buf[6] << 16 | (uint32_t)f->buf[7] << 24;
            if (len > FJ_MAX_PAYLOAD) { f->sync_errors++; drop(f, 1); continue; }
            f->need = FJ_HEADER_SIZE + len + 2;
        }
        if (f->have < f->need) return false;
        uint32_t len = f->need - FJ_HEADER_SIZE - 2;
        uint16_t crc = f->buf[f->need - 2] | f->buf[f->need - 1] << 8;
        if (crc != fj_crc16(f->buf + 2, FJ_HEADER_SIZE - 2 + len, 0xFFFF)) {
            f->crc_errors++;
            drop(f, 1);       // resync inside the bad frame
            continue;
        }
        out->type = f->buf[2];
        out->seq = f->buf[3];
        out->len = len;
        out->payload = f->buf + FJ_HEADER_SIZE;
        f->done = f->need;    // keep it readable until the next call
        f->need = 0;
        return true;
    }
}

bool fj_framer_push(fj_framer_t *f, const uint8_t *data, uint32_t n, uint32_t *consumed, fj_frame_t *out) {
    if (f->done) {            // release the frame handed out last time
        uint32_t k = f->done;
        f->done = 0;
        drop(f, k);
        if (process(f, out)) { *consumed = 0; return true; }
    }
    uint32_t used = 0;
    while (used < n) {
        uint32_t want = fj_framer_want(f);
        uint32_t take = n - used < want ? n - used : want;
        if (f->have + take > sizeof f->buf) take = sizeof f->buf - f->have;
        memcpy(f->buf + f->have, data + used, take);
        f->have += take;
        used += take;
        if (process(f, out)) { *consumed = used; return true; }
    }
    *consumed = used;
    return false;
}

uint32_t fj_frame_encode(uint8_t *dst, uint8_t type, uint8_t seq, const void *payload, uint32_t len) {
    dst[0] = 'F'; dst[1] = 'J'; dst[2] = type; dst[3] = seq;
    dst[4] = len; dst[5] = len >> 8; dst[6] = len >> 16; dst[7] = len >> 24;
    if (len) memcpy(dst + FJ_HEADER_SIZE, payload, len);
    uint16_t crc = fj_crc16(dst + 2, FJ_HEADER_SIZE - 2 + len, 0xFFFF);
    dst[FJ_HEADER_SIZE + len] = crc;
    dst[FJ_HEADER_SIZE + len + 1] = crc >> 8;
    return FJ_HEADER_SIZE + len + 2;
}
