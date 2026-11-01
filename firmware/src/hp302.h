// HP 63 / 302 / 123 / 803 cartridge interface (black and tri-colour).
//
// Ported from Jeroen Domburg's (Sprite_tm) printercart_simple driver
// (https://github.com/Spritetm/printercart_simple, "THE BEER-WARE LICENSE" rev. 42:
// "As long as you retain this notice you can do whatever you want with this stuff.
// If we meet some day, and you think this stuff is worth it, you can buy me a beer in
// return.") - see also the Apache-2.0 PrintSpiderLib by Pavel Semenov.
//
// One firing cycle of a cartridge = 14 packets. In each packet three data lines (D1-D3)
// clock 8 bits each into the cartridge, so a cycle carries 14 x 3 x 8 = 336 nozzle bits
// ("nozzle data", 42 bytes). A waveform template (27 samples per packet at 3.33 MHz) supplies
// the select/clock lines (S1-S5, DCLK, CSYNC) and the heater power pulses (F3, F5).
#pragma once
#include <stdint.h>
#include <stdbool.h>

#define HP302_NOZDATA      42            // bytes of nozzle data per firing cycle
#define HP302_SAMPLE_HZ    3333333       // waveform sample rate
#define HP302_TPL_LEN      27            // samples per packet (template length)
#define HP302_PACKETS      14
#define HP302_IDLE         8             // idle samples after each packet
#define HP302_CYCLE_SAMPLES (HP302_PACKETS * (HP302_TPL_LEN + HP302_IDLE))   // 490 = 147 us

// black cartridge: two rows of 168 nozzles, interleaved (600 dpi together)
#define HP302_K_ROW        168
#define HP302_K_FIRST      2             // first/last nozzles of each row are not connected
#define HP302_K_LAST       164           // use nozzles 2..163 of each row -> 324 rows at 600 dpi
// colour cartridge: cyan, magenta, yellow rows side by side, nozzles at 1/300 in
#define HP302_C_FIRST      14            // the colour nozzles start around index 14
#define HP302_C_COUNT      84            // nozzles used per colour -> 168 rows at 600 dpi

enum { HP302_CART_BLACK = 0, HP302_CART_COLOR = 1 };

// Output sample bits (= GPIO offset from the first cartridge pin).
enum {
    HP302_D1 = 1 << 0, HP302_D2 = 1 << 1, HP302_D3 = 1 << 2, HP302_CSYNC = 1 << 3,
    HP302_S2 = 1 << 4, HP302_S4 = 1 << 5, HP302_S1 = 1 << 6, HP302_S5 = 1 << 7,
    HP302_DCLK = 1 << 8, HP302_S3 = 1 << 9,
    HP302_F3_K = 1 << 10, HP302_F5_K = 1 << 11,     // heater power, black cartridge
    HP302_F3_C = 1 << 12, HP302_F5_C = 1 << 13,     // heater power, colour cartridge
};
#define HP302_PINS 14

// Set the bit for black nozzle p (0..167) in row (0/1).
void hp302_set_black(uint8_t *nozdata, int p, int row);
// Set the bit for colour nozzle p (0..111) of colour c (0 cyan, 1 magenta, 2 yellow).
void hp302_set_color(uint8_t *nozdata, int p, int c);
// Where those bits are, for building lookup tables: returns byte index, *mask gets the bit.
int hp302_black_bit(int p, int row, uint8_t *mask);
int hp302_color_bit(int p, int c, uint8_t *mask);

// Append one firing cycle for cartridge `cart` to `out` (zeroed beforehand); returns samples
// written (HP302_CYCLE_SAMPLES), or 0 if nozdata is empty (nothing to fire).
int hp302_cycle(uint16_t *out, int cart, const uint8_t *nozdata);
