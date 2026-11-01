# FreeJet FJ-2: an open DIY inkjet printer

A paper printer you print and build yourself: a 3D-printed frame, standard
**HP 63 / HP 302** cartridges (black and/or tri-colour, cheap, everywhere,
refillable), a $5 Raspberry Pi Pico 2 for brains, and its own driver over
USB. The concept comes from [Openprinter](https://www.crowdsupply.com/open-tools/openprinter)
(Open Tools): same cartridges, one feed roller, the roll sitting in slots in
the frame. The cartridge driving comes from Sprite_tm's
[MagicBrush/PrintSpider](https://spritesmods.com/?art=magicbrush) work.
FreeJet is buildable today and GPL-licensed.

![FreeJet FJ-2 assembly animation](docs/img/assembly_animation.gif)

*Assembly in 14 steps, then a print ([MP4](docs/img/assembly_animation.mp4)). Rendered from the
real CAD files with `python3 tools/render_animation.py`.*

| | |
|---|---|
| Prints | black 600 × 600 dpi, grayscale (halftoned), colour 600 × 300 dpi with the tri-colour cartridge; [how](docs/12-grayscale-and-color.md) |
| Paper | Letter / A4 / Legal / A5 sheets on a straight rear tray, or rolls up to 220 mm |
| Ink | HP 63 / 302 (also 123 / 803) black and tri-colour, refill with a syringe |
| Connection | USB; no kernel driver to install on Linux, macOS or Windows |
| Software | CUPS print queue (Linux), `freejet` command-line tool (all systems); share it over Wi-Fi from the computer it's plugged into |
| Build | 28 printed part types (PETG + a little TPU); bought mechanics are only 3 steel rods, 5 bearings, 2 motors, belts, 4 spring-steel leaves, 2 switches and M3 screws ([why](docs/01-design.md#printed-vs-bought)) |
| Cost | about **$99 in parts + $15 black / $18 colour cartridge** ([BOM](docs/bom.csv)) |

> **Status: design complete, not yet built.** The driver, firmware and CAD
> are written and tested in software (see [status](docs/10-roadmap.md)),
> but no physical prototype exists yet. Before the first build, a real
> cartridge and a salvaged contact flex need measuring, and the flex's
> pad-to-signal mapping must be checked against the MagicBrush write-up.

## How it works

```
 your PC                                    FreeJet FJ-2
 ┌───────────────────────────┐   USB        ┌──────────────────────────────────────────┐
 │ app → CUPS → rastertofreejet ─────────────► Pico 2  core0: USB, job queue, steppers   │
 │      (600 dpi, colour      │  frames +   │         core1: compose nozzle data        │
 │       separation, halftone,│  CRC, flow  │         PIO + DMA: 14-line waveform       │
 │       passes, PackBits)    │  control    │   level shifters (9 V / 16 V) + heater    │
 │ or: freejet print doc.pdf  │             │   switches → contact flex → HP 302 K + C  │
 └───────────────────────────┘             └──────────────────────────────────────────┘
```

* The **carriage** runs on two rods, belt-driven, and fires one 1/600"
  column at a time from its commanded position (no encoder needed).
* The **paper** goes straight through: rear tray → under the leaf springs →
  **one** rubber feed roller → ribbed platen → out the front. A lever switch
  finds the sheet's edge exactly. Single sheets keep a ~22 mm bottom margin,
  because the roller lets go of them there; roll paper prints to the cut.
* The **HP 302 cartridges** have their nozzle-select logic inside. The Pico's
  PIO plays a 14-line, 3.33 MHz waveform from DMA (ported sample-exact from
  Sprite_tm's driver): data, select and clock lines shared by both cartridges,
  plus two heater lines each. Black fires, then colour, in every column.
  Hardware one-shots cut any heater pulse after ~3 µs, whatever the software does.
* A **service station** caps the cartridges when parked, wipes them, and has a
  spittoon to clear the nozzles before each page.

## Repository

| Folder | What |
|---|---|
| [`docs/`](docs) | everything you need to build and use it (start below) |
| [`cad/`](cad) | parametric OpenSCAD parts, assembly, collision check; ready STLs in `cad/stl` (one cartridge) and `cad/stl-kcmy` (black + colour) |
| [`firmware/`](firmware) | Pico 2 firmware (C, Pico SDK) + PC tests: waveform vs. the original driver, data path simulator |
| [`host/`](host) | `freejet` Python package: CLI, CUPS filter and backend, PPD, emulator, tests |
| [`tools/`](tools) | parameter table generator, animation renderer |

## Build guide

1. [Design and decisions](docs/01-design.md): why HP 302, why this paper path, specs
2. [Printing the parts](docs/02-printing-parts.md)
3. [Electronics](docs/03-electronics.md)
4. [Assembly](docs/04-assembly.md)
5. [Firmware](docs/07-firmware.md)
6. [Driver and printing](docs/06-host-driver.md)
7. [First power-on and calibration](docs/08-calibration.md)
8. Optional: [grayscale and colour](docs/12-grayscale-and-color.md)
9. Optional: [share the printer over Wi-Fi](docs/11-print-server.md) (no extra hardware)
10. [Troubleshooting](docs/09-troubleshooting.md) · [USB protocol](docs/05-protocol.md) · [Roadmap](docs/10-roadmap.md)

## Quick start (once built)

```bash
pip install "./host[pdf]"
freejet setup --inks K        # or CMY / KCMY
freejet status
freejet test nozzles
freejet print my-document.pdf
# Linux print queue for every app:
sudo host/cups/install.sh --add
```

## Development

```bash
pip install -e "./host[pdf,test]"
python3 -m pytest host/tests     # protocol, colour, encoder, emulator, C firmware data path, real CUPS run
make -C firmware/tests && firmware/tests/wave_test   # waveform vs. Sprite_tm's generator
make -C cad -j8                  # regenerate STLs (CARTS=KCMY for the two-cartridge build)
cmake -S firmware -B firmware/build -DPICO_SDK_PATH=~/pico-sdk && make -C firmware/build
```

You can try the whole software side without hardware:
`freejet preview some.pdf --inks KCMY -o out.png` runs your document through
the real encoder and a software printer.

## Credits and licence

* HP 63/302 cartridge waveform and nozzle mapping: **Jeroen Domburg
  (Sprite_tm)**, [printercart_simple](https://github.com/Spritetm/printercart_simple)
  (beer-ware licence, notice kept in `firmware/src/hp302.c`), with background
  from [MagicBrush](https://spritesmods.com/?art=magicbrush) and the
  [PrintSpider cartridge module](https://hackaday.io/project/176931-hp-printer-cartridge-control-module).
* Concept: [Openprinter](https://www.crowdsupply.com/open-tools/openprinter)
  by Open Tools (cartridges, single-roller paper path, roll in the chassis,
  modules). No Openprinter files were used (none have been published yet;
  theirs will be CC BY-NC-SA 4.0).
* Everything else in this repository: **GPL-3.0-or-later** (see [LICENSE](LICENSE)),
  hardware design files included.

"HP" and the cartridge numbers are trademarks of HP Inc.; this project is not
affiliated with HP. It uses the cartridges as standard consumable parts.
