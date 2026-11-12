#!/usr/bin/env python3
"""B102 (host): the end-screen learner (`tools/h7_endscreen.py`) on synthetic pictures drawn here — no game art.

The "screen": a 320 × 260 picture with a still panel (bars and boxes), a moving banner (a stripe whose offset changes
every frame), a varying portrait (a box whose shade changes every frame) and a seven-segment digit per side (the
tally); outcomes start 0-0, end_P1 1-0, end_P2 0-1; `other` frames are moving shapes on another background. Each frame
carries a little noise (±2). Runs are written as PNG + index.csv in a temp folder (removed at exit). PIL + numpy only.

    python3 -m unittest discover -s tests/b102_h7_endscreen -v
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import time
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

W, H = 320, 260
BANNER = (0, 8, 320, 40)            # the moving banner
PORTRAIT = (16, 70, 96, 200)        # the varying portrait
LEFT_DIGIT, RIGHT_DIGIT = (130, 150), (176, 150)   # the digits' top-left corners
SEG = {"0": "abcdef", "1": "bc"}


def digit(d: ImageDraw.ImageDraw, x: int, y: int, ch: str) -> None:
    """A seven-segment digit 20 × 36, segments 4 px thick, white on the panel."""
    s = SEG[ch]
    boxes = {"a": (x, y, x + 20, y + 4), "b": (x + 16, y, x + 20, y + 18), "c": (x + 16, y + 18, x + 20, y + 36),
             "d": (x, y + 32, x + 20, y + 36), "e": (x, y + 18, x + 4, y + 36), "f": (x, y, x + 4, y + 18)}
    for k in s:
        d.rectangle(boxes[k], fill=235)


def screen(i: int, tally: str, rng: np.random.Generator, portrait_shade: int | None = None) -> Image.Image:
    im = Image.new("L", (W, H), 40)
    d = ImageDraw.Draw(im)
    d.rectangle((110, 60, 210, 230), fill=90)                      # the still panel
    d.rectangle((120, 140, 200, 196), fill=20)                     # the tally box
    for k in range(6):
        d.rectangle((230, 70 + 25 * k, 300, 88 + 25 * k), fill=150 + 15 * k)   # still boxes
    off = (i * 7) % 40                                              # the moving banner
    for x in range(-40, W + 40, 40):
        d.rectangle((x + off, BANNER[1], x + off + 18, BANNER[3]), fill=200)
    shade = int(rng.integers(30, 220)) if portrait_shade is None else portrait_shade
    d.rectangle(PORTRAIT, fill=shade)                               # the varying portrait
    d.ellipse((30, 90, 80, 140), fill=int(rng.integers(30, 220)) if portrait_shade is None else 255 - shade)
    digit(d, *LEFT_DIGIT, tally[0])
    digit(d, *RIGHT_DIGIT, tally[1])
    return noisy(im, rng)


def other(i: int, rng: np.random.Generator) -> Image.Image:
    im = Image.new("L", (W, H), int(rng.integers(100, 180)))
    d = ImageDraw.Draw(im)
    for _ in range(6):
        x, y = int(rng.integers(0, W - 60)), int(rng.integers(0, H - 60))
        d.ellipse((x, y, x + int(rng.integers(20, 90)), y + int(rng.integers(20, 90))), fill=int(rng.integers(0, 255)))
    d.rectangle((0, H - 30, W, H), fill=(i * 13) % 255)
    return noisy(im, rng)


def noisy(im: Image.Image, rng: np.random.Generator) -> Image.Image:
    a = np.asarray(im, dtype=np.int16) + rng.integers(-2, 3, size=(H, W))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")


def write_runs(root: Path) -> tuple[Path, Path]:
    """Runs: begin (start), win1 (other then end_P1), win2 (end_P2), fight (other), with ignore stretches."""
    rng = np.random.default_rng(102)
    runs = root / "runs"
    plan = {
        "begin": [("ignore", 2, None), ("start", 24, "00")],
        "win1": [("other", 8, None), ("ignore", 1, None), ("end_P1", 16, "10")],
        "win2": [("ignore", 2, None), ("end_P2", 16, "01")],
        "fight": [("other", 30, None)],
    }
    labels = {"classes": {"start": "0-0", "end_P1": "1-0", "end_P2": "0-1", "other": "anything else",
                          "ignore": "not used"}, "runs": {}}
    for run, parts in plan.items():
        d = runs / run
        d.mkdir(parents=True)
        rows, t, ranges, i = [], 0.0, [], 0
        for label, n, tally in parts:
            ranges.append({"from": t, "to": t + 0.5 * (n - 1), "label": label})
            for _ in range(n):
                img = (screen(i, tally, rng) if tally else
                       (other(i, rng) if label == "other" else Image.new("L", (W, H), int(rng.integers(0, 255)))))
                name = f"f{i:04d}.png"
                img.save(d / name)
                rows.append({"seconds": f"{t:.1f}", "file": name})
                t += 0.5
                i += 1
        with (d / "index.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["seconds", "file"])
            w.writeheader()
            w.writerows(rows)
        labels["runs"][run] = ranges
    lp = root / "labels.json"
    lp.write_text(json.dumps(labels))
    return runs, lp


def mask_in(mask: np.ndarray, box: tuple[int, int, int, int]) -> int:
    """The mask's pixels inside a box given on the 320 × 260 picture (mapped onto the 160 × 120 grid)."""
    sx, sy = E.SIZE[0] / W, E.SIZE[1] / H
    x0, y0, x1, y1 = int(box[0] * sx), int(box[1] * sy), int(np.ceil(box[2] * sx)), int(np.ceil(box[3] * sy))
    return int(mask[y0:y1, x0:x1].sum())


class Learner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="b102_"))
        cls.runs, cls.labels = write_runs(cls.tmp)
        cls.spec, cls.arrays, cls.report = E.learn(cls.runs, cls.labels, name="fixture")
        cls.rng = np.random.default_rng(7)

    def reader(self):
        return E.Reader(self.spec, self.arrays)

    def test_the_reduced_size(self):
        a = E.reduce(screen(0, "00", self.rng))
        self.assertEqual(a.shape, (120, 160))
        self.assertEqual(a.dtype, np.float32)
        self.assertEqual(self.spec["size"], [160, 120])

    def test_the_masks_leave_out_the_moving_and_varying_parts(self):
        sm, om = self.arrays["screen_mask"], self.arrays["outcome_mask"]
        self.assertEqual(mask_in(sm, BANNER), 0)
        inner = (PORTRAIT[0] + 4, PORTRAIT[1] + 4, PORTRAIT[2] - 4, PORTRAIT[3] - 4)
        self.assertEqual(mask_in(sm, inner), 0)
        self.assertGreater(sm.sum(), 0.5 * sm.size)                       # the still panel and the rest
        self.assertGreater(om.sum(), 0)
        digits = (LEFT_DIGIT[0] - 2, LEFT_DIGIT[1] - 2, RIGHT_DIGIT[0] + 22, RIGHT_DIGIT[1] + 38)
        self.assertEqual(mask_in(om, digits), int(om.sum()))              # the outcome mask inside the digits
        self.assertEqual(mask_in(om, BANNER) + mask_in(om, PORTRAIT), 0)

    def test_the_report(self):
        r = self.report
        self.assertEqual(r["frames_per_class"], {"start": 24, "end_P1": 16, "end_P2": 16, "other": 38})
        for c in ("start", "end_P1", "end_P2"):
            self.assertEqual(r["classes"][c]["verdict"], "separable")
            self.assertGreater(r["classes"][c]["gap"], 0)
        self.assertEqual(r["screen"]["verdict"], "separable")
        self.assertTrue(0 < r["outcome_mask"]["share"] < 0.05)

    def test_the_classes_are_told_apart(self):
        for tally, want in (("00", "start"), ("10", "end_P1"), ("01", "end_P2")):
            for i in range(5):
                r = self.reader().read(screen(100 + i, tally, self.rng))
                self.assertTrue(r["screen"], r)
                self.assertEqual(r["class"], want, r)
                self.assertGreaterEqual(r["margin"], self.spec["margin_needed"])

    def test_an_unseen_outcome_reads_unknown(self):
        for i in range(5):
            r = self.reader().read(screen(200 + i, "11", self.rng))
            self.assertTrue(r["screen"], r)
            self.assertEqual(r["class"], "unknown", r)

    def test_an_unseen_portrait_still_reads(self):
        r = self.reader().read(screen(300, "10", self.rng, portrait_shade=0))
        self.assertEqual((r["screen"], r["class"]), (True, "end_P1"))

    def test_an_other_frame_never_reads_as_the_screen(self):
        rng = np.random.default_rng(99)
        for i in range(60):
            r = self.reader().read(other(1000 + i, rng))                    # a fresh reader: the full search
            self.assertFalse(r["screen"], r)
            self.assertEqual(r["class"], "other")
        blank = self.reader().read(Image.new("L", (W, H), 0))
        self.assertFalse(blank["screen"])

    def test_moved_pictures_read_with_the_search(self):
        for dx, dy, s in ((6, 0, 1.0), (0, -6, 1.0), (4, 4, 1.03), (-5, 2, 0.97)):
            img = screen(400, "01", self.rng)
            cx, cy = W / 2.0, H / 2.0
            img = img.transform(img.size, Image.AFFINE, (1 / s, 0, cx - (cx + dx) / s, 0, 1 / s, cy - (cy + dy) / s),
                                resample=Image.BILINEAR, fillcolor=0)
            r = self.reader().read(img)
            self.assertEqual((r["screen"], r["class"]), (True, "end_P2"), (dx, dy, s, r))

    def test_side_bars_are_cut(self):
        canvas = Image.new("L", (W + 160, H), 0)
        canvas.paste(screen(500, "10", self.rng), (80, 0))
        r = self.reader().read(canvas)
        self.assertEqual((r["screen"], r["class"], r["searched"]), (True, "end_P1", False))

    def test_the_search_is_kept_and_floored(self):
        rd = self.reader()
        t = [100.0]
        rd.clock = lambda: t[0]
        rng = np.random.default_rng(3)
        r1 = rd.read(other(1, rng))
        self.assertTrue(r1["searched"])
        r2 = rd.read(other(2, rng))
        self.assertFalse(r2["searched"])                                     # within 10 s: no second search
        t[0] += E.SEARCH_EVERY
        self.assertTrue(rd.read(other(3, rng))["searched"])

    def test_one_read_is_milliseconds(self):
        rd = self.reader()
        img = screen(600, "10", self.rng)
        rd.read(img)
        times = []
        for _ in range(20):
            t0 = time.perf_counter()
            rd.read(img)
            times.append(time.perf_counter() - t0)
        self.assertLess(float(np.median(times)), 0.05)

    def test_k_in_a_row(self):
        e = E.Ended(self.spec)
        self.assertEqual(e.k, 3)
        for c in ("end_P1",) * 4:                                             # an end before the start: not counted
            self.assertIsNone(e.feed(c))
        self.assertFalse(e.seen_start)
        for c in ("start", "start", "other", "start", "start"):
            e.feed(c)
        self.assertFalse(e.seen_start)                                        # broken by an other read
        e.feed("start")
        self.assertTrue(e.seen_start)
        for c in ("other",) * 10 + ("end_P2", "end_P2", "other", "unknown", "unknown", "unknown", "end_P2", "end_P2"):
            self.assertIsNone(e.feed(c))
        self.assertEqual(e.feed("end_P2"), "end_P2")
        self.assertEqual(e.feed("end_P1"), "end_P2")                          # ended stays ended
        e2 = E.Ended(self.spec)
        e2.start_loaded()
        self.assertIsNone(e2.feed("end_P1"))
        self.assertIsNone(e2.feed("end_P1"))
        self.assertEqual(e2.feed("end_P1"), "end_P1")

    def test_a_class_with_no_frames_is_a_plain_error(self):
        data = json.loads(self.labels.read_text())
        data["classes"]["end_P3"] = "a class no range names"
        bad = self.tmp / "labels_bad.json"
        bad.write_text(json.dumps(data))
        with self.assertRaises(ValueError) as cm:
            E.learn(self.runs, bad)
        self.assertEqual(str(cm.exception), "the labels name a class with no frames: end_P3")
        data = json.loads(self.labels.read_text())
        data["runs"]["missing"] = [{"from": 0, "to": 1, "label": "start"}]
        bad.write_text(json.dumps(data))
        with self.assertRaises(ValueError) as cm:
            E.learn(self.runs, bad)
        self.assertEqual(str(cm.exception), "the labels name a run with no frames: missing")

    def test_halves(self):
        labels = E.load_labels(self.labels)
        first = E.labelled_frames(self.runs, labels, "first")
        second = E.labelled_frames(self.runs, labels, "second")
        self.assertEqual({c: len(v) for c, v in first.items()}, {"start": 12, "end_P1": 8, "end_P2": 8, "other": 19})
        self.assertEqual({c: len(v) for c, v in second.items()}, {"start": 12, "end_P1": 8, "end_P2": 8, "other": 19})
        self.assertFalse(set(map(str, first["start"])) & set(map(str, second["start"])))
        spec, arrays, _ = E.learn(self.runs, self.labels, half="first")
        s = E.score(self.runs, self.labels, spec, arrays, half="second")
        self.assertEqual(s["other_read_as_screen"], 0)
        self.assertEqual(s["right"], {"start": [12, 12], "end_P1": [8, 8], "end_P2": [8, 8], "other": [19, 19]})

    def test_the_spec_on_disk(self):
        out = self.tmp / "fixture.endscreen.json"
        E.save_spec(self.spec, self.arrays, out)
        self.assertTrue((self.tmp / "fixture.endscreen.npz").is_file())
        spec, arrays = E.load_spec(out)
        self.assertEqual(spec["classes"], ["start", "end_P1", "end_P2"])
        self.assertLess(out.stat().st_size, 4096)                             # the JSON is small
        r = E.Reader(spec, arrays).read(screen(700, "01", self.rng))
        self.assertEqual(r["class"], "end_P2")
        npz = self.tmp / "fixture.endscreen.npz"
        data = bytearray(npz.read_bytes())
        data[-1] ^= 0xFF
        npz.write_bytes(bytes(data))
        with self.assertRaises(ValueError) as cm:
            E.load_spec(out)
        self.assertEqual(str(cm.exception), "the spec's arrays file does not match the spec")

    def test_nothing_written_beside_the_frames(self):
        before = sorted(p.name for p in (self.runs / "begin").iterdir())
        E.learn(self.runs, self.labels)
        E.score(self.runs, self.labels, self.spec, self.arrays)
        self.assertEqual(sorted(p.name for p in (self.runs / "begin").iterdir()), before)


if __name__ == "__main__":
    unittest.main()
