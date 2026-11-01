// FreeJet FJ-1 main board pin map and fixed constants (Raspberry Pi Pico 2 / RP2350).
// Matches docs/03-electronics.md - change both together.
#pragma once

// --- motion -----------------------------------------------------------------
#define PIN_X_STEP      2
#define PIN_X_DIR       3
#define PIN_Y_STEP      4
#define PIN_Y_DIR       5
#define PIN_MOTOR_EN_N  6    // both TMC2209 EN pins, low = enabled
#define PIN_X_HOME_N    7    // carriage home microswitch to GND (pressed = low)
#define PIN_PAPER_N     8    // paper lever microswitch after the input rollers (paper = low)
#define PIN_BUTTON_N    9    // front panel button to GND
#define PIN_HEAD_PWR    10   // high = printhead supply (VHD) on
#define PIN_LED         11   // front panel LED (on-board LED is driven too)

// --- printhead board (16-way ribbon) -------------------------------------------
#define PIN_H_CLR_N     12   // clears both shift-register chains
#define PIN_A_SER       13   // address chain (3x 74HCT595 -> 3x TBD62783A -> A1..A22)
#define PIN_A_SRCLK     14
#define PIN_A_RCLK      15
#define PIN_P_SER0      16   // primitive chain data, one line per cartridge slot: GP16..GP19
                             // (2x 74HCT595 -> 2x TBD62783A -> P1..P14 on each head board), PIO OUT x4
#define PIN_P_SRCLK     20   // PIO side-set (shared by all head boards)
#define PIN_P_RCLK      21   // PIO SET base (shared)
#define PIN_FIRE        22   // PIO SET base + 1 -> one-shot on each board -> 595 /OE (shared)
#define MAX_HEADS       4

// --- analog ----------------------------------------------------------------------
#define PIN_TSR_SEL0    0    // 74HC4051 select lines: which cartridge's TSR goes to ADC0
#define PIN_TSR_SEL1    1    // (single-cartridge builds can leave the mux out: slot 0 = no select)
#define PIN_ADC_TSR     26   // ADC0: cartridge thermal sense resistor (1k pull-up to 3V3, via mux)
#define PIN_ADC_VHD     27   // ADC1: head supply through 100k/15k divider
#define ADC_CH_TSR      0
#define ADC_CH_VHD      1
#define VHD_DIVIDER     (115.0f / 15.0f)

// --- timing ------------------------------------------------------------------
#define MOTION_TICK_HZ  50000      // stepper ISR rate (max 25k steps/s per axis)
#define PIO_FIRE_HZ     30000000   // fire state machine clock (33 ns resolution)
#define PULSE_NS_LIMIT  2400       // never exceed, whatever the parameter says

// --- buffers -----------------------------------------------------------------
#define RING_BYTES      (1u << 18) // 256 KiB of compressed swath data
#define OP_QUEUE_LEN    32

#define MODEL_NAME      "FJ-1"
