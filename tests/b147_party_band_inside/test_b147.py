#!/usr/bin/env python3
"""B147 (host): the practice band inside the frame's inner 90 % — through the real HTTP server on loopback.

PP-H3d, the user: "The practice band was there (maybe a little too high, it was partially cut off)". The app fits the
whole 16:9 frame to its full-screen surface (no crop, no zoom): the cut is the TV's overscan. B147: the same words, the
box's top at h*5/100, as wide as the words — rows 36-85 of 720, columns 379-899 on the 720p profile (B151's longer
words "PRACTICE — press Select (Share) to go back": columns 318-960).

- **The commands** (B143's `b143` scenario of B114's harness, mine and HEAD's): the two practices' commands carry the
  new band (its `y=h*5/100+10`, `boxborderw=10|16|10|16`); the real goes', the ways back' and the onn's own start's
  commands equal HEAD's at the same step.
- **The output frame** (no display needed): a made-up 4:3 picture as the source of the practice command's own `-vf`
  (`hwupload` swapped for an RGB frame out) against the same chain without the band: the rows above h*5/100 and the
  columns within w*5/100 of either side equal within 2 grey levels (B144's bound); the changed rows inside 36-90;
  every changed pixel inside the inner 90 %; the box only as wide as the words (B151: inside a centred 4:3 picture's
  columns; was < half the frame, which the longer words pass by 3 px); the text's white
  pixels in it. The same at the 1080 rung's size.
- The flags absent: B114's flag test (run with the suites). Temp dirs removed.

    python3 -m unittest discover -s tests/b147_party_band_inside -v
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b143_party_audio_switch"))
sys.path.insert(0, str(ROOT / "companion"))
import test_b143 as b143  # noqa: E402  (its scenario runner; its tests are not collected here)
import native_stream as ns  # noqa: E402


def vf_of(argv: list) -> str:
    return argv[argv.index("-vf") + 1]


class Commands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mine = b143.run_mode(None)["b143_starts"]
        cls.head = b143.run_mode(b143.BASELINE)["b143_starts"]

    def test_the_practices_carry_the_new_band_and_nothing_else_changed(self):
        self.assertEqual(len(self.mine), 9)
        self.assertIn("y=h*5/100+10", ns.PARTY_BANNER_FILTER)
        self.assertIn("boxborderw=10|16|10|16", ns.PARTY_BANNER_FILTER)
        for i, s in enumerate(self.mine):
            has = ns.PARTY_BANNER_FILTER in vf_of(s["argv"])
            self.assertEqual(has, i in (3, 5), (i, vf_of(s["argv"])))
        for i in (0, 1, 2, 4, 6, 7, 8):                     # the onn's start, real goes, ways back: HEAD's
            self.assertEqual(self.mine[i]["argv"], self.head[i]["argv"], i)


@unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
class OutputFrame(unittest.TestCase):
    def frame(self, tmp: Path, size: tuple[int, int], banner: bool):
        import numpy as np
        from PIL import Image
        m = object.__new__(ns.NativeStreamManager)
        m._apply_profile_selection()
        m._linux_display = lambda: ":0"
        m._linux_vaapi_device = lambda: "/fixture/renderD128"
        m._party_banner_on = banner
        w, h = size
        vf = vf_of(m._build_linux_ffmpeg_command(ffmpeg=Path("/fixture/ffmpeg"), capture_target={"_window_id": 1},
                                                 width=w, height=h)).replace(",hwupload", ",format=rgb24")
        out = tmp / f"{w}_{int(banner)}.png"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(tmp / "made_up.png"),
                        "-vf", vf, "-frames:v", "1", "-y", str(out)], check=True, timeout=60)
        return np.asarray(Image.open(out).convert("L")).astype(int)

    def test_the_band_inside_the_inner_ninety_percent(self):
        import numpy as np
        from PIL import Image
        tmp = Path(tempfile.mkdtemp(prefix="b147_"))
        try:
            rng = np.random.default_rng(147)                       # a made-up 4:3 picture: blocks of grey and colour
            blocks = rng.integers(60, 230, size=(12, 16, 3), dtype=np.uint8)
            Image.fromarray(np.kron(blocks, np.ones((60, 60, 1), dtype=np.uint8))).save(tmp / "made_up.png")
            for (w, h), rows in (((1280, 720), (36, 90)), ((1920, 1080), (54, 135))):
                a, b = self.frame(tmp, (w, h), True), self.frame(tmp, (w, h), False)
                self.assertEqual(a.shape, (h, w))
                d = np.abs(a - b) > 2
                ys, xs = np.where(d)
                top, side = h * 5 // 100, w * 5 // 100
                self.assertGreaterEqual(int(ys.min()), top, (w, h))            # nothing above h*5/100
                self.assertLessEqual(int(ys.max()), rows[1], (w, h))
                self.assertGreaterEqual(int(xs.min()), side, (w, h))           # nothing within w*5/100 of a side
                self.assertLessEqual(int(xs.max()), w - side - 1, (w, h))
                self.assertLessEqual(int(np.abs(a[:top] - b[:top]).max()), 2)  # above: the source's own, within 2
                self.assertLessEqual(int(np.abs(a[:, :side] - b[:, :side]).max()), 2)
                self.assertLessEqual(int(np.abs(a[:, w - side:] - b[:, w - side:]).max()), 2)
                pic = (w - h * 4 // 3) // 2                                     # B151: as wide as the words, inside
                self.assertGreaterEqual(int(xs.min()), pic, (w, h))             # a centred 4:3 picture's columns
                self.assertLessEqual(int(xs.max()), w - pic - 1, (w, h))
                box = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                self.assertGreater(int((box > 200).sum()), 300)                 # the text's white pixels
                if (w, h) == (1280, 720):
                    self.assertEqual((int(ys.min()), int(ys.max())), (36, 85))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
