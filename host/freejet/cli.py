"""`freejet` command line tool: print, preview, calibrate and maintain."""
import argparse
import struct
import sys
import time

import numpy as np

from . import protocol as P
from .params import BY_ID, BY_NAME, PARAMS
from .raster import PageSetup, load_pages, parse_ranges


def _setup(a) -> PageSetup:
    return PageSetup(paper=a.paper, roll_width_mm=a.roll_width, roll_length_mm=a.length,
                     margin_mm=a.margin, fit=not a.actual_size, dither=a.dither,
                     inkset=a.inks, gamma=a.gamma)


def _pages(a):
    setup = _setup(a)
    for f in a.files:
        for page in load_pages(f, setup, parse_ranges(a.pages)):
            for _ in range(a.copies):
                yield page


def _open(a):
    from .transport import Printer
    return Printer(a.port)


def _frames(a, pages, info=None):
    from .job import job_frames
    kw = {}
    if info:
        kw = dict(max_cols=info["max_cols"], ring_bytes=info["ring_bytes"])
    return job_frames(pages, bidirectional=not a.unidirectional, roll=a.paper == "roll",
                      cut_pause=a.paper == "roll" and not a.no_cut_pause,
                      inkset=getattr(a, "inks", "K"), **kw)


def _progress(e):
    msg = {"paper_needed": "Insert a sheet into the rear slot (printer is waiting)...",
           "paper_loaded": "Paper loaded, printing.",
           "cut_now": "Cut the page with the slide cutter, then press the button.",
           "head_hot_pause": "Printhead cooling down...",
           "job_done": "Done."}.get(e["event"])
    if e["event"] == "page_done":
        msg = f"Page {e['value']} finished."
    if msg:
        print(msg, flush=True)


def cmd_print(a):
    if a.dry_run:
        return _preview(a, _pages(a), a.dry_run)
    with _open(a) as pr:
        info = pr.info()
        st = pr.status()
        if "head" not in st["flags"]:
            sys.exit("No cartridge detected - check the HP45 is seated and the head cable.")
        t0 = time.time()
        pr.stream(_frames(a, _pages(a), info), _progress)
        print(f"Printed in {time.time() - t0:.0f} s")


def _preview(a, pages, out):
    from PIL import Image

    from .color import INKSETS
    from .emulator import VirtualPrinter
    vp = VirtualPrinter()
    vp.n_heads = len(INKSETS[getattr(a, "inks", "K")])
    for fr in _frames(a, pages):
        vp.write(fr)
    if vp.errors:
        sys.exit("printer would reject this job: " + "; ".join(vp.errors))
    for i, page in enumerate(vp.pages, 1):
        name = out if len(vp.pages) == 1 else out.replace(".png", f"-{i}.png")
        composite(page, getattr(a, "inks", "K")).save(name, dpi=(600, 600))
        print(f"wrote {name}  ({page.shape[-1]}x{page.shape[-2]} px)")


# approximate on-paper colour of each ink (RGB 0..1), used to simulate prints
INK_RGB = {"K": (0.08, 0.08, 0.1), "LK": (0.62, 0.62, 0.64), "C": (0.0, 0.62, 0.87),
           "M": (0.85, 0.05, 0.5), "Y": (1.0, 0.92, 0.0)}


def composite(page, inkset="K"):
    """Simulate the printed page: multiply each ink's colour where it has drops."""
    from PIL import Image

    from .color import INKSETS
    planes = page[None] if page.ndim == 2 else page
    if len(planes) == 1:
        return Image.fromarray(~planes[0]).convert("1")
    rgb = np.ones(planes.shape[1:] + (3,), np.float32)
    for ink, pl in zip(INKSETS[inkset], planes):
        rgb[pl] *= np.array(INK_RGB[ink], np.float32)
    return Image.fromarray((rgb * 255).astype(np.uint8), "RGB")


def cmd_preview(a):
    _preview(a, _pages(a), a.output)


def cmd_list(a):
    from .transport import find_ports
    ports = find_ports()
    if not ports:
        print("No FreeJet printers found.")
    for dev, sn, desc in ports:
        print(f"{dev}\t{sn}\t{desc}")


def cmd_status(a):
    with _open(a) as pr:
        for k, v in {**pr.info(), **pr.status()}.items():
            print(f"{k:12} {v}")


def cmd_param(a):
    with _open(a) as pr:
        if a.action == "list":
            for p in PARAMS:
                print(f"{p.name:22} {pr.get_param(p.id):>9}   (default {p.default})  {p.help}")
        elif a.action == "get":
            print(pr.get_param(BY_NAME[a.name].id))
        elif a.action == "set":
            pr.set_param(BY_NAME[a.name].id, int(a.value))
            print(f"{a.name} = {a.value}  (run `freejet param save` to keep it)")
        elif a.action == "save":
            pr.simple(P.PARAM_SAVE)
            print("saved to printer flash")
        elif a.action == "defaults":
            pr.simple(P.PARAM_DEFAULTS)
            print("restored defaults (not saved yet)")


def cmd_maint(a):
    with _open(a) as pr:
        if a.cmd == "home":
            pr.simple(P.HOME)
        elif a.cmd == "park":
            pr.simple(P.PARK)
        elif a.cmd == "clean":
            pr.simple(P.SPIT, struct.pack("<H", a.spits), timeout=120)
        elif a.cmd == "feed":
            pr.simple(P.FEED, struct.pack("<i", round(a.mm * 1000)))
        elif a.cmd == "motors-off":
            pr.simple(P.MOTORS_OFF)
        elif a.cmd == "fire":
            pr.simple(P.NOZZLE_FIRE, struct.pack("<HH", a.nozzle if a.nozzle >= 0 else 0xFFFF,
                                                  a.count), timeout=30)
        elif a.cmd == "bootsel":
            pr.send(P.BOOTSEL)
            print("Printer rebooted into USB boot mode: copy freejet.uf2 to the RPI-RP2 drive.")
        elif a.cmd == "abort":
            pr.simple(P.ABORT)
        print("ok")


def cmd_test(a):
    from . import testpages as T
    from .color import INKSETS
    n = len(INKSETS[a.inks])
    if a.which == "nozzles":     # one nozzle-check band per cartridge
        one = T.nozzle_check()
        page = np.zeros((n, n * (one.shape[0] + 60), one.shape[1]), bool)
        for s in range(n):
            page[s, s * (one.shape[0] + 60):s * (one.shape[0] + 60) + one.shape[0]] = one
    elif a.which == "heads":
        if n < 2:
            sys.exit("head alignment needs --inks KLK, CMY or CMYK")
        page = T.heads_page(n)
    else:
        if a.which == "rows":
            down = 1
            if not a.dry_run:
                with _open(a) as pr:
                    down = pr.get_param(BY_NAME["nozzle0_downstream"].id)
            rows = np.arange(P.ROWS)
            nozzle = rows if down else (P.ROWS - 1 - rows)
            mono = T.alignment_page(nozzle % 2 == 1)
        elif a.which == "bidir":
            mono, _ = T.bidir_page()
        else:
            mono = T.feed_page()
        page = np.zeros((n,) + mono.shape, bool)
        page[0] = mono                   # row / bidir / feed tests use slot 0 only
    a.files, a.copies = [], 1
    a.paper = "letter" if a.paper == "roll" else a.paper
    w = round(215.9 / 25.4 * 600) if a.paper == "letter" else round(210 / 25.4 * 600)
    m = 120
    full = np.zeros((n, page.shape[1] + 2 * m, w), bool)
    full[:, m:m + page.shape[1], m:m + page.shape[2]] = page[:, :, :w - m]
    if a.which not in ("bidir",):
        a.unidirectional = True
    out = full[0] if n == 1 else full
    if a.dry_run:
        return _preview(a, [out], a.dry_run)
    with _open(a) as pr:
        pr.stream(_frames(a, [out], pr.info()), _progress)


def cmd_calibrate(a):
    um = P.UM_PER_COL
    if a.what in ("head-x", "head-y"):
        if len(a.args) != 2:
            sys.exit("usage: freejet calibrate head-x|head-y SLOT K")
        a.slot, a.value = int(a.args[0]), a.args[1]
    else:
        a.slot, a.value = None, a.args[0]
    with _open(a) as pr:
        if a.what == "rows":
            # the test shifted the odd column's data by k: the real gap is k columns smaller
            pid = BY_NAME["row_gap_um"].id
            old = pr.get_param(pid)
            new = round(old - a.value * um)
        elif a.what == "bidir":
            # right-to-left half was shifted by k: fire those passes k columns later
            pid = BY_NAME["bidir_offset_um"].id
            old = pr.get_param(pid)
            new = round(old + a.value * um)
        elif a.what in ("head-x", "head-y"):
            if not a.slot or not 1 <= a.slot <= 3:
                sys.exit("give the slot (1-3), e.g.  freejet calibrate head-x 2 -1")
            if a.what == "head-x":   # slot s data was shifted k columns: it really sits -k further
                pid = BY_NAME[f"head{a.slot}_x_um"].id
                old = pr.get_param(pid)
                new = round(old - a.value * um)
            else:                    # shifted k rows: move its data k rows with spare nozzles
                pid = BY_NAME[f"head{a.slot}_dy_rows"].id
                old = pr.get_param(pid)
                new = round(old + a.value)
        else:  # feed: value = measured mm over the 250 mm test
            pid = BY_NAME["y_steps_per_m"].id
            old = pr.get_param(pid)
            new = round(old * 250.0 / a.value)
        pr.set_param(pid, new)
        pr.simple(P.PARAM_SAVE)
        print(f"{BY_ID[pid].name}: {old} -> {new} (saved)")


def build_parser():
    ap = argparse.ArgumentParser(prog="freejet", description="FreeJet FJ-1 printer tool")
    ap.add_argument("--port", help="serial port (default: auto-detect)")
    sub = ap.add_subparsers(dest="command", required=True)

    def page_opts(p):
        p.add_argument("--paper", default="letter", choices=["letter", "a4", "legal", "a5", "roll"])
        p.add_argument("--roll-width", type=float, default=216.0, help="roll width in mm")
        p.add_argument("--length", type=float, help="roll page length in mm (default: fit content)")
        p.add_argument("--margin", type=float, default=3.0, help="margins in mm")
        p.add_argument("--actual-size", action="store_true", help="don't scale to fit")
        p.add_argument("--dither", default="auto", choices=["auto", "fs", "threshold", "ordered"])
        p.add_argument("--inks", default="K", choices=["K", "KLK", "CMY", "CMYK"],
                       help="cartridges fitted, left to right: K = black only, KLK = black + light "
                            "black (grayscale), CMY / CMYK = colour (must match param n_heads)")
        p.add_argument("--gamma", type=float, default=1.0,
                       help="tone curve: >1 lightens mid-tones if photos print too dark")
        p.add_argument("--unidirectional", action="store_true",
                       help="print left-to-right only (slower, best alignment)")
        p.add_argument("--no-cut-pause", action="store_true", help="roll: don't stop for cutting")
        p.add_argument("--pages", help="page ranges, e.g. 1-3,5")
        p.add_argument("--copies", type=int, default=1)

    p = sub.add_parser("print", help="print PDF / image / text files")
    p.add_argument("files", nargs="+")
    page_opts(p)
    p.add_argument("--dry-run", metavar="OUT.png", help="simulate instead of printing")
    p.set_defaults(func=cmd_print)

    p = sub.add_parser("preview", help="render exactly what would be printed to a PNG")
    p.add_argument("files", nargs="+")
    p.add_argument("-o", "--output", default="preview.png")
    page_opts(p)
    p.set_defaults(func=cmd_preview)

    sub.add_parser("list", help="list attached printers").set_defaults(func=cmd_list)
    sub.add_parser("status", help="show printer status").set_defaults(func=cmd_status)

    p = sub.add_parser("param", help="read/change settings")
    p.add_argument("action", choices=["list", "get", "set", "save", "defaults"])
    p.add_argument("name", nargs="?", choices=list(BY_NAME))
    p.add_argument("value", nargs="?")
    p.set_defaults(func=cmd_param)

    p = sub.add_parser("test", help="print a calibration page")
    p.add_argument("which", choices=["nozzles", "rows", "bidir", "feed", "heads"])
    page_opts(p)
    p.add_argument("--dry-run", metavar="OUT.png")
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("calibrate", help="apply a calibration result and save it")
    p.add_argument("what", choices=["rows", "bidir", "feed", "head-x", "head-y"])
    p.add_argument("args", nargs="+", type=float,
                   help="block number from the test page, or measured mm; head-x/head-y: SLOT K")
    p.set_defaults(func=cmd_calibrate)

    for name, hlp in [("home", "home the carriage"), ("park", "park + cap the cartridge"),
                      ("motors-off", "release the motors"), ("abort", "cancel the current job"),
                      ("bootsel", "reboot into firmware-update mode")]:
        sub.add_parser(name, help=hlp).set_defaults(func=cmd_maint, cmd=name)
    p = sub.add_parser("clean", help="spit all nozzles into the spittoon")
    p.add_argument("--spits", type=int, default=200)
    p.set_defaults(func=cmd_maint, cmd="clean")
    p = sub.add_parser("feed", help="feed paper forward")
    p.add_argument("mm", type=float)
    p.set_defaults(func=cmd_maint, cmd="feed")
    p = sub.add_parser("fire", help="fire one nozzle (or all with -1) in place, for debugging")
    p.add_argument("nozzle", type=int)
    p.add_argument("--count", type=int, default=100)
    p.set_defaults(func=cmd_maint, cmd="fire")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    from .transport import PrinterError
    try:
        return a.func(a) or 0
    except PrinterError as e:
        print(f"printer error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
