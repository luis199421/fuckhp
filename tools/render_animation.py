#!/usr/bin/env python3
"""Render the FreeJet assembly animation (cad/animation.scad) to GIF and MP4.

Needs OpenSCAD (+ xvfb-run on a headless machine), Pillow and ffmpeg.
    python3 tools/render_animation.py [--fast]
Writes docs/img/assembly_animation.gif and .mp4.
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCAD = ROOT / "cad" / "animation.scad"
OUT = ROOT / "docs" / "img"
FAST = "--fast" in sys.argv
W, H = (640, 400) if FAST else (960, 600)
FPS = 15

STEPS = [
    "Side plates (printed, roll slots built in)",
    "Carriage with 3 LM8UU bearings in clamped housings",
    "Carriage rails slide through plates and bearings",
    "Printed platen beam bolts between the plates",
    "The one feed roller: TPU tires, 60T printed pulley",
    "Feed motor and 200 mm GT2 loop (3:1)",
    "Leaf-spring bar presses the paper onto the roller",
    "Printed collars lock the rods",
    "Service station: cap sled, wiper, spittoon, home switch",
    "Carriage motor, idler and belt",
    "Paper sensor and electronics tray (Pico 2 board)",
    "Contact flex, then the HP 302 cartridge",
    "Paper tray, roll drops into the plate slots",
    "FreeJet FJ-2, ready",
    "Printing: sheet feeds in, one 13.7 mm pass at a time",
]
FRAMES_PER_STEP = 6 if FAST else 10
PRINT_FRAMES = 40 if FAST else 84
HOLD = 6 if FAST else 15


def timeline():
    """(step, u) for every frame."""
    out = []
    for s in range(len(STEPS) - 1):
        n = FRAMES_PER_STEP if s != 13 else FRAMES_PER_STEP // 2
        out += [(s, (i + 1) / n) for i in range(n)]
    out += [(len(STEPS) - 1, i / (PRINT_FRAMES - 1)) for i in range(PRINT_FRAMES)]
    out += [(len(STEPS) - 1, 1.0)] * HOLD
    return out


def camera(i, n):
    t = i / (n - 1)
    e = t * t * (3 - 2 * t)
    rz = 28 + 182 * e             # rear 3/4 view -> front 3/4 view
    rx = 57 - 4 * math.sin(math.pi * t)
    dist = 930 - 120 * e
    return f"170,-15,-5,{rx:.2f},0,{rz:.2f},{dist:.1f}"


def render(args):
    i, (step, u), cam, path = args
    cmd = ["openscad", "--colorscheme=Tomorrow", f"--imgsize={W},{H}", "--projection=p",
           f"--camera={cam}", "-D", f"STEP={step}", "-D", f"U={u:.4f}", "-o", str(path), str(SCAD)]
    if shutil.which("xvfb-run") and not os.environ.get("DISPLAY"):
        cmd = ["xvfb-run", "-a"] + cmd
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not path.exists():
        raise RuntimeError(f"frame {i}: {r.stderr[-400:]}")
    return i


def caption(path, step, i):
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    try:
        big = ImageFont.truetype("DejaVuSans-Bold.ttf", H // 24)
        small = ImageFont.truetype("DejaVuSans.ttf", H // 30)
    except OSError:
        big = small = ImageFont.load_default()
    d.rectangle([0, H - H // 9, W, H], fill=(20, 24, 32, 215))
    label = f"{step + 1:>2}/{len(STEPS)}  {STEPS[step]}" if step < len(STEPS) - 1 else STEPS[step]
    d.text((W // 40, H - H // 9 + H // 36), label, font=big, fill=(255, 255, 255))
    d.text((W // 40, H // 40), "FreeJet FJ-2 · assembly", font=small, fill=(60, 70, 90))
    im.save(path)


def main():
    frames = timeline()
    n = len(frames)
    tmp = Path(tempfile.mkdtemp(prefix="fj_anim_"))
    jobs = [(i, f, camera(i, n), tmp / f"f{i:04d}.png") for i, f in enumerate(frames)]
    print(f"rendering {n} frames at {W}x{H} into {tmp} ...", flush=True)
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for k, _ in enumerate(ex.map(render, jobs), 1):
            if k % 20 == 0:
                print(f"  {k}/{n}", flush=True)
    for i, (step, _), _, p in jobs:
        caption(p, step, i)
    OUT.mkdir(parents=True, exist_ok=True)
    mp4 = OUT / "assembly_animation.mp4"
    gif = OUT / "assembly_animation.gif"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-movflags", "+faststart", str(mp4)],
                   check=True)
    gw = min(W, 720)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
                    "-vf", f"fps=12,scale={gw}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];"
                           "[b][p]paletteuse=dither=bayer:bayer_scale=4", str(gif)], check=True)
    print(f"wrote {mp4} ({mp4.stat().st_size // 1024} KB) and {gif} ({gif.stat().st_size // 1024} KB)")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
