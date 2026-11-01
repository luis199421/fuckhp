"""Calibration and diagnostic pages (all generated as ink masks)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .protocol import DPI, ROWS

MM = DPI / 25.4


def _font(px):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", px)
    except OSError:
        return ImageFont.load_default(size=px)


def _canvas(w_mm, h_mm):
    img = Image.new("1", (round(w_mm * MM), round(h_mm * MM)), 1)
    return img, ImageDraw.Draw(img)


def _ink(img):
    return ~np.asarray(img, dtype=bool)


def nozzle_check(width_mm=200) -> np.ndarray:
    """Every nozzle draws its own short dash. A missing dash = clogged/dead nozzle.
    Dashes are staggered in 10 columns so neighbours never touch; row r is in
    column r % 10. A solid block underneath shows overall density."""
    img, d = _canvas(width_mm, 60)
    f = _font(round(3 * MM))
    d.text((round(5 * MM), round(1 * MM)), "FreeJet nozzle check - each nozzle = one dash, "
           "rows 0..299 top to bottom, staggered in 10 columns", font=f, fill=0)
    page = _ink(img)
    top = round(8 * MM)
    dash = round(6 * MM)
    gap = round(2 * MM)
    x0 = round(5 * MM)
    for r in range(ROWS):
        x = x0 + (r % 10) * (dash + gap)
        page[top + r, x:x + dash] = True
    # density block + row labels every 50 rows
    bx = x0 + 10 * (dash + gap) + round(4 * MM)
    page[top:top + ROWS, bx:bx + round(25 * MM)] = True
    lab = Image.new("1", (round(30 * MM), ROWS + 40), 1)
    ld = ImageDraw.Draw(lab)
    for r in range(0, ROWS, 50):
        ld.text((0, r), f"{r}", font=_font(30), fill=0)
    la = _ink(lab)
    lx = bx + round(28 * MM)
    page[top:top + la.shape[0], lx:lx + la.shape[1]] |= la
    return page


def alignment_page(odd_rows: np.ndarray, span=6, width_mm=200) -> np.ndarray:
    """odd_rows: bool[300], True for data rows driven by the odd nozzle column."""
    img, d = _canvas(width_mm, 45)
    f = _font(round(2.8 * MM))
    d.text((round(5 * MM), 0), "Row alignment: pick the block with single sharp lines -> "
           "freejet calibrate rows <k>", font=f, fill=0)
    block_w = round(width_mm * MM / (2 * span + 1))
    for i, k in enumerate(range(-span, span + 1)):
        d.text((i * block_w + round(2 * MM), round(5 * MM)), f"{k:+d}", font=f, fill=0)
    page = _ink(img)
    top = round(12 * MM)
    for i, k in enumerate(range(-span, span + 1)):
        bx = i * block_w + round(2 * MM)
        for line in range(6):
            x = bx + line * round(1.6 * MM)
            page[top:top + ROWS, x] |= ~odd_rows          # even column nozzles
            page[top:top + ROWS, x + k] |= odd_rows        # odd column, shifted by k
    return page


def bidir_page(span=6, width_mm=200) -> tuple[np.ndarray, int]:
    """Top half of each line comes from one pass, bottom half from a pass the
    other way (the planner alternates directions every 300 rows). The bottom
    half is pre-shifted by k columns; pick the straightest block, then
    freejet calibrate bidir <k>. Returns (page, row where the 2nd pass starts)."""
    img, d = _canvas(width_mm, 50)
    f = _font(round(2.8 * MM))
    d.text((round(5 * MM), 0), "Bidirectional: pick the block whose lines are straight -> "
           "freejet calibrate bidir <k>", font=f, fill=0)
    block_w = round(width_mm * MM / (2 * span + 1))
    for i, k in enumerate(range(-span, span + 1)):
        d.text((i * block_w + round(2 * MM), round(5 * MM)), f"{k:+d}", font=f, fill=0)
    page = _ink(img)
    top = round(12 * MM)
    # header text occupies its own passes; the lines start on a fresh pass
    for i, k in enumerate(range(-span, span + 1)):
        bx = i * block_w + round(2 * MM)
        for line in range(6):
            x = bx + line * round(1.6 * MM)
            page[top:top + ROWS, x] = True
            page[top + ROWS:top + 2 * ROWS, x + k] = True
    return page, top + ROWS


def feed_page(length_mm=250.0, width_mm=200) -> np.ndarray:
    """Two thin horizontal lines exactly `length_mm` apart plus a swath-stitch
    ladder. Measure the distance and run: freejet calibrate feed <measured_mm>."""
    img, d = _canvas(width_mm, length_mm + 20)
    f = _font(round(3 * MM))
    y1 = round(10 * MM)
    y2 = y1 + round(length_mm * MM)
    for y in (y1, y2):
        d.rectangle([0, y, img.width - 1, y + 1], fill=0)
    d.text((round(5 * MM), y1 + round(3 * MM)),
           f"Measure between the two lines (should be {length_mm:.1f} mm), then", font=f, fill=0)
    d.text((round(5 * MM), y1 + round(8 * MM)), "freejet calibrate feed <measured mm>", font=f, fill=0)
    # stitch test: grey fill; dark/white stripes every 12.7 mm = feed error
    page = _ink(img)
    sx0, sx1 = round(130 * MM), round(190 * MM)
    yy = np.arange(y1 + round(20 * MM), y2 - round(5 * MM))
    page[yy[:, None], np.arange(sx0, sx1)[None, :]] = ((yy[:, None] + np.arange(sx0, sx1)[None, :]) % 2 == 0)
    return page
