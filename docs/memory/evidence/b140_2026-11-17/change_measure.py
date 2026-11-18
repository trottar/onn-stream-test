#!/usr/bin/env python3
"""B140, offline (read only): the measure that tells the begin is on the window, from H7-D2 pass P's kept pictures.

The measure: both grabs grey, reduced to 64 x 48 (BOX); the share of cells whose value moved by more than 16 grey
levels. Computed for every pair the hub could meet: the window before the begin against itself later (notices fading,
the label coming and going — "no begin yet"), and the window before the begin against the window with the begin
(T88: S0's boot frame → S1's select screen; T89: the first read → the second, when its start was read). Also with the
right bar's label and the left bar's notices removed (as B139's settings leave the window). Prints JSON, numbers only.
usage: change_measure.py <repo>"""
import csv, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
REPO = Path(sys.argv[1]).resolve()
RULES = Path.home() / "privyhub_h7" / "rules"
FRAMES = REPO / "runtime" / "h7_frames"
ids = {json.loads(p.read_text())["players"]: p.name.split(".")[0] for p in RULES.glob("*.party.json")}
GRID, LEVELS = (64, 48), 16


def small(path):
    return np.asarray(Image.open(path).convert("L").resize(GRID, Image.BOX), dtype=np.float32)


def moved(a, b):
    return round(float((np.abs(a - b) > LEVELS).mean()), 4)


out = {"grid": list(GRID), "levels": LEVELS}
for who, n, stamp, before, begin in (("T88", 2, "20261117T234139Z", range(1, 13), range(13, 67)),
                                      ("T89", 4, "20261117T234305Z", range(1, 2), range(2, 67))):
    d = FRAMES / f"{ids[n]}_{stamp}"
    rows = {int(r["file"][1:7]): r for r in csv.DictReader(open(d / "index.csv"))}
    pics = {k: small(d / rows[k]["file"]) for k in rows}
    pre = list(before)
    no_begin = [moved(pics[a], pics[b]) for a in pre for b in pre if b > a]
    to_begin = [moved(pics[a], pics[b]) for a in pre for b in begin]
    out[who] = {"before_pictures": len(pre), "begin_pictures": len(list(begin)),
                "no_begin_yet_max": max(no_begin) if no_begin else None,
                "no_begin_yet_values": sorted(set(no_begin))[-5:] if no_begin else [],
                "to_begin_min": min(to_begin), "to_begin_median": float(np.median(to_begin)),
                "begin_classes": sorted({rows[k]["class"] for k in begin})}
print(json.dumps(out, indent=1))
