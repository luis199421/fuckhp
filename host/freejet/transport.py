"""Talk to a real FreeJet over USB (CDC-ACM serial; no driver install needed
on Windows 10+, macOS or Linux)."""
import queue
import struct
import threading
import time

from . import protocol as P

USB_VID = 0x1209   # pid.codes
USB_PID = 0x0001   # pid.codes shared *test* PID - get a real one before selling any
PRODUCT = "FreeJet"


class PrinterError(RuntimeError):
    pass


def find_ports():
    """Return [(device, serial_number, description)] of attached printers."""
    from serial.tools import list_ports
    out = []
    for p in list_ports.comports():
        if (p.vid, p.pid) == (USB_VID, USB_PID) or (p.product or "").startswith(PRODUCT):
            out.append((p.device, p.serial_number or "", p.product or p.description))
    return out


def port_for_serial(serial_number: str | None):
    ports = find_ports()
    for dev, sn, _ in ports:
        if not serial_number or sn == serial_number:
            return dev
    raise PrinterError("no FreeJet printer found on USB" +
                       (f" with serial {serial_number}" if serial_number else ""))


class Printer:
    def __init__(self, port: str | None = None, timeout: float = 5.0, link=None):
        if link is None:
            import serial
            link = serial.Serial(port or port_for_serial(None), 115200, timeout=0.05,
                                 write_timeout=None)
        self.link = link
        self.timeout = timeout
        self.seq = 0
        self.parser = P.Parser()
        self.inbox: "queue.Queue[P.Frame]" = queue.Queue()
        self.on_event = None
        self._stop = threading.Event()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def close(self):
        self._stop.set()
        self._reader.join(1)
        self.link.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    # -- low level -------------------------------------------------------------
    def _read_loop(self):
        while not self._stop.is_set():
            try:
                data = self.link.read(4096)
            except Exception:  # port vanished
                break
            if not data:
                continue
            for fr in self.parser.feed(data):
                if fr.type == P.EVENT and self.on_event:
                    self.on_event(P.decode_event(fr.payload))
                if fr.type == P.LOG:
                    continue
                self.inbox.put(fr)

    def _next_seq(self):
        self.seq = (self.seq + 1) & 0xFF
        return self.seq

    def send(self, mtype, payload=b""):
        seq = self._next_seq()
        self.link.write(P.frame(mtype, payload, seq))
        return seq

    def wait_for(self, pred, timeout=None):
        end = time.monotonic() + (timeout or self.timeout)
        while True:
            left = end - time.monotonic()
            if left <= 0:
                raise PrinterError("printer did not answer (timeout)")
            try:
                fr = self.inbox.get(timeout=left)
            except queue.Empty:
                continue
            if pred(fr):
                return fr

    def request(self, mtype, payload=b"", reply=P.ACK, timeout=None):
        seq = self.send(mtype, payload)

        def match(fr):
            if fr.type == P.ACK:
                s, _, code = P.ACK_S.unpack(fr.payload[:4])
                if s != seq:
                    return None
                if code:
                    return True
                return reply == P.ACK
            return fr.type == reply
        fr = self.wait_for(match, timeout)
        if fr.type == P.ACK:
            _, _, code = P.ACK_S.unpack(fr.payload[:4])
            if code:
                raise PrinterError(P.ERRORS.get(code, f"error {code}"))
        return fr

    # -- high level -------------------------------------------------------------
    def info(self):
        return P.decode_info(self.request(P.HELLO, reply=P.INFO).payload)

    def status(self):
        return P.decode_status(self.request(P.GET_STATUS, reply=P.STATUS).payload)

    def get_param(self, pid):
        fr = self.request(P.PARAM_GET, struct.pack("<H", pid), reply=P.PARAM)
        return P.PARAM_S.unpack(fr.payload[:8])[2]

    def set_param(self, pid, value):
        self.request(P.PARAM_SET, P.PARAM_S.pack(pid, 0, int(value)))

    def simple(self, mtype, payload=b"", timeout=60):
        self.request(mtype, payload, timeout=timeout)

    def stream(self, frames, progress=None):
        """Send a job stream; the USB link itself throttles us when the printer's
        buffer is full. Raises on the first error the printer reports."""
        errors = []
        done = threading.Event()

        def ev(e):
            if e["code"] in (P.EV_ERROR, P.EV_ABORTED):
                errors.append(e.get("error", e["event"]))
                done.set()
            elif e["code"] == P.EV_JOB_DONE:
                done.set()
            if progress:
                progress(e)
        self.on_event = ev
        try:
            for fr in frames:
                if errors:
                    break
                self.link.write(fr)
                self._drain_acks(errors)
            while not done.wait(0.2):
                self._drain_acks(errors)
                if errors:
                    break
        finally:
            self.on_event = None
        if errors:
            raise PrinterError(errors[0])

    def _drain_acks(self, errors):
        while True:
            try:
                fr = self.inbox.get_nowait()
            except queue.Empty:
                return
            if fr.type == P.ACK:
                _, typ, code = P.ACK_S.unpack(fr.payload[:4])
                if code:
                    errors.append(P.ERRORS.get(code, f"error {code}"))
