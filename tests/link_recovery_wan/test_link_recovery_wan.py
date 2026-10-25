#!/usr/bin/env python3
"""B23: `PRIVYHUB_LINK_RECOVERY_WAN=1` -- the hold's H and the stall's threshold per path class (WAN-R1): lan as wired
(950 / 400), remote-direct 450 / 200, remote-relayed / -unknown as wired; `link_recovery_config` per set applied.

    python3 -m unittest discover -s tests/link_recovery_wan -v

The fake path class: the address test and the overlay's path injected. The real B2 detector (with B6's `Tuning` as its
wire attaches it) and the real B7 `StallSignal` (unthreaded) with a fake recovery. The replay: G4-S4's control-gap log
(its 3 rows inline; no address in them) through the real detector at H 950 and 450 (LAN-R1's form: the real code in
process, fed from the recorded rows); the evidence script `b23_2026-10-24/replay_holds.py` runs every log WAN-R1 read.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import types
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import hold_tuning  # noqa: E402
import input_hold  # noqa: E402
import link_recovery_wan as wan  # noqa: E402
import stall_signal  # noqa: E402

# G4-S4's control-gap log (docs/memory/evidence/g4_s4_2026-10-24/copies/logs/games/native_stream_ctrl_gaps.log)
G4_S4_GAPS = [
    {"start_utc": "2026-10-24T19:25:22.875Z", "end_utc": "2026-10-24T19:25:30.782Z", "gap_ms": 7907.1},
    {"start_utc": "2026-10-24T21:02:36.267Z", "end_utc": "2026-10-24T21:02:46.079Z", "gap_ms": 9811.4},
    {"start_utc": "2026-10-24T21:04:33.935Z", "end_utc": "2026-10-24T21:04:46.452Z", "gap_ms": 12516.8},
]
REAL_DROP_MS = 3000.0       # WAN-R1's rule (G4-S4's): a gap >= 3 s is a real drop


class Recovery:
    def __init__(self):
        self.rows = []
        self._lock = threading.Lock()
        self._state, self._last_desync_reason, self._state_since = "PLAYING", None, 0.0
        self.entered = []

    def _log(self, event, **kw):
        self.rows.append({"event": event, **kw})

    def _enter_recovery(self, trigger, age_ms):
        self.entered.append((trigger, age_ms))
        self._state, self._last_desync_reason = "PAUSED_RECOVERING", trigger


def stack(hold=True, stall=True, b6=True):
    """The objects as B2 / B6 / B7's wires leave them: H 950 (B6's `1`), the stall 400 (B9's `1`)."""
    rec = Recovery()
    emitted = []
    det = None
    if hold:
        det = input_hold.InputHoldDetector(250, emitted.append)      # B2's own default ...
        if b6:
            det.hold_s = hold_tuning.H_DEFAULT_MS / 1000.0             # ... then B6's wire: 950
            det.tuning = hold_tuning.Tuning(hold_tuning.H_DEFAULT_MS)
    st = None
    if stall:
        st = stall_signal.StallSignal(rec, stall_signal.DEFAULT_MS, threaded=False)
        rec._client_stall = st
    controller = types.SimpleNamespace(_input_hold=det)
    return rec, controller, det, st, emitted


def wan_for(rec, det, st, overlay, path, config_row=None):
    return wan.WanThresholds(rec, det, st, is_overlay=lambda ip: overlay, overlay_path=lambda: path,
                             config_row=config_row, threaded=False)


class TheSets(unittest.TestCase):
    def test_lan_is_as_wired(self):
        rec, _c, det, st, _e = stack()
        w = wan_for(rec, det, st, overlay=False, path="direct")
        self.assertEqual(w.note_stream_start("lan-client"), wan.SET_LAN)
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms, det.tuning.hold_ms), (950, 400, 950))
        row = rec.rows[-1]
        self.assertEqual(row["event"], "link_recovery_config")
        self.assertEqual(row["wan"]["set"], "lan")
        self.assertEqual((row["wan"]["hold_ms"], row["wan"]["stall_ms"]), (950, 400))

    def test_remote_direct_takes_wan_r1s_values(self):
        rec, _c, det, st, _e = stack()
        w = wan_for(rec, det, st, overlay=True, path="direct")
        w.note_stream_start("overlay-client")
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms, det.tuning.hold_ms), (450, 200, 450))
        sets = [r["wan"]["set"] for r in rec.rows if r["event"] == "link_recovery_config"]
        self.assertEqual(sets, ["remote-unknown", "remote-direct"])        # pending, then the overlay's answer
        last = rec.rows[-1]["wan"]
        self.assertEqual((last["path_class"], last["path"], last["hold_ms"], last["stall_ms"]),
                         ("remote", "direct", 450, 200))
        self.assertIn("WAN-R1 direct", last["why"])

    def test_remote_relayed_and_unknown_are_as_wired(self):
        for path, want in (("relayed", "remote-relayed"), ("no-peer", "remote-unknown"), ("none", "remote-unknown"),
                           ("unread", "remote-unknown")):
            rec, _c, det, st, _e = stack()
            w = wan_for(rec, det, st, overlay=True, path=path)
            w.note_stream_start("overlay-client")
            self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (950, 400), path)
            self.assertEqual(rec.rows[-1]["wan"]["set"], want, path)
        rec, _c, det, st, _e = stack()

        def boom():
            raise RuntimeError("tailscale not running")

        w = wan.WanThresholds(rec, det, st, is_overlay=lambda ip: True, overlay_path=boom, threaded=False)
        w.note_stream_start("overlay-client")
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (950, 400))
        self.assertEqual((rec.rows[-1]["wan"]["set"], rec.rows[-1]["wan"]["path"]), ("remote-unknown", "unread"))

    def test_sessions_in_turn_restore_the_lan(self):
        rec, _c, det, st, _e = stack()
        overlay = {"v": False}
        w = wan.WanThresholds(rec, det, st, is_overlay=lambda ip: overlay["v"], overlay_path=lambda: "direct",
                              threaded=False)
        seen = []
        for v in (False, True, False, True):
            overlay["v"] = v
            w.note_stream_start("client")
            seen.append((round(det.hold_s * 1000), st.threshold_ms))
        self.assertEqual(seen, [(950, 400), (450, 200), (950, 400), (450, 200)])

    def test_a_late_overlay_answer_for_an_older_session_is_ignored(self):
        rec, _c, det, st, _e = stack()
        gate = threading.Event()
        answered = threading.Event()

        def slow_path():
            gate.wait(5)
            return "direct"

        overlay = {"v": True}
        w = wan.WanThresholds(rec, det, st, is_overlay=lambda ip: overlay["v"], overlay_path=slow_path, threaded=True)
        w.note_stream_start("overlay-client")                   # session 1: remote, its path read pending
        overlay["v"] = False
        w.note_stream_start("lan-client")                       # session 2: lan
        orig = w._apply

        def spy(*a):
            orig(*a)
            answered.set()

        w._apply = spy
        gate.set()
        answered.wait(5)
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (950, 400))
        self.assertEqual(w.in_force["set"], "lan")

    def test_only_what_is_wired_is_set(self):
        rec, _c, det, st, _e = stack(hold=False)
        w = wan_for(rec, det, st, overlay=True, path="direct")
        w.note_stream_start("c")
        self.assertEqual(st.threshold_ms, 200)
        self.assertIsNone(rec.rows[-1]["wan"]["hold_ms"])
        rec, c, det, st, _e = stack(hold=False, stall=False)
        self.assertIsNone(wan.wire(rec, c, {wan.FLAG_ENV: "1"}))
        self.assertEqual(rec.rows[-1]["event"], "link_recovery_wan_config")
        self.assertTrue(rec.rows[-1]["ignored"])

    def test_the_rows_with_the_umbrella(self):
        rec, c, det, st, _e = stack()
        umbrella = {"umbrella": True, "implied": ["PRIVYHUB_INPUT_HOLD"], "explicit": {}, "at": "import", "reapply": []}
        w = wan.wire(rec, c, {wan.FLAG_ENV: "1"}, config_row=lambda: dict(umbrella))
        cfg = rec.rows[-1]
        self.assertEqual(cfg["event"], "link_recovery_wan_config")
        self.assertEqual((cfg["lan_hold_ms"], cfg["lan_stall_ms"]), (950, 400))
        self.assertEqual(cfg["sets"]["remote-direct"]["hold_ms"], 450)
        self.assertEqual(cfg["sets"]["remote-direct"]["stall_ms"], 200)
        w._is_overlay = lambda ip: False
        w.note_stream_start("c")
        row = rec.rows[-1]
        self.assertEqual(row["event"], "link_recovery_config")
        self.assertEqual(row["at"], "session")                   # B21's `import` overwritten by the session's
        self.assertEqual((row["umbrella"], row["implied"], row["reapply"]), (True, ["PRIVYHUB_INPUT_HOLD"], []))
        self.assertEqual(row["wan"]["set"], "lan")

    def test_the_default_path_class_readers(self):
        self.assertFalse(wan._default_is_overlay("not-an-address"))
        env = {k: v for k, v in os.environ.items() if k != "PRIVYHUB_OVERLAY_PROVIDER"}
        code = ("import sys; sys.path.insert(0, 'companion'); import link_recovery_wan as w; "
                "print(w._default_overlay_path())")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(out.stdout.strip(), "unread", out.stderr[-300:])   # no provider: unread, nothing spawned


class TheThresholdsAct(unittest.TestCase):
    def test_a_250_ms_stall_pauses_on_direct_not_on_the_lan(self):
        for overlay, want in ((False, []), (True, [("client_stall", 250.0)])):
            rec, _c, det, st, _e = stack()
            wan_for(rec, det, st, overlay=overlay, path="direct").note_stream_start("c")
            st.handle((stall_signal.KIND_STALL, False, 1, 100, 250), 10.0)
            self.assertEqual(rec.entered, want, overlay)

    def test_a_600_ms_silence_holds_on_direct_not_on_the_lan(self):
        for overlay, want in ((False, 0), (True, 1)):
            rec, _c, det, st, emitted = stack()
            wan_for(rec, det, st, overlay=overlay, path="direct").note_stream_start("c")
            det.on_packet(100.0)
            for i in range(1, 61):                              # 600 ms of quiet checks, 10 ms apart
                det.on_quiet(100.0 + i / 100.0, 100.0)
            self.assertEqual(sum(1 for e in emitted if e[0] == "hold"), want, overlay)


def _t(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()


def replay(gaps, hold_ms):
    """The silences through the real B2 detector (B6's tuning attached), 10-ms quiet checks; (real, false) holds."""
    emitted = []
    det = input_hold.InputHoldDetector(250, emitted.append)
    det.hold_s = hold_ms / 1000.0
    det.tuning = hold_tuning.Tuning(hold_ms)
    real = false = 0
    for g in gaps:
        start, end = _t(g["start_utc"]), _t(g["end_utc"])
        det.on_packet(start)
        before = sum(1 for e in emitted if e[0] == "hold")
        t = start
        while t < end:
            t += 0.010
            det.on_quiet(min(t, end), start)
        det.on_packet(end)
        if sum(1 for e in emitted if e[0] == "hold") > before:
            if float(g["gap_ms"]) >= REAL_DROP_MS:
                real += 1
            else:
                false += 1
    return real, false


class TheReplay(unittest.TestCase):
    def test_g4_s4_at_the_old_and_the_new_h(self):
        self.assertEqual(replay(G4_S4_GAPS, 950), (3, 0))
        self.assertEqual(replay(G4_S4_GAPS, 450), (3, 0))

    def test_the_inline_rows_are_the_logs(self):
        log = ROOT / "docs/memory/evidence/g4_s4_2026-10-24/copies/logs/games/native_stream_ctrl_gaps.log"
        if not log.is_file():
            self.skipTest("the evidence copy is not in this tree (the /tmp copy holds companion/ tools/ tests/ only)")
        rows = [json.loads(x) for x in log.read_text().splitlines() if x.strip()]
        self.assertEqual([{k: r[k] for k in ("start_utc", "end_utc", "gap_ms")} for r in rows], G4_S4_GAPS)

    def test_a_lan_silence_between_the_two_hs(self):
        lan = [{"start_utc": "2026-10-24T15:20:00.000Z", "end_utc": "2026-10-24T15:20:00.564Z", "gap_ms": 564.0}]
        self.assertEqual(replay(lan, 950), (0, 0))
        self.assertEqual(replay(lan, 450), (0, 1))              # why the LAN keeps 950 (CL-B11 cell 1's 564 ms)


class Addendum1(unittest.TestCase):
    """The path re-read during a remote session, and the guard on remote-direct (design_addendum_1.md)."""

    def test_the_reread_follows_the_path(self):
        rec, _c, det, st, _e = stack()
        path = {"v": "direct"}
        w = wan.WanThresholds(rec, det, st, is_overlay=lambda ip: True, overlay_path=lambda: path["v"], threaded=False)
        w.note_stream_start("overlay-client")
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (450, 200))
        n = len(rec.rows)
        w.reread_once(w._session)                               # nothing new: no row
        self.assertEqual(len(rec.rows), n)
        path["v"] = "no-peer"                                   # the hotspot toggle
        w.reread_once(w._session)
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (950, 400))
        self.assertEqual(rec.rows[-1]["wan"]["set"], "remote-unknown")
        path["v"] = "direct"
        w.reread_once(w._session)
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (450, 200))

    def test_the_reread_loop_stops_with_its_session(self):
        rec, _c, det, st, _e = stack()
        overlay = {"v": True}
        sleeps = []
        w = wan.WanThresholds(rec, det, st, is_overlay=lambda ip: overlay["v"], overlay_path=lambda: "direct",
                              threaded=True)
        done = threading.Event()

        def sleep(s):
            sleeps.append(s)
            if len(sleeps) == 2:
                overlay["v"] = False
                w.note_stream_start("lan-client")               # a new session: the old loop must end
            if len(sleeps) > 5:
                done.set()
                raise SystemExit
        w._sleep = sleep
        w._threaded = False
        w.note_stream_start("overlay-client")                   # session 1 applied synchronously
        w._threaded = True
        w._read_path(1)                                         # the loop, run here
        self.assertEqual(sleeps, [10.0, 10.0])
        self.assertEqual(w.in_force["set"], "lan")

    def test_a_non_drop_hold_on_direct_reverts_the_session(self):
        rec, _c, det, st, emitted = stack()
        w = wan_for(rec, det, st, overlay=True, path="direct")
        w.note_stream_start("overlay-client")
        det.on_packet(100.0)
        for i in range(1, 61):                                   # a 600-ms silence: a hold at 450 ...
            det.on_quiet(100.0 + i / 100.0, 100.0)
        det.on_packet(100.6)                                     # ... released at 600 ms: not a drop
        self.assertEqual([e[0] for e in emitted], ["hold", "release"])   # the original emit, unchanged
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (950, 400))
        self.assertEqual(w.guard_trips, 1)
        last = rec.rows[-1]["wan"]
        self.assertEqual((last["set"], last["why"]), ("remote-unknown", wan.WHY_GUARD))
        w.reread_once(w._session)                                # the re-read does not bring 450 back
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (950, 400))
        w.note_stream_start("overlay-client")                    # a new session: direct again
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (450, 200))

    def test_a_real_drop_does_not_trip_the_guard(self):
        rec, _c, det, st, emitted = stack()
        w = wan_for(rec, det, st, overlay=True, path="direct")
        w.note_stream_start("overlay-client")
        det.on_packet(100.0)
        for i in range(1, 501):                                  # a 5-s drop
            det.on_quiet(100.0 + i / 100.0, 100.0)
        det.on_packet(105.0)
        self.assertEqual(w.guard_trips, 0)
        self.assertEqual((round(det.hold_s * 1000), st.threshold_ms), (450, 200))

    def test_the_guard_only_on_direct(self):
        rec, _c, det, st, emitted = stack()
        w = wan_for(rec, det, st, overlay=False, path="direct")
        w.note_stream_start("lan-client")
        det.on_packet(100.0)
        for i in range(1, 121):                                  # a 1.2-s silence on the LAN: a hold at 950
            det.on_quiet(100.0 + i / 100.0, 100.0)
        det.on_packet(101.2)
        self.assertEqual(w.guard_trips, 0)
        self.assertEqual(w.in_force["set"], "lan")


def replay_guarded(gaps):
    """H 450 from the session's start; the first non-drop hold reverts to 950 for the rest (addendum 1)."""
    emitted = []
    det = input_hold.InputHoldDetector(250, emitted.append)
    det.hold_s, det.tuning = 0.450, hold_tuning.Tuning(450)
    real = false = 0
    for g in gaps:
        start, end = _t(g["start_utc"]), _t(g["end_utc"])
        det.on_packet(start)
        before = sum(1 for e in emitted if e[0] == "hold")
        t = start
        while t < end:
            t += 0.010
            det.on_quiet(min(t, end), start)
        det.on_packet(end)
        if sum(1 for e in emitted if e[0] == "hold") > before:
            if float(g["gap_ms"]) >= REAL_DROP_MS:
                real += 1
            else:
                false += 1
                det.hold_s, det.tuning.hold_ms = 0.950, 950
    return real, false


class TheGuardedReplay(unittest.TestCase):
    def test_g4_s4_guarded(self):
        self.assertEqual(replay_guarded(G4_S4_GAPS), (3, 0))

    def test_g4_s1_run_2_the_toggle(self):
        log = ROOT / "docs/memory/evidence/wan_r1_2026-10-24/copies/s1r2/native_stream_ctrl_gaps.log"
        if not log.is_file():
            self.skipTest("the evidence copy is not in this tree")
        gaps = [json.loads(x) for x in log.read_text().splitlines() if x.strip()]
        self.assertEqual(replay(gaps, 950), (0, 1))
        self.assertEqual(replay(gaps, 450), (0, 18))
        self.assertEqual(replay_guarded(gaps), (0, 2))          # the trip, then 950's one


class Absent(unittest.TestCase):
    def test_nothing_imported(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys, importlib.util; sys.path.insert(0, 'companion');"
                "s = importlib.util.spec_from_file_location('g', 'companion/plugins/games.py');"
                "m = importlib.util.module_from_spec(s); s.loader.exec_module(m);"
                "print('link_recovery_wan' in sys.modules, m._link_recovery_wan is None)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=300)
        self.assertEqual(out.stdout.strip().splitlines()[-1], "False True", out.stderr[-500:])

    def test_the_flag_reads_exactly_one(self):
        for v in ("0", "yes", "", " 2 "):
            self.assertFalse(wan.enabled({wan.FLAG_ENV: v}), v)
        self.assertTrue(wan.enabled({wan.FLAG_ENV: " 1 "}))
        self.assertFalse(wan.enabled({}))


if __name__ == "__main__":
    unittest.main()
