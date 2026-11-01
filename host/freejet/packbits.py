"""PackBits run-length coding (the TIFF/Apple variant).

Control byte n:
  0..127   -> copy the next n+1 bytes literally
  129..255 -> repeat the next byte 257-n times (2..128 copies)
  128      -> no-op (never emitted)
"""


def encode(data: bytes) -> bytes:
    out = bytearray()
    n = len(data)
    i = 0
    while i < n:
        # length of the run starting at i
        run = 1
        while i + run < n and run < 128 and data[i + run] == data[i]:
            run += 1
        if run >= 2:
            out.append(257 - run)
            out.append(data[i])
            i += run
            continue
        # literal: extend until a run of >=2 (a 2-run inside a literal costs the same
        # either way, so only break on runs of 3+ to keep literals long)
        start = i
        i += 1
        while i < n and i - start < 128:
            if i + 2 < n and data[i] == data[i + 1] == data[i + 2]:
                break
            i += 1
        out.append(i - start - 1)
        out += data[start:i]
    return bytes(out)


def decode(data: bytes, expected_len: int | None = None) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        c = data[i]
        i += 1
        if c < 128:
            cnt = c + 1
            if i + cnt > n:
                raise ValueError("truncated literal")
            out += data[i:i + cnt]
            i += cnt
        elif c > 128:
            if i >= n:
                raise ValueError("truncated run")
            out += bytes([data[i]]) * (257 - c)
            i += 1
    if expected_len is not None and len(out) != expected_len:
        raise ValueError(f"decoded {len(out)} bytes, expected {expected_len}")
    return bytes(out)
