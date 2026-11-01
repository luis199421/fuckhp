# 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `No FreeJet printers found` | USB cable is charge-only; on Linux add yourself to `dialout`; firmware not flashed. |
| `no cartridge detected` | Cartridge not pressed on the pads; TSR wire; adjust `tsr_min`/`tsr_max` to your reading (`freejet status` shows `tsr`). |
| `no head voltage` | VHD switch wiring, 12 V brick, `vhd_min_mv` too high for your supply. |
| `homing failed` | Home switch not reached: wiring, carriage blocked, belt slipping. |
| Printer waits for paper forever | Paper lever not pressed by the sheet: lever too low/high; the rollers aren't gripping (pinch springs). Press the button to retry. |
| `paper jam` | A sheet was still inside at the start of a page, or never left after printing. Clear it, press the button to eject. |
| `data underrun` | Carriage faster than the head can fire: lower `x_speed_mm_s` or `prim_groups`. |
| Faint print / missing dots | `freejet clean`; wipe the nozzle plate; raise `pulse_ns` by 100; refill the cartridge. |
| Doubled vertical lines | Row alignment: `freejet test rows`. |
| Jagged verticals only in bidirectional | `freejet test bidir`, or print `--unidirectional`. |
| White/dark horizontal stripes every 12.7 mm | Feed calibration: `freejet test feed`. |
| Smears | Head gap too small, paper cockling, star wheels not spinning freely. |
| Skewed print | Sheet not along the left guide; pinch pressure unequal left/right. |
| Ink dries in the nozzles between jobs | Cap not sealing: sled pad height, `home_backoff_um` (park position). |
| Firmware reboots during printing | Power: the 12 V brick dips when the head fires; check the head board's 470 µF caps and GND wiring. |
