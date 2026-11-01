# 10. Status and roadmap

## Where this is

| Part | State |
|---|---|
| Host driver (CLI, rasteriser, protocol, CUPS filter/backend, emulator) | written and tested in software: 21 tests, including a real CUPS + Ghostscript run |
| Firmware | written, builds cleanly for the Pico 2; its data path (frames → ring → compose → nozzles) is tested on a PC against the host. Not yet run on hardware. |
| CAD | 23 parametric parts; every part is a single solid; the carriage's travel passes a collision check. Not yet test-printed; cartridge dimensions are estimates. |
| Main board | wiring documented (modules on perfboard) |
| Printhead board | circuit and netlist done, contact footprint generated; **PCB layout still to draw** |

Nobody has built one yet. The first build is a prototype.

## Next

1. Lay out the printhead board in KiCad (footprint + netlist are in
   `hardware/head-board`), order with ENIG.
2. Build prototype #1, measure the real HP45, fix the carriage dimensions.
3. Verify pulse width / addresses on a scope, then first prints.
4. Tune defaults (speeds, feed steps, sensor distances) from the prototype.
5. IPP Everywhere printer application (e.g. PAPPL-based) so Windows, macOS,
   iOS and Android can print with no driver at all.
6. Optional sheet feeder (stack of 20–50 sheets).
7. Optional automatic cutter for roll mode.
8. Second cartridge slot for colour, once a colour head is reverse-engineered.
9. Get a dedicated USB PID from pid.codes.
