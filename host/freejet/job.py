"""Turn pages into the byte stream the printer understands."""
from typing import Iterable, Iterator

import numpy as np

from . import protocol as P
from .swath import plan_swaths


class Sequencer:
    def __init__(self):
        self.seq = 0

    def __call__(self, mtype, payload=b""):
        self.seq = (self.seq + 1) & 0xFF
        return P.frame(mtype, payload, self.seq)


def job_frames(pages: Iterable[np.ndarray], *, bidirectional: bool = True,
               roll: bool = False, cut_pause: bool = False, max_cols: int = 5184,
               ring_bytes: int = 262144) -> Iterator[bytes]:
    """Yield protocol frames for a whole job. `pages` may be a lazy iterator."""
    f = Sequencer()
    yield f(P.JOB_BEGIN, bytes([P.JOB_ROLL if roll else 0, 0, 0, 0]))
    # keep 1/8 of the ring free so the next pass can stream in while printing
    max_bytes = ring_bytes - ring_bytes // 8
    for page in pages:
        length_um = round(page.shape[0] * P.UM_PER_COL) if roll else 0
        yield f(P.PAGE_BEGIN, length_um.to_bytes(4, "little") + bytes(4))
        for s in plan_swaths(page, bidirectional, max_cols, max_bytes):
            yield f(P.SWATH_BEGIN, P.swath_begin(s.y_um, s.x0, s.ncols, s.direction, len(s.data)))
            for i in range(0, len(s.data), P.MAX_PAYLOAD):
                yield f(P.SWATH_DATA, s.data[i:i + P.MAX_PAYLOAD])
        yield f(P.PAGE_END, bytes([P.PAGE_END_CUT_PAUSE if cut_pause else 0, 0, 0, 0]))
    yield f(P.JOB_END)
