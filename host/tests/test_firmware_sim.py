"""End-to-end check of the firmware's portable data path (C code) against the
host encoder: random pages -> job stream -> fw_sim -> pages must match."""
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from freejet import protocol as P
from freejet.job import job_frames
from freejet.params import BY_NAME, PARAMS

FW = Path(__file__).resolve().parents[2] / "firmware"
SIM = FW / "tests" / "fw_sim"


@pytest.fixture(scope="module")
def sim():
    if not shutil.which("make") or not shutil.which("cc"):
        pytest.skip("no C compiler")
    subprocess.run(["make", "-s", "-C", str(SIM.parent)], check=True)
    return SIM


def read_pbm(path):
    data = path.read_bytes()
    head, rest = data.split(b"\n", 2)[:2], data.split(b"\n", 2)[2]
    w, h = map(int, head[1].split())
    bits = np.unpackbits(np.frombuffer(rest, np.uint8).reshape(h, (w + 7) // 8), axis=1)[:, :w]
    return bits.astype(bool)


def page(seed, h=2000, w=5184):
    rng = np.random.default_rng(seed)
    p = rng.random((h, w)) < 0.02
    p[:, :300] = False
    p[:, -300:] = False                      # leave room for the 4 mm row gap
    p[500:520, 400:4800] = True              # solid bar
    p[100:1900, 2000] = True                 # vertical line
    p[1200:1500] = False                     # a blank band to skip
    return p


GEOM = ["4000", "25000", "4000", "78"]   # k_row_gap_um color_x_um cmy_pitch_um k_dy_rows


@pytest.mark.parametrize("flip,gap,bidir", [(0, 4000, True), (1, 4000, True),
                                            (0, -4000, True), (0, 4000, False)])
def test_firmware_composer_reproduces_pages(sim, tmp_path, flip, gap, bidir):
    pages = [page(1), page(2, 900)]
    job = tmp_path / "job.bin"
    job.write_bytes(b"".join(job_frames(pages, bidirectional=bidir, roll=True)))
    out = subprocess.run([str(sim), str(job), str(tmp_path / "out"), str(flip), str(gap)] + GEOM[1:],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    for i, src in enumerate(pages, 1):
        got = read_pbm(tmp_path / f"out-{i}-0.pbm")
        h = src.shape[0]
        assert np.array_equal(got[:h, :src.shape[1]], src), f"page {i} differs"
        assert not got[h:].any()


def test_firmware_survives_line_noise(sim, tmp_path):
    frames = list(job_frames([page(3, 600)], roll=True))
    noisy = b"FJ\x13garbage" + b"".join(fr if i != 3 else fr + b"FJ\x99\x00\xff" for i, fr in enumerate(frames))
    job = tmp_path / "noisy.bin"
    job.write_bytes(noisy)
    out = subprocess.run([str(sim), str(job), str(tmp_path / "n"), "0"] + GEOM,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    got = read_pbm(tmp_path / "n-1-0.pbm")
    src = page(3, 600)
    assert np.array_equal(got[:600], src)


def test_generated_firmware_files_in_sync():
    import sys
    sys.path.insert(0, str(FW.parent / "tools"))
    import gen_params
    assert (FW / "src" / "params_table.h").read_text() == gen_params.render()
    assert len({p.id for p in PARAMS}) == len(PARAMS)


def test_waveform_matches_original_driver(sim):
    out = subprocess.run([str(FW / "tests" / "wave_test")], capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


@pytest.mark.parametrize("inkset,flip,kdy", [("KCMY", 0, 78), ("KCMY", 1, 0), ("CMY", 0, 0), ("CMY", 1, 0)])
def test_firmware_composer_colour(sim, tmp_path, inkset, flip, kdy):
    from freejet.color import INKSETS
    n = len(INKSETS[inkset])
    rng = np.random.default_rng(7)
    planes = np.stack([page(10 + i, 1500) & (rng.random((1500, 5184)) < 0.7) for i in range(n)])
    planes[:, :, -1100:] = False                 # the colour columns sit right of black
    for i, ink in enumerate(INKSETS[inkset]):
        if ink != "K":
            planes[i, 1::2] = False              # colour nozzles are 1/300 in apart
    job = tmp_path / "job.bin"
    job.write_bytes(b"".join(job_frames([planes], inkset=inkset, roll=True)))
    args = [str(sim), str(job), str(tmp_path / "c"), str(flip), "4000", "25000", "4000", str(kdy)]
    out = subprocess.run(args, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    for pl in range(n):
        got = read_pbm(tmp_path / f"c-1-{pl}.pbm")
        src = planes[pl]
        h = min(got.shape[0], src.shape[0])
        assert np.array_equal(got[:h, :src.shape[1]], src[:h]), f"plane {pl} differs"
        assert not src[h:].any() and not got[h:].any()
