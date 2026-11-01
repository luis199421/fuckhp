# 10. Status and roadmap

## Where this is

| Part | State |
|---|---|
| Host driver (CLI, rasteriser, colour separation, protocol, CUPS filter/backend, emulator) | written and tested in software: 34 tests, including a real CUPS + Ghostscript colour run |
| Firmware | written, builds cleanly for the Pico 2. The cartridge waveform is compared sample by sample against Sprite_tm's original driver; the data path (frames → ring → compose → nozzle data) is tested on a PC for K, CMY and KCMY. Not yet run on hardware. |
| CAD | 28 parametric parts, single solids, carriage travel passes a collision check, for both the black-only and the black + colour build. Not yet test-printed; **cartridge dimensions are estimates**. |
| Main board | wiring documented (modules + DIP chips on perfboard) |
| Cartridge contacts | salvaged DeskJet contact flex; **pad-to-signal mapping must be verified** against the MagicBrush write-up |

Nobody has built one yet. The first build is a prototype.

## Next

1. Measure a real HP 302 / 63 (both cartridges) and a salvaged contact flex;
   fix `cart_w/d/h`, `nz_back` and the flex recess in `cad/fj.scad`.
2. Build prototype #1. Verify the waveform and heater pulses on a scope
   (no cartridge), then first nozzle checks.
3. Measure the real nozzle geometry (`k_row_gap_um`, `color_x_um`,
   `cmy_pitch_um`, `k_dy_rows`, `nozzle_flip`) and make them the defaults.
4. Tune speeds, leaf-spring pressure, feed steps and sensor distances.
5. A small PCB for the main board (optional, the perfboard works).
6. Try network sharing (`docs/11-print-server.md`) with iOS, Android and
   Windows; later maybe a PAPPL-based IPP Everywhere printer application.
7. Optional sheet feeder (stack of 20–50 sheets) and roll cutter.
8. Get a dedicated USB PID from pid.codes.
