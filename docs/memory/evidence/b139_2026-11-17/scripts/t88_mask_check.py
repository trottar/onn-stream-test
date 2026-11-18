#!/usr/bin/env python3
"""B139, offline (read only, nothing started): why the party's mask made T88's paused read worse on the hub.

H7-D2 pass P's kept T88 pictures (the watcher's own grabs, unmasked, 74: S0 the boot frame before any frame with the
launch's notices, S1-S5 paused after 2 / 10 / 30 / 90 / 210 frames, S6-S7 running, then paused again) through the real
reader and T88's spec, four ways per picture:
  un     — as kept;
  mask   — B137's mask as the party applies it (`h7_minigame.mask_label`, LABEL_BOX);
  black  — the label's own pixels (anything not black in the right bar's top 140 rows) set to black;
  gone   — the label's pixels replaced by the bar's own tone below it (the window as it is with RetroArch's text off);
each read by a fresh reader and by one reader kept across the pictures in order (as a watch does), with the bar cut
(the left / right edge columns no brighter than the darkest + 16). Then, to see the reads the hub took during the
launch's notices: the begin picture with S0's notices copied into the left bar, un / mask.
Prints JSON, numbers only. usage: t88_mask_check.py <repo>"""
import csv, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "tools")); sys.path.insert(0, str(REPO / "companion"))
import h7_endscreen as es
from h7_minigame import mask_label
RULES = Path.home() / "privyhub_h7" / "rules"
FRAMES = REPO / "runtime" / "h7_frames"
gid = [p.name.split(".")[0] for p in RULES.glob("*.party.json") if json.loads(p.read_text())["players"] == 2][0]
spec, arr = es.load_spec(RULES / f"{gid}.endscreen.json")
d = FRAMES / f"{gid}_20261117T234139Z"
rows = list(csv.DictReader(open(d / "index.csv")))
BAR = 1619                                              # the right bar's first column at 1920 x 1080 (T88's picture 1301 px)


def black(img):
    a = np.asarray(img).copy(); reg = a[:140, BAR:]; reg[reg.max(axis=2) > 0] = 0; return Image.fromarray(a)


def gone(img):
    a = np.asarray(img).copy(); below = np.median(a[200:, BAR:].reshape(-1, 3), axis=0).astype(np.uint8)
    reg = a[:140, BAR:]; reg[reg.max(axis=2) > int(below.max()) + 16] = below; return Image.fromarray(a)


def cut(img):
    A = np.asarray(img.convert("L")); cols = A.max(axis=0) <= int(A.min()) + 16
    return [es._lead(cols), es._lead(cols[::-1])]


ways = {"un": lambda i: i, "mask": mask_label, "black": black, "gone": gone}
clock = [0.0]
kept = {k: es.Reader(spec, arr, clock=lambda: clock[0]) for k in ways}
per = []
for r in rows:
    clock[0] = float(r["seconds"])
    img = Image.open(d / r["file"]).convert("RGB")
    rec = {"pic": int(r["file"][1:7]), "s": float(r["seconds"]), "kept_class": r["class"]}
    for k, f in ways.items():
        im = f(img)
        a = es.Reader(spec, arr).read(im); b = kept[k].read(im, now=clock[0])
        rec[k] = {"fresh": [a["class"], a["distances"]["screen"]], "kept": [b["class"], b["distances"]["screen"]], "cut": cut(im)}
    per.append(rec)


def summary(lo, hi):
    sel = [x for x in per if lo <= x["pic"] <= hi]
    out = {}
    for k in ways:
        ds = [x[k]["fresh"][1] for x in sel]
        out[k] = {"start": sum(x[k]["fresh"][0] == "start" for x in sel), "of": len(sel),
                  "screen_min_max": [min(ds), max(ds)], "cut_right_min": min(x[k]["cut"][1] for x in sel),
                  "kept_reader_start": sum(x[k]["kept"][0] == "start" for x in sel)}
    return out


beg = np.asarray(Image.open(d / rows[12]["file"]).convert("RGB"))
sim = {}
for src in (3, 8):
    s0 = np.asarray(Image.open(d / rows[src - 1]["file"]).convert("RGB"))
    w = beg.copy(); w[800:, :301] = s0[800:, :301]
    sim[f"begin_with_notices_of_pic_{src}"] = {k: [es.Reader(spec, arr).read(f(Image.fromarray(w)))["distances"]["screen"],
                                                   cut(f(Image.fromarray(w)))] for k, f in (("un", ways["un"]), ("mask", mask_label))}
print(json.dumps({"thresholds": {"screen": spec["screen_threshold"], "start": spec["class_thresholds"]["start"]},
                  "boot_S0_1_12": summary(1, 12), "paused_13_47": summary(13, 47), "all_paused_13_66": summary(13, 66),
                  "running_67_74": summary(67, 74), "notices_simulated": sim, "per_picture": per}, indent=1))
