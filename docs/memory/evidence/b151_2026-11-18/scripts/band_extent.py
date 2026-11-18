#!/usr/bin/env python3
"""B151: the band's rows and columns on the output frame (B147's method: a made-up 4:3 picture through the practice
command's own -vf, hwupload swapped for an RGB frame out, against the same chain without the band; changed = > 2 grey
levels). usage: band_extent.py <repo or work copy>"""
import shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "companion"))
import numpy as np
from PIL import Image
import native_stream as ns

def frame(tmp, w, h, banner):
    m = object.__new__(ns.NativeStreamManager)
    m._apply_profile_selection()
    m._linux_display = lambda: ":0"
    m._linux_vaapi_device = lambda: "/fixture/renderD128"
    m._party_banner_on = banner
    argv = m._build_linux_ffmpeg_command(ffmpeg=Path("/fixture/ffmpeg"), capture_target={"_window_id": 1}, width=w, height=h)
    vf = argv[argv.index("-vf") + 1].replace(",hwupload", ",format=rgb24")
    out = tmp / f"{w}_{int(banner)}.png"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(tmp / "made_up.png"), "-vf", vf,
                    "-frames:v", "1", "-y", str(out)], check=True, timeout=60)
    return np.asarray(Image.open(out).convert("L")).astype(int)

tmp = Path(tempfile.mkdtemp(prefix="b151_band_"))
try:
    rng = np.random.default_rng(147)
    blocks = rng.integers(60, 230, size=(12, 16, 3), dtype=np.uint8)
    Image.fromarray(np.kron(blocks, np.ones((60, 60, 1), dtype=np.uint8))).save(tmp / "made_up.png")
    print("words:", ns.PARTY_BANNER_TEXT)
    for w, h in ((1280, 720), (1920, 1080)):
        a, b = frame(tmp, w, h, True), frame(tmp, w, h, False)
        ys, xs = np.where(np.abs(a - b) > 2)
        top, side = h * 5 // 100, w * 5 // 100
        inner = ys.min() >= top and ys.max() <= h - top - 1 and xs.min() >= side and xs.max() <= w - side - 1
        width = int(xs.max() - xs.min() + 1)
        print(f"{w}x{h}: rows {ys.min()}-{ys.max()}, columns {xs.min()}-{xs.max()} ({width} x {ys.max()-ys.min()+1} px, "
              f"{100*width/w:.1f} % of the width); inner 90 % rows {top}-{h-top-1} columns {side}-{w-side-1}: "
              f"{'all inside' if inner else 'OUTSIDE'}; of a 4:3 picture ({h*4//3} x {h}): "
              f"{100*width*(ys.max()-ys.min()+1)/(h*4//3*h):.1f} %")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
