"""Load documents (PDF, images, text) and turn them into 1-bit 600 dpi pages."""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .color import INKSETS, separate
from .protocol import DPI

MM = DPI / 25.4  # pixels per mm

PAPER_MM = {
    "letter": (215.9, 279.4),
    "a4": (210.0, 297.0),
    "legal": (215.9, 355.6),
    "a5": (148.0, 210.0),
}


@dataclass
class PageSetup:
    paper: str = "letter"          # key of PAPER_MM, or "roll"
    roll_width_mm: float = 216.0
    roll_length_mm: float | None = None   # None = as long as the content
    margin_mm: float = 3.0
    fit: bool = True               # scale to the printable area (keeps aspect)
    dither: str = "auto"           # auto | fs | threshold | ordered
    inkset: str = "K"              # K | CMY | KCMY  (see color.py)
    gamma: float = 1.0             # >1 lightens mid-tones (compensates ink spread)

    @property
    def size_px(self) -> tuple[int, int] | None:
        """(width, height) of the paper in pixels, height None for open rolls."""
        if self.paper == "roll":
            h = None if self.roll_length_mm is None else round(self.roll_length_mm * MM)
            return round(self.roll_width_mm * MM), h
        w, h = PAPER_MM[self.paper]
        return round(w * MM), round(h * MM)


def to_ink(gray: Image.Image, method: str = "auto") -> np.ndarray:
    """8-bit grayscale (255 = white) -> bool ink mask."""
    g = gray.convert("L")
    if method in ("auto", "fs"):
        if method == "auto":
            # crush near-white / near-black so text and lines stay crisp,
            # dither only the genuinely gray areas
            lut = [0 if v < 60 else 255 if v > 200 else int((v - 60) * 255 / 140) for v in range(256)]
            g = g.point(lut)
        bw = g.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    elif method == "threshold":
        bw = g.point(lambda v: 255 if v >= 128 else 0).convert("1", dither=Image.Dither.NONE)
    elif method == "ordered":
        bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])
        a = np.asarray(g, dtype=np.uint16)
        t = (bayer[np.arange(a.shape[0])[:, None] % 4, np.arange(a.shape[1])[None, :] % 4] + 0.5) * 16
        return a < t
    else:
        raise ValueError(f"unknown dither method {method!r}")
    return ~np.asarray(bw, dtype=bool)


def place(img: Image.Image, setup: PageSetup, src_dpi: float | None = None) -> np.ndarray:
    """Scale/position an image onto the page and separate it into ink planes.
    Returns bool (rows, cols) for the plain black ink set, else (planes, rows, cols)."""
    pw, ph = setup.size_px
    m = round(setup.margin_mm * MM)
    aw = pw - 2 * m
    ah = None if ph is None else ph - 2 * m
    mono = setup.inkset == "K"
    img = img.convert("L" if mono else "RGB")
    if setup.fit:
        s = aw / img.width
        if ah is not None:
            s = min(s, ah / img.height)
    else:
        s = DPI / (src_dpi or DPI)
    if abs(s - 1) > 1e-3:
        img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))),
                         Image.Resampling.LANCZOS)
    height = ph if ph is not None else img.height + 2 * m
    canvas = Image.new(img.mode, (pw, height), "white")
    canvas.paste(img.crop((0, 0, min(img.width, aw), min(img.height, height - 2 * m))), (m, m))
    if setup.inkset == "K":
        return to_ink(canvas, setup.dither) if setup.gamma == 1.0 else \
            separate(canvas, "K", setup.dither, setup.gamma)[0]
    return separate(canvas, setup.inkset, setup.dither, setup.gamma)


def load_pages(path: str | Path, setup: PageSetup, pages: set[int] | None = None) -> Iterator[np.ndarray]:
    """Yield page ink masks for a PDF, image or plain-text file."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        yield from _pdf_pages(path, setup, pages)
    elif ext in (".txt", ".text", ".md", ".log", ".csv"):
        yield from _text_pages(path.read_text(errors="replace"), setup)
    else:
        img = Image.open(path)
        n = getattr(img, "n_frames", 1)
        for i in range(n):
            if pages and (i + 1) not in pages:
                continue
            img.seek(i)
            frame = ImageOps.exif_transpose(img)
            if frame.mode in ("RGBA", "LA", "P", "PA"):
                bg = Image.new("RGBA", frame.size, "white")
                frame = Image.alpha_composite(bg, frame.convert("RGBA"))
            dpi = img.info.get("dpi", (DPI, DPI))[0] or DPI
            yield place(frame, setup, float(dpi))


def _pdf_pages(path, setup, pages):
    try:
        import pypdfium2 as pdfium
    except ImportError as e:  # pragma: no cover
        raise SystemExit("PDF support needs pypdfium2:  pip install pypdfium2") from e
    pdf = pdfium.PdfDocument(str(path))
    for i in range(len(pdf)):
        if pages and (i + 1) not in pages:
            continue
        page = pdf[i]
        w_pt, h_pt = page.get_size()
        pw, ph = setup.size_px
        # render at 600 dpi, or smaller if the PDF page is larger than the paper
        scale = DPI / 72
        if setup.fit:
            m = 2 * setup.margin_mm * MM
            scale = min(scale, (pw - m) / w_pt) if ph is None else \
                min(scale, (pw - m) / w_pt, (ph - m) / h_pt)
        img = page.render(scale=scale, grayscale=setup.inkset == "K").to_pil()
        fit_setup = PageSetup(**{**setup.__dict__, "fit": False})
        yield place(img, fit_setup, DPI)


def _text_pages(text: str, setup: PageSetup, pt: float = 10.0):
    pw, ph = setup.size_px
    m = round(max(setup.margin_mm, 12.0) * MM)
    size = round(pt / 72 * DPI)
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", size)
    except OSError:
        font = ImageFont.load_default(size=size)
    line_h = round(size * 1.25)
    page_h = ph if ph is not None else 10 ** 9
    per_page = max(1, (page_h - 2 * m) // line_h)
    lines = text.expandtabs(4).splitlines() or [""]
    for start in range(0, len(lines), per_page):
        chunk = lines[start:start + per_page]
        h = ph if ph is not None else 2 * m + line_h * len(chunk)
        img = Image.new("L", (pw, h), 255)
        d = ImageDraw.Draw(img)
        for j, line in enumerate(chunk):
            d.text((m, m + j * line_h), line, fill=0, font=font)
        ink = to_ink(img, "threshold")
        n = len(INKSETS[setup.inkset])
        if n == 1:
            yield ink
        else:   # text always goes to the black slot (or to C+M+Y for a CMY set)
            planes = np.zeros((n,) + ink.shape, bool)
            if setup.inkset == "CMY":
                planes[:] = ink
            else:
                planes[0] = ink
            yield planes


def parse_ranges(spec: str | None) -> set[int] | None:
    """'1-3,5' -> {1, 2, 3, 5}"""
    if not spec:
        return None
    out = set()
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out
