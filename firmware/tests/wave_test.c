// Checks hp302.c against Sprite_tm's original printcart_generate_waveform (copied below
// unchanged except for the ESP32 I2S word swap), the nozzle bit maps for collisions, and
// the safety-relevant shape of the waveform (heater pulse lengths).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/hp302.h"

/* --- original (beer-ware, Jeroen Domburg) --------------------------------------- */
#define TP_BIT_TOGGLE1 (1<<0)
#define TP_BIT_TOGGLE2 (1<<1)
#define TP_CSYNC_LAST (1<<14)
#define TP_CSYNC_NORM (1<<15)
#define OUT_D1 (1<<0)
#define OUT_D2 (1<<1)
#define OUT_D3 (1<<2)
#define OUT_CSYNC (1<<3)
#define OUT_F3 (1<<10)
#define OUT_F5 (1<<11)
static uint16_t waveform_tpl_color_b[]={0x0,0xc000,0xc101,0xc141,0x42,0x2,0x4101,0x4111,0x12,0x4002,0x4101,0x4301,0x602,0x4402,0x4501,0x4521,0x422,0x402,0x4000,0x4000,0x4080,0x880,0x800,0x800,0x800,0x800,0x800};
static uint16_t waveform_tpl_black_b[]={0x0,0xc000,0xc101,0xc141,0x42,0x2,0xc101,0xc111,0x12,0x4002,0x4101,0x4301,0x602,0x402,0x501,0x521,0x422,0x402,0x4002,0x4000,0x4080,0x880,0x800,0x800,0x800,0x800,0x800};
static int orig(uint16_t *w, const uint16_t *tp, const uint8_t *nozdata, int l) {
	const uint8_t *d1data=&nozdata[0]; const uint8_t *d2data=&nozdata[14]; const uint8_t *d3data=&nozdata[28];
	int p=0; int is_empty=1;
	for (int i=0; i<42; i++) if (nozdata[i]!=0) { is_empty=0; break; }
	for (int j=0; j<14; j++) {
		uint8_t bit=0; int ov=0; uint16_t mask=0xffff;
		mask&=~(OUT_CSYNC|OUT_D1|OUT_D2|OUT_D3);
		int power=(d1data[j]|d2data[j]|d3data[j]);
		if ((power&0x0f)==0x00) mask&=~OUT_F3;
		if ((power&0xf0)==0x00) mask&=~OUT_F5;
		uint16_t csync_sel=0;
		if (j==13) csync_sel=TP_CSYNC_LAST; else csync_sel=TP_CSYNC_NORM;
		for (int i=0; i<l; i++) {
			if (is_empty) { w[p++]=0; continue; }
			uint16_t v=tp[i];
			if ((v&(TP_BIT_TOGGLE1|TP_BIT_TOGGLE2))!=ov) { if (!bit) bit=1; else bit<<=1; ov=v&(TP_BIT_TOGGLE1|TP_BIT_TOGGLE2); }
			int en=v&(TP_BIT_TOGGLE1|TP_BIT_TOGGLE2);
			v&=mask;
			if (en) { if (!(d1data[j]&bit)) v|=OUT_D1; if (!(d2data[j]&bit)) v|=OUT_D2; if (!(d3data[j]&bit)) v|=OUT_D3; }
			if (v&csync_sel) v|=OUT_CSYNC;
			w[p++]=v;
		}
		p+=8;
	}
	return (p+1)&~1;
}
/* -------------------------------------------------------------------------------- */

int main(void) {
    int fails = 0;
    srand(1);
    for (int t = 0; t < 2000; t++) {
        uint8_t nd[42];
        for (int i = 0; i < 42; i++) nd[i] = (rand() % 4) ? (uint8_t)rand() : 0;
        if (t % 50 == 0) memset(nd, 0, 42), nd[rand() % 42] = 1u << (rand() % 8);
        for (int cart = 0; cart < 2; cart++) {
            uint16_t a[600] = {0}, b[600] = {0};
            int na = hp302_cycle(a, cart, nd);
            orig(b, cart ? waveform_tpl_color_b : waveform_tpl_black_b, nd, 27);
            for (int i = 0; i < na; i++) {
                uint16_t mine = a[i];
                if (cart) mine = (mine & ~(HP302_F3_C | HP302_F5_C)) | ((mine & HP302_F3_C) ? OUT_F3 : 0) | ((mine & HP302_F5_C) ? OUT_F5 : 0);
                uint16_t ref = b[i] & 0x0FFF;      // only 12 real output lines in the original
                if (mine != ref) { if (fails < 5) printf("mismatch cart %d sample %d: %04x vs %04x\n", cart, i, mine, ref); fails++; }
                // heater lines of the other cartridge must never be on
                if (cart == 0 && (a[i] & (HP302_F3_C | HP302_F5_C))) fails++;
                if (cart == 1 && (a[i] & (HP302_F3_K | HP302_F5_K))) fails++;
            }
            // heater pulses: no F pulse longer than 8 samples (2.4 us)
            for (int f = 10; f < 14; f++) {
                int run = 0;
                for (int i = 0; i < na; i++) { run = (a[i] >> f & 1) ? run + 1 : 0; if (run > 8) { fails++; break; } }
            }
            if (na && na != HP302_CYCLE_SAMPLES) fails++;
        }
    }
    // nozzle maps: every nozzle has its own bit
    uint8_t seen[2][42] = {{0}};
    for (int q = 0; q < 2; q++) for (int p = 0; p < HP302_K_ROW; p++) {
        uint8_t m; int byte = hp302_black_bit(p, q, &m);
        if (seen[0][byte] & m) { printf("black collision %d/%d\n", p, q); fails++; }
        seen[0][byte] |= m;
    }
    for (int c = 0; c < 3; c++) for (int p = 0; p < 112; p++) {
        uint8_t m; int byte = hp302_color_bit(p, c, &m);
        if (seen[1][byte] & m) { printf("colour collision %d/%d\n", p, c); fails++; }
        seen[1][byte] |= m;
    }
    printf("%s: %d failures\n", fails ? "FAIL" : "ok", fails);
    return fails != 0;
}
