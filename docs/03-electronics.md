# 3. Electronics

One main board does everything: a Raspberry Pi Pico 2, two stepper drivers,
and the small cartridge interface. The cartridges themselves contain the
nozzle-select logic, so they only need 12 signals plus 2 heater lines each.
It all fits on a 90 × 70 mm perfboard in the electronics tray under the platen.
A flat cable goes up to the carriage, where the contact flex presses on the
cartridges.

```
 12 V 5 A brick ─[3 A polyfuse]─┬─[1N5822 to GND: blows the fuse if reversed]
                                ├─► TMC2209 x2 (VM) ──► NEMA17 carriage, NEMA17 paper feed
                                ├─► MP1584 → 5.0 V ─► Pico 2 VSYS (via 1N5819), 74HCT logic, CD4504 VCC
                                ├─► MP1584 → 9.0 V ─► CD4504 #1 VDD  (D1 D2 D3 CSYNC at 9 V)
                                └─► IRF9540N head switch (GP5, soft start)
                                        └─► MT3608 boost → 16.0 V ─► CD4504 #2 VDD (S1-S5, DCLK at 16 V)
                                                                  └► 4 heater switches (F3/F5 x 2 cartridges)
 USB ── Pico 2 ── GP6..GP19 (14 lines, PIO) ──► level shifters / heater switches ──► flat cable ──► contact flex ──► HP 302
```

## Pico 2 pin map

Same as [`firmware/src/config.h`](../firmware/src/config.h).

| GPIO | Signal | Connects to |
|---|---|---|
| GP0 / GP1 | X_STEP / X_DIR | TMC2209 #1 |
| GP2 / GP3 | Y_STEP / Y_DIR | TMC2209 #2 |
| GP4 | MOTOR_EN_N | both TMC2209 EN (low = on), 10 kΩ pull-up |
| GP5 | HEAD_PWR | 2.2 kΩ → 2N3904 base (16 V rail switch) |
| GP6, GP7, GP8 | D1, D2, D3 | CD4504 #1 inputs (→ 9 V) |
| GP9 | CSYNC | CD4504 #1 input (→ 9 V) |
| GP10, GP11, GP12, GP13 | S2, S4, S1, S5 | CD4504 #2 inputs (→ 16 V) |
| GP14 | DCLK | CD4504 #2 input (→ 16 V) |
| GP15 | S3 | CD4504 #2 input (→ 16 V) |
| GP16, GP17 | F3, F5 black | heater switches, black cartridge |
| GP18, GP19 | F3, F5 colour | heater switches, colour cartridge |
| GP20 | X_HOME_N | home microswitch (service station) to GND, 100 nF |
| GP21 | PAPER_N | paper lever switch to GND (closed = paper), 100 nF |
| GP22 | BUTTON_N | front button to GND |
| GP26 / ADC0 | VHD sense | 16 V rail via 100 kΩ / 15 kΩ, 100 nF |
| GP27 | LED | 330 Ω → LED → GND |

The PIO plays the 14 cartridge lines as one 3.33 MHz waveform from DMA.
Their order is fixed (see `hp302.h`), so keep GP6–GP19 exactly as listed.

## Cartridge interface

| Part | Qty | Notes |
|---|---|---|
| CD4504BE (DIP-16) | 2 | hex level shifter. VCC = 5 V (input side, TTL mode via the MODE pin, check the datasheet), VDD = 9 V (#1) or 16 V (#2) |
| MP1584 module | 1 | set to 9.0 V before connecting |
| MT3608 module | 1 | 12 V in → set to 16.0 V before connecting; its input is the switched 12 V |
| AO3401A P-MOSFET on a SOT-23 adapter | 4 | heater switches, source to 16 V through 2.7 Ω, gate 1 kΩ to source |
| 2N7000 | 4 | pulls each P-FET gate low |
| 74HCT123 | 2 | four one-shots, one per heater line: **pulse limiter** |
| 74HCT08 | 1 | heater enable = GPIO AND one-shot |
| 100 Ω | 10 | in series with each level-shifter output (damps ringing on the cable) |
| 4.7 kΩ | 4 | heater lines to GND (off = 0 V) |
| 470 µF 25 V low-ESR + 10 µF | 1 + 2 | on the 16 V rail, next to the heater switches |
| 100 nF | 6 | one per chip |

**Data and select lines.** CD4504 #1 lifts D1, D2, D3 and CSYNC to 9 V.
CD4504 #2 lifts S1–S5 and DCLK to 16 V. Both cartridges get these lines in
parallel; only the heater lines are separate per cartridge. The firmware fires
the black and the colour cartridge one after the other in each column, so the
shared lines never carry two patterns at once.

**Heater lines (F3, F5) and their pulse limiter.** These carry the heater
current, so a stuck-high line burns nozzles. Others who drove these
cartridges report damage from pulses longer than ~10 µs. Each heater line is:

```
 GPxx ──┬─────────────► 74HCT08 A ─┐
        └─► 74HCT123 B (A# = GND, CLR# = 5 V, Rx 10 kΩ, Cx 680 pF ≈ 3 µs) ──Q─► 74HCT08 B
                                                     74HCT08 Y ─► 2N7000 gate (100 kΩ to GND)
 16 V ── 2.7 Ω ──┬── AO3401 source           2N7000 drain ── AO3401 gate (1 kΩ to source)
                  └── AO3401 drain ─► Fx out (4.7 kΩ to GND) ─► cable ─► cartridge
```

The firmware's pulses are ~2 µs (from the waveform templates). The one-shot cuts
anything longer than ~3 µs, even if the Pico hangs with a line high. Check it
with a scope before connecting a cartridge (see the bring-up steps below).

**16 V rail switch.** As before: IRF9540N high-side on the 12 V feeding the
MT3608, gate pulled up with 47 kΩ, pulled down through 10 kΩ by a 2N3904 from
GP5, 220 nF gate–source for a ~2 ms soft start. The firmware switches it on only
during jobs. At boot GP5 is driven low first.

## Cartridge contacts: salvage them

The cartridges have a small flex with gold pads on the back. The reliable way
to contact them is to **salvage the carriage's contact flex and its flat cable
from a dead HP DeskJet** that takes HP 63/302/123/803 cartridges: 2130, 2620,
2630, 3630, 3830, 4520, ENVY 4500… These printers are thrown away by the
million. Cut the carriage's plastic away around the flex (or keep the flex on its
spring/foam backing) and screw it into the printed carriage's flex recess. Keep the
flat cable and its board-side connector, and land the cable on the main board.

**Identify the signals before powering anything.** I could not find a
verified pad-by-pad table I can reproduce here. Use the MagicBrush write-up
by Sprite_tm ([spritesmods.com/?art=magicbrush](https://spritesmods.com/?art=magicbrush),
pinout page) and the [PrintSpider cartridge module](https://hackaday.io/project/176931-hp-printer-cartridge-control-module):

1. With a multimeter, find which flat-cable wire reaches which cartridge pad
   (continuity through the flex, cartridge removed).
2. Label the pads D1, D2, D3, CSYNC, S1–S5, DCLK, F3, F5 and GND from that pinout.
3. Double-check the GND pads: they connect to each other inside a cartridge
   (measure on an empty cartridge).
4. Wire D/CSYNC/S/DCLK of both cartridge positions in parallel, and F3/F5 of each
   position to its own heater switch.

## Steppers, power, switches

Unchanged from the black-only design. TMC2209 StepSticks with MS1/MS2 tied to
3.3 V (1/16 step) and current set with the trimmer (≈0.6 A carriage, ≈0.7 A
feed). The MP1584s and the MT3608 must be adjusted **before** they are connected.
Switches are NO to GND with 100 nF across them.

## Bring-up (before a cartridge goes in)

1. Power with no Pico: check 5 V, 9 V, and that 16 V is **0 V**.
2. Plug in the Pico over USB, flash the firmware, run `freejet status`.
3. 12 V on: `freejet home`, `freejet feed 20`.
4. Contact flex connected but **no cartridge**. Scope on an F line and on DCLK,
   then run `freejet fire black --count 20`. Check: the 16 V rail comes up, DCLK/S
   swing 0–16 V, D/CSYNC 0–9 V, and each F pulse is ~2 µs and never longer than
   ~3 µs (pull the GPIO high by hand: the one-shot must still cut it).
5. Insert the cartridge, `freejet clean`, `freejet test nozzles`.
