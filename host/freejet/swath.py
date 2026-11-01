"""Cut a 1-bit page into printhead passes ("swaths") and encode them.

Page bitmap convention: numpy bool array, shape (rows, cols) at 600 dpi, or
(planes, rows, cols) for several cartridges (one plane per ink slot).
True = put ink there, pixel (0, 0) = top-left corner of the paper as it comes
out of the printer (the leading edge is the top).

With several planes (CMY or KCMY) every plane is compressed separately and
the planes travel back to back in one pass.

A swath covers 324 consecutive pixel rows with the black cartridge alone, 168
when the colour cartridge is used. Row 0 of a swath is the row under the nozzle
closest to the paper exit (the firmware maps rows to physical nozzles, so the
host never needs the cartridge's nozzle tables).

Swath data = for each pixel column, in the order the carriage meets them,
336 bits packed LSB-first into 42 bytes (row r -> byte r // 8, bit r % 8);
the whole thing PackBits-compressed.
"""
from dataclasses import dataclass

import numpy as np

from . import packbits
from .protocol import COL_BYTES, ROWS, ROWS_COLOR, ROWS_K, UM_PER_COL


@dataclass
class Swath:
    y_px: int          # page row under swath row 0
    x0: int            # first (left-most) pixel column
    ncols: int
    direction: int     # 0 = left-to-right, 1 = right-to-left
    data: bytes        # PackBits-compressed column data, firing order (all planes)
    plane_lens: tuple = ()   # length of each plane's part of `data` (multi-plane only)

    @property
    def y_um(self) -> int:
        return round(self.y_px * UM_PER_COL)


def column_bytes(band: np.ndarray) -> np.ndarray:
    """band: bool (ROWS, ncols) -> uint8 (ncols, COL_BYTES)."""
    assert band.shape[0] == ROWS
    return np.packbits(band.T, axis=1, bitorder="little")


def plan_swaths(page: np.ndarray, bidirectional: bool = True, max_cols: int = 5184,
                max_bytes: int | None = None) -> list[Swath]:
    """Greedy plan: start each pass at the next inked row, skip blank space."""
    planes = page[None] if page.ndim == 2 else page
    planes = planes.astype(bool, copy=False)
    n_pl, h, w = planes.shape
    rows = ROWS_K if n_pl == 1 else ROWS_COLOR
    if w > max_cols:
        if planes[:, :, max_cols:].any():
            raise ValueError(f"page has ink beyond column {max_cols} (printer limit)")
        planes = planes[:, :, :max_cols]
        w = max_cols
    any_ink = planes.any(axis=0)
    inked_rows = np.flatnonzero(any_ink.any(axis=1))
    swaths: list[Swath] = []
    direction = 0
    ri = 0
    while ri < len(inked_rows):
        y = int(inked_rows[ri])
        band = np.zeros((n_pl, ROWS, w), dtype=bool)
        chunk = planes[:, y:y + rows]
        band[:, :chunk.shape[1]] = chunk
        cols = np.flatnonzero(band.any(axis=(0, 1)))
        x0, x1 = int(cols[0]), int(cols[-1]) + 1
        colbytes = [column_bytes(band[p, :, x0:x1]) for p in range(n_pl)]
        limit = None if max_bytes is None else max_bytes // n_pl
        for sx0, sx1 in _split(colbytes[0], x0, x1, limit):
            parts = []
            for p in range(n_pl):
                part = colbytes[p][sx0 - x0:sx1 - x0]
                if direction == 1:
                    part = part[::-1]
                parts.append(packbits.encode(part.tobytes()))
            swaths.append(Swath(y, sx0, sx1 - sx0, direction, b"".join(parts),
                                tuple(len(x) for x in parts) if n_pl > 1 else ()))
            if bidirectional:
                direction ^= 1
        ri = int(np.searchsorted(inked_rows, y + rows))
    return swaths


def _split(colbytes, x0, x1, max_bytes):
    """Split a pass into column ranges whose raw size fits the device buffer."""
    if max_bytes is None or (x1 - x0) * COL_BYTES <= max_bytes:
        return [(x0, x1)]
    step = max(1, max_bytes // COL_BYTES)
    return [(a, min(a + step, x1)) for a in range(x0, x1, step)]


def decode_swath(s: Swath, n_planes: int = 1) -> np.ndarray:
    """-> bool (planes, ROWS, ncols) in left-to-right order."""
    lens = s.plane_lens or (len(s.data),)
    out, off = [], 0
    for ln in lens:
        raw = packbits.decode(s.data[off:off + ln], s.ncols * COL_BYTES)
        off += ln
        cols = np.frombuffer(raw, dtype=np.uint8).reshape(s.ncols, COL_BYTES)
        if s.direction == 1:
            cols = cols[::-1]
        out.append(np.unpackbits(cols, axis=1, bitorder="little")[:, :ROWS].T.astype(bool))
    return np.stack(out)


def render_swaths(swaths: list[Swath], height: int, width: int, n_planes: int = 1) -> np.ndarray:
    """Inverse of plan_swaths (used by the emulator and tests)."""
    page = np.zeros((n_planes, height + ROWS, width), dtype=bool)
    for s in swaths:
        page[:, s.y_px:s.y_px + ROWS, s.x0:s.x0 + s.ncols] |= decode_swath(s, n_planes)
    page = page[:, :height]
    return page[0] if n_planes == 1 else page
