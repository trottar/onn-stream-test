#!/usr/bin/env python3
"""B144 (host): a practice banner on the onn's picture only — through the real HTTP server on loopback.

The user at PP-H3c: "it's hard to tell if we're in practice since they have the same screen so maybe a hub side banner
at the top (unless that messes with the vision model)". B144: while a practice plays, the encoder's own filter draws
"PRACTICE — press Select (Share) to go back" (B151; was "… press Start …") across the top of the stream's picture (after format=nv12, before hwupload); the
title's window is never drawn on (the watcher reads the window, not the stream).

- **The encoder's commands** (B143's `b143` mode of B114's scenario: the real routes, the real
  `NativeStreamManager._start_linux_locked` on G8-S2's stubs behind the stream stub, every start's command recorded):
  the two practices' switches carry the band; the real goes', the ways back' and the users' own start's do not, and
  each of those equals HEAD's command at the same step (the same scenario on HEAD's companion); the practice's command
  with the band taken out equals the real go's.
- **The title's window untouched / the band in the output frame** (needs the hub's display, `DISPLAY=:0` or the
  environment's; skipped without X): a made-up 960 × 720 window showing a known picture, grabbed by its id with the
  stream's own x11grab arguments: the window's own picture (no band); the practice command's own `-vf` (its
  `hwupload` swapped for an RGB frame out) on that grab: the band's rows (B147: 36-85 of 720) differ from the same chain
  without the band, every other row equal within 2 grey levels, the text's white pixels inside the band.
- The flags absent: B114's flag test (run with the suites). Temp dirs removed.

    python3 -m unittest discover -s tests/b144_party_practice_banner -v
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b143_party_audio_switch"))
sys.path.insert(0, str(ROOT / "companion"))
import test_b143 as b143  # noqa: E402  (its scenario runner; its tests are not collected here)

BANNER_TEXT = "PRACTICE — press Select (Share) to go back"   # B151


def vf_of(argv: list) -> str:
    return argv[argv.index("-vf") + 1]


class EncoderCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mine = b143.run_mode(None)["b143_starts"]
        cls.head = b143.run_mode(b143.BASELINE)["b143_starts"]

    def test_0_the_steps(self):
        # 0 the board (the onn's own start), a2: 1 real go, 2 back; a5: 3 practice, 4 back, 5 practice, 6 back,
        # 7 real go, 8 back
        self.assertEqual([s["board"] for s in self.mine], [True, False, True, False, True, False, True, False, True])
        self.assertEqual([s["board"] for s in self.head], [s["board"] for s in self.mine])

    def test_1_only_the_practices_carry_the_band(self):
        for i, s in enumerate(self.mine):
            has = BANNER_TEXT in vf_of(s["argv"])
            self.assertEqual(has, i in (3, 5), (i, vf_of(s["argv"])))
            if has:
                self.assertIn("format=nv12,drawtext=", vf_of(s["argv"]))
                self.assertTrue(vf_of(s["argv"]).endswith(",hwupload"))

    def test_2_every_other_command_is_heads(self):
        for i in (0, 1, 2, 4, 6, 7, 8):
            self.assertEqual(self.mine[i]["argv"], self.head[i]["argv"], i)
        import native_stream as ns
        for i in (3, 5):
            argv = list(self.mine[i]["argv"])
            k = argv.index("-vf")
            argv[k + 1] = argv[k + 1].replace("," + ns.PARTY_BANNER_FILTER, "")
            self.assertEqual(argv, self.mine[7]["argv"], i)            # the band is the only difference

    def test_3_head_never_draws_it(self):
        self.assertFalse(any(BANNER_TEXT in vf_of(s["argv"]) for s in self.head))


WINDOW = r'''
import sys, tkinter as tk
from PIL import Image, ImageTk
img = Image.open(sys.argv[1])
root = tk.Tk(); root.overrideredirect(True); root.geometry("960x720+40+40")
c = tk.Canvas(root, width=960, height=720, highlightthickness=0, bd=0); c.pack()
ph = ImageTk.PhotoImage(img); c.create_image(0, 0, anchor="nw", image=ph)
root.update(); print(c.winfo_id(), flush=True)
root.after(int(float(sys.argv[2]) * 1000), root.destroy); root.mainloop()
'''


@unittest.skipUnless(shutil.which("ffmpeg") and (os.environ.get("DISPLAY") or Path("/tmp/.X11-unix/X0").exists()),
                     "no ffmpeg or no X display")
class WindowAndFrame(unittest.TestCase):
    def test_window_untouched_and_the_band_in_the_output(self):
        import numpy as np
        from PIL import Image
        import native_stream as ns
        tmp = Path(tempfile.mkdtemp(prefix="b144_"))
        env = dict(os.environ, DISPLAY=os.environ.get("DISPLAY") or ":0")
        try:
            rng = np.random.default_rng(144)                           # a made-up picture: blocks of grey and colour
            blocks = rng.integers(40, 216, size=(12, 16, 3), dtype=np.uint8)
            pic = np.kron(blocks, np.ones((60, 60, 1), dtype=np.uint8))
            Image.fromarray(pic).save(tmp / "made_up.png")
            w = subprocess.Popen([sys.executable, "-c", WINDOW, str(tmp / "made_up.png"), "6"], env=env,
                                 stdout=subprocess.PIPE, text=True)
            wid = int(w.stdout.readline().strip())
            time.sleep(0.8)
            grab = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-f", "x11grab", "-framerate", "60",
                    "-draw_mouse", "0", "-window_id", str(wid), "-i", env["DISPLAY"]]
            m = object.__new__(ns.NativeStreamManager)
            m._apply_profile_selection()
            m._linux_display = lambda: env["DISPLAY"]
            m._linux_vaapi_device = lambda: "/fixture/renderD128"
            m._party_banner_on = True
            practice_vf = vf_of(m._build_linux_ffmpeg_command(ffmpeg=Path("/fixture/ffmpeg"),
                                                             capture_target={"_window_id": wid}))
            m._party_banner_on = False
            plain_vf = vf_of(m._build_linux_ffmpeg_command(ffmpeg=Path("/fixture/ffmpeg"),
                                                          capture_target={"_window_id": wid}))
            self.assertIn(BANNER_TEXT, practice_vf)
            self.assertNotIn(BANNER_TEXT, plain_vf)
            subprocess.run(grab + ["-frames:v", "1", "-y", str(tmp / "window.png")], check=True, env=env, timeout=30)
            for name, vf in (("practice", practice_vf), ("plain", plain_vf)):
                vf_rgb = vf.replace(",hwupload", ",format=rgb24")
                subprocess.run(grab + ["-vf", vf_rgb, "-frames:v", "1", "-y", str(tmp / f"{name}.png")], check=True,
                               env=env, timeout=30)
            w.wait(timeout=15)
            w.stdout.close()
            win = np.asarray(Image.open(tmp / "window.png").convert("RGB")).astype(int)
            self.assertEqual(win.shape[:2], (720, 960))
            self.assertLessEqual(int(np.abs(win - pic.astype(int)).max()), 2)     # the window's own picture: no band
            a = np.asarray(Image.open(tmp / "practice.png").convert("L")).astype(int)
            b = np.asarray(Image.open(tmp / "plain.png").convert("L")).astype(int)
            self.assertEqual(a.shape, (720, 1280))
            diff_rows = [y for y in range(720) if np.abs(a[y] - b[y]).max() > 2]
            # B147: the band inside the inner 90 % — rows 36-85 of 720 (B144's was 0-58)
            self.assertTrue(diff_rows and min(diff_rows) >= 36 and max(diff_rows) <= 90, (diff_rows[:3], diff_rows[-3:]))
            self.assertLessEqual(int(np.abs(a[:36] - b[:36]).max()), 2)           # above it equal
            self.assertLessEqual(int(np.abs(a[91:] - b[91:]).max()), 2)           # below it equal
            band = a[36:86, 160:1120]
            self.assertGreater(int((band > 200).sum()), 500)                      # the text's white pixels
            self.assertLess(float(band[band <= 200].mean()), float(b[36:86, 160:1120].mean()))   # the box darker
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
