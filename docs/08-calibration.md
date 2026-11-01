# 8. First power-on and calibration

Do the electronics bring-up in [`03-electronics.md`](03-electronics.md)
first (it checks the pulse width **before** a cartridge is connected).

## 1. Motion

```bash
freejet status          # state idle, flags show 'head' with a cartridge in
freejet home            # carriage goes left until the service-station switch trips
freejet park            # cap should press on the nozzles
freejet feed 30         # paper rollers turn forward
```

* Carriage moves the wrong way → `freejet param set x_dir_invert 1`.
* Paper goes backwards → `freejet param set y_dir_invert 1`.
* `freejet param save` after any change you want to keep.

## 2. Nozzles

```bash
freejet clean            # 200 spits into the spittoon
freejet test nozzles     # insert a sheet when asked
```

Every nozzle draws one dash, staggered in 10 columns. A few missing dashes
are normal on a fresh or long-stored cartridge: run `freejet clean` and
print again; wipe the nozzle plate with a damp lint-free cloth if needed.
Whole groups missing → check the contact pads / cartridge seating. Every
dash missing → check VHD and the ribbon.

## 3. Nozzle row alignment

The HP45 has two columns of nozzles ~4.05 mm apart; the firmware delays one
against the other by `row_gap_um`.

```bash
freejet test rows        # 13 blocks of vertical lines, numbered -6 … +6
freejet calibrate rows 2 # the block whose lines look single and sharp
```

If the sharpest block is at the edge (±6), apply it and print again.

## 4. Bidirectional alignment

```bash
freejet test bidir       # line halves printed in opposite directions
freejet calibrate bidir -1
```

Pick the block where the top and bottom halves of each line meet straight.

## 5. Paper feed

```bash
freejet test feed        # two lines 250 mm apart + a grey stitch patch
freejet calibrate feed 248.6     # what you measured, in mm
```

Then look at the grey patch: thin white lines every 12.7 mm = the paper
moves too far per pass (increase `y_steps_per_m` slightly); dark lines =
overlap (decrease). Fine-tune with `freejet param set y_steps_per_m …`.

## 6. Margins / position

* `col0_x_um`: where column 0 (the paper's left edge) is relative to home.
  If prints are shifted sideways, adjust it by the error.
* `sensor_to_nozzle_um`: top margin. If the first line lands lower than it
  should, reduce it by the error.

## 7. Head gap

1.0–1.5 mm between the nozzle plate and the paper. Too close smears on
cockled paper, too far makes fuzzy text. Adjust with the platen set screws.

## Useful parameters

`freejet param list` shows everything with defaults. The ones you are most
likely to touch: `x_speed_mm_s` (lower = sharper, slower), `pulse_ns`
(1600–2000; raise if prints are faint, never above 2200 for long),
`spit_count`, `idle_motor_off_s`.
