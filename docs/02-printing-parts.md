# 2. Printing the parts

All parts are parametric OpenSCAD files in [`cad/parts`](../cad/parts) that
share the dimensions in [`cad/fj.scad`](../cad/fj.scad). Ready-made STLs
are in [`cad/stl`](../cad/stl) (black cartridge, or colour cartridge only) and
[`cad/stl-kcmy`](../cad/stl-kcmy) (black + colour cartridges: wider frame,
2-pocket carriage). Regenerate them with `make -C cad -j8` or
`make -C cad -j8 CARTS=KCMY` after changing anything.

**Before printing the carriage**, measure your cartridge with calipers and set
`cart_w`, `cart_d`, `cart_h` and `nz_back` (nozzle line to the contact face) in
`cad/fj.scad`. The defaults are estimates. Print the carriage once in draft
quality and test-fit the cartridge and the salvaged contact flex first.

Material: **PETG** for everything, **TPU** for the four tires, the cap and the
wiper. Bed size needed: 220 × 220 mm.

| STL | Qty | Settings | Notes |
|---|---|---|---|
| side_plate_left / side_plate_right | 1 + 1 | 0.2 mm, 4 walls, 40 % gyroid | flat on the bed; roll keyhole at the top rear |
| carriage | 1 | 0.16 mm, 4 walls, 40 % | upright as modelled, no supports |
| carriage_pad | 1 per cartridge | TPU or PETG, 100 % | between clamp screw and cartridge |
| platen_1 … platen_N | 1 each (3 for the black build) | 0.2 mm, 4 walls, 30 % | **upside down** (ribs on the bed) |
| roller_hub | 4 | 0.16 mm, 100 % | on the feed roller shaft |
| roller_tire_TPU | 4 | TPU, 100 % | (2 O-rings 18 × 2 mm per hub if you have no TPU) |
| gt2_pulley_60t | 1 | 0.12 mm, 100 % | flat face down |
| leaf_bar_1 / leaf_bar_2 | 1 + 1 | 0.2 mm, 50 % | the bar that holds the paper-pressure leaves |
| leaf_clamp | 4 | 0.2 mm, 100 % | |
| x_motor_bracket / x_idler_bracket | 1 + 1 | 0.2 mm, 50 % | |
| service_station_base / service_station_sled | 1 + 1 | 0.2 mm 40 % / 0.16 mm 100 % | |
| service_cap_TPU | 1 per cartridge | TPU (85A best), 100 % | |
| service_wiper_TPU | 1 | TPU 95A, 100 % | |
| rod_collar | 6 | 0.2 mm, 100 % | rails and roller shaft, outside the plates |
| sensor_bracket | 1 | 0.2 mm, 50 % | |
| electronics_tray | 1 | 0.2 mm, 20 % | |
| paper_tray_1 … paper_tray_N | 1 each (2 for the black build) | 0.2 mm, 20 % | |
| paper_guide | 1 | 0.2 mm | sliding right-hand guide |
| tray_bracket | 2 | 0.2 mm, 50 % | mirror one in the slicer |
| roll_core | 2 | 0.2 mm, 20 % | optional, roll paper |
| roll_spindle | 3 (OpenSCAD prints the count) | upright, 100 % | optional; pieces pin together with M3 |

About 0.75 kg of PETG and 20 g of TPU, roughly 30 hours of printing.

## Checking the design

* `cad/assembly.scad` shows the whole machine (`-D CARR_X=200` moves the
  carriage). Renders are in `docs/img`.
* `cad/animation.scad` + `tools/render_animation.py` render the step-by-step
  assembly animation (`docs/img/assembly_animation.gif` / `.mp4`).
* Each part renders as a single solid (no floating pieces).
* The carriage's full travel was checked against the plates, platen, roller,
  leaf bar and leaves, sensor and return belt with `cad/check_collisions.scad`
  (a CSG intersection that must come out empty). Repeat it after you change dimensions.
