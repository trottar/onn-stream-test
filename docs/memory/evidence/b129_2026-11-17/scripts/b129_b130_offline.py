#!/usr/bin/env python3
"""B129 / B130 offline (read only; numbers only; nothing written beside the pictures). H7-D1's four keep folders and the
earlier labelled runs, read with the rules folder's specs (read in place) as the watcher reads: one Reader per watch,
its clock the pictures' own seconds. B129: each picture cut by the game's own window rectangle (the rule's rectangle,
stated); B130: the watcher's settle rule replayed at 8.0 s and 15.0 s. One JSON line per result; ids never printed.

usage: b129_b130_offline.py <repo> <part: b129|b130>
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image

REPO = Path(sys.argv[1]).resolve()
PART = sys.argv[2]
sys.path.insert(0, str(REPO / "tools"))
import h7_endscreen as E  # noqa: E402

F = REPO / "runtime" / "h7_frames"
RULES = Path.home() / "privyhub_h7" / "rules"
T88_RECT = (0, 0, 1920, 1080)          # T88's window (the keeper's log, and the rule: the process's own window)
T89_RECT = (960, 384, 960, 720)        # T89's window (the keeper's log; = the stream's 960 x 720 window)
D1 = {"T88 early": "_20261117T055540Z", "T88 late": "_20261117T055857Z",
      "T89 early": "_20261117T055953Z", "T89 late": "_20261117T060103Z"}


def out(**kw):
    print(json.dumps(kw, sort_keys=True), flush=True)


def spec_of(system):
    path = next(p for p in sorted(RULES.glob(f"game_{system}_*.endscreen.json")))
    return E.load_spec(path)


def run_dir(suffix):
    return next(p for p in F.iterdir() if p.name.endswith(suffix))


def rows(run):
    with (run / "index.csv").open(newline="") as fh:
        return list(csv.DictReader(fh))


def cut(img, rect):
    x, y, w, h = rect
    return img.crop((x, y, x + w, y + h))          # Pillow pads what lies off the screen black, as the grab's crop


def watch(run, spec, arr, rect):
    """The watcher's reads of a keep folder, in order, one Reader (its clock the pictures' seconds)."""
    now = [0.0]
    rd = E.Reader(spec, arr, clock=lambda: now[0])
    res = []
    for r in rows(run):
        t = float(r["seconds"])
        now[0] = t
        with Image.open(run / r["file"]) as im:
            img = cut(im.convert("L"), rect) if rect is not None else im.convert("L")
        x = rd.read(img, now=t)
        res.append({"s": t, "class": x["class"], "screen": x["distances"]["screen"],
                    "start": x["distances"].get(spec["start_class"])})
    return res


def settle(reads, window):
    """B105 / B130's rule: true at the first read naming the start; false at the first read at or after the window."""
    for r in reads:
        if r["class"] == "start":
            return {"recognised": True, "at_s": r["s"]}
        if r["s"] >= window:
            return {"recognised": False, "at_s": r["s"]}
    return {"recognised": None, "at_s": None}


def b129():
    s89, a89 = spec_of("n64")
    s88, a88 = spec_of("ps1")
    for name in ("T89 early", "T89 late"):
        run = run_dir(D1[name])
        whole = watch(run, s89, a89, None)
        mine = watch(run, s89, a89, T89_RECT)
        first = next((r for r in mine if r["class"] == "start"), None)
        out(item="B129", run=name, rect=list(T89_RECT), pictures=len(mine),
            as_kept_whole_screen={"start_reads": sum(r["class"] == "start" for r in whole),
                                  "least_start": min(r["start"] for r in whole if r["start"] is not None)},
            cut_by_the_rule={"first_start_s": first["s"] if first else None,
                             "least_start": min(r["start"] for r in mine if r["start"] is not None),
                             "classes": {c: sum(r["class"] == c for r in mine) for c in {r["class"] for r in mine}},
                             "start_threshold": s89["screens"]["start"]["threshold"]},
            reads=[[r["s"], r["class"], r["start"]] for r in mine])
    # other read as the screen: T89's labelled fights (H7-C1's run — already the window: the rule's cut is the whole picture)
    lab = E.load_labels(F / "t89_c1_20261117T003035Z" / "labels.json")
    others = E.labelled_frames(F, lab)["other"]
    screen = 0
    least = 1.0
    for p in others:
        with Image.open(p) as im:
            x = E.Reader(s89, a89).read(im.convert("L"))
        screen += bool(x["screen"])
        least = min(least, x["distances"]["screen"])
    out(item="B129", what="T89's labelled fights (H7-C1) through the T89 spec", pictures=len(others),
        other_read_as_screen=screen, least_screen_distance=round(least, 4))
    # T88: the rule finds the same full-screen window — the pictures read exactly as the watcher read them
    for name in ("T88 early", "T88 late"):
        run = run_dir(D1[name])
        mine = watch(run, s88, a88, T88_RECT)
        kept = rows(run)
        same_class = sum(m["class"] == k["class"] for m, k in zip(mine, kept))
        dmax = max(abs(m["screen"] - float(k["screen"])) for m, k in zip(mine, kept))
        out(item="B129", run=name, rect=list(T88_RECT), pictures=len(mine), class_same_as_the_watcher=same_class,
            screen_distance_max_difference=round(dmax, 4))
    return


def b130():
    s89, a89 = spec_of("n64")
    s88, a88 = spec_of("ps1")
    runs = {}
    for name in ("T88 early", "T88 late"):                       # the watcher's own reads (today's path)
        runs[name] = [{"s": float(r["seconds"]), "class": r["class"]} for r in rows(run_dir(D1[name]))]
    for name in ("T89 early", "T89 late"):                       # B129's cut
        runs[name] = watch(run_dir(D1[name]), s89, a89, T89_RECT)
    for name, reads in runs.items():
        out(item="B130", run=name, setup=True, at_15=settle(reads, 15.0), at_8=settle(reads, 8.0))
    # never the start
    synth = [{"s": round(1.2 + i, 2) if i == 0 else float(i + 1), "class": c}
             for i, c in enumerate((["other", "unknown"] * 30)[:45])]
    out(item="B130", run="synthetic: never the start", at_15=settle(synth, 15.0), at_8=settle(synth, 8.0))
    t89_desktop = [{"s": float(r["seconds"]), "class": r["class"]} for r in rows(run_dir(D1["T89 early"]))]
    out(item="B130", run="H7-D1 T89 early as the watcher read it (the stale rectangle)",
        at_15=settle(t89_desktop, 15.0), at_8=settle(t89_desktop, 8.0))
    live = F / "h7v2_20261116_run"
    lab = E.load_labels(live / "labels.json")
    for r in [x for x in lab["runs"]["h7v2_20261116_run"] if x["label"] == "other"]:
        lo, hi = float(r["from"]), float(r["to"])
        pics = [x for x in rows(live) if lo <= float(x["seconds"]) <= hi][:30]
        now = [0.0]
        rd = E.Reader(s88, a88, clock=lambda: now[0])
        reads = []
        for x in pics:
            t = float(x["seconds"]) - lo + 1.0
            now[0] = t
            with Image.open(live / x["file"]) as im:
                reads.append({"s": round(t, 2), "class": rd.read(im.convert("L"), now=t)["class"]})
        out(item="B130", run=f"H7-V2 live fight stretch from {lo:.1f} s (30 reads)", at_15=settle(reads, 15.0),
            at_8=settle(reads, 8.0), classes=sorted({r["class"] for r in reads}))
    # earlier answers: H7-C2's T88 cheat slot 1 stretch (a setup; 6.97 s) — the per-load replay's reads
    c2 = F / "t88_c2_20261117T024815Z"
    now = [0.0]
    rd = E.Reader(s88, a88, clock=lambda: now[0])
    reads = []
    for x in rows(c2)[:41]:
        t = float(x["seconds"])
        now[0] = t
        with Image.open(c2 / x["file"]) as im:
            reads.append({"s": t, "class": rd.read(im.convert("L"), now=t)["class"]})
    out(item="B130", run="H7-C2 T88 cheat slot 1 (from its load)", at_15=settle(reads, 15.0), at_8=settle(reads, 8.0))


if __name__ == "__main__":
    {"b129": b129, "b130": b130}[PART]()
