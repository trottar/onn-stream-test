#!/usr/bin/env python3
"""B122 (host): a place for every player — `tools/h7_endscreen.py`'s spec version 3, on synthetic pictures drawn here
(no game art).

The results screen: a 640 × 480 picture with a still frame (a title bar, a label box, four markers) and a **row of four
seven-segment place digits (1-4) under the four markers**, over a **moving scene** (a striped background whose offset
and tone change every frame, a "stage" shade per match, drifting blobs); the start screen: a select screen of its own
(a grid of boxes, four slots, a moving cursor; the title bar shared); `other`: moving shapes. Training rows: 1234, 2341, 3412 — so every column has seen
three places and missed one. Read: 4123 (never seen whole, and every column's place one it never showed), 2143 (never
seen whole; two columns' places never shown there); a duplicated place → `unknown`; a half-drawn row → never `ended`;
K; the spec on disk (version 3, and a version-2 spec still loads); a place shown in no column → learning refuses.
Temp folders removed at exit.

    python3 -m unittest discover -s tests/b122_h7_places -v
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
sys.path.insert(0, str(ROOT / "tools"))
import _tmp_cleanup  # noqa: E402,F401
import h7_endscreen as E  # noqa: E402

W, H = 640, 480
COLS = [210 + 90 * j for j in range(4)]           # each column's digit left edge
ROW_Y = 150
SEG = {"1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc"}


def digit(d: ImageDraw.ImageDraw, x: int, y: int, ch: str, fill: int = 240) -> None:
    """A seven-segment digit 28 × 48, segments 7 px thick, with a black outline box behind it."""
    d.rectangle((x - 4, y - 4, x + 32, y + 52), fill=10)
    b = {"a": (x, y, x + 28, y + 7), "b": (x + 21, y, x + 28, y + 24), "c": (x + 21, y + 24, x + 28, y + 48),
         "d": (x, y + 41, x + 28, y + 48), "e": (x, y + 24, x + 7, y + 48), "f": (x, y, x + 7, y + 24),
         "g": (x, y + 21, x + 28, y + 28)}
    for k in SEG[ch]:
        d.rectangle(b[k], fill=fill)


def scene(i: int, stage: int, rng: np.random.Generator) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("L", (W, H), 60 + stage)
    d = ImageDraw.Draw(im)
    off = (i * 11) % 60
    for x in range(-60, W + 60, 60):                                   # the moving stripes
        d.rectangle((x + off, 0, x + off + 25, H), fill=(90 + stage + (i * 7) % 50) % 256)
    for _ in range(5):                                                 # drifting blobs (confetti, characters)
        x, y = int(rng.integers(0, W - 40)), int(rng.integers(260, H - 40))
        d.ellipse((x, y, x + 40, y + 40), fill=int(rng.integers(0, 255)))
    d.rectangle((40, 20, 600, 50), fill=200)                           # the still frame: title bar
    d.rectangle((40, 150, 170, 200), fill=30)                          # the label box
    d.rectangle((170, 214, 600, 219), fill=235)                        # the rule under the row
    d.rectangle((40, 232, 170, 276), fill=30)                          # a second label box
    d.rectangle((40, 60, 600, 66), fill=235)                           # the rule under the title
    for x in COLS:
        d.polygon([(x - 2, 110), (x + 30, 110), (x + 14, 134)], fill=170)   # the markers
    return im, d


def results(i: int, row: str, stage: int, rng: np.random.Generator, drawn: int = 4) -> Image.Image:
    im, d = scene(i, stage, rng)
    for j, ch in enumerate(row[:drawn]):
        digit(d, COLS[j], ROW_Y, ch, fill=250 if ch == "1" else 235)
    return noisy(im, rng)


def start(i: int, rng: np.random.Generator) -> Image.Image:
    """The select screen: its own steady layout (a grid of boxes, four slots), the title bar shared with the results
    screen, a small moving cursor."""
    im = Image.new("L", (W, H), 45)
    d = ImageDraw.Draw(im)
    d.rectangle((40, 20, 600, 50), fill=200)                           # the title bar (shared)
    for r_ in range(3):
        for c_ in range(6):
            d.rectangle((60 + 90 * c_, 80 + 70 * r_, 130 + 90 * c_, 135 + 70 * r_), fill=110 + 20 * ((r_ + c_) % 4))
    for j in range(4):
        d.rectangle((50 + 140 * j, 320, 170 + 140 * j, 460), fill=180 - 25 * j)   # the four players' slots
    cx = 60 + (i * 37) % 500
    d.ellipse((cx, 290, cx + 20, 310), fill=250)                       # the moving cursor
    return noisy(im, rng)


def other(i: int, rng: np.random.Generator) -> Image.Image:
    im = Image.new("L", (W, H), int(rng.integers(90, 190)))
    d = ImageDraw.Draw(im)
    for _ in range(8):
        x, y = int(rng.integers(0, W - 90)), int(rng.integers(0, H - 90))
        d.ellipse((x, y, x + int(rng.integers(30, 120)), y + int(rng.integers(30, 120))), fill=int(rng.integers(0, 255)))
    return noisy(im, rng)


def noisy(im: Image.Image, rng: np.random.Generator) -> Image.Image:
    a = np.asarray(im, dtype=np.int16) + rng.integers(-2, 3, size=(H, W))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


TRAIN = ("1234", "2341", "3412")


def write_run(root: Path, plan: list, name: str = "run", seed: int = 122) -> tuple[Path, dict]:
    """plan: [(label, n, row or None, stage)] -> runs/<name>/ (PNG + index.csv) and its labels."""
    rng = np.random.default_rng(seed)
    d = root / "runs" / name
    d.mkdir(parents=True)
    rows, ranges, t, i = [], [], 0.0, 0
    for label, n, row, stage in plan:
        ranges.append({"from": t, "to": t + (n - 1), "label": label})
        for _ in range(n):
            img = (results(i, row, stage, rng) if row else start(i, rng) if label == "start" else other(i, rng))
            fname = f"f{i:04d}.png"
            img.save(d / fname)
            rows.append({"seconds": f"{t:.1f}", "file": fname})
            t += 1.0
            i += 1
    with (d / "index.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["seconds", "file"])
        w.writeheader()
        w.writerows(rows)
    classes = {"start": "the select screen", "other": "anything else", "ignore": "not used"}
    classes.update({lab: "a place row" for lab, _n, _r, _s in plan if lab.startswith("end_r")})
    return root / "runs", {"classes": classes, "runs": {name: ranges}}


class Places(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="b122_"))
        plan = []
        for k, row in enumerate(TRAIN):
            plan += [("start", 10, None, 0), ("other", 10, None, 0), (f"end_r{row}", 14, row, 20 * (k + 1))]
        cls.runs, cls.labels = write_run(cls.tmp, plan)
        cls.spec, cls.arrays, cls.report = E.learn(cls.runs, cls.labels, name="syn")
        cls.rng = np.random.default_rng(7)

    def read(self, img, reader=None):
        return (reader or E.Reader(self.spec, self.arrays)).read(img)

    def test_version_3_and_the_row_learnt(self):
        self.assertEqual(self.spec["version"], 3)
        self.assertEqual((self.spec["classes"], self.spec["end_classes"]), (["start", "end"], ["end"]))
        pl = self.spec["places"]
        self.assertEqual(pl["ports"], 4)
        self.assertEqual(pl["spacing_px_320"], 45)                       # 90 px of 640 = 45 of 320
        xs = [x for _y, x in pl["offsets_px_320"]]
        self.assertEqual([b - a for a, b in zip(xs, xs[1:])], [45, 45, 45])
        self.assertTrue(all(pl["separable"].values()))
        self.assertTrue(self.spec["usable"])
        self.assertEqual(pl["seen_in_column"], {"1": [1, 2, 3], "2": [2, 3, 4], "3": [1, 3, 4], "4": [1, 2, 4]})

    def test_the_training_rows_read_back(self):
        for k, row in enumerate(TRAIN):
            r = self.read(results(500 + k, row, 20 * (k + 1), self.rng))
            self.assertEqual((r["class"], r["places"]), ("end", [int(c) for c in row]), (row, r))

    def test_a_row_never_seen_whole_every_place_new_to_its_column(self):
        for k in range(4):
            r = self.read(results(600 + k, "4123", 15 + 9 * k, self.rng))
            self.assertEqual((r["class"], r["places"]), ("end", [4, 1, 2, 3]), r)

    def test_a_place_never_seen_in_a_column(self):
        r = self.read(results(700, "2143", 33, self.rng))
        self.assertEqual((r["class"], r["places"]), ("end", [2, 1, 4, 3]), r)

    def test_a_duplicated_place_is_unknown(self):
        r = self.read(results(800, "1134", 20, self.rng))
        self.assertEqual((r["class"], r["places"]), ("unknown", None), r)
        self.assertEqual(r["ports"][2:], [3, 4])                           # each column's own read is kept

    def test_a_half_drawn_row_is_unknown_and_never_ends(self):
        reader = E.Reader(self.spec, self.arrays)
        ended = E.Ended(self.spec, 3)
        ended.start_loaded()
        for i in range(6):
            r = reader.read(results(900 + i, "3412", 60, self.rng, drawn=2))
            self.assertIn(r["class"], ("unknown", "other"), r)            # never `end`, never a place row
            self.assertIsNone(r["places"])
            self.assertIsNone(ended.feed(r["class"], r["places"]))

    def test_k_agreeing_reads_of_the_whole_row(self):
        reader = E.Reader(self.spec, self.arrays)
        ended = E.Ended(self.spec, 3)
        r0 = reader.read(start(950, self.rng))
        self.assertEqual(r0["class"], "start")
        for _ in range(3):
            ended.feed("start")
        seq = [("2143", None), ("2143", None), ("4123", None), ("4123", None), ("4123", "end")]
        for i, (row, want) in enumerate(seq):
            r = reader.read(results(960 + i, row, 40, self.rng))
            self.assertEqual(ended.feed(r["class"], r["places"]), want, (i, row))
        self.assertEqual(ended.places, [4, 1, 2, 3])
        two = E.Ended(self.spec, 2)
        two.start_loaded()
        r = reader.read(results(990, "2143", 40, self.rng))
        two.feed(r["class"], r["places"])
        self.assertEqual(two.feed(r["class"], r["places"]), "end")

    def test_the_start_and_other_pictures(self):
        self.assertEqual(self.read(start(1000, self.rng))["class"], "start")
        for i in range(20):
            r = self.read(other(1100 + i, self.rng))
            self.assertFalse(r["screen"], r)
            self.assertIsNone(r["places"])

    def test_the_spec_on_disk_and_the_score(self):
        p = E.save_spec(self.spec, self.arrays, self.tmp / "syn.endscreen.json")
        spec, arrays = E.load_spec(p)
        self.assertEqual(spec["version"], 3)
        r = E.Reader(spec, arrays).read(results(1200, "4123", 25, self.rng))
        self.assertEqual(r["places"], [4, 1, 2, 3])
        sc = E.score_places(self.runs, self.labels, spec, arrays)
        self.assertEqual(sc["places_wrong"], 0)
        self.assertEqual(sc["other_read_as_screen"], 0)
        for row in TRAIN:
            self.assertEqual(sc["rows"][f"end_r{row}"]["right"], 14, sc["rows"])

    def test_replay_names_the_places(self):
        tmp = Path(tempfile.mkdtemp(prefix="b122_rp_"))
        plan = [("start", 6, None, 0), ("other", 6, None, 0), ("end_r4123", 6, "4123", 50),
                ("start", 6, None, 0), ("other", 6, None, 0), ("end_r2143", 6, "2143", 70)]
        runs, labels = write_run(tmp, plan, seed=9)
        rp = E.replay(runs / "run", self.spec, self.arrays, 3, labels)
        self.assertEqual([(e["class"], e["places"]) for e in rp["ended"]], [("end", [4, 1, 2, 3]), ("end", [2, 1, 4, 3])])
        self.assertEqual([e["after_end_screen_s"] for e in rp["ended"]], [2.0, 2.0])   # K = 3 at one a second

    def test_a_place_shown_in_no_column_is_refused(self):
        tmp = Path(tempfile.mkdtemp(prefix="b122_no4_"))
        plan = [("start", 6, None, 0), ("other", 6, None, 0), ("end_r1231", 2, None, 0)]
        with self.assertRaises(ValueError):                               # not a permutation
            E.place_ports(["start", "other", "end_r1231"])
        with self.assertRaises(ValueError) as cm:
            E.learn_places({(1, 2, 3): [np.zeros((240, 320), np.float32)], (2, 1, 3): [np.zeros((240, 320), np.float32)]}, 4)
        self.assertIn("place 4 is never shown", str(cm.exception))
        del plan, tmp

    def test_mixed_labels_refused_and_version_2_unchanged(self):
        with self.assertRaises(ValueError):
            E.place_ports(["start", "other", "end_r12", "end_P1"])
        self.assertIsNone(E.place_ports(["start", "other", "end_P1", "end_P2"]))
        # a version-2 spec (two-player labels) learns and loads as before
        tmp = Path(tempfile.mkdtemp(prefix="b122_v2_"))
        rng = np.random.default_rng(3)
        d = tmp / "runs" / "v2"
        d.mkdir(parents=True)
        rows, ranges, t, i = [], [], 0.0, 0
        # two-player labels on one layout (as T88's): the start and both ends differ only in the row
        for label, n, row in (("start", 10, "4444"), ("other", 10, None), ("end_P1", 10, "1234"), ("end_P2", 10, "4321")):
            ranges.append({"from": t, "to": t + n - 1, "label": label})
            for _ in range(n):
                img = results(i, row, 30, rng) if row else other(i, rng)
                img.save(d / f"f{i:04d}.png")
                rows.append({"seconds": f"{t:.1f}", "file": f"f{i:04d}.png"})
                t += 1
                i += 1
        with (d / "index.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["seconds", "file"])
            w.writeheader()
            w.writerows(rows)
        labels = {"classes": {"start": "s", "other": "o", "end_P1": "p1", "end_P2": "p2"}, "runs": {"v2": ranges}}
        spec, arrays, _rep = E.learn(tmp / "runs", labels, name="two")
        self.assertEqual(spec["version"], 2)
        self.assertNotIn("places", spec)
        p = E.save_spec(spec, arrays, tmp / "two.endscreen.json")
        spec2, arrays2 = E.load_spec(p)
        r = E.Reader(spec2, arrays2).read(results(99, "1234", 30, rng))
        self.assertEqual(r["class"], "end_P1")
        self.assertNotIn("places", r)                                     # version 2's read has no new key


if __name__ == "__main__":
    unittest.main()
