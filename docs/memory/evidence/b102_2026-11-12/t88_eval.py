#!/usr/bin/env python3
"""B102 on T88's real frames (read-only; numbers only). Learns in memory on the first half of each labelled range,
scores the second half (and every `other` frame), times the learn / one read / one search on the hub, then scores the
same frames moved in memory (shift in px of the 640-wide picture, rescale about the centre; PIL affine, black fill)
with the search off and on. Nothing is written beside the frames; no spec is kept; prints one JSON line per part.

usage: t88_eval.py <repo> <runs folder> <labels file>
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

REPO, RUNS, LABELS = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(REPO / "tools"))
import h7_endscreen as E  # noqa: E402


def emit(part, **kw):
    print(json.dumps({"part": part, **kw}, sort_keys=True), flush=True)


def moved(dx, dy, s):
    def f(img):
        w, h = img.size
        cx, cy = w / 2.0, h / 2.0
        return img.transform(img.size, Image.AFFINE, (1 / s, 0, cx - (cx + dx) / s, 0, 1 / s, cy - (cy + dy) / s),
                             resample=Image.BILINEAR, fillcolor=0)
    return f


# 1. learn on the first half of each labelled range
spec, arrays, report = E.learn(RUNS, LABELS, half="first", name="t88")
emit("learn_first_half", report=report, spec={k: spec[k] for k in (
    "size", "aspect", "classes", "start_class", "end_classes", "screen_threshold", "class_thresholds", "separable",
    "margin_needed", "usable", "k", "screen_mask_px", "outcome_mask_px", "frames")})

# 2. score: the second half of each range; then every labelled frame (all `other` frames included)
emit("score_second_half", **E.score(RUNS, LABELS, spec, arrays, half="second"))
emit("score_all_labelled", **E.score(RUNS, LABELS, spec, arrays, half=None))

# 3. times on the hub: one read (plain; the picture already decoded), one search
labels = E.load_labels(LABELS)
paths = E.labelled_frames(RUNS, labels, "second")
one_end = Image.open(paths["end_P1"][0]).convert("L")
one_other = Image.open(paths["other"][0]).convert("L")
rd = E.Reader(spec, arrays)
plain = []
for _ in range(50):
    t0 = time.perf_counter(); rd.read(one_end); plain.append((time.perf_counter() - t0) * 1000)
srch = []
for _ in range(10):
    r2 = E.Reader(spec, arrays)
    t0 = time.perf_counter(); r2.read(one_other); srch.append((time.perf_counter() - t0) * 1000)
dec = []
for _ in range(20):
    t0 = time.perf_counter()
    with Image.open(paths["end_P1"][0]) as im:
        im.convert("L")
    dec.append((time.perf_counter() - t0) * 1000)
emit("times_ms", read_plain_median=round(float(np.median(plain)), 2), read_plain_worst=round(max(plain), 2),
     read_with_search_median=round(float(np.median(srch)), 1), read_with_search_worst=round(max(srch), 1),
     jpeg_decode_median=round(float(np.median(dec)), 2), learn_s=report["learn_s"])

# 4. moved pictures: shift (px at 640 wide) and rescale; search off and on
CASES = [(2, 0, 1.0), (4, 0, 1.0), (8, 0, 1.0), (12, 0, 1.0), (0, 4, 1.0), (0, 8, 1.0), (-6, 5, 1.0), (8, 8, 1.0),
         (0, 0, 0.97), (0, 0, 1.03), (0, 0, 0.95), (0, 0, 1.05), (5, 3, 1.04), (-4, -6, 0.96),
         (16, 0, 1.0), (0, 0, 0.92), (0, 0, 1.08)]
for dx, dy, s in CASES:
    for search in (False, True):
        t0 = time.perf_counter()
        r = E.score(RUNS, LABELS, spec, arrays, half="second", transform=moved(dx, dy, s), search=search)
        emit("moved", dx=dx, dy=dy, scale=s, search=search, right=r["right"],
             other_read_as_screen=r["other_read_as_screen"], worst_own_distance=r["worst_own_distance"],
             least_margin=r["least_margin"], read_ms=r["read_ms"], seconds=round(time.perf_counter() - t0, 1))
emit("done")
