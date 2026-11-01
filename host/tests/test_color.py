import numpy as np
from PIL import Image

from freejet.color import INKSETS, separate
from freejet.emulator import VirtualPrinter
from freejet.job import job_frames
from freejet.raster import PageSetup, place


def patch(rgb, size=64):
    return Image.new("RGB", (size, size), rgb)


def cover(plane):
    return float(plane.mean())


def test_cmyk_primaries_and_black():
    red = separate(patch((255, 0, 0)), "KCMY", "fs")
    k, c, m, y = (cover(p) for p in red)
    # colour drops only on every other row (1/300 in nozzles)
    assert k == 0 and c == 0 and m > 0.47 and y > 0.47 and not red[2][1::2].any()
    black = separate(patch((0, 0, 0)), "KCMY", "fs")
    assert cover(black[0]) > 0.95 and black[1:].sum() == 0      # text black = black ink only
    white = separate(patch((255, 255, 255)), "KCMY", "fs")
    assert white.sum() == 0


def test_total_ink_is_limited():
    navy = separate(patch((10, 10, 60)), "KCMY", "fs")
    assert cover(navy[0]) + 2 * sum(cover(p) for p in navy[1:]) <= 2.7


def test_gamma_lightens_midtones():
    mid = patch((128, 128, 128))
    assert cover(separate(mid, "K", "fs", 1.5)[0]) < cover(separate(mid, "K", "fs", 1.0)[0]) - 0.1


def test_colour_job_through_emulator():
    img = Image.new("RGB", (300, 200), "white")
    img.paste((0, 160, 220), (20, 20, 120, 120))
    img.paste((0, 0, 0), (150, 20, 280, 60))
    setup = PageSetup(paper="a5", inkset="KCMY", dither="fs")
    page = place(img, setup, 100)
    assert page.shape[0] == 4
    vp = VirtualPrinter()
    vp.inkset = "KCMY"
    for fr in job_frames([page], inkset="KCMY"):
        vp.write(fr)
    assert not vp.errors
    out = vp.pages[0]
    h = min(out.shape[1], page.shape[1])
    w = page.shape[2]
    assert np.array_equal(out[:, :h, :w], page[:, :h])
    assert not out[:, :, w:].any()


def test_inkset_mismatch_is_refused():
    vp = VirtualPrinter()           # black-only printer
    page = np.zeros((4, 400, 400), bool)
    page[:, 10:20, 10:20] = True
    for fr in job_frames([page], inkset="KCMY"):
        vp.write(fr)
    assert any("ink set" in e for e in vp.errors)


def test_standard_geometry_matches_cad():
    import re
    from pathlib import Path
    from freejet.cli import standard_geometry
    fj = (Path(__file__).resolve().parents[2] / "cad" / "fj.scad").read_text()
    assert re.search(r"head_pitch = 28;", fj) and "paper_x0  = 70 + head_span" in fj
    assert "spit_x    = 62 + head_span" in fj and "home_x    = 30;" in fj
    g1, g2 = standard_geometry("K"), standard_geometry("KCMY")
    assert g1["col0_x_um"] == (70 - 30) * 1000 and g1["spit_x_um"] == (62 - 30) * 1000
    assert g2["col0_x_um"] - g1["col0_x_um"] == 28000 and g2["cartridges"] == 3
