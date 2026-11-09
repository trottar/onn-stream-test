#!/usr/bin/env python3
"""B70 (host): the hub's X pointer is not drawn into the capture -- x11grab gets `-draw_mouse 0` by default;
PRIVYHUB_CAPTURE_POINTER=1 keeps today's argv byte for byte.

    python3 -m unittest discover -s tests/b70_capture_pointer -v

The real `_build_linux_ffmpeg_command` on an instance made with object.__new__ (nothing spawned); the display, the
VAAPI node and the window id are fixed stand-ins (as C5-M1's suite). No temp dir is made.
"""

from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import native_stream as ns  # noqa: E402

ENV = "PRIVYHUB_CAPTURE_POINTER"
# today's argv (C5-M1's golden, the adopted 720p60 profile): what =1 must give back byte for byte
TODAY = (
    "/usr/bin/ffmpeg -hide_banner -loglevel info -nostdin -vaapi_device "
    "/dev/dri/renderD128 -f x11grab -framerate 60 -window_id 12345 -i :0 -vf "
    "scale=1280:720:force_original_aspect_ratio=decrease:flags=fast_bilinear,"
    "pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,format=nv12,hwupload -an -c:v "
    "h264_vaapi -profile:v high -b:v 7000k -maxrate 7000k -bufsize 7000k "
    "-max_frame_size 90000 -g 15 -bf 0 -payload_type 96 -f rtp "
    "rtp://127.0.0.1:48110?pkt_size=1200"
)


def env(value=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    if value is not None:
        e[ENV] = value
    return mock.patch.dict(os.environ, e, clear=True)


def manager():
    m = object.__new__(ns.NativeStreamManager)
    m._apply_profile_selection()
    return m


def argv(**kw):
    with mock.patch.object(ns.NativeStreamManager, "_linux_display", staticmethod(lambda: ":0")), \
         mock.patch.object(ns.NativeStreamManager, "_linux_vaapi_device",
                           staticmethod(lambda: Path("/dev/dri/renderD128"))):
        return manager()._build_linux_ffmpeg_command(Path("/usr/bin/ffmpeg"), {"_window_id": 12345}, **kw)


class CapturePointer(unittest.TestCase):
    def test_default_draws_no_pointer(self):
        for value in (None, "0", "", "yes", "2", " 0 "):
            with self.subTest(value=value), env(value):
                a = argv()
                self.assertEqual(a.count("-draw_mouse"), 1)
                i = a.index("-draw_mouse")
                self.assertEqual(a[i + 1], "0")
                self.assertLess(a.index("-f"), i)                      # an x11grab input option ...
                self.assertLess(i, a.index("-window_id"))              # ... before the window and the input
                self.assertLess(i, a.index("-i"))
                # nothing else moved: removing the pair gives today's argv
                self.assertEqual(" ".join(a[:i] + a[i + 2:]), TODAY)

    def test_one_keeps_today_byte_for_byte(self):
        for value in ("1", " 1 "):
            with self.subTest(value=value), env(value):
                self.assertEqual(" ".join(argv()), TODAY)
                self.assertNotIn("-draw_mouse", argv())

    def test_sized_and_rate_paths_carry_it(self):
        with env():
            a = argv(width=1920, height=1080, bitrate_kbps=9000, max_bitrate_kbps=9000)
            self.assertEqual(a[a.index("-draw_mouse") + 1], "0")
        with env("1"):
            self.assertNotIn("-draw_mouse", argv(width=1920, height=1080, bitrate_kbps=9000, max_bitrate_kbps=9000))

    def test_the_helper_is_the_only_reader(self):
        src = (ROOT / "companion" / "native_stream.py").read_text()
        self.assertEqual(src.count('"PRIVYHUB_CAPTURE_POINTER"'), 1)
        tree = ast.parse(src)
        users = [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "CAPTURE_POINTER_ENV"]
        self.assertEqual(len(users), 2)                                 # its assignment, the helper's read
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_capture_pointer_args"]
        self.assertEqual(len(calls), 1)                                 # one call: the Linux builder's
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_build_linux_ffmpeg_command")
        self.assertTrue(any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_capture_pointer_args"
                            for n in ast.walk(fn)))


if __name__ == "__main__":
    unittest.main()
