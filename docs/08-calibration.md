# 8. First power-on and calibration

Do the electronics bring-up in [`03-electronics.md`](03-electronics.md)
first (it checks the heater pulses **before** a cartridge is connected).

## 0. Tell the printer which cartridges are fitted

```bash
freejet setup --inks K      # black only
freejet setup --inks CMY    # tri-colour only (in the left pocket)
freejet setup --inks KCMY   # black + colour (two-pocket build)
```

This sets `cartridges` and the frame geometry for the standard build
(`col0_x_um`, `spit_x_um`, `x_travel_um`). Add the same `--inks …` to every
`freejet test …` below.

## 1. Motion

```bash
freejet status          # state idle; shows the 16 V rail and the paper sensor
freejet home            # carriage goes left until the service-station switch trips
freejet park            # the cap(s) should press on the nozzles
freejet feed 30         # the roller turns forward, paper comes out the front
```

* Carriage moves the wrong way → `freejet param set x_dir_invert 1`.
* Paper goes backwards → `freejet param set y_dir_invert 1`.
* `freejet param save` after any change you want to keep.

## 2. Nozzles

```bash
freejet clean            # spits every nozzle into the spittoon
freejet test nozzles     # insert a sheet when asked
```

Every nozzle draws one dash, staggered in columns. A few missing dashes are
normal on a fresh or long-stored cartridge: run `freejet clean` and print
again; dab the nozzle plate with a damp lint-free cloth if needed. Whole
groups missing → contact flex pressure or a wrong wire. Nothing at all →
the 16 V rail, the heater switches, F3/F5 wiring.

If the dashes form a staircase going the "wrong" way (the top of the page is
printed last within each pass), set `freejet param set nozzle_flip 1`.

## 3. Black nozzle row alignment

The black cartridge has two columns of nozzles a few mm apart
(`k_row_gap_um`, default 4.0 mm, a guess until measured).

```bash
freejet test rows        # 13 blocks of vertical lines, numbered -6 … +6
freejet calibrate rows 2 # the block whose lines look single and sharp
```

If the sharpest block is at the edge (±6), apply it and print again.

## 4. Colour alignment (CMY or KCMY)

```bash
freejet test colors --inks KCMY
freejet calibrate color-x -3     # "plane 1 vs plane 0" block: cyan merges with black
freejet calibrate cmy-pitch 1    # "plane 2 vs plane 1" block: magenta merges with cyan
freejet calibrate k-dy 2         # Y block: black dash in line with the cyan dash
```

* `color_x_um`: how far the colour cartridge's cyan nozzles are from black
  row 0 (pocket pitch 28 mm minus the nozzle positions).
* `cmy_pitch_um`: the spacing between the cyan, magenta and yellow nozzle columns
  inside the colour cartridge.
* `k_dy_rows`: which 168 of the black cartridge's 324 rows line up with the
  colour nozzles in a colour pass. Black is taller than colour, so this
  corrects vertical misalignment without moving anything.

With `--inks CMY` only `cmy-pitch` applies. Repeat until the blocks around 0
look best.

## 5. Bidirectional alignment

```bash
freejet test bidir       # line halves printed in opposite directions
freejet calibrate bidir -1
```

Pick the block where the top and bottom halves of each line meet straight.

## 6. Paper feed

```bash
freejet test feed        # two lines 250 mm apart + a grey stitch patch
freejet calibrate feed 248.6     # what you measured, in mm
```

Then look at the grey patch: thin white lines between passes = the paper moves
too far per pass (increase `y_steps_per_m` slightly); dark lines = overlap
(decrease). Fine-tune with `freejet param set y_steps_per_m …`. The default
(138 900) is calculated for the 22 mm roller, the 60T/20T belt and 1/16 steps.

## 7. Margins / position

* `col0_x_um`: where column 0 (the paper's left edge) is relative to home.
  If prints are shifted sideways, adjust it by the error.
* `sensor_to_nozzle_um`: top margin. If the first line lands lower than it
  should, reduce it by the error.
* `sheet_tail_um`: how far past the moment the sensor sees the sheet's tail the
  printer still prints. If the last line of a page is smeared or crooked
  (the roller has let go), reduce it.

## 8. Head gap

1.0–1.5 mm between the nozzle plate and the paper. Too close smears on
cockled paper, too far makes fuzzy text. Adjust with the platen beam's
slotted end flanges.

## Useful parameters

`freejet param list` shows everything with defaults. The ones you are most
likely to touch: `x_speed_mm_s` (lower = sharper, slower), `spit_count`,
`vhd_min_mv`, `idle_motor_off_s`.
