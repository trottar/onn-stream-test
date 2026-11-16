#!/usr/bin/env python3
"""B104 (host): the tone-independent read (`tools/h7_endscreen.py`, spec version 2) on synthetic pictures drawn here
with B102's drawing (a still panel, a moving banner, a varying portrait, a seven-segment tally) — no game art.

Cases: the same screen under an offset, a gain and a curve reads the same class; fights under each never read as the
screen; two classes whose pictures differ only by a whole-picture tone change → "not separable"; a tally whose tone
alone differs from the rest IS told apart (disclosed: the measure ranks against the picture's own screen-mask tone);
a picture inside black bars of another size reads as the bare picture; a game's own dark border is not cut; a flat
picture is never the screen; a version-1 spec refused with the plain line; two sources of different sizes and tones
learnt together; a labelled frame unlike its label does not set the threshold; a pair of classes never seen in one
source cannot make the outcome mask; `replay` (its ended moments, re-armed; the CLI); one read in milliseconds.
Temp dirs removed at exit. PIL + numpy only.

    python3 -m unittest discover -s tests/b104_h7_tone -v
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import subprocess
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
sys.path.insert(0, str(ROOT / "tests" / "b102_h7_endscreen"))
sys.path.insert(0, str(ROOT / "tools"))
import _tmp_cleanup  # noqa: E402,F401
import h7_endscreen as E  # noqa: E402
import test_b102 as b102  # noqa: E402  (a module: its tests are not collected twice)

W, H = b102.W, b102.H
TALLY = {"start": "00", "end_P1": "10", "end_P2": "01"}
CONFOUND_BOX = (230, 222, 300, 254)          # a "character" patch whose shade belongs to a source


def tone(img: Image.Image, offset=0.0, gain=1.0, gamma=1.0) -> Image.Image:
    a = np.asarray(img, dtype=np.float32)
    a = 255.0 * (np.clip(a, 0, 255) / 255.0) ** gamma
    a = np.clip(a * gain + offset, 0, 255)
    return Image.fromarray(np.rint(a).astype(np.uint8), "L")


TONES = {"offset+30": dict(offset=30), "offset-30": dict(offset=-30), "gain0.8": dict(gain=0.8),
         "gain1.2": dict(gain=1.2), "gamma0.8": dict(gamma=0.8), "gamma1.25": dict(gamma=1.25)}


def dim_digits(img: Image.Image, shade: int = 150) -> Image.Image:
    """The tally drawn at another shade (the rest of the picture as it is)."""
    a = np.asarray(img).copy()
    x0, y0 = b102.LEFT_DIGIT[0] - 2, b102.LEFT_DIGIT[1] - 2
    x1, y1 = b102.RIGHT_DIGIT[0] + 22, b102.RIGHT_DIGIT[1] + 38
    box = a[y0:y1, x0:x1]
    box[box >= 200] = shade
    return Image.fromarray(a, "L")


def window(img: Image.Image, size=(1200, 520), scale=2.0) -> Image.Image:
    """The picture scaled and centred in a black window of another size."""
    w, h = round(img.size[0] * scale), round(img.size[1] * scale)
    canvas = Image.new("L", size, 0)
    canvas.paste(img.resize((w, h), Image.BILINEAR), ((size[0] - w) // 2, (size[1] - h) // 2))
    return canvas


def write_run(folder: Path, pictures: list[tuple[str, Image.Image]], step=1.0) -> list[dict]:
    """A run folder (PNG + index.csv); -> its label ranges."""
    folder.mkdir(parents=True)
    rows, ranges = [], []
    for i, (label, img) in enumerate(pictures):
        name = f"f{i:04d}.png"
        img.save(folder / name)
        rows.append({"seconds": f"{i * step:.1f}", "file": name})
        if ranges and ranges[-1]["label"] == label:
            ranges[-1]["to"] = i * step
        else:
            ranges.append({"from": i * step, "to": i * step, "label": label})
    with (folder / "index.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["seconds", "file"])
        w.writeheader()
        w.writerows(rows)
    return ranges


CLASSES = {"start": "0-0", "end_P1": "1-0", "end_P2": "0-1", "other": "anything else", "ignore": "not used"}
TWO = {"start": "0-0", "end_P1": "another", "other": "anything else", "ignore": "not used"}


class ToneIndependent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="b104_"))
        cls.runs, cls.labels = b102.write_runs(cls.tmp)
        cls.spec, cls.arrays, cls.report = E.learn(cls.runs, cls.labels, name="fixture")
        cls.rng = np.random.default_rng(104)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def reader(self, spec=None, arrays=None):
        return E.Reader(spec or self.spec, arrays or self.arrays)

    def test_the_spec_is_version_2_in_ranks(self):
        self.assertEqual((self.spec["version"], self.spec["measure"]), (2, "rank-against-screen-mask"))
        for k in ("tol", "flat", "bar_max", "bar_share", "steady_r", "differ_r", "sep", "min_gap"):
            self.assertIn(k, self.spec)
        for c in ("start", "end_P1", "end_P2"):
            self.assertEqual(self.report["classes"][c]["verdict"], "separable")

    def test_the_same_screen_under_a_tone_change_reads_the_same(self):
        for name, kw in TONES.items():
            for tally, want in (("00", "start"), ("10", "end_P1"), ("01", "end_P2")):
                for i in range(3):
                    img = b102.screen(100 + i, tally, self.rng)
                    plain = self.reader().read(img)
                    toned = self.reader().read(tone(img, **kw))
                    self.assertEqual((plain["screen"], plain["class"]), (True, want))
                    self.assertEqual((toned["screen"], toned["class"]), (True, want), (name, tally, toned))
                    self.assertFalse(toned["searched"], (name, toned))         # read at once, no search needed
        for kw in (dict(gain=1.2, offset=30), dict(gamma=0.8, gain=1.2), dict(gamma=1.25, offset=30)):
            r = self.reader().read(tone(b102.screen(150, "10", self.rng), **kw))
            self.assertEqual((r["screen"], r["class"]), (True, "end_P1"), (kw, r))
        # pairs that clip the dark end into one black (background 40 and the tally box 20 both to ~0): the limit of
        # any tone-free measure — the tally may then read unknown, never another class
        for kw in (dict(gain=0.8, offset=-30), dict(gamma=1.25, offset=-30)):
            for tally, want in (("00", "start"), ("10", "end_P1"), ("01", "end_P2")):
                r = self.reader().read(tone(b102.screen(160, tally, self.rng), **kw))
                self.assertTrue(r["screen"], (kw, r))
                self.assertIn(r["class"], (want, "unknown"), (kw, r))

    def test_a_fight_under_any_tone_never_reads_as_the_screen(self):
        rng = np.random.default_rng(99)
        for name, kw in [("none", {}), *TONES.items()]:
            for i in range(15):
                r = self.reader().read(tone(b102.other(1000 + i, rng), **kw))      # a fresh reader: the full search
                self.assertFalse(r["screen"], (name, r))
                self.assertEqual(r["class"], "other")

    def test_classes_that_differ_only_by_the_whole_pictures_tone_are_not_separable(self):
        rng = np.random.default_rng(5)
        pics = ([("start", b102.screen(i, "00", rng)) for i in range(12)]
                + [("end_P1", tone(b102.screen(50 + i, "00", rng), gain=0.7, offset=20)) for i in range(12)]
                + [("other", b102.other(i, rng)) for i in range(12)])
        root = self.tmp / "tone_only"
        labels = {"classes": TWO, "runs": {"r": write_run(root / "r", pics)}}
        spec, arrays, report = E.learn(root, labels)
        self.assertEqual(report["outcome_mask"]["px"], 0)
        for c in ("start", "end_P1"):
            self.assertEqual(report["classes"][c]["verdict"], "not separable from these frames")
            self.assertFalse(spec["separable"][c])
        r = E.Reader(spec, arrays).read(tone(b102.screen(99, "00", rng), gain=0.7, offset=20))
        self.assertEqual((r["screen"], r["class"]), (True, "unknown"))              # never named

    def test_a_tally_whose_tone_alone_differs_is_told_apart_disclosed(self):
        """Ranked against the picture's own screen-mask tone, a dimmer tally is a different picture."""
        rng = np.random.default_rng(6)
        pics = ([("start", b102.screen(i, "00", rng)) for i in range(12)]
                + [("end_P1", dim_digits(b102.screen(50 + i, "00", rng))) for i in range(12)]
                + [("other", b102.other(i, rng)) for i in range(12)])
        root = self.tmp / "patch_tone"
        labels = {"classes": TWO, "runs": {"r": write_run(root / "r", pics)}}
        spec, arrays, report = E.learn(root, labels)
        self.assertEqual(report["classes"]["end_P1"]["verdict"], "separable")
        r = E.Reader(spec, arrays).read(dim_digits(b102.screen(99, "00", rng)))
        self.assertEqual(r["class"], "end_P1")

    def test_a_picture_inside_black_bars_of_another_size_reads_as_the_bare_picture(self):
        img = b102.screen(500, "10", self.rng)
        bare = self.reader().read(img)
        for size, scale in (((1200, 520), 2.0), ((W, H + 200), 1.0), ((1920, 1080), 1080 / H), ((W + 160, H), 1.0)):
            win = window(img, size, scale)
            got, want = E.game_area(win).size, (round(W * scale), round(H * scale))
            self.assertLessEqual(max(abs(got[0] - want[0]), abs(got[1] - want[1])), 2, (size, got, want))
            r = self.reader().read(win)
            self.assertEqual((r["screen"], r["class"], r["searched"]), (True, "end_P1", False), (size, r))
            self.assertLess(abs(r["distances"]["screen"] - bare["distances"]["screen"]), 0.02)
        for kw in (dict(offset=30), dict(offset=-30), dict(gain=0.8), dict(gamma=1.25, offset=20)):    # amendment 4
            win = tone(window(img, (1200, 520), 2.0), **kw)                    # the bars change tone with the rest
            got = E.game_area(win).size
            self.assertLessEqual(max(abs(got[0] - 640), abs(got[1] - 520)), 2, (kw, got))
            r = self.reader().read(win)
            self.assertEqual((r["screen"], r["class"], r["searched"]), (True, "end_P1", False), (kw, r))

    def test_a_games_own_dark_border_is_not_cut(self):
        img = b102.screen(510, "01", self.rng)
        top = img.copy()
        ImageDraw.Draw(top).rectangle((0, 0, W, 11), fill=0)                       # 12 rows (4.6 %), one side
        self.assertEqual(E.game_area(top).size, (W, H))
        left = img.copy()
        ImageDraw.Draw(left).rectangle((0, 0, 39, H), fill=0)                      # one side only: not a bar
        self.assertEqual(E.game_area(left).size, (W, H))
        both = img.copy()
        d = ImageDraw.Draw(both)
        d.rectangle((0, 0, W, 7), fill=0)
        d.rectangle((0, H - 8, W, H), fill=0)                                      # 3 % each side: kept
        self.assertEqual(E.game_area(both).size, (W, H))
        self.assertEqual(E.game_area(Image.new("L", (W, H), 0)).size, (W, H))       # black: nothing to cut to

    def test_a_flat_picture_is_never_the_screen(self):
        rng = np.random.default_rng(8)
        for img in (Image.new("L", (W, H), 128), Image.new("L", (W, H), 0),
                    Image.fromarray(np.clip(128 + rng.integers(-2, 3, (H, W)), 0, 255).astype(np.uint8), "L")):
            r = self.reader().read(img)
            self.assertFalse(r["screen"], r)
            self.assertTrue(r["flat"], r)

    def test_a_version_1_spec_is_refused_with_the_plain_line(self):
        d = self.tmp / "v1"
        d.mkdir()
        old = {k: v for k, v in self.spec.items() if k != "measure"}
        old["version"] = 1
        buf = io.BytesIO()
        np.savez_compressed(buf, **self.arrays)
        (d / "old.endscreen.npz").write_bytes(buf.getvalue())
        import hashlib
        old.update(arrays="old.endscreen.npz", arrays_sha256=hashlib.sha256(buf.getvalue()).hexdigest())
        (d / "old.endscreen.json").write_text(json.dumps(old))
        with self.assertRaises(ValueError) as cm:
            E.load_spec(d / "old.endscreen.json")
        self.assertEqual(str(cm.exception),
                         "this end-screen spec was learnt with the old measure (absolute grey levels): learn it again")
        with self.assertRaises(ValueError):
            E.Reader(old, self.arrays)
        r = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools" / "h7_endscreen.py"), "read",
                            str(d / "old.endscreen.json"), str(self.runs / "begin" / "f0005.png")],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual((r.returncode, r.stdout), (1, ""))
        self.assertIn("learn it again", r.stderr)
        other = dict(old, version=3)
        (d / "x.endscreen.json").write_text(json.dumps(other))
        with self.assertRaises(ValueError) as cm:
            E.load_spec(d / "x.endscreen.json")
        self.assertEqual(str(cm.exception), "not an end-screen spec this tool reads")

    def test_two_sources_of_different_sizes_and_tones_learnt_together(self):
        src = self.runs
        dst = self.tmp / "window_runs"
        for run in ("begin", "win1", "win2", "fight"):
            (dst / run).mkdir(parents=True)
            shutil.copyfile(src / run / "index.csv", dst / run / "index.csv")
            for p in (src / run).glob("*.png"):
                with Image.open(p) as im:
                    window(tone(im.convert("L"), gain=0.85, offset=-15, gamma=1.1), (1200, 520), 2.0).save(dst / run / p.name)
        spec, arrays, report = E.learn([(src, self.labels), (dst, self.labels)], None, half="first")
        self.assertEqual(set(report["frames_per_source"]), {"source_1", "source_2"})
        for c in ("start", "end_P1", "end_P2"):
            self.assertEqual(report["classes"][c]["verdict"], "separable")
        s = E.score([(src, self.labels), (dst, self.labels)], None, spec, arrays, half="second")
        self.assertEqual(s["other_read_as_screen"], 0)
        self.assertEqual(s["right"], {"start": [24, 24], "end_P1": [16, 16], "end_P2": [16, 16], "other": [38, 38]})
        self.assertEqual(s["right_per_source"]["source_2"]["end_P2"], [8, 8])

    def test_a_frame_unlike_its_label_does_not_set_the_threshold(self):
        """A slip (a 0-0 labelled 1-0) does not widen 1-0's threshold; it stays a foreign frame for 0-0 (strict),
        so 0-0 is said "not separable" at learning — loud at the desk, never a guess at the TV."""
        rng = np.random.default_rng(9)
        pics = ([("start", b102.screen(i, "00", rng)) for i in range(12)]
                + [("end_P1", b102.screen(50 + i, "10", rng)) for i in range(14)]
                + [("end_P1", b102.screen(70, "00", rng))]                          # a slip: a 0-0 labelled 1-0
                + [("end_P2", b102.screen(90 + i, "01", rng)) for i in range(12)]
                + [("other", b102.other(i, rng)) for i in range(12)])
        root = self.tmp / "slips"
        labels = {"classes": CLASSES, "runs": {"r": write_run(root / "r", pics)}}
        spec, arrays, report = E.learn(root, labels)
        self.assertEqual(report["unlike_label"], {"start": 0, "end_P1": 1, "end_P2": 0})
        self.assertEqual(report["classes"]["end_P1"]["unlike_label"], 1)
        self.assertLess(report["classes"]["end_P1"]["worst_own"], 0.05)              # the slip did not set it
        self.assertEqual(report["classes"]["end_P1"]["verdict"], "separable")
        self.assertEqual(report["classes"]["end_P2"]["verdict"], "separable")
        self.assertEqual(report["classes"]["start"]["verdict"], "not separable from these frames")
        rd = E.Reader(spec, arrays)
        self.assertEqual(rd.read(b102.screen(200, "10", rng))["class"], "end_P1")
        self.assertEqual(rd.read(b102.screen(201, "00", rng))["class"], "unknown")      # never guessed

    def test_a_labelled_screen_under_a_notice_does_not_loosen_the_screen(self):
        """Amendment 4: a 1-0 picture with a notice over the tally and the panel (nearest another class: unlike its
        label) sets neither 1-0's threshold nor the screen's."""
        rng = np.random.default_rng(12)

        def noticed(img):
            ImageDraw.Draw(img).rectangle((100, 120, 260, 215), fill=235)
            return img

        pics = ([("start", b102.screen(i, "00", rng)) for i in range(12)]
                + [("end_P1", b102.screen(30 + i, "10", rng)) for i in range(14)]
                + [("end_P1", noticed(b102.screen(50, "10", rng)))]
                + [("end_P2", b102.screen(60 + i, "01", rng)) for i in range(12)]
                + [("other", b102.other(i, rng)) for i in range(12)])
        root = self.tmp / "notice"
        labels = {"classes": CLASSES, "runs": {"r": write_run(root / "r", pics)}}
        spec, arrays, report = E.learn(root, labels)
        self.assertEqual(report["unlike_label"]["end_P1"], 1)
        self.assertLess(report["screen"]["worst_own"], 0.05, report["screen"])

    def test_a_stretch_that_comes_and_goes_within_a_class_is_not_the_outcome(self):
        """Amendment 3: a mark under the tally shown in half of one class's frames (a handicap bar) differs between
        the classes' means but is not steady within its class: it stays out of the outcome mask."""
        rng = np.random.default_rng(13)
        bar = (130, 200, 200, 214)

        def barred(img):
            ImageDraw.Draw(img).rectangle(bar, fill=250)
            return img

        pics = ([("start", b102.screen(i, "00", rng)) for i in range(12)]
                + [("end_P1", barred(b102.screen(30 + i, "10", rng)) if i % 2 else b102.screen(30 + i, "10", rng))
                   for i in range(14)]
                + [("end_P2", b102.screen(60 + i, "01", rng)) for i in range(12)]
                + [("other", b102.other(i, rng)) for i in range(12)])
        root = self.tmp / "stretch"
        labels = {"classes": CLASSES, "runs": {"r": write_run(root / "r", pics)}}
        spec, arrays, report = E.learn(root, labels)
        self.assertEqual(b102.mask_in(arrays["outcome_mask"], bar), 0)
        self.assertGreater(report["outcome_mask"]["px"], 0)
        for c in ("start", "end_P1", "end_P2"):
            self.assertEqual(report["classes"][c]["verdict"], "separable")

    def test_a_gap_smaller_than_the_minimum_is_not_separable(self):
        """Amendment 3: one source's 0-1 frames (identical, noiseless) against the other's 0-0: over the mask the
        first source could learn (the left digit) they differ only by picture noise — a tiny positive gap, never
        enough to name either."""
        rng = np.random.default_rng(14)
        one = ([("start", b102.screen(i, "00", rng)) for i in range(12)]
               + [("end_P1", b102.screen(30 + i, "10", rng)) for i in range(12)]
               + [("other", b102.other(i, rng)) for i in range(12)])
        clean = b102.screen(60, "01", rng)
        two = [("end_P2", clean.copy()) for _ in range(12)] + [("other", b102.other(40 + i, rng)) for i in range(6)]
        r1, r2 = self.tmp / "gap1", self.tmp / "gap2"
        l1 = {"classes": CLASSES, "runs": {"r": write_run(r1 / "r", one)}}
        l2 = {"classes": CLASSES, "runs": {"r": write_run(r2 / "r", two)}}
        spec, arrays, report = E.learn([(r1, l1), (r2, l2)], None)
        for c in ("start", "end_P2"):
            self.assertLess(report["classes"][c]["gap"], E.MIN_GAP, report["classes"][c])
            self.assertEqual(report["classes"][c]["verdict"], "not separable from these frames")
        self.assertEqual(report["classes"]["end_P1"]["verdict"], "separable")

    def test_a_labelled_screen_mostly_covered_does_not_set_the_screens_threshold(self):
        """Amendment 4: a 1-0 picture with most of the screen under a notice (its tally too: nearest 0-0) — its screen
        distance is a fight's; it must not set the screen's threshold."""
        rng = np.random.default_rng(15)

        def covered(img):
            ImageDraw.Draw(img).rectangle((0, 50, W, H), fill=235)
            return img

        pics = ([("start", b102.screen(i, "00", rng)) for i in range(12)]
                + [("end_P1", b102.screen(30 + i, "10", rng)) for i in range(14)]
                + [("end_P1", covered(b102.screen(50, "10", rng)))]
                + [("end_P2", b102.screen(60 + i, "01", rng)) for i in range(12)]
                + [("other", b102.other(i, rng)) for i in range(12)])
        root = self.tmp / "covered"
        labels = {"classes": CLASSES, "runs": {"r": write_run(root / "r", pics)}}
        spec, arrays, report = E.learn(root, labels)
        self.assertEqual(report["unlike_label"]["end_P1"], 1)
        self.assertEqual(report["screen"]["verdict"], "separable")
        self.assertLess(report["screen"]["worst_own"], 0.05, report["screen"])

    def test_a_changed_eighth_of_the_still_part_still_reads(self):
        """B102's median kept: a flat patch over ~12 % of the still part (other portraits) still reads — the median
        stays under the threshold where a mean would not. (The limit, stated in the record: ranks against the
        picture's own tone move when much of the still part changes; ~12-15 % is what this screen absorbs.)"""
        for i, (w, shade) in enumerate(((60, 128), (40, 250), (60, 0))):
            img = b102.screen(700 + i, "01", self.rng)
            ImageDraw.Draw(img).rectangle((0, 44, w, H), fill=shade)
            r = self.reader().read(img, search=False)
            self.assertEqual((r["screen"], r["class"]), (True, "end_P2"), (w, shade, r))

    def test_a_pair_never_seen_in_one_source_cannot_make_the_outcome_mask(self):
        rng = np.random.default_rng(10)

        def boxed(img, shade):
            ImageDraw.Draw(img).rectangle(CONFOUND_BOX, fill=shade)
            return img

        one = ([("start", boxed(b102.screen(i, "00", rng), 60)) for i in range(12)]
               + [("end_P1", boxed(b102.screen(30 + i, "10", rng), 60)) for i in range(12)]
               + [("other", b102.other(i, rng)) for i in range(12)])
        two = ([("end_P2", boxed(b102.screen(60 + i, "01", rng), 200)) for i in range(12)]
               + [("other", b102.other(40 + i, rng)) for i in range(6)])
        r1, r2 = self.tmp / "conf1", self.tmp / "conf2"
        l1 = {"classes": CLASSES, "runs": {"r": write_run(r1 / "r", one)}}
        l2 = {"classes": CLASSES, "runs": {"r": write_run(r2 / "r", two)}}
        spec, arrays, report = E.learn([(r1, l1), (r2, l2)], None)
        self.assertEqual(b102.mask_in(arrays["outcome_mask"], CONFOUND_BOX), 0)       # the "character" left out
        self.assertGreater(report["outcome_mask"]["px"], 0)                           # the left digit kept
        self.assertEqual(report["classes"]["end_P1"]["verdict"], "separable")
        self.assertEqual(report["classes"]["end_P2"]["verdict"], "not separable from these frames")
        rd = E.Reader(spec, arrays)
        self.assertNotEqual(rd.read(boxed(b102.screen(300, "00", rng), 200))["class"], "end_P2")
        self.assertNotEqual(rd.read(boxed(b102.screen(301, "01", rng), 60))["class"], "end_P2")

    def test_replay_says_when_ended_and_re_arms(self):
        rng = np.random.default_rng(11)
        seq = (["start"] * 5 + ["other"] * 6 + ["end_P1"] * 5 + ["other"] * 4 + ["start"] * 4 + ["other"] * 5
               + ["end_P2"] * 5)
        pics = [(c, b102.screen(i, TALLY[c], rng) if c != "other" else b102.other(i, rng)) for i, c in enumerate(seq)]
        folder = self.tmp / "replay_run"
        ranges = write_run(folder, [(c, window(tone(im, gain=0.9, offset=-10), (1200, 520), 2.0)) for c, im in pics])
        (folder / "labels.json").write_text(json.dumps({"classes": CLASSES, "runs": {"replay_run": ranges}}))
        for k, after in ((3, 2.0), (2, 1.0)):
            out = E.replay(folder, self.spec, self.arrays, k=k, labels=folder / "labels.json")
            self.assertEqual(out["end_screen_arrivals_s"], [11.0, 29.0])
            self.assertEqual([(e["class"], e["seconds"], e["after_end_screen_s"]) for e in out["ended"]],
                             [("end_P1", 11.0 + after, after), ("end_P2", 29.0 + after, after)])
            self.assertEqual([c for _t, c, _d in out["reads"]], seq)
            self.assertEqual([c for _t, c in out["changes"]],
                             ["start", "other", "end_P1", "other", "start", "other", "end_P2"])
        spec_path = self.tmp / "fixture.endscreen.json"
        E.save_spec(self.spec, self.arrays, spec_path)
        r = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools" / "h7_endscreen.py"), "replay", str(folder),
                            str(spec_path), "--k", "3"], capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [json.loads(x) for x in r.stdout.splitlines()]
        self.assertEqual(sum(1 for x in lines if "seconds" in x and "class" in x and "ended" not in x), len(seq))
        self.assertEqual([x["ended"] for x in lines if "ended" in x], ["end_P1", "end_P2"])
        self.assertEqual(lines[-1]["summary"]["end_screen_arrivals_s"], [11.0, 29.0])

    def test_one_read_is_milliseconds(self):
        for img in (b102.screen(600, "10", self.rng), window(b102.screen(601, "10", self.rng), (1920, 1080), 1080 / H)):
            rd = self.reader()
            rd.read(img)
            times = []
            for _ in range(15):
                t0 = time.perf_counter()
                rd.read(img)
                times.append(time.perf_counter() - t0)
            self.assertLess(float(np.median(times)), 0.05)


if __name__ == "__main__":
    unittest.main()
