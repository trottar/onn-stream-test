#!/usr/bin/env python3
"""C5-M1: the 1080p60 candidate profile and PRIVYHUB_NATIVE_PROFILE_ID.

    python3 -m unittest tools/test_c5_m1_profile_selector.py -v

The real NativeStreamManager argv builder runs on an instance made with
object.__new__ (nothing spawned, no relay, no files); display, VAAPI node
and window id are fixed stand-ins.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "companion"))

import native_stream as ns  # noqa: E402
import native_stream_profiles as nsp  # noqa: E402

ENV = "PRIVYHUB_NATIVE_PROFILE_ID"

# The adopted profile's to_dict() and argv before C5-M1 (golden_before.txt).
ADOPTED_DICT = {
    "id": "native_game_720p60_reference", "width": 1280, "height": 720,
    "fps": 60, "bitrate_kbps": 7000, "max_bitrate_kbps": 7000,
    "gop_frames": 15, "bframes": 0, "fec_group_size": 8,
    "max_frame_size_bytes": 90000, "audio_queue_target_packets": 12,
    "audio_queue_capacity_packets": 17, "audio_redundancy_copies": 2,
    "audio_redundancy_offset_packets": 4,
}
ADOPTED_ARGV = (
    "/usr/bin/ffmpeg -hide_banner -loglevel info -nostdin -vaapi_device "
    "/dev/dri/renderD128 -f x11grab -framerate 60 -window_id 12345 -i :0 -vf "
    "scale=1280:720:force_original_aspect_ratio=decrease:flags=fast_bilinear,"
    "pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,format=nv12,hwupload -an -c:v "
    "h264_vaapi -profile:v high -b:v 7000k -maxrate 7000k -bufsize 7000k "
    "-max_frame_size 90000 -g 15 -bf 0 -payload_type 96 -f rtp "
    "rtp://127.0.0.1:48110?pkt_size=1200"
)


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    env.update(extra)
    return mock.patch.dict(os.environ, env, clear=True)


def manager():
    M = ns.NativeStreamManager
    m = object.__new__(M)
    m._apply_profile_selection()
    return m


def argv(m):
    with mock.patch.object(ns.NativeStreamManager, "_linux_display", staticmethod(lambda: ":0")), \
         mock.patch.object(ns.NativeStreamManager, "_linux_vaapi_device",
                           staticmethod(lambda: Path("/dev/dri/renderD128"))):
        return " ".join(m._build_linux_ffmpeg_command(Path("/usr/bin/ffmpeg"), {"_window_id": 12345}))


class Profiles(unittest.TestCase):
    def test_adopted_unchanged(self):
        self.assertEqual(nsp.NATIVE_GAME_720P60_REFERENCE.to_dict(), ADOPTED_DICT)
        self.assertIs(ns.NativeStreamManager.PROFILE, nsp.NATIVE_GAME_720P60_REFERENCE)

    def test_candidate_validates_and_is_as_designed(self):
        c = nsp.NATIVE_GAME_1080P60_CANDIDATE
        nsp.NativeStreamProfile(**c.to_dict())  # __post_init__ passes
        self.assertEqual(
            (c.id, c.width, c.height, c.fps, c.bitrate_kbps, c.max_bitrate_kbps,
             c.gop_frames, c.bframes, c.fec_group_size, c.max_frame_size_bytes),
            ("native_game_1080p60_candidate", 1920, 1080, 60, 15750, 15750, 15, 0, 8, 200_000))
        a = nsp.NATIVE_GAME_720P60_REFERENCE
        for f in ("audio_queue_target_packets", "audio_queue_capacity_packets",
                  "audio_redundancy_copies", "audio_redundancy_offset_packets"):
            self.assertEqual(getattr(c, f), getattr(a, f), f)


class Selector(unittest.TestCase):
    def test_unset_and_empty_are_the_adopted_profile(self):
        for env in ({}, {ENV: ""}, {ENV: "   "}):
            p, info = nsp.select_native_profile(env)
            self.assertIs(p, nsp.NATIVE_GAME_720P60_REFERENCE)
            self.assertEqual((info["source"], info["requested"], info["profile_id_ignored"]),
                             ("default", None, False))

    def test_known_id(self):
        p, info = nsp.select_native_profile({ENV: " native_game_1080p60_candidate "})
        self.assertIs(p, nsp.NATIVE_GAME_1080P60_CANDIDATE)
        self.assertEqual(info["source"], ENV)

    def test_unknown_id_is_ignored_and_flagged(self):
        p, info = nsp.select_native_profile({ENV: "native_game_4k"})
        self.assertIs(p, nsp.NATIVE_GAME_720P60_REFERENCE)
        self.assertTrue(info["profile_id_ignored"])


class Manager(unittest.TestCase):
    def test_golden_unset_argv_identical(self):
        with clean_env():
            m = manager()
            self.assertEqual(argv(m), ADOPTED_ARGV)
            self.assertFalse(m.encoder_overrides()["any_override"])
            self.assertIsNone(m.encoder_overrides()["profile_id_override"])

    def test_candidate_argv_changes_only_size_bitrate_cap(self):
        with clean_env(**{ENV: "native_game_1080p60_candidate"}):
            m = manager()
            got = argv(m)
            ov = m.encoder_overrides()
        want = (ADOPTED_ARGV.replace("scale=1280:720", "scale=1920:1080")
                .replace("pad=1280:720", "pad=1920:1080")
                .replace("7000k", "15750k").replace("-max_frame_size 90000", "-max_frame_size 200000"))
        self.assertEqual(got, want)
        self.assertTrue(ov["any_override"])
        self.assertEqual(ov["profile_id_override"], "native_game_1080p60_candidate")
        self.assertEqual((m.WIDTH, m.HEIGHT, m.BITRATE_KBPS, m.PROFILE.id),
                         (1920, 1080, 15750, "native_game_1080p60_candidate"))
        # the class keeps the adopted profile; only this instance is shadowed
        self.assertIs(ns.NativeStreamManager.PROFILE, nsp.NATIVE_GAME_720P60_REFERENCE)
        self.assertEqual(ns.NativeStreamManager.BITRATE_KBPS, 7000)

    def test_unknown_id_keeps_adopted_argv_but_counts_as_override(self):
        with clean_env(**{ENV: "nonsense"}):
            m = manager()
            self.assertEqual(argv(m), ADOPTED_ARGV)
            self.assertTrue(m.encoder_overrides()["any_override"])
            self.assertTrue(m._profile_selection["profile_id_ignored"])


class C5M2Arms(unittest.TestCase):
    """C5-M2: the three 1080p60 follow-up arms (handoffs/C5-M2_1080P60_FOLLOWUP_ARMS_TASK.md)."""
    ARMS = {
        "native_game_1080p60_c1_parity_cap90": (15750, 90_000),
        "native_game_1080p60_c2_80pct_cap160": (12600, 160_000),
        "native_game_1080p60_c3_80pct_cap90": (12600, 90_000),
    }

    def test_each_arm_is_as_the_task_names_it(self):
        a = nsp.NATIVE_GAME_720P60_REFERENCE
        for pid, (kbps, cap) in self.ARMS.items():
            p = nsp.NATIVE_STREAM_PROFILES[pid]
            nsp.NativeStreamProfile(**p.to_dict())
            self.assertEqual((p.width, p.height, p.fps, p.bitrate_kbps, p.max_bitrate_kbps, p.gop_frames, p.bframes,
                              p.fec_group_size, p.max_frame_size_bytes),
                             (1920, 1080, 60, kbps, kbps, 15, 0, 8, cap), pid)
            for f in ("audio_queue_target_packets", "audio_queue_capacity_packets",
                      "audio_redundancy_copies", "audio_redundancy_offset_packets"):
                self.assertEqual(getattr(p, f), getattr(a, f), (pid, f))

    def test_selected_only_by_the_env_and_the_argv_follows(self):
        for pid, (kbps, cap) in self.ARMS.items():
            with clean_env(**{ENV: pid}):
                m = manager()
                cmd = argv(m)
                ov = m.encoder_overrides()
            self.assertIn("scale=1920:1080:", cmd)
            self.assertIn(f"-b:v {kbps}k -maxrate {kbps}k -bufsize {kbps}k", cmd)
            self.assertIn(f"-max_frame_size {cap} -g 15 -bf 0", cmd)
            self.assertTrue(ov["any_override"])

    def test_unset_is_still_the_adopted_argv(self):
        with clean_env():
            self.assertEqual(argv(manager()), ADOPTED_ARGV)


class C5M3LowRungs(unittest.TestCase):
    """C5-M3: the three low rungs (handoffs/C5-M3_LOW_RUNG_SCREENING_TASK.md)."""
    ARMS = {"native_game_720p60_4000": (1280, 720, 4000), "native_game_720p60_3000": (1280, 720, 3000),
            "native_game_540p60_3500": (960, 540, 3500)}

    def test_each_rung_is_as_the_task_names_it(self):
        a = nsp.NATIVE_GAME_720P60_REFERENCE
        for pid, (w, h, kbps) in self.ARMS.items():
            p = nsp.NATIVE_STREAM_PROFILES[pid]
            nsp.NativeStreamProfile(**p.to_dict())
            self.assertEqual((p.width, p.height, p.fps, p.bitrate_kbps, p.max_bitrate_kbps, p.gop_frames, p.bframes,
                              p.fec_group_size, p.max_frame_size_bytes), (w, h, 60, kbps, kbps, 15, 0, 8, 90_000), pid)
            for f in ("audio_queue_target_packets", "audio_queue_capacity_packets",
                      "audio_redundancy_copies", "audio_redundancy_offset_packets"):
                self.assertEqual(getattr(p, f), getattr(a, f), (pid, f))

    def test_argv_follows_and_unset_is_still_adopted(self):
        for pid, (w, h, kbps) in self.ARMS.items():
            with clean_env(**{ENV: pid}):
                m = manager()
                cmd = argv(m)
                ov = m.encoder_overrides()
            self.assertIn(f"scale={w}:{h}:", cmd)
            self.assertIn(f"pad={w}:{h}:", cmd)
            self.assertIn(f"-b:v {kbps}k -maxrate {kbps}k -bufsize {kbps}k -max_frame_size 90000 -g 15 -bf 0", cmd)
            self.assertTrue(ov["any_override"])
        with clean_env():
            self.assertEqual(argv(manager()), ADOPTED_ARGV)

    def test_none_is_on_the_live_ladder(self):
        import adaptive_bitrate as ab
        for pid, (_, _, kbps) in self.ARMS.items():
            self.assertNotIn(kbps, ab.LADDER_KBPS)


if __name__ == "__main__":
    unittest.main()
