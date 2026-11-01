// Pass composer: turns swath column data (pixel space) into HP45 fire words, for 1-4
// cartridges ("heads") side by side in the carriage.
//
// Each HP45 has two nozzle columns ~4 mm apart (even and odd nozzles), and each cartridge
// sits at its own X offset. When the head reference (= slot 0's even column) is over pixel
// column c, nozzle column (h, q) is over c + off[h][q]. Every nozzle column therefore reads
// its own plane of the swath data with its own cursor, lagging the others.
//
// fire words: words[h][a] = bitmask of head h's primitives to pulse while address a is on.
// Address and primitive numbers are HP45 "raw" 0-based numbers (A1 = 0, P1 = 0).
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "hp45_map.h"
#include "fj_proto.h"
#include "packbits.h"

#define FJ_MAX_HEADS FJ_MAX_PLANES

typedef struct {
    uint8_t byte, bit, addr;
    uint16_t prim_mask;
} fj_nozzle_ref_t;

typedef struct {
    fj_nozzle_ref_t by_parity[FJ_MAX_HEADS][2][HP45_NOZZLES / 2];   // filled by fj_compose_tables()
    uint16_t count[FJ_MAX_HEADS][2];
    uint16_t all_words[HP45_ADDRESSES];               // every nozzle of one head on
} fj_tables_t;

typedef uint16_t fj_words_t[FJ_MAX_HEADS][HP45_ADDRESSES];

typedef struct {
    const fj_tables_t *t;
    int32_t x0, n, dir, heads;
    int32_t off[FJ_MAX_HEADS][2];   // pixel offset of each nozzle column vs head reference
    int32_t lag[FJ_MAX_HEADS][2];   // firing step at which each column reaches the first data column
    int32_t maxo, mino;
    int32_t steps;                  // number of firing steps (head reference columns) in the pass
    fj_pb_t cur[FJ_MAX_HEADS][2];
    uint8_t col[FJ_MAX_HEADS][2][FJ_COL_BYTES];
    bool error;
} fj_pass_t;

// nozzle0_downstream: physical row p is nozzle p (true) or nozzle 299 - p (false).
// With heads > 1 a pass uses rows 0..287 and data row r goes to physical row
// r + FJ_ROW_SPARE + dy[h], so each cartridge can be lined up vertically +-6 rows.
void fj_compose_tables(fj_tables_t *t, int heads, bool nozzle0_downstream, const int8_t dy[FJ_MAX_HEADS]);

// start/len: where each head's plane is in the ring. head_off: pixel offset of each head's even
// column vs slot 0 (slot 0 = 0); off_odd: odd column vs even column (round(row_gap_um / um_per_col)).
void fj_pass_setup(fj_pass_t *p, const fj_tables_t *t, const fj_ring_t *r,
                   const uint32_t start[], const uint32_t len[], bool packed, int heads,
                   int32_t x0, int32_t ncols, int32_t dir, const int32_t head_off[], int32_t off_odd);

// Head reference pixel column at firing step j.
int32_t fj_pass_ref_col(const fj_pass_t *p, int32_t j);

// Compose firing step j (must be called with j = 0, 1, 2, ... in order).
// Returns false if the data stream is short/corrupt.
bool fj_pass_compose(fj_pass_t *p, int32_t j, fj_words_t words);

// Fire words for nozzle `nozzle` (0..299) of head `head`, or every nozzle (nozzle -1) of
// every head < heads (head -1).
void fj_words_for_nozzle(const fj_tables_t *t, int heads, int head, int nozzle, fj_words_t words);
