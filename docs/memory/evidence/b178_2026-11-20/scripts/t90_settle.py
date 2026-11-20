#!/usr/bin/env python3
"""Queue BG B178: T90's six kept saves, settled — numbers only (no picture, no name). Reads the scratch copy of the
pictures session A's learn made (the tool's env places pointed at the scratch) and the label record my readings made.
usage: t90_settle.py <repo> (the env places set by the scratch's env.sh)"""
import csv, json, sys
from pathlib import Path
R = Path(sys.argv[1]); sys.path.insert(0, str(R / "tools"))
import numpy as np
from PIL import Image
import party_add_game as pag, h7_endscreen as es
code = "T90"
pics = pag.home(code) / "pictures"
kept = pag.kept_states(code)
rec = pag.label_record(code)
lab = json.loads((pics / "labels.json").read_text())
print("picture size (the hub's capture, every save):", sorted({Image.open(pics / r / next(csv.DictReader((pics / r / "index.csv").open()))["file"]).size for r in kept}))
print("the final screen held (s from the save's load, its own labelled range; then other screens):")
for r in sorted(k for k in kept if k.startswith("end_")):
    rng = [x for x in lab["runs"][r] if x["label"] != "ignore"]
    print(f"  {r}: {rng[0]['from']}-{rng[0]['to']} s of a 20-s run; pictures in it identical: ", end="")
    rows = [x["file"] for x in csv.DictReader((pics / r / "index.csv").open())]
    a = [np.asarray(Image.open(pics / r / f).convert("L"), np.int16) for f in rows[:int(rng[0]["to"]) // 1]]
    print(max(float(np.abs(x - a[0]).mean()) for x in a))
print("each side's place (640 x 480 game area):", json.dumps(rec.get("places")))
es_ = pag._endscreen()
nums = {r: v["readings"][0] for r, v in rec["saves"].items()}
labels = pag._labels(pics, kept, es_, {r: pag._score_class(v) for r, v in nums.items()})
b = {"game": "t90"}
full, farr, why = pag._learn_without(es_, b, pics, labels, [])
sc = full["score"]
print("digit glyphs, line height (px at 640 x 480):", [p["bot"] - p["top"] + 1 for p in sc["places"]])
print("digits learnt:", sc["keys"], "thresholds:", sc["thresholds"], "margin_needed:", sc["margin_needed"], "own variation:", sc.get("noise"))
print("left out — each glyph's nearest template, its distance and that template's threshold (a digit read only within it):")
for left in sorted(nums):
    spec, arr, why = pag._learn_without(es_, b, pics, labels, [left])
    rows = [x["file"] for x in csv.DictReader((pics / left / "index.csv").open())]
    with Image.open(pics / left / rows[0]) as im:
        a = es_.score_picture(im)
    out = []
    for k, pl in enumerate(spec["score"]["places"]):
        for ch, g in zip(str(nums[left][k]), es_.place_glyphs(a, pl) or []):
            d = es_.cell_dists(es_.glyph_cell(a, g, pl), arr["digit_refs"])
            i = int(np.argmin(d)); key = spec["score"]["keys"][i]
            out.append(f"{ch}: nearest {key} at {float(d[i]):.3f} (bar {spec['score']['thresholds'][key]})")
    print(f"  {left} ({'-'.join(map(str, nums[left]))}), learnt from the others {spec['score']['keys']}: " + "; ".join(out))
