"""Minimal reader for CUPS raster (v1/v2/v3) and PWG raster streams.

Only what a monochrome inkjet needs: 1 or 8 bits per pixel, one colour.
"""
import struct
from dataclasses import dataclass
from typing import BinaryIO, Iterator

import numpy as np

HEADER_SIZE = 1796
SYNC_BE = {b"RaSt": 1, b"RaS2": 2, b"RaS3": 3}
SYNC_LE = {b"tSaR": 1, b"2SaR": 2, b"3SaR": 3}

# cups_cspace_t values where a set bit / high value means ink (CUPS_CSPACE_K).
# Luminance spaces (W = 0, SW = 18) are the other way round: 0 = black.
BLACK_IS_ONE = {3}


@dataclass
class PageHeader:
    hw_res: tuple
    width: int
    height: int
    bits_per_color: int
    bits_per_pixel: int
    bytes_per_line: int
    color_order: int
    color_space: int
    num_copies: int
    page_size_pt: tuple
    media_type: str
    cups_integer: tuple


def _parse_header(raw: bytes, endian: str) -> PageHeader:
    u = lambda off: struct.unpack_from(endian + "I", raw, off)[0]  # noqa: E731
    return PageHeader(
        hw_res=(u(276), u(280)),
        width=u(372), height=u(376),
        bits_per_color=u(384), bits_per_pixel=u(388), bytes_per_line=u(392),
        color_order=u(396), color_space=u(400),
        num_copies=u(340),
        page_size_pt=(u(352), u(356)),
        media_type=raw[128:192].split(b"\0")[0].decode(errors="replace"),
        cups_integer=struct.unpack_from(endian + "16I", raw, 452),
    )


def read_pages(f: BinaryIO) -> Iterator[tuple[PageHeader, np.ndarray]]:
    """Yield (header, gray) with gray = uint8 array (height, width), 255 = white."""
    sync = f.read(4)
    if sync in SYNC_BE:
        endian, version = ">", SYNC_BE[sync]
    elif sync in SYNC_LE:
        endian, version = "<", SYNC_LE[sync]
    else:
        raise ValueError(f"not a CUPS raster stream (sync {sync!r})")
    while True:
        raw = f.read(HEADER_SIZE)
        if len(raw) < HEADER_SIZE:
            return
        h = _parse_header(raw, endian)
        if h.bits_per_pixel not in (1, 8) or h.color_order != 0:
            raise ValueError(f"unsupported raster: {h.bits_per_pixel} bpp, order {h.color_order}")
        if version == 2:
            data = _read_compressed(f, h)
        else:
            data = f.read(h.bytes_per_line * h.height)
        rows = np.frombuffer(data, np.uint8).reshape(h.height, h.bytes_per_line)
        if h.bits_per_pixel == 1:
            bits = np.unpackbits(rows, axis=1)[:, :h.width]
            ink = bits.astype(bool) if h.color_space in BLACK_IS_ONE else ~bits.astype(bool)
            gray = np.where(ink, 0, 255).astype(np.uint8)
        else:
            gray = rows[:, :h.width].copy()
            if h.color_space in BLACK_IS_ONE:
                gray = 255 - gray
        yield h, gray


def _read_compressed(f, h: PageHeader) -> bytes:
    """CUPS v2 / PWG compression: per line a repeat count, then runs of pixels."""
    bpp = max(1, h.bits_per_pixel // 8)
    out = bytearray()
    y = 0
    while y < h.height:
        rep = f.read(1)[0] + 1
        line = bytearray()
        while len(line) < h.bytes_per_line:
            c = f.read(1)[0]
            if c == 128:            # rest of line is white (PWG: fill with 0xFF / 0x00)
                fill = 0x00 if h.color_space in BLACK_IS_ONE else 0xFF
                line += bytes([fill]) * (h.bytes_per_line - len(line))
            elif c < 128:           # repeat next pixel c+1 times
                px = f.read(bpp)
                line += px * (c + 1)
            else:                   # 257-c literal pixels
                line += f.read((257 - c) * bpp)
        line = bytes(line[:h.bytes_per_line])
        for _ in range(min(rep, h.height - y)):
            out += line
        y += rep
    return bytes(out)
