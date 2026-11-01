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


@pytest.mark.parametrize("down,gap,bidir", [(1, 4050, True), (0, 4050, True),
                                            (1, -4050, True), (1, 4050, False)])
def test_firmware_composer_reproduces_pages(sim, tmp_path, down, gap, bidir):
    pages = [page(1), page(2, 900)]
    job = tmp_path / "job.bin"
    job.write_bytes(b"".join(job_frames(pages, bidirectional=bidir)))
    out = subprocess.run([str(sim), str(job), str(tmp_path / "out"), str(down), str(gap)],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    for i, src in enumerate(pages, 1):
        got = read_pbm(tmp_path / f"out-{i}.pbm")
        h = src.shape[0]
        assert np.array_equal(got[:h, :src.shape[1]], src), f"page {i} differs"
        assert not got[h:].any()


def test_firmware_survives_line_noise(sim, tmp_path):
    frames = list(job_frames([page(3, 600)]))
    noisy = b"FJ\x13garbage" + b"".join(fr if i != 3 else fr + b"FJ\x99\x00\xff" for i, fr in enumerate(frames))
    job = tmp_path / "noisy.bin"
    job.write_bytes(noisy)
    out = subprocess.run([str(sim), str(job), str(tmp_path / "n"), "1", "4050"],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    got = read_pbm(tmp_path / "n-1.pbm")
    src = page(3, 600)
    assert np.array_equal(got[:600], src)


def test_generated_firmware_files_in_sync():
    import sys
    sys.path.insert(0, str(FW.parent / "tools"))
    import gen_params
    import hp45_tables
    assert (FW / "src" / "params_table.h").read_text() == gen_params.render()
    assert (FW / "src" / "hp45_map.c").read_text() == hp45_tables.emit_c()
    assert hp45_tables.check()
    assert BY_NAME["pulse_ns"].max <= 2400 and len({p.id for p in PARAMS}) == len(PARAMS)
