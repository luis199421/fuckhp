"""Run a PDF through the real CUPS filter chain (if CUPS is installed) with our PPD,
then through rastertofreejet and the emulator."""
import io
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from freejet.cups_filter import main as filter_main
from freejet.cups_raster import read_pages
from freejet.emulator import VirtualPrinter

PPD = Path(__file__).resolve().parents[1] / "cups" / "freejet.ppd"


@pytest.mark.skipif(not shutil.which("cupsfilter"), reason="CUPS not installed")
def test_pdf_through_cups(tmp_path, monkeypatch):
    img = Image.new("L", (850, 1100), 255)
    ImageDraw.Draw(img).rectangle([100, 100, 750, 160], fill=0)     # 1 in from the top-left
    img.save(tmp_path / "t.pdf", resolution=100)
    ras = subprocess.run(["cupsfilter", "-p", str(PPD), "-m", "application/vnd.cups-raster",
                          str(tmp_path / "t.pdf")], capture_output=True, check=True).stdout
    h, gray = next(read_pages(io.BytesIO(ras)))
    assert h.hw_res == (600, 600)
    dx, dy = h.page_offset_px()
    assert gray.shape[1] + 2 * dx in range(5095, 5106)
    (tmp_path / "t.ras").write_bytes(ras)
    out = io.BytesIO()

    class Out:
        buffer = out
    monkeypatch.setattr(sys, "stdout", Out)
    assert filter_main(["rastertofreejet", "1", "u", "t", "1", "", str(tmp_path / "t.ras")]) == 0
    vp = VirtualPrinter()
    vp.write(out.getvalue())
    assert not vp.errors and len(vp.pages) == 1
    page = vp.pages[0]
    ys, xs = np.nonzero(page)
    # bar at (100..750, 100..160) px @100 dpi  ->  x6 at 600 dpi
    assert abs(ys.min() - 600) < 8 and abs(xs.min() - 600) < 8
    assert abs(xs.max() - 4506) < 10 and abs(ys.max() - 966) < 10


@pytest.mark.skipif(not shutil.which("cupsfilter"), reason="CUPS not installed")
def test_colour_pdf_through_cups(tmp_path, monkeypatch):
    img = Image.new("RGB", (850, 1100), "white")
    ImageDraw.Draw(img).rectangle([100, 100, 400, 300], fill=(255, 0, 0))   # red = magenta + yellow
    img.save(tmp_path / "c.pdf", resolution=100)
    ras = subprocess.run(["cupsfilter", "-p", str(PPD), "-m", "application/vnd.cups-raster",
                          "-o", "ColorModel=RGB", str(tmp_path / "c.pdf")],
                         capture_output=True, check=True).stdout
    (tmp_path / "c.ras").write_bytes(ras)
    out = io.BytesIO()

    class Out:
        buffer = out
    monkeypatch.setattr(sys, "stdout", Out)
    assert filter_main(["rastertofreejet", "1", "u", "t", "1", "FJInkSet=KCMY FJDither=FS",
                        str(tmp_path / "c.ras")]) == 0
    vp = VirtualPrinter()
    vp.inkset = "KCMY"
    vp.write(out.getvalue())
    assert not vp.errors
    k, c, m, y = vp.pages[0]
    assert m.sum() > 1000 and y.sum() > 1000 and c.sum() < m.sum() / 20 and k.sum() < m.sum() / 20
