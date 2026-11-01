"""Calibration and diagnostic pages (all generated as ink masks)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .protocol import DPI, ROWS_COLOR, ROWS_K

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


def nozzle_check(width_mm=200, rows=ROWS_K, step=1) -> np.ndarray:
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
    for i, r in enumerate(range(0, rows, step)):     # step 2: colour nozzles are 1/300 in apart
        x = x0 + (i % 10) * (dash + gap)
        page[top + r, x:x + dash] = True
    # density block + row labels every 50 rows
    bx = x0 + 10 * (dash + gap) + round(4 * MM)
    page[top:top + rows:step, bx:bx + round(25 * MM)] = True
    lab = Image.new("1", (round(30 * MM), rows + 40), 1)
    ld = ImageDraw.Draw(lab)
    for r in range(0, rows, 50):
        ld.text((0, r), f"{r}", font=_font(30), fill=0)
    la = _ink(lab)
    lx = bx + round(28 * MM)
    page[top:top + la.shape[0], lx:lx + la.shape[1]] |= la
    return page


def alignment_page(odd_rows: np.ndarray, span=6, width_mm=200) -> np.ndarray:
    """odd_rows: bool[324], True for data rows printed by the black cartridge's nozzle row 1."""
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
            page[top:top + ROWS_K, x] |= ~odd_rows          # nozzle row 0
            page[top:top + ROWS_K, x + k] |= odd_rows        # nozzle row 1, shifted by k
    return page


def bidir_page(span=6, width_mm=200) -> tuple[np.ndarray, int]:
    """The top half of each line is printed left-to-right (the first pass of the
    job), the bottom half right-to-left (the second pass), pre-shifted by k
    columns. Pick the block whose lines are straight, then
    `freejet calibrate bidir <k>`. Labels go *below* the lines so that the lines
    really are the first two passes. Returns (page, row where pass 2 starts)."""
    block_w = round(width_mm * MM / (2 * span + 1))
    h = 2 * ROWS_K + round(16 * MM)
    page = np.zeros((h, round(width_mm * MM)), dtype=bool)
    for i, k in enumerate(range(-span, span + 1)):
        bx = i * block_w + round(2 * MM) + span
        for line in range(6):
            x = bx + line * round(1.6 * MM)
            page[0:ROWS_K, x] = True
            page[ROWS_K:2 * ROWS_K, x + k] = True
    img, d = _canvas(width_mm, 14)
    f = _font(round(2.8 * MM))
    for i, k in enumerate(range(-span, span + 1)):
        d.text((i * block_w + round(2 * MM), round(1 * MM)), f"{k:+d}", font=f, fill=0)
    d.text((round(5 * MM), round(7 * MM)), "Bidirectional: pick the block whose lines are straight -> "
           "freejet calibrate bidir <k>", font=f, fill=0)
    lab = _ink(img)
    page[2 * ROWS_K + 20:2 * ROWS_K + 20 + lab.shape[0], :lab.shape[1]] |= lab[:h - 2 * ROWS_K - 20]
    return page, ROWS_K


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


def colors_page(planes_n: int, span=6, width_mm=200) -> np.ndarray:
    """Line the inks up. Plane 0 is the reference (black in KCMY, cyan in CMY); every other
    plane s is compared with plane s-1:
      X blocks: vertical lines, plane s-1 at x, plane s at x + k -> pick where they merge:
                KCMY: slot 1 (C vs K) -> calibrate color-x <k>; slots 2, 3 (M vs C, Y vs M)
                -> calibrate cmy-pitch <k>  (CMY: slots 1, 2 -> cmy-pitch)
      Y blocks (KCMY only): black dash shifted k rows against a cyan dash -> calibrate k-dy <k>
    Returns (planes, rows, cols)."""
    w = round(width_mm * MM)
    block_w = w // (2 * span + 1)
    band = 2 * ROWS_COLOR + round(16 * MM)
    rows = (planes_n - 1) * band + (band if planes_n == 4 else 0) + 60
    planes = np.zeros((planes_n, rows, w), dtype=bool)
    f = _font(round(2.6 * MM))

    def label(top, text):
        img, d = _canvas(width_mm, 12)
        d.text((0, 0), text, font=f, fill=0)
        for i, k in enumerate(range(-span, span + 1)):
            d.text((i * block_w + round(2 * MM), round(5.5 * MM)), f"{k:+d}", font=f, fill=0)
        lab = _ink(img)
        planes[0, top:top + lab.shape[0], :lab.shape[1]] |= lab
        return top + lab.shape[0] + 10

    for s in range(1, planes_n):
        y0 = label((s - 1) * band, f"X: plane {s} vs plane {s - 1}")
        for i, k in enumerate(range(-span, span + 1)):
            bx = i * block_w + round(2 * MM) + span
            for line in range(5):
                x = bx + line * round(1.6 * MM)
                planes[s - 1, y0:y0 + ROWS_COLOR:2, x] = True
                planes[s, y0:y0 + ROWS_COLOR:2, x + k] = True
    if planes_n == 4:
        y0 = label(3 * band, "Y: black dash vs cyan dash -> calibrate k-dy <k>") + 20
        y0 += y0 % 2
        for i, k in enumerate(range(-span, span + 1)):
            bx = i * block_w + round(2 * MM) + span
            for yy in (y0, y0 + 60):
                planes[1, yy, bx + 60:bx + 120] = True          # cyan (even row)
                planes[0, yy + k, bx:bx + 60] = True            # black, shifted k rows
    return planes
