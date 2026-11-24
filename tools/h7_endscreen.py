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

B178 — each side's number on the final screen (spec version 4, only when every end class is a score label
`end_s<a>-<b>[-<c>-<d>]`, the numbers each side shows, P1 first; any other labels as before):
  the screen — version 3's: one end class `end` (every score class merged), `start`, `other`.
  the places — the game's area at 640 x 480; ink = pixels off their local mean (radius 8 or 16) by 12 % of the
           picture's own spread; strings of glyphs (8-connected parts >= 10 px tall, tops / bottoms within 2 px);
           each side's place a string with as many glyphs as its number has digits in every save, at one place
           (top / bottom within 2 px, centre or an edge within 4 px); the sides chosen together: a line height they
           share, then the readings' agreement (one digit's glyphs alike), then the tallest.
  a digit  — each glyph's cell normalised by its own 5th / 95th percentiles, 24 px tall; its distance to a template the
           largest 3 x 3 local mean |difference| (least over +/-1 px); each digit's template its labelled glyphs'
           mean, its threshold halfway from its own spread (at least the title's own: the largest spread of a digit
           two saves show) to the nearest other digit; margin_needed half the least margin seen. A digit never
           labelled has no template.
  a read   — the screen as version 3; on `end` every side's number, or `unknown` when any glyph is not read (never
           the nearest digit by itself). `EndedScore`: K agreeing reads of the class and every number.
  B200    — a number as drawn (`Drawn`: its value an int, its glyphs its text — "03" is 3 with the glyphs 0 and 3);
           a place whose glyphs are the same shape in saves labelled with different digits is never taken
           (`_shapes_explained`); a line-score column off its final's line (a box of small cells) found anywhere on
           the picture, its glyphs in their own group when another size.

B191 / B192 — a word spelled by the player who lost (spec version 5, `learn_letters`, called by the add-a-game tool with
the word and each end save's corners as the session read them; never from labels alone):
  the start — B122's one-screen learner on the begin's own still picture against the mid-match save's and the end
           saves' pictures, B137's top-right corner (200 x 70) black in every picture, at learn and at every read.
  a corner — each player's letters (P1 the left third, P2 the right third; top or bottom), found from two cues — the
           pixels the same in two saves showing that player's same letters over different pictures, and the pixels off
           a plain corner's commonest colour (never the end screens' fixed pixels, never a dark one) — as a string of
           as many glyphs as the session read, at one place in the most saves; the box around it fits the whole word.
           Its colours: chromaticity bins as common among the letters' pixels as `ratio` x among the backgrounds'.
  a letter — the glyph's pixels in a 36 x 40 window; a template per letter (shared by the players: one font); the mean
           |difference| least over +/-3 px; thresholds halfway to the nearest other letter; the margin.
  B192    — synthetic pictures to train, never to prove: the letters' pixels of each real end save put over patches
           cut from the title's own pictures (shifted, scaled, a fixed seed from the saves); held-out pictures made
           first; rounds of training pictures until every held-out one is read (`trained`, with its counts).
  a read  — start; else both corners: exactly one spelled -> end_P<the other>; none -> other; both -> unknown; one not
           read beside a spelled one -> unknown (`end_unread`); a moving screen never the same end twice in a row.

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
# B178: each side's score (spec version 4)
VERSION_SCORE = 4
SCORE_SIDE = r"(?:(?:\d{1,4}|_)(?:\+(?:\d{1,4}|_))*=)?\d{1,4}"     # B181: 15, or the line score 9+2+2+2+_+_=15
SCORE_LABEL = re.compile(rf"^end_s({SCORE_SIDE}(?:-{SCORE_SIDE}){{1,3}})$")   # end_s15-2: P1's 15, P2's 2 (2-4 sides)
SCORE_SIZE = (640, 480)          # the picture the numbers are read on (the game's area)
SCORE_RS = (8, 16)               # px: the local mean's radius tried for the ink
SCORE_INK = 0.12                 # ink: off its local mean by this share of the picture's own 2nd-98th percentile spread
SCORE_INK_MIN = 8.0              # ... and by at least this many grey levels
SCORE_HMIN = 10                  # px: a number's glyph is at least this tall (at SCORE_SIZE)
SCORE_TOL = 2                    # px: one line's tops / bottoms agree within this; a place holds within 2x this
SCORE_CELL = (24, 20)            # a glyph's cell: its crop resized to this height keeping its width, centred
SCORE_SHIFT = 1                  # px: a cell compared within +/- this shift
SCORE_MAX_DIGITS = 4


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
    n = score_sides(paths)
    if n is not None:                                     # B178: scores -> version 4
        return _learn_v4(paths, ids, per_source, aspect, start_class, name, n, t0)
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


# --- B178: each side's score on the final screen (spec version 4) ---------------------------------------------------
def score_sides(classes) -> int | None:
    """n when every end class (not start / other / ignore) is a score label `end_s<a>-<b>[-<c>-<d>]` (one n for all,
    2-4 sides); None when none is (version 2 / 3 as before); ValueError when they are mixed."""
    ends = [c for c in classes if c not in (START, OTHER, IGNORE)]
    nums = [c for c in ends if SCORE_LABEL.match(c)]
    if not nums:
        return None
    if len(nums) != len(ends):
        raise ValueError("some end classes are scores and some are not: label them one way")
    ns = {len(score_numbers(c)) for c in nums}
    if len(ns) != 1:
        raise ValueError("the score labels name different numbers of sides")
    return ns.pop()


class Drawn(int):
    """B200: a number as the screen draws it — its value for every check (`int`), its glyphs for every glyph count and
    every glyph's label (`str`): Drawn("03") == 3, str() "03". JSON writes the value."""

    def __new__(cls, text):
        text = str(text)
        obj = super().__new__(cls, int(text))
        obj.text = text
        return obj

    def __str__(self) -> str:
        return self.text

    def __format__(self, spec: str) -> str:
        return self.text if not spec else int(self).__format__(spec)

    def __reduce__(self):
        return (Drawn, (self.text,))


def score_numbers(label: str) -> list[int]:
    """Each side's final (the result), P1 first; B200: as drawn (`Drawn`)."""
    return [Drawn(side.rpartition("=")[2]) for side in SCORE_LABEL.match(label).group(1).split("-")]


def score_cells(label: str) -> list[list]:
    """B181: each side's line-score cells left to right (a number — B200: as drawn — or None for a blank cell); [] for
    a final alone."""
    out = []
    for side in SCORE_LABEL.match(label).group(1).split("-"):
        cells, eq, _fin = side.rpartition("=")
        out.append([None if x == "_" else Drawn(x) for x in cells.split("+")] if eq else [])
    return out


def score_picture(img: Image.Image, align=IDENTITY) -> np.ndarray:
    """The picture the numbers are read on: grey, the game's area, SCORE_SIZE (BILINEAR); the reader's alignment
    (found at 320 x 240) applied at this size."""
    im = game_area(img.convert("L")).resize(SCORE_SIZE, Image.BILINEAR)
    if tuple(align) != IDENTITY:
        s, dx, dy = align
        k = SCORE_SIZE[0] / MID[0]
        im = _moved(im, (s, dx * k, dy * k))
    return np.asarray(im, dtype=np.float32)


def _contrast(a: np.ndarray) -> float:
    return float(np.percentile(a, 98) - np.percentile(a, 2))


def _box_mean(a: np.ndarray, r: int) -> np.ndarray:
    h, w = a.shape
    p = np.pad(a.astype(np.float64), r + 1, mode="edge")
    ii = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    return ((ii[k:k + h, k:k + w] - ii[:h, k:k + w] - ii[k:k + h, :w] + ii[:h, :w]) / (k * k)).astype(np.float32)


def _ink(a: np.ndarray, pol: int, r: int, contrast: float) -> np.ndarray:
    """Pixels brighter (pol 1) or darker (pol -1) than their local mean (radius r) by SCORE_INK of the picture's own
    spread (at least SCORE_INK_MIN grey)."""
    t = max(SCORE_INK_MIN, SCORE_INK * contrast)
    d = a - _box_mean(a, r)
    return d > t if pol > 0 else -d > t


def _components(m: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """8-connected parts of a mask (a pixel font's diagonal strokes touch only at corners): (top, left, bottom, right,
    pixels), in scan order."""
    h, w = m.shape
    lab = np.full((h, w), -1, np.int32)
    out = []
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if lab[y0, x0] >= 0:
            continue
        n = len(out)
        st = [(y0, x0)]
        lab[y0, x0] = n
        t, b, l, r, c = y0, y0, x0, x0, 0
        while st:
            y, x = st.pop()
            c += 1
            t, b, l, r = min(t, y), max(b, y), min(l, x), max(r, x)
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1),
                           (y + 1, x + 1), (y + 1, x - 1), (y - 1, x + 1), (y - 1, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and lab[yy, xx] < 0:
                    lab[yy, xx] = n
                    st.append((yy, xx))
        out.append((t, l, b, r, c))
    return out


def _merge_x(cs: list) -> list:
    """Parts overlapping in x are one glyph; left to right."""
    gl: list = []
    for c in sorted(cs, key=lambda c: (c[1], c[0])):
        if gl and c[1] <= gl[-1][3]:
            g = gl[-1]
            gl[-1] = (min(g[0], c[0]), g[1], max(g[2], c[2]), max(g[3], c[3]), g[4] + c[4])
        else:
            gl.append(c)
    return gl


def _gap_ok(prev, nxt) -> bool:
    h = prev[2] - prev[0] + 1
    return -SCORE_TOL <= nxt[1] - prev[3] - 1 <= max(4, 0.6 * h)


_STRINGS: dict = {}


def score_strings(a: np.ndarray) -> list[dict]:
    """Every string of glyphs on the picture, each polarity and radius: parts >= SCORE_HMIN tall and no wider than 1.5x
    their height, grouped left to right while their top and bottom agree within SCORE_TOL and the gap is small."""
    key = hashlib.sha256(a.tobytes()).hexdigest()
    if key in _STRINGS:
        return _STRINGS[key]
    contrast = _contrast(a)
    out = []
    for pol in (1, -1):
        for r in SCORE_RS:
            cs = [c for c in _components(_ink(a, pol, r, contrast))
                  if c[2] - c[0] + 1 >= SCORE_HMIN and c[3] - c[1] + 1 <= 1.5 * (c[2] - c[0] + 1)]
            cs.sort(key=lambda c: (c[1], c[0]))
            used: set = set()
            for i, c in enumerate(cs):
                if i in used:
                    continue
                s = [c]
                used.add(i)
                while True:
                    nxt = None
                    for j, k in enumerate(cs):
                        if j in used or abs(k[0] - c[0]) > SCORE_TOL or abs(k[2] - c[2]) > SCORE_TOL:
                            continue
                        if _gap_ok(s[-1], k) and (nxt is None or k[1] < cs[nxt][1]):
                            nxt = j
                    if nxt is None:
                        break
                    used.add(nxt)
                    s.append(cs[nxt])
                s = _merge_x(s)
                if len(s) <= SCORE_MAX_DIGITS:
                    out.append({"pol": pol, "r": r, "n": len(s), "top": s[0][0], "bot": s[0][2], "x0": s[0][1],
                                "x1": s[-1][3]})
    if len(_STRINGS) > 256:
        _STRINGS.clear()
    _STRINGS[key] = out
    return out


_ANCHOR = {"centre": lambda d: (d["x0"] + d["x1"]) / 2.0, "left": lambda d: float(d["x0"]),
           "right": lambda d: float(d["x1"])}


def _find_place(strs: dict, digits: dict, ok=None) -> tuple[list, list]:
    """One side's places: a string with that side's number of digits in every save, at one place (top / bottom within
    SCORE_TOL, the anchor within 2 x SCORE_TOL). -> (every such place, best first: the tallest, the least spread …;
    the saves where the place that holds in the most saves breaks, when none holds in all). B200: `ok(place)` ->
    (taken, the saves that refuse it): a place it refuses is never taken (before one variant per screen place is
    kept); when it refuses every place, the saves it names."""
    runs = sorted(strs)
    best, best_cover = [], (-1, None)
    for r0 in runs:
        for c in strs[r0]:
            if c["n"] != digits[r0]:
                continue
            for mode, key in _ANCHOR.items():
                got, miss = {r0: c}, []
                for r in runs:
                    if r == r0:
                        continue
                    m = [d for d in strs[r] if d["pol"] == c["pol"] and d["r"] == c["r"] and d["n"] == digits[r]
                         and abs(key(d) - key(c)) <= 2 * SCORE_TOL and abs(d["top"] - c["top"]) <= SCORE_TOL
                         and abs(d["bot"] - c["bot"]) <= SCORE_TOL]
                    if m:
                        got[r] = min(m, key=lambda d: (abs(key(d) - key(c)), d["x0"]))
                    else:
                        miss.append(r)
                place = {"pol": c["pol"], "r": c["r"], "align": mode,
                         "top": int(np.median([g["top"] for g in got.values()])),
                         "bot": int(np.median([g["bot"] for g in got.values()])),
                         "x0": int(min(g["x0"] for g in got.values())), "x1": int(max(g["x1"] for g in got.values()))}
                spread = max(key(g) for g in got.values()) - min(key(g) for g in got.values())
                rank = (-(place["bot"] - place["top"]), spread, -c["pol"], c["r"], place["x0"], mode)   # the tallest
                if not miss and place not in [b_ for _r, b_ in best]:
                    best.append((rank, place))
                if miss and len(got) > best_cover[0]:
                    best_cover = (len(got), sorted(miss))
    refused: list = []
    if best and ok is not None:                          # B200: a place whose shapes the labels do not explain
        fine = []
        for x in sorted(best, key=lambda x: x[0]):
            took, who = ok(x[1])
            if took:
                fine.append(x)
            elif not refused:
                refused = sorted(who) or runs
        if not fine:
            return [], refused
        best = fine
    if best:
        kept: list = []                                  # one entry per place on the screen: its best variant
        for _r, b_ in sorted(best, key=lambda x: x[0]):
            if not any(_overlap(b_, k_) for k_ in kept):
                kept.append(b_)
        return kept, []
    return [], best_cover[1] or runs


def _overlap(a: dict, b: dict) -> bool:
    return not (a["bot"] < b["top"] or a["top"] > b["bot"] or a["x1"] < b["x0"] or a["x0"] > b["x1"])


SCORE_CHOICES = 4                # each side's best places weighed against each other (when the lengths do not decide)
SCORE_SAME_SHAPE = 0.5           # B200: glyphs labelled with different digits this near (or nearer than two labelled
#                                  alike) are one shape: the place is not a number (measured: alike <= 0.492, different
#                                  >= 0.719 on T90's and T92's real places; 0.034 at the hollow of T92's leading 0s)


def _shape_cells(first: dict, place: dict, want: dict) -> list | None:
    """B200: every labelled glyph's cell at a place, on each save's picture -> [(its drawn digit, save, cell, its
    index in the number)]; None when a save's number does not fit the place (as many glyphs as it is drawn with).
    `want`: {save: its number as drawn, or None for a blank (skipped)}."""
    out = []
    for r, v in want.items():
        if v is None:
            continue
        gl = place_glyphs(first[r], place)
        if gl is None or len(gl) != len(str(v)):
            return None
        out += [(ch, r, glyph_cell(first[r], g, place), i) for i, (ch, g) in enumerate(zip(str(v), gl))]
    return out


def _shapes_explained(cells: list) -> tuple[bool, list]:
    """B200 (BL item 1): the labels explain a place's shapes when the nearest two glyphs labelled with different digits
    are farther apart than the farther of (the farthest two labelled alike, SCORE_SAME_SHAPE) — a panel, a heading's
    glyph, the hollow of a leading 0, a stats cell is the same shape in saves labelled with different digits. With one
    save left out it may hold while the other saves still show different digits there (that save's own reading may be
    wrong: label's read-back names it); else the place is never taken. -> (explained, the saves of the nearest such
    pair)."""
    pairs = []
    for x in range(len(cells)):
        for y in range(x + 1, len(cells)):
            a, b = cells[x], cells[y]
            pairs.append((float(cell_dists(a[2], b[2][None])[0]), a[0] == b[0], a[1], b[1]))

    def holds(skip) -> bool:
        use = [q for q in pairs if skip not in (q[2], q[3])]
        alike = max([q[0] for q in use if q[1]] or [0.0])
        unlike = [q[0] for q in use if not q[1]]
        if not unlike:                                        # one digit only: nothing to judge — left out, no proof
            return skip is None
        return min(unlike) > max(alike, SCORE_SAME_SHAPE)
    if holds(None):
        return True, []
    if any(holds(r) for r in sorted({c_[1] for c_ in cells})):
        return True, ["excused"]                              # explained only with one save left out
    near = min((q for q in pairs if not q[1]), key=lambda q: q[0])
    return False, sorted({near[2], near[3]})


def _agreement(places: list, firsts: dict, nums: dict) -> float | None:
    """How well the readings fit these places: every save's glyphs at each place, as many as its number's digits
    (else None), and the mean distance of each glyph to its digit's mean over every save (one digit's glyphs alike)."""
    cells: dict[str, list] = {}
    for r, a in firsts.items():
        contrast = _contrast(a)
        for k, pl in enumerate(places):
            gl = place_glyphs(a, pl, contrast)
            if gl is None or len(gl) != len(str(nums[r][k])):
                return None
            for ch, g in zip(str(nums[r][k]), gl):
                cells.setdefault(ch, []).append(glyph_cell(a, g, pl))
    d = [float(cell_dists(c, np.mean(v, axis=0)[None])[0]) for v in cells.values() for c in v]
    return float(np.mean(d)) if d else None


def _choose_places(cands: list, firsts: dict, nums: dict) -> list:
    """One place per side, none overlapping another. Each side's best SCORE_CHOICES places, every combination: a line
    height every side shares (within SCORE_TOL) first, then the readings' agreement (`_agreement`: when two sides'
    numbers are as long in every save, only the digits tell P1's place from P2's), then the places' own order."""
    import itertools
    best = None
    for combo in itertools.product(*[c[:SCORE_CHOICES] for c in cands]):
        if any(_overlap(a, b) for i, a in enumerate(combo) for b in combo[i + 1:]):
            continue
        hs = [c["bot"] - c["top"] for c in combo]
        fit = _agreement(list(combo), firsts, nums)
        if fit is None:
            continue
        key = (max(hs) - min(hs) > SCORE_TOL, round(fit, 4), [cands[k].index(c) for k, c in enumerate(combo)])
        if best is None or key < best[0]:
            best = (key, [dict(c) for c in combo])
    return best[1] if best else []


def place_glyphs(a: np.ndarray, place: dict, contrast: float | None = None) -> list | None:
    """The glyphs of the number at a learnt place, left to right: parts whose top and bottom are the line's within
    SCORE_TOL, parts overlapping in x merged. None when they do not make one number (a gap too wide, more digits than
    SCORE_MAX_DIGITS)."""
    contrast = _contrast(a) if contrast is None else contrast
    top, bot, r = place["top"], place["bot"], int(place["r"])
    h = bot - top + 1
    pad = int(round(h * SCORE_CELL[1] / SCORE_CELL[0])) + 2
    H, W = a.shape
    y0, y1 = max(0, top - h // 2), min(H, bot + h // 2 + 1)
    x0, x1 = max(0, place["x0"] - pad), min(W, place["x1"] + pad + 1)
    oy, ox = max(0, y0 - r - 1), max(0, x0 - r - 1)
    sub = a[oy:min(H, y1 + r + 1), ox:min(W, x1 + r + 1)]
    cs = [(c[0] + oy, c[1] + ox, c[2] + oy, c[3] + ox, c[4]) for c in _components(_ink(sub, place["pol"], r, contrast))]
    main = [c for c in cs if x0 <= c[1] and c[3] < x1 and abs(c[0] - top) <= SCORE_TOL and abs(c[2] - bot) <= SCORE_TOL]
    gl = _merge_x(main)
    if not gl or len(gl) > SCORE_MAX_DIGITS or not all(_gap_ok(p, q) for p, q in zip(gl, gl[1:])):
        return None
    return gl


def glyph_cell(a: np.ndarray, g, place: dict) -> np.ndarray:
    """A glyph's cell: its crop over the line's rows, normalised by its own 5th / 95th percentiles (inverted for dark
    ink), resized to SCORE_CELL's height keeping its width (BOX), centred in a cell one pixel larger each way."""
    top, bot = place["top"], place["bot"]
    crop = a[top:bot + 1, g[1]:g[3] + 1]
    lo, hi = np.percentile(crop, 5), np.percentile(crop, 95)
    v = np.clip((crop - lo) / max(float(hi - lo), 1.0), 0.0, 1.0)
    if place["pol"] < 0:
        v = 1.0 - v
    ch, cw = SCORE_CELL
    w = min(cw, max(1, int(round(v.shape[1] * ch / v.shape[0]))))
    arr = np.asarray(Image.fromarray((v * 255).astype(np.uint8)).resize((w, ch), Image.BOX), np.float32) / 255.0
    cell = np.zeros((ch + 2, cw + 2), np.float32)
    off = (cw + 2 - w) // 2
    cell[1:ch + 1, off:off + w] = arr
    return cell


def _local_max(d: np.ndarray) -> np.ndarray:
    """(m, h, w) differences -> (m,): the largest 3 x 3 mean (edges repeated) — a stroke one glyph has and the other
    lacks counts in full, where a mean over the whole cell dilutes it (B178 addendum: T90's 8 / 9)."""
    p = np.pad(d, ((0, 0), (1, 1), (1, 1)), mode="edge")
    s = sum(p[:, y:y + d.shape[1], x:x + d.shape[2]] for y in range(3) for x in range(3))
    return (s / 9.0).max(axis=(1, 2))


def cell_dists(cell: np.ndarray, refs: np.ndarray) -> np.ndarray:
    """To each template: the largest local (3 x 3) mean |difference|, the least over +/- SCORE_SHIFT px."""
    best = np.full(refs.shape[0], np.inf)
    for dy in range(-SCORE_SHIFT, SCORE_SHIFT + 1):
        for dx in range(-SCORE_SHIFT, SCORE_SHIFT + 1):
            c = np.roll(np.roll(cell, dy, 0), dx, 1)
            best = np.minimum(best, _local_max(np.abs(refs - c[None])))
    return best


def read_scores(a: np.ndarray, score: dict, refs: np.ndarray) -> dict:
    """Every side's number at its place: {"scores": [..] or None (any glyph not read), "read": per side the digits
    read ('?' for a glyph not read; None when no number), "margin": the least margin of a digit read}. A digit only
    when its template is separable, the glyph within its threshold and the next template margin_needed further."""
    contrast = _contrast(a)
    keys = list(score["keys"])
    need = score.get("margin_needed")
    out, read, least = [], [], None
    for place in score["places"]:
        gl = place_glyphs(a, place, contrast)
        if gl is None:
            out.append(None)
            read.append(None)
            continue
        idx = [i for i, k in enumerate(keys) if k[:-1] == place["group"]]     # B200: its own group only ("" is
        digs = ""                                                             # no longer every key's prefix)
        for g in gl:
            if not idx:
                digs += "?"
                continue
            d = cell_dists(glyph_cell(a, g, place), refs[idx])
            order = np.argsort(d, kind="stable")
            best = keys[idx[int(order[0])]]
            margin = float(d[order[1]] - d[order[0]]) if len(idx) > 1 else float("inf")
            thr = score["thresholds"].get(best)
            ok = (score["separable"].get(best) and thr is not None and float(d[order[0]]) <= thr and need is not None
                  and margin >= need)
            digs += best[len(place["group"]):] if ok else "?"
            if ok and len(idx) > 1:
                least = margin if least is None else min(least, margin)
        read.append(digs)
        out.append(Drawn(digs) if digs and "?" not in digs else None)        # B200: as drawn ("03": 3)
    return {"scores": None if None in out else out, "read": read,
            "margin": round(least, 4) if least is not None else None}


def _digit_stats(cells: dict, shown: dict) -> tuple:
    """B178's templates, thresholds and margin from {key: [cells]} -> (keys, refs, gaps, need, noise, smallest)."""
    empty = np.zeros((0, SCORE_CELL[0] + 2, SCORE_CELL[1] + 2), np.float32)
    keys = sorted(cells)
    refs = np.stack([np.mean(cells[k], axis=0) for k in keys]).astype(np.float32) if keys else empty
    own_of = {k: max(float(cell_dists(c, refs[i:i + 1])[0]) for c in cells[k]) for i, k in enumerate(keys)}
    noise = max([own_of[k] for k in keys if shown.get(k, 0) >= 2] or [0.0])     # one digit from save to save
    gaps, margins = {}, []
    for i, k in enumerate(keys):
        grp = k[:-1]
        same = [j for j, k2 in enumerate(keys) if k2[:-1] == grp]
        own = max(own_of[k], noise)
        foreign = [float(cell_dists(c, refs[i:i + 1])[0]) for j in same if j != i for c in cells[keys[j]]]
        gaps[k] = _gap(own, min(foreign), MIN_GAP) if foreign else {
            "worst_own": round(own, 4), "best_foreign": None, "gap": None, "threshold": None,
            "verdict": "no other digit to tell it from"}
        for c in cells[k]:
            d = cell_dists(c, refs[same])
            order = np.argsort(d, kind="stable")
            if same[int(order[0])] == i and len(same) > 1:
                margins.append(float(d[order[1]] - d[order[0]]))
    need = round(SAFETY * min(margins), 4) if margins else None
    return keys, refs, gaps, need, noise, (round(min(margins), 4) if margins else None)


def _stat_score(keys, gaps, need) -> dict:
    return {"keys": keys, "thresholds": {k: gaps[k]["threshold"] for k in keys},
            "separable": {k: gaps[k]["verdict"] == "separable" for k in keys}, "margin_needed": need}


def _read_digits(a: np.ndarray, gl: list, place: dict, score: dict, refs: np.ndarray) -> str:
    """The glyphs at a place read as digits ('?' for one not read) — B178's rule."""
    keys = list(score["keys"])
    idx = [i for i, k in enumerate(keys) if k[:-1] == place["group"]]         # B200: its own group only
    need = score.get("margin_needed")
    digs = ""
    for g in gl:
        if not idx:
            digs += "?"
            continue
        d = cell_dists(glyph_cell(a, g, place), refs[idx])
        order = np.argsort(d, kind="stable")
        best = keys[idx[int(order[0])]]
        margin = float(d[order[1]] - d[order[0]]) if len(idx) > 1 else float("inf")
        thr = score["thresholds"].get(best)
        ok = (score["separable"].get(best) and thr is not None and float(d[order[0]]) <= thr and need is not None
              and margin >= need)
        digs += best[len(place["group"]):] if ok else "?"
    return digs


def read_columns(a: np.ndarray, score: dict, refs: np.ndarray) -> list[list]:
    """B181: every learnt line-score column, per side: its number read, "_" when the cell is blank, "?"-holding text
    when a glyph is not read, None for a column with no place."""
    contrast = _contrast(a)
    out = []
    for k, cols in enumerate(score.get("columns") or []):
        row = []
        for pl in cols:
            if pl is None:
                row.append(None)
                continue
            gl = place_glyphs(a, pl, contrast)
            if gl is None:
                row.append("_")
                continue
            digs = _read_digits(a, gl, pl, score, refs)
            row.append(Drawn(digs) if "?" not in digs else digs)
        out.append(row)
    return out


def save_glyphs(score: dict, nums: list, lines: list, paths: list) -> list[tuple]:
    """B186: every labelled glyph of one save at the spec's places and columns, in every picture given ->
    [(picture index, where — "<side>" or "<side>.<column>" — , glyph index, key, cell)]. A number whose glyphs do
    not fit its place is left out (as the learner's own `gather`)."""
    out = []
    for pi, path in enumerate(paths):
        with Image.open(path) as im:
            a = score_picture(im)
        contrast = _contrast(a)
        spots = [(p, nums[k], f"{k + 1}") for k, p in enumerate(score["places"])]
        spots += [(pl, lines[k][c], f"{k + 1}.{c + 1}") for k, row in enumerate(score.get("columns") or [])
                  for c, pl in enumerate(row) if pl is not None and k < len(lines) and c < len(lines[k])
                  and lines[k][c] is not None]
        for pl, v, where in spots:
            gl = place_glyphs(a, pl, contrast)
            if gl is None or len(gl) != len(str(v)):
                continue
            for i, (ch, g) in enumerate(zip(str(v), gl)):
                out.append((pi, where, i, pl["group"] + ch, glyph_cell(a, g, pl)))
    return out


def read_glyph_with(others: dict, shown: dict, key: str, own: list, cell: np.ndarray) -> str:
    """B186: one glyph read by templates learnt from `others` ({key: [cells]}, the other saves' glyphs; `shown`: how
    many saves show each key) and `own` (its own save's other glyphs of `key`, never the glyph itself), by B178's own
    rule (`_digit_stats`: thresholds, margin) -> the digit read, or "?"."""
    cells = {k: list(v) for k, v in others.items() if k != key}
    if not own:
        return "?"
    cells[key] = list(own)
    sh = {k: v for k, v in shown.items() if k != key}
    sh[key] = 1
    keys, refs, gaps, need, _noise, _small = _digit_stats(cells, sh)
    score = _stat_score(keys, gaps, need)
    group = key[:-1]
    idx = [i for i, k in enumerate(keys) if k[:-1] == group]
    d = cell_dists(cell, refs[idx])
    order = np.argsort(d, kind="stable")
    best = keys[idx[int(order[0])]]
    margin = float(d[order[1]] - d[order[0]]) if len(idx) > 1 else float("inf")
    thr = score["thresholds"].get(best)
    ok = (score["separable"].get(best) and thr is not None and float(d[order[0]]) <= thr and need is not None
          and margin >= need)
    return best[len(group):] if ok else "?"


def spread_across_within(glyphs: dict) -> tuple:
    """B186: {save: [(key, cell)]} (one picture of each save) -> (the largest distance between two glyphs of one key
    from two saves, the largest within one save, pairs across, pairs within), over the keys two saves show; None for a
    side with no pair."""
    by: dict = {}
    for save, gs in glyphs.items():
        for key, cell in gs:
            by.setdefault(key, []).append((save, cell))
    across, within, na, nw = None, None, 0, 0
    for key, gs in by.items():
        if len({s_ for s_, _c in gs}) < 2:
            continue
        for i, (sa, ca) in enumerate(gs):
            for sb, cb in gs[i + 1:]:
                dd = float(cell_dists(ca, cb[None])[0])
                if sa == sb:
                    within, nw = (dd if within is None else max(within, dd)), nw + 1
                else:
                    across, na = (dd if across is None else max(across, dd)), na + 1
    return (None if across is None else round(across, 4), None if within is None else round(within, 4), na, nw)


def _clusters(points: list) -> list:
    """Anchors within 2 x SCORE_TOL of a cluster's first are one cluster; left to right."""
    out: list = []
    for x, item in sorted(points, key=lambda t: t[0]):
        if out and x - out[-1][0] <= 2 * SCORE_TOL:
            out[-1][1].append(item)
        else:
            out.append([x, [item]])
    return out


def _centre(p_: dict) -> tuple[float, float]:
    return (p_["x0"] + p_["x1"]) / 2.0, (p_["top"] + p_["bot"]) / 2.0


def _nearest_own(pl: dict, own: dict | None, finals: list) -> bool:
    """B204: an off-line column is its side's when it is no farther from that side's final than from any other's."""
    if own is None:
        return True
    cx, cy = _centre(pl)
    dist = lambda f: ((_centre(f)[0] - cx) ** 2 + (_centre(f)[1] - cy) ** 2) ** 0.5
    return all(dist(own) <= dist(f) for f in finals if f is not own)


def _offline_column(first: dict, want: dict, taken: list, own: dict | None = None,
                    finals: list | None = None) -> tuple[list, list]:
    """B200: a filled column with no place on its final's line, looked for anywhere on the picture as a final is: a
    string with as many glyphs as each save's cell is drawn with, at one place in every save that fills it, its shapes
    explained by the labels, overlapping no place already taken, no number there in a save whose cell is blank. ->
    (its candidates, best first: [(how well its glyphs fit their labels — `_agreement` — , place, explained only
    with a save left out)], or [] and the saves where it breaks)."""
    fill = sorted(r for r in want if want[r] is not None)
    blank = [r for r in want if want[r] is None]

    excused: list = []

    def ok(pl):
        if any(_overlap(pl, t) for t in taken) or not _nearest_own(pl, own, finals or []):
            return False, []
        if any(place_glyphs(first[r], pl) is not None for r in blank):
            return False, blank
        cells = _shape_cells(first, pl, {r: want[r] for r in fill})
        got = _shapes_explained(cells) if cells is not None else (False, [])
        if got[0] and got[1] == ["excused"]:
            excused.append(pl)
        return got[0], ([] if got[0] else got[1])
    found, miss = _find_place({r: score_strings(first[r]) for r in fill}, {r: len(str(want[r])) for r in fill}, ok)
    fits = [(_agreement([pl], {r: first[r] for r in fill}, {r: [want[r]] for r in fill}), i, pl)
            for i, pl in enumerate(found)]
    fits = sorted((f for f in fits if f[0] is not None),       # one the labels explain with no save excused first
                  key=lambda f: (any(f[2] is e for e in excused), round(f[0], 4), f[1]))
    if not fits:
        return [], (miss if not found else fill)
    return [(round(f[0], 4), {**f[2], "align": "centre", "offline": True}, any(f[2] is e for e in excused))
            for f in fits], []


def _before(a: dict, b: dict) -> bool:
    """B200: place a is drawn after place b in reading order (a row lower, or the same row further right)."""
    if abs(a["top"] - b["top"]) <= SCORE_TOL:
        return a["x0"] < b["x0"]
    return a["top"] < b["top"]


def _choose_offline(cands: dict) -> dict:
    """B200: a side's off-line columns chosen together — none overlapping another, the periods in the order they are
    drawn (a later column never before an earlier one in reading order) first, then the fewest explained only with a
    save left out, then the glyphs' fit summed, then each column's own order. B204: each column weighs as many
    candidates as the side has off-line columns (at least SCORE_CHOICES), searched depth first, overlaps pruned.
    {column: candidates} -> {column: place} (empty when no choice holds)."""
    cols = sorted(cands)
    cap = max(SCORE_CHOICES, len(cols))
    best = [None]

    def walk(i: int, combo: list) -> None:
        if i == len(cols):
            pls = [x[1] for x in combo]
            out_of_order = sum(1 for a_ in range(len(pls)) for b_ in range(a_ + 1, len(pls)) if _before(pls[b_], pls[a_]))
            key = (out_of_order, sum(1 for x in combo if x[2]), round(sum(x[0] for x in combo), 4),
                   [cands[c].index(x) for c, x in zip(cols, combo)])
            if best[0] is None or key < best[0][0]:
                best[0] = (key, {c: dict(x[1]) for c, x in zip(cols, combo)})
            return
        for x in cands[cols[i]][:cap]:
            if not any(_overlap(x[1], y[1]) for y in combo):
                walk(i + 1, combo + [x])
    walk(0, [])
    return best[0][1] if best[0] else {}


def _find_columns(first: dict, saves: dict, k: int, fin: dict, score1: dict, refs1: np.ndarray,
                  taken: list | None = None, finals: list | None = None) -> tuple:
    """B181: side k's line-score columns, left to right, on its final's line (section B181 of the design). ->
    ([place or None per column], {column: the saves where it breaks} for a labelled column with no place). B200: a
    place whose shapes its labels do not explain is never taken; a column with no place on the line is looked for off
    it (`_offline_column`; `taken`: the places already taken, every side's)."""
    taken = list(taken or [])
    runs = sorted(first)
    ncol = len(saves[runs[0]][1][k])
    row = {r: [s_ for s_ in score_strings(first[r]) if s_["pol"] == fin["pol"] and s_["r"] == fin["r"]
               and abs(s_["top"] - fin["top"]) <= SCORE_TOL and abs(s_["bot"] - fin["bot"]) <= SCORE_TOL
               and s_["x1"] < fin["x0"]] for r in runs}
    clusters = _clusters([((s_["x0"] + s_["x1"]) / 2.0, (r, s_)) for r in runs for s_ in row[r]])
    need = score1.get("margin_needed")
    cols, broken, prev = [], {}, None
    off: dict = {}                                            # B200: the off-line columns' candidates
    for c in range(ncol):
        want = {r: saves[r][1][k][c] for r in runs}
        if all(v is None for v in want.values()):
            cols.append(None)
            continue
        valid, cover = [], (-1, runs)
        for cx, members in clusters:
            if prev is not None and cx <= prev or cx >= fin["x0"]:
                continue
            by = {}
            for r, s_ in members:
                by.setdefault(r, []).append(s_)
            miss = [r for r in runs if (want[r] is None) != (r not in by)
                    or (want[r] is not None and not any(s_["n"] == len(str(want[r])) for s_ in by[r]))]
            if miss:
                if len(runs) - len(miss) > cover[0]:
                    cover = (len(runs) - len(miss), miss)
                continue
            got = [s_ for r in runs if want[r] is not None for s_ in by[r] if s_["n"] == len(str(want[r]))]
            pl = {"pol": fin["pol"], "r": fin["r"], "align": "centre", "group": fin["group"], "top": fin["top"],
                  "bot": fin["bot"], "x0": int(min(g["x0"] for g in got)), "x1": int(max(g["x1"] for g in got))}
            if any(_overlap(pl, t) for t in taken):           # B200: another side's final on the same line
                continue
            glyphs, agree, ok = [], 0, True
            for r in runs:
                if want[r] is None:
                    continue
                gl = place_glyphs(first[r], pl)
                if gl is None or len(gl) != len(str(want[r])):
                    ok = False
                    break
                read = _read_digits(first[r], gl, pl, score1, refs1) if len(refs1) else ""
                agree += sum(1 for a_, b_ in zip(read, str(want[r])) if a_ == b_)
                glyphs += [(ch, glyph_cell(first[r], g, pl)) for ch, g in zip(str(want[r]), gl)]
            if ok and need is not None:                       # a separator: the same glyph whatever the label
                ok = not any(a_[0] != b_[0] and float(cell_dists(a_[1], b_[1][None])[0]) < need
                             for i, a_ in enumerate(glyphs) for b_ in glyphs[i + 1:])
            if ok:                                            # B200: not one shape whatever the label
                ok = _shapes_explained(_shape_cells(first, pl, want) or [])[0]
            if ok:
                valid.append((cx, agree, pl))
        if not valid:                                         # B200: off the final's line
            got, miss = _offline_column(first, want, taken + [p_ for p_ in cols if p_ is not None], fin, finals)
            if got:
                off[c] = got
                cols.append(None)                             # chosen with the side's other off-line columns
                continue
            broken[str(c + 1)] = [Path(r).name for r in (cover[1] if cover[0] >= 0 else miss or runs)]
            cols.append(None)
            continue
        done = [((p_["x0"] + p_["x1"]) / 2.0, i) for i, p_ in enumerate(cols) if p_ is not None and not p_.get("offline")]
        if len(done) >= 2:                                    # the place the other columns' spacing predicts
            (x_a, i_a), (x_b, i_b) = done[-2], done[-1]
            guess = x_b + (x_b - x_a) / (i_b - i_a) * (c - i_b)
        else:
            guess = None
        best = min(valid, key=lambda v: (-v[1], abs(v[0] - guess) if guess is not None else 0.0, v[0]))
        cols.append(best[2])
        prev = best[0]
    if off:                                                   # B200: the side's off-line columns, together
        line = [p_ for p_ in cols if p_ is not None]
        off = {c: [x for x in v if not any(_overlap(x[1], q) for q in line)] for c, v in off.items()}
        chosen = _choose_offline(off) if all(off.values()) else {}
        for c in sorted(off):
            if c in chosen:
                cols[c] = chosen[c]
            else:
                broken[str(c + 1)] = [Path(r).name for r in runs]
    return cols, broken


SIZES_PER_DIGIT = 12             # B204: the glyphs of one digit and one size weighed (the first, in save order)


def _one_font(cells: dict, fg: str, og: str) -> tuple[bool, float | None, float | None]:
    """B204: whether a group of another size is the score's own font — every pair of one digit across the two groups
    (the digits both show) nearer than every pair of two digits (either group). {key: [cells]} -> (counted, the
    farthest one-digit pair across sizes, the nearest two-digit pair); not counted when no digit is in both."""
    def own(g):
        return {k[-1]: v[:SIZES_PER_DIGIT] for k, v in cells.items() if k[:-1] == g}
    a, b = own(fg), own(og)
    both = sorted(set(a) & set(b))
    if not both:
        return False, None, None
    same = max(float(cell_dists(x, y[None])[0]) for d in both for x in a[d] for y in b[d])
    glyphs = [(d, c) for grp in (a, b) for d, v in grp.items() for c in v]
    two = min(float(cell_dists(x, y[None])[0]) for i, (d1, x) in enumerate(glyphs) for d2, y in glyphs[i + 1:]
              if d1 != d2) if len({d for d, _c in glyphs}) > 1 else None
    return (two is not None and same < two), round(same, 4), (round(two, 4) if two is not None else None)


def learn_scores(saves: dict) -> tuple[dict, dict, dict]:
    """From {save: (its finals, its line-score cells per side, [its pictures])} -> (the spec's `score`, its arrays, a
    report): each side's final's place (the same in every save), B181's line-score columns, each digit's template,
    threshold and the margin needed (section B178 of the docstring)."""
    runs = sorted(saves)
    n = len(saves[runs[0]][0])
    first = {}
    for r in runs:
        with Image.open(saves[r][2][0]) as im:
            first[r] = score_picture(im)
    strs = {r: score_strings(first[r]) for r in runs}
    cands, broken = [], {}
    for k in range(n):
        want = {r: saves[r][0][k] for r in runs}

        def ok(pl, want=want):                                # B200: the labels explain the place's shapes
            cells = _shape_cells(first, pl, want)
            return _shapes_explained(cells) if cells is not None else (False, [])
        found, miss = _find_place(strs, {r: len(str(saves[r][0][k])) for r in runs}, ok)
        if not found:
            broken[str(k + 1)] = [Path(r).name for r in miss]
        cands.append(found)
    places = [] if broken else _choose_places(cands, first, {r: saves[r][0] for r in runs})
    if not broken and not places:
        broken = {"all": ["the sides' places overlap"]}
    ncols = {k: {len(saves[r][1][k]) for r in runs} for k in range(n)}
    for k, sizes in ncols.items():                            # B181: every save the same columns per side
        if len(sizes) > 1:
            most = max(sizes, key=lambda z: (sum(1 for r in runs if len(saves[r][1][k]) == z), z))
            broken[f"{k + 1}.cells"] = [Path(r).name for r in runs if len(saves[r][1][k]) != most]
    empty = np.zeros((0, SCORE_CELL[0] + 2, SCORE_CELL[1] + 2), np.float32)
    base = {"sides": n, "places": places, "keys": [], "thresholds": {}, "separable": {}, "margin_needed": None,
            "pooled": False, "cell": list(SCORE_CELL), "columns": []}
    if broken:
        return {**base, "found": False, "not_found": broken}, {"digit_refs": empty}, {"found": False, "not_found": broken}
    heights = [p["bot"] - p["top"] for p in places]
    pooled = max(heights) - min(heights) <= SCORE_TOL
    for k, p in enumerate(places):
        p["group"] = "" if pooled else f"{k + 1}:"

    def gather(cols: list) -> tuple[dict, dict, dict]:
        cells: dict[str, list] = {}
        unfit: dict = {}
        for r in runs:
            nums, lines, paths = saves[r]
            for path in paths:
                with Image.open(path) as im:
                    a = score_picture(im)
                contrast = _contrast(a)
                spots = [(p, nums[k], f"{k + 1}") for k, p in enumerate(places)]
                spots += [(pl, lines[k][c], f"{k + 1}.{c + 1}") for k, row in enumerate(cols)
                          for c, pl in enumerate(row) if pl is not None and lines[k][c] is not None]
                for pl, v, where in spots:
                    gl = place_glyphs(a, pl, contrast)
                    if gl is None or len(gl) != len(str(v)):
                        unfit.setdefault(Path(r).name, set()).add(where)
                        continue
                    for ch, g in zip(str(v), gl):
                        cells.setdefault(pl["group"] + ch, []).append(glyph_cell(a, g, pl))
        shown = {}
        for r in runs:
            nums, lines, _paths = saves[r]
            digs = {places[k]["group"] + ch for k in range(n)
                    for v in [nums[k]] + [x for x in lines[k] if x is not None] for ch in str(v)}
            for key in digs:
                shown[key] = shown.get(key, 0) + 1
        return cells, unfit, shown

    cells, unfit, shown = gather([])                          # the finals alone first (B178)
    keys, refs, gaps, need, noise, small = _digit_stats(cells, shown)
    columns, cbroken, sizes = [], {}, None
    if any(saves[r][1][k] for r in runs for k in range(n)):   # B181: the line score's columns
        score1 = _stat_score(keys, gaps, need)
        for k in range(n):
            taken = places + [p_ for row in columns for p_ in row if p_ is not None]
            cols, br = _find_columns(first, saves, k, places[k], score1, refs, taken, places)
            columns.append(cols)
            for c, who in br.items():
                cbroken[f"{k + 1}.{c}"] = who
        def hgt(p_):
            return p_["bot"] - p_["top"]
        other = [(k, p_) for k, row in enumerate(columns) for p_ in row          # B200: an off-line column of
                 if p_ is not None and p_.get("offline") and abs(hgt(p_) - hgt(places[k])) > SCORE_TOL]   # another size
        one = bool(other) and max(hgt(p_) for _k, p_ in other) - min(hgt(p_) for _k, p_ in other) <= SCORE_TOL
        for k, row in enumerate(columns):                     # one of the final's size: the final's glyphs
            for p_ in row:
                if p_ is not None and p_.get("offline"):
                    p_["group"] = places[k]["group"]
        for k, p_ in other:                                   # ... another size: its own glyphs
            p_["group"] = "c:" if one else f"c{k + 1}:"
        if cbroken:
            return ({**base, "found": False, "not_found": cbroken, "pooled": pooled, "columns": columns},
                    {"digit_refs": empty}, {"found": False, "not_found": cbroken})
        cells, unfit, shown = gather(columns)                 # then every labelled number
        fgs = {p_["group"] for p_ in places}
        ogs = {p_["group"] for row in columns for p_ in row if p_ is not None} - fgs
        if pooled and len(fgs) == 1 and ogs:                  # B204: another size, the score's font or not
            fg = fgs.pop()
            sizes = {}
            for og in sorted(ogs):
                one, same, two = _one_font(cells, fg, og)
                sizes[og] = {"counted": one, "one digit across sizes, farthest": same,
                             "two digits, nearest": two}
                if one:
                    for row in columns:
                        for p_ in row:
                            if p_ is not None and p_["group"] == og:
                                p_["group"] = fg
            if any(v["counted"] for v in sizes.values()):
                cells, unfit, shown = gather(columns)
        keys, refs, gaps, need, noise, small = _digit_stats(cells, shown)
    score = {**base, "found": True, "pooled": pooled, **_stat_score(keys, gaps, need), "columns": columns,
             **({"sizes": sizes} if sizes else {}),
             "glyphs": {k: len(cells[k]) for k in keys}, "saves_showing": shown, "noise": round(noise, 4),
             "unfit": {r: sorted(v) for r, v in sorted(unfit.items())}}
    report = {"found": True, "places": places, "columns": columns, "digits": gaps, "margin_needed": need,
              "smallest_margin_seen": small, "unfit": score["unfit"]}
    return score, {"digit_refs": refs}, report


def _learn_v4(paths, ids, per_source, aspect, start_class, name, n, t0):
    """B178: the screens as version 3 (start, end — every score class merged), then each side's number on the end
    screen."""
    frames: dict[str, list[np.ndarray]] = {}
    saves: dict[str, tuple] = {}
    for c, ps in paths.items():
        key = END if SCORE_LABEL.match(c) else c
        frames.setdefault(key, [])
        for p in ps:
            with Image.open(p) as im:
                frames[key].append(_final(mid(im)))
            if key == END:
                saves.setdefault(str(Path(p).parent), (score_numbers(c), score_cells(c), []))[2].append(p)
    for c in (start_class, END, OTHER):
        if not frames.get(c):
            raise ValueError(f"the labels name no {c} frames")
    st = {c: np.stack(v).astype(np.float32) for c, v in frames.items()}
    screens, arrays = {}, {}
    for c, other_screen in ((start_class, END), (END, start_class)):
        mask, ref, gap = _learn_one_screen(st[c], [st[OTHER], st[other_screen]])
        screens[c] = gap
        arrays[f"{c}_mask"], arrays[f"{c}_ref"] = mask, ref
    score, sarrays, sreport = learn_scores(saves)
    arrays.update(sarrays)
    usable = (all(g["threshold"] is not None for g in screens.values()) and score["found"]
              and bool(score["keys"]) and score["margin_needed"] is not None)
    spec = {
        "version": VERSION_SCORE, "kind": "privyhub-h7-endscreen", "measure": MEASURE, "size": list(SIZE),
        "aspect": round(float(aspect), 5), "classes": [start_class, END], "start_class": start_class,
        "end_classes": [END], "screens": {c: {"threshold": g["threshold"], "own_worst": g["worst_own"],
                                              "mask_px": g["mask_px"]} for c, g in screens.items()},
        "score": score, "usable": usable, "steady_r": STEADY_R, "shared_near": SHARED_NEAR,
        "shared_share": SHARED_SHARE, "tol": TOL, "quant": 1.0 / QUANT, "flat": FLAT, "bar_max": BAR_MAX,
        "bar_share": BAR_SHARE, "k": K, "search_every_s": SEARCH_EVERY,
        "search": {"coarse_scales": list(COARSE_SCALES), "coarse_shifts_px_320": list(COARSE_SHIFTS),
                   "fine_scale": FINE_SCALE, "fine_shift_px_320": FINE_SHIFT},
        "score_size": list(SCORE_SIZE), "score_ink": SCORE_INK, "score_tol": SCORE_TOL,
        "frames": {c: len(v) for c, v in frames.items()},
        "arrays": f"{name}.endscreen.npz" if name else None, "arrays_sha256": None,
    }
    if len(per_source) > 1:
        spec["frames_per_source"] = per_source
    report = {"measure": MEASURE, "frames_per_class": spec["frames"], "screens": screens, "score": sreport,
              "usable": usable, "learn_s": round(time.perf_counter() - t0, 2)}
    return spec, arrays, report


# --- B191 / B192: a word spelled by the player who lost (spec version 5) ---------------------------------------------
VERSION_LETTERS = 5
LETTERS_SIDE = re.compile(r"^(?:[A-Z-]{1,12}|_)$")    # a corner as read: its letters, '-' a not-yet mark, '_' nothing
LETTERS_WORD = re.compile(r"^[A-Z]{2,12}$")
LETTERS_SIZE = (640, 480)        # the corners are read on the game's area at this size, in colour
LETTERS_EQ = 12                  # levels (the largest channel): a pixel the same in two saves
LETTERS_DIFFER = 0.5             # two saves are different pictures when fewer than this share of their pixels is the same
LETTERS_FLAT, LETTERS_FLAT_DIST, LETTERS_QF = 0.5, 48, 16   # a plain corner: this share within this of its commonest colour
LETTERS_FILL = 150               # R+G+B: under this a pixel is the letters' shadow (dark backgrounds share it)
LETTERS_PART = 6                 # px: a glyph's part
LETTERS_TOUCH = 1                # px: parts this close in x are one glyph
LETTERS_SPECK = 0.4              # a glyph under this share of the smallest labelled glyph's pixels is a speck
LETTERS_NB = 32                  # chromaticity bins per axis (r, g of r+g+b)
LETTERS_VMIN = 90                # R+G+B: darker pixels have no colour
LETTERS_TMIN = 0.002             # a colour is the letters' only when at least this share of their pixels
LETTERS_RATIOS = (5, 10, 20, 40)  # ... and this many times as common among them as among the backgrounds (the least
#                                  that reads every real save and every held-out synthetic picture)
LETTERS_PAD = 8                  # px around a corner's box
LETTERS_PLACE_TOL = 8            # px: two saves' strings at one place
LETTERS_FIXED = 0.9              # a string whose cut pixels stay this much the same under other letters is fixed text
LETTERS_FOUND_PX = 20            # px: each glyph of a string found by the cut at least this (a speck is not a letter)
LETTERS_CELL = (36, 40)          # a glyph's window (no resizing: one font size in a title)
LETTERS_SHIFT = 3                # px: a glyph compared within +/- this
LETTERS_CORNER = (200, 70)       # B137's LABEL_BOX: RetroArch's "Paused." corner, black for the start test
LETTERS_MOVED = (16, 0.20)       # B140's BEGIN_MOVED bar: >= 20 % of the 64 x 48 cells moved by > 16 levels (in colour:
#                                  the largest channel)
SYN_HELD, SYN_PER_ROUND, SYN_ROUNDS = 8, 16, 4        # B192: per end save: held out, added a round; rounds at most
SYN_SCALE, SYN_SHIFT = (1.0, 1.4), 2
SYN_OWN = 0.85                   # a training glyph teaches its letter's shape only when this share of it is pasted letter


def letters_area(img: Image.Image) -> np.ndarray:
    """The game's area in colour at LETTERS_SIZE (B104's bar cut)."""
    return np.asarray(game_area(img.convert("RGB")).resize(LETTERS_SIZE, Image.BILINEAR), dtype=np.float32)


def corner_black(img: Image.Image) -> Image.Image:
    """B137's corner painted black (the start test's picture, paused or not)."""
    out = img.convert("RGB").copy()
    w = out.size[0]
    out.paste((0, 0, 0), (max(0, w - LETTERS_CORNER[0]), 0, w, min(out.size[1], LETTERS_CORNER[1])))
    return out


def letters_zones(n: int) -> dict:
    """The corners each player's letters are looked for in: P1 the left third, P2 the right third; top and bottom."""
    w, h = LETTERS_SIZE[0] // 3, LETTERS_SIZE[1] // 3
    W, H = LETTERS_SIZE
    return {1: [(0, 0, w, h), (0, H - h, w, H)], 2: [(W - w, 0, W, h), (W - w, H - h, W, H)]}


def _lparts(m: np.ndarray) -> list:
    return [c for c in _components(m) if c[4] >= LETTERS_PART]


def _merge_touch(cs: list) -> list:
    """Reading a corner: parts overlapping in x, or touching (a gap of at most LETTERS_TOUCH px), are one glyph; left
    to right. (A letter's thin join can be lost to the colour cut; a font's letters stand further apart: T91's 3 px
    and more.) The corner search keeps B178's overlap rule: there the cut's shadows would join letters."""
    gl: list = []
    for c in sorted(cs, key=lambda c: (c[1], c[0])):
        if gl and c[1] <= gl[-1][3] + 1 + LETTERS_TOUCH:
            g = gl[-1]
            gl[-1] = (min(g[0], c[0]), g[1], max(g[2], c[2]), max(g[3], c[3]), g[4] + c[4])
        else:
            gl.append(c)
    return gl


def letter_strings(m: np.ndarray, x0: int = 0, y0: int = 0) -> list:
    """Strings of glyphs: parts on one line (their spans overlap by half the smaller), parts overlapping in x one glyph,
    a string split where the gap is wider than a glyph (at least 12 px)."""
    lines: list = []
    for c in sorted(_lparts(m), key=lambda c: -(c[2] - c[0])):
        for ln in lines:
            if min(ln[1], c[2]) - max(ln[0], c[0]) >= 0.5 * min(ln[1] - ln[0], c[2] - c[0]):
                ln[2].append(c)
                ln[0], ln[1] = min(ln[0], c[0]), max(ln[1], c[2])
                break
        else:
            lines.append([c[0], c[2], [c]])
    out = []
    for _t, _b, grp in lines:
        gl = _merge_x(grp)                                # the search: overlapping parts only
        cur = [gl[0]]
        for g in gl[1:]:
            if g[1] - cur[-1][3] - 1 <= max(12, cur[-1][2] - cur[-1][0]):
                cur.append(g)
            else:
                out.append(cur)
                cur = [g]
        out.append(cur)
    return [[(t + y0, l + x0, b + y0, r + x0, n) for t, l, b, r, n in s] for s in out]


def _cue(A: dict, sides: dict, p: int, e: str, zone, fixed: np.ndarray) -> np.ndarray:
    """B191's cut in one corner of one save: the pixels the same in another save showing this player's same letters
    over a different picture, and the pixels off a plain corner's commonest colour; never a dark one. (The end
    screens' fixed text is left to the string search: a string of the side's length, at one place in the most saves.)"""
    x0, y0, x1, y1 = zone
    m = np.zeros((y1 - y0, x1 - x0), bool)
    for f in A:
        if f == e or sides[f][p] != sides[e][p]:
            continue
        eq = np.abs(A[e] - A[f]).max(axis=2) <= LETTERS_EQ
        if eq.mean() < LETTERS_DIFFER:
            m |= eq[y0:y1, x0:x1]
    a = A[e][y0:y1, x0:x1]
    q = (a // LETTERS_QF).astype(np.int64)
    k = q[..., 0] * 256 + q[..., 1] * 16 + q[..., 2]
    u, cnt = np.unique(k, return_counts=True)
    mode = int(u[np.argmax(cnt)])
    mc = (np.array([mode // 256, mode // 16 % 16, mode % 16]) + 0.5) * LETTERS_QF
    far = np.abs(a - mc).max(axis=2) > LETTERS_FLAT_DIST
    if (~far).mean() >= LETTERS_FLAT:
        m |= far
    del fixed                    # not excluded: where two saves' letters overlap in one colour it would cut the letters
    return m & (a.sum(axis=2) >= LETTERS_FILL)


def letters_colour(a: np.ndarray) -> np.ndarray:
    """Each pixel's chromaticity bin (r, g of r+g+b, LETTERS_NB each); -1 for a pixel too dark to have a colour."""
    s = a.sum(axis=2) + 1e-6
    r = np.clip((a[..., 0] / s * LETTERS_NB).astype(np.int64), 0, LETTERS_NB - 1)
    g = np.clip((a[..., 1] / s * LETTERS_NB).astype(np.int64), 0, LETTERS_NB - 1)
    k = r * LETTERS_NB + g
    k[s < LETTERS_VMIN] = -1
    return k


def _lhist(k: np.ndarray) -> np.ndarray:
    k = k[k >= 0]
    return np.bincount(k, minlength=LETTERS_NB * LETTERS_NB).astype(np.float64)


def letters_bins(text: np.ndarray, bg: np.ndarray, ratio: float) -> np.ndarray:
    """A colour is the letters' when it is at least LETTERS_TMIN of their pixels and `ratio` x as common among them as
    among the backgrounds' pixels."""
    tt, bb = text / max(float(text.sum()), 1.0), bg / max(float(bg.sum()), 1.0)
    return (tt >= LETTERS_TMIN) & (tt >= ratio * bb)


def letters_mask(a: np.ndarray, box, bins: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = box
    k = letters_colour(a[y0:y1, x0:x1])
    m = np.zeros(k.shape, bool)
    m[k >= 0] = bins[k[k >= 0]]
    return m


def letters_glyphs(a: np.ndarray, box, bins: np.ndarray, glyph_min: float, want: int | None = None) -> tuple:
    """The box's glyphs in its own coordinates, left to right (parts overlapping in x one glyph; specks dropped). When
    that is not `want` glyphs, parts touching in x are joined too (`_merge_touch`), and taken only if that is `want`."""
    m = letters_mask(a, box, bins)
    parts = _lparts(m)
    gl = [g for g in _merge_x(parts) if g[4] >= glyph_min]
    if want is not None and len(gl) != want:
        gt = [g for g in _merge_touch(parts) if g[4] >= glyph_min]
        if len(gt) == want:
            gl = gt
    return m, gl


def letter_cell(m: np.ndarray, g) -> np.ndarray:
    """The glyph's pixels (its own box only) in a LETTERS_CELL window on its centre."""
    ch, cw = LETTERS_CELL
    t, l, b, r = g[0], g[1], g[2], g[3]
    sub = np.zeros(m.shape, np.float32)
    sub[t:b + 1, l:r + 1] = m[t:b + 1, l:r + 1]
    ys, xs = (t + b) // 2 - ch // 2, (l + r) // 2 - cw // 2
    out = np.zeros(LETTERS_CELL, np.float32)
    y_a, y_b = max(0, ys), min(m.shape[0], ys + ch)
    x_a, x_b = max(0, xs), min(m.shape[1], xs + cw)
    if y_b > y_a and x_b > x_a:
        out[y_a - ys:y_b - ys, x_a - xs:x_b - xs] = sub[y_a:y_b, x_a:x_b]
    return out


def _shifts(c: np.ndarray):
    p = np.pad(c, LETTERS_SHIFT)
    for dy in range(-LETTERS_SHIFT, LETTERS_SHIFT + 1):
        for dx in range(-LETTERS_SHIFT, LETTERS_SHIFT + 1):
            yield p[LETTERS_SHIFT + dy:LETTERS_SHIFT + dy + c.shape[0], LETTERS_SHIFT + dx:LETTERS_SHIFT + dx + c.shape[1]]


def letter_dists(refs: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Each template's distance to a glyph: the mean |difference|, the least over +/- LETTERS_SHIFT px."""
    best = np.full(len(refs), np.inf, np.float32)
    for sh in _shifts(c):
        best = np.minimum(best, np.abs(refs - sh[None]).mean(axis=(1, 2)))
    return best


def _aligned_mean(cs: list) -> np.ndarray:
    ref = cs[0]
    out = []
    for c in cs:
        out.append(min(_shifts(c), key=lambda sh: float(np.abs(ref - sh).mean())))
    return np.mean(out, axis=0)


def fit_letters(cells: dict) -> dict:
    """Each letter's template (its glyphs aligned and averaged), its threshold halfway from its own spread to the
    nearest other letter's glyph (separable with a gap >= MIN_GAP), margin_needed half the least margin seen."""
    keys = sorted(cells)
    if not keys:
        return {"keys": [], "refs": np.zeros((0,) + LETTERS_CELL, np.float32), "thresholds": {}, "separable": {},
                "margin_needed": None}
    refs = np.stack([_aligned_mean(cells[k]) for k in keys]).astype(np.float32)
    ds = {k: [letter_dists(refs, c) for c in cells[k]] for k in keys}
    thr, sep, margins = {}, {}, []
    for i, k in enumerate(keys):
        own = max(float(d[i]) for d in ds[k])
        foreign = min([float(d[i]) for k2 in keys if k2 != k for d in ds[k2]] or [1.0])
        g = _gap(own, foreign, MIN_GAP)
        sep[k] = g["verdict"] == "separable"
        thr[k] = g["threshold"]
        for d in ds[k]:
            if len(keys) > 1:
                margins.append(float(np.sort(d)[1] - d[i]))
    need = round(SAFETY * min(margins), 4) if margins else (0.0 if len(keys) == 1 else None)
    return {"keys": keys, "refs": refs, "thresholds": thr, "separable": sep, "margin_needed": need}


def read_corner(a: np.ndarray, box, bins: np.ndarray, fitted: dict, word: str, glyph_min: float,
                blank_ok: bool = False):
    """One corner as letters, or None (not read): as many glyphs as the word has letters (none: '_' when the title
    shows nothing there), each one letter under its threshold with the margin, and that letter the word's at its place
    or '-'. Never the nearest letter by itself."""
    m, gl = letters_glyphs(a, box, bins, glyph_min, len(word))
    if not gl:
        return "_" if blank_ok else None
    if len(gl) != len(word) or not fitted["keys"]:
        return None
    out = []
    need = fitted["margin_needed"]
    for i, g in enumerate(gl):
        dd = letter_dists(fitted["refs"], letter_cell(m, g))
        o = np.argsort(dd)
        k = fitted["keys"][int(o[0])]
        margin = float(dd[o[1]] - dd[o[0]]) if len(dd) > 1 else float("inf")
        t = fitted["thresholds"].get(k)
        if t is None or need is None or float(dd[o[0]]) > t or margin < need or k not in (word[i], "-"):
            return None
        out.append(k)
    return "".join(out)


def _letters_places(A: dict, sides: dict, word: str, n: int) -> tuple:
    """-> ({p: box}, {p: [(save, string, cut, zone)]}) or (None, why)."""
    ends = sorted(A)
    fixed = np.all([np.abs(A[e] - A[ends[0]]).max(axis=2) <= LETTERS_EQ for e in ends], axis=0) \
        if len(ends) > 1 else np.zeros(A[ends[0]].shape[:2], bool)
    found = {}
    for p in range(1, n + 1):
        cands = []
        for zone in letters_zones(n)[p]:
            for e in ends:
                want = 0 if sides[e][p - 1] == "_" else len(sides[e][p - 1])
                if not want:
                    continue
                m = _cue(A, sides, p - 1, e, zone, fixed)
                for s in letter_strings(m, zone[0], zone[1]):
                    if len(s) == want and min(g[4] for g in s) >= LETTERS_FOUND_PX:
                        cands.append((e, s, m, zone))
        clusters: list = []
        for c in cands:
            cx = (c[1][0][1] + c[1][-1][3]) / 2.0
            cy = (min(g[0] for g in c[1]) + max(g[2] for g in c[1])) / 2.0
            for cl in clusters:
                if abs(cl["cx"] - cx) <= LETTERS_PLACE_TOL and abs(cl["cy"] - cy) <= LETTERS_PLACE_TOL:
                    cl["m"].append(c)
                    break
            else:
                clusters.append({"cx": cx, "cy": cy, "m": [c]})
        def fixed_text(cl) -> bool:
            """The end screens' own text: its pixels stay the same (LETTERS_FIXED of them) in a save the session read
            other letters for this player in — letters change with the reading."""
            e, s, m, zone = cl["m"][0]
            t, b_ = min(g[0] for g in s), max(g[2] for g in s)
            l_, r_ = s[0][1], s[-1][3]
            cut = m[t - zone[1]:b_ - zone[1] + 1, l_ - zone[0]:r_ - zone[0] + 1]
            if not cut.any():
                return False
            for f in ends:
                if sides[f][p - 1] != sides[e][p - 1]:
                    eq = np.abs(A[e][t:b_ + 1, l_:r_ + 1] - A[f][t:b_ + 1, l_:r_ + 1]).max(axis=2) <= LETTERS_EQ
                    if float(eq[cut].mean()) >= LETTERS_FIXED:
                        return True
            return False
        clusters = [cl for cl in clusters if not fixed_text(cl)]
        if not clusters:
            return None, f"P{p}'s letters were found in no save"
        saves_of = lambda cl: len({c[0] for c in cl["m"]})
        clusters.sort(key=lambda cl: (-saves_of(cl), -sum(g[4] for c in cl["m"] for g in c[1])))
        if len(clusters) > 1 and saves_of(clusters[0]) == saves_of(clusters[1]):
            return None, f"P{p}'s letters were found at two places as often"
        found[p] = clusters[0]
    gw = max(g[3] - g[1] + 1 for cl in found.values() for c in cl["m"] for g in c[1])
    gh = max(g[2] - g[0] + 1 for cl in found.values() for c in cl["m"] for g in c[1])
    W, H = LETTERS_SIZE
    places = {}
    for p, cl in found.items():
        half = (len(word) * gw + (len(word) - 1) * 6) / 2.0 + LETTERS_PAD
        top = min(g[0] for c in cl["m"] for g in c[1])
        bot = max(g[2] for c in cl["m"] for g in c[1])
        if bot - top + 1 < gh:
            top, bot = (top + bot) / 2.0 - gh / 2.0, (top + bot) / 2.0 + gh / 2.0
        places[p] = [int(max(0, cl["cx"] - half)), int(max(0, top - 3)), int(min(W, cl["cx"] + half)),
                     int(min(H, bot + 4))]
    return places, found


def _corner_text(a: np.ndarray, box, bins: np.ndarray, glyph_min: float) -> np.ndarray:
    m, gl = letters_glyphs(a, box, bins, glyph_min)
    keep = np.zeros_like(m)
    for g in gl:
        keep[g[0]:g[2] + 1, g[1]:g[3] + 1] = m[g[0]:g[2] + 1, g[1]:g[3] + 1]
    return keep


def _texty(src: np.ndarray, sy: int, sx: int, ph: int, pw: int, bins: dict, glyph_min: float) -> bool:
    """A patch holding a letter-sized shape in any player's letters' colours (the game's other text)."""
    for b in bins.values():
        m = letters_mask(src, (sx, sy, sx + pw, sy + ph), b)
        if any(c[4] >= glyph_min for c in _components(m)):
            return True
    return False


def letters_seed(items: list) -> int:
    """B192: the same saves (their pictures and readings) always give the same synthetic set."""
    h = hashlib.sha256()
    for a, sides in items:
        h.update(np.ascontiguousarray(a[::8, ::8]).astype(np.uint8).tobytes())
        h.update("/".join(sides).encode())
    return int(h.hexdigest()[:8], 16)


def synthetic_letters(places: dict, bins: dict, items: list, frames: list, fixed: np.ndarray, rng, per: int,
                      cuts: list, glyph_min: float) -> list:
    """B192: each real end save's letters over other backgrounds — each corner's box given a patch cut from one of the
    title's own pictures at a random place and scale (never overlapping a letters box or the end screens' fixed text,
    never a patch holding the game's other text), the save's own letter pixels put back at their place moved by up to
    SYN_SHIFT px. -> [(picture, sides, {p: the pasted pixels})]. Training only: never read by a gate."""
    W, H = LETTERS_SIZE
    out = []
    for i, (a, sides) in enumerate(items):
        for _j in range(per):
            b = a.copy()
            pasted = {}
            for p, box in places.items():
                x0, y0, x1, y1 = box
                h, w = y1 - y0, x1 - x0
                src, sy, sx, ph, pw = frames[0], 0, 0, h, w
                for _try in range(60):
                    src = frames[int(rng.integers(len(frames)))]
                    s = float(rng.uniform(*SYN_SCALE))
                    ph, pw = max(2, int(round(h / s))), max(2, int(round(w / s)))
                    sy, sx = int(rng.integers(0, H - ph)), int(rng.integers(0, W - pw))
                    if fixed[sy:sy + ph, sx:sx + pw].any():
                        continue
                    if any(not (sx + pw <= q[0] or q[2] <= sx or sy + ph <= q[1] or q[3] <= sy) for q in places.values()):
                        continue
                    if _texty(src, sy, sx, ph, pw, bins, glyph_min):
                        continue
                    break
                patch = Image.fromarray(np.clip(src[sy:sy + ph, sx:sx + pw], 0, 255).astype(np.uint8))
                b[y0:y1, x0:x1] = np.asarray(patch.resize((w, h), Image.BILINEAR), dtype=np.float32)
                dy, dx = (int(v) for v in rng.integers(-SYN_SHIFT, SYN_SHIFT + 1, 2))
                ys, xs = np.nonzero(cuts[i][p])
                yy, xx = ys + dy, xs + dx
                ok = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
                b[yy[ok] + y0, xx[ok] + x0] = a[ys[ok] + y0, xs[ok] + x0]
                pm = np.zeros((h, w), bool)
                pm[yy[ok], xx[ok]] = True
                pasted[p] = pm
            out.append((b, list(sides), pasted))
    return out


def _letter_cells(places: dict, bins: dict, items: list, word: str, glyph_min: float) -> tuple:
    cells: dict = {}
    bad = []
    for i, it in enumerate(items):
        a, sides = it[0], it[1]
        pasted = it[2] if len(it) > 2 else None              # B192: a training picture's own letter pixels
        for p, box in places.items():
            st = sides[p - 1]
            m, gl = letters_glyphs(a, box, bins[p], glyph_min, 0 if st == "_" else len(st))
            if st == "_":
                if gl:
                    bad.append((i, p))
                continue
            if len(gl) != len(st):
                bad.append((i, p))
                continue
            for ch, g in zip(st, gl):
                if pasted is not None:                       # a glyph a background speck joined teaches no shape
                    own = m[g[0]:g[2] + 1, g[1]:g[3] + 1]
                    if own.any() and float(pasted[p][g[0]:g[2] + 1, g[1]:g[3] + 1][own].mean()) < SYN_OWN:
                        continue
                cells.setdefault(ch, []).append(letter_cell(m, g))
    return cells, bad


def _read_sides(places: dict, bins: dict, fitted: dict, word: str, glyph_min: float, blank: dict, a) -> list:
    return [read_corner(a, places[p], bins[p], fitted, word, glyph_min, blank.get(p, False)) for p in sorted(places)]


def learn_letters(starts: list, others: list, ends: dict, sides: dict, word: str, players: int, name: str = "",
                  start_class: str = START) -> tuple:
    """B191 / B192: starts / others — picture paths of the begin's and the mid-match save's screens; ends — {role:
    [picture paths]} (the label stage's two of each end save); sides — {role: [P1's corner, P2's, ...]} as the session
    read them; word — the user's. -> (spec, arrays, report). Synthetic pictures only train; nothing here proves."""
    t0 = time.perf_counter()
    if not LETTERS_WORD.match(word or ""):
        raise ValueError("the word is 2-12 letters A-Z")
    if players != 2:
        raise ValueError("a letters title has two players")
    roles = sorted(ends)
    report: dict = {"word_length": len(word), "end_saves": len(roles)}
    # the start: B122's one-screen learner on the begin's own still picture, B137's corner black
    def grey(p):
        with Image.open(p) as im:
            return _final(mid(corner_black(im)))
    st = np.stack([grey(p) for p in starts]).astype(np.float32)
    foreign = [np.stack([grey(p) for p in others]).astype(np.float32)] if others else []
    foreign.append(np.stack([grey(p) for r in roles for p in ends[r]]).astype(np.float32))
    smask, sref, sgap = _learn_one_screen(st, foreign)
    arrays = {f"{start_class}_mask": smask, f"{start_class}_ref": sref}
    # the corners
    def colour(p):
        with Image.open(p) as im:
            return letters_area(im)
    A = {r: colour(ends[r][0]) for r in roles}
    items = [(A[r], list(sides[r])) for r in roles]                      # B192: one picture of each end save
    checks = items + [(colour(p), list(sides[r])) for r in roles for p in ends[r][1:]]   # every picture read right
    frames = [colour(p) for p in list(starts[:1]) + list(others[:1])] + [A[r] for r in roles]
    places, found = _letters_places(A, sides, word, players)
    spec = {"version": VERSION_LETTERS, "kind": "privyhub-h7-endscreen", "measure": MEASURE, "size": list(SIZE),
            "classes": [start_class] + [f"end_P{k}" for k in range(1, players + 1)], "start_class": start_class,
            "end_classes": [f"end_P{k}" for k in range(1, players + 1)], "k": K,
            "screens": {start_class: {"threshold": sgap["threshold"], "own_worst": sgap["worst_own"],
                                      "mask_px": sgap["mask_px"]}},
            "letters": {"word": word, "players": players, "found": places is not None,
                        "not_found": None if places is not None else found, "size": list(LETTERS_SIZE),
                        "cell": list(LETTERS_CELL), "shift": LETTERS_SHIFT, "corner": list(LETTERS_CORNER),
                        "moved": list(LETTERS_MOVED)},
            "usable": False, "arrays": f"{name}.endscreen.npz" if name else None, "arrays_sha256": None}
    report["start"] = sgap
    if places is None:
        report["letters"] = {"not_found": found}
        report["learn_s"] = round(time.perf_counter() - t0, 2)
        return spec, arrays, report
    fixed = np.all([np.abs(A[e] - A[roles[0]]).max(axis=2) <= LETTERS_EQ for e in roles], axis=0) \
        if len(roles) > 1 else np.zeros(A[roles[0]].shape[:2], bool)
    # the colours: the found strings' pixels against every picture's pixels outside the boxes
    bg = np.zeros(LETTERS_NB * LETTERS_NB)
    for a in frames + [colour(p) for p in starts[1:2]]:
        k = letters_colour(a)
        for b in places.values():
            k[b[1]:b[3], b[0]:b[2]] = -1
        bg += _lhist(k)
    text = {}
    smallest = []
    for p, cl in found.items():
        t = np.zeros(LETTERS_NB * LETTERS_NB)
        for e, s, m, zone in cl["m"]:
            for g in s:
                sub = m[g[0] - zone[1]:g[2] - zone[1] + 1, g[1] - zone[0]:g[3] - zone[0] + 1]
                k = letters_colour(A[e][g[0]:g[2] + 1, g[1]:g[3] + 1])
                t += _lhist(np.where(sub, k, -1))
                smallest.append(g[4])
        text[p] = t
    glyph_min = max(float(LETTERS_PART), LETTERS_SPECK * float(min(smallest)))
    blank = {p: any(sides[r][p - 1] == "_" for r in roles) for p in places}
    # B192: held-out pictures first, then rounds of training pictures until every held-out one is read
    seed = letters_seed(items)
    rng = np.random.default_rng(seed)
    first = {p: letters_bins(text[p], bg, LETTERS_RATIOS[1]) for p in places}
    cuts = [{p: _corner_text(a, places[p], first[p], glyph_min) for p in places} for a, _s in items]
    held = synthetic_letters(places, first, items, frames, fixed, rng, SYN_HELD, cuts, glyph_min)
    ttext = {p: text[p].copy() for p in places}
    tbg = {p: bg.copy() for p in places}
    trained: list = []
    rounds, best, done = [], None, None
    for rnd in range(1, SYN_ROUNDS + 1):
        batch = synthetic_letters(places, first, items, frames, fixed, rng, SYN_PER_ROUND, cuts, glyph_min)
        trained += batch
        for b, _s, pasted in batch:
            for p, box in places.items():
                x0, y0, x1, y1 = box
                k = letters_colour(b[y0:y1, x0:x1])
                ttext[p] += _lhist(np.where(pasted[p], k, -1))
                tbg[p] += _lhist(np.where(pasted[p], -1, k))
        row = {"round": rnd, "trained": len(trained), "held_out": len(held)}
        for ratio in LETTERS_RATIOS:
            bins = {p: letters_bins(ttext[p], tbg[p], ratio) for p in places}
            cells, bad = _letter_cells(places, bins, checks, word, glyph_min)
            if bad:
                continue
            c2, _bad2 = _letter_cells(places, bins, trained, word, glyph_min)     # (picture, sides, pasted)
            real = fit_letters(cells)
            for k2, v in c2.items():                     # a training glyph teaches a letter only when the real saves'
                if k2 not in real["keys"]:               # own reader reads it as that letter by distance
                    continue
                i2, t2 = real["keys"].index(k2), real["thresholds"].get(k2)
                cells[k2].extend(c for c in v if t2 is not None and float(letter_dists(real["refs"], c)[i2]) <= t2)
            fitted = fit_letters(cells)
            if not fitted["keys"] or not all(fitted["separable"].values()) or fitted["margin_needed"] is None:
                continue
            real_wrong = sum(_read_sides(places, bins, fitted, word, glyph_min, blank, a) != list(s) for a, s in checks)
            held_wrong = [i for i, (a, s, _p) in enumerate(held)
                          if _read_sides(places, bins, fitted, word, glyph_min, blank, a) != list(s)]
            cand = (real_wrong, len(held_wrong), ratio, bins, fitted, held_wrong)
            if best is None or cand[:2] < best[:2]:
                best = cand
            if not real_wrong and not held_wrong:
                done = cand
                break
        row.update({"ratio": best[2] if best else None, "real_wrong": best[0] if best else None,
                    "held_out_wrong": best[1] if best else None})
        rounds.append(row)
        if done:
            break
    trained_rep = {"seed": seed, "held_out": len(held), "trained": len(trained),
                   "backgrounds": len(frames), "rounds": rounds, "per_end_save": {"held_out": SYN_HELD,
                                                                                "a_round": SYN_PER_ROUND},
                   "held_out_wrong": best[1] if best else None, "real_wrong": best[0] if best else None,
                   "every_held_out_read": done is not None}
    if best is not None and best[5]:                       # which saves' letters the unread held-out pictures carried
        trained_rep["held_out_wrong_of"] = sorted({roles[i // SYN_HELD] for i in best[5]})
    report["synthetic"] = trained_rep
    if best is None:
        spec["letters"]["trained"] = trained_rep
        report["learn_s"] = round(time.perf_counter() - t0, 2)
        return spec, arrays, report
    _rw, _hw, ratio, bins, fitted, _hl = best
    spec["letters"].update({
        "places": {str(p): list(b) for p, b in places.items()}, "ratio": ratio, "glyph_min": round(glyph_min, 2),
        "blank": {str(p): v for p, v in blank.items()}, "keys": fitted["keys"],
        "thresholds": {k: v for k, v in fitted["thresholds"].items()}, "margin_needed": fitted["margin_needed"],
        "separable": fitted["separable"], "trained": trained_rep,
        "found_in": {str(p): sorted({c[0] for c in cl["m"]}) for p, cl in found.items()}})
    arrays["letters_bins"] = np.stack([bins[p] for p in sorted(places)])
    arrays["letters_refs"] = fitted["refs"]
    spec["usable"] = bool(sgap["threshold"] is not None and fitted["keys"] and fitted["margin_needed"] is not None
                          and all(fitted["separable"].values()))
    report["letters"] = {"places": places, "keys": fitted["keys"], "thresholds": fitted["thresholds"],
                         "margin_needed": fitted["margin_needed"], "ratio": ratio}
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


def check_spec(spec: dict) -> None:
    """A spec this tool reads, or ValueError with the plain line (a version-1 spec: learn it again)."""
    if not isinstance(spec, dict) or spec.get("kind") != "privyhub-h7-endscreen":
        raise ValueError("not an end-screen spec this tool reads")
    if spec.get("version") == 1:
        raise ValueError(OLD_MEASURE)
    if spec.get("version") not in (VERSION, VERSION_PLACES, VERSION_SCORE, VERSION_LETTERS) \
            or spec.get("measure") != MEASURE:
        raise ValueError("not an end-screen spec this tool reads")
    if spec.get("version") == VERSION_LETTERS and not isinstance(spec.get("letters"), dict):    # B191
        raise ValueError("a version-5 spec names its letters")
    if spec.get("version") == VERSION_PLACES and not isinstance(spec.get("places"), dict):
        raise ValueError("a version-3 spec names its places")
    if spec.get("version") == VERSION_SCORE and not isinstance(spec.get("score"), dict):     # B178
        raise ValueError("a version-4 spec names its scores")
    if spec.get("version") == VERSION_SCORE and "max_score" in spec["score"]:                 # B198
        m = spec["score"]["max_score"]
        if isinstance(m, bool) or not isinstance(m, int) or m < 0:
            raise ValueError("a version-4 spec's max_score is a whole number")


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
    v4 = spec.get("version") == VERSION_SCORE                                   # B178
    if spec.get("version") == VERSION_LETTERS:                                  # B191
        st = spec["start_class"]
        keys = (f"{st}_mask", f"{st}_ref") + (("letters_bins", "letters_refs") if "places" in spec["letters"] else ())
        with np.load(io.BytesIO(data), allow_pickle=False) as z:
            arrays = {k: z[k] for k in keys}
        lt = spec["letters"]
        if arrays[f"{st}_mask"].shape != (SIZE[1], SIZE[0]) or ("places" in lt and (
                arrays["letters_bins"].shape != (len(lt["places"]), LETTERS_NB * LETTERS_NB)
                or arrays["letters_refs"].shape != (len(lt["keys"]),) + tuple(lt["cell"]))):
            raise ValueError("the spec's arrays do not fit the spec")
        return spec, arrays
    keys = (tuple(f"{c}_{k}" for c in spec["classes"] for k in ("mask", "ref")) + ("place_mask", "place_refs")
            if v3 else tuple(f"{c}_{k}" for c in spec["classes"] for k in ("mask", "ref")) + ("digit_refs",)
            if v4 else ("screen_mask", "screen_ref", "outcome_mask", "refs"))
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        arrays = {k: z[k] for k in keys}
    if v4:
        sc = spec["score"]
        if (any(arrays[f"{c}_mask"].shape != (SIZE[1], SIZE[0]) for c in spec["classes"])
                or arrays["digit_refs"].shape[0] != len(sc.get("keys") or [])):
            raise ValueError("the spec's arrays do not fit the spec")
        return spec, arrays
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
        if cls is Reader and isinstance(spec, dict) and spec.get("version") == VERSION_SCORE:    # B178
            return super().__new__(ReaderScore)
        if cls is Reader and isinstance(spec, dict) and spec.get("version") == VERSION_LETTERS:  # B191
            return super().__new__(ReaderLetters)
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


class ReaderScore(ReaderPlaces):
    """B178: a version-4 spec — one screen per class (start, end, as version 3), each side's number on the end screen.
    `end` only with every side's number read; else `unknown` (scores null). Never a digit by nearness alone. B198: a
    spec with `score.max_score` reads a final above it as `unknown` with `end_unread` (and `above_max`)."""

    def __init__(self, spec: dict, arrays: dict, clock=time.monotonic):
        check_spec(spec)
        self.spec, self.clock = spec, clock
        self.classes = list(spec["classes"])
        self.masks = {c: arrays[f"{c}_mask"].astype(bool) for c in self.classes}
        self.srefs = {c: arrays[f"{c}_ref"][self.masks[c]].astype(np.float32) for c in self.classes}
        self.thr = {c: spec["screens"][c]["threshold"] for c in self.classes}
        self.own_worst = {c: spec["screens"][c].get("own_worst") for c in self.classes}
        self.score = spec["score"]
        self.digit_refs = arrays["digit_refs"].astype(np.float32)
        self.align = IDENTITY
        self.last_search: float | None = None

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
                if c2 is not None and worst is not None and ds2[c2] <= worst:
                    self.align, cls, ds = al, c2, ds2
        out = {"screen": cls is not None, "class": cls or OTHER,
               "distances": {"screen": round(min(ds.values()), 4), **{c: round(v, 4) for c, v in ds.items()}},
               "margin": None, "flat": False, "align": [round(self.align[0], 4), self.align[1], self.align[2]],
               "searched": searched, "scores": None}
        if cls == END:
            if not self.score.get("found"):
                out["class"] = UNKNOWN
                return out
            sr = read_scores(score_picture(img, self.align), self.score, self.digit_refs)
            out.update(score_read=sr["read"], margin=sr["margin"])
            top = self.score.get("max_score")
            if sr["scores"] is None:
                out["class"] = UNKNOWN
                out["end_unread"] = True                  # B182: the final screen, a number on it not read
            elif top is not None and max(sr["scores"]) > int(top):
                out["class"] = UNKNOWN                    # B198: a final above the title's highest score: never a
                out.update(end_unread=True, above_max=True)   # result (given up by B182's rule)
            else:
                out["scores"] = sr["scores"]
        return out


class ReaderLetters(Reader):
    """B191: a version-5 spec — each player's corner read as letters: the player whose letters spell the whole word
    lost, the other won (`end_P<the other>`); both -> unknown; a word spelled is never the begin; with none spelled, the
    start by its own still picture (B137's corner black), else other; a corner not read while the other spelled -> unknown with `end_unread` (B182); a moving
    screen (B140's measure against the read before) never reads as the same end twice in a row."""

    def __init__(self, spec: dict, arrays: dict, clock=time.monotonic):
        check_spec(spec)
        self.spec, self.clock = spec, clock
        self.classes = list(spec["classes"])
        self.start = spec["start_class"]
        self.smask = arrays[f"{self.start}_mask"].astype(bool)
        self.sref = arrays[f"{self.start}_ref"][self.smask].astype(np.float32)
        self.sthr = spec["screens"][self.start]["threshold"]
        lt = spec["letters"]
        self.word = lt["word"]
        self.found = bool(lt.get("found")) and "places" in lt
        if self.found:
            self.places = {int(p): tuple(b) for p, b in lt["places"].items()}
            self.bins = {p: arrays["letters_bins"][i].astype(bool) for i, p in enumerate(sorted(self.places))}
            self.fitted = {"keys": list(lt["keys"]), "refs": arrays["letters_refs"].astype(np.float32),
                           "thresholds": dict(lt["thresholds"]), "margin_needed": lt["margin_needed"]}
            self.glyph_min = float(lt["glyph_min"])
            self.blank = {int(p): bool(v) for p, v in (lt.get("blank") or {}).items()}
        self.align = IDENTITY
        self.last_search = None
        self.prev_small = None
        self.prev_class = None

    def sides(self, img: Image.Image) -> list:
        a = letters_area(img)
        return _read_sides(self.places, self.bins, self.fitted, self.word, self.glyph_min, self.blank, a)

    def read(self, img: Image.Image, now: float | None = None, search: bool = True) -> dict:
        small = np.asarray(img.convert("RGB").resize((64, 48)), dtype=np.int16)        # in colour: two scenes of one
        moved = self.prev_small is not None and float(                                # grey level still differ
            (np.abs(small - self.prev_small).max(axis=2) > LETTERS_MOVED[0]).mean()) >= LETTERS_MOVED[1]
        self.prev_small = small
        r, flat = ranks(_final(mid(corner_black(img))), self.smask)
        sd = _screen_dist(r, flat, self.smask, self.sref)
        out = {"screen": False, "class": OTHER, "distances": {self.start: round(sd, 4)}, "margin": None,
               "flat": bool(flat), "align": [1.0, 0.0, 0.0], "searched": False, "letters": None, "moved": moved}
        got = self.sides(img) if self.found else None
        spelled = [s == self.word for s in got] if got else []
        if got is not None:
            out["letters"] = got
        if any(spelled):                                   # a word spelled is never the begin
            if all(s is not None for s in got):
                if sum(spelled) == 1:
                    out.update(screen=True, **{"class": f"end_P{2 if spelled[0] else 1}"})
                else:
                    out["class"] = UNKNOWN                 # both spelled: no result
            else:
                out.update(**{"class": UNKNOWN}, end_unread=True)   # B182: a corner not read beside a spelled one
            if out["class"] in self.spec["end_classes"] and moved and self.prev_class == out["class"]:
                out["class"] = UNKNOWN                     # a moving screen: never the same end twice in a row
        elif self.sthr is not None and sd <= self.sthr:
            out.update(screen=True, **{"class": self.start})
        self.prev_class = out["class"]
        return out


def read(spec: dict, arrays: dict, img: Image.Image) -> dict:
    """One picture, read by a fresh Reader (a non-screen picture gets the full search)."""
    return Reader(spec, arrays).read(img)


def thresholds(spec: dict) -> dict:
    """What a read's distances are held against (B105's `last`)."""
    if spec.get("version") == VERSION_LETTERS:             # B191
        lt = spec["letters"]
        return {"screens": {c: v["threshold"] for c, v in spec["screens"].items()},
                "letters": dict(lt.get("thresholds") or {}), "margin_needed": lt.get("margin_needed")}
    if spec.get("version") == VERSION_SCORE:               # B178
        sc = spec["score"]
        return {"screens": {c: v["threshold"] for c, v in spec["screens"].items()},
                "digits": dict(sc.get("thresholds") or {}), "margin_needed": sc.get("margin_needed")}
    if spec.get("version") == VERSION_PLACES:              # B122
        pl = spec["places"]
        return {"screens": {c: v["threshold"] for c, v in spec["screens"].items()},
                "places": dict(pl["thresholds"]), "margin_needed": pl["margin_needed"]}
    return {"screen": spec.get("screen_threshold"), "classes": dict(spec.get("class_thresholds") or {}),
            "margin_needed": spec.get("margin_needed")}


class Ended:
    """K agreeing reads in a row; an end class counts only after the start was seen (K start reads, or a load).
    A version-4 spec (B178) is followed by `EndedScore`."""

    def __new__(cls, spec: dict, k: int | None = None):
        if cls is Ended and isinstance(spec, dict) and spec.get("version") == VERSION_SCORE:
            return super().__new__(EndedScore)
        return super().__new__(cls)

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


class EndedScore(Ended):
    """B178: K agreeing reads of the class and every side's number; `scores` once ended (port 1 first)."""

    def __init__(self, spec: dict, k: int | None = None):
        super().__init__(spec, k)
        self.scores: list[int] | None = None

    def feed(self, cls: str, scores=None) -> str | None:
        if self.ended:
            return self.ended
        key = (cls, tuple(scores) if scores is not None else None)
        if key == self.run_class:
            self.run += 1
        else:
            self.run_class, self.run = key, 1
        if self.run >= self.k:
            if cls == self.start:
                self.seen_start = True
            elif cls in self.ends and self.seen_start and scores is not None:
                self.ended = cls
                self.scores = [x if isinstance(x, int) else int(x) for x in scores]   # B200: as read (Drawn)
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


def score_scores(runs, labels, spec: dict, arrays: dict, half: str | None = None, search: bool = True) -> dict:
    """B178: a version-4 spec against labels with score classes. Per labelled class: pictures read right (a score
    class: `end` with exactly its numbers; start / other: that class) / read as other numbers (`wrong`) / unknown /
    other; `other` read as the screen (must be 0). Each picture read by a fresh Reader."""
    sources = _sources(runs, labels)
    rows: dict[str, dict[str, int]] = {}
    other_screen = 0
    for rf, lb in sources:
        paths = labelled_frames(rf, load_labels(lb), "second" if half == "second" else None)
        for c, ps in paths.items():
            want = score_numbers(c) if SCORE_LABEL.match(c) else None
            tally = rows.setdefault(c, {"right": 0, "wrong": 0, "unknown": 0, "other": 0, "n": 0})
            for p in ps:
                with Image.open(p) as im:
                    r = Reader(spec, arrays).read(im.convert("L"), search=search)
                tally["n"] += 1
                if c == OTHER and r["screen"]:
                    other_screen += 1
                if want is None:
                    tally["right" if r["class"] == c else ("unknown" if r["class"] == UNKNOWN else
                                                          ("other" if r["class"] == OTHER else "wrong"))] += 1
                elif r["class"] == END:
                    tally["right" if r.get("scores") == want else "wrong"] += 1
                else:
                    tally["unknown" if r["class"] == UNKNOWN else ("other" if r["class"] == OTHER else "wrong")] += 1
    return {"rows": rows, "other_read_as_screen": other_screen}


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
