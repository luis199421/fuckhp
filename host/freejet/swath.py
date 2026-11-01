"""Cut a 1-bit page into printhead passes ("swaths") and encode them.

Page bitmap convention: numpy bool array, shape (rows, cols) at 600 dpi,
True = put ink there, pixel (0, 0) = top-left corner of the paper as it comes
out of the printer (the leading edge is the top).

A swath covers 300 consecutive pixel rows. Row 0 of a swath is the row under
the nozzle closest to the paper exit (the firmware maps rows to physical
nozzles, so the host never needs the HP45 nozzle table).

Swath data = for each pixel column, in the order the carriage meets them,
300 bits packed LSB-first into 38 bytes (row r -> byte r // 8, bit r % 8);
the whole thing PackBits-compressed.
"""
from dataclasses import dataclass

import numpy as np

from . import packbits
from .protocol import COL_BYTES, ROWS, UM_PER_COL


@dataclass
class Swath:
    y_px: int          # page row under swath row 0
    x0: int            # first (left-most) pixel column
    ncols: int
    direction: int     # 0 = left-to-right, 1 = right-to-left
    data: bytes        # PackBits-compressed column data, firing order

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
    if page.dtype != bool:
        page = page.astype(bool)
    h, w = page.shape
    if w > max_cols:
        if page[:, max_cols:].any():
            raise ValueError(f"page has ink beyond column {max_cols} (printer limit)")
        page = page[:, :max_cols]
        w = max_cols
    inked_rows = np.flatnonzero(page.any(axis=1))
    swaths: list[Swath] = []
    direction = 0
    ri = 0
    while ri < len(inked_rows):
        y = int(inked_rows[ri])
        band = np.zeros((ROWS, w), dtype=bool)
        chunk = page[y:y + ROWS]
        band[:chunk.shape[0]] = chunk
        cols = np.flatnonzero(band.any(axis=0))
        x0, x1 = int(cols[0]), int(cols[-1]) + 1
        colbytes = column_bytes(band[:, x0:x1])
        for sx0, sx1 in _split(colbytes, x0, x1, max_bytes):
            part = colbytes[sx0 - x0:sx1 - x0]
            if direction == 1:
                part = part[::-1]
            swaths.append(Swath(y, sx0, sx1 - sx0, direction,
                                packbits.encode(part.tobytes())))
            if bidirectional:
                direction ^= 1
        ri = int(np.searchsorted(inked_rows, y + ROWS))
    return swaths


def _split(colbytes, x0, x1, max_bytes):
    """Split a pass into column ranges whose raw size fits the device buffer."""
    if max_bytes is None or (x1 - x0) * COL_BYTES <= max_bytes:
        return [(x0, x1)]
    step = max(1, max_bytes // COL_BYTES)
    return [(a, min(a + step, x1)) for a in range(x0, x1, step)]


def render_swaths(swaths: list[Swath], height: int, width: int) -> np.ndarray:
    """Inverse of plan_swaths (used by the emulator and tests)."""
    page = np.zeros((height + ROWS, width), dtype=bool)
    for s in swaths:
        raw = packbits.decode(s.data, s.ncols * COL_BYTES)
        cols = np.frombuffer(raw, dtype=np.uint8).reshape(s.ncols, COL_BYTES)
        if s.direction == 1:
            cols = cols[::-1]
        bits = np.unpackbits(cols, axis=1, bitorder="little")[:, :ROWS].T.astype(bool)
        page[s.y_px:s.y_px + ROWS, s.x0:s.x0 + s.ncols] |= bits
    return page[:height]
