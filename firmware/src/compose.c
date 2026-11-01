#include "compose.h"
#include <string.h>

void fj_compose_tables(fj_tables_t *t, int heads, bool nozzle0_downstream, const int8_t dy[FJ_MAX_HEADS]) {
    memset(t, 0, sizeof *t);
    int rows = heads > 1 ? FJ_ROWS_MULTI : FJ_ROWS;
    int base = heads > 1 ? FJ_ROW_SPARE : 0;
    for (int n = 0; n < HP45_NOZZLES; n++)
        t->all_words[hp45_nozzle_address[n]] |= (uint16_t)(1u << hp45_nozzle_primitive[n]);
    for (int h = 0; h < FJ_MAX_HEADS; h++) {
        int shift = base + (heads > 1 ? dy[h] : 0);
        for (int n = 0; n < HP45_NOZZLES; n++) {
            int q = n & 1;
            int phys = nozzle0_downstream ? n : HP45_NOZZLES - 1 - n;
            int r = phys - shift;                    // data row this nozzle prints
            if (r < 0 || r >= rows) continue;        // spare nozzle
            fj_nozzle_ref_t *e = &t->by_parity[h][q][t->count[h][q]++];
            e->byte = (uint8_t)(r >> 3);
            e->bit = (uint8_t)(1u << (r & 7));
            e->addr = hp45_nozzle_address[n];
            e->prim_mask = (uint16_t)(1u << hp45_nozzle_primitive[n]);
        }
    }
}

void fj_pass_setup(fj_pass_t *p, const fj_tables_t *t, const fj_ring_t *r,
                   const uint32_t start[], const uint32_t len[], bool packed, int heads,
                   int32_t x0, int32_t ncols, int32_t dir, const int32_t head_off[], int32_t off_odd) {
    memset(p, 0, sizeof *p);
    p->t = t;
    p->x0 = x0;
    p->n = ncols;
    p->dir = dir;
    p->heads = heads;
    p->maxo = INT32_MIN;
    p->mino = INT32_MAX;
    for (int h = 0; h < heads; h++)
        for (int q = 0; q < 2; q++) {
            int32_t o = head_off[h] + (q ? off_odd : 0);
            p->off[h][q] = o;
            if (o > p->maxo) p->maxo = o;
            if (o < p->mino) p->mino = o;
        }
    for (int h = 0; h < heads; h++)
        for (int q = 0; q < 2; q++) {
            p->lag[h][q] = dir == 0 ? p->maxo - p->off[h][q] : p->off[h][q] - p->mino;
            fj_pb_init(&p->cur[h][q], r, start[h], len[h], packed);
        }
    p->steps = ncols + (p->maxo - p->mino);
}

int32_t fj_pass_ref_col(const fj_pass_t *p, int32_t j) {
    return p->dir == 0 ? p->x0 - p->maxo + j : p->x0 + p->n - 1 - p->mino - j;
}

bool fj_pass_compose(fj_pass_t *p, int32_t j, fj_words_t words) {
    memset(words, 0, sizeof(fj_words_t));
    for (int h = 0; h < p->heads; h++)
        for (int q = 0; q < 2; q++) {
            int32_t k = j - p->lag[h][q];
            if (k < 0 || k >= p->n) continue;
            if (!fj_pb_read(&p->cur[h][q], p->col[h][q], FJ_COL_BYTES)) { p->error = true; return false; }
            const uint8_t *c = p->col[h][q];
            const fj_nozzle_ref_t *e = p->t->by_parity[h][q];
            uint16_t *w = words[h];
            for (int i = p->t->count[h][q]; i > 0; i--, e++)
                if (c[e->byte] & e->bit) w[e->addr] |= e->prim_mask;
        }
    return true;
}

void fj_words_for_nozzle(const fj_tables_t *t, int heads, int head, int nozzle, fj_words_t words) {
    memset(words, 0, sizeof(fj_words_t));
    for (int h = 0; h < heads; h++) {
        if (head >= 0 && h != head) continue;
        if (nozzle < 0) memcpy(words[h], t->all_words, sizeof t->all_words);
        else if (nozzle < HP45_NOZZLES)
            words[h][hp45_nozzle_address[nozzle]] = (uint16_t)(1u << hp45_nozzle_primitive[nozzle]);
    }
}
