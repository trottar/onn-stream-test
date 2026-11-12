#!/usr/bin/env python3
"""B102 follow-up on T88's real frames (read-only; numbers only): for the moved cases where `t88_eval.py` showed a
frame not read right with the search on, what those frames were read as (the confusion counts) — a wrong side would
matter, `unknown` would not end a game. Same learn (first half), same moved second half as `t88_eval.py`.

usage: t88_moved_confusion.py <repo> <runs folder> <labels file> dx,dy,scale [dx,dy,scale ...]
"""
import json
import sys
from pathlib import Path

from PIL import Image

REPO, RUNS, LABELS = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(REPO / "tools"))
import h7_endscreen as E  # noqa: E402


def moved(dx, dy, s):
    def f(img):
        w, h = img.size
        cx, cy = w / 2.0, h / 2.0
        return img.transform(img.size, Image.AFFINE, (1 / s, 0, cx - (cx + dx) / s, 0, 1 / s, cy - (cy + dy) / s),
                             resample=Image.BILINEAR, fillcolor=0)
    return f


spec, arrays, _ = E.learn(RUNS, LABELS, half="first", name="t88")
for case in sys.argv[4:]:
    dx, dy, s = (float(x) for x in case.split(","))
    r = E.score(RUNS, LABELS, spec, arrays, half="second", transform=moved(dx, dy, s), search=True)
    print(json.dumps({"dx": dx, "dy": dy, "scale": s, "confusion": r["confusion"],
                      "other_read_as_screen": r["other_read_as_screen"]}, sort_keys=True), flush=True)
