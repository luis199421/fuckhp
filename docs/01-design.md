# 1. Design: built on what already works

FreeJet borrows its concept from projects that already work, and keeps what
makes each of them simple:

* **[Openprinter](https://www.crowdsupply.com/open-tools/openprinter)** (Open Tools):
  standard HP 63/302 cartridges, sheets *or* roll paper, a minimal
  paper path with **one feed roller**, the roll sitting in slots in the chassis,
  pre-assembled modules dropped into a plain frame.
* **[MagicBrush / PrintSpider](https://spritesmods.com/?art=magicbrush)** by Sprite_tm
  and the [PrintSpider cartridge module](https://hackaday.io/project/176931-hp-printer-cartridge-control-module):
  driving those cartridges directly from a microcontroller with 12 signals, a
  couple of level shifters and a boost converter. FreeJet's waveform code is a
  port of [Sprite_tm's beer-ware driver](https://github.com/Spritetm/printercart_simple).
* **3D printers:** steel rods, LM8UU bearings, GT2 belts, NEMA17 + TMC2209, a
  printed frame: cheap, everywhere, well understood.

| | Openprinter (Crowd Supply page, Nov 2026) | FreeJet FJ-2 (this repo) |
|---|---|---|
| Cartridges | HP 63 (US) / HP 302 (EU), black and/or colour | **same**: HP 63/302/123/803, black and/or tri-colour, refillable |
| Resolution | 600 dpi B/W, 1200 dpi colour | 600 × 600 dpi black, 600 × 300 dpi colour |
| Paper | Letter, tabloid, 11" roll / A4, A3, 297 mm roll | Letter/A4/Legal/A5 sheets, rolls up to 220 mm wide |
| Paper drive | one roller | **one roller** + 4 spring-steel leaves; roll in slots in the side plates |
| Cutter | integrated | tear-off edge |
| Frame | sheet-metal chassis | **3D-printed** plates and platen beam on 3 steel rods |
| Electronics | Raspberry Pi Zero W + STM32 cartridge board | **one** board: Raspberry Pi Pico 2 + 2× TMC2209 + level shifters |
| Connection | USB-C, USB-A, Wi-Fi, Bluetooth | USB (no kernel driver); network via the host computer's CUPS |
| Driver | CUPS on the printer | CUPS filter + backend, `freejet` CLI (Linux/macOS/Windows) |
| Power | 24 V | 12 V / 5 A |
| Licence | CC BY-NC-SA 4.0 (non-commercial) | GPL-3.0 (commercial use allowed) |

## Decisions, and why

**Cartridges: HP 63/302 family.** These are some of the cheapest, most widely
sold cartridges, they include a fresh printhead, and they refill with a
syringe. They have their nozzle-select logic built in, so a printer drives
them with only 12 signal lines plus 2 heater lines per cartridge, at 9 V and
16 V. That electrical interface has been reverse-engineered and published
(MagicBrush, PrintSpider), and Openprinter uses the same cartridges. Colour
comes from the tri-colour cartridge next to the black one: two cartridges, no
custom inks. (An earlier FreeJet revision used the HP 45; it needed 36 drive
lines, a 10-chip head board and four refilled cartridges for colour. See the git
history.)

**One feed roller, close to the printhead.** Like Openprinter: a single
driven roller 25 mm behind the nozzles, with four thin spring-steel leaves pressing
the paper onto its tires. There are no exit rollers, star wheels or pinch shaft.
The cost is that a single sheet can't be printed in its last ~22 mm, because the
roller has let go of it. That is less than a normal 25 mm document margin, and the
print dialog knows about it. Roll paper prints right to the cut.

**Straight paper path, roll in the plates.** Sheets slide in on the rear
tray along a fixed left guide until they rest against the roller. The roll's
spindle drops into keyhole slots in the side plates and feeds into the same path.

**Printed frame, steel only where it counts.** Two side plates, a bolted
platen beam that also squares the frame, and three 8 mm rods: two carriage
rails and the roller shaft.

**Brains: Raspberry Pi Pico 2.** $5, native USB. A 2-instruction PIO program
plays the cartridge waveform (14 lines at 3.33 MHz) straight from DMA while the
CPU does everything else. The black and colour cartridges share their data and
clock lines and fire one after the other in each 1/600" column, about 300 µs
for both.

**USB without a driver install.** The printer is a USB serial device. The
"driver" is user-space software: a CUPS filter that separates, halftones and
cuts pages into passes, and a backend that streams them with flow control.

**Safety for the cartridge.** Every heater line passes through a hardware
one-shot that cuts it after ~3 µs, whatever the software does. The 16 V heater
rail is only on during jobs. The firmware's waveform is checked in the
test-suite: no heater pulse longer than 2.4 µs.

## Specifications (design targets)

| | |
|---|---|
| Resolution | black 600 × 600 dpi (324 nozzles, 13.7 mm per pass); colour 600 × 300 dpi (3 × 84 nozzles, 7.1 mm per pass) |
| Print width | 219 mm max |
| Margins | 3 mm; sheets: 22 mm at the bottom |
| Speed | ~1 page/min black text (bidirectional); colour pages slower (narrower passes) |
| Paper | 60–120 g/m² sheets, rolls ≤ 220 mm wide, ≤ 90 mm diameter |
| Interface | USB full speed (CDC-ACM), VID:PID 1209:0001 (test PID) |
| Power | 12 V / 5 A |
| Size | ≈ 42 × 30 × 16 cm (black only), ≈ 48 cm wide with black + colour |
| Cost | ≈ $99 in parts + cartridges, see the BOM |

These are calculated targets. Nobody has built this exact machine yet.

## Printed vs bought

Print a part unless printing it would make the printer less reliable.

| Bought | Why it isn't printed |
|---|---|
| 3× 8 mm steel rods | straightness sets the head gap and the roller contact over the whole width |
| 3× LM8UU, 2× 608 | printed bushings wear and develop play: wobbly lines, feed drift |
| 2× NEMA17, 20T metal pulleys, idler, belts | printed pulleys slip on a 5 mm motor shaft; nothing printable replaces a belt |
| 4 spring-steel leaves, 1 small spring | plastic springs creep: the paper pressure would fade |
| switches, button, LED, M3 screws | cheap, standard, reliable |
| contact flex | the cartridge pads need gold contacts with the right spring: salvaged from a dead DeskJet |

Printed: side plates (with roll slots), platen beam, carriage, roller hubs and
TPU tires, 60T pulley, leaf bar, collars, service station (TPU cap and wiper),
sensor bracket, electronics tray, paper tray, roll spindle and cores.
