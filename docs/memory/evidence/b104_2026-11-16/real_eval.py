#!/usr/bin/env python3
"""B104: the tone-independent reader on the real pictures (read only; numbers only; nothing written beside them).

Sources (outside git, read only): H7-V1's headless screenshots with Cowork's labels ("V1"), and H7-V2's 508 window
pictures with Cowork's labels ("LIVE"). Every spec here is learnt in memory; none is written anywhere. Each picture is
read by a fresh Reader (the full search when it is not the screen), as `score` does. One JSON line per result.

usage: real_eval.py <repo> <arrangement: a1|a2|a3|a4|a5|replay|all> [--procs N]
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "tools"))
import h7_endscreen as E  # noqa: E402

FR = REPO / "runtime" / "h7_frames"
V1 = (FR / "t88", json.loads((FR / "t88" / "labels.json").read_text()))
LIVE_RUN = "h7v2_20261116_run"
LIVE_LABELS = json.loads((FR / LIVE_RUN / "labels.json").read_text())
LIVE = (FR, LIVE_LABELS)


def out(**kw):
    print(json.dumps(kw, sort_keys=True), flush=True)


def live_match(name: str) -> dict:
    """The live labels cut to one match's seconds (the labels' `matches` block)."""
    m = LIVE_LABELS["matches"][name]
    lo, hi = float(m["from"]), float(m["to"])
    ranges = [r for r in LIVE_LABELS["runs"][LIVE_RUN] if float(r["from"]) >= lo - 1e-6 and float(r["to"]) <= hi + 1e-6]
    return {"classes": LIVE_LABELS["classes"], "runs": {LIVE_RUN: ranges}}


def v1_runs(*runs: str) -> dict:
    return {"classes": V1[1]["classes"], "runs": {r: V1[1]["runs"][r] for r in runs}}


# --- tone changes, on the full picture before reduction, clipped to 0-255 -------------------------------------------
def tone(kind: str, *vals):
    def f(img: Image.Image) -> Image.Image:
        a = np.asarray(img, dtype=np.float32)
        for k, v in zip(kind.split("+"), vals):
            if k == "offset":
                a = a + v
            elif k == "gain":
                a = a * v
            elif k == "gamma":
                a = 255.0 * (np.clip(a, 0, 255) / 255.0) ** v
            a = np.clip(a, 0, 255)
        return Image.fromarray(np.rint(a).astype(np.uint8), "L")
    return f


TONES = [("none",)] + [("offset", v) for v in (-30, -20, -10, 10, 20, 30)] + \
        [("gain", v) for v in (0.8, 0.9, 1.1, 1.2)] + [("gamma", v) for v in (0.8, 0.9, 1.1, 1.25)] + \
        [("gain+offset", g, o) for g in (0.8, 1.2) for o in (-30, 30)] + \
        [("gamma+offset", g, o) for g in (0.8, 1.25) for o in (-30, 30)] + \
        [("gain+gamma", g, c) for g in (0.8, 1.2) for c in (0.8, 1.25)]


# --- reading a labelled set --------------------------------------------------------------------------------------
def items(sources: list, half: str | None) -> list[tuple[str, str]]:
    got = []
    for runs, labels in sources:
        for c, ps in E.labelled_frames(runs, E.load_labels(labels), half).items():
            got += [(c, str(p)) for p in ps]
    return got


_W: dict = {}


def _init(spec, arrays):
    _W["spec"], _W["arrays"] = spec, arrays


def _read_one(job):
    label, path, tkey = job
    with Image.open(path) as im:
        img = im.convert("L")
    if tkey[0] != "none":
        img = tone(tkey[0], *tkey[1:])(img)
    t0 = time.perf_counter()
    r = E.Reader(_W["spec"], _W["arrays"]).read(img)
    ms = (time.perf_counter() - t0) * 1000.0
    c = r["class"]
    return label, c, r["screen"], r["distances"]["screen"], (r["distances"].get(label) if c == label else None), \
        (r["margin"] if c == label else None), ms


def read_set(spec, arrays, its, tkey=("none",), procs=6) -> list:
    with Pool(procs, initializer=_init, initargs=(spec, arrays)) as pool:
        return pool.map(_read_one, [(c, p, tkey) for c, p in its], chunksize=8)


def summarise(spec, res, base=None) -> dict:
    cols = [*spec["classes"], E.UNKNOWN, E.OTHER]
    conf: dict = {}
    worst, least, other_least, other_screen = {}, {}, 1.0, 0
    for label, c, scr, sd, own, margin, _ms in res:
        conf.setdefault(label, dict.fromkeys(cols, 0))[c] += 1
        if label == E.OTHER:
            other_least = min(other_least, sd)
            other_screen += bool(scr)
        if own is not None:
            worst[label] = max(worst.get(label, 0.0), own)
            least[label] = min(least.get(label, 9.0), margin)
    s = {"right": {c: [conf[c][c], sum(conf[c].values())] for c in conf},
         "wrong": {c: {k: v for k, v in conf[c].items() if k != c and v} for c in conf},
         "other_read_as_screen": other_screen, "other_least_screen_distance": round(other_least, 4),
         "screen_threshold": spec["screen_threshold"],
         "worst_own_class_distance": {k: round(v, 4) for k, v in worst.items()},
         "least_margin": {k: round(v, 4) for k, v in least.items()}, "margin_needed": spec["margin_needed"],
         "read_ms_median": round(float(np.median([r[-1] for r in res])), 2)}
    screens = [r[3] for r in res if r[0] != E.OTHER]
    if screens:
        s["screens_screen_distance"] = {"median": round(float(np.median(screens)), 4),
                                        "p95": round(float(np.percentile(screens, 95)), 4),
                                        "max": round(float(max(screens)), 4)}
    if base is not None:
        s["changed_vs_untouched"] = sum(1 for a, b in zip(res, base) if a[1] != b[1])
        s["misread"] = sum(1 for a, b in zip(res, base) if a[1] != b[1] and a[1] != E.OTHER and a[1] != a[0])
    return s


def learn_mem(sources, half=None):
    t0 = time.perf_counter()
    spec, arrays, report = E.learn(sources, None, half)
    report["learn_s"] = round(time.perf_counter() - t0, 1)
    return spec, arrays, report


def short_report(rep: dict) -> dict:
    return {"frames_per_class": rep["frames_per_class"], "frames_per_source": rep.get("frames_per_source"),
            "screen_mask_px": rep["screen_mask"]["px"], "screen_mask_share": rep["screen_mask"]["share"],
            "outcome_mask_px": rep["outcome_mask"]["px"], "outcome_bbox_160x120": rep["outcome_mask"]["bbox_160x120"],
            "screen": rep["screen"], "classes": rep["classes"], "margin_needed": rep["margin_needed"],
            "smallest_margin_seen": rep["smallest_margin_seen"], "usable": rep["usable"], "unlike_label": rep.get("unlike_label"), "learn_s": rep["learn_s"]}


def main(which: str, procs: int) -> None:
    allv1 = items([V1], None)
    alllive = items([LIVE], None)
    if which in ("a1", "all"):
        spec, arrays, rep = learn_mem([V1])
        out(arrangement="1a", what="learnt from H7-V1's screenshots alone", report=short_report(rep))
        out(arrangement="1a", what="-> all live pictures against Cowork's labels",
            score=summarise(spec, read_set(spec, arrays, alllive, procs=procs)))
        spec, arrays, rep = learn_mem([LIVE])
        out(arrangement="1b", what="learnt from the live pictures alone", report=short_report(rep))
        out(arrangement="1b", what="-> all H7-V1 frames", score=summarise(spec, read_set(spec, arrays, allv1, procs=procs)))
    if which in ("a2", "all"):
        for tag, learn_from, score_on, what in (
                ("2a", [(FR, live_match("M1")), (V1[0], v1_runs("end_p2"))], [(FR, live_match("M2"))],
                 "learnt from live match 1 (its start, end_P1, other) + H7-V1's end_P2 run -> live match 2"),
                ("2b", [(FR, live_match("M2")), (V1[0], v1_runs("end_p1"))], [(FR, live_match("M1"))],
                 "the mirror: live match 2 (its start, end_P2, other) + H7-V1's end_P1 run -> live match 1")):
            spec, arrays, rep = learn_mem(learn_from)
            out(arrangement=tag, what=what, report=short_report(rep),
                score=summarise(spec, read_set(spec, arrays, items(score_on, None), procs=procs)))
    if which in ("a3", "all"):
        spec, arrays, rep = learn_mem([V1, LIVE])
        out(arrangement="3", what="learnt from everything (H7-V1 + the live run): the spec A will use",
            report=short_report(rep), spec_numbers={k: spec[k] for k in (
                "screen_threshold", "class_thresholds", "separable", "margin_needed", "usable", "screen_mask_px",
                "outcome_mask_px", "frames", "aspect", "version", "measure")})
        out(arrangement="3", what="-> H7-V1 (all)", score=summarise(spec, read_set(spec, arrays, allv1, procs=procs)))
        out(arrangement="3", what="-> live (all)", score=summarise(spec, read_set(spec, arrays, alllive, procs=procs)))
    if which in ("a4", "all"):
        spec, arrays, rep = learn_mem([V1, LIVE], half="first")
        held = items([V1, LIVE], "second")
        out(arrangement="4a", what="learnt on the first halves of both; tone changes on the held-out second halves",
            report=short_report(rep), held_out=len(held))
        base = None
        for tk in TONES:
            res = read_set(spec, arrays, held, tk, procs)
            if base is None:
                base = res
            out(arrangement="4a", tone=list(tk), score=summarise(spec, res, base))
        spec, arrays, rep = learn_mem([V1])
        out(arrangement="4b", what="learnt from H7-V1 alone; tone changes on all live pictures (all held out)")
        base = None
        for tk in TONES:
            res = read_set(spec, arrays, alllive, tk, procs)
            if base is None:
                base = res
            out(arrangement="4b", tone=list(tk), score=summarise(spec, res, base))
    if which in ("a5", "all"):
        spec, arrays, rep = learn_mem([V1], half="first")
        out(arrangement="5", what="H7-V1 alone as in B102: first halves -> second halves", report=short_report(rep))
        held = items([V1], "second")
        base = read_set(spec, arrays, held, procs=procs)
        out(arrangement="5", moved="none", score=summarise(spec, base))
        for dx, dy, s in ((2, 0, 1.0), (4, 0, 1.0), (8, 0, 1.0), (0, 8, 1.0), (8, 8, 1.0), (0, 4, 1.0), (-6, 5, 1.0),
                          (0, 0, 0.97), (0, 0, 1.03), (0, 0, 0.95), (0, 0, 1.05), (0, 0, 1.08), (5, 3, 1.04),
                          (-4, -6, 0.96), (12, 0, 1.0), (16, 0, 1.0), (0, 0, 0.92)):
            with Pool(procs, initializer=_init, initargs=(spec, arrays)) as pool:
                res = pool.map(_moved_one, [(c, p, (dx, dy, s)) for c, p in held], chunksize=8)
            out(arrangement="5", moved=[dx, dy, s], score=summarise(spec, res))
        # one read's time, single process, a live picture (1920 x 1080) and a screenshot (640 x 525), decoded first
        for name, path in (("screenshot", items([V1], None)[0][1]), ("window", alllive[0][1])):
            with Image.open(path) as im:
                img = im.convert("L")
            rd = E.Reader(spec, arrays)
            rd.read(img)
            ts = []
            for _ in range(30):
                t0 = time.perf_counter()
                rd.read(img, search=False)
                ts.append((time.perf_counter() - t0) * 1000.0)
            t0 = time.perf_counter()
            rd._search(E.mid(img))
            out(arrangement="5", read_time=name, size=list(img.size), one_read_ms_median=round(float(np.median(ts)), 2),
                one_read_ms_worst=round(float(max(ts)), 2), search_ms=round((time.perf_counter() - t0) * 1000.0, 1))
    if which in ("replay", "all"):
        spec, arrays, rep = learn_mem([V1, LIVE])
        for k in (3, 2):
            r = E.replay(FR / LIVE_RUN, spec, arrays, k=k, labels=LIVE_LABELS)
            counts = {}
            for _t, c, _d in r["reads"]:
                counts[c] = counts.get(c, 0) + 1
            out(replay="live run, the arrangement-3 spec", k=k, pictures=r["pictures"], classes_read=counts,
                changes=r["changes"], ended=r["ended"], end_screen_arrivals_s=r["end_screen_arrivals_s"])


def _moved_one(job):
    label, path, (dx, dy, s) = job
    with Image.open(path) as im:
        img = im.convert("L")
    w, h = img.size
    cx, cy = w / 2.0, h / 2.0
    k = w / 640.0
    ddx, ddy = dx * k, dy * k
    img = img.transform(img.size, Image.AFFINE, (1 / s, 0, cx - (cx + ddx) / s, 0, 1 / s, cy - (cy + ddy) / s),
                        resample=Image.BILINEAR, fillcolor=0)
    t0 = time.perf_counter()
    r = E.Reader(_W["spec"], _W["arrays"]).read(img)
    ms = (time.perf_counter() - t0) * 1000.0
    c = r["class"]
    return label, c, r["screen"], r["distances"]["screen"], (r["distances"].get(label) if c == label else None), \
        (r["margin"] if c == label else None), ms


if __name__ == "__main__":
    procs = int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 6
    main(sys.argv[2], procs)
