"""A software FreeJet: speaks the same protocol, "prints" into numpy pages.

Used by the test-suite and by `freejet preview`, so the whole host pipeline
can be checked without hardware. It enforces the same rules as the firmware
(no backward feeding, swath size vs. buffer, column range, job structure).
"""
import struct

import numpy as np

from . import packbits
from . import protocol as P
from .params import PARAMS, BY_ID


class VirtualPrinter:
    def __init__(self, ring_bytes: int = 262144, max_cols: int = 5184):
        self.ring_bytes = ring_bytes
        self.max_cols = max_cols
        self.parser = P.Parser()
        self.params = {p.id: p.default for p in PARAMS}
        self.pages: list[np.ndarray] = []
        self.events: list[dict] = []
        self.errors: list[str] = []
        self._out = bytearray()
        self._job = False
        self._roll = False
        self.n_heads = 1          # like the firmware's n_heads parameter
        self._planes = 1
        self._page = None
        self._paper_y_um = 0
        self._swath = None
        self._swath_buf = bytearray()
        self._pages_done = 0

    # -- transport-like interface --------------------------------------------
    def write(self, data: bytes):
        for fr in self.parser.feed(data):
            self._handle(fr)
        return len(data)

    def read_all(self) -> bytes:
        out, self._out = bytes(self._out), bytearray()
        return out

    # -- helpers --------------------------------------------------------------
    def _send(self, mtype, payload=b""):
        self._out += P.frame(mtype, payload)

    def _ack(self, fr, code=0):
        self._send(P.ACK, P.ACK_S.pack(fr.seq, fr.type, code))
        if code:
            self.errors.append(P.ERRORS.get(code, str(code)))

    def _event(self, code, arg=0, value=0):
        self.events.append(P.decode_event(P.EVENT_S.pack(code, 0, arg, value)))
        self._send(P.EVENT, P.EVENT_S.pack(code, 0, arg, value))

    def _ensure_rows(self, rows):
        if self._page.shape[1] < rows:
            grow = np.zeros((self._planes, rows - self._page.shape[1] + 2000, self.max_cols), bool)
            self._page = np.concatenate([self._page, grow], axis=1)

    def _handle(self, fr: P.Frame):
        t, p = fr.type, fr.payload
        if t == P.HELLO:
            self._send(P.INFO, P.encode_info(ring=self.ring_bytes, max_cols=self.max_cols))
        elif t == P.GET_STATUS:
            flags = 0b111 | (0b100000 if self._job else 0)
            self._send(P.STATUS, P.STATUS_S.pack(0 if not self._job else 2, flags, 0, 2048, 12000,
                                                  self.ring_bytes, 0, 0, self._pages_done,
                                                  self._paper_y_um, 0))
        elif t == P.PARAM_GET:
            (pid,) = struct.unpack_from("<H", p)
            if pid not in self.params:
                return self._ack(fr, 20)
            self._send(P.PARAM, P.PARAM_S.pack(pid, 0, self.params[pid]))
        elif t == P.PARAM_SET:
            pid, _, val = P.PARAM_S.unpack(p[:8])
            prm = BY_ID.get(pid)
            if prm is None:
                return self._ack(fr, 20)
            if not prm.min <= val <= prm.max:
                return self._ack(fr, 4)
            self.params[pid] = val
            self._ack(fr)
        elif t in (P.PARAM_SAVE, P.HOME, P.PARK, P.SPIT, P.MOTORS_OFF, P.MOVE_X,
                   P.NOZZLE_FIRE, P.FEED, P.ABORT, P.PARAM_DEFAULTS):
            if t == P.PARAM_DEFAULTS:
                self.params = {q.id: q.default for q in PARAMS}
            self._ack(fr)
        elif t == P.JOB_BEGIN:
            planes = max(1, p[1]) if len(p) > 1 else 1
            if planes != self.n_heads:
                return self._ack(fr, 22)
            self._job, self._roll, self._planes = True, bool(p[0] & P.JOB_ROLL), planes
            self._ack(fr)
        elif t == P.PAGE_BEGIN:
            if not self._job:
                return self._ack(fr, 19)
            self._page = np.zeros((self._planes, 4000, self.max_cols), bool)
            self._paper_y_um = 0
            self._ack(fr)
            self._event(P.EV_PAPER_LOADED)
        elif t == P.SWATH_BEGIN:
            if self._page is None:
                return self._ack(fr, 19)
            y_um, x0, ncols, direction, flags, _, n = P.SWATH_S.unpack(p[:P.SWATH_S.size])
            lens = (n,)
            if self._planes > 1:
                lens = struct.unpack_from(f"<{self._planes}I", p, P.SWATH_S.size)
                if sum(lens) != n:
                    return self._ack(fr, 4)
            if y_um < self._paper_y_um:
                return self._ack(fr, 18)
            if n > self.ring_bytes:
                return self._ack(fr, 10)
            if x0 < 0 or x0 + ncols > self.max_cols or ncols == 0:
                return self._ack(fr, 9)
            self._swath = (y_um, x0, ncols, direction, flags, n, lens)
            self._swath_buf = bytearray()
            self._ack(fr)
            if n == 0:
                self._finish_swath()
        elif t == P.SWATH_DATA:
            if self._swath is None:
                self.errors.append("data without swath")
                return
            self._swath_buf += p
            if len(self._swath_buf) >= self._swath[5]:
                self._finish_swath()
        elif t == P.PAGE_END:
            if self._page is None:
                return self._ack(fr, 19)
            self._ack(fr)
            used = np.flatnonzero(self._page.any(axis=(0, 2)))
            h = int(used[-1]) + 1 if len(used) else 0
            pg = self._page[:, :max(h, 1)].copy()
            self.pages.append(pg[0] if self._planes == 1 else pg)
            self._page = None
            self._pages_done += 1
            self._event(P.EV_PAGE_DONE, 0, self._pages_done)
        elif t == P.JOB_END:
            self._job = False
            self._ack(fr)
            self._event(P.EV_JOB_DONE)
        else:
            self._ack(fr, 3)

    def _finish_swath(self):
        y_um, x0, ncols, direction, flags, n, lens = self._swath
        data = bytes(self._swath_buf[:n])
        y = round(y_um / P.UM_PER_COL)
        self._ensure_rows(y + P.ROWS)
        off = 0
        for pl, ln in enumerate(lens):
            chunk = data[off:off + ln]
            off += ln
            raw = packbits.decode(chunk, ncols * P.COL_BYTES) if flags & P.SWATH_PACKBITS else chunk
            cols = np.frombuffer(raw, np.uint8).reshape(ncols, P.COL_BYTES)
            if direction == 1:
                cols = cols[::-1]
            bits = np.unpackbits(cols, axis=1, bitorder="little")[:, :P.ROWS].T.astype(bool)
            self._page[pl, y:y + P.ROWS, x0:x0 + ncols] |= bits
        self._paper_y_um = y_um
        self._swath = None
