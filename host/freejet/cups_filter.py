"""CUPS filter: application/vnd.cups-raster -> FreeJet job stream.

Installed as  <cups>/filter/rastertofreejet  (see host/cups/install.sh).
CUPS calls:  rastertofreejet job-id user title copies options [file]
"""
import shlex
import sys

import numpy as np

from PIL import Image

from .cups_raster import read_pages
from .job import job_frames
from .raster import to_ink


def parse_options(s: str) -> dict:
    out = {}
    for tok in shlex.split(s or ""):
        k, _, v = tok.partition("=")
        out[k] = v if v else "true"
    return out


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) not in (6, 7):
        log("Usage: rastertofreejet job-id user title copies options [file]")
        return 1
    opts = parse_options(argv[5])
    bidir = opts.get("FJBidirectional", "True").lower() in ("true", "on", "yes", "1")
    dither = {"Threshold": "threshold", "Ordered": "ordered", "FS": "fs"}.get(
        opts.get("FJDither", "Auto"), "auto")
    roll = opts.get("FJMediaSource", "Sheet") == "Roll"
    cut_pause = roll and opts.get("FJCutPause", "True").lower() in ("true", "on", "yes", "1")
    src = open(argv[6], "rb") if len(argv) == 7 else sys.stdin.buffer

    def pages():
        for n, (h, gray) in enumerate(read_pages(src), 1):
            if h.hw_res != (600, 600):
                log(f"ERROR: raster must be 600x600 dpi, got {h.hw_res}")
                raise SystemExit(1)
            # copies are expanded upstream by CUPS (*cupsManualCopies: True)
            log(f"PAGE: {n} 1")
            log(f"INFO: Preparing page {n}")
            ink = to_ink(Image.fromarray(gray, "L"), dither)
            # CUPS may send only the imageable area: put it back on a full page
            dx, dy = h.page_offset_px()
            pw = round(h.page_size_pt[0] * 600 / 72)
            ph = round(h.page_size_pt[1] * 600 / 72)
            page = np.zeros((max(ph, dy + ink.shape[0]), max(pw, dx + ink.shape[1])), bool)
            page[dy:dy + ink.shape[0], dx:dx + ink.shape[1]] = ink
            yield page

    out = sys.stdout.buffer
    for fr in job_frames(pages(), bidirectional=bidir, roll=roll, cut_pause=cut_pause):
        out.write(fr)
    out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
