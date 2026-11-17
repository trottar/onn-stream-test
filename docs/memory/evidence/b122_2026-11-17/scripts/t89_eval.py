#!/usr/bin/env python3
"""B122: places on T89's real pictures (read only; numbers only; nothing written beside them). Cowork's labels; five
folds — each match's stretch (its select screen, its fight, its results) held out, learnt on the rest, the held-out
pictures read; then learnt from all five (the spec A will use, written to a scratch folder outside git, given as
argv[3]); B104's tone changes on every fold's held-out pictures; replay K = 3 and 2; one read's time. One JSON line per
result. Each picture read by a fresh Reader, as `score` does.

usage: t89_eval.py <repo> <run name> <scratch dir for the all-five spec> [--procs N]
"""
from __future__ import annotations

import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(sys.argv[1]).resolve()
RUN = sys.argv[2]
SCRATCH = Path(sys.argv[3])
PROCS = int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 4
sys.path.insert(0, str(REPO / "tools"))
import h7_endscreen as E  # noqa: E402

FR = REPO / "runtime" / "h7_frames"
LABELS = json.loads((FR / RUN / "labels.json").read_text())
RANGES = LABELS["runs"][RUN]


def out(**kw):
    print(json.dumps(kw, sort_keys=True), flush=True)


def tone(kind: str, *vals):                 # B104's, unchanged
    def f(img):
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


def matches() -> list[tuple[str, float, float]]:
    """Each match's stretch: from just after the previous match's last results picture to its own last one."""
    out_, prev_end, cur, last_to = [], -1.0, None, None
    for r in RANGES:
        lab = r["label"]
        if E.PLACE_LABEL.match(lab):
            cur, last_to = lab, float(r["to"])
        elif cur is not None and lab not in (E.IGNORE,):
            out_.append((cur, prev_end, last_to))
            prev_end, cur = last_to, None
    if cur is not None:
        out_.append((cur, prev_end, last_to))
    return out_


def cut(keep):
    """The labels with every range outside `keep(lo, hi)` set to ignore (a class left with no range dropped)."""
    rs = [dict(r) if keep(float(r["from"]), float(r["to"])) else dict(r, label=E.IGNORE) for r in RANGES]
    used = {r["label"] for r in rs} | {E.IGNORE}
    return {"classes": {c: t for c, t in LABELS["classes"].items() if c in used}, "runs": {RUN: rs}}


def items(labels) -> list[tuple[str, str]]:
    got = E.labelled_frames(FR, labels)
    return [(str(p), c) for c, ps in got.items() for p in ps]


_S = {}


def _init(spec, arrays):
    _S["spec"], _S["arrays"] = spec, arrays


def _read(job):
    path, label, tkey = job
    with Image.open(path) as im:
        img = im.convert("L")
    if tkey[0] != "none":
        img = tone(tkey[0], *tkey[1:])(img)
    t0 = time.perf_counter()
    r = E.Reader(_S["spec"], _S["arrays"]).read(img)
    return [Path(path).name, label, r["class"], r.get("places"), r.get("ports"), r["screen"],
            round((time.perf_counter() - t0) * 1000.0, 2)]


def read_set(spec, arrays, its, tkey=("none",)):
    with Pool(PROCS, initializer=_init, initargs=(spec, arrays)) as pool:
        return pool.map(_read, [(p, c, tkey) for p, c in its], chunksize=8)


def summarise(res, n=4) -> dict:
    rows, ports, other_screen = {}, {str(j + 1): {"right": 0, "unread": 0, "wrong": 0} for j in range(n)}, 0
    for name, label, cls, places, got, screen, _ms in res:
        t = rows.setdefault(label, {"right": 0, "unknown": 0, "wrong": 0, "other": 0, "n": 0})
        t["n"] += 1
        if label == E.OTHER and screen:
            other_screen += 1
        if E.PLACE_LABEL.match(label):
            row = E.place_row(label)
            k = ("right" if cls == E.END and places == row else "unknown" if cls == E.UNKNOWN else
                 "other" if cls == E.OTHER else "wrong")
            t[k] += 1
            if got:
                for j in range(n):
                    ports[str(j + 1)]["unread" if got[j] is None else "right" if got[j] == row[j] else "wrong"] += 1
        else:
            t["right" if cls == label else "unknown" if cls == E.UNKNOWN else "other" if cls == E.OTHER else "wrong"] += 1
    ms = [r[-1] for r in res]
    return {"rows": rows, "ports": ports, "other_read_as_screen": other_screen,
            "places_wrong": sum(v["wrong"] for v in ports.values()),
            "read_ms": {"median": round(float(np.median(ms)), 2), "p95": round(float(np.percentile(ms, 95)), 2)}}


def main():
    ms = matches()
    out(what="the matches' stretches (seconds of the run)", matches=[[m, round(a, 2), round(b, 2)] for m, a, b in ms])
    for i, (lab, lo, hi) in enumerate(ms):
        inside = lambda a, b, lo=lo, hi=hi: a > lo + 1e-6 and b <= hi + 1e-6
        train = cut(lambda a, b, f=inside: not f(a, b))
        held = cut(inside)
        t0 = time.perf_counter()
        spec, arrays, rep = E.learn(FR, train)
        learn_s = round(time.perf_counter() - t0, 1)
        its = items(held)
        base = read_set(spec, arrays, its)
        out(fold=f"M{i + 1}", held_out=lab, learn_s=learn_s, row=rep["places"]["row"],
            offsets=rep["places"]["offsets_px_320"], seen_in_column=rep["places"]["seen_in_column"],
            place_thresholds={q: v["threshold"] for q, v in rep["places"]["places"].items()},
            margin_needed=rep["places"]["margin_needed"], screens=rep["screens"], usable=spec["usable"],
            score=summarise(base))
        changed = {}
        for tk in TONES[1:]:
            res = read_set(spec, arrays, its, tk)
            n = sum(1 for a, b in zip(base, res) if (a[2], a[3]) != (b[2], b[3]))
            changed["+".join(map(str, tk))] = n
        out(fold=f"M{i + 1}", tone_changes_readings_changed=changed, total_changed=sum(changed.values()),
            pictures=len(its))
    t0 = time.perf_counter()
    spec, arrays, rep = E.learn(FR, LABELS, name="t89")
    out(what="learnt from all five: the spec A will use", learn_s=round(time.perf_counter() - t0, 1),
        report={k: rep[k] for k in ("frames_per_class", "screens", "usable")},
        places=rep["places"], spec_numbers={k: spec[k] for k in ("version", "screens", "k",
                                                                  "usable", "places")})
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = E.save_spec(spec, arrays, SCRATCH / "t89.endscreen.json")
    spec2, arrays2 = E.load_spec(path)
    res = read_set(spec2, arrays2, items(LABELS))
    out(what="the all-five spec -> every labelled picture", score=summarise(res))
    for k in (3, 2):
        rp = E.replay(FR / RUN, spec2, arrays2, k, LABELS)
        out(what=f"replay K = {k}", ended=rp["ended"], end_screen_arrivals_s=rp["end_screen_arrivals_s"],
            pictures=rp["pictures"])


if __name__ == "__main__":
    os.nice(10)
    main()
