# 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `No FreeJet printers found` | USB cable is charge-only; on Linux add yourself to `dialout`; firmware not flashed. |
| `ink set doesn't match the cartridges` | The job's `--inks` / *Cartridges fitted* option and the printer's `cartridges` setting differ: run `freejet setup --inks …` or fix the print option. |
| `no head voltage` | 16 V rail: IRF9540N/2N3904 wiring, MT3608 not adjusted, 12 V brick, `vhd_min_mv` too high. |
| `homing failed` | Home switch not reached: wiring, carriage blocked, belt slipping. |
| Printer waits for paper forever | The paper lever isn't pressed by the sheet: bend the lever or move the sensor bracket. Push the sheet in until it stops at the roller; press the button to retry. |
| Sheet isn't pulled in / slips | Leaf springs too light: bend them down a little; clean the TPU tires with alcohol. |
| `paper jam` | A sheet was still inside at the start of a page, or never left after printing. Clear it, press the button to eject. |
| `sheet end` | The page has content in the bottom ~22 mm of a single sheet, where the roller can't hold it. Print with the default margins, or use roll paper. |
| `data underrun` | Carriage faster than the head can fire: lower `x_speed_mm_s`. |
| Nothing prints, carriage moves | Contact flex not pressing (tighten the thumbscrew), wrong pad mapping, F3/F5 not reaching the cartridge. Check with `freejet fire black` and a scope. |
| Faint print / missing dots | `freejet clean`; dab the nozzle plate; refill or replace the cartridge. |
| Doubled vertical lines (black) | Row alignment: `freejet test rows`. |
| Jagged verticals only in bidirectional | `freejet test bidir`, or print `--unidirectional`. |
| White/dark horizontal stripes between passes | Feed calibration: `freejet test feed`. |
| Each pass printed upside down (staircase) | `freejet param set nozzle_flip 1`. |
| Smears | Head gap too small, paper cockling, too much ink: try `--gamma 1.25`. |
| Skewed print | Sheet not along the left guide; leaf pressure unequal left/right. |
| Ink dries in the nozzles between jobs | Cap not sealing: print the cap in softer TPU (85A), check the sled lifts it, `home_backoff_um` (park position). |
| Firmware reboots during printing | Power: the 12 V brick dips when the heads fire; check the 470 µF on the 16 V rail and the GND wiring. |
| Colour fringes around black text or lines | Cartridges not lined up: `freejet test colors` + `calibrate color-x / cmy-pitch / k-dy`. |
| Colours wrong / swapped | Black must be in the left pocket, colour in the right. If cyan and yellow are swapped, `nozzle_flip` is probably wrong. |
| Colour prints too dark or muddy | Try `--gamma 1.25`; use coated inkjet paper. |
