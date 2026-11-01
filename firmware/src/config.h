// FreeJet FJ-2 main board pin map and fixed constants (Raspberry Pi Pico 2 / RP2350).
// Matches docs/03-electronics.md - change both together.
#pragma once

// --- motion -----------------------------------------------------------------
#define PIN_X_STEP      0
#define PIN_X_DIR       1
#define PIN_Y_STEP      2
#define PIN_Y_DIR       3
#define PIN_MOTOR_EN_N  4    // both TMC2209 EN pins, low = enabled
#define PIN_HEAD_PWR    5    // high = cartridge heater supply (12 V -> 16 V boost) on

// --- cartridges: 14 consecutive GPIOs, played by the PIO (bit order = hp302.h) -------
//   GP6 D1, GP7 D2, GP8 D3, GP9 CSYNC, GP10 S2, GP11 S4, GP12 S1, GP13 S5, GP14 DCLK,
//   GP15 S3, GP16 F3 black, GP17 F5 black, GP18 F3 colour, GP19 F5 colour
#define PIN_CART0       6

// --- switches / UI ------------------------------------------------------------
#define PIN_X_HOME_N    20   // carriage home microswitch (service station) to GND
#define PIN_PAPER_N     21   // paper lever switch before the feed roller (paper = low)
#define PIN_BUTTON_N    22   // front panel button to GND
#define PIN_LED         27   // front panel LED (on-board LED is driven too)

// --- analog ----------------------------------------------------------------------
#define PIN_ADC_VHD     26   // ADC0: 16 V heater rail through a 100k/15k divider
#define ADC_CH_VHD      0
#define VHD_DIVIDER     (115.0f / 15.0f)

// --- timing ------------------------------------------------------------------
#define MOTION_TICK_HZ  50000      // stepper ISR rate (max 25k steps/s per axis)
#define PIN_TICK_SLICE  28         // a PWM slice used only as a timer (pin not used for PWM)

// --- buffers -----------------------------------------------------------------
#define RING_BYTES      (1u << 18) // 256 KiB of compressed swath data
#define OP_QUEUE_LEN    32

#define MODEL_NAME      "FJ-2"
