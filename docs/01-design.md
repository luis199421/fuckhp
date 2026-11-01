# 1. Design: what we kept from OpenPrinter and what we changed

[Openprinter](https://www.crowdsupply.com/open-tools/openprinter) (Open Tools,
Paris) showed the idea people wanted: a repairable inkjet with no DRM,
refillable standard cartridges, sheets *or* roll paper and a built-in cutter.
As of its Sep 2026 update it is still "launching soon" on Crowd Supply, and
its files will be CC BY-NC-SA 4.0 (non-commercial). FreeJet takes the same
ideas and makes them buildable today at home, under the GPL.

| | Openprinter (Crowd Supply page, Nov 2026) | FreeJet FJ-1 (this repo) |
|---|---|---|
| Ink | HP 63 (US) / HP 302 (EU), black and/or colour, refillable | **HP 45 (51645A)**, black, refillable |
| Why that cartridge | common consumer cartridges | the only HP head whose drive signals are publicly reverse-engineered and proven in open projects |
| Resolution | 600 dpi B/W, 1200 dpi colour | 600 × 600 dpi |
| Speed | TBD | ~1 text page/min (estimate) |
| Paper | Letter, tabloid, 11" roll / A4, A3, 297 mm roll | Letter/A4/Legal/A5 sheets (rear slot), rolls up to 220 mm |
| Cutter | integrated | serrated tear-off edge (roll); automatic cutter on the roadmap |
| Frame | standard mechanical components, desk or wall mount | **3D-printed** plates/parts on eight 8 mm rods |
| Electronics | Raspberry Pi Zero W main board + STM32 cartridge board | Raspberry Pi Pico 2 + 2× TMC2209 + printhead board |
| User interface | 1.47" TFT + jog wheel | one button + LED (status in the computer's print dialog) |
| Connection | USB-C, USB-A (print from a stick), Wi-Fi, Bluetooth | **USB** (no kernel driver needed); network sharing through the host computer ([how](11-print-server.md)) |
| Driver | CUPS running on the printer's Pi | CUPS filter + backend and `freejet` CLI on your computer: the printer itself only needs a $5 Pico 2 |
| Power | 24 V | 12 V / 5 A |
| Size | 50 × 10 × 11 cm | ≈ 42 × 33 × 15 cm with the tray |
| Licence | CC BY-NC-SA 4.0 (non-commercial) | GPL-3.0 (commercial use allowed) |

The main thing we can't match yet is colour: nobody has published how to
drive HP 63/302 heads, and they carry ID chips. FreeJet's firmware keeps all
printhead knowledge in one place (`compose.c`, `hp45_map.c`, the head board),
so a second head type can be added later without touching the host side.

## Decisions, and why

**Cartridge: HP45.** Every inkjet printhead is driven through a matrix of
power lines and gate lines with microsecond pulses. For most cartridges
(including HP 63/302) the pinout and nozzle map are undocumented and the
cartridges carry ID chips. The HP45 is the exception: Yvo de Haas (Ytec3D)
reverse-engineered it completely and published the nozzle map, pad layout
and timing under GPL-3.0, and it has been used in open 3D-printing and
food-printing projects for years. It is still sold everywhere (it's also an
industrial coding cartridge), it's cheap remanufactured, and it refills with
a syringe. 300 nozzles at 600 dpi give a 12.7 mm swath per pass: plenty for
text and line art. Colour can be added later with a second carriage slot
once a colour head is reverse-engineered (see the roadmap).

**Paper path: flat and straight.** Feeding single sheets from a stack is
the least reliable part of any printer (pick rollers, separation pads,
skew). FJ-1 uses a straight-through path: you slide a sheet into the rear
slot along a fixed left guide, the slowly turning rollers grab it, and a
lever switch after the rollers finds the leading edge exactly. No bends, no
pick mechanism, nothing to jam. Rolls feed into the same slot.

**Mechanics: rods + printed plates.** Eight identical 8 mm × 400 mm rods
give straight, stiff, cheap references for the carriage, the rollers and
the platen. Everything else prints on a 220 × 220 mm bed in PETG. The
platen is three ribbed segments, each adjustable for height on set screws.

**Motion: steppers, no encoder.** At 600 dpi one pixel is 42.3 µm. A GT2
20-tooth pulley at 1/16 microstepping moves 12.5 µm per step, and the
firmware fires columns from the commanded position, so no linear encoder
is needed. The paper drive uses a 76:20 belt reduction (7 µm per step).

**Brains: Raspberry Pi Pico 2 (RP2350).** $5, native USB, and the PIO
state machines generate the 1.8 µs fire pulses with 33 ns resolution while
the CPU does everything else. Core 1 does nothing but fire nozzles; core 0
runs USB, motion and the job queue. It runs entirely from RAM so flash
cache misses can't disturb pulse timing.

**USB without a driver install.** The printer shows up as a USB serial
port (CDC-ACM). Linux, macOS and Windows 10+ all have that driver built in.
The "printer driver" is ordinary user-space software: a CUPS filter that
converts pages into passes, and a backend that streams them. The protocol
has framing, CRC and flow control (the USB link itself pauses the computer
when the printer's 256 KB buffer is full).

**The host does the imaging, the printer does the printhead.** The computer
rasterises, halftones and cuts pages into 300-row passes (compressed with
PackBits). The firmware knows the HP45: nozzle map, the 4.05 mm offset
between the two nozzle rows, pulse splitting. Swapping to a different head
later only changes firmware.

**Safety first for the printhead.** A heater pulse that lasts milliseconds
instead of microseconds kills nozzles instantly. The fire signal passes
through a hardware one-shot that caps it at ~3 µs whatever the software
does, the head supply is switched off whenever no job runs, and the firmware
refuses to fire without a cartridge, with low voltage, or when the head is
too hot.

## Specifications (design targets)

| | |
|---|---|
| Resolution | 600 × 600 dpi, 1 bit (halftoned grey) |
| Print width | 219 mm max (Letter/A4 with 3 mm margins) |
| Speed | ~1 page/min for a text page bidirectional, ~2–3 min for a full-coverage page |
| Carriage | 80 mm/s while printing (firmware limits it to what the head can fire) |
| Paper | 60–120 g/m² sheets, rolls ≤ 220 mm wide, ≤ 90 mm diameter |
| Ink | HP45 / 51645A, ~42 ml, ~900 pages at 5 % |
| Interface | USB full speed (CDC-ACM), VID:PID 1209:0001 (test PID) |
| Power | 12 V / 5 A brick |
| Size | ≈ 420 × 330 × 150 mm with the tray |
| Cost | ≈ $120–170 + cartridge, see the BOM |

These are calculated design targets. Nobody has built this exact machine yet;
treat the first build as a prototype and expect to adjust things.
