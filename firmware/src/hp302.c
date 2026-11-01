// See hp302.h for origin and licence of this code (Sprite_tm, beer-ware).
#include "hp302.h"
#include <string.h>

// template bits (as in the original driver)
#define TP_BIT_TOGGLE1 (1 << 0)
#define TP_BIT_TOGGLE2 (1 << 1)
#define TP_F3          (1 << 10)
#define TP_F5          (1 << 11)
#define TP_CSYNC_LAST  (1 << 14)
#define TP_CSYNC_NORM  (1 << 15)
#define TP_PASS_MASK   0x03F0          // S2 S4 S1 S5 DCLK S3: copied straight to the outputs

// "B" waveforms of the original driver (newer cartridges)
static const uint16_t tpl_color[HP302_TPL_LEN] = {
    0x0, 0xc000, 0xc101, 0xc141, 0x42, 0x2, 0x4101, 0x4111, 0x12, 0x4002, 0x4101, 0x4301, 0x602,
    0x4402, 0x4501, 0x4521, 0x422, 0x402, 0x4000, 0x4000, 0x4080, 0x880, 0x800, 0x800, 0x800, 0x800, 0x800};
static const uint16_t tpl_black[HP302_TPL_LEN] = {
    0x0, 0xc000, 0xc101, 0xc141, 0x42, 0x2, 0xc101, 0xc111, 0x12, 0x4002, 0x4101, 0x4301, 0x602,
    0x402, 0x501, 0x521, 0x422, 0x402, 0x4002, 0x4000, 0x4080, 0x880, 0x800, 0x800, 0x800, 0x800, 0x800};

static const int8_t color_bo[3][14] = {
    {8, 13, 4, 9, 0, 5, 10, 1, 6, 11, 2, 7, 12, 3},
    {11, 2, 7, 12, 3, 8, 13, 4, 9, 0, 5, 10, 1, 6},
    {0, 5, 10, 1, 6, 11, 2, 7, 12, 3, 8, 13, 4, 9}};

typedef struct { uint8_t c, bit, order; } bw_nozinfo_t;
static const bw_nozinfo_t black_ni[24] = {
    {2, 0, 1}, {2, 1, 1}, {1, 0, 1}, {1, 1, 1}, {0, 0, 1}, {0, 1, 1}, {2, 4, 1}, {2, 5, 1},
    {1, 4, 1}, {1, 5, 1}, {0, 4, 1}, {0, 5, 1}, {2, 2, 0}, {2, 3, 0}, {1, 2, 0}, {1, 3, 0},
    {0, 2, 0}, {0, 3, 0}, {2, 6, 0}, {2, 7, 0}, {1, 6, 0}, {1, 7, 0}, {0, 6, 0}, {0, 7, 0}};
static const int8_t black_bo[2][14] = {
    {4, 12, 10, 2, 8, 0, 6, 13, 7, 1, 9, 3, 11, 5},
    {13, 7, 1, 9, 3, 11, 5, 4, 12, 10, 2, 8, 0, 6}};

int hp302_color_bit(int p, int c, uint8_t *mask) {
    if (p < 0 || p >= 8 * 14 || c < 0 || c > 2) { *mask = 0; return 0; }
    *mask = (uint8_t)(1u << (p / 14));
    return color_bo[c][p % 14] + 14 * c;
}

int hp302_black_bit(int p, int row, uint8_t *mask) {
    if (p < 0 || p >= HP302_K_ROW || row < 0 || row > 1) { *mask = 0; return 0; }
    if (row) p += HP302_K_ROW;
    int j = p / 14, k = 13 - (p % 14);
    *mask = (uint8_t)(1u << black_ni[j].bit);
    return black_ni[j].c * 14 + black_bo[black_ni[j].order][k];
}

void hp302_set_black(uint8_t *l, int p, int row) { uint8_t m; int b = hp302_black_bit(p, row, &m); l[b] |= m; }
void hp302_set_color(uint8_t *l, int p, int c) { uint8_t m; int b = hp302_color_bit(p, c, &m); l[b] |= m; }

int hp302_cycle(uint16_t *out, int cart, const uint8_t *nozdata) {
    const uint16_t *tp = cart == HP302_CART_BLACK ? tpl_black : tpl_color;
    const uint8_t *d1 = &nozdata[0], *d2 = &nozdata[14], *d3 = &nozdata[28];
    int any = 0;
    for (int i = 0; i < HP302_NOZDATA; i++) any |= nozdata[i];
    if (!any) return 0;
    uint16_t f3 = cart == HP302_CART_BLACK ? HP302_F3_K : HP302_F3_C;
    uint16_t f5 = cart == HP302_CART_BLACK ? HP302_F5_K : HP302_F5_C;
    int p = 0;
    for (int j = 0; j < HP302_PACKETS; j++) {
        uint8_t bit = 0;
        int ov = 0;
        int power = d1[j] | d2[j] | d3[j];
        uint16_t csync_sel = j == HP302_PACKETS - 1 ? TP_CSYNC_LAST : TP_CSYNC_NORM;
        for (int i = 0; i < HP302_TPL_LEN; i++) {
            uint16_t v = tp[i];
            if ((v & (TP_BIT_TOGGLE1 | TP_BIT_TOGGLE2)) != ov) {   // next data bit
                bit = bit ? (uint8_t)(bit << 1) : 1;
                ov = v & (TP_BIT_TOGGLE1 | TP_BIT_TOGGLE2);
            }
            int en = v & (TP_BIT_TOGGLE1 | TP_BIT_TOGGLE2);
            uint16_t o = v & TP_PASS_MASK;
            // heater power only for the half of the packet that has nozzles to fire
            if ((v & TP_F3) && (power & 0x0f)) o |= f3;
            if ((v & TP_F5) && (power & 0xf0)) o |= f5;
            if (en) {                                            // data is active-low
                if (!(d1[j] & bit)) o |= HP302_D1;
                if (!(d2[j] & bit)) o |= HP302_D2;
                if (!(d3[j] & bit)) o |= HP302_D3;
            }
            if (v & csync_sel) o |= HP302_CSYNC;
            out[p++] = o;
        }
        p += HP302_IDLE;     // idle (zero) samples after each packet
    }
    return p;
}
