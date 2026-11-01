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
    red = separate(patch((255, 0, 0)), "CMYK", "fs")
    k, c, m, y = (cover(p) for p in red)
    assert k == 0 and c == 0 and m > 0.95 and y > 0.95
    black = separate(patch((0, 0, 0)), "CMYK", "fs")
    assert cover(black[0]) > 0.95 and black[1:].sum() == 0      # text black = black ink only
    white = separate(patch((255, 255, 255)), "CMYK", "fs")
    assert white.sum() == 0


def test_total_ink_is_limited():
    navy = separate(patch((10, 10, 60)), "CMYK", "fs")
    assert sum(cover(p) for p in navy) <= 2.7


def test_light_black_does_the_light_greys():
    light = separate(patch((200, 200, 200)), "KLK", "fs")
    assert cover(light[0]) < 0.02 and cover(light[1]) > 0.3       # only light black
    dark = separate(patch((40, 40, 40)), "KLK", "fs")
    assert cover(dark[0]) > 0.6                                   # black takes over


def test_gamma_lightens_midtones():
    mid = patch((128, 128, 128))
    assert cover(separate(mid, "K", "fs", 1.5)[0]) < cover(separate(mid, "K", "fs", 1.0)[0]) - 0.1


def test_colour_job_through_emulator():
    img = Image.new("RGB", (300, 200), "white")
    img.paste((0, 160, 220), (20, 20, 120, 120))
    img.paste((0, 0, 0), (150, 20, 280, 60))
    setup = PageSetup(paper="a5", inkset="CMYK", dither="fs")
    page = place(img, setup, 100)
    assert page.shape[0] == 4
    vp = VirtualPrinter()
    vp.n_heads = 4
    for fr in job_frames([page], inkset="CMYK"):
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
    for fr in job_frames([page], inkset="CMYK"):
        vp.write(fr)
    assert any("ink set" in e for e in vp.errors)
