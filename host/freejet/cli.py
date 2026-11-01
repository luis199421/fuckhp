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
                      inkset=getattr(a, "inks", "K"), warn=lambda m: print("warning:", m), **kw)


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
            sys.exit("No cartridge detected - check the cartridge is seated against the contact flex.")
        t0 = time.time()
        pr.stream(_frames(a, _pages(a), info), _progress)
        print(f"Printed in {time.time() - t0:.0f} s")


def _preview(a, pages, out):
    from PIL import Image

    from .color import INKSETS
    from .emulator import VirtualPrinter
    vp = VirtualPrinter()
    vp.inkset = getattr(a, "inks", "K")
    for fr in _frames(a, pages):
        vp.write(fr)
    if vp.errors:
        sys.exit("printer would reject this job: " + "; ".join(vp.errors))
    for i, page in enumerate(vp.pages, 1):
        name = out if len(vp.pages) == 1 else out.replace(".png", f"-{i}.png")
        composite(page, getattr(a, "inks", "K")).save(name, dpi=(600, 600))
        print(f"wrote {name}  ({page.shape[-1]}x{page.shape[-2]} px)")


# approximate on-paper colour of each ink (RGB 0..1), used to simulate prints
INK_RGB = {"K": (0.08, 0.08, 0.1), "C": (0.0, 0.62, 0.87),
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
            cart = {"black": 0, "colour": 1, "both": 0xFFFF}[a.cartridge]
            pr.simple(P.NOZZLE_FIRE, struct.pack("<HH", cart, a.count), timeout=30)
        elif a.cmd == "bootsel":
            pr.send(P.BOOTSEL)
            print("Printer rebooted into USB boot mode: copy freejet.uf2 to the RPI-RP2 drive.")
        elif a.cmd == "abort":
            pr.simple(P.ABORT)
        print("ok")


def cmd_test(a):
    from . import testpages as T
    from .color import INKSETS
    inks = INKSETS[a.inks]
    n = len(inks)
    if a.which == "nozzles":     # one nozzle-check band per ink
        bands = [T.nozzle_check(rows=P.ROWS_K if ink == "K" else P.ROWS_COLOR,
                                step=1 if ink == "K" else 2) for ink in inks]
        h = max(b.shape[0] for b in bands) + 60
        page = np.zeros((n, n * h, bands[0].shape[1]), bool)
        for s, b in enumerate(bands):
            page[s, s * h:s * h + b.shape[0]] = b
    elif a.which == "colors":
        if n < 2:
            sys.exit("colour alignment needs --inks CMY or KCMY")
        page = T.colors_page(n)
    else:
        if a.which == "rows":
            if "K" not in inks:
                sys.exit("the rows test is for the black cartridge (--inks K or KCMY)")
            flip = 0
            if not a.dry_run:
                with _open(a) as pr:
                    flip = pr.get_param(BY_NAME["nozzle_flip"].id)
            rows = np.arange(P.ROWS_K)
            mono = T.alignment_page((rows % 2 == 1) ^ bool(flip))
        elif a.which == "bidir":
            mono, _ = T.bidir_page()
        else:
            mono = T.feed_page()
        page = np.zeros((n,) + mono.shape, bool)
        page[0] = mono                   # row / bidir / feed tests use the first ink only
    a.files, a.copies = [], 1
    a.paper = "letter" if a.paper == "roll" else a.paper
    w = round(215.9 / 25.4 * 600) if a.paper == "letter" else round(210 / 25.4 * 600)
    m = 120
    full = np.zeros((n, page.shape[1] + 2 * m, w), bool)
    full[:, m:m + page.shape[1], m:m + page.shape[2]] = page[:, :, :w - m]
    if a.which != "bidir":
        a.unidirectional = True
    out = full[0] if n == 1 else full
    if a.dry_run:
        return _preview(a, [out], a.dry_run)
    with _open(a) as pr:
        pr.stream(_frames(a, [out], pr.info()), _progress)


CARTRIDGE_PITCH = 28     # mm between the black and the colour cartridge (cad/fj.scad)


def standard_geometry(inks: str) -> dict:
    """Parameter values for the standard FreeJet frame with these cartridges (must match
    cad/fj.scad: frame 2 x span wider when both cartridges are fitted)."""
    span = CARTRIDGE_PITCH if inks == "KCMY" else 0
    return {"cartridges": {"K": 1, "CMY": 2, "KCMY": 3}[inks],
            "col0_x_um": (40 + span) * 1000, "spit_x_um": (32 + span) * 1000,
            "x_travel_um": (300 + span) * 1000}


def cmd_setup(a):
    vals = standard_geometry(a.inks)
    with _open(a) as pr:
        for name, v in vals.items():
            pr.set_param(BY_NAME[name].id, v)
        pr.simple(P.PARAM_SAVE)
    print(f"configured for ink set {a.inks}: " + ", ".join(f"{k}={v}" for k, v in vals.items()))
    print("now run: freejet test nozzles --inks " + a.inks +
          ("" if a.inks == "K" else f"  and  freejet test colors --inks {a.inks}"))


def cmd_calibrate(a):
    um = P.UM_PER_COL
    a.value = a.args[0]
    with _open(a) as pr:
        if a.what == "rows":
            # the test shifted nozzle row 1's data by k: the real gap is k columns smaller
            pid = BY_NAME["k_row_gap_um"].id
            old = pr.get_param(pid)
            new = round(old - a.value * um)
        elif a.what == "bidir":
            # right-to-left half was shifted by k: fire those passes k columns later
            pid = BY_NAME["bidir_offset_um"].id
            old = pr.get_param(pid)
            new = round(old + a.value * um)
        elif a.what in ("color-x", "cmy-pitch"):   # plane data was shifted k columns
            pid = BY_NAME["color_x_um" if a.what == "color-x" else "cmy_pitch_um"].id
            old = pr.get_param(pid)
            new = round(old - a.value * um)
        elif a.what == "k-dy":                        # black dash shifted k rows
            pid = BY_NAME["k_dy_rows"].id
            old = pr.get_param(pid)
            new = round(old - a.value)
        else:  # feed: value = measured mm over the 250 mm test
            pid = BY_NAME["y_steps_per_m"].id
            old = pr.get_param(pid)
            new = round(old * 250.0 / a.value)
        pr.set_param(pid, new)
        pr.simple(P.PARAM_SAVE)
        print(f"{BY_ID[pid].name}: {old} -> {new} (saved)")


def build_parser():
    ap = argparse.ArgumentParser(prog="freejet", description="FreeJet FJ-2 printer tool")
    ap.add_argument("--port", help="serial port (default: auto-detect)")
    sub = ap.add_subparsers(dest="command", required=True)

    def page_opts(p):
        p.add_argument("--paper", default="letter", choices=["letter", "a4", "legal", "a5", "roll"])
        p.add_argument("--roll-width", type=float, default=216.0, help="roll width in mm")
        p.add_argument("--length", type=float, help="roll page length in mm (default: fit content)")
        p.add_argument("--margin", type=float, default=3.0, help="margins in mm")
        p.add_argument("--actual-size", action="store_true", help="don't scale to fit")
        p.add_argument("--dither", default="auto", choices=["auto", "fs", "threshold", "ordered"])
        p.add_argument("--inks", default="K", choices=["K", "CMY", "KCMY"],
                       help="cartridges to print with: K = black, CMY = colour cartridge, "
                            "KCMY = both (must match param cartridges)")
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
    p.add_argument("which", choices=["nozzles", "rows", "bidir", "feed", "colors"])
    page_opts(p)
    p.add_argument("--dry-run", metavar="OUT.png")
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("setup", help="set cartridge count + frame geometry for a standard build")
    p.add_argument("--inks", required=True, choices=["K", "CMY", "KCMY"])
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("calibrate", help="apply a calibration result and save it")
    p.add_argument("what", choices=["rows", "bidir", "feed", "color-x", "cmy-pitch", "k-dy"])
    p.add_argument("args", nargs=1, type=float, help="block number from the test page, or measured mm")
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
    p = sub.add_parser("fire", help="fire every nozzle of a cartridge over the spittoon (debugging)")
    p.add_argument("cartridge", choices=["black", "colour", "both"])
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
