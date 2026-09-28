#!/usr/bin/env python3
"""C3-F1: recovery's encoder restart at any ladder level -- unit tests (no session).

    python3 -m unittest tools/test_c3_f1_recovery_restart.py -v

The real `_run_c3_linux_bitrate_cycle` and the real
`NativeStreamManager._build_linux_ffmpeg_command` run against a fake
manager: fake encoder processes, a fake FEC relay whose packet counter
advances, fake session I/O. Nothing is spawned and nothing touches a socket.
"""

from __future__ import annotations

import os
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "companion"))

import native_stream as ns  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

LEVELS = (5000, 5500, 6000, 7000)


class FakeProc:
    def __init__(self, argv=None):
        self.argv = argv

    def poll(self):
        return None


class Watched:
    """Records every method called on it, other than the allowed reads."""

    def __init__(self, name, allowed):
        self._name, self._allowed, self.calls = name, set(allowed), []

    def __getattr__(self, item):
        if item.startswith("_"):
            raise AttributeError(item)

        def f(*a, **k):
            self.calls.append(item)
            return self._reply(item)
        return f


class FakeRelay(Watched):
    def __init__(self):
        super().__init__("relay", {"status"})
        self.running = True
        self._packets = 0

    def _reply(self, item):
        if item == "status":
            self._packets += 5
            return {"running": True, "rtp_packets": self._packets, "send_errors": 0}
        return None


class FakeSessionIO(Watched):
    def __init__(self):
        super().__init__("session_io", {"status"})

    def _reply(self, item):
        if item == "status":
            return {"audio": {"active": True, "send_errors": 0},
                    "controller": {"active": True, "bad_packets": 0}}
        return None


def fake_manager(level):
    m = ns.NativeStreamManager.__new__(ns.NativeStreamManager)
    m._lock = threading.RLock()
    m.project_root = ROOT
    m._active_bitrate_kbps = level
    m._fec_relay = FakeRelay()
    m._session_io = FakeSessionIO()
    m._process = FakeProc()
    m._capture_process = None
    m._log_handle = open(os.devnull, "w")
    m._client_port = 48100
    m._capture_target = {"_window_id": 4242, "pid": os.getpid(), "width": 1280, "height": 720}
    m.killed = []
    m._reap_locked = lambda: None
    m._running_locked = lambda: True
    m._linux_host = lambda: True
    m._find_ffmpeg = lambda: "/usr/bin/ffmpeg"
    m._linux_display = lambda: ":0"
    m._linux_xdotool = lambda: "/usr/bin/xdotool"
    m._linux_vaapi_device = lambda: "/dev/dri/renderD128"
    m._kill_managed_process = lambda p: m.killed.append(p)
    return m


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        self.t += 0.1
        return self.t


def run_restart(m):
    spawned = []

    def popen(argv, **kw):
        p = FakeProc(argv)
        spawned.append(p)
        return p
    clock = Clock()
    out = probe.run_c3_linux_recovery_restart(
        m, popen_factory=popen, monotonic=clock, sleep=lambda s: None,
        perf_counter_ns=lambda: int(clock() * 1e9))
    return out, spawned


def argv_rate(argv, flag):
    return argv[argv.index(flag) + 1]


class RecoveryRestartTests(unittest.TestCase):

    def test_restart_at_each_level_keeps_the_level(self):
        """Rule: at 5000/5500/6000/7000 the recovery primitive rebuilds the argv at
        exactly that level (-b:v and -maxrate), and the level stays the active one."""
        for level in LEVELS:
            m = fake_manager(level)
            out, spawned = run_restart(m)
            self.assertEqual(len(spawned), 1, level)
            argv = spawned[0].argv
            self.assertEqual(argv_rate(argv, "-b:v"), f"{level}k", level)
            self.assertEqual(argv_rate(argv, "-maxrate"), f"{level}k", level)
            self.assertEqual(m._active_bitrate_kbps, level)
            self.assertEqual((out["from_bitrate_kbps"], out["target_bitrate_kbps"]), (level, level))
            self.assertEqual(out["schema"], probe.RECOVERY_SCHEMA)
            self.assertEqual(out["mode"], probe.RECOVERY_MODE)

    def test_restart_touches_only_the_encoder(self):
        """Rule: only the FFmpeg process is replaced -- the relay and session I/O
        (audio, controller) are read, never stopped or started."""
        for level in LEVELS:
            m = fake_manager(level)
            old = m._process
            run_restart(m)
            self.assertEqual(m.killed, [old])
            self.assertEqual(set(m._fec_relay.calls), {"status"})
            self.assertEqual(set(m._session_io.calls), {"status"})
            self.assertTrue(m._fec_relay.running)

    def test_restart_refuses_an_unvalidated_level(self):
        """Rule: the recovery path only runs at a validated ladder level."""
        m = fake_manager(4000)
        with self.assertRaises(RuntimeError):
            run_restart(m)

    def test_manager_dispatch(self):
        """Rule: recovery_restart_encoder calls the validated continuity cycle at
        7000 (unchanged path) and the level-preserving restart off 7000."""
        calls = []
        orig_cont = ns.NativeStreamManager.diagnostic_c3_actuator_continuity_cycle
        orig_rr = probe.run_c3_linux_recovery_restart
        try:
            ns.NativeStreamManager.diagnostic_c3_actuator_continuity_cycle = (
                lambda self: calls.append(("continuity", self._active_bitrate_kbps)) or {"video": {}})
            probe.run_c3_linux_recovery_restart = (
                lambda mgr, **k: calls.append(("level", mgr._active_bitrate_kbps)) or {"video": {}})
            for level in LEVELS:
                fake_manager(level).recovery_restart_encoder()
        finally:
            ns.NativeStreamManager.diagnostic_c3_actuator_continuity_cycle = orig_cont
            probe.run_c3_linux_recovery_restart = orig_rr
        self.assertEqual(calls, [("level", 5000), ("level", 5500), ("level", 6000), ("continuity", 7000)])

    def test_continuity_diagnostic_unchanged(self):
        """Rule: the continuity diagnostic still refuses off 7000 and still runs its
        own cycle at 7000."""
        for level in (5000, 5500, 6000):
            with self.assertRaises(ns.NativeStreamError):
                fake_manager(level).diagnostic_c3_actuator_continuity_cycle()
        seen = []
        orig = probe.run_c3_linux_actuator_continuity_cycle
        try:
            probe.run_c3_linux_actuator_continuity_cycle = lambda mgr: seen.append(mgr._active_bitrate_kbps) or {"ok": True}
            self.assertEqual(fake_manager(7000).diagnostic_c3_actuator_continuity_cycle(), {"ok": True})
        finally:
            probe.run_c3_linux_actuator_continuity_cycle = orig
        self.assertEqual(seen, [7000])

    def test_transition_and_characterization_paths_unchanged(self):
        """Rule: a ladder transition to the same level is still a no-op error, and the
        characterization path still requires the 7000 start."""
        m = fake_manager(6000)
        with self.assertRaises(RuntimeError) as cm:
            probe.run_c3_linux_validated_bitrate_transition(m, target_bitrate_kbps=6000)
        self.assertIn("noop", str(cm.exception))
        with self.assertRaises(RuntimeError) as cm:
            probe.run_c3_linux_fixed_bitrate_cycle(fake_manager(6000), 5000)
        self.assertIn("reference", str(cm.exception))

    def test_recovery_is_wired_to_the_new_primitive(self):
        """Rule: link-drop recovery's restart_encoder is recovery_restart_encoder."""
        src = (ROOT / "companion/plugins/games.py").read_text()
        i = src.index("restart_encoder=(")
        self.assertIn(".recovery_restart_encoder", src[i:i + 200])

    def test_shadow_controller_unaffected(self):
        """Rule: the shadow controller neither references nor imports the restart."""
        src = (ROOT / "companion/adaptive_bitrate.py").read_text()
        for name in ("recovery_restart", "c3_linux_actuator_probe", "native_stream"):
            self.assertNotIn(name, src)


if __name__ == "__main__":
    unittest.main()
