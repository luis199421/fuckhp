#include "compose.h"
#include <string.h>

int fj_inkset_planes(int s) { return s == FJ_INK_K ? 1 : s == FJ_INK_CMY ? 3 : 4; }
int fj_inkset_rows(int s) { return s == FJ_INK_K ? FJ_ROWS_K : FJ_ROWS_COLOR; }
bool fj_inkset_uses(int s, int cart) {
    return cart == HP302_CART_BLACK ? s != FJ_INK_CMY : s != FJ_INK_K;
}

static void add(fj_ncol_t *c, int row, int rows, bool flip, int nbyte, uint8_t nmask, int top) {
    int r = flip ? top - row : row;
    if (r < 0 || r >= rows || !nmask) return;
    fj_nz_t *z = &c->nz[c->n++];
    z->byte = (uint8_t)(r >> 3);
    z->bit = (uint8_t)(1u << (r & 7));
    z->nbyte = (uint8_t)nbyte;
    z->nmask = nmask;
}

void fj_build_tables(fj_tables_t *t, const fj_geom_t *g) {
    memset(t, 0, sizeof *t);
    t->rows = fj_inkset_rows(g->inkset);
    t->planes = fj_inkset_planes(g->inkset);
    int plane = 0;
    uint8_t m;
    if (fj_inkset_uses(g->inkset, HP302_CART_BLACK)) {
        int dy = g->inkset == FJ_INK_K ? 0 : g->k_dy_rows;
        for (int q = 0; q < 2; q++) {
            fj_ncol_t *c = &t->col[t->ncols++];
            c->plane = (uint8_t)plane;
            c->cart = HP302_CART_BLACK;
            c->off = q ? g->k_row_gap_cols : 0;
            for (int p = HP302_K_FIRST; p < HP302_K_LAST; p++) {
                int phys = 2 * (p - HP302_K_FIRST) + q;               // 0..323 at 600 dpi
                int b = hp302_black_bit(p, q, &m);
                // flip turns the whole 324-row column upside down before the colour offset
                int row = (g->flip ? 2 * (HP302_K_LAST - HP302_K_FIRST) - 1 - phys : phys) - dy;
                add(c, row, t->rows, false, b, m, 0);
            }
        }
        plane++;
    }
    if (fj_inkset_uses(g->inkset, HP302_CART_COLOR)) {
        for (int k = 0; k < 3; k++) {
            fj_ncol_t *c = &t->col[t->ncols++];
            c->plane = (uint8_t)(plane + k);
            c->cart = HP302_CART_COLOR;
            c->off = g->color_x_cols + k * g->cmy_pitch_cols;
            for (int p = HP302_C_FIRST; p < HP302_C_FIRST + HP302_C_COUNT; p++) {
                int b = hp302_color_bit(p, k, &m);
                add(c, 2 * (p - HP302_C_FIRST), t->rows, g->flip, b, m, 2 * (HP302_C_COUNT - 1));
            }
        }
    }
    // spit patterns: every connected nozzle
    for (int q = 0; q < 2; q++)
        for (int p = HP302_K_FIRST; p < HP302_K_LAST; p++) hp302_set_black(t->spit[0], p, q);
    for (int k = 0; k < 3; k++)
        for (int p = HP302_C_FIRST; p < HP302_C_FIRST + HP302_C_COUNT; p++) hp302_set_color(t->spit[1], p, k);
}

void fj_pass_setup(fj_pass_t *p, const fj_tables_t *t, const fj_ring_t *r, const uint32_t start[],
                   const uint32_t len[], bool packed, int32_t x0, int32_t ncols, int32_t dir) {
    memset(p, 0, sizeof *p);
    p->t = t;
    p->x0 = x0;
    p->n = ncols;
    p->dir = dir;
    p->maxo = INT32_MIN;
    p->mino = INT32_MAX;
    for (int i = 0; i < t->ncols; i++) {
        if (t->col[i].off > p->maxo) p->maxo = t->col[i].off;
        if (t->col[i].off < p->mino) p->mino = t->col[i].off;
    }
    for (int i = 0; i < t->ncols; i++) {
        const fj_ncol_t *c = &t->col[i];
        p->lag[i] = dir == 0 ? p->maxo - c->off : c->off - p->mino;
        fj_pb_init(&p->cur[i], r, start[c->plane], len[c->plane], packed);
    }
    p->steps = ncols + (p->maxo - p->mino);
}

int32_t fj_pass_ref_col(const fj_pass_t *p, int32_t j) {
    return p->dir == 0 ? p->x0 - p->maxo + j : p->x0 + p->n - 1 - p->mino - j;
}

bool fj_pass_compose(fj_pass_t *p, int32_t j, fj_nozdata_t out) {
    memset(out, 0, sizeof(fj_nozdata_t));
    for (int i = 0; i < p->t->ncols; i++) {
        int32_t k = j - p->lag[i];
        if (k < 0 || k >= p->n) continue;
        if (!fj_pb_read(&p->cur[i], p->col[i], FJ_COL_BYTES)) { p->error = true; return false; }
        const fj_ncol_t *c = &p->t->col[i];
        const uint8_t *d = p->col[i];
        uint8_t *o = out[c->cart];
        const fj_nz_t *z = c->nz;
        for (int n = c->n; n > 0; n--, z++)
            if (d[z->byte] & z->bit) o[z->nbyte] |= z->nmask;
    }
    return true;
}
