// Host-side simulation of the firmware data path:
//   job stream -> framer -> ring -> pass composer -> HP45 fire words
//   -> "physical" nozzle positions -> page bitmap (PBM).
// It inverts the nozzle map, so it proves the composer drives every nozzle
// at the right place. Used by host/tests/test_firmware_sim.py.
//
// usage: fw_sim <job.bin> <out-prefix> <nozzle0_downstream 0|1> <row_gap_um>
//               [heads head1_x_um head2_x_um head3_x_um dy1 dy2 dy3]
// writes <out-prefix>-<page>-<plane>.pbm
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/compose.h"
#include "../src/frame.h"

#define RING_SIZE (1u << 18)
#define MAX_COLS 5184
#define MAX_ROWS 4000

static uint8_t ring_buf[RING_SIZE];
static fj_ring_t ring;
static fj_tables_t tables;
static uint8_t page[FJ_MAX_HEADS][MAX_ROWS][MAX_COLS];
static int page_rows, page_no;
static int nozzle_of[HP45_PRIMITIVES][HP45_ADDRESSES];

static int n_heads = 1;

static void write_page(const char *prefix) {
    ++page_no;
    for (int pl = 0; pl < n_heads; pl++) {
        char name[512];
        snprintf(name, sizeof name, "%s-%d-%d.pbm", prefix, page_no, pl);
        FILE *f = fopen(name, "wb");
        int h = page_rows > 0 ? page_rows : 1;
        fprintf(f, "P4\n%d %d\n", MAX_COLS, h);
        for (int y = 0; y < h; y++) {
            uint8_t line[MAX_COLS / 8] = {0};
            for (int x = 0; x < MAX_COLS; x++) if (page[pl][y][x]) line[x >> 3] |= 0x80 >> (x & 7);
            fwrite(line, 1, sizeof line, f);
        }
        fclose(f);
    }
    memset(page, 0, sizeof page);
    page_rows = 0;
}

int main(int argc, char **argv) {
    if (argc != 5 && argc != 12) { fprintf(stderr, "usage: fw_sim job.bin prefix down gap_um [heads hx1 hx2 hx3 dy1 dy2 dy3]\n"); return 2; }
    FILE *in = fopen(argv[1], "rb");
    if (!in) { perror(argv[1]); return 2; }
    int down = atoi(argv[3]);
    int off_odd = (int)lroundf(atof(argv[4]) / FJ_UM_PER_COL);
    int32_t head_off[FJ_MAX_HEADS] = {0};
    int8_t dy[FJ_MAX_HEADS] = {0};
    if (argc == 12) {
        n_heads = atoi(argv[5]);
        for (int h = 1; h < 4; h++) {
            head_off[h] = (int32_t)lroundf(atof(argv[5 + h]) / FJ_UM_PER_COL);
            dy[h] = (int8_t)atoi(argv[8 + h]);
        }
    }
    int base = n_heads > 1 ? FJ_ROW_SPARE : 0;
    int rows = n_heads > 1 ? FJ_ROWS_MULTI : FJ_ROWS;
    fj_ring_init(&ring, ring_buf, RING_SIZE);
    fj_compose_tables(&tables, n_heads, down, dy);
    memset(nozzle_of, -1, sizeof nozzle_of);
    for (int n = 0; n < HP45_NOZZLES; n++) {
        if (nozzle_of[hp45_nozzle_primitive[n]][hp45_nozzle_address[n]] != -1) {
            fprintf(stderr, "nozzle map not one-to-one\n"); return 1;
        }
        nozzle_of[hp45_nozzle_primitive[n]][hp45_nozzle_address[n]] = n;
    }
    static fj_framer_t fr;
    fj_framer_init(&fr);
    fj_swath_begin_t sw = {0};
    uint32_t sw_start = 0, sw_got = 0, plane_len[FJ_MAX_HEADS] = {0};
    int job_planes = 1;
    int in_swath = 0, frames = 0, passes = 0;
    uint8_t chunk[777];   // odd size on purpose: exercises split frames
    size_t n;
    while ((n = fread(chunk, 1, sizeof chunk, in)) > 0) {
        uint32_t off = 0;
        while (off < n) {
            fj_frame_t f;
            uint32_t used;
            int got = fj_framer_push(&fr, chunk + off, (uint32_t)(n - off), &used, &f);
            off += used;
            if (!got) continue;
            frames++;
            if (f.type == FJ_JOB_BEGIN) {
                job_planes = f.len > 1 && f.payload[1] ? f.payload[1] : 1;
                if (job_planes != n_heads) { fprintf(stderr, "ink set mismatch\n"); return 1; }
            } else if (f.type == FJ_SWATH_BEGIN) {
                memcpy(&sw, f.payload, sizeof sw);
                plane_len[0] = sw.data_len;
                if (n_heads > 1) memcpy(plane_len, f.payload + sizeof sw, 4u * n_heads);
                sw_start = ring.head; sw_got = 0; in_swath = 1;
            } else if (f.type == FJ_SWATH_DATA && in_swath) {
                if (fj_ring_free(&ring) < f.len) { fprintf(stderr, "ring overflow\n"); return 1; }
                fj_ring_write(&ring, f.payload, f.len);
                sw_got += f.len;
            } else if (f.type == FJ_PAGE_END) {
                write_page(argv[2]);
            }
            if (in_swath && sw_got == sw.data_len) {
                in_swath = 0;
                passes++;
                static fj_pass_t p;
                uint32_t starts[FJ_MAX_HEADS], acc = sw_start;
                for (int h = 0; h < n_heads; h++) { starts[h] = acc; acc += plane_len[h]; }
                fj_pass_setup(&p, &tables, &ring, starts, plane_len, sw.flags & FJ_SWATH_PACKBITS, n_heads,
                              sw.x0, sw.ncols, sw.dir, head_off, off_odd);
                int y0 = (int)lroundf(sw.y_um / FJ_UM_PER_COL);
                fj_words_t words;
                for (int j = 0; j < p.steps; j++) {
                    if (!fj_pass_compose(&p, j, words)) { fprintf(stderr, "data error\n"); return 1; }
                    int c = fj_pass_ref_col(&p, j);
                    for (int h = 0; h < n_heads; h++)
                    for (int a = 0; a < HP45_ADDRESSES; a++)
                        for (int pr = 0; pr < HP45_PRIMITIVES; pr++) {
                            if (!(words[h][a] >> pr & 1)) continue;
                            int noz = nozzle_of[pr][a];
                            if (noz < 0) { fprintf(stderr, "fired a non-existent nozzle\n"); return 1; }
                            int x = c + head_off[h] + (noz & 1 ? off_odd : 0);
                            int phys = down ? noz : HP45_NOZZLES - 1 - noz;
                            int r = phys - base - (n_heads > 1 ? dy[h] : 0);
                            if (r < 0 || r >= rows) { fprintf(stderr, "fired a spare nozzle\n"); return 1; }
                            int y = y0 + r;
                            if (x < 0 || x >= MAX_COLS || y >= MAX_ROWS) { fprintf(stderr, "out of page\n"); return 1; }
                            page[h][y][x] = 1;
                            if (y + 1 > page_rows) page_rows = y + 1;
                        }
                }
                fj_ring_release_to(&ring, sw_start + sw.data_len);
            }
        }
    }
    fprintf(stderr, "frames=%d passes=%d pages=%d crc_err=%u sync_err=%u\n",
            frames, passes, page_no, fr.crc_errors, fr.sync_errors);
    return 0;
}
