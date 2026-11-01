// Host-side simulation of the firmware data path for HP 63/302 cartridges:
//   job stream -> framer -> ring -> pass composer -> nozzle data per cartridge
//   -> nozzle positions -> page bitmaps per ink plane (PBM).
// Used by host/tests/test_firmware_sim.py.
//
// usage: fw_sim <job.bin> <out-prefix> <flip 0|1> <k_row_gap_um> <color_x_um> <cmy_pitch_um> <k_dy_rows>
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
static uint8_t page[FJ_MAX_PLANES][MAX_ROWS][MAX_COLS];
static int page_rows, page_no, n_planes = 1;

static void write_page(const char *prefix) {
    ++page_no;
    for (int pl = 0; pl < n_planes; pl++) {
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
    if (argc != 8) { fprintf(stderr, "usage: fw_sim job.bin prefix flip kgap_um colorx_um pitch_um kdy\n"); return 2; }
    FILE *in = fopen(argv[1], "rb");
    if (!in) { perror(argv[1]); return 2; }
    fj_geom_t g = {0};
    g.flip = atoi(argv[3]);
    g.k_row_gap_cols = (int32_t)lroundf(atof(argv[4]) / FJ_UM_PER_COL);
    g.color_x_cols = (int32_t)lroundf(atof(argv[5]) / FJ_UM_PER_COL);
    g.cmy_pitch_cols = (int32_t)lroundf(atof(argv[6]) / FJ_UM_PER_COL);
    g.k_dy_rows = atoi(argv[7]);
    fj_ring_init(&ring, ring_buf, RING_SIZE);
    static fj_framer_t fr;
    fj_framer_init(&fr);
    fj_swath_begin_t sw = {0};
    uint32_t sw_start = 0, sw_got = 0, plane_len[FJ_MAX_PLANES] = {0};
    int in_swath = 0, frames = 0, passes = 0;
    uint8_t chunk[777];
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
                g.inkset = f.len > 2 ? f.payload[2] : 0;
                fj_build_tables(&tables, &g);
                n_planes = tables.planes;
                int planes = f.len > 1 && f.payload[1] ? f.payload[1] : 1;
                if (planes != n_planes) { fprintf(stderr, "plane count mismatch\n"); return 1; }
            } else if (f.type == FJ_SWATH_BEGIN) {
                memcpy(&sw, f.payload, sizeof sw);
                plane_len[0] = sw.data_len;
                if (n_planes > 1) memcpy(plane_len, f.payload + sizeof sw, 4u * n_planes);
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
                uint32_t starts[FJ_MAX_PLANES], acc = sw_start;
                for (int h = 0; h < n_planes; h++) { starts[h] = acc; acc += plane_len[h]; }
                fj_pass_setup(&p, &tables, &ring, starts, plane_len, sw.flags & FJ_SWATH_PACKBITS,
                              sw.x0, sw.ncols, sw.dir);
                int y0 = (int)lroundf(sw.y_um / FJ_UM_PER_COL);
                fj_nozdata_t nd;
                for (int j = 0; j < p.steps; j++) {
                    if (!fj_pass_compose(&p, j, nd)) { fprintf(stderr, "data error\n"); return 1; }
                    int c = fj_pass_ref_col(&p, j);
                    // decode: which nozzles fired -> where they are
                    for (int i = 0; i < tables.ncols; i++) {
                        const fj_ncol_t *col = &tables.col[i];
                        for (int k = 0; k < col->n; k++) {
                            const fj_nz_t *z = &col->nz[k];
                            if (!(nd[col->cart][z->nbyte] & z->nmask)) continue;
                            int row = z->byte * 8 + __builtin_ctz(z->bit);
                            int x = c + col->off, y = y0 + row;
                            if (x < 0 || x >= MAX_COLS || y >= MAX_ROWS) { fprintf(stderr, "out of page\n"); return 1; }
                            page[col->plane][y][x] = 1;
                            if (y + 1 > page_rows) page_rows = y + 1;
                        }
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
