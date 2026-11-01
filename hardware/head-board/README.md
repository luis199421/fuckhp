# Printhead board (rides on the carriage)

A narrow 2-layer PCB, **26 × 92 mm**, one per cartridge (narrow so that up to
four sit side by side at the 28 mm cartridge pitch for grayscale/colour builds;
the top part sticks out above the carriage and carries the ribbon connector).
One face carries the 52 round gold
contact pads that the HP45's flex circuit presses against (footprint:
[`HP45_Contacts.kicad_mod`](HP45_Contacts.kicad_mod), coordinates in
[`hp45_pads.csv`](hp45_pads.csv)). The other face carries the driver chips,
so the high-current pulses travel only a few millimetres. Only logic and
power come up the 16-way ribbon cable from the main board.

> **Status:** the circuit below is complete and the firmware is written for
> it, but the PCB layout has not been drawn yet (see `docs/10-roadmap.md`).
> Order it with **ENIG** (gold) finish: the cartridge contacts need it.
> For a first test you can hand-wire the drivers on perfboard and only order
> the contact-pad PCB.

## How the HP45 is driven

* 300 nozzles = 14 **primitives** (P1–P14, the heater supply) × 22
  **addresses** (A1–A22, gates of the cartridge's built-in transistors).
* To fire nozzle *n*: switch on its address line (~12 V), then pulse its
  primitive line at ~12 V for ~1.8 µs. Up to 14 nozzles (one per primitive)
  can share one address pulse; the firmware splits them into 3 groups, as
  Ytec3D found the head misfires when all 14 heat at once.
* Address lines: 3× 74HCT595 shift registers → 3× TBD62783A source drivers.
  The firmware walks a single "1" through them (A1, A2 … A22).
* Primitive lines: 2× 74HCT595 → 2× TBD62783A. The Pico's PIO shifts in the
  14 bits for one sub-pulse, latches them, and then raises `FIRE`.
* **Safety:** `FIRE` only opens the primitive drivers through a 74HC123
  one-shot (max ~3 µs) and a NAND gate. If the firmware hangs or the cable
  is unplugged, a pulse can never be longer than the one-shot allows, and the
  pull-downs keep every driver off. A heater left on for milliseconds
  destroys the nozzle, so do not skip this.

## Parts

| Ref | Part | Package | Notes |
|---|---|---|---|
| U1, U2, U3 | 74HCT595 | SOIC-16 | address chain |
| U4, U5 | 74HCT595 | SOIC-16 | primitive chain |
| U6, U7, U8 | TBD62783AFWG | SOP-18 | address drivers (8-ch source, 50 V / 500 mA) |
| U9, U10 | TBD62783AFWG | SOP-18 | primitive drivers |
| U11 | 74HC123 | SOIC-16 | one-shot pulse limiter (one half used) |
| U12 | 74HC00 | SOIC-14 | NAND gate (one gate used, tie unused inputs to GND) |
| RN1, RN2 | 4× 10 kΩ array ×2 each | 0603×4 | pull-downs on U9/U10 inputs (595 outputs float when /OE is high) |
| R1–R22 | 4.7 kΩ | 0603 | pull-down on every address line (fast gate discharge) |
| R23 | 10 kΩ | 0603 | `FIRE` pull-down |
| R24 | 10 kΩ 1 % | 0603 | U11 Rext (sets the max pulse) |
| C1 | 680 pF C0G | 0603 | U11 Cext → ~3 µs max pulse; **check with a scope**, it must be 2.5–4 µs |
| R25 | 100 Ω | 0603 | TSR series resistor |
| C2, C3 | 470 µF 25 V low-ESR | radial 8 mm | VHD bulk, right next to U9/U10 |
| C4–C7 | 10 µF 25 V X7R | 1206 | VHD ceramics at each driver's VCC pin |
| C8–C19 | 100 nF | 0603 | one per logic chip + one at each driver |
| C20 | 10 µF | 0805 | 5 V bulk |
| J1 | 2×8 IDC box header | 2.54 mm | ribbon to the main board |
| J2 | HP45 contact pattern | — | `HP45_Contacts.kicad_mod`, ENIG |

## Connections

### J1 – ribbon cable (same order on the main board)

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | VHD (head supply, 12 V switched) | 2 | VHD |
| 3 | GND | 4 | GND |
| 5 | +5 V logic | 6 | GND |
| 7 | P_SRCLK | 8 | GND |
| 9 | P_SER (this slot's own line) | 10 | P_RCLK |
| 11 | FIRE | 12 | A_SRCLK |
| 13 | A_SER | 14 | A_RCLK |
| 15 | H_CLR_N | 16 | TSR |

### Logic

* All 74HCT595: VCC = +5 V, GND, `SRCLR#` (pin 10) = `H_CLR_N`.
* Address chain: U1 `SER` (14) = `A_SER`; U1 `QH'` (9) → U2 `SER`; U2 `QH'` → U3 `SER`.
  `SRCLK` (11) = `A_SRCLK`, `RCLK` (12) = `A_RCLK`, `OE#` (13) = GND.
* Primitive chain: U4 `SER` = `P_SER`; U4 `QH'` → U5 `SER`. `SRCLK` = `P_SRCLK`,
  `RCLK` = `P_RCLK`, `OE#` = `FIRE_EN#` (below).
* One-shot U11 (first half): `1A#` (1) = GND, `1B` (2) = `FIRE`, `1CLR#` (3) = +5 V,
  `1Cext` (14) / `1Rext/Cext` (15) = C1, R24 to +5 V per the datasheet; `1Q` (13) = `PULSE_OK`.
  Tie the unused half's inputs: `2A#` = +5 V, `2B` = GND, `2CLR#` = GND.
* U12 gate A: `FIRE_EN#` = NAND(`FIRE`, `PULSE_OK`) → U4/U5 `OE#`.
* `FIRE` has R23 to GND at the connector.
* TBD62783A: `VCC` (common source, pin 9) = VHD, `GND` (pin 10) = GND,
  `IN1..IN8` (pins 1–8), `OUT1..OUT8` (pins 18–11). Check the pinout against
  the datasheet of the exact part you buy.

### Address lines (A1–A22)

The firmware fires addresses in this order, A1 first.

| Driver | Input from | Output | HP45 line | Contact pad |
|---|---|---|---|---|
| U6 | U1 QA | OUT1 | A1 | 15 |
| U6 | U1 QB | OUT2 | A2 | 29 |
| U6 | U1 QC | OUT3 | A3 | 23 |
| U6 | U1 QD | OUT4 | A4 | 37 |
| U6 | U1 QE | OUT5 | A5 | 47 |
| U6 | U1 QF | OUT6 | A6 | 17 |
| U6 | U1 QG | OUT7 | A7 | 38 |
| U6 | U1 QH | OUT8 | A8 | 25 |
| U7 | U2 QA | OUT1 | A9 | 8 |
| U7 | U2 QB | OUT2 | A10 | 39 |
| U7 | U2 QC | OUT3 | A11 | 30 |
| U7 | U2 QD | OUT4 | A12 | 31 |
| U7 | U2 QE | OUT5 | A13 | 36 |
| U7 | U2 QF | OUT6 | A14 | 1 |
| U7 | U2 QG | OUT7 | A15 | 26 |
| U7 | U2 QH | OUT8 | A16 | 45 |
| U8 | U3 QA | OUT1 | A17 | 16 |
| U8 | U3 QB | OUT2 | A18 | 52 |
| U8 | U3 QC | OUT3 | A19 | 22 |
| U8 | U3 QD | OUT4 | A20 | 14 |
| U8 | U3 QE | OUT5 | A21 | 24 |
| U8 | U3 QF | OUT6 | A22 | 6 |

Each address line also has its 4.7 kΩ pull-down (R1–R22) to GND.

### Primitive lines (P1–P14)

Primitive *Pn* is bit *n−1* of each sub-pulse word.

| Driver | Input from | Output | HP45 line | Contact pad |
|---|---|---|---|---|
| U9 | U4 QA | OUT1 | P1 | 12 |
| U9 | U4 QB | OUT2 | P2 | 20 |
| U9 | U4 QC | OUT3 | P3 | 40 |
| U9 | U4 QD | OUT4 | P4 | 13 |
| U9 | U4 QE | OUT5 | P5 | 41 |
| U9 | U4 QF | OUT6 | P6 | 49 |
| U9 | U4 QG | OUT7 | P7 | 33 |
| U9 | U4 QH | OUT8 | P8 | 4 |
| U10 | U5 QA | OUT1 | P9 | 50 |
| U10 | U5 QB | OUT2 | P10 | 46 |
| U10 | U5 QC | OUT3 | P11 | 3 |
| U10 | U5 QD | OUT4 | P12 | 21 |
| U10 | U5 QE | OUT5 | P13 | 7 |
| U10 | U5 QF | OUT6 | P14 | 32 |

* GND pads: 2, 5, 9, 10, 11, 18, 19, 34, 35, 42, 43, 44, 48, 51
* TSR pad: 27 
* 10X (ID) pad: 28 (not connected)
* TSR (the cartridge's thermal sense resistor) → R25 → J1 pin 16. The 1 kΩ
  pull-up to 3.3 V is on the main board, so a missing cartridge or ribbon
  reads as "no head" (ADC ≈ 4095).
* All GND pads go to the ground pour. Use wide copper for VHD and GND: each
  sub-pulse draws roughly 1.5–2.5 A for 1.8 µs (5 heaters × ~0.4 A).

## Where the numbers come from

The nozzle-to-line map, the pad positions and the drive figures (≈12 V,
≈1.8 µs, 3 sub-pulses, 4.05 mm between the two nozzle rows) come from Yvo de
Haas' open-source HP45 work (Ytec3D, GPL-3.0):
[HP45-standalone-V4](https://github.com/yvodehaas/HP45-standalone-V4) and
[HP45-standalone-controller-V4.02](https://github.com/yvodehaas/HP45-standalone-controller-V4.02).
We corrected 7 entries of the published address table that mapped two
nozzles onto the same heater (see `tools/hp45_tables.py`). The pad numbers
here are the connector pin numbers of that design.
