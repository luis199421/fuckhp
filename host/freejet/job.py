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
               ring_bytes: int = 262144, inkset: str = "K") -> Iterator[bytes]:
    """Yield protocol frames for a whole job. `pages` may be a lazy iterator of
    (rows, cols) or (planes, rows, cols) arrays; planes must match the ink set."""
    from .color import INKSET_IDS, INKSETS
    n_planes = len(INKSETS[inkset])
    f = Sequencer()
    yield f(P.JOB_BEGIN, P.job_begin(roll, n_planes, INKSET_IDS[inkset]))
    # keep 1/8 of the ring free so the next pass can stream in while printing
    max_bytes = ring_bytes - ring_bytes // 8
    for page in pages:
        if (1 if page.ndim == 2 else page.shape[0]) != n_planes:
            raise ValueError(f"page has {1 if page.ndim == 2 else page.shape[0]} planes, "
                             f"ink set {inkset} needs {n_planes}")
        length_um = round(page.shape[-2] * P.UM_PER_COL) if roll else 0
        yield f(P.PAGE_BEGIN, length_um.to_bytes(4, "little") + bytes(4))
        for s in plan_swaths(page, bidirectional, max_cols, max_bytes):
            yield f(P.SWATH_BEGIN, P.swath_begin(s.y_um, s.x0, s.ncols, s.direction, len(s.data),
                                                 plane_lens=list(s.plane_lens)))
            for i in range(0, len(s.data), P.MAX_PAYLOAD):
                yield f(P.SWATH_DATA, s.data[i:i + P.MAX_PAYLOAD])
        yield f(P.PAGE_END, bytes([P.PAGE_END_CUT_PAUSE if cut_pause else 0, 0, 0, 0]))
    yield f(P.JOB_END)
