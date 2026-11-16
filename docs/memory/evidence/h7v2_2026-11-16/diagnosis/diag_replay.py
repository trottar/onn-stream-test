"""Replay the kept pictures through B102's Reader + Ended, as-is and with a brightness offset. Read only."""
import sys, csv, collections
sys.path.insert(0, "tools")
import numpy as np, h7_endscreen as H
from PIL import Image
RUN = "runtime/h7_frames/h7v2_20261116_run"
spec, arr = H.load_spec("<the rules folder>/<T88's id>.endscreen.json")
rows = list(csv.DictReader(open(RUN + "/index.csv")))
off = float(sys.argv[1])
rd = H.Reader(spec, arr, clock=lambda: 0.0)
t = 0.0
out = []
for r in rows:
    im = Image.open(f"{RUN}/{r['file']}").convert("L")
    if off:
        im = im.point(lambda v: min(255, v + off))
    t += 1.0
    x = rd.read(im, now=t)
    out.append((r["utc"], x["class"], x["distances"]["screen"]))
prev = None; start = None
for u, c, d in out:
    if c != prev:
        if prev is not None:
            print(f"{start[11:23]}-{last[11:23]} {prev:8s} n={n} screen_d {dmin:.1f}-{dmax:.1f}")
        prev, start, n, dmin, dmax = c, u, 0, 1e9, 0
    n += 1; last = u; dmin = min(dmin, d); dmax = max(dmax, d)
print(f"{start[11:23]}-{last[11:23]} {prev:8s} n={n} screen_d {dmin:.1f}-{dmax:.1f}")
print(collections.Counter(c for _, c, _ in out))
