#!/usr/bin/env python3
"""B102 (H7): the end-screen learner — from labelled pictures alone, which part of a game's screen marks where a mini
game starts / ends and which part tells the outcomes apart; then read a picture back.

No hand-drawn boxes: everything comes from the labelled frames (the same has to work for dozens of games).

  learn  — a folder of runs (`<run>/index.csv` with `seconds,file,…`, the frames beside it) and a labels file
           (`{"classes": {name: text}, "runs": {run: [{"from", "to", "label"}]}}`; `ignore` left out; `other` = not the
           screen; `start` = the start class; every other class an end class). Every frame reduced to a 160 × 120
           grey picture. The screen mask: the pixels steady across the screen classes' frames taken together; the
           outcome mask: the pixels steady within each screen class and different between them; each class's
           reference: its mean over the outcome mask. The thresholds halfway across the gaps the labelled frames leave.
           Output: a spec (`<name>.endscreen.json`, small) + its arrays (`<name>.endscreen.npz`, beside it) + a report.
  read   — screen? (the median distance over the screen mask under its threshold) → which class (the nearest
           reference over the outcome mask, under its threshold, with a margin to the second) → else `unknown`;
           not the screen → `other`. A small alignment search (shift / scale) when a picture does not read as the
           screen; the `Reader` keeps the alignment it found.
  Ended  — K agreeing reads in a row (K = 3, at one read a second), an end class only after the start was seen.
  score  — the confusion counts, and the number of `other` frames read as the screen (must be 0).

PIL + numpy only (both on the hub as Debian packages). Nothing is written beside the frames.

usage: h7_endscreen.py learn <runs> <labels> <out.endscreen.json> [--half first]
       h7_endscreen.py score <runs> <labels> <spec.endscreen.json> [--half second]
       h7_endscreen.py read  <spec.endscreen.json> <picture>
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

VERSION = 1
SIZE = (160, 120)               # the reduced picture: 19,200 grey values
MID = (320, 240)                # the step the alignment search moves
STEADY = 6.0                    # grey levels: a pixel's deviation under this is steady
DIFFER = 32.0                   # grey levels: two classes' means further apart than this differ
SAFETY = 0.5                    # thresholds sit this far across a gap (halfway)
ASPECT_TOLERANCE = 0.02         # a picture whose aspect differs more than this has bars to take off
K = 3                           # agreeing reads in a row to end (one read a second)
SEARCH_EVERY = 10.0             # s: at most one alignment search per this, when the screen is not seen
COARSE_SCALES = (0.95, 0.975, 1.0, 1.025, 1.05)
COARSE_SHIFTS = (-4, -2, 0, 2, 4)                # px of the 320 × 240 step (±8 px of a 640-wide picture)
FINE_SCALE, FINE_SHIFT = 0.0125, 1
START, OTHER, IGNORE, UNKNOWN = "start", "other", "ignore", "unknown"
IDENTITY = (1.0, 0.0, 0.0)


# --- the picture --------------------------------------------------------------------------------------------------
def _cut_bars(img: Image.Image, aspect: float | None) -> Image.Image:
    """The centre at the spec's aspect, when the picture's aspect differs by more than 2 % (a window's bars)."""
    if not aspect:
        return img
    w, h = img.size
    have = w / h
    if have > aspect * (1 + ASPECT_TOLERANCE):
        nw = max(1, round(h * aspect))
        x0 = (w - nw) // 2
        return img.crop((x0, 0, x0 + nw, h))
    if have < aspect / (1 + ASPECT_TOLERANCE):
        nh = max(1, round(w / aspect))
        y0 = (h - nh) // 2
        return img.crop((0, y0, w, y0 + nh))
    return img


def mid(img: Image.Image, aspect: float | None = None) -> Image.Image:
    """Grey, bars off, 320 × 240 (BILINEAR filters when shrinking)."""
    return _cut_bars(img.convert("L"), aspect).resize(MID, Image.BILINEAR)


def _final(im_mid: Image.Image) -> np.ndarray:
    return np.asarray(im_mid.resize(SIZE, Image.BOX), dtype=np.float32)


def _moved(im_mid: Image.Image, align) -> Image.Image:
    s, dx, dy = align
    if (s, dx, dy) == IDENTITY:
        return im_mid
    w, h = im_mid.size
    cx, cy = w / 2.0, h / 2.0
    return im_mid.transform(im_mid.size, Image.AFFINE, (1 / s, 0, cx - (cx + dx) / s, 0, 1 / s, cy - (cy + dy) / s),
                            resample=Image.BILINEAR, fillcolor=0)


def reduce(img: Image.Image, aspect: float | None = None, align=IDENTITY) -> np.ndarray:
    """The reduced picture: 160 × 120 grey values (float32, 0-255)."""
    return _final(_moved(mid(img, aspect), align))


# --- the labelled runs --------------------------------------------------------------------------------------------
def load_labels(path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("runs"), dict):
        raise ValueError("the labels file has no runs")
    classes = data.get("classes")
    if not isinstance(classes, dict) or not classes:
        raise ValueError("the labels file names no classes")
    return data


def labelled_frames(runs_folder, labels: dict, half: str | None = None) -> dict[str, list[Path]]:
    """{class: [frame paths]} — `ignore` left out; half "first" / "second": that half of each range (by count)."""
    runs_folder = Path(runs_folder)
    classes = set(labels["classes"])
    out: dict[str, list[Path]] = {c: [] for c in classes if c != IGNORE}
    for run, ranges in labels["runs"].items():
        index = runs_folder / run / "index.csv"
        if not index.is_file():
            raise ValueError(f"the labels name a run with no frames: {run}")
        with index.open(newline="", encoding="utf-8") as fh:
            rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader(fh)]
        for r in ranges:
            label = r.get("label")
            if label not in classes:
                raise ValueError(f"a range's label is not one of the classes: {label}")
            if label == IGNORE:
                continue
            lo, hi = float(r["from"]) - 1e-6, float(r["to"]) + 1e-6
            sel = [runs_folder / run / f for t, f in rows if lo <= t <= hi]
            if half in ("first", "second") and sel:
                cut = max(1, len(sel) // 2)
                sel = sel[:cut] if half == "first" else sel[cut:]
            out[label].extend(sel)
    return out


# --- learn --------------------------------------------------------------------------------------------------------
def _median_dist(a: np.ndarray, mask: np.ndarray, ref: np.ndarray) -> float:
    return float(np.median(np.abs(a[mask] - ref)))


def _class_dists(a: np.ndarray, outcome: np.ndarray, refs: np.ndarray) -> np.ndarray:
    if refs.shape[1] == 0:
        return np.full(refs.shape[0], np.inf, dtype=np.float32)
    return np.abs(a[outcome][None, :] - refs).mean(axis=1)


def _gap(own: float, foreign: float) -> dict:
    gap = foreign - own
    return {"worst_own": round(own, 3), "best_foreign": round(foreign, 3), "gap": round(gap, 3),
            "threshold": round(own + SAFETY * gap, 3) if gap > 0 else None,
            "verdict": "separable" if gap > 0 else "not separable from these frames"}


def learn_arrays(frames: dict[str, list[np.ndarray]], aspect: float, start_class: str = START,
                 name: str = "") -> tuple[dict, dict, dict]:
    """From reduced frames {class: [160 × 120 arrays]} → (spec, arrays, report)."""
    for c, fs in frames.items():
        if not fs:
            raise ValueError(f"the labels name a class with no frames: {c}")
    if OTHER not in frames:
        raise ValueError("the labels name no other frames: the screen's threshold cannot be learnt")
    screens = [c for c in frames if c != OTHER]
    if start_class not in screens:
        raise ValueError(f"the start class has no frames: {start_class}")
    if len(screens) < 2:
        raise ValueError("at least two screen classes are needed (a start and an end)")
    screens = [start_class] + sorted(c for c in screens if c != start_class)
    stacks = {c: np.stack(frames[c]).astype(np.float32) for c in frames}
    union = np.concatenate([stacks[c] for c in screens])
    screen_mask = union.std(axis=0) < STEADY
    screen_ref = union.mean(axis=0)
    within = np.stack([stacks[c].std(axis=0) for c in screens]).max(axis=0) < STEADY
    means = {c: stacks[c].mean(axis=0) for c in screens}
    apart = np.zeros(union.shape[1:], dtype=np.float32)
    for i, a in enumerate(screens):
        for b in screens[i + 1:]:
            apart = np.maximum(apart, np.abs(means[a] - means[b]))
    outcome_mask = within & (apart > DIFFER)
    refs = np.stack([means[c][outcome_mask] for c in screens]).astype(np.float32)
    sref = screen_ref[screen_mask]

    def sd(a):
        return float(np.median(np.abs(a[screen_mask] - sref))) if screen_mask.any() else float("inf")

    own_screen = max(sd(a) for c in screens for a in stacks[c])
    foreign_screen = min(sd(a) for a in stacks[OTHER])
    screen = _gap(own_screen, foreign_screen)
    per_class, margins = {}, []
    for i, c in enumerate(screens):
        own = [float(_class_dists(a, outcome_mask, refs)[i]) for a in stacks[c]]
        foreign = [float(_class_dists(a, outcome_mask, refs)[i]) for d in screens if d != c for a in stacks[d]]
        per_class[c] = _gap(max(own), min(foreign))
        for a in stacks[c]:
            dd = _class_dists(a, outcome_mask, refs)
            if int(np.argmin(dd)) == i and len(dd) > 1:
                margins.append(float(np.sort(dd)[1] - dd[i]))
    margin_needed = round(SAFETY * min(margins), 3) if margins and outcome_mask.any() else None
    if not outcome_mask.any():
        for c in screens:
            per_class[c].update(threshold=None, verdict="not separable from these frames")
    ys, xs = np.nonzero(outcome_mask)
    total = SIZE[0] * SIZE[1]
    spec = {
        "version": VERSION, "kind": "privyhub-h7-endscreen", "size": list(SIZE), "aspect": round(float(aspect), 5),
        "classes": screens, "start_class": start_class, "end_classes": screens[1:],
        "screen_threshold": screen["threshold"], "class_thresholds": {c: per_class[c]["threshold"] for c in screens},
        "separable": {c: per_class[c]["verdict"] == "separable" for c in screens},
        "margin_needed": margin_needed, "usable": screen["threshold"] is not None,
        "steady": STEADY, "differ": DIFFER, "safety": SAFETY, "k": K, "search_every_s": SEARCH_EVERY,
        "search": {"coarse_scales": list(COARSE_SCALES), "coarse_shifts_px_320": list(COARSE_SHIFTS),
                   "fine_scale": FINE_SCALE, "fine_shift_px_320": FINE_SHIFT},
        "screen_mask_px": int(screen_mask.sum()), "outcome_mask_px": int(outcome_mask.sum()),
        "frames": {c: len(frames[c]) for c in [*screens, OTHER]},
        "arrays": f"{name}.endscreen.npz" if name else None, "arrays_sha256": None,
    }
    arrays = {"screen_mask": screen_mask, "screen_ref": screen_ref.astype(np.float32),
              "outcome_mask": outcome_mask, "refs": refs}
    report = {
        "frames_per_class": spec["frames"],
        "screen_mask": {"px": int(screen_mask.sum()), "share": round(float(screen_mask.sum()) / total, 4)},
        "outcome_mask": {"px": int(outcome_mask.sum()), "share": round(float(outcome_mask.sum()) / total, 4),
                         "bbox_160x120": ([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                                          if len(xs) else None)},
        "screen": screen, "classes": per_class, "margin_needed": margin_needed,
        "smallest_margin_seen": round(min(margins), 3) if margins else None, "usable": spec["usable"],
    }
    return spec, arrays, report


def _aspect_of(paths: list[Path]) -> float:
    sizes = []
    for p in paths[:: max(1, len(paths) // 20)]:
        with Image.open(p) as im:
            sizes.append(im.size[0] / im.size[1])
    return float(np.median(sizes))


def learn(runs_folder, labels_path, half: str | None = None, start_class: str = START, name: str = ""):
    t0 = time.perf_counter()
    labels = load_labels(labels_path)
    paths = labelled_frames(runs_folder, labels, "first" if half == "first" else None)
    for c, ps in paths.items():
        if not ps:
            raise ValueError(f"the labels name a class with no frames: {c}")
    aspect = _aspect_of([p for ps in paths.values() for p in ps])
    frames = {c: [reduce(Image.open(p), aspect) for p in ps] for c, ps in paths.items()}
    spec, arrays, report = learn_arrays(frames, aspect, start_class, name)
    report["learn_s"] = round(time.perf_counter() - t0, 2)
    return spec, arrays, report


# --- the spec on disk ---------------------------------------------------------------------------------------------
def _npz_bytes(arrays: dict) -> bytes:
    buf = io.BytesIO()
    np.savez_compressed(buf, **arrays)
    return buf.getvalue()


def save_spec(spec: dict, arrays: dict, json_path) -> Path:
    """`<name>.endscreen.json` + `<name>.endscreen.npz` beside it (the JSON names it and carries its sha256)."""
    json_path = Path(json_path)
    if not json_path.name.endswith(".endscreen.json"):
        raise ValueError("a spec's file name ends in .endscreen.json")
    npz = json_path.with_name(json_path.name[: -len(".json")] + ".npz")
    data = _npz_bytes(arrays)
    npz.write_bytes(data)
    out = dict(spec, arrays=npz.name, arrays_sha256=hashlib.sha256(data).hexdigest())
    json_path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return json_path


def load_spec(json_path) -> tuple[dict, dict]:
    json_path = Path(json_path)
    spec = json.loads(json_path.read_text(encoding="utf-8"))
    if spec.get("kind") != "privyhub-h7-endscreen" or spec.get("version") != VERSION:
        raise ValueError("not an end-screen spec this tool reads")
    name = str(spec.get("arrays") or "")
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise ValueError("the spec names no arrays file")
    data = (json_path.parent / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != spec.get("arrays_sha256"):
        raise ValueError("the spec's arrays file does not match the spec")
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        arrays = {k: z[k] for k in ("screen_mask", "screen_ref", "outcome_mask", "refs")}
    if arrays["screen_mask"].shape != (SIZE[1], SIZE[0]) or arrays["refs"].shape[0] != len(spec["classes"]):
        raise ValueError("the spec's arrays do not fit the spec")
    return spec, arrays


# --- read ---------------------------------------------------------------------------------------------------------
class Reader:
    """Reads pictures against one spec; keeps the alignment a search found (the window does not move in a game)."""

    def __init__(self, spec: dict, arrays: dict, clock=time.monotonic):
        self.spec, self.clock = spec, clock
        self.screen_mask = arrays["screen_mask"].astype(bool)
        self.sref = arrays["screen_ref"][self.screen_mask].astype(np.float32)
        self.outcome = arrays["outcome_mask"].astype(bool)
        self.refs = arrays["refs"].astype(np.float32)
        self.classes = list(spec["classes"])
        self.align = IDENTITY
        self.last_search: float | None = None

    def _sd(self, a: np.ndarray) -> float:
        if not self.screen_mask.any():
            return float("inf")
        return float(np.median(np.abs(a[self.screen_mask] - self.sref)))

    def _search(self, im_mid: Image.Image) -> tuple[float, tuple]:
        best = (float("inf"), IDENTITY)
        for s in COARSE_SCALES:
            for dx in COARSE_SHIFTS:
                for dy in COARSE_SHIFTS:
                    d = self._sd(_final(_moved(im_mid, (s, float(dx), float(dy)))))
                    if d < best[0]:
                        best = (d, (s, float(dx), float(dy)))
        s0, x0, y0 = best[1]
        for s in (s0 - FINE_SCALE, s0, s0 + FINE_SCALE):
            for dx in (x0 - FINE_SHIFT, x0, x0 + FINE_SHIFT):
                for dy in (y0 - FINE_SHIFT, y0, y0 + FINE_SHIFT):
                    al = (round(s, 4), float(dx), float(dy))
                    d = self._sd(_final(_moved(im_mid, al)))
                    if d < best[0]:
                        best = (d, al)
        return best

    def _classify(self, a: np.ndarray) -> tuple[str, dict, float]:
        spec = self.spec
        dd = _class_dists(a, self.outcome, self.refs)
        order = np.argsort(dd)
        best = int(order[0])
        margin = float(dd[order[1]] - dd[best]) if len(dd) > 1 else float("inf")
        c = self.classes[best]
        cthr = spec["class_thresholds"].get(c)
        need = spec.get("margin_needed")
        ok = (spec["separable"].get(c) and cthr is not None and dd[best] <= cthr
              and need is not None and margin >= need)
        return (c if ok else UNKNOWN), {c2: round(float(dd[i]), 3) for i, c2 in enumerate(self.classes)}, margin

    def read(self, img: Image.Image, now: float | None = None, search: bool = True) -> dict:
        spec = self.spec
        thr = spec.get("screen_threshold")
        im_mid = mid(img, spec.get("aspect"))
        a = _final(_moved(im_mid, self.align))
        sd = self._sd(a)
        screen = thr is not None and sd <= thr
        cls = self._classify(a)[0] if screen else OTHER
        searched = False
        if thr is not None and search and (not screen or cls == UNKNOWN):     # amendment 1: unknown searches too
            now = self.clock() if now is None else now
            if self.last_search is None or now - self.last_search >= SEARCH_EVERY:
                self.last_search, searched = now, True
                d, al = self._search(im_mid)
                if d <= thr and d < sd:
                    self.align, sd = al, d
                    a = _final(_moved(im_mid, al))
        out = {"screen": bool(thr is not None and sd <= thr), "class": OTHER,
               "distances": {"screen": round(sd, 3)}, "margin": None,
               "align": [round(self.align[0], 4), self.align[1], self.align[2]], "searched": searched}
        if not out["screen"]:
            return out
        cls, dists, margin = self._classify(a)
        out["distances"].update(dists)
        out["margin"] = round(margin, 3)
        out["class"] = cls
        return out


def read(spec: dict, arrays: dict, img: Image.Image) -> dict:
    """One picture, read by a fresh Reader (a non-screen picture gets the full search)."""
    return Reader(spec, arrays).read(img)


class Ended:
    """K agreeing reads in a row; an end class counts only after the start was seen (K start reads, or a load)."""

    def __init__(self, spec: dict, k: int | None = None):
        self.start = spec["start_class"]
        self.ends = set(spec["end_classes"])
        self.k = int(k or spec.get("k") or K)
        self.seen_start = False
        self.run_class, self.run = None, 0
        self.ended: str | None = None

    def start_loaded(self) -> None:
        self.seen_start = True

    def feed(self, cls: str) -> str | None:
        """One read's class → the end class once ended, else None."""
        if self.ended:
            return self.ended
        if cls == self.run_class:
            self.run += 1
        else:
            self.run_class, self.run = cls, 1
        if self.run >= self.k:
            if cls == self.start:
                self.seen_start = True
            elif cls in self.ends and self.seen_start:
                self.ended = cls
        return self.ended


# --- score --------------------------------------------------------------------------------------------------------
def score(runs_folder, labels_path, spec: dict, arrays: dict, half: str | None = None, transform=None,
          search: bool = True) -> dict:
    """The confusion counts per labelled class and `other_read_as_screen` (must be 0). `transform(img) → img`
    (optional) moves every picture first (the alignment check). Each picture read by a fresh Reader."""
    labels = load_labels(labels_path)
    paths = labelled_frames(runs_folder, labels, "second" if half == "second" else None)
    cols = [*spec["classes"], UNKNOWN, OTHER]
    confusion = {c: dict.fromkeys(cols, 0) for c in paths}
    worst_own: dict[str, float] = {}
    least_margin: dict[str, float] = {}
    times, other_screen = [], 0
    for c, ps in paths.items():
        for p in ps:
            with Image.open(p) as im:
                img = im.convert("L")
            if transform is not None:
                img = transform(img)
            t0 = time.perf_counter()
            r = Reader(spec, arrays).read(img, search=search)
            times.append((time.perf_counter() - t0) * 1000.0)
            confusion[c][r["class"]] += 1
            if c == OTHER and r["screen"]:
                other_screen += 1
            if r["class"] == c and c != OTHER:
                worst_own[c] = max(worst_own.get(c, 0.0), r["distances"][c])
                least_margin[c] = min(least_margin.get(c, float("inf")), r["margin"])
    return {"confusion": confusion,
            "right": {c: [confusion[c][c], sum(confusion[c].values())] for c in confusion},
            "other_read_as_screen": other_screen,
            "worst_own_distance": {c: round(v, 3) for c, v in worst_own.items()},
            "least_margin": {c: round(v, 3) for c, v in least_margin.items()},
            "read_ms": {"median": round(float(np.median(times)), 2), "worst": round(float(max(times)), 2),
                        "n": len(times)} if times else None}


# --- CLI ----------------------------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if len(argv) >= 4 and argv[0] == "learn":
        half = argv[5] if len(argv) >= 6 and argv[4] == "--half" else None
        out = Path(argv[3])
        name = out.name[: -len(".endscreen.json")] if out.name.endswith(".endscreen.json") else ""
        spec, arrays, report = learn(argv[1], argv[2], half, name=name)
        save_spec(spec, arrays, out)
        print(json.dumps(report, indent=1, sort_keys=True))
        return 0
    if len(argv) >= 4 and argv[0] == "score":
        half = argv[5] if len(argv) >= 6 and argv[4] == "--half" else None
        spec, arrays = load_spec(argv[3])
        print(json.dumps(score(argv[1], argv[2], spec, arrays, half), indent=1, sort_keys=True))
        return 0
    if len(argv) == 3 and argv[0] == "read":
        spec, arrays = load_spec(argv[1])
        with Image.open(argv[2]) as im:
            print(json.dumps(read(spec, arrays, im.convert("L")), sort_keys=True))
        return 0
    print(__doc__.split("usage:")[1].strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
