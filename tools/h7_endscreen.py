#!/usr/bin/env python3
"""B102 (H7): the end-screen learner — from labelled pictures alone, which part of a game's screen marks where a mini
game starts / ends and which part tells the outcomes apart; then read a picture back.
B104: the read made independent of tone (spec version 2) — a gain, an offset or a mild curve on the whole picture
changes no reading; the game's picture found inside a larger window by this tool; screenshots and window pictures of
different sizes learnt from together; `replay`.

No hand-drawn boxes: everything comes from the labelled frames (the same has to work for dozens of games).

  the picture — grey; **the game's area**: a window's black bars (whole edge columns / rows whose brightest pixel is
           <= the picture's darkest + 16) cut on one axis only, the smaller side's count, when it is >= 5 % of that
           side; then 320 x 240
           (BILINEAR) -> 160 x 120 (BOX): 19,200 grey values.
  the measure — **ranks against the picture's own screen-mask tone**: each pixel's value replaced by the share of the
           screen mask's pixels darker than it (by more than tau), plus half the share within +/- tau of it; tau = 2 %
           of the picture's own contrast (its 2nd-98th percentile spread over the mask). A gain, an offset or a
           monotone curve leaves the ranks as they are. A flat picture (spread < 8 levels) has no tone: distance 1.0.
  learn  — a folder of runs (`<run>/index.csv` with `seconds,file,...`, the frames beside it) and a labels file
           (`{"classes": {name: text}, "runs": {run: [{"from", "to", "label"}]}}`; `ignore` left out; `other` = not the
           screen; `start` = the start class; every other class an end class); one source or several. The screen
           mask: the pixels whose rank is steady across the screen classes' frames taken together; the outcome mask:
           steady within each screen class and apart between them; each class's reference: its mean ranks over the
           outcome mask. The thresholds halfway across the gaps the labelled frames leave.
           Output: a spec (`<name>.endscreen.json`, small) + its arrays (`<name>.endscreen.npz`, beside it) + a report.
  read   — screen? (the median rank distance over the screen mask under its threshold) -> which class (the nearest
           reference over the outcome mask, under its threshold, with a margin to the second) -> else `unknown`;
           not the screen -> `other`. A small alignment search (shift / scale) when a picture does not read as the
           screen; the `Reader` keeps the alignment it found.
  Ended  — K agreeing reads in a row (K = 3, at one read a second), an end class only after the start was seen.
  score  — the confusion counts, and the number of `other` frames read as the screen (must be 0).
  replay — a run's pictures in order through one Reader and Ended (re-armed after each end): the classes, the
           changes, when `ended` would be said (against the labels, when there are any).

A version-1 spec (absolute grey levels) is refused: learn it again. PIL + numpy only (both on the hub as Debian
packages). Nothing is written beside the frames.

B122 — a place for every player (spec version 3, only when every end class is a place row `end_r<d1..dn>`: the Place
row read left to right, port 1 first, a permutation of 1..n; any other labels learn version 2 exactly as before):
  the screen — today's learner on `start`, one end class `end` (every place row merged) and `other`.
  the row   — learnt from the labels alone: on the end pictures' ranks at 320 x 240 (against the screen mask), the
           matches' mean pictures; for every spacing and cell size, the per-pixel ratio of between-place to
           within-place variance (each place's values from whichever columns showed it), box-averaged -> the row's
           spacing, origin and cell; the glyph mask (ratio > 1 in the padded cell); each column's cell refined +/-3 px.
  a place   — one reference per place pooled over every column that showed it: a place never shown in a column is
           read there with the reference learnt in the others, at that column's own learnt position (+/-1 px). A
           place shown in no column cannot be learnt (refused: the pictures need it).
  a read    — the screen and its class as before; for `end` every column's place (the nearest reference by the mean
           rank distance over the glyph mask, under its threshold, with the margin); any column unread or two columns the same place -> `unknown`, `places` null.
  Ended     — K agreeing reads of the whole row (the class and the places).

usage: h7_endscreen.py learn <runs> <labels> [<runs> <labels> ...] <out.endscreen.json> [--half first]
       h7_endscreen.py score <runs> <labels> [<runs> <labels> ...] <spec.endscreen.json> [--half second]
       h7_endscreen.py read  <spec.endscreen.json> <picture>
       h7_endscreen.py replay <run folder> <spec.endscreen.json> [--k K] [--labels <labels>]
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

VERSION = 2                     # B104: ranks against the picture's own screen-mask tone (version 1: grey levels)
MEASURE = "rank-against-screen-mask"
OLD_MEASURE = "this end-screen spec was learnt with the old measure (absolute grey levels): learn it again"
SIZE = (160, 120)               # the reduced picture: 19,200 grey values
MID = (320, 240)                # the step the alignment search moves
STEADY_R = 0.05                 # ranks: a pixel's deviation under this is steady
DIFFER_R = 0.25                 # ranks: two classes' means further apart than this differ
SEP = 3.0                       # amendment 3: the difference must exceed this x the pixel's widest within-class spread
MIN_GAP = 0.05                  # amendment 3: a class's gap under this is the sources' noise: not separable
SAFETY = 0.5                    # thresholds sit this far across a gap (halfway)
BAR_MAX = 16                    # grey above the picture's darkest: an edge column / row no brighter is a window's bar
BAR_SHARE = 0.05                # bars are cut only when they are at least this share of their side
QUANT = 4                       # steps per grey level (a quarter level): 1,024 histogram steps
BINS = 256 * QUANT
TOL = 0.02                      # tau: values within this share of the picture's own contrast count as equal
FLAT = 8.0                      # grey: a picture whose 2nd-98th percentile spread over the mask is under this is flat
K = 3                           # agreeing reads in a row to end (one read a second)
SEARCH_EVERY = 10.0             # s: at most one alignment search per this, when the screen is not seen
COARSE_SCALES = (0.95, 0.975, 1.0, 1.025, 1.05)
COARSE_SHIFTS = (-4, -2, 0, 2, 4)                # px of the 320 × 240 step (±8 px of a 640-wide picture)
FINE_SCALE, FINE_SHIFT = 0.0125, 1
START, OTHER, IGNORE, UNKNOWN = "start", "other", "ignore", "unknown"
IDENTITY = (1.0, 0.0, 0.0)
# B122: places (spec version 3)
VERSION_PLACES = 3
END = "end"                                       # a version-3 spec's one end class
PLACE_LABEL = re.compile(r"^end_r([1-9]+)$")      # a place row: end_r1234 = port 1 is 1st, port 2 2nd, ...
PLACE_CELLS = ((12, 8), (16, 12), (20, 16), (24, 20))   # cell sizes tried (rows x columns of the 320 x 240 picture)
PLACE_MIN_SPACING = 8                             # px of 320
PLACE_PAD = 4                                     # the cell padded by this on every side
PLACE_FISHER = 1.0                                # a glyph pixel: between-place / within-place variance above this
PLACE_REFINE = 3                                  # each column's cell refined within +/- this many px
PLACE_SEARCH = 1                                  # a read's cell searched within +/- this many px


# --- the picture --------------------------------------------------------------------------------------------------
def _lead(flags: np.ndarray) -> int:
    """How many leading entries are True."""
    if flags.all():
        return int(len(flags))
    return int(np.argmin(flags))


def game_area(img: Image.Image) -> Image.Image:
    """B104: the game's picture inside a window — the window's black bars cut, one way for every caller.

    Per side, the whole edge columns (left / right) or rows (top / bottom) whose brightest pixel is at most the
    picture's darkest + BAR_MAX (amendment 4: relative, so a tone change of the whole window does not hide them); per
    axis the smaller of its two sides (bars are symmetric; a game's own dark edge on one side is not a bar); only the
    axis with the larger share is cut, and only when that share is >= BAR_SHARE and leaves at least half. Else the
    picture as it is (a screenshot; a game's own dark border of a few per cent)."""
    a = np.asarray(img)
    if a.ndim != 2:
        a = np.asarray(img.convert("L"))
    h, w = a.shape
    floor = int(a.min()) + BAR_MAX
    cols = a.max(axis=0) <= floor
    rows = a.max(axis=1) <= floor
    bx = min(_lead(cols), _lead(cols[::-1]))
    by = min(_lead(rows), _lead(rows[::-1]))
    sx, sy = bx / w, by / h
    if sx >= sy and sx >= BAR_SHARE and w - 2 * bx >= w / 2:
        return img.crop((bx, 0, w - bx, h))
    if sy > sx and sy >= BAR_SHARE and h - 2 * by >= h / 2:
        return img.crop((0, by, w, h - by))
    return img


def mid(img: Image.Image, aspect: float | None = None) -> Image.Image:
    """Grey, the game's area (bars off), 320 x 240 (BILINEAR filters when shrinking). `aspect`: unused since B104."""
    return game_area(img.convert("L")).resize(MID, Image.BILINEAR)


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
    """The reduced picture: 160 x 120 grey values (float32, 0-255)."""
    return _final(_moved(mid(img), align))


# --- the measure: ranks against the picture's own screen-mask tone (B104) ------------------------------------------
def ranks(a: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, bool]:
    """Every pixel's rank in the picture's own values over `mask`: the share darker than v - tau plus half the share
    within +/- tau (tau = TOL x the 2nd-98th percentile spread over the mask, at least one quarter level).
    -> (ranks 0-1 for every pixel, flat). A flat picture (spread < FLAT) has no tone to rank."""
    q = np.clip(np.rint(a * QUANT), 0, BINS - 1).astype(np.int32)
    v = q[mask]
    n = int(v.size)
    if n == 0:
        return np.zeros(a.shape, dtype=np.float32), True
    h = np.bincount(v, minlength=BINS)
    c = np.cumsum(h)
    lo = int(np.searchsorted(c, 0.02 * n))
    hi = int(np.searchsorted(c, 0.98 * n))
    spread = (hi - lo) / QUANT
    if spread < FLAT:
        return np.zeros(a.shape, dtype=np.float32), True
    t = max(1, int(round(TOL * spread * QUANT)))
    cp = np.concatenate(([0], c)).astype(np.float64)        # cp[j] = how many are < j
    below = cp[np.clip(q - t, 0, BINS)]
    upto = cp[np.clip(q + t + 1, 0, BINS)]
    return ((below + upto) / (2.0 * n)).astype(np.float32), False


# --- the labelled runs --------------------------------------------------------------------------------------------
def load_labels(path) -> dict:
    data = path if isinstance(path, dict) else json.loads(Path(path).read_text(encoding="utf-8"))
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
def _screen_dist(r: np.ndarray, flat: bool, mask: np.ndarray, sref: np.ndarray) -> float:
    """The median |rank - the screen reference| over the screen mask; 1.0 for a flat picture."""
    if flat or not mask.any():
        return 1.0
    return float(np.median(np.abs(r[mask] - sref)))


def _class_dists(r: np.ndarray, flat: bool, outcome: np.ndarray, refs: np.ndarray) -> np.ndarray:
    """The mean |rank - each class's reference| over the outcome mask; 1.0 for a flat picture."""
    if refs.shape[1] == 0:
        return np.full(refs.shape[0], np.inf, dtype=np.float32)
    if flat:
        return np.ones(refs.shape[0], dtype=np.float32)
    return np.abs(r[outcome][None, :] - refs).mean(axis=1)


def _gap(own: float, foreign: float, min_gap: float = 0.0) -> dict:
    gap = foreign - own
    ok = gap > 0 and gap >= min_gap
    return {"worst_own": round(own, 4), "best_foreign": round(foreign, 4), "gap": round(gap, 4),
            "threshold": round(own + SAFETY * gap, 4) if ok else None,
            "verdict": "separable" if ok else "not separable from these frames"}


def _learn_screen_mask(stack: np.ndarray) -> np.ndarray:
    """Pixels whose rank (against the mask itself) is steady across every screen frame: three passes from every
    pixel; a pixel may come back at a later pass."""
    mask = np.ones(stack.shape[1:], dtype=bool)
    for _ in range(3):
        rk = np.stack([ranks(a, mask)[0] for a in stack])
        new = rk.std(axis=0) < STEADY_R
        if not new.any():
            return new
        mask = new
    return mask


def learn_arrays(frames: dict[str, list[np.ndarray]], aspect: float, start_class: str = START,
                 name: str = "", sources: dict | None = None,
                 frame_sources: dict[str, list[int]] | None = None) -> tuple[dict, dict, dict]:
    """From reduced frames {class: [160 x 120 arrays]} -> (spec, arrays, report). `frame_sources`: {class: [the
    source each frame came from]} (one source when absent) — amendment 3: two classes make the outcome mask only
    where both have frames in one source."""
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
    screen_mask = _learn_screen_mask(union)
    ranked = {c: [ranks(a, screen_mask) for a in stacks[c]] for c in frames}
    rstack = {c: np.stack([r for r, _f in ranked[c]]) for c in frames}
    screen_ref = np.concatenate([rstack[c] for c in screens]).mean(axis=0)
    sref = screen_ref[screen_mask]
    spread = np.stack([np.percentile(rstack[c], 90, axis=0) - np.percentile(rstack[c], 10, axis=0)
                       for c in screens]).max(axis=0)
    means = {c: rstack[c].mean(axis=0) for c in screens}
    ids = {c: np.asarray(frame_sources[c] if frame_sources else [0] * len(frames[c])) for c in frames}
    apart = np.zeros(union.shape[1:], dtype=np.float32)
    for src in sorted({int(i) for c in screens for i in ids[c]}):
        here = {c: rstack[c][ids[c] == src].mean(axis=0) for c in screens if (ids[c] == src).any()}
        names = list(here)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                apart = np.maximum(apart, np.abs(here[a] - here[b]))
    outcome_mask = (apart > DIFFER_R) & (apart > SEP * spread)
    refs = np.stack([means[c][outcome_mask] for c in screens]).astype(np.float32)

    def sd(c):
        return [_screen_dist(r, f, screen_mask, sref) for r, f in ranked[c]]

    dists = {c: [_class_dists(r, f, outcome_mask, refs) for r, f in ranked[c]] for c in screens}
    like = {c: [int(np.argmin(dd)) == i for dd in dists[c]] for i, c in enumerate(screens)}
    own_screen = max(d for c in screens for d, ok in zip(sd(c), like[c]) if ok) \
        if any(any(v) for v in like.values()) else float("inf")                 # amendment 4: like their label
    foreign_screen = min(sd(OTHER))
    screen = _gap(own_screen, foreign_screen)
    per_class, margins, unlike = {}, [], {}
    for i, c in enumerate(screens):
        own = [float(dd[i]) for dd in dists[c] if int(np.argmin(dd)) == i]     # amendment 3: like their label
        unlike[c] = len(dists[c]) - len(own)
        foreign = [float(dd[i]) for d in screens if d != c for dd in dists[d]]
        per_class[c] = _gap(max(own) if own else float("inf"), min(foreign), MIN_GAP)
        per_class[c]["unlike_label"] = unlike[c]
        for dd in dists[c]:
            if int(np.argmin(dd)) == i and len(dd) > 1:
                margins.append(float(np.sort(dd)[1] - dd[i]))
    margin_needed = round(SAFETY * min(margins), 4) if margins and outcome_mask.any() else None
    if not outcome_mask.any():
        for c in screens:
            per_class[c].update(threshold=None, verdict="not separable from these frames")
    ys, xs = np.nonzero(outcome_mask)
    total = SIZE[0] * SIZE[1]
    spec = {
        "version": VERSION, "kind": "privyhub-h7-endscreen", "measure": MEASURE, "size": list(SIZE),
        "aspect": round(float(aspect), 5),
        "classes": screens, "start_class": start_class, "end_classes": screens[1:],
        "screen_threshold": screen["threshold"], "class_thresholds": {c: per_class[c]["threshold"] for c in screens},
        "separable": {c: per_class[c]["verdict"] == "separable" for c in screens},
        "margin_needed": margin_needed, "usable": screen["threshold"] is not None,
        "steady_r": STEADY_R, "differ_r": DIFFER_R, "sep": SEP, "min_gap": MIN_GAP, "safety": SAFETY, "tol": TOL, "quant": 1.0 / QUANT,
        "flat": FLAT, "bar_max": BAR_MAX, "bar_share": BAR_SHARE, "k": K, "search_every_s": SEARCH_EVERY,
        "search": {"coarse_scales": list(COARSE_SCALES), "coarse_shifts_px_320": list(COARSE_SHIFTS),
                   "fine_scale": FINE_SCALE, "fine_shift_px_320": FINE_SHIFT},
        "screen_mask_px": int(screen_mask.sum()), "outcome_mask_px": int(outcome_mask.sum()),
        "frames": {c: len(frames[c]) for c in [*screens, OTHER]},
        "arrays": f"{name}.endscreen.npz" if name else None, "arrays_sha256": None,
    }
    if sources:
        spec["frames_per_source"] = sources
    arrays = {"screen_mask": screen_mask, "screen_ref": screen_ref.astype(np.float32),
              "outcome_mask": outcome_mask, "refs": refs}
    report = {
        "measure": MEASURE, "frames_per_class": spec["frames"],
        "screen_mask": {"px": int(screen_mask.sum()), "share": round(float(screen_mask.sum()) / total, 4)},
        "outcome_mask": {"px": int(outcome_mask.sum()), "share": round(float(outcome_mask.sum()) / total, 4),
                         "bbox_160x120": ([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                                          if len(xs) else None)},
        "screen": screen, "classes": per_class, "margin_needed": margin_needed,
        "smallest_margin_seen": round(min(margins), 4) if margins else None, "usable": spec["usable"],
        "unlike_label": unlike,
    }
    if sources:
        report["frames_per_source"] = sources
    return spec, arrays, report


# --- B122: places (spec version 3) -------------------------------------------------------------------------------
def place_ports(classes) -> int | None:
    """n when every end class (not start / other / ignore) is a place row `end_r<d1..dn>` (a permutation of 1..n,
    n 2-4, one n for all); None when none is (today's version 2); ValueError when they are mixed."""
    ends = [c for c in classes if c not in (START, OTHER, IGNORE)]
    rows = [c for c in ends if PLACE_LABEL.match(c)]
    if not rows:
        return None
    if len(rows) != len(ends):
        raise ValueError("some end classes are place rows and some are not: label them one way")
    ns = set()
    for c in rows:
        d = PLACE_LABEL.match(c).group(1)
        if not 2 <= len(d) <= 4 or sorted(int(x) for x in d) != list(range(1, len(d) + 1)):
            raise ValueError(f"a place row names each place 1..n once: {c}")
        ns.add(len(d))
    if len(ns) != 1:
        raise ValueError("the place rows name different numbers of ports")
    return ns.pop()


def place_row(label: str) -> list[int]:
    return [int(x) for x in PLACE_LABEL.match(label).group(1)]


def mask320(screen_mask: np.ndarray) -> np.ndarray:
    """The 160 x 120 screen mask at the 320 x 240 step (each value twice each way)."""
    return np.kron(screen_mask.astype(np.uint8), np.ones((2, 2), dtype=np.uint8)).astype(bool)


def mid_ranks(im_mid: Image.Image, screen_mask: np.ndarray, align=IDENTITY) -> np.ndarray:
    """B122: the 320 x 240 picture (aligned) ranked against its own screen-mask tone (B104's measure)."""
    a = np.asarray(_moved(im_mid, align), dtype=np.float32)
    return ranks(a, mask320(screen_mask))[0]


def _fisher(groups: list[list[np.ndarray]]) -> np.ndarray:
    gm = np.stack([np.mean(g, axis=0) for g in groups])
    within = np.mean([((np.stack(g) - np.mean(g, axis=0)) ** 2).mean(axis=0) for g in groups], axis=0)
    return gm.var(axis=0) / (within + 1e-3)


def _box_best(fis: np.ndarray, ch: int, cw: int) -> tuple[float, int, int]:
    """The (mean, y, x) of the ch x cw window with the highest mean (an integral image)."""
    h, w = fis.shape
    if h < ch or w < cw:
        return float("-inf"), 0, 0
    ii = np.zeros((h + 1, w + 1), dtype=np.float64)
    ii[1:, 1:] = fis.cumsum(0).cumsum(1)
    box = (ii[ch:, cw:] - ii[:-ch, cw:] - ii[ch:, :-cw] + ii[:-ch, :-cw]) / (ch * cw)
    i = np.unravel_index(int(np.argmax(box)), box.shape)
    return float(box[i]), int(i[0]), int(i[1])


def _cell(r: np.ndarray, oy: int, ox: int, ch: int, cw: int) -> np.ndarray | None:
    h, w = r.shape
    if oy < 0 or ox < 0 or oy + ch > h or ox + cw > w:
        return None
    return r[oy:oy + ch, ox:ox + cw]


def _cell_dists(r: np.ndarray, oy: int, ox: int, ch: int, cw: int, glyph: np.ndarray, refs: np.ndarray,
                search: int = PLACE_SEARCH) -> np.ndarray:
    """A column's distance to each place: the mean |rank - reference| over the glyph mask (as B102's outcome
    distance), the least over the +/- `search` px shifts (inf when the cell falls off the picture)."""
    best = np.full(refs.shape[0], np.inf, dtype=np.float64)
    for dy in range(-search, search + 1):
        for dx in range(-search, search + 1):
            c = _cell(r, oy + dy, ox + dx, ch, cw)
            if c is None:
                continue
            d = np.abs(c[None, :, :] - refs)[:, glyph].mean(axis=1)
            best = np.minimum(best, d)
    return best


def learn_places(rows: dict[tuple, list[np.ndarray]], n: int) -> tuple[dict, dict, dict]:
    """From {place row: [320 x 240 rank pictures]} -> (the spec's `places`, its arrays, a report). The row's spacing,
    origin and cell from the between- / within-place variance of the matches' mean pictures; one reference per place
    pooled over every column that showed it."""
    if len(rows) < 2:
        raise ValueError("places need at least two different place rows")
    seen = {q for row in rows for q in row}
    missing = [q for q in range(1, n + 1) if q not in seen]
    if missing:
        raise ValueError(f"place {missing[0]} is never shown: the pictures need a match where someone is {missing[0]}-th")
    orders = sorted(rows)
    means = np.stack([np.mean(rows[o], axis=0) for o in orders])
    h, w = means.shape[1:]
    best = None
    for s in range(PLACE_MIN_SPACING, w // (n - 1) + 1):
        xs = w - (n - 1) * s
        if xs <= 0:
            break
        groups: list[list[np.ndarray]] = [[] for _ in range(n)]
        for m, o in enumerate(orders):
            for j in range(n):
                groups[o[j] - 1].append(means[m, :, j * s: j * s + xs])
        fis = _fisher(groups)
        for ch, cw in PLACE_CELLS:
            v, y, x = _box_best(fis, ch, cw)
            if best is None or v > best[0]:
                best = (v, s, y, x, ch, cw, fis)
    score_, s, y0, x0, ch, cw, fis = best
    cy, cx, hh, ww = y0 - PLACE_PAD, x0 - PLACE_PAD, ch + 2 * PLACE_PAD, cw + 2 * PLACE_PAD
    cy, cx = max(0, cy), max(0, cx)
    glyph = fis[cy:cy + hh, cx:cx + ww] > PLACE_FISHER
    hh, ww = glyph.shape
    if not glyph.any():
        raise ValueError("no pixels carry the places in these pictures")
    offs = [(cy, cx + j * s) for j in range(n)]
    cells = [(r, list(o)) for o in orders for r in rows[o]]

    def refs_at(offs_):
        out = []
        for q in range(1, n + 1):
            got = [c for r, o in cells for j in range(n) if o[j] == q
                   for c in [_cell(r, offs_[j][0], offs_[j][1], hh, ww)] if c is not None]
            out.append(np.mean(got, axis=0))
        return np.stack(out).astype(np.float32)

    for _ in range(2):
        refs = refs_at(offs)
        new = []
        for j in range(n):
            pick = None
            for dy in range(-PLACE_REFINE, PLACE_REFINE + 1):
                for dx in range(-PLACE_REFINE, PLACE_REFINE + 1):
                    oy, ox = offs[j][0] + dy, offs[j][1] + dx
                    ds = []
                    for r, o in cells:
                        c = _cell(r, oy, ox, hh, ww)
                        if c is None:
                            ds = None
                            break
                        ds.append(float(np.abs(c - refs[o[j] - 1])[glyph].mean()))
                    if ds is None:
                        continue
                    d = float(np.mean(ds))
                    if pick is None or d < pick[0]:
                        pick = (d, (oy, ox))
            new.append(pick[1] if pick else offs[j])
        offs = new
    refs = refs_at(offs)
    own: dict[int, list[float]] = {q: [] for q in range(1, n + 1)}
    foreign: dict[int, list[float]] = {q: [] for q in range(1, n + 1)}
    margins = []
    for r, o in cells:
        for j in range(n):
            d = _cell_dists(r, offs[j][0], offs[j][1], hh, ww, glyph, refs)
            q = o[j]
            if int(np.argmin(d)) + 1 == q:
                own[q].append(float(d[q - 1]))
                margins.append(float(np.sort(d)[1] - d[q - 1]))
            for k in range(1, n + 1):
                if k != q:
                    foreign[k].append(float(d[k - 1]))
    gaps = {q: _gap(max(own[q]) if own[q] else float("inf"), min(foreign[q]) if foreign[q] else float("inf"))
            for q in range(1, n + 1)}
    need = round(SAFETY * min(margins), 4) if margins else None
    seen_in = {str(j + 1): sorted({o[j] for o in orders}) for j in range(n)}
    places = {"ports": n, "spacing_px_320": int(s), "cell": [int(hh), int(ww)],
              "offsets_px_320": [[int(a), int(b)] for a, b in offs], "row_score": round(score_, 2),
              "glyph_px": int(glyph.sum()), "thresholds": {str(q): gaps[q]["threshold"] for q in gaps},
              "separable": {str(q): gaps[q]["verdict"] == "separable" for q in gaps}, "margin_needed": need,
              "search_px": PLACE_SEARCH, "rows": ["".join(map(str, o)) for o in orders],
              "frames": {"".join(map(str, o)): len(rows[o]) for o in orders}, "seen_in_column": seen_in}
    report = {"row": {"spacing_px_320": int(s), "origin_px_320": [int(y0), int(x0)], "cell": [int(ch), int(cw)],
                      "score": round(score_, 2)}, "offsets_px_320": places["offsets_px_320"],
              "glyph_px": places["glyph_px"], "places": gaps, "margin_needed": need,
              "smallest_margin_seen": round(min(margins), 4) if margins else None, "seen_in_column": seen_in}
    return places, {"place_mask": glyph, "place_refs": refs}, report


def read_places(r320: np.ndarray, places: dict, glyph: np.ndarray, refs: np.ndarray) -> dict:
    """Every column's place: {"places": [..] | None (any unread or a place twice), "ports": [p or None per column],
    "distances": [[per place] per column], "margins": [per column]}."""
    hh, ww = places["cell"]
    got, dists, margins = [], [], []
    for oy, ox in places["offsets_px_320"]:
        d = _cell_dists(r320, oy, ox, hh, ww, glyph, refs, int(places.get("search_px", PLACE_SEARCH)))
        order = np.argsort(d)
        q = int(order[0]) + 1
        margin = float(d[order[1]] - d[order[0]]) if len(d) > 1 else float("inf")
        thr = places["thresholds"].get(str(q))
        need = places.get("margin_needed")
        ok = (places["separable"].get(str(q)) and thr is not None and np.isfinite(d[q - 1]) and d[q - 1] <= thr
              and need is not None and margin >= need)
        got.append(q if ok else None)
        dists.append([round(float(x), 4) if np.isfinite(x) else None for x in d])
        margins.append(round(margin, 4) if np.isfinite(margin) else None)
    whole = None if (None in got or len(set(got)) != len(got)) else got
    return {"places": whole, "ports": got, "distances": dists, "margins": margins}


def _sources(runs, labels) -> list:
    """[(runs folder, labels dict or path)] from one pair or a list of pairs."""
    if labels is None:
        return [(r, l) for r, l in runs]
    return [(runs, labels)]


def _paths(sources: list, half: str | None) -> tuple[dict[str, list[Path]], dict, dict[str, list[int]]]:
    paths: dict[str, list[Path]] = {}
    ids: dict[str, list[int]] = {}
    per_source = {}
    for i, (runs, labels) in enumerate(sources):
        got = labelled_frames(runs, load_labels(labels), half)
        per_source[f"source_{i + 1}"] = {c: len(ps) for c, ps in got.items()}
        for c, ps in got.items():
            paths.setdefault(c, []).extend(ps)
            ids.setdefault(c, []).extend([i] * len(ps))
    return paths, per_source, ids


def _cut_aspect(paths: list[Path]) -> float:
    sizes = []
    for p in paths[:: max(1, len(paths) // 20)]:
        with Image.open(p) as im:
            w, h = game_area(im.convert("L")).size
        sizes.append(w / h)
    return float(np.median(sizes))


def learn(runs, labels=None, half: str | None = None, start_class: str = START, name: str = ""):
    """One source (`runs`, `labels`) or several (`runs` = [(runs, labels), ...], `labels` None)."""
    t0 = time.perf_counter()
    paths, per_source, ids = _paths(_sources(runs, labels), "first" if half == "first" else None)
    for c, ps in paths.items():
        if not ps:
            raise ValueError(f"the labels name a class with no frames: {c}")
    aspect = _cut_aspect([p for ps in paths.values() for p in ps])
    n = place_ports(paths)
    if n is not None:                                     # B122: place rows -> version 3
        return _learn_v3(paths, ids, per_source, aspect, start_class, name, n, t0)
    frames = {}
    for c, ps in paths.items():
        frames[c] = []
        for p in ps:
            with Image.open(p) as im:
                frames[c].append(reduce(im))
    spec, arrays, report = learn_arrays(frames, aspect, start_class, name,
                                        per_source if len(per_source) > 1 else None, ids)
    report["learn_s"] = round(time.perf_counter() - t0, 2)
    return spec, arrays, report


SHARED_NEAR, SHARED_SHARE = 0.1, 0.5   # B122 am. 2, 3: a pixel half a foreign class ranks this near is shared


def _learn_one_screen(stack: np.ndarray, foreign: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, dict]:
    """B122 (amendments 2, 3): one screen class's own mask (steady in its pictures, minus the pixels it shares with
    either foreign class — the `other` pictures, the other screen), its reference and its threshold (halfway to the
    nearest foreign picture)."""
    m = _learn_screen_mask(stack)
    ref = np.stack([ranks(a, m)[0] for a in stack]).mean(axis=0)
    shared = np.zeros(m.shape, dtype=bool)
    for st in foreign:
        near = (np.abs(np.stack([ranks(a, m)[0] for a in st]) - ref) < SHARED_NEAR).mean(axis=0)
        shared |= near >= SHARED_SHARE
    mask = m & ~shared
    if not mask.any():
        raise ValueError("no pixels tell this screen from the other pictures")
    ref = np.stack([ranks(a, mask)[0] for a in stack]).mean(axis=0).astype(np.float32)

    def sd(a):
        r, f = ranks(a, mask)
        return _screen_dist(r, f, mask, ref[mask])
    own = max(sd(a) for a in stack)
    best = min(sd(a) for st in foreign for a in st)
    return mask, ref, dict(_gap(own, best), mask_px=int(mask.sum()), shared_px_left_out=int((m & ~mask).sum()))


def _learn_v3(paths, ids, per_source, aspect, start_class, name, n, t0):
    """B122: one screen per screen class (start, end — every place row merged), then the places on the end screen."""
    frames: dict[str, list[np.ndarray]] = {}
    mids: dict[tuple, list[Image.Image]] = {}
    for c, ps in paths.items():
        key = END if PLACE_LABEL.match(c) else c
        frames.setdefault(key, [])
        for p in ps:
            with Image.open(p) as im:
                m = mid(im)
            frames[key].append(_final(m))
            if key == END:
                mids.setdefault(tuple(place_row(c)), []).append(m)
    for c in (start_class, END, OTHER):
        if not frames.get(c):
            raise ValueError(f"the labels name no {c} frames")
    st = {c: np.stack(v).astype(np.float32) for c, v in frames.items()}
    screens, arrays = {}, {}
    for c, other_screen in ((start_class, END), (END, start_class)):
        mask, ref, gap = _learn_one_screen(st[c], [st[OTHER], st[other_screen]])
        screens[c] = gap
        arrays[f"{c}_mask"], arrays[f"{c}_ref"] = mask, ref
    rows = {o: [mid_ranks(m, arrays[f"{END}_mask"]) for m in ms] for o, ms in mids.items()}
    places, parrays, preport = learn_places(rows, n)
    arrays.update(parrays)
    usable = (all(g["threshold"] is not None for g in screens.values()) and all(places["separable"].values())
              and bool(places["margin_needed"]))
    spec = {
        "version": VERSION_PLACES, "kind": "privyhub-h7-endscreen", "measure": MEASURE, "size": list(SIZE),
        "aspect": round(float(aspect), 5), "classes": [start_class, END], "start_class": start_class,
        "end_classes": [END], "screens": {c: {"threshold": g["threshold"], "own_worst": g["worst_own"],
                                              "mask_px": g["mask_px"]} for c, g in screens.items()},
        "places": places, "usable": usable, "steady_r": STEADY_R, "shared_near": SHARED_NEAR,
        "shared_share": SHARED_SHARE, "tol": TOL, "quant": 1.0 / QUANT, "flat": FLAT, "bar_max": BAR_MAX,
        "bar_share": BAR_SHARE, "k": K, "search_every_s": SEARCH_EVERY,
        "search": {"coarse_scales": list(COARSE_SCALES), "coarse_shifts_px_320": list(COARSE_SHIFTS),
                   "fine_scale": FINE_SCALE, "fine_shift_px_320": FINE_SHIFT},
        "frames": {c: len(v) for c, v in frames.items()},
        "arrays": f"{name}.endscreen.npz" if name else None, "arrays_sha256": None,
    }
    if len(per_source) > 1:
        spec["frames_per_source"] = per_source
    report = {"measure": MEASURE, "frames_per_class": spec["frames"], "screens": screens, "places": preport,
              "usable": usable, "learn_s": round(time.perf_counter() - t0, 2)}
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


def check_spec(spec: dict) -> None:
    """A spec this tool reads, or ValueError with the plain line (a version-1 spec: learn it again)."""
    if not isinstance(spec, dict) or spec.get("kind") != "privyhub-h7-endscreen":
        raise ValueError("not an end-screen spec this tool reads")
    if spec.get("version") == 1:
        raise ValueError(OLD_MEASURE)
    if spec.get("version") not in (VERSION, VERSION_PLACES) or spec.get("measure") != MEASURE:
        raise ValueError("not an end-screen spec this tool reads")
    if spec.get("version") == VERSION_PLACES and not isinstance(spec.get("places"), dict):
        raise ValueError("a version-3 spec names its places")


def load_spec(json_path) -> tuple[dict, dict]:
    json_path = Path(json_path)
    spec = json.loads(json_path.read_text(encoding="utf-8"))
    check_spec(spec)
    name = str(spec.get("arrays") or "")
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise ValueError("the spec names no arrays file")
    data = (json_path.parent / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != spec.get("arrays_sha256"):
        raise ValueError("the spec's arrays file does not match the spec")
    v3 = spec.get("version") == VERSION_PLACES
    keys = (tuple(f"{c}_{k}" for c in spec["classes"] for k in ("mask", "ref")) + ("place_mask", "place_refs")
            if v3 else ("screen_mask", "screen_ref", "outcome_mask", "refs"))
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        arrays = {k: z[k] for k in keys}
    if v3:
        if any(arrays[f"{c}_mask"].shape != (SIZE[1], SIZE[0]) for c in spec["classes"]):
            raise ValueError("the spec's arrays do not fit the spec")
    elif arrays["screen_mask"].shape != (SIZE[1], SIZE[0]) or arrays["refs"].shape[0] != len(spec["classes"]):
        raise ValueError("the spec's arrays do not fit the spec")
    if v3:
        pl = spec["places"]
        if (list(arrays["place_mask"].shape) != list(pl["cell"]) or arrays["place_refs"].shape[0] != pl["ports"]
                or len(pl["offsets_px_320"]) != pl["ports"]):
            raise ValueError("the spec's arrays do not fit the spec")
    return spec, arrays


# --- read ---------------------------------------------------------------------------------------------------------
class Reader:
    """Reads pictures against one spec; keeps the alignment a search found (the window does not move in a game).
    A version-3 spec (B122) is read by `ReaderPlaces`."""

    def __new__(cls, spec: dict, arrays: dict, clock=time.monotonic):
        if cls is Reader and isinstance(spec, dict) and spec.get("version") == VERSION_PLACES:
            return super().__new__(ReaderPlaces)
        return super().__new__(cls)

    def __init__(self, spec: dict, arrays: dict, clock=time.monotonic):
        check_spec(spec)
        self.spec, self.clock = spec, clock
        self.screen_mask = arrays["screen_mask"].astype(bool)
        self.sref = arrays["screen_ref"][self.screen_mask].astype(np.float32)
        self.outcome = arrays["outcome_mask"].astype(bool)
        self.refs = arrays["refs"].astype(np.float32)
        self.classes = list(spec["classes"])
        self.align = IDENTITY
        self.last_search: float | None = None

    def _ranked(self, a: np.ndarray) -> tuple[np.ndarray, bool]:
        return ranks(a, self.screen_mask)

    def _sd(self, a: np.ndarray) -> float:
        r, flat = self._ranked(a)
        return _screen_dist(r, flat, self.screen_mask, self.sref)

    def _fit(self, a: np.ndarray) -> tuple[float, float]:
        """(the median — the screen test —, the mean — the search's objective, amendment 2) over the screen mask."""
        r, flat = self._ranked(a)
        if flat or not self.screen_mask.any():
            return 1.0, 1.0
        d = np.abs(r[self.screen_mask] - self.sref)
        return float(np.median(d)), float(d.mean())

    def _search(self, im_mid: Image.Image) -> tuple[float, float, tuple]:
        """-> (median, mean, alignment) of the candidate with the smallest mean."""
        best = (float("inf"), float("inf"), IDENTITY)
        for s in COARSE_SCALES:
            for dx in COARSE_SHIFTS:
                for dy in COARSE_SHIFTS:
                    med, mean = self._fit(_final(_moved(im_mid, (s, float(dx), float(dy)))))
                    if mean < best[1]:
                        best = (med, mean, (s, float(dx), float(dy)))
        s0, x0, y0 = best[2]
        for s in (s0 - FINE_SCALE, s0, s0 + FINE_SCALE):
            for dx in (x0 - FINE_SHIFT, x0, x0 + FINE_SHIFT):
                for dy in (y0 - FINE_SHIFT, y0, y0 + FINE_SHIFT):
                    al = (round(s, 4), float(dx), float(dy))
                    med, mean = self._fit(_final(_moved(im_mid, al)))
                    if mean < best[1]:
                        best = (med, mean, al)
        return best

    def _classify(self, r: np.ndarray, flat: bool) -> tuple[str, dict, float]:
        spec = self.spec
        dd = _class_dists(r, flat, self.outcome, self.refs)
        order = np.argsort(dd)
        best = int(order[0])
        margin = float(dd[order[1]] - dd[best]) if len(dd) > 1 else float("inf")
        c = self.classes[best]
        cthr = spec["class_thresholds"].get(c)
        need = spec.get("margin_needed")
        ok = (spec["separable"].get(c) and cthr is not None and dd[best] <= cthr
              and need is not None and margin >= need)
        return (c if ok else UNKNOWN), {c2: round(float(dd[i]), 4) for i, c2 in enumerate(self.classes)}, margin

    def read(self, img: Image.Image, now: float | None = None, search: bool = True) -> dict:
        spec = self.spec
        thr = spec.get("screen_threshold")
        im_mid = mid(img)
        a = _final(_moved(im_mid, self.align))
        r, flat = self._ranked(a)
        sd = _screen_dist(r, flat, self.screen_mask, self.sref)
        screen = thr is not None and sd <= thr
        cls = self._classify(r, flat)[0] if screen else OTHER
        searched = False
        if thr is not None and search and (not screen or cls == UNKNOWN):     # amendment 1: unknown searches too
            now = self.clock() if now is None else now
            if self.last_search is None or now - self.last_search >= SEARCH_EVERY:
                self.last_search, searched = now, True
                d, mean, al = self._search(im_mid)
                if d <= thr and mean < self._fit(a)[1]:                       # amendment 2: the mean decides
                    self.align, sd = al, d
                    a = _final(_moved(im_mid, al))
                    r, flat = self._ranked(a)
        out = {"screen": bool(thr is not None and sd <= thr), "class": OTHER,
               "distances": {"screen": round(sd, 4)}, "margin": None, "flat": bool(flat),
               "align": [round(self.align[0], 4), self.align[1], self.align[2]], "searched": searched}
        if not out["screen"]:
            return out
        cls, dists, margin = self._classify(r, flat)
        out["distances"].update(dists)
        out["margin"] = round(margin, 4)
        out["class"] = cls
        return out


class ReaderPlaces(Reader):
    """B122 (amendment 2): a version-3 spec — one screen per class (start, end), the places on the end screen."""

    def __init__(self, spec: dict, arrays: dict, clock=time.monotonic):
        check_spec(spec)
        self.spec, self.clock = spec, clock
        self.classes = list(spec["classes"])
        self.masks = {c: arrays[f"{c}_mask"].astype(bool) for c in self.classes}
        self.srefs = {c: arrays[f"{c}_ref"][self.masks[c]].astype(np.float32) for c in self.classes}
        self.thr = {c: spec["screens"][c]["threshold"] for c in self.classes}
        self.own_worst = {c: spec["screens"][c].get("own_worst") for c in self.classes}     # amendment 4
        self.places = spec["places"]
        self.place_mask = arrays["place_mask"].astype(bool)
        self.place_refs = arrays["place_refs"].astype(np.float32)
        self.align = IDENTITY
        self.last_search: float | None = None

    def _dist(self, a: np.ndarray, c: str, mean: bool = False) -> float:
        r, flat = ranks(a, self.masks[c])
        if flat:
            return 1.0
        d = np.abs(r[self.masks[c]] - self.srefs[c])
        return float(d.mean() if mean else np.median(d))

    def _match(self, a: np.ndarray) -> tuple[str | None, dict]:
        ds = {c: self._dist(a, c) for c in self.classes}
        ok = [c for c in self.classes if self.thr[c] is not None and ds[c] <= self.thr[c]]
        return (min(ok, key=lambda c: ds[c] / max(self.thr[c], 1e-9)) if ok else None), ds

    def _search_v3(self, im_mid: Image.Image) -> tuple:
        """The alignment that brings the picture nearest (by the mean) to the screen it is already nearest to."""
        a0 = _final(_moved(im_mid, self.align))
        c = min(self.classes, key=lambda k: self._dist(a0, k, True))
        best = (float("inf"), IDENTITY)
        for sc in COARSE_SCALES:
            for dx in COARSE_SHIFTS:
                for dy in COARSE_SHIFTS:
                    m = self._dist(_final(_moved(im_mid, (sc, float(dx), float(dy)))), c, True)
                    if m < best[0]:
                        best = (m, (sc, float(dx), float(dy)))
        s0, x0, y0 = best[1]
        for sc in (s0 - FINE_SCALE, s0, s0 + FINE_SCALE):
            for dx in (x0 - FINE_SHIFT, x0, x0 + FINE_SHIFT):
                for dy in (y0 - FINE_SHIFT, y0, y0 + FINE_SHIFT):
                    al = (round(sc, 4), float(dx), float(dy))
                    m = self._dist(_final(_moved(im_mid, al)), c, True)
                    if m < best[0]:
                        best = (m, al)
        return best[1]

    def read(self, img: Image.Image, now: float | None = None, search: bool = True) -> dict:
        im_mid = mid(img)
        a = _final(_moved(im_mid, self.align))
        cls, ds = self._match(a)
        searched = False
        if cls is None and search and any(t is not None for t in self.thr.values()):
            now = self.clock() if now is None else now
            if self.last_search is None or now - self.last_search >= SEARCH_EVERY:
                self.last_search, searched = now, True
                al = self._search_v3(im_mid)
                c2, ds2 = self._match(_final(_moved(im_mid, al)))
                worst = self.own_worst.get(c2) if c2 is not None else None
                if c2 is not None and worst is not None and ds2[c2] <= worst:   # amendment 4: as close as its own
                    self.align, cls, ds = al, c2, ds2
        out = {"screen": cls is not None, "class": cls or OTHER,
               "distances": {"screen": round(min(ds.values()), 4), **{c: round(v, 4) for c, v in ds.items()}},
               "margin": None, "flat": False, "align": [round(self.align[0], 4), self.align[1], self.align[2]],
               "searched": searched, "places": None}
        if cls == END:
            pr = read_places(mid_ranks(im_mid, self.masks[END], self.align), self.places, self.place_mask,
                             self.place_refs)
            ms = [m for m in pr["margins"] if m is not None]
            out.update(place_distances=pr["distances"], place_margins=pr["margins"], ports=pr["ports"],
                       margin=min(ms) if ms else None)
            if pr["places"] is None:
                out["class"] = UNKNOWN
            else:
                out["places"] = pr["places"]
        return out


def read(spec: dict, arrays: dict, img: Image.Image) -> dict:
    """One picture, read by a fresh Reader (a non-screen picture gets the full search)."""
    return Reader(spec, arrays).read(img)


def thresholds(spec: dict) -> dict:
    """What a read's distances are held against (B105's `last`)."""
    if spec.get("version") == VERSION_PLACES:              # B122
        pl = spec["places"]
        return {"screens": {c: v["threshold"] for c, v in spec["screens"].items()},
                "places": dict(pl["thresholds"]), "margin_needed": pl["margin_needed"]}
    return {"screen": spec.get("screen_threshold"), "classes": dict(spec.get("class_thresholds") or {}),
            "margin_needed": spec.get("margin_needed")}


class Ended:
    """K agreeing reads in a row; an end class counts only after the start was seen (K start reads, or a load)."""

    def __init__(self, spec: dict, k: int | None = None):
        self.start = spec["start_class"]
        self.ends = set(spec["end_classes"])
        self.k = int(k or spec.get("k") or K)
        self.seen_start = False
        self.run_class, self.run = None, 0
        self.ended: str | None = None
        self.places: list[int] | None = None          # B122: the row the end was said with (version 3)

    def start_loaded(self) -> None:
        self.seen_start = True

    def feed(self, cls: str, places=None) -> str | None:
        """One read's class (and, version 3, its places) -> the end class once ended, else None. K agreeing reads of
        the whole row: the same class and the same places."""
        if self.ended:
            return self.ended
        key = (cls, tuple(places) if places else None)
        if key == self.run_class:
            self.run += 1
        else:
            self.run_class, self.run = key, 1
        if self.run >= self.k:
            if cls == self.start:
                self.seen_start = True
            elif cls in self.ends and self.seen_start:
                self.ended = cls
                self.places = list(places) if places else None
        return self.ended


# --- score --------------------------------------------------------------------------------------------------------
def score(runs, labels, spec: dict, arrays: dict, half: str | None = None, transform=None,
          search: bool = True) -> dict:
    """The confusion counts per labelled class and `other_read_as_screen` (must be 0). One source (`runs`,
    `labels`) or several (`runs` = [(runs, labels), ...], `labels` None). `transform(img) -> img` (optional) changes
    every picture first (alignment, tone). Each picture read by a fresh Reader."""
    sources = _sources(runs, labels)
    cols = [*spec["classes"], UNKNOWN, OTHER]
    confusion: dict[str, dict[str, int]] = {}
    worst_own: dict[str, float] = {}
    least_margin: dict[str, float] = {}
    times, other_screen, other_least = [], 0, float("inf")
    per_source = {}
    for i, (rf, lb) in enumerate(sources):
        paths = labelled_frames(rf, load_labels(lb), "second" if half == "second" else None)
        mine = {c: dict.fromkeys(cols, 0) for c in paths}
        for c, ps in paths.items():
            confusion.setdefault(c, dict.fromkeys(cols, 0))
            for p in ps:
                with Image.open(p) as im:
                    img = im.convert("L")
                if transform is not None:
                    img = transform(img)
                t0 = time.perf_counter()
                r = Reader(spec, arrays).read(img, search=search)
                times.append((time.perf_counter() - t0) * 1000.0)
                confusion[c][r["class"]] += 1
                mine[c][r["class"]] += 1
                if c == OTHER:
                    other_least = min(other_least, r["distances"]["screen"])
                    if r["screen"]:
                        other_screen += 1
                if r["class"] == c and c != OTHER:
                    worst_own[c] = max(worst_own.get(c, 0.0), r["distances"][c])
                    least_margin[c] = min(least_margin.get(c, float("inf")), r["margin"])
        per_source[f"source_{i + 1}"] = {c: [mine[c][c], sum(mine[c].values())] for c in mine}
    out = {"confusion": confusion,
           "right": {c: [confusion[c][c], sum(confusion[c].values())] for c in confusion},
           "other_read_as_screen": other_screen,
           "other_least_screen_distance": round(other_least, 4) if other_least != float("inf") else None,
           "worst_own_distance": {c: round(v, 4) for c, v in worst_own.items()},
           "least_margin": {c: round(v, 4) for c, v in least_margin.items()},
           "read_ms": {"median": round(float(np.median(times)), 2), "worst": round(float(max(times)), 2),
                       "n": len(times)} if times else None}
    if len(sources) > 1:
        out["right_per_source"] = per_source
    return out


def score_places(runs, labels, spec: dict, arrays: dict, half: str | None = None, transform=None,
                 search: bool = True, keep_reads: bool = False) -> dict:
    """B122: a version-3 spec against labels with place rows. Per labelled class: rows read right / unknown / wrong /
    other (a place row: `end` with exactly its places; `start` / `other`: that class); per port: places right / unread
    / wrong (each column's own read, also inside an `unknown` row); `other` read as the screen (must be 0); the time
    to read one picture. Each picture read by a fresh Reader."""
    sources = _sources(runs, labels)
    n = spec["places"]["ports"]
    rows: dict[str, dict[str, int]] = {}
    ports = {str(j + 1): {"right": 0, "unread": 0, "wrong": 0} for j in range(n)}
    times, other_screen = [], 0
    reads = []
    for rf, lb in sources:
        paths = labelled_frames(rf, load_labels(lb), "second" if half == "second" else None)
        for c, ps in paths.items():
            row = place_row(c) if PLACE_LABEL.match(c) else None
            tally = rows.setdefault(c, {"right": 0, "unknown": 0, "wrong": 0, "other": 0, "n": 0})
            for p in ps:
                with Image.open(p) as im:
                    img = im.convert("L")
                if transform is not None:
                    img = transform(img)
                t0 = time.perf_counter()
                r = Reader(spec, arrays).read(img, search=search)
                times.append((time.perf_counter() - t0) * 1000.0)
                tally["n"] += 1
                if keep_reads:
                    reads.append([p.name, c, r["class"], r.get("places")])
                if c == OTHER and r["screen"]:
                    other_screen += 1
                if row is None:
                    want = c
                    tally["right" if r["class"] == want else ("unknown" if r["class"] == UNKNOWN else
                                                             ("other" if r["class"] == OTHER else "wrong"))] += 1
                    continue
                if r["class"] == END and r.get("places") == row:
                    tally["right"] += 1
                elif r["class"] == UNKNOWN:
                    tally["unknown"] += 1
                elif r["class"] == OTHER:
                    tally["other"] += 1
                else:
                    tally["wrong"] += 1
                got = r.get("ports")
                if got is not None:
                    for j in range(n):
                        k = "unread" if got[j] is None else ("right" if got[j] == row[j] else "wrong")
                        ports[str(j + 1)][k] += 1
    out = {"rows": rows, "ports": ports, "other_read_as_screen": other_screen,
           "places_wrong": sum(v["wrong"] for v in ports.values()),
           "read_ms": {"median": round(float(np.median(times)), 2), "worst": round(float(max(times)), 2),
                       "n": len(times)} if times else None}
    if keep_reads:
        out["reads"] = reads
    return out


# --- replay -------------------------------------------------------------------------------------------------------
def _index(run_folder: Path) -> list[tuple[float, str]]:
    index = run_folder / "index.csv"
    if not index.is_file():
        raise ValueError("the run folder has no index.csv")
    with index.open(newline="", encoding="utf-8") as fh:
        rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader(fh)]
    return sorted(rows)


def _end_arrivals(rows: list[tuple[float, str]], labels: dict, run: str, ends: set) -> list[float]:
    """The seconds of the first picture labelled with an end class after an `other` stretch (each match's end)."""
    ranges = sorted(labels.get("runs", {}).get(run, []), key=lambda r: float(r["from"]))
    out, prev = [], None
    for r in ranges:
        label = r.get("label")
        if label == IGNORE:
            continue
        if label in ends and prev != label:
            lo, hi = float(r["from"]) - 1e-6, float(r["to"]) + 1e-6
            first = next((t for t, _f in rows if lo <= t <= hi), None)
            if first is not None and (prev == OTHER or prev is None):
                out.append(first)
        prev = label
    return out


def replay(run_folder, spec: dict, arrays: dict, k: int | None = None, labels=None) -> dict:
    """A run's pictures in order through one Reader (its clock the pictures' own seconds) and Ended (re-armed after
    each end, the start then to be seen again). -> {"reads": [[seconds, class, screen distance]], "changes",
    "ended": [{"seconds", "class", "after_end_screen_s"}], "k"}."""
    run_folder = Path(run_folder)
    rows = _index(run_folder)
    now = [0.0]
    reader = Reader(spec, arrays, clock=lambda: now[0])
    ended = Ended(spec, k)
    reads, changes, ends = [], [], []
    last = None
    for t, f in rows:
        now[0] = t
        with Image.open(run_folder / f) as im:
            r = reader.read(im.convert("L"), now=t)
        reads.append([t, r["class"], r["distances"]["screen"]])
        here = (r["class"], tuple(r["places"]) if r.get("places") else None)
        if here != last:
            changes.append([t, r["class"]] + ([r["places"]] if r.get("places") else []))
            last = here
        done = ended.feed(r["class"], r.get("places"))
        if done:
            ends.append({"seconds": t, "class": done, **({"places": ended.places} if ended.places else {})})
            ended = Ended(spec, k)
    arrivals = []
    if labels is not None:
        lab = load_labels(labels)
        ends_set = set(spec["end_classes"])
        if spec.get("version") == VERSION_PLACES:          # B122: the labels name the place rows
            ends_set = {c for c in lab["classes"] if PLACE_LABEL.match(c)}
        arrivals = _end_arrivals(rows, lab, run_folder.name, ends_set)
        for e in ends:
            before = [a for a in arrivals if a <= e["seconds"]]
            e["end_screen_from_s"] = before[-1] if before else None
            e["after_end_screen_s"] = round(e["seconds"] - before[-1], 2) if before else None
    return {"k": ended.k, "pictures": len(rows), "reads": reads, "changes": changes, "ended": ends,
            "end_screen_arrivals_s": arrivals}


# --- CLI ----------------------------------------------------------------------------------------------------------
def _pairs(args: list[str]) -> list[tuple[str, str]]:
    if len(args) < 2 or len(args) % 2:
        raise ValueError("give runs and labels in pairs")
    return [(args[i], args[i + 1]) for i in range(0, len(args), 2)]


def main(argv: list[str]) -> int:
    def opt(name):
        if name in argv:
            i = argv.index(name)
            if i + 1 >= len(argv):
                raise ValueError(f"{name} needs a value")
            v = argv[i + 1]
            del argv[i:i + 2]
            return v
        return None

    argv = list(argv)
    half = opt("--half")
    k = opt("--k")
    labels = opt("--labels")
    if len(argv) >= 4 and argv[0] == "learn":
        out = Path(argv[-1])
        name = out.name[: -len(".endscreen.json")] if out.name.endswith(".endscreen.json") else ""
        spec, arrays, report = learn(_pairs(argv[1:-1]), None, half, name=name)
        save_spec(spec, arrays, out)
        print(json.dumps(report, indent=1, sort_keys=True))
        return 0
    if len(argv) >= 4 and argv[0] == "score":
        spec, arrays = load_spec(argv[-1])
        fn = score_places if spec.get("version") == VERSION_PLACES else score
        print(json.dumps(fn(_pairs(argv[1:-1]), None, spec, arrays, half), indent=1, sort_keys=True))
        return 0
    if len(argv) == 3 and argv[0] == "read":
        spec, arrays = load_spec(argv[1])
        with Image.open(argv[2]) as im:
            print(json.dumps(read(spec, arrays, im.convert("L")), sort_keys=True))
        return 0
    if len(argv) == 3 and argv[0] == "replay":
        spec, arrays = load_spec(argv[2])
        folder = Path(argv[1])
        if labels is None and (folder / "labels.json").is_file():
            labels = str(folder / "labels.json")
        out = replay(folder, spec, arrays, int(k) if k else None, labels)
        for t, c, d in out["reads"]:
            print(json.dumps({"seconds": t, "class": c, "screen": d}))
        for ch in out["changes"]:
            print(json.dumps({"change": ch[1], "seconds": ch[0], **({"places": ch[2]} if len(ch) > 2 else {})}))
        for e in out["ended"]:
            print(json.dumps({"ended": e["class"], **e}))           # version 3: with its places
        print(json.dumps({"summary": {"k": out["k"], "pictures": out["pictures"], "ended": len(out["ended"]),
                                      "end_screen_arrivals_s": out["end_screen_arrivals_s"]}}))
        return 0
    print(__doc__.split("usage:")[1].strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
