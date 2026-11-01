# 2. Printing the parts

All parts are parametric OpenSCAD files in [`cad/parts`](../cad/parts) that
share the dimensions in [`cad/fj.scad`](../cad/fj.scad). Ready-made STLs
are in [`cad/stl`](../cad/stl); regenerate them with `make -C cad -j8`
after changing anything.

**Before printing the carriage**, measure your HP45 with calipers and set
`cart_w`, `cart_d`, `cart_h`, `nz_back` (nozzle line to the contact face) and
`pad_z0` in `cad/fj.scad`. The defaults are estimates. Print the carriage
once in draft quality and test-fit the cartridge before printing it properly.

Material: **PETG** for everything (PLA creeps near warm motors and under
spring load), **TPU 95A** for the twelve tires. Bed size needed: 220 × 220 mm.

| STL | Qty | Settings | Notes |
|---|---|---|---|
| side_plate_left / side_plate_right | 1 + 1 | 0.2 mm, 4 walls, 40 % gyroid | flat on the bed |
| carriage | 1 | 0.16 mm, 4 walls, 40 % | upright as modelled, no supports |
| carriage_pad | 1 | TPU or PETG, 100 % | |
| platen_1, platen_2, platen_3 | 1 each | 0.2 mm, 3 walls, 25 % | **upside down** (ribs on the bed) for a flat paper surface |
| roller_hub | 12 | 0.16 mm, 100 % | 4 per drive shaft + 4 on the pinch shaft |
| roller_tire_TPU | 12 | TPU, 100 % | or 2 O-rings (18 × 2 mm) per hub |
| star_wheel | 6 | 0.12 mm, 100 % | 4 used, 2 spare: points must be sharp |
| gt2_pulley_76t | 2 | 0.12 mm, 100 % | flat face down |
| x_motor_bracket | 1 | 0.2 mm, 50 % | |
| x_idler_bracket | 1 | 0.2 mm, 50 % | |
| service_station_base | 1 | 0.2 mm, 40 % | |
| service_station_sled | 1 | 0.16 mm, 100 % | |
| sensor_bracket | 1 | 0.2 mm, 50 % | |
| electronics_tray | 1 | 0.2 mm, 20 % | |
| paper_tray_left / paper_tray_right | 1 + 1 | 0.2 mm, 20 % | |
| paper_guide | 1 | 0.2 mm | |
| tray_bracket | 2 | 0.2 mm, 50 % | mirror one in the slicer |
| roll_arm | 2 | 0.2 mm, 50 % | optional, mirror one |
| roll_core | 2 | 0.2 mm, 20 % | optional |

About 0.8 kg of PETG and 30 g of TPU in total, roughly 30 hours of printing.

## Checking the design

* `cad/assembly.scad` shows the whole machine (`-D CARR_X=200` moves the
  carriage). Renders are in `docs/img`.
* Each part renders as a single solid (no floating pieces).
* The carriage's full travel was checked against the plates, platen, rollers,
  star wheels, sensor and return belt with `cad/check_collisions.scad`
  (a CSG intersection that must come out empty). Repeat it after you change dimensions.
