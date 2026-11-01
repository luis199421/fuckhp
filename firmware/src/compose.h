// Pass composer for HP 63/302 cartridges: swath column data (pixel space, one plane per
// ink) -> nozzle data for the black and the colour cartridge.
//
// Nozzle columns ("ncols"): black row 0, black row 1, cyan, magenta, yellow. Each sits at
// its own X offset from the head reference (black row 0) and reads its plane of the swath
// with its own cursor, so all of them print the same pixel column at different moments.
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "fj_proto.h"
#include "hp302.h"
#include "packbits.h"

#define FJ_MAX_NCOLS 5

enum { FJ_INK_K = 0, FJ_INK_CMY = 1, FJ_INK_KCMY = 2 };   // ink set ids (JOB_BEGIN)

typedef struct {
    int inkset;
    bool flip;                 // nozzle index grows upstream instead of downstream
    int32_t k_row_gap_cols;    // black row 1 vs row 0
    int32_t color_x_cols;      // cyan column vs black row 0
    int32_t cmy_pitch_cols;    // magenta vs cyan, yellow vs magenta
    int32_t k_dy_rows;         // colour jobs: which black rows line up with the colour swath
} fj_geom_t;

typedef struct { uint8_t byte, bit, nbyte, nmask; } fj_nz_t;     // data bit -> nozzle bit
typedef struct {
    uint8_t plane, cart;
    int32_t off;
    uint16_t n;
    fj_nz_t nz[HP302_K_ROW];
} fj_ncol_t;

typedef struct {
    fj_ncol_t col[FJ_MAX_NCOLS];
    int ncols, planes, rows;
    uint8_t spit[2][HP302_NOZDATA];   // every connected nozzle of each cartridge
} fj_tables_t;

typedef uint8_t fj_nozdata_t[2][HP302_NOZDATA];

int fj_inkset_planes(int inkset);           // 1, 3 or 4
int fj_inkset_rows(int inkset);             // 324 (black only) or 168
bool fj_inkset_uses(int inkset, int cart);  // does this ink set use the black/colour cartridge
void fj_build_tables(fj_tables_t *t, const fj_geom_t *g);

typedef struct {
    const fj_tables_t *t;
    int32_t x0, n, dir, maxo, mino, steps;
    int32_t lag[FJ_MAX_NCOLS];
    fj_pb_t cur[FJ_MAX_NCOLS];
    uint8_t col[FJ_MAX_NCOLS][FJ_COL_BYTES];
    bool error;
} fj_pass_t;

void fj_pass_setup(fj_pass_t *p, const fj_tables_t *t, const fj_ring_t *r, const uint32_t start[],
                   const uint32_t len[], bool packed, int32_t x0, int32_t ncols, int32_t dir);
int32_t fj_pass_ref_col(const fj_pass_t *p, int32_t j);
// Compose firing step j (call with j = 0, 1, 2, ...). Returns false on corrupt data.
bool fj_pass_compose(fj_pass_t *p, int32_t j, fj_nozdata_t out);
