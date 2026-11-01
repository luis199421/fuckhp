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
    """The top half of each line is printed left-to-right (the first pass of the
    job), the bottom half right-to-left (the second pass), pre-shifted by k
    columns. Pick the block whose lines are straight, then
    `freejet calibrate bidir <k>`. Labels go *below* the lines so that the lines
    really are the first two passes. Returns (page, row where pass 2 starts)."""
    block_w = round(width_mm * MM / (2 * span + 1))
    h = 2 * ROWS + round(16 * MM)
    page = np.zeros((h, round(width_mm * MM)), dtype=bool)
    for i, k in enumerate(range(-span, span + 1)):
        bx = i * block_w + round(2 * MM) + span
        for line in range(6):
            x = bx + line * round(1.6 * MM)
            page[0:ROWS, x] = True
            page[ROWS:2 * ROWS, x + k] = True
    img, d = _canvas(width_mm, 14)
    f = _font(round(2.8 * MM))
    for i, k in enumerate(range(-span, span + 1)):
        d.text((i * block_w + round(2 * MM), round(1 * MM)), f"{k:+d}", font=f, fill=0)
    d.text((round(5 * MM), round(7 * MM)), "Bidirectional: pick the block whose lines are straight -> "
           "freejet calibrate bidir <k>", font=f, fill=0)
    lab = _ink(img)
    page[2 * ROWS + 20:2 * ROWS + 20 + lab.shape[0], :lab.shape[1]] |= lab[:h - 2 * ROWS - 20]
    return page, ROWS


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


def heads_page(n_heads: int, span=6, width_mm=200) -> np.ndarray:
    """Line up cartridges 1..n-1 against cartridge 0 (slot 0 = left-most).
    For each slot two rows of 13 blocks (k = -6..+6):
      X: vertical lines, slot 0 at x, slot s at x + k  -> pick the block where they merge,
         then  freejet calibrate head-x <slot> <k>
      Y: short horizontal dashes, slot 0 at row y, slot s at row y + k -> pick the block where
         they form one straight line, then  freejet calibrate head-y <slot> <k>
    Returns (planes, rows, cols)."""
    w = round(width_mm * MM)
    block_w = w // (2 * span + 1)
    band = 2 * ROWS + round(14 * MM)
    planes = np.zeros((n_heads, max(1, n_heads - 1) * band + 60, w), dtype=bool)
    for s in range(1, n_heads):
        top = (s - 1) * band
        img, d = _canvas(width_mm, 12)
        f = _font(round(2.6 * MM))
        d.text((0, 0), f"slot {s}:  X blocks (top) -> calibrate head-x {s} <k>;  "
                       f"Y blocks (bottom) -> calibrate head-y {s} <k>", font=f, fill=0)
        for i, k in enumerate(range(-span, span + 1)):
            d.text((i * block_w + round(2 * MM), round(5.5 * MM)), f"{k:+d}", font=f, fill=0)
        lab = _ink(img)
        planes[0, top:top + lab.shape[0], :lab.shape[1]] |= lab
        y0 = top + lab.shape[0] + 10
        for i, k in enumerate(range(-span, span + 1)):
            bx = i * block_w + round(2 * MM) + span
            for line in range(5):                     # X: vertical lines
                x = bx + line * round(1.6 * MM)
                planes[0, y0:y0 + 120, x] = True
                planes[s, y0:y0 + 120, x + k] = True
            yy = y0 + 160 + 40                        # Y: dashes side by side
            planes[0, yy, bx:bx + 60] = True
            planes[s, yy + k, bx + 60:bx + 120] = True
            planes[0, yy + 60, bx:bx + 60] = True
            planes[s, yy + 60 + k, bx + 60:bx + 120] = True
    return planes
