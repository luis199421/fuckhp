#include "compose.h"
#include <string.h>

void fj_compose_tables(fj_tables_t *t, bool nozzle0_downstream) {
    int k[2] = {0, 0};
    memset(t->all_words, 0, sizeof t->all_words);
    for (int n = 0; n < HP45_NOZZLES; n++) {
        int q = n & 1;
        int r = nozzle0_downstream ? n : HP45_NOZZLES - 1 - n;
        fj_nozzle_ref_t *e = &t->by_parity[q][k[q]++];
        e->byte = (uint8_t)(r >> 3);
        e->bit = (uint8_t)(1u << (r & 7));
        e->addr = hp45_nozzle_address[n];
        e->prim_mask = (uint16_t)(1u << hp45_nozzle_primitive[n]);
        t->all_words[e->addr] |= e->prim_mask;
    }
}

void fj_pass_setup(fj_pass_t *p, const fj_tables_t *t, const fj_ring_t *r, uint32_t start,
                   uint32_t len, bool packed, int32_t x0, int32_t ncols, int32_t dir, int32_t off_odd) {
    memset(p, 0, sizeof *p);
    p->t = t;
    p->x0 = x0;
    p->n = ncols;
    p->dir = dir;
    p->off[0] = 0;
    p->off[1] = off_odd;
    int32_t maxo = off_odd > 0 ? off_odd : 0, mino = off_odd < 0 ? off_odd : 0;
    for (int q = 0; q < 2; q++) {
        p->lag[q] = dir == 0 ? maxo - p->off[q] : p->off[q] - mino;
        fj_pb_init(&p->cur[q], r, start, len, packed);
    }
    p->steps = ncols + (maxo - mino);
}

int32_t fj_pass_ref_col(const fj_pass_t *p, int32_t j) {
    int32_t maxo = p->off[1] > 0 ? p->off[1] : 0, mino = p->off[1] < 0 ? p->off[1] : 0;
    return p->dir == 0 ? p->x0 - maxo + j : p->x0 + p->n - 1 - mino - j;
}

bool fj_pass_compose(fj_pass_t *p, int32_t j, uint16_t words[HP45_ADDRESSES]) {
    memset(words, 0, HP45_ADDRESSES * sizeof words[0]);
    for (int q = 0; q < 2; q++) {
        int32_t k = j - p->lag[q];
        if (k < 0 || k >= p->n) continue;
        if (!fj_pb_read(&p->cur[q], p->col[q], FJ_COL_BYTES)) { p->error = true; return false; }
        const uint8_t *c = p->col[q];
        const fj_nozzle_ref_t *e = p->t->by_parity[q];
        for (int i = 0; i < HP45_NOZZLES / 2; i++, e++)
            if (c[e->byte] & e->bit) words[e->addr] |= e->prim_mask;
    }
    return true;
}

void fj_words_for_nozzle(const fj_tables_t *t, int nozzle, uint16_t words[HP45_ADDRESSES]) {
    if (nozzle < 0) { memcpy(words, t->all_words, sizeof t->all_words); return; }
    memset(words, 0, HP45_ADDRESSES * sizeof words[0]);
    if (nozzle < HP45_NOZZLES)
        words[hp45_nozzle_address[nozzle]] = (uint16_t)(1u << hp45_nozzle_primitive[nozzle]);
}
