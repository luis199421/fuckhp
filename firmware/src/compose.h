// Pass composer: turns swath column data (pixel space) into HP45 fire words.
//
// The HP45 has two nozzle columns ~4 mm apart (even and odd nozzles). When the
// head reference (= the even column) is over pixel column c, the odd column is
// over c + off_odd. Each column therefore reads the swath data with its own
// cursor, lagging the other by |off_odd| columns.
//
// fire words: words[a] = bitmask of primitives to pulse while address a is on.
// Address and primitive numbers are HP45 "raw" 0-based numbers (A1 = 0, P1 = 0).
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "hp45_map.h"
#include "fj_proto.h"
#include "packbits.h"

typedef struct {
    uint8_t byte, bit, addr;
    uint16_t prim_mask;
} fj_nozzle_ref_t;

typedef struct {
    fj_nozzle_ref_t by_parity[2][HP45_NOZZLES / 2];   // filled by fj_compose_tables()
    uint16_t all_words[HP45_ADDRESSES];               // every nozzle on
} fj_tables_t;

typedef struct {
    const fj_tables_t *t;
    int32_t x0, n, dir;
    int32_t off[2];         // pixel offset of the even/odd nozzle column vs head reference
    int32_t lag[2];         // firing step at which each column reaches the first data column
    int32_t steps;          // number of firing steps (head reference columns) in the pass
    fj_pb_t cur[2];
    uint8_t col[2][FJ_COL_BYTES];
    bool error;
} fj_pass_t;

// nozzle0_downstream: data row r is nozzle r (true) or nozzle 299 - r (false)
void fj_compose_tables(fj_tables_t *t, bool nozzle0_downstream);

// off_odd = round(row_gap_um / um_per_col)
void fj_pass_setup(fj_pass_t *p, const fj_tables_t *t, const fj_ring_t *r, uint32_t start,
                   uint32_t len, bool packed, int32_t x0, int32_t ncols, int32_t dir, int32_t off_odd);

// Head reference pixel column at firing step j.
int32_t fj_pass_ref_col(const fj_pass_t *p, int32_t j);

// Compose firing step j (must be called with j = 0, 1, 2, ... in order).
// Returns false if the data stream is short/corrupt.
bool fj_pass_compose(fj_pass_t *p, int32_t j, uint16_t words[HP45_ADDRESSES]);

// Fire words for a single nozzle (0..299) or all nozzles (-1).
void fj_words_for_nozzle(const fj_tables_t *t, int nozzle, uint16_t words[HP45_ADDRESSES]);
