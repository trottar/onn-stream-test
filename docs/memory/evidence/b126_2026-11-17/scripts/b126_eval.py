#!/usr/bin/env python3
"""B126: both readers on the unlocked select screens (read only; numbers only; nothing written beside the pictures).

Every spec is learnt in memory with `tools/h7_endscreen.py` as it stands (the design's steps 1-11). One JSON line per
result. Each picture read by a fresh Reader (as `score` does). No names, no paths in the output (pictures by file
name only).

usage: b126_eval.py <repo> <part: t88|t88tone|t89|t89tone|replay|all> [--procs N] [--rules-spec <the T88 spec>]
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
PART = sys.argv[2]
PROCS = int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 6
RULES_SPEC = sys.argv[sys.argv.index("--rules-spec") + 1] if "--rules-spec" in sys.argv else None
sys.path.insert(0, str(REPO / "tools"))
import h7_endscreen as E  # noqa: E402

FR = REPO / "runtime" / "h7_frames"
C2_88, C2_89, C1_89, LIVE_RUN = ("t88_c2_20261117T024815Z", "t89_c2_20261117T024815Z", "t89_c1_20261117T003035Z",
                                 "h7v2_20261116_run")


def lab(run):
    return json.loads((FR / run / "labels.json").read_text())


V1 = (FR / "t88", lab("t88"))                 # H7-V1's screenshots (runs inside t88/)
LIVE = (FR, lab(LIVE_RUN))
C2 = (FR, lab(C2_88))
C1 = (FR, lab(C1_89))
T89C2 = (FR, lab(C2_89))
SRC88 = {"V1": V1, "LIVE": LIVE, "C2": C2}


def out(**kw):
    print(json.dumps(kw, sort_keys=True), flush=True)


def tone(kind: str, *vals):                   # B104's, unchanged
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


def items(src, half=None) -> list[tuple[str, str]]:
    runs, labels = src
    got = E.labelled_frames(runs, E.load_labels(labels), half)
    return [(str(p), c) for c, ps in got.items() for p in ps]


_S: dict = {}


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
    d = r["distances"]
    return [Path(path).name, label, r["class"], r.get("places"), r.get("ports"), bool(r["screen"]),
            d.get("screen"), d.get(label) if label in d else None, r.get("margin"),
            round((time.perf_counter() - t0) * 1000.0, 2)]


def read_set(spec, arrays, its, tkey=("none",)):
    with Pool(PROCS, initializer=_init, initargs=(spec, arrays)) as pool:
        return pool.map(_read, [(p, c, tkey) for p, c in its], chunksize=8)


def sum_v2(res) -> dict:
    """Version 2: per class right / n, unknown, wrong classes, other as the screen; the distances."""
    conf: dict = {}
    other_screen, other_least = 0, 1.0
    own_screen, own_class, margins = [], {}, {}
    for name, label, cls, _pl, _po, screen, sd, cd, margin, _ms in res:
        conf.setdefault(label, {})
        conf[label][cls] = conf[label].get(cls, 0) + 1
        if label == E.OTHER:
            other_screen += screen
            other_least = min(other_least, sd)
        else:
            own_screen.append(sd)
            if cls == label:
                own_class.setdefault(label, []).append(cd)
                margins.setdefault(label, []).append(margin)
    s = {"right": {c: [v.get(c, 0), sum(v.values())] for c, v in conf.items()},
         "unknown": {c: v.get(E.UNKNOWN, 0) for c, v in conf.items() if v.get(E.UNKNOWN)},
         "wrong_class": {c: {k: n for k, n in v.items() if k not in (c, E.UNKNOWN, E.OTHER)}
                         for c, v in conf.items() if any(k not in (c, E.UNKNOWN, E.OTHER) for k in v)},
         "screens_read_other": {c: v.get(E.OTHER, 0) for c, v in conf.items() if c != E.OTHER and v.get(E.OTHER)},
         "other_read_as_screen": other_screen, "other_least_screen_distance": round(other_least, 4)}
    if own_screen:
        s["screens_screen_distance"] = {"median": round(float(np.median(own_screen)), 4),
                                        "max": round(float(max(own_screen)), 4)}
    s["worst_own_class_distance"] = {c: round(max(v), 4) for c, v in own_class.items()}
    s["least_margin"] = {c: round(min(v), 4) for c, v in margins.items()}
    s["not_right"] = [[r[0], r[1], r[2]] for r in res if r[2] != r[1]]
    return s


def sum_v3(res, n=4) -> dict:
    rows, ports, other_screen = {}, {str(j + 1): {"right": 0, "unread": 0, "wrong": 0} for j in range(n)}, 0
    for name, label, cls, places, got, screen, *_ in res:
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
            t["right" if cls == label else "unknown" if cls == E.UNKNOWN else "other" if cls == E.OTHER
              else "wrong"] += 1
    ms = [r[-1] for r in res]
    return {"rows": rows, "ports": ports, "other_read_as_screen": other_screen,
            "places_wrong": sum(v["wrong"] for v in ports.values()),
            "not_right": [[r[0], r[1], r[2], r[3]] for r in res
                          if not ((r[2] == r[1]) or (r[2] == E.END and r[3] == E.place_row(r[1])
                                                     if E.PLACE_LABEL.match(r[1]) else False))],
            "read_ms": {"median": round(float(np.median(ms)), 2), "p95": round(float(np.percentile(ms, 95)), 2)}}


def learn(sources, half=None):
    t0 = time.perf_counter()
    spec, arrays, rep = E.learn(list(sources), None, half)
    rep["learn_s"] = round(time.perf_counter() - t0, 1)
    return spec, arrays, rep


def rep_v2(rep):
    return {"frames_per_class": rep["frames_per_class"], "frames_per_source": rep.get("frames_per_source"),
            "screen_mask": rep["screen_mask"], "outcome_mask": rep["outcome_mask"], "screen": rep["screen"],
            "classes": rep["classes"], "margin_needed": rep["margin_needed"],
            "smallest_margin_seen": rep["smallest_margin_seen"], "usable": rep["usable"],
            "unlike_label": rep.get("unlike_label"), "learn_s": rep["learn_s"]}


def per_source_v2(spec, arrays, names):
    for nm in names:
        res = read_set(spec, arrays, items(SRC88[nm]))
        yield nm, sum_v2(res)


# --- T88 ----------------------------------------------------------------------------------------------------------
def t88():
    spec0, arr0, rep0 = learn([V1, LIVE])
    same = None
    if RULES_SPEC:
        rs, ra = E.load_spec(RULES_SPEC)
        keys = ("screen_threshold", "class_thresholds", "margin_needed", "screen_mask_px", "outcome_mask_px",
                "classes", "version")
        same = {"numbers_equal": all(rs[k] == spec0[k] for k in keys),
                "arrays_equal": all(np.array_equal(ra[k], arr0[k]) for k in ra)}
    out(step="1 learnt from V1 + LIVE (H7-V3's spec) in memory", equal_to_rules_folder_spec=same,
        report=rep_v2(rep0))
    for nm in ("C2", "V1", "LIVE"):
        out(step="1 H7-V3's spec scored", on=nm, score=sum_v2(read_set(spec0, arr0, items(SRC88[nm]))))
    spec, arrays, rep = learn([V1, LIVE, C2])
    out(step="2 learnt from V1 + LIVE + C2", report=rep_v2(rep),
        spec_numbers={k: spec[k] for k in ("screen_threshold", "class_thresholds", "margin_needed", "separable",
                                            "usable", "screen_mask_px", "outcome_mask_px")})
    for nm, s in per_source_v2(spec, arrays, ("V1", "LIVE", "C2")):
        out(step="2 the three-source spec scored", on=nm, score=s)
    for held, train in (("LIVE", ("V1", "C2")), ("V1", ("LIVE", "C2"))):
        sp, ar, rp = learn([SRC88[t] for t in train])
        out(step="3 fold", learnt_from=list(train), held_out=held, report=rep_v2(rp),
            score=sum_v2(read_set(sp, ar, items(SRC88[held]))))


def t88tone():
    for name, sources, half, held in (("learnt without C2 -> all C2", [V1, LIVE], None, None),
                                      ("V1 + LIVE + C2 first halves -> C2 second halves", [V1, LIVE, C2], "first",
                                       "second")):
        spec, arrays, rep = learn(sources, half)
        its = items(C2, held)
        base = read_set(spec, arrays, its)
        changed, misread, other_screen = {}, {}, {}
        for tk in TONES[1:]:
            res = read_set(spec, arrays, its, tk)
            key = "+".join(map(str, tk))
            changed[key] = sum(1 for a, b in zip(base, res) if a[2] != b[2])
            misread[key] = sum(1 for b in res if b[2] not in (b[1], E.UNKNOWN, E.OTHER))
            other_screen[key] = sum(1 for b in res if b[1] == E.OTHER and b[5])
        out(step="4 tone grid on held-out C2", arrangement=name, usable=spec["usable"], pictures=len(its),
            untouched=sum_v2(base), readings_changed=changed, total_changed=sum(changed.values()),
            misread_total=sum(misread.values()), other_as_screen_total=sum(other_screen.values()))


# --- T89 ----------------------------------------------------------------------------------------------------------
C1_RANGES = C1[1]["runs"][C1_89]


def c1_matches():
    """B122's stretches: from just after the previous match's last results picture to its own last one."""
    out_, prev_end, cur, last_to = [], -1.0, None, None
    for r in C1_RANGES:
        lb = r["label"]
        if E.PLACE_LABEL.match(lb):
            cur, last_to = lb, float(r["to"])
        elif cur is not None and lb != E.IGNORE:
            out_.append((cur, prev_end, last_to))
            prev_end, cur = last_to, None
    if cur is not None:
        out_.append((cur, prev_end, last_to))
    return out_


def c1_cut(keep):
    rs = [dict(r) if keep(float(r["from"]), float(r["to"])) else dict(r, label=E.IGNORE) for r in C1_RANGES]
    used = {r["label"] for r in rs} | {E.IGNORE}
    return (FR, {"classes": {c: t for c, t in C1[1]["classes"].items() if c in used}, "runs": {C1_89: rs}})


def t89c2_parts():
    """T89C2's start pictures split by the labels' own words: 4-41 unlocked, 86-102 locked (by picture number)."""
    its = items(T89C2)
    def num(p):
        return int(Path(p).stem[1:])
    unlocked = [(p, c) for p, c in its if c == E.START and 4 <= num(p) <= 41]
    locked = [(p, c) for p, c in its if c == E.START and 86 <= num(p) <= 102]
    ends = [(p, c) for p, c in its if c != E.START]
    return unlocked, locked, ends


def rep_v3(rep, spec):
    return {"frames_per_class": rep["frames_per_class"], "screens": rep["screens"], "row": rep["places"]["row"],
            "offsets": rep["places"]["offsets_px_320"], "seen_in_column": rep["places"]["seen_in_column"],
            "place_thresholds": {q: v["threshold"] for q, v in rep["places"]["places"].items()},
            "place_gaps": {q: v["gap"] for q, v in rep["places"]["places"].items()},
            "margin_needed": rep["places"]["margin_needed"], "glyph_px": rep["places"].get("glyph_px"),
            "usable": spec["usable"], "learn_s": rep["learn_s"]}


def t89_parts_scored(spec, arrays):
    unlocked, locked, ends = t89c2_parts()
    return {"unlocked_start": sum_v3(read_set(spec, arrays, unlocked)),
            "locked_start": sum_v3(read_set(spec, arrays, locked)),
            "results": sum_v3(read_set(spec, arrays, ends))}


def t89():
    spec0, arr0, rep0 = learn([C1])
    out(step="6 B122's all-five spec (C1 alone) in memory", report=rep_v3(rep0, spec0))
    out(step="6 C1 alone -> T89C2 (held out)", score=t89_parts_scored(spec0, arr0))
    spec, arrays, rep = learn([C1, T89C2])
    out(step="7 learnt from C1 + T89C2", report=rep_v3(rep, spec))
    out(step="7 scored on C1", score=sum_v3(read_set(spec, arrays, items(C1))))
    out(step="7 scored on T89C2", score=t89_parts_scored(spec, arrays))
    for i, (lb, lo, hi) in enumerate(c1_matches()):
        inside = (lambda a, b, lo=lo, hi=hi: a > lo + 1e-6 and b <= hi + 1e-6)
        train = c1_cut(lambda a, b, f=inside: not f(a, b))
        held = c1_cut(inside)
        sp, ar, rp = learn([train, T89C2])
        out(step="8 C1 fold with T89C2 in training", fold=f"M{i + 1}", held_out=lb, report=rep_v3(rp, sp),
            score=sum_v3(read_set(sp, ar, items(held))))


def t89tone():
    spec, arrays, rep = learn([C1])
    its = items(T89C2)
    base = read_set(spec, arrays, its)
    changed = {}
    for tk in TONES[1:]:
        res = read_set(spec, arrays, its, tk)
        changed["+".join(map(str, tk))] = sum(1 for a, b in zip(base, res) if (a[2], a[3]) != (b[2], b[3]))
    out(step="9 tone grid on T89C2 held out (C1 alone)", pictures=len(its), untouched=sum_v3(base),
        readings_changed=changed, total_changed=sum(changed.values()))


# --- replay ---------------------------------------------------------------------------------------------------------
def load_stretches(run, labels):
    """Each load's stretch: from an `ignore` range's start (the labels: the first seconds after a load) to the next."""
    starts = [float(r["from"]) for r in labels["runs"][run] if r["label"] == E.IGNORE]
    return [(a, b) for a, b in zip(starts, starts[1:] + [1e9])]


def per_load(run, spec, arrays, labels, k=None):
    rows = E._index(FR / run)
    res = []
    rng = sorted(labels["runs"][run], key=lambda r: float(r["from"]))
    for lo, hi in load_stretches(run, labels):
        now = [0.0]
        reader = E.Reader(spec, arrays, clock=lambda: now[0])
        ended = E.Ended(spec, k)
        ended.start_loaded()
        first_label = next((r["label"] for r in rng if float(r["from"]) > lo and r["label"] != E.IGNORE), None)
        first_lab_t = next((float(r["from"]) for r in rng if float(r["from"]) > lo and r["label"] != E.IGNORE), None)
        first_start, said, classes = None, None, {}
        for t, f in rows:
            if not (lo - 1e-6 <= t < hi - 1e-6):
                continue
            now[0] = t
            with Image.open(FR / run / f) as im:
                r = reader.read(im.convert("L"), now=t)
            classes[r["class"]] = classes.get(r["class"], 0) + 1
            if first_start is None and r["class"] == spec["start_class"]:
                first_start = t
            if said is None and ended.feed(r["class"], r.get("places")):
                said = {"seconds": t, "class": ended.ended, "places": ended.places}
        res.append({"load_at_s": lo, "labelled": first_label, "first_labelled_s": first_lab_t,
                    "first_start_read_after_load_s": round(first_start - lo, 2) if first_start is not None else None,
                    "ended": said, "after_first_labelled_s": (round(said["seconds"] - first_lab_t, 2)
                                                              if said and first_lab_t is not None else None),
                    "reads": classes})
    return res


def short_replay(rp):
    return {"ended": rp["ended"], "changes": rp["changes"], "arrivals": rp["end_screen_arrivals_s"],
            "pictures": rp["pictures"], "k": rp["k"]}


def replay():
    s88_old, a88_old, _ = learn([V1, LIVE])
    s88, a88, _ = learn([V1, LIVE, C2])
    s89_old, a89_old, _ = learn([C1])
    s89, a89, _ = learn([C1, T89C2])
    for k in (3, 2):
        out(step="10 replay C2 (T88), the three-source spec", k=k,
            tool=short_replay(E.replay(FR / C2_88, s88, a88, k, C2[1])), per_load=per_load(C2_88, s88, a88, C2[1], k))
        out(step="10 replay T89C2, the C1 + T89C2 spec", k=k,
            tool=short_replay(E.replay(FR / C2_89, s89, a89, k, T89C2[1])),
            per_load=per_load(C2_89, s89, a89, T89C2[1], k))
    out(step="10 replay C2 (T88), H7-V3's spec (for comparison)", k=3,
        tool=short_replay(E.replay(FR / C2_88, s88_old, a88_old, 3, C2[1])),
        per_load=per_load(C2_88, s88_old, a88_old, C2[1], 3))
    out(step="10 replay T89C2, B122's spec (for comparison)", k=3,
        tool=short_replay(E.replay(FR / C2_89, s89_old, a89_old, 3, T89C2[1])),
        per_load=per_load(C2_89, s89_old, a89_old, T89C2[1], 3))
    for k in (3, 2):
        old = E.replay(FR / LIVE_RUN, s88_old, a88_old, k, LIVE[1])
        new = E.replay(FR / LIVE_RUN, s88, a88, k, LIVE[1])
        out(step="11 LIVE replay: H7-V3's spec vs the three-source spec", k=k, old_ended=old["ended"],
            new_ended=new["ended"], ended_same=old["ended"] == new["ended"],
            changes_same=old["changes"] == new["changes"],
            reads_differing=[[a[0], a[1], b[1]] for a, b in zip(old["reads"], new["reads"]) if a[1] != b[1]])
        old = E.replay(FR / C1_89, s89_old, a89_old, k, C1[1])
        new = E.replay(FR / C1_89, s89, a89, k, C1[1])
        out(step="11 C1 replay: B122's spec vs the C1 + T89C2 spec", k=k, old_ended=old["ended"],
            new_ended=new["ended"], ended_same=old["ended"] == new["ended"],
            changes_same=old["changes"] == new["changes"],
            reads_differing=[[a[0], a[1], b[1]] for a, b in zip(old["reads"], new["reads"]) if a[1] != b[1]])


# --- amendment 1 (03:16:21Z): C2's pictures 4-7 (RetroArch's notices) as ignore, in memory only ----------------------
def c2_notices_ignored():
    lb = json.loads(json.dumps(C2[1]))
    rs = []
    for r in lb["runs"][C2_88]:
        if r["label"] == E.START and float(r["from"]) < 4.0:     # pictures 4-7 = seconds 3.02-6.02
            rs.append({"from": r["from"], "to": 6.02, "label": E.IGNORE})
            rs.append({"from": 7.02, "to": r["to"], "label": E.START})
        else:
            rs.append(r)
    lb["runs"][C2_88] = rs
    return (FR, lb)


def a1():
    C2p = c2_notices_ignored()
    SRC88["C2'"] = C2p
    sp, ar, rp = learn([V1, C2])
    starts = [(p, c) for p, c in items(C2) if c == E.START and int(Path(p).stem[1:]) <= 8]
    out(step="A1.2 V1 + C2: C2's first start pictures", reads=[r[:9] for r in read_set(sp, ar, starts)],
        screen=rp["screen"], start=rp["classes"]["start"])
    for held, train in (("LIVE", ("V1", "C2'")), ("V1", ("LIVE", "C2'"))):
        sp, ar, rp = learn([SRC88[t] for t in train])
        out(step="A1.1 fold (C2's notices ignored)", learnt_from=list(train), held_out=held, report=rep_v2(rp),
            score=sum_v2(read_set(sp, ar, items(SRC88[held]))))
    sp, ar, rp = learn([V1, LIVE, C2p])
    out(step="A1.1 learnt from V1 + LIVE + C2' (C2's notices ignored)", report=rep_v2(rp))
    for nm in ("V1", "LIVE", "C2'", "C2"):
        out(step="A1.1 V1 + LIVE + C2' scored", on=nm, score=sum_v2(read_set(sp, ar, items(SRC88[nm]))))
    sp, ar, rp = learn([V1, LIVE, C2p], "first")
    its = items(C2p, "second")
    base = read_set(sp, ar, its)
    changed, misread = {}, 0
    for tk in TONES[1:]:
        res = read_set(sp, ar, its, tk)
        changed["+".join(map(str, tk))] = sum(1 for a, b in zip(base, res) if a[2] != b[2])
        misread += sum(1 for b in res if b[2] not in (b[1], E.UNKNOWN, E.OTHER))
    out(step="A1.1 tone grid: V1 + LIVE + C2' first halves -> C2' second halves", pictures=len(its),
        untouched=sum_v2(base), readings_changed=changed, total_changed=sum(changed.values()), misread_total=misread)


# --- amendment 2 (see design_amendment_2_hashed_at.txt): the tone grid on C2 under the three-source spec (not held out)
def a2():
    sp, ar, rp = learn([V1, LIVE, C2])
    its = items(C2)
    base = read_set(sp, ar, its)
    changed, misread, other_screen = {}, 0, 0
    for tk in TONES[1:]:
        res = read_set(sp, ar, its, tk)
        changed["+".join(map(str, tk))] = sum(1 for a, b in zip(base, res) if a[2] != b[2])
        misread += sum(1 for b in res if b[2] not in (b[1], E.UNKNOWN, E.OTHER))
        other_screen += sum(1 for b in res if b[1] == E.OTHER and b[5])
    out(step="A2 tone grid: V1 + LIVE + C2 -> all C2 (not held out)", pictures=len(its), untouched=sum_v2(base),
        readings_changed=changed, total_changed=sum(changed.values()), misread_total=misread,
        other_as_screen_total=other_screen)


if __name__ == "__main__":
    os.nice(10)
    t0 = time.perf_counter()
    parts = {"t88": t88, "t88tone": t88tone, "t89": t89, "t89tone": t89tone, "replay": replay, "a1": a1, "a2": a2}
    for p in (parts if PART == "all" else [PART]):
        parts[p]()
    out(done=PART, seconds=round(time.perf_counter() - t0, 1))
