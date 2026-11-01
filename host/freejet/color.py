"""Ink sets and colour separation.

A FreeJet carries 1 to 4 HP45-format cartridges side by side; each one can be
filled with a different ink. The ink set says what is in which slot (slot 0 is
the left-most cartridge in the carriage):

    K     1 cartridge:  black                       (the basic printer)
    KLK   2 cartridges: black, light black (grey)   smooth grayscale / photos
    CMY   3 cartridges: cyan, magenta, yellow       colour, black made from CMY
    CMYK  4 cartridges: black, cyan, magenta, yellow  colour with real black text

`separate()` turns an image into one bool "put a drop here" plane per slot.
"""
import numpy as np
from PIL import Image

INKSETS = {
    "K": ["K"],
    "KLK": ["K", "LK"],
    "CMY": ["C", "M", "Y"],
    "CMYK": ["K", "C", "M", "Y"],
}
INKSET_IDS = {name: i for i, name in enumerate(INKSETS)}

LK_STRENGTH = 0.33     # optical density of a light-black dot relative to black
TOTAL_INK = 2.6        # CMYK: max sum of coverages (paper can't take 400 %)


def _halftone(amount: np.ndarray, method: str, seed: int = 0) -> np.ndarray:
    """amount: float 0..1 (1 = solid ink) -> bool drops."""
    if method == "threshold":
        return amount >= 0.5
    if method == "ordered":
        bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5
        # shift the matrix per plane so the colour screens don't sit on top of each other
        yy = (np.arange(amount.shape[0])[:, None] + seed) % 4
        xx = (np.arange(amount.shape[1])[None, :] + 2 * seed) % 4
        return amount * 16 > bayer[yy, xx]
    # error diffusion (Floyd-Steinberg) in C via Pillow
    img = Image.fromarray(np.clip(255 - amount * 255 + 0.5, 0, 255).astype(np.uint8), "L")
    return ~np.asarray(img.convert("1", dither=Image.Dither.FLOYDSTEINBERG), dtype=bool)


def _crisp(v: np.ndarray, lo: float = 0.08, hi: float = 0.92) -> np.ndarray:
    """'auto' mode: snap nearly-white to white and nearly-solid to solid so text and
    lines stay sharp; only real mid-tones get dithered."""
    out = (v - lo) / (hi - lo)
    return np.clip(out, 0, 1)


def separate(img: Image.Image, inkset: str = "K", dither: str = "auto",
             gamma: float = 1.0) -> np.ndarray:
    """Return bool array (planes, height, width) in slot order."""
    if inkset not in INKSETS:
        raise ValueError(f"unknown ink set {inkset!r} (choose from {', '.join(INKSETS)})")
    method = "fs" if dither == "auto" else dither
    crisp = _crisp if dither == "auto" else (lambda v: v)
    lin = (lambda v: np.power(np.clip(v, 0, 1), gamma)) if gamma != 1.0 else (lambda v: v)

    if inkset in ("K", "KLK"):
        d = 1.0 - np.asarray(img.convert("L"), dtype=np.float32) / 255.0   # darkness 0..1
        d = crisp(d)
        if inkset == "K":
            return _halftone(lin(d), method)[None]
        # black only where it's darker than light black can go; light black does the rest
        k = np.clip((d - 0.30) / 0.70, 0, 1)
        lk = np.clip((d - k) / LK_STRENGTH, 0, 1)
        return np.stack([_halftone(lin(k), method, 0), _halftone(lin(lk), method, 1)])

    rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    c, m, y = (crisp(1.0 - rgb[..., i]) for i in range(3))
    if inkset == "CMY":
        return np.stack([_halftone(lin(p), method, s) for s, p in enumerate((c, m, y))])
    # CMYK: grey component replacement - neutral greys and black text use the black ink
    k = np.minimum(np.minimum(c, m), y)
    c, m, y = c - k, m - k, y - k
    total = c + m + y + k
    scale = np.where(total > TOTAL_INK, (TOTAL_INK - k) / np.maximum(c + m + y, 1e-6), 1.0)
    c, m, y = c * scale, m * scale, y * scale
    return np.stack([_halftone(lin(p), method, s) for s, p in enumerate((k, c, m, y))])
