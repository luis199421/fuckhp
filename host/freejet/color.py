"""Ink sets and colour separation for HP 63/302-type cartridges.

FreeJet takes a black cartridge, a tri-colour cartridge, or both, side by side:

    K     black cartridge                         text, line art, halftoned grey
    CMY   colour cartridge                        colour; black mixed from C+M+Y
    KCMY  black + colour cartridges               colour with real black text

`separate()` turns an image into one bool "put a drop here" plane per ink.
The colour cartridge has its nozzles 1/300 in apart, so colour planes are
halftoned at 600 x 300 dpi and only use every other row.
"""
import numpy as np
from PIL import Image

INKSETS = {
    "K": ["K"],
    "CMY": ["C", "M", "Y"],
    "KCMY": ["K", "C", "M", "Y"],
}
INKSET_IDS = {name: i for i, name in enumerate(INKSETS)}

TOTAL_INK = 2.6        # KCMY: max sum of coverages (paper can't take 400 %)


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


def _halftone_300(amount: np.ndarray, method: str, seed: int = 0) -> np.ndarray:
    """Halftone at half the vertical resolution and put the drops on even rows only."""
    h = amount.shape[0]
    a = amount[: h - h % 2].reshape(h // 2, 2, -1).mean(axis=1) if h > 1 else amount
    dots = _halftone(a, method, seed)
    out = np.zeros(amount.shape, bool)
    out[0:2 * dots.shape[0]:2] = dots
    return out


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

    if inkset == "K":
        d = 1.0 - np.asarray(img.convert("L"), dtype=np.float32) / 255.0   # darkness 0..1
        return _halftone(lin(crisp(d)), method)[None]

    rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    c, m, y = (crisp(1.0 - rgb[..., i]) for i in range(3))
    if inkset == "CMY":
        return np.stack([_halftone_300(lin(p), method, s) for s, p in enumerate((c, m, y))])
    # KCMY: grey component replacement - neutral greys and black text use the black ink
    k = np.minimum(np.minimum(c, m), y)
    c, m, y = c - k, m - k, y - k
    total = c + m + y + k
    scale = np.where(total > TOTAL_INK, (TOTAL_INK - k) / np.maximum(c + m + y, 1e-6), 1.0)
    c, m, y = c * scale, m * scale, y * scale
    return np.stack([_halftone(lin(k), method, 0)] +
                    [_halftone_300(lin(p), method, s + 1) for s, p in enumerate((c, m, y))])
