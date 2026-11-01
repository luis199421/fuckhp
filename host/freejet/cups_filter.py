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
from .color import INKSETS, separate


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
    inkset = opts.get("FJInkSet", "K")
    if inkset not in INKSETS:
        log(f"ERROR: unknown ink set {inkset}")
        return 1
    gamma = float(opts.get("FJGamma", "1.0"))
    src = open(argv[6], "rb") if len(argv) == 7 else sys.stdin.buffer

    def pages():
        for n, (h, gray) in enumerate(read_pages(src), 1):
            if h.hw_res != (600, 600):
                log(f"ERROR: raster must be 600x600 dpi, got {h.hw_res}")
                raise SystemExit(1)
            # copies are expanded upstream by CUPS (*cupsManualCopies: True)
            log(f"PAGE: {n} 1")
            log(f"INFO: Preparing page {n}")
            img = Image.fromarray(gray, "RGB" if gray.ndim == 3 else "L")
            ink = separate(img, inkset, dither, gamma)
            if len(INKSETS[inkset]) == 1:
                ink = ink[0]
            # CUPS may send only the imageable area: put it back on a full page
            dx, dy = h.page_offset_px()
            pw = round(h.page_size_pt[0] * 600 / 72)
            ph = round(h.page_size_pt[1] * 600 / 72)
            hh, ww = ink.shape[-2:]
            page = np.zeros(ink.shape[:-2] + (max(ph, dy + hh), max(pw, dx + ww)), bool)
            page[..., dy:dy + hh, dx:dx + ww] = ink
            yield page

    out = sys.stdout.buffer
    for fr in job_frames(pages(), bidirectional=bidir, roll=roll, cut_pause=cut_pause, inkset=inkset):
        out.write(fr)
    out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
