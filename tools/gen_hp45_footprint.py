#!/usr/bin/env python3
"""Generate a KiCad footprint for the HP45 contact pattern from
hardware/head-board/hp45_pads.csv (+ hp45_holes.csv).

The pad coordinates come from Yvo de Haas' HP45 standalone controller V4.02
(https://github.com/yvodehaas/HP45-standalone-controller-V4.02, GPL-3.0),
where the cartridge's flex circuit presses directly onto round gold (ENIG)
pads on the PCB. Pad *numbers* are the connector pin numbers used in that
design; the `signal` column gives the HP45 line in raw P1..P14 / A1..A22 terms.
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "hardware" / "head-board"


def main():
    pads = list(csv.DictReader(open(HERE / "hp45_pads.csv")))
    holes = list(csv.DictReader(open(HERE / "hp45_holes.csv")))
    out = ['(footprint "HP45_Contacts" (version 20221018) (generator freejet) (layer "F.Cu")',
           '  (descr "HP45 / 51645A inkjet cartridge contact pads (press contact, ENIG finish). '
           'Coordinates from Ytec3D HP45 controller V4.02, GPL-3.0")',
           '  (attr smd)',
           '  (fp_text reference "J2" (at 0 -35) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
           '  (fp_text value "HP45_Contacts" (at 0 2.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
           '  (fp_rect (start -9.28 -33.35) (end 9.78 0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS"))']
    for p in pads:
        out.append(f'  (pad "{p["pad"]}" smd circle (at {p["x_mm"]} {p["y_mm"]}) (size 1.3 1.3) '
                   f'(layers "F.Cu" "F.Mask") (pinfunction "{p["signal"]}"))')
    for h in holes:
        d = float(h["diameter_mm"])
        out.append(f'  (pad "" np_thru_hole circle (at {h["x_mm"]} {h["y_mm"]}) (size {d} {d}) '
                   f'(drill {d}) (layers "*.Cu" "*.Mask"))')
    out.append(")")
    (HERE / "HP45_Contacts.kicad_mod").write_text("\n".join(out) + "\n")
    print("wrote", HERE / "HP45_Contacts.kicad_mod")


if __name__ == "__main__":
    main()
