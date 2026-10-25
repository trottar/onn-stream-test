#!/usr/bin/env python3
"""B22: `PRIVYHUB_RESTART_FAST=1` -- a guarded restart's start answered before the old teardown; the old encoder killed
first, the new one spawned only after it exited, the old audio stopped beside it, today's 0.75-s check, then the new
audio; the ready's `status()` waits on the lock. Absent / not eligible = today's start.

    python3 -m unittest discover -s tests/restart_fast -v

A real `NativeStreamManager` on a temp root (constructing nothing live): fake encoder processes on a registry per
window (terminate -> exit after a delay), a fake FEC relay, a fake session I/O (the old audio's stop 0.7 s), the capture
target and the encoder's `Popen` patched. `plugins/games.py` loaded alone (B17's `tests/guard_end` harness) with the
flag in the environment at its import. Timings are wall-clock (real threads), with margins stated per assertion.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import native_stream  # noqa: E402
import restart_fast as rf  # noqa: E402


def load_games_plugin(env):
    with mock.patch.dict(os.environ, env):
        spec = importlib.util.spec_from_file_location(f"b22_games_{len(env)}_{id(env)}",
                                                      ROOT / "companion" / "plugins" / "games.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


G_FAST = load_games_plugin({"PRIVYHUB_RESTART_FAST": "1"})
G_TODAY = load_games_plugin({})

T0 = time.monotonic()


def now():
    return time.monotonic() - T0


class Events:
    def __init__(self):
        self.rows = []
        self._lock = threading.Lock()

    def add(self, name, **kw):
        with self._lock:
            self.rows.append((now(), name, kw))

    def names(self):
        return [r[1] for r in self.rows]

    def at(self, name):
        return next(r[0] for r in self.rows if r[1] == name)


class Registry:
    """The live encoders per capture window: two at once on one window is the failure."""

    def __init__(self):
        self.live = {}
        self.max_live = {}
        self._lock = threading.Lock()

    def up(self, window):
        with self._lock:
            self.live[window] = self.live.get(window, 0) + 1
            self.max_live[window] = max(self.max_live.get(window, 0), self.live[window])

    def down(self, window):
        with self._lock:
            self.live[window] -= 1


class FakeProc:
    _n = 1000

    def __init__(self, registry, window, exit_delay_s, events, name):
        FakeProc._n += 1
        self.pid = FakeProc._n
        self.registry, self.window, self.exit_delay_s, self.events, self.name = registry, window, exit_delay_s, events, name
        self._exit_at = None
        self._done = False
        registry.up(window)

    def poll(self):
        if self._exit_at is not None and time.monotonic() >= self._exit_at and not self._done:
            self._done = True
            self.registry.down(self.window)
            self.events.add(f"{self.name}_exited")
        return 0 if self._done else None

    def terminate(self):
        self.events.add(f"{self.name}_terminated")
        self._exit_at = time.monotonic() + self.exit_delay_s

    def kill(self):
        self._exit_at = time.monotonic()

    def wait(self, timeout=None):
        while self.poll() is None:
            time.sleep(0.005)
        return 0


class FakeRelay:
    def __init__(self, events):
        self.running = True
        self.events = events

    def start(self, client_ip, client_port):
        self.running = True
        self.events.add("relay_start")

    def stop(self):
        self.running = False
        self.events.add("relay_stop")

    def status(self):
        return {"running": self.running}

    def pacing_status(self):
        return {}


class FakeAudio:
    def __init__(self, events):
        self.events = events

    def set_redundancy(self, copies, offset_packets):
        pass


class FakeSessionIO:
    def __init__(self, events, stop_s=0.7):
        self.events, self.stop_s = events, stop_s
        self.audio = FakeAudio(events)
        self.controller = types.SimpleNamespace(last_client_packet_age_ms=lambda: 0)

    def stop_stream(self):
        self.events.add("old_audio_stop_begin")
        time.sleep(self.stop_s)
        self.events.add("old_audio_stopped")

    def start(self, **kw):
        self.events.add("new_audio_started")
        return self.status()

    def status(self):
        return {"audio": {"active": True}, "controller": {"active": True}}


class Codec:
    """AUDIO_CODEC's surface: `prepare` must come after the old audio stopped."""

    active = True

    def __init__(self, events, declared=("opus",)):
        self.events, self._declared = events, declared

    def declared(self, host):
        return self._declared

    def prepare(self, streamer, client_ip):
        self.events.add("codec_prepare")
        return None


def manager(events, registry, tmp, old_exit_s=1.0, spawn_s=0.3, audio_stop_s=0.7, old=True):
    m = native_stream.NativeStreamManager(Path(tmp))
    m._session_io = FakeSessionIO(events, audio_stop_s)
    m._fec_relay = FakeRelay(events)
    m._linux_host = lambda: True
    m._find_ffmpeg = lambda: Path("/usr/bin/ffmpeg")
    m._linux_display = lambda: ":0"
    m._linux_xdotool = lambda: "/usr/bin/xdotool"
    m._linux_vaapi_device = lambda: Path("/dev/dri/renderD128")
    m._host_thermal_c = lambda: None
    m._select_capture_target = lambda managed_process_id: {"type": "window", "_window_id": "w1", "width": 1280,
                                                            "height": 720, "title": "RetroArch"}
    m._build_linux_ffmpeg_command = lambda ffmpeg, capture_target, **kw: ["ffmpeg", "-window_id",
                                                                          capture_target["_window_id"]]

    def popen(cmd, **kw):
        time.sleep(spawn_s)
        events.add("new_encoder_spawned")
        return FakeProc(registry, cmd[-1], 0.05, events, "new_encoder")

    m._popen = popen
    if old:
        m._process = FakeProc(registry, "w1", old_exit_s, events, "old_encoder")
        m._capture_target = {"type": "window", "_window_id": "w1", "width": 1280, "height": 720, "title": "RetroArch"}
        m._client_port = 48100
    return m


def plugin(G, m, events):
    class Emu:
        def status(self):
            return {"active": True, "paused": True, "pid": os.getpid()}

    p = object.__new__(G.GamesPlugin)
    p._emulator = Emu()
    p._recovery = types.SimpleNamespace(note_stream_start=lambda: events.add("note_stream_start"),
                                        session_ended=lambda: events.add("session_ended"), _stall_owner=None,
                                        _log=lambda event, **kw: events.add(event, **kw))
    p._native_stream = m
    p._diagnostic_heartbeat_interval_ms = lambda: 2000
    p._adaptive_bitrate_session_ended = lambda: events.add("ladder_session_end")
    if G._restart_fast is not None:
        p._restart_fast = G._restart_fast.RestartFast(p._recovery._log)
    return p


class Patched(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="b22_")
        self.events = Events()
        self.registry = Registry()
        self.codec = Codec(self.events)
        self.patches = [mock.patch.object(native_stream.host_resource_sampling, "start", lambda *a, **k: None),
                        mock.patch.object(native_stream.host_resource_sampling, "status", lambda *a, **k: {}),
                        mock.patch.object(native_stream, "AUDIO_CODEC", self.codec),
                        mock.patch.object(native_stream, "_audio_codec",
                                          types.SimpleNamespace(CODEC_OPUS="opus", REFUSAL="refused"), create=True),
                        # restart_fast's own subprocess reference only (never the global module): no real process
                        mock.patch.object(rf, "subprocess", types.SimpleNamespace(
                            Popen=lambda cmd, **kw: self.popen(cmd, **kw), DEVNULL=-3, STDOUT=-2)),
                        mock.patch.object(native_stream, "subprocess", types.SimpleNamespace(
                            Popen=lambda cmd, **kw: self.popen(cmd, **kw), DEVNULL=-3, STDOUT=-2,
                            TimeoutExpired=__import__("subprocess").TimeoutExpired, run=None))]
        self.popen = None
        self.plugins = []
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.plugins:
            w = getattr(getattr(p, "_restart_fast", None), "_worker", None)
            if w is not None:
                w.join(10)
        for p in self.patches:
            p.stop()

    def start_fast(self, m, query="port=48100&guard_end=1", G=None):
        p = plugin(G or G_FAST, m, self.events)
        self.plugins.append(p)
        self.popen = m._popen
        t = time.monotonic()
        out = p.handle_post_request("native-stream-start", query, "127.0.0.1")
        response_s = time.monotonic() - t
        self.events.add("response")
        return p, out, response_s


class TheFastRestart(Patched):
    def test_response_before_the_teardown_and_the_ready_waits_for_the_worker(self):
        m = manager(self.events, self.registry, self.tmp)
        p, out, response_s = self.start_fast(m)
        # the response: <= 300 ms with a 1.0-s encoder exit, a 0.7-s audio stop and a 0.3-s spawn behind it
        self.assertLess(response_s, 0.300, response_s)
        self.assertEqual(out["restart_fast"], {"armed": True, "old_stream_active": True})
        self.assertIs(out.get("guard_end"), True)
        for key in ("game_session", "paused", "stabilization_required", "heartbeat_interval_ms", "active", "audio",
                    "controller", "alpha_version", "fec_enabled", "gop_frames"):
            self.assertIn(key, out)
        self.assertTrue(out["active"])
        # the client: the old report 70 ms after the response, then the ready (its first act is status())
        time.sleep(0.070)
        self.events.add("old_report_received")
        st = m.status()
        self.events.add("session_started")
        self.assertTrue(st["active"])
        p._restart_fast._worker.join(5)
        # no two encoders on one capture (first: the clearest failure)
        self.assertEqual(self.registry.max_live, {"w1": 1})
        names = self.events.names()
        # bookkeeping first, then the response, the report, the worker's end, the ready
        for a, b in (("session_ended", "restart_fast"), ("restart_fast", "response"),
                     ("response", "old_report_received"), ("old_report_received", "restart_fast_done"),
                     ("restart_fast_done", "session_started"), ("old_encoder_terminated", "old_encoder_exited"),
                     ("old_encoder_exited", "new_encoder_spawned"), ("old_audio_stop_begin", "new_encoder_spawned"),
                     ("new_encoder_spawned", "old_audio_stopped"), ("old_audio_stopped", "codec_prepare"),
                     ("codec_prepare", "new_audio_started"), ("new_audio_started", "restart_fast_done")):
            self.assertLess(names.index(a), names.index(b), (a, b, names))
        self.assertGreaterEqual(self.events.at("session_started"), self.events.at("restart_fast_done"))
        # the ready waited for the worker: ~1.0 (exit) + 0.3 (spawn) + 0.75 (check) after the start
        self.assertGreater(self.events.at("session_started") - self.events.at("response"), 1.5)
        done = next(r[2] for r in self.events.rows if r[1] == "restart_fast_done")
        self.assertLessEqual(done["released_ms"], done["spawned_ms"])
        self.assertGreaterEqual(done["checked_ms"] - done["spawned_ms"], 700.0)   # today's 0.75-s check (+-50)
        self.assertLessEqual(done["checked_ms"], done["done_ms"])
        # the old audio overlapped the spawn: it began before, ended after
        self.assertLess(self.events.at("old_audio_stop_begin"), self.events.at("new_encoder_spawned"))
        fast = next(r[2] for r in self.events.rows if r[1] == "restart_fast")
        self.assertLess(fast["response_ms"], 300.0)
        self.assertTrue(m._running_locked())
        self.assertEqual(m._capture_target["_window_id"], "w1")
        self.assertEqual(m._client_port, 48100)
        # the record's timeline (only when asked: B22_TIMELINE=<file>)
        if os.environ.get("B22_TIMELINE"):
            t_entry = self.events.at("session_ended")
            with open(os.environ["B22_TIMELINE"], "w") as f:
                f.write(f"handler response_s {response_s:.3f}\n")
                for t, name, kw in self.events.rows:
                    f.write(f"{(t - t_entry) * 1000:8.1f} ms  {name}  {kw if kw else ''}\n")

    def test_the_check_runs_once_even_past_its_deadline(self):
        m = manager(self.events, self.registry, self.tmp, old_exit_s=0.05, audio_stop_s=1.2, spawn_s=0.0)
        p, out, _ = self.start_fast(m)
        p._restart_fast._worker.join(5)
        done = next(r[2] for r in self.events.rows if r[1] == "restart_fast_done")
        self.assertGreater(done["audio_stopped_ms"] - done["spawned_ms"], 750.0)
        self.assertIn("checked_ms", done)

    def test_a_dead_new_encoder_fails_closed(self):
        m = manager(self.events, self.registry, self.tmp, old_exit_s=0.05, spawn_s=0.0)
        inner = m._popen

        def dying(cmd, **kw):
            proc = inner(cmd, **kw)
            proc.terminate()   # exits 50 ms later, inside the check
            return proc

        m._popen = dying
        p, out, _ = self.start_fast(m)
        p._restart_fast._worker.join(5)
        self.assertIn("restart_fast_failed", self.events.names())
        self.assertNotIn("restart_fast_done", self.events.names())
        self.assertFalse(m.status()["active"])
        self.assertIsNone(m._process)

    def test_a_failure_in_the_worker_ends_the_stream_and_is_logged(self):
        m = manager(self.events, self.registry, self.tmp, old_exit_s=0.05, spawn_s=0.0)

        def gone(managed_process_id):
            raise native_stream.NativeStreamError("The managed RetroArch window is gone.")

        m._select_capture_target = gone
        p, out, _ = self.start_fast(m)
        p._restart_fast._worker.join(5)
        failed = next(r[2] for r in self.events.rows if r[1] == "restart_fast_failed")
        self.assertIn("NativeStreamError", failed["error"])
        self.assertNotIn("new_encoder_spawned", self.events.names())
        self.assertIn("old_audio_stopped", self.events.names())     # the old audio still stopped
        st = m.status()
        self.assertFalse(st["active"])

    def test_a_codec_refusal_is_refused_before_anything_changes(self):
        m = manager(self.events, self.registry, self.tmp)
        self.codec._declared = ()
        p = plugin(G_FAST, m, self.events)
        self.plugins.append(p)
        self.popen = m._popen
        with self.assertRaises(RuntimeError) as cm:
            p.handle_post_request("native-stream-start", "port=48100&guard_end=1", "127.0.0.1")
        self.assertIn("refused", str(cm.exception))
        self.assertNotIn("old_encoder_terminated", self.events.names())
        self.assertIsNone(p._restart_fast._worker)
        self.assertNotIn("codec_prepare", self.events.names())

    def test_a_status_poll_during_the_worker_waits_on_the_lock(self):
        m = manager(self.events, self.registry, self.tmp)
        p, out, _ = self.start_fast(m)
        t = time.monotonic()
        m.status()
        waited = time.monotonic() - t
        p._restart_fast._worker.join(5)
        self.assertGreater(waited, 1.0)


class NotEligibleIsToday(Patched):
    def today_start_calls(self, m, query, G):
        calls = []
        m.start = lambda **kw: calls.append(kw) or {"active": True}
        p = plugin(G, m, self.events)
        self.plugins.append(p)
        self.popen = m._popen
        out = p.handle_post_request("native-stream-start", query, "127.0.0.1")
        return calls, out

    def test_without_guard_end(self):
        m = manager(self.events, self.registry, self.tmp)
        calls, out = self.today_start_calls(m, "port=48100", G_FAST)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("restart_fast", out)
        self.assertNotIn("old_encoder_terminated", self.events.names())

    def test_without_a_running_encoder(self):
        m = manager(self.events, self.registry, self.tmp, old=False)
        calls, out = self.today_start_calls(m, "port=48100&guard_end=1", G_FAST)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("restart_fast", out)

    def test_flag_absent(self):
        self.assertIsNone(G_TODAY._restart_fast)
        m = manager(self.events, self.registry, self.tmp)
        calls, out = self.today_start_calls(m, "port=48100&guard_end=1", G_TODAY)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("restart_fast", out)
        self.assertIs(out.get("guard_end"), True)

    def test_flag_not_one(self):
        for v in ("0", "yes", "", " 2 "):
            self.assertFalse(rf.enabled({rf.FLAG_ENV: v}), v)
        self.assertTrue(rf.enabled({rf.FLAG_ENV: " 1 "}))
        self.assertIsNone(load_games_plugin({"PRIVYHUB_RESTART_FAST": "0"})._restart_fast)

    def test_not_linux(self):
        m = manager(self.events, self.registry, self.tmp)
        m._linux_host = lambda: False
        self.assertFalse(rf.RestartFast.eligible(m))


class Absent(unittest.TestCase):
    def test_nothing_imported(self):
        import subprocess
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys, importlib.util; sys.path.insert(0, 'companion');"
                "s = importlib.util.spec_from_file_location('g', 'companion/plugins/games.py');"
                "m = importlib.util.module_from_spec(s); s.loader.exec_module(m);"
                "print('restart_fast' in sys.modules, m._restart_fast is None)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=300)
        self.assertEqual(out.stdout.strip().splitlines()[-1], "False True", out.stderr[-500:])

    def test_config_row(self):
        self.assertEqual(rf.RestartFast(lambda *a, **k: None).config(), {"startup_check_s": 0.75, "lock_wait_s": 2.0})


if __name__ == "__main__":
    unittest.main()
