#!/usr/bin/env python3
"""E3-R2 -- unit tests of the three parts behind PRIVYHUB_RECOVERY_TRIGGER=v2, on synthetic timelines (not data):
the confirm (R1's v2 threshold), the silence-gap log, and the controller-pause exit. Nothing is spawned, no socket.

    python3 docs/memory/evidence/e3_r2_2026-10-08/test_e3_r2.py -v
"""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "companion"))

import native_session_io as nsio  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402


class FakeQueue:
    def __init__(self):
        self.items = []

    def put(self, x):
        self.items.append(x)


def bridge():
    b = object.__new__(nsio.NativeControllerBridge)
    b._last_any_packet_at = 0.0
    b._silence_confirm_s = 0.0
    b._silence_first_over_at = None
    b._silence_threshold_s = 1.0
    b._gap_queue = None
    b._gap_open = None
    return b


def silence_fire_time(b, last_packet, threshold_s, confirm_s, packets_between=()):
    """The receive loop's timeout branch, every 50 ms after the last packet: the first t at which it would fire."""
    b._silence_threshold_s, b._silence_confirm_s = threshold_s, confirm_s
    b._silence_first_over_at = None
    b._last_any_packet_at = last_packet
    t = last_packet
    for _ in range(400):
        t = round(t + 0.05, 3)
        for p in packets_between:
            if abs(p - t) < 1e-9:
                b._last_any_packet_at = t
        if t - b._last_any_packet_at > b._silence_threshold_s and b._silence_confirmed(t):
            return t
    return None


class Confirm(unittest.TestCase):
    def test_today_fires_on_first_check_over_1s(self):
        self.assertAlmostEqual(silence_fire_time(bridge(), 10.0, 1.0, 0.0), 11.05, places=3)

    def test_v2_needs_5s_and_a_second_check_250ms_later(self):
        self.assertAlmostEqual(silence_fire_time(bridge(), 10.0, 5.0, 0.25), 15.3, places=3)

    def test_v2_a_packet_between_restarts_the_confirm(self):
        # a packet at 15.1 (after the first over-threshold check at 15.05): the silence restarts from 15.1
        self.assertAlmostEqual(silence_fire_time(bridge(), 10.0, 5.0, 0.25, packets_between=(15.1,)), 20.35, places=3)

    def test_v2_a_3s_uplink_stall_never_fires(self):
        b = bridge()
        b._silence_threshold_s, b._silence_confirm_s, b._last_any_packet_at = 5.0, 0.25, 10.0
        fired = [t for t in [10 + i * 0.05 for i in range(1, 61)] if t - 10.0 > 5.0 and b._silence_confirmed(t)]
        self.assertEqual(fired, [])


class GapLog(unittest.TestCase):
    def feed(self, times, flush_at=None):
        b = bridge()
        b._gap_queue = FakeQueue()
        for t in times:
            b._gap_note_packet(t)
            b._last_any_packet_at = t
        if flush_at is not None and b._gap_open is not None and flush_at - b._gap_open["end"] >= b.GAP_LOG_BURST_S:
            b._gap_flush()
        return b._gap_queue.items

    def test_steady_460pps_logs_nothing(self):
        self.assertEqual(self.feed([10 + i / 460 for i in range(4600)], flush_at=30), [])

    def test_one_gap_with_its_catch_up_burst(self):
        t = [10 + i / 460 for i in range(460)]                    # 10.0 .. ~11.0
        last = t[-1]
        burst = [last + 1.2 + i * 0.0005 for i in range(300)]   # the late packets in 150 ms
        tail = [burst[-1] + (i + 1) / 460 for i in range(460)]   # normal again
        items = self.feed(t + burst + tail, flush_at=tail[-1] + 1)
        self.assertEqual(len(items), 1)
        r = items[0]
        self.assertAlmostEqual(r["gap_ms"], 1200.0, delta=0.5)
        self.assertGreaterEqual(r["burst_500ms"], 300)        # the burst and the start of the tail inside 500 ms
        self.assertFalse(r["burst_truncated"])

    def test_250ms_is_not_a_gap_but_260_is(self):
        self.assertEqual(self.feed([10.0, 10.25, 10.26], flush_at=12), [])
        items = self.feed([10.0, 10.26, 10.27], flush_at=12)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["burst_500ms"], 2)

    def test_a_second_gap_inside_the_burst_window_truncates_the_first(self):
        items = self.feed([10.0, 10.3, 10.31, 10.6, 10.61], flush_at=12)
        self.assertEqual([r["burst_truncated"] for r in items], [True, False])

    def test_off_by_default(self):
        b = bridge()
        self.assertIsNone(b._gap_queue)


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


class Exit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clock = Clock()
        self.patch = mock.patch.object(ldr.time, "monotonic", self.clock)
        self.patch.start()
        self.calls = []
        self.age = 3.0
        self.rec = ldr.LinkDropRecovery(
            Path(self.tmp.name),
            pause_game=lambda: self.calls.append("pause"),
            resume_game=lambda: self.calls.append("resume"),
            save_recovery_state=lambda: (self.calls.append("save") or {"state_file": "x"}),
            restart_encoder=lambda: (self.calls.append("restart") or {}),
            full_start_encoder=lambda: (self.calls.append("full_start") or {}),
            stream_active=lambda: True,
            end_session=lambda: self.calls.append("end"),
            client_packet_age_ms=lambda: self.age,
            recovery_save_detail=lambda: {},
        )
        self.rec._running.set()          # no monitor thread: the test drives _tick itself
        self.rec.session_started()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def log(self):
        p = self.rec.log_path()
        return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []

    def run_until(self, t_end, ages=None, heartbeats=()):
        """advance in 0.25-s ticks; ages(t) -> controller age ms; heartbeats: [(t, output_age_ms)]"""
        hb = sorted(heartbeats)
        while self.clock.t < t_end - 1e-9:
            self.clock.t = round(self.clock.t + ldr.MONITOR_INTERVAL_S, 3)
            while hb and hb[0][0] <= self.clock.t:
                self.rec.note_heartbeat({"last_output_age_ms": hb.pop(0)[1]})
            if ages:
                self.age = ages(self.clock.t)
            self.rec._tick()

    def test_controller_pause_exits_when_packets_return_and_output_is_fresh(self):
        self.rec.enable_controller_exit(True)
        self.age = 5300.0
        self.rec.note_client_silence(5300.0)                     # paused at t=1000
        self.assertEqual(self.rec.current_state(), ldr.STATE_PAUSED_RECOVERING)
        # packets back at 1001.0; heartbeats every 2 s from 1000.5 (fresh)
        self.run_until(1010, ages=lambda t: 6000.0 if t < 1001.0 else 3.0,
                       heartbeats=[(1000.5 + 2 * i, 20) for i in range(6)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PLAYING)
        res = [r for r in self.log() if r["event"] == "resumed"]
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["via"], "controller_return")
        # (a) at 1001.25 (second check); the first heartbeat after it at 1002.5 -> resumed at 1002.5
        self.assertEqual(res[0]["recovering_ms"], 2500)
        self.assertEqual(self.calls, ["pause", "resume"])

    def test_a_heartbeat_before_the_packets_return_does_not_count(self):
        self.rec.enable_controller_exit(True)
        self.rec.note_client_silence(5300.0)
        self.run_until(1004, ages=lambda t: 6000.0 if t < 1001.4 else 3.0, heartbeats=[(1001.3, 10)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PAUSED_RECOVERING)
        self.run_until(1006, ages=lambda t: 3.0, heartbeats=[(1005.3, 10)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PLAYING)

    def test_a_stale_output_age_waits_for_a_fresh_heartbeat(self):
        self.rec.enable_controller_exit(True)
        self.rec.note_client_silence(5300.0)
        self.run_until(1006, ages=lambda t: 3.0, heartbeats=[(1001.0, 1500), (1003.0, 301), (1005.0, 300)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PLAYING)
        self.assertEqual([r for r in self.log() if r["event"] == "resumed"][0]["output_age_ms"], 300)

    def test_one_good_check_is_not_two(self):
        self.rec.enable_controller_exit(True)
        self.rec.note_client_silence(5300.0)
        # the age dips under 500 on alternate checks only
        self.run_until(1010, ages=lambda t: 3.0 if int(t * 4) % 2 else 900.0,
                       heartbeats=[(1000.5 + 2 * i, 20) for i in range(5)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PAUSED_RECOVERING)

    def test_a_client_triggered_pause_keeps_its_own_exit(self):
        self.rec.enable_controller_exit(True)
        self.rec.note_client_desync("output_silence", 1100.0)
        self.run_until(1010, ages=lambda t: 3.0, heartbeats=[(1000.5 + 2 * i, 20) for i in range(5)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PAUSED_RECOVERING)
        self.assertNotIn("resume", self.calls)

    def test_flag_absent_no_exit_then_gives_up_at_120s(self):
        self.rec.note_client_silence(1003.0)
        self.run_until(1125, ages=lambda t: 3.0, heartbeats=[(1000.5 + 2 * i, 20) for i in range(62)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PAUSED_SAVED)
        self.assertEqual(self.calls, ["pause", "save"])

    def test_packets_never_return_gives_up_at_120s_with_the_flag(self):
        self.rec.enable_controller_exit(True)
        self.rec.note_client_silence(5300.0)
        self.run_until(1125, ages=lambda t: 5300.0 + (t - 1000) * 1000, heartbeats=[])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PAUSED_SAVED)
        self.assertNotIn("resume", self.calls)

    def test_a_failed_resume_stays_paused_and_retries_on_a_newer_heartbeat(self):
        self.rec.enable_controller_exit(True)
        fails = {"n": 1}

        def resume():
            if fails["n"]:
                fails["n"] -= 1
                raise RuntimeError("not confirmed")
            self.calls.append("resume")
        self.rec._resume_game = resume
        self.rec.note_client_silence(5300.0)
        self.run_until(1002, ages=lambda t: 3.0, heartbeats=[(1001.0, 10)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PAUSED_RECOVERING)
        self.assertEqual([r["event"] for r in self.log()][-1], "controller_exit_failed")
        self.run_until(1004, ages=lambda t: 3.0, heartbeats=[(1003.0, 10)])
        self.assertEqual(self.rec.current_state(), ldr.STATE_PLAYING)


def cost():
    """clause (v)'s per-packet price of the gap log on this host: ns per accepted packet, steady 460 pps"""
    b = bridge()
    b._gap_queue = FakeQueue()
    n = 200_000
    ts = [10 + i / 460 for i in range(n)]
    t0 = time.perf_counter()
    for t in ts:
        b._gap_note_packet(t)
        b._last_any_packet_at = t
    on = (time.perf_counter() - t0) / n
    b2 = bridge()
    t0 = time.perf_counter()
    for t in ts:
        if b2._gap_queue is not None:
            b2._gap_note_packet(t)
        b2._last_any_packet_at = t
    off = (time.perf_counter() - t0) / n
    return {"ns_per_packet_on": round(on * 1e9, 1), "ns_per_packet_off": round(off * 1e9, 1),
            "core_points_at_460pps": round((on - off) * 460 * 100, 5)}


if __name__ == "__main__":
    if "--cost" in sys.argv:
        print(json.dumps(cost()))
        sys.exit(0)
    unittest.main()
