import numpy as np
import pytest
from PIL import Image, ImageDraw

from freejet import protocol as P
from freejet.emulator import VirtualPrinter
from freejet.job import job_frames
from freejet.raster import PageSetup, load_pages
from freejet.swath import plan_swaths, render_swaths
from freejet.transport import Printer, PrinterError


def random_page(seed=0, h=3300, w=5100):
    rng = np.random.default_rng(seed)
    page = np.zeros((h, w), bool)
    for _ in range(40):   # random blocks of text-like noise with blank gaps
        y, x = rng.integers(0, h - 200), rng.integers(0, w - 800)
        page[y:y + rng.integers(5, 200), x:x + rng.integers(5, 800)] = rng.random() < 0.5 or \
            rng.random((1, 1)) < 0.5
    page[rng.integers(0, h, 500), rng.integers(0, w, 500)] = True
    return page


@pytest.mark.parametrize("bidir", [True, False])
def test_swaths_reproduce_page(bidir):
    page = random_page(1)
    sw = plan_swaths(page, bidirectional=bidir)
    assert np.array_equal(render_swaths(sw, *page.shape), page)
    ys = [s.y_px for s in sw]
    assert ys == sorted(ys)                       # never feed backwards
    if bidir:
        assert {s.direction for s in sw} == {0, 1}


def test_blank_regions_are_skipped():
    page = np.zeros((6600, 5100), bool)
    page[100, 100:200] = True
    page[6000, 4000] = True
    sw = plan_swaths(page)
    assert len(sw) == 2
    assert sw[0].ncols == 100 and sw[1].ncols == 1


def test_split_large_swaths():
    page = np.ones((300, 5100), bool)
    page[::2, ::3] = False
    sw = plan_swaths(page, max_bytes=50_000)
    assert len(sw) > 1
    assert all(s.ncols * P.COL_BYTES <= 50_000 for s in sw)
    assert np.array_equal(render_swaths(sw, *page.shape), page)


def test_full_job_through_emulator():
    pages = [random_page(2), random_page(3)]
    vp = VirtualPrinter()
    for fr in job_frames(pages):
        vp.write(fr)
    assert not vp.errors
    assert [e["event"] for e in vp.events][-1] == "job_done"
    for src, out in zip(pages, vp.pages):
        h = min(src.shape[0], out.shape[0])
        assert np.array_equal(out[:h, :src.shape[1]], src[:h])
        assert not out[h:].any()


def test_emulator_rejects_backfeed():
    from freejet import packbits
    col = packbits.encode(bytes(P.COL_BYTES))
    vp = VirtualPrinter()
    for t, p in [(P.JOB_BEGIN, bytes(4)), (P.PAGE_BEGIN, bytes(8)),
                 (P.SWATH_BEGIN, P.swath_begin(5000, 0, 1, 0, len(col))), (P.SWATH_DATA, col),
                 (P.SWATH_BEGIN, P.swath_begin(1000, 0, 1, 0, len(col)))]:
        vp.write(P.frame(t, p))
    assert "paper cannot move backwards" in vp.errors


class EmuLink:
    """Looks like a pyserial port, backed by the emulator."""

    def __init__(self):
        self.vp = VirtualPrinter()

    def write(self, b):
        return self.vp.write(b)

    def read(self, n):
        import time
        out = self.vp.read_all()
        if not out:
            time.sleep(0.005)
        return out

    def close(self):
        pass


def test_transport_against_emulator():
    with Printer(link=EmuLink(), timeout=2) as pr:
        assert pr.info()["rows"] == 300
        assert pr.get_param(40) == 1800
        pr.set_param(40, 1700)
        assert pr.get_param(40) == 1700
        with pytest.raises(PrinterError):
            pr.set_param(40, 99999)          # out of range -> error ack
        events = []
        pr.stream(job_frames([random_page(4, 900, 3000)]), events.append)
        assert events[-1]["event"] == "job_done"


def test_load_pdf_image_and_text(tmp_path):
    img = Image.new("L", (850, 1100), 255)
    d = ImageDraw.Draw(img)
    d.rectangle([100, 100, 700, 200], fill=0)
    d.ellipse([200, 400, 600, 800], fill=128)
    img.save(tmp_path / "a.png", dpi=(100, 100))
    img.save(tmp_path / "a.pdf", resolution=100)
    (tmp_path / "a.txt").write_text("hello\nworld\n" * 200)
    setup = PageSetup(paper="letter")
    for f in ["a.png", "a.pdf", "a.txt"]:
        pages = list(load_pages(tmp_path / f, setup))
        assert pages and pages[0].shape == (6600, 5100), f
        ink = pages[0].mean()
        assert 0.002 < ink < 0.5, (f, ink)
    pdf = next(load_pages(tmp_path / "a.pdf", setup))
    # the black bar is solid black and lands where the PDF put it (scaled to fit)
    assert pdf[round(150 * 6), 400 * 6]
