"""CUPS backend:  freejet://FJ-1?serial=XXXX

Installed as <cups>/backend/freejet with mode 0700 (runs as root so it can
open /dev/ttyACM*). With no arguments it lists attached printers; with
job arguments it copies the filter output to the printer and reports the
printer's state (out of paper, errors) back to CUPS.
"""
import os
import sys
import urllib.parse

from . import protocol as P
from .transport import Printer, PrinterError, find_ports, port_for_serial

CUPS_BACKEND_OK, CUPS_BACKEND_FAILED, CUPS_BACKEND_STOP, CUPS_BACKEND_RETRY = 0, 1, 4, 6


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def discover():
    for dev, sn, desc in find_ports():
        uri = "freejet://FJ-1" + (f"?serial={urllib.parse.quote(sn)}" if sn else "")
        print(f'direct {uri} "FreeJet FJ-1" "FreeJet FJ-1 USB ({sn or dev})" '
              f'"MFG:FreeJet;MDL:FJ-1;CMD:FJRASTER;CLS:PRINTER;" ""', flush=True)
    return CUPS_BACKEND_OK


def frames_from(stream):
    """Re-chunk the filter's byte stream at frame boundaries."""
    parser = P.Parser()
    while True:
        data = stream.read(65536)
        if not data:
            return
        for fr in parser.feed(data):
            yield P.frame(fr.type, fr.payload, fr.seq)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) == 1:
        return discover()
    if len(argv) not in (6, 7):
        log("Usage: freejet job-id user title copies options [file]")
        return CUPS_BACKEND_FAILED
    uri = os.environ.get("DEVICE_URI", "")
    q = urllib.parse.parse_qs(urllib.parse.urlparse(uri).query)
    serial = q.get("serial", [None])[0]
    try:
        port = port_for_serial(serial)
    except PrinterError as e:
        log(f"INFO: {e}; waiting")
        return CUPS_BACKEND_RETRY
    src = open(argv[6], "rb") if len(argv) == 7 else sys.stdin.buffer

    def progress(e):
        ev = e["event"]
        if ev == "paper_needed":
            log("STATE: +media-needed")
            log("INFO: Insert paper into the rear slot")
        elif ev == "paper_loaded":
            log("STATE: -media-needed")
        elif ev == "cut_now":
            log("INFO: Cut the page, then press the button")
        elif ev == "page_done":
            log(f"INFO: Page {e['value']} done")
        elif ev == "head_hot_pause":
            log("INFO: Letting the printhead cool down")

    try:
        with Printer(port) as pr:
            info = pr.info()
            log(f"DEBUG: printer {info}")
            st = pr.status()
            if "head" not in st["flags"]:
                log("STATE: +cover-open")
                log("ERROR: No ink cartridge detected")
                return CUPS_BACKEND_STOP
            pr.stream(frames_from(src), progress)
    except PrinterError as e:
        log(f"ERROR: {e}")
        return CUPS_BACKEND_FAILED
    except OSError as e:
        log(f"ERROR: USB connection lost: {e}")
        return CUPS_BACKEND_RETRY
    log("STATE: -media-needed")
    return CUPS_BACKEND_OK


if __name__ == "__main__":
    sys.exit(main())
