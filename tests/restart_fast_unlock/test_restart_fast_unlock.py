#!/usr/bin/env python3
"""B24: `PRIVYHUB_RESTART_FAST_UNLOCK=1` inside the adopted `PRIVYHUB_RESTART_FAST=1` -- the ready at the new encoder's
check, the old audio's stop after it outside the lock (the capture bounded at 300 ms, logged), the relay stopped before
the old encoder's kill (SIGKILL after a 100-ms grace). Absent = the adopted G-A5 worker.

    python3 -m unittest discover -s tests/restart_fast_unlock -v

B22's harness (`tests/restart_fast/test_restart_fast.py`, imported as a module, unedited): a real `NativeStreamManager`
on a temp root, fake encoders on a per-window registry, a fake relay and session I/O, `plugins/games.py` loaded alone.
Added here: a tracing lock (holder, acquire / release times), a frame generator (every 16 ms each live encoder's frame
is forwarded if the relay runs: a dying encoder forwards into any running relay), and a fake old audio whose capture
exits 2.0 s after SIGTERM (CL-B13 return 1's 2,088-ms stop) or whose stop stalls 2.2 s with no capture to kill.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "restart_fast"))

import test_restart_fast as h  # noqa: E402  (B22's harness, unedited; imported as a module, its tests not collected)
import restart_fast_unlock as rfu  # noqa: E402

G_UNLOCK = h.load_games_plugin({"PRIVYHUB_RESTART_FAST": "1", "PRIVYHUB_RESTART_FAST_UNLOCK": "1"})
G_UNLOCK_ALONE = h.load_games_plugin({"PRIVYHUB_RESTART_FAST_UNLOCK": "1"})


class TracingLock:
    """The manager's RLock, traced: every outermost hold (thread name, acquired, released)."""

    def __init__(self):
        self._l = threading.RLock()
        self._depth = threading.local()
        self.holds = []
        self._open = {}

    def acquire(self, *a, **k):
        got = self._l.acquire(*a, **k)
        if got:
            d = getattr(self._depth, "n", 0)
            self._depth.n = d + 1
            if d == 0:
                self._open[threading.get_ident()] = (threading.current_thread().name, h.now())
        return got

    def release(self):
        d = self._depth.n - 1
        self._depth.n = d
        if d == 0:
            name, t = self._open.pop(threading.get_ident())
            self.holds.append((name, t, h.now()))
        self._l.release()

    __enter__ = acquire

    def __exit__(self, *exc):
        self.release()


class CaptureAudio(h.FakeAudio):
    def __init__(self, events, capture):
        super().__init__(events)
        self._process = capture


class SlowAudioIO(h.FakeSessionIO):
    """The real stop's order: the sender silenced, the capture SIGTERMed and waited <= 2 s (then SIGKILL), ~88 ms of
    joins / pactl; or (no capture) a 2.2-s stall nothing can shorten."""

    def __init__(self, events, registry, capture_exit_s=2.0, stall_s=None):
        super().__init__(events, 0.0)
        self.stall_s = stall_s
        capture = None if stall_s is not None else h.FakeProc(registry, "audio", capture_exit_s, events, "old_capture")
        self.audio = CaptureAudio(events, capture)

    def stop_stream(self):
        self.events.add("old_audio_stop_begin")
        if self.stall_s is not None:
            time.sleep(self.stall_s)
        else:
            p = self.audio._process
            self.audio._process = None
            if p is not None and p.poll() is None:
                p.terminate()
                t = time.monotonic()
                while p.poll() is None and time.monotonic() - t < 2.0:
                    time.sleep(0.005)
                if p.poll() is None:
                    p.kill()
                    p.wait()
            time.sleep(0.088)
        self.events.add("old_audio_stopped")


class Frames:
    """Every 16 ms, each live encoder's frame is forwarded if the relay runs."""

    def __init__(self, m, procs):
        self.m, self.procs, self.rows = m, procs, []
        self._stop = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while not self._stop.is_set():
            for p in list(self.procs):
                if p.name.endswith("encoder") and p._exit_at is None or (p._exit_at is not None and time.monotonic() < p._exit_at):
                    if self.m._fec_relay.running:
                        self.rows.append((h.now(), p.name))
            time.sleep(0.016)

    def stop(self):
        self._stop.set()


class Unlocked(h.Patched):
    def setUp(self):
        super().setUp()
        self.procs = []
        # restart_fast_unlock's own subprocess reference too (never the global module): no real process
        patch = h.mock.patch.object(rfu, "subprocess", h.types.SimpleNamespace(
            Popen=lambda cmd, **kw: self.popen(cmd, **kw), DEVNULL=-3, STDOUT=-2))
        patch.start()
        self.patches.append(patch)

    def tearDown(self):
        for f in getattr(self, "frames", []):
            f.stop()
        super().tearDown()

    def mgr(self, old_exit_s=1.0, spawn_s=0.3, audio=None):
        m = h.manager(self.events, self.registry, self.tmp, old_exit_s=old_exit_s, spawn_s=spawn_s)
        m._lock = TracingLock()
        if audio is not None:
            m._session_io = audio
        self.procs.append(m._process)
        inner = m._popen

        def popen(cmd, **kw):
            p = inner(cmd, **kw)
            self.procs.append(p)
            return p

        m._popen = popen
        return m

    def start(self, m, G=None):
        G = G or G_UNLOCK
        p = h.plugin(G, m, self.events)
        p._restart_fast = G._restart_fast_unlock.RestartFastUnlock(p._recovery._log)
        self.plugins.append(p)
        self.popen = m._popen
        self.frames = [Frames(m, self.procs)]
        t = time.monotonic()
        out = p.handle_post_request("native-stream-start", "port=48100&guard_end=1", "127.0.0.1")
        response_s = time.monotonic() - t
        self.events.add("response")
        return p, out, response_s

    def ready(self, m):
        """The client: the old report 70 ms after the response, then the ready (its first act is status())."""
        time.sleep(0.070)
        self.events.add("old_report_received")
        st = m.status()
        self.events.add("session_started")
        return st

    def dump(self, tag, extra=""):
        """The record's timeline (only when asked: B24_TIMELINE=<dir>)."""
        d = os.environ.get("B24_TIMELINE")
        if not d:
            return
        entry = self.events.at("session_ended")
        with open(os.path.join(d, f"host_fake_timeline_{tag}.txt"), "w") as f:
            f.write(extra)
            for t, name, kw in self.events.rows:
                f.write(f"{(t - entry) * 1000:8.1f} ms  {name}  {kw if kw else ''}\n")

    def row(self, name):
        return next(r[2] for r in self.events.rows if r[1] == name)

    def wait_for(self, name, s=10.0):
        t = time.monotonic()
        while name not in self.events.names() and time.monotonic() - t < s:
            time.sleep(0.01)
        self.assertIn(name, self.events.names())


class TheSlowAudioStop(Unlocked):
    def test_a_2_s_capture_the_ready_at_the_check_the_stop_after_it(self):
        m = self.mgr(old_exit_s=0.12, audio=SlowAudioIO(self.events, self.registry, capture_exit_s=2.0))
        p, out, response_s = self.start(m)
        self.assertLess(response_s, 0.300)
        self.assertEqual(out["restart_fast"], {"armed": True, "old_stream_active": True})
        st = self.ready(m)
        self.assertTrue(st["active"])
        self.wait_for("restart_fast_audio")
        done = self.row("restart_fast_done")
        entry = self.events.at("session_ended")
        ready_ms = (self.events.at("session_started") - entry) * 1000.0
        # R1 / R3: the ready at the check's end, the lock released there
        self.assertLessEqual(done["unlocked_ms"] - done["checked_ms"], 20.0)
        self.assertLessEqual(ready_ms, done["checked_ms"] + 50.0)
        self.assertLess(ready_ms, 1_500.0)                     # the G-A5 worker would wait ~2.2 s here
        # the capture bounded at 300 ms, logged after the ready
        stop = self.row("restart_fast_audio_stop")
        self.assertTrue(stop["capture_killed_at_bound"])
        self.assertEqual(stop["capture_returncode"], 0)        # the fake's poll() code (the real one reads -9)
        self.assertLess(stop["restart_fast_audio_stop_ms"], 600.0)
        self.assertTrue(stop["joined"])
        # bounded, the stop ended inside the check's window: its row comes at the lock's release, beside the ready
        # (after the ready only when a stop outlasts the check: test_a_2_2_s_stall_nothing_shortens)
        self.assertLessEqual(stop["restart_fast_audio_stop_end_ms"], done["unlocked_ms"])
        names = self.events.names()
        for a, b in (("session_ended", "restart_fast"), ("restart_fast", "response"), ("response", "old_report_received"),
                     ("old_report_received", "restart_fast_done"), ("restart_fast_done", "session_started"),
                     ("restart_fast_done", "restart_fast_audio_stop"), ("old_audio_stopped", "new_audio_started"),
                     ("restart_fast_audio_stop", "restart_fast_audio")):
            self.assertLess(names.index(a), names.index(b), (a, b, names))
        self.assertTrue(self.row("restart_fast_audio")["started"])
        self.dump("slow_capture", f"the ready (session_started) after entry: {ready_ms:.1f} ms\n")

    def test_a_2_2_s_stall_nothing_shortens(self):
        m = self.mgr(old_exit_s=0.12, audio=SlowAudioIO(self.events, self.registry, stall_s=2.2))
        p, out, _ = self.start(m)
        self.ready(m)
        self.wait_for("restart_fast_audio", 15.0)
        done = self.row("restart_fast_done")
        entry = self.events.at("session_ended")
        self.assertLessEqual((self.events.at("session_started") - entry) * 1000.0, done["checked_ms"] + 50.0)
        stop = self.row("restart_fast_audio_stop")
        self.assertGreater(stop["restart_fast_audio_stop_ms"], 2_100.0)
        self.assertFalse(stop["capture_killed_at_bound"])
        self.assertGreater(self.events.at("restart_fast_audio_stop"), self.events.at("session_started") + 0.5)
        self.assertLess(self.events.names().index("session_started"), self.events.names().index("new_audio_started"))


class TheOldEncodersFrames(Unlocked):
    def test_a_450_ms_exit_forwards_nothing_after_the_kill(self):
        m = self.mgr(old_exit_s=0.45)
        p, out, _ = self.start(m)
        self.ready(m)
        p._restart_fast._worker.join(10)
        self.frames[0].stop()
        entry = self.events.at("session_ended")
        done = self.row("restart_fast_done")
        kill = self.events.at("old_encoder_terminated")
        old = [t for t, n in self.frames[0].rows if n == "old_encoder"]
        new = [t for t, n in self.frames[0].rows if n == "new_encoder"]
        self.assertTrue(old and new)
        # R2: the old encoder's last frame forwarded <= entry + 0.3 s (the relay stopped before its kill)
        self.assertLessEqual(max(old) - entry, 0.300)
        self.assertLess(self.events.at("relay_stop"), kill)
        self.assertEqual([t for t in old if t > kill], [])
        # R4: no second after the kill with both encoders' frames
        both = {int(t) for t in old if t > kill} & {int(t) for t in new}
        self.assertEqual(both, set())
        # the SIGKILL at the 100-ms grace, not the 450-ms exit
        self.assertLess(done["released_ms"], 250.0)
        self.assertLessEqual(done["relay_stopped_ms"], 50.0)
        self.assertEqual(self.registry.max_live, {"w1": 1})
        self.assertLess(self.events.at("old_encoder_exited"), self.events.at("new_encoder_spawned"))
        self.dump("slow_encoder_exit", f"old frames forwarded: {len(old)}, the last after entry: "
                                       f"{(max(old) - entry) * 1000:.1f} ms; new frames: {len(new)}\n")


class TheLock(Unlocked):
    def test_the_worker_holds_it_to_the_checks_end_only(self):
        m = self.mgr(old_exit_s=0.12, audio=SlowAudioIO(self.events, self.registry, capture_exit_s=2.0))
        p, out, _ = self.start(m)
        self.ready(m)
        self.wait_for("restart_fast_audio")
        done = self.row("restart_fast_done")
        entry = self.events.at("session_ended")
        worker = [x for x in m._lock.holds if x[0] == "PrivyHub-Restart-Fast"]
        main = max(worker, key=lambda x: x[2] - x[1])
        self.assertLess(main[1], self.events.at("response"))                    # held before the response
        self.assertLessEqual((main[2] - entry) * 1000.0, done["checked_ms"] + 20.0)
        # the tail's other holds: the two short session checks only
        others = [x for x in worker if x is not main]
        self.assertEqual(len(others), 2)
        self.assertTrue(all(x[2] - x[1] < 0.05 for x in others), others)


class TheTail(Unlocked):
    def test_a_stop_during_the_tail_skips_the_new_audio(self):
        m = self.mgr(old_exit_s=0.05, audio=SlowAudioIO(self.events, self.registry, stall_s=1.5))
        p, out, _ = self.start(m)
        self.ready(m)
        self.wait_for("restart_fast_done")
        with m._lock:
            m._stop_locked()                                     # a native-stream-stop while the old audio stalls
        self.wait_for("restart_fast_audio", 10.0)
        row = self.row("restart_fast_audio")
        self.assertFalse(row["started"])
        self.assertNotIn("new_audio_started", self.events.names())

    def test_a_failure_releases_the_lock(self):
        m = self.mgr(old_exit_s=0.05, spawn_s=0.0)

        def gone(managed_process_id):
            raise h.native_stream.NativeStreamError("The managed RetroArch window is gone.")

        m._select_capture_target = gone
        p, out, _ = self.start(m)
        p._restart_fast._worker.join(10)
        self.assertIn("restart_fast_failed", self.events.names())
        self.assertFalse(m.status()["active"])
        self.assertNotIn("new_encoder_spawned", self.events.names())
        self.assertEqual(self.row("restart_fast_audio")["started"], False)


class Absent(unittest.TestCase):
    def test_the_adopted_worker_without_the_flag(self):
        self.assertIsNone(h.G_FAST._restart_fast_unlock)
        self.assertIsNotNone(h.G_FAST._restart_fast)
        self.assertIsNone(G_UNLOCK_ALONE._restart_fast_unlock)   # the unlock flag alone: nothing
        self.assertIsNone(G_UNLOCK_ALONE._restart_fast)
        self.assertIs(G_UNLOCK._restart_fast_unlock.RestartFastUnlock.__mro__[1], G_UNLOCK._restart_fast.RestartFast)

    def test_nothing_imported(self):
        for extra in ({}, {"PRIVYHUB_RESTART_FAST": "1"}, {"PRIVYHUB_RESTART_FAST_UNLOCK": "1"},
                      {"PRIVYHUB_RESTART_FAST": "1", "PRIVYHUB_RESTART_FAST_UNLOCK": "0"}):
            env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
            env.update(extra)
            code = ("import sys, importlib.util; sys.path.insert(0, 'companion');"
                    "s = importlib.util.spec_from_file_location('g', 'companion/plugins/games.py');"
                    "m = importlib.util.module_from_spec(s); s.loader.exec_module(m);"
                    "print('restart_fast_unlock' in sys.modules, m._restart_fast_unlock is None)")
            out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True,
                                 text=True, timeout=300)
            self.assertEqual(out.stdout.strip().splitlines()[-1], "False True", (extra, out.stderr[-400:]))

    def test_the_flag_and_the_config(self):
        for v in ("0", "yes", "", " 2 "):
            self.assertFalse(rfu.enabled({rfu.FLAG_ENV: v}), v)
        self.assertTrue(rfu.enabled({rfu.FLAG_ENV: " 1 "}))
        self.assertEqual(rfu.RestartFastUnlock(lambda *a, **k: None).config(),
                         {"kill_grace_s": 0.1, "capture_bound_s": 0.3, "audio_join_cap_s": 10.0,
                          "startup_check_s": 0.75})

    def test_the_adopted_module_is_unchanged(self):
        import hashlib
        pred = ROOT / "docs/memory/evidence/b24_2026-10-26/predecessors/restart_fast.py"
        if not pred.is_file():
            self.skipTest("the evidence copy is not in this tree")
        self.assertEqual(hashlib.sha256((ROOT / "companion/restart_fast.py").read_bytes()).hexdigest(),
                         hashlib.sha256(pred.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
