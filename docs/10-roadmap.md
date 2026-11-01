# 10. Status and roadmap

## Where this is

| Part | State |
|---|---|
| Host driver (CLI, rasteriser, protocol, CUPS filter/backend, emulator) | written and tested in software: 21 tests, including a real CUPS + Ghostscript run |
| Firmware | written, builds cleanly for the Pico 2; its data path (frames → ring → compose → nozzles) is tested on a PC against the host. Not yet run on hardware. |
| CAD | 27 parametric parts; every part is a single solid; the carriage's travel passes a collision check. Not yet test-printed; cartridge dimensions are estimates. |
| Main board | wiring documented (modules on perfboard) |
| Printhead board | circuit and netlist done, contact footprint generated; **PCB layout still to draw** |

Nobody has built one yet. The first build is a prototype.

## Next

1. Lay out the printhead board in KiCad (footprint + netlist are in
   `hardware/head-board`), order with ENIG.
2. Build prototype #1, measure the real HP45, fix the carriage dimensions.
3. Verify pulse width / addresses on a scope, then first prints.
4. Tune defaults (speeds, feed steps, sensor distances) from the prototype.
5. Try network sharing (`docs/11-print-server.md`) with iOS,
   Android and Windows; later maybe a PAPPL-based IPP Everywhere printer
   application, and printing straight from a USB stick (as Openprinter plans).
6. Optional sheet feeder (stack of 20–50 sheets).
7. Optional automatic cutter for roll mode (Openprinter has one integrated).
8. Grayscale/colour (done in software: 2–4 HP45-format cartridges with different inks, see
   `12-grayscale-and-color.md`); needs real ink tests, especially home-mixed light black.
9. Get a dedicated USB PID from pid.codes.
