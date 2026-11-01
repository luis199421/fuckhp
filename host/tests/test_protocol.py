import random

import numpy as np

from freejet import packbits
from freejet import protocol as P


def test_crc_reference_vector():
    assert P.crc16(b"123456789") == 0x29B1   # CRC-16/CCITT-FALSE check value


def test_frame_roundtrip_with_garbage_and_splits():
    frames = [P.frame(P.SWATH_DATA, bytes(range(256)) * 10, 7), P.frame(P.HELLO, b"", 8)]
    stream = b"\x00garbage F" + frames[0] + b"FJ\xff" + frames[1]
    pr = P.Parser()
    got = []
    for i in range(0, len(stream), 13):
        got += pr.feed(stream[i:i + 13])
    assert [(f.type, f.seq) for f in got] == [(P.SWATH_DATA, 7), (P.HELLO, 8)]
    assert got[0].payload == bytes(range(256)) * 10


def test_corrupt_frame_rejected():
    f = bytearray(P.frame(P.FEED, b"\x01\x02\x03\x04", 1))
    f[9] ^= 0xFF
    assert P.Parser().feed(bytes(f)) == []


def test_packbits_roundtrip():
    rng = random.Random(1)
    cases = [b"", b"a", b"aa", b"abc", b"\0" * 1000, bytes(rng.randrange(256) for _ in range(5000))]
    cases += [bytes(rng.choice([0, 0, 0, 255, rng.randrange(256)]) for _ in range(3000)) for _ in range(20)]
    for c in cases:
        enc = packbits.encode(c)
        assert packbits.decode(enc, len(c)) == c
        assert len(enc) <= len(c) + (len(c) + 127) // 128 + 1


def test_packbits_compresses_blank_columns():
    blank = bytes(P.COL_BYTES * 5000)
    assert len(packbits.encode(blank)) < len(blank) // 60


def test_struct_sizes_match_firmware():
    assert P.INFO_S.size == 32
    assert P.STATUS_S.size == 24
    assert P.SWATH_S.size == 16
    assert P.EVENT_S.size == 8
