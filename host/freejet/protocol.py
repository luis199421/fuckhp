"""FreeJet USB wire protocol (host side). See docs/05-protocol.md.

Every message is a frame:

    offset size  field
    0      2     magic "FJ"
    2      1     type
    3      1     seq      (host picks; device echoes it in ACK)
    4      4     length N (little-endian, N <= MAX_PAYLOAD)
    8      N     payload  (little-endian structs)
    8+N    2     CRC-16/CCITT-FALSE over bytes 2 .. 8+N-1 (type..payload)
"""
import struct
from dataclasses import dataclass

MAGIC = b"FJ"
HEADER = struct.Struct("<2sBBI")
MAX_PAYLOAD = 16384
PROTO_VERSION = 2

DPI = 600
# HP 63/302 cartridges: the black one prints 324 rows (1/600 in) per pass, the colour one
# 84 rows per colour at 1/300 in = 168 rows of 1/600 in. Columns carry 336 bits (42 bytes).
ROWS_K = 324                  # rows per pass, black cartridge only
ROWS_COLOR = 168              # rows per pass when the colour cartridge is used
ROWS = 336                    # bits per column in the data format
MAX_PLANES = 4
COL_BYTES = ROWS // 8         # 42 bytes per pixel column
UM_PER_COL = 25400 / DPI      # 42.333 um

# host -> device
HELLO = 0x01
GET_STATUS = 0x02
JOB_BEGIN = 0x10
PAGE_BEGIN = 0x11
SWATH_BEGIN = 0x12
SWATH_DATA = 0x13
PAGE_END = 0x14
JOB_END = 0x15
FEED = 0x16
PARAM_GET = 0x20
PARAM_SET = 0x21
PARAM_SAVE = 0x22
PARAM_DEFAULTS = 0x23
HOME = 0x30
PARK = 0x31
SPIT = 0x32
MOTORS_OFF = 0x33
MOVE_X = 0x34
NOZZLE_FIRE = 0x35            # u16 cartridge (0 black, 1 colour, 0xFFFF both), u16 count
ABORT = 0x3F
BOOTSEL = 0x7F

# device -> host
ACK = 0x80
INFO = 0x81
STATUS = 0x82
EVENT = 0x83
PARAM = 0x84
LOG = 0x85

# JOB_BEGIN flags
JOB_ROLL = 0x01
# JOB_BEGIN payload: u8 flags, u8 planes (0 = 1), u8 ink set id (0 K, 1 CMY, 2 KCMY), u8 pad
# SWATH_BEGIN flags
SWATH_PACKBITS = 0x01
# with planes > 1, SWATH_BEGIN is followed by u32 plane_len[planes]; data = planes back to back
# PAGE_END flags
PAGE_END_CUT_PAUSE = 0x01

STATES = {0: "idle", 1: "busy", 2: "printing", 3: "waiting for paper",
          4: "waiting for button", 5: "error"}
STATUS_FLAGS = ["homed", "paper", "head", "head_power", "motors", "job",
                "wait_paper", "wait_button"]

EVENTS = {1: "paper_needed", 2: "paper_loaded", 3: "page_done", 4: "job_done",
          5: "error", 6: "cut_now", 7: "head_hot_pause", 8: "aborted"}
EV_PAPER_NEEDED, EV_PAPER_LOADED, EV_PAGE_DONE, EV_JOB_DONE, EV_ERROR, \
    EV_CUT_NOW, EV_HEAD_HOT, EV_ABORTED = range(1, 9)

ERRORS = {
    0: "ok", 1: "bad crc", 2: "bad frame", 3: "unknown command", 4: "bad argument",
    5: "busy", 6: "no cartridge detected", 7: "not homed", 8: "homing failed",
    9: "position out of range", 10: "swath too big", 11: "data underrun",
    12: "paper jam", 13: "printhead too hot", 14: "no head voltage", 15: "aborted",
    16: "flash write failed", 17: "queue full", 18: "paper cannot move backwards",
    19: "no job active", 20: "unknown parameter", 21: "column rate too high for speed",
    22: "the job's ink set doesn't match the cartridges fitted (param cartridges)",
    23: "content goes past the printable bottom of the sheet",
}

INFO_S = struct.Struct("<HH16sIHHHH")          # 32 bytes
STATUS_S = struct.Struct("<BBHHHIBBHii")       # 24 bytes
EVENT_S = struct.Struct("<BBHi")
ACK_S = struct.Struct("<BBH")
PARAM_S = struct.Struct("<HHi")
SWATH_S = struct.Struct("<ihHBBHI")            # 16 bytes


def crc16(data: bytes, crc: int = 0xFFFF) -> int:
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


try:  # binascii has a fast table-driven CRC-CCITT (same polynomial, caller sets init)
    import binascii

    def crc16(data: bytes, crc: int = 0xFFFF) -> int:  # noqa: F811
        return binascii.crc_hqx(data, crc)
except ImportError:  # pragma: no cover
    pass


def frame(mtype: int, payload: bytes = b"", seq: int = 0) -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload too large")
    head = HEADER.pack(MAGIC, mtype, seq & 0xFF, len(payload))
    body = head[2:] + payload
    return head + payload + struct.pack("<H", crc16(body))


@dataclass
class Frame:
    type: int
    seq: int
    payload: bytes


class Parser:
    """Incremental frame parser: feed() bytes, iterate complete frames."""

    def __init__(self):
        self.buf = bytearray()
        self.errors = 0

    def feed(self, data: bytes):
        self.buf += data
        out = []
        while True:
            i = self.buf.find(MAGIC)
            if i < 0:
                # keep a trailing 'F' in case the magic is split
                del self.buf[:max(0, len(self.buf) - 1)]
                break
            if i:
                del self.buf[:i]
                self.errors += 1
            if len(self.buf) < HEADER.size:
                break
            _, mtype, seq, n = HEADER.unpack_from(self.buf)
            if n > MAX_PAYLOAD:
                del self.buf[:2]
                self.errors += 1
                continue
            total = HEADER.size + n + 2
            if len(self.buf) < total:
                break
            body = bytes(self.buf[2:HEADER.size + n])
            (crc,) = struct.unpack_from("<H", self.buf, HEADER.size + n)
            if crc != crc16(body):
                del self.buf[:2]
                self.errors += 1
                continue
            out.append(Frame(mtype, seq, bytes(self.buf[HEADER.size:HEADER.size + n])))
            del self.buf[:total]
        return out


# ---- payload helpers ------------------------------------------------------

def swath_begin(y_um: int, x0: int, ncols: int, direction: int, data_len: int,
                flags: int = SWATH_PACKBITS, plane_lens: list[int] | None = None) -> bytes:
    head = SWATH_S.pack(y_um, x0, ncols, direction, flags, 0, data_len)
    if plane_lens and len(plane_lens) > 1:
        assert sum(plane_lens) == data_len
        head += struct.pack(f"<{len(plane_lens)}I", *plane_lens)
    return head


def job_begin(roll: bool = False, planes: int = 1, inkset_id: int = 0) -> bytes:
    return bytes([JOB_ROLL if roll else 0, planes, inkset_id, 0])


def decode_info(p: bytes) -> dict:
    proto, fw, model, ring, dpi, rows, max_cols, max_payload = INFO_S.unpack(p[:INFO_S.size])
    return dict(proto=proto, fw=f"{fw >> 8}.{fw & 0xFF}", model=model.rstrip(b"\0").decode(),
                ring_bytes=ring, dpi=dpi, rows=rows, max_cols=max_cols, max_payload=max_payload)


def encode_info(model="FJ-2", fw=(2, 0), ring=262144, max_cols=5184) -> bytes:
    return INFO_S.pack(PROTO_VERSION, (fw[0] << 8) | fw[1], model.encode()[:16], ring,
                       DPI, ROWS_K, max_cols, MAX_PAYLOAD)


def decode_status(p: bytes) -> dict:
    (state, flags, error, tsr, vhd, ring_free, qlen, last_ev, pages, paper_y,
     x_um) = STATUS_S.unpack(p[:STATUS_S.size])
    return dict(state=STATES.get(state, state), flags=[f for i, f in enumerate(STATUS_FLAGS)
                if flags & (1 << i)], error=ERRORS.get(error, error), tsr=tsr, vhd_mv=vhd,
                ring_free=ring_free, queue=qlen, last_event=EVENTS.get(last_ev, last_ev),
                pages=pages, paper_y_um=paper_y, x_um=x_um)


def decode_event(p: bytes) -> dict:
    code, _, arg, value = EVENT_S.unpack(p[:EVENT_S.size])
    d = dict(event=EVENTS.get(code, code), code=code, arg=arg, value=value)
    if code == EV_ERROR:
        d["error"] = ERRORS.get(arg, arg)
    return d
