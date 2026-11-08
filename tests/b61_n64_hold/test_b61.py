#!/usr/bin/env python3
"""B61 (host): the N64 Home-hold freeze -- no state save into a running N64 core (the hold's scratch skipped, the
release a plain resume, the slot-0 capture paused first) and the silent-port bound on the stall resume; PS1 and the
flag-absent paths as today. Fakes only (B9's fake core on loopback, a fake clock); temp dirs removed at exit.

    python3 -m unittest discover -s tests/b61_n64_hold -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401
sys.path.insert(0, str(ROOT / "tests" / "rewind_cores"))

import rewind_cores as rc  # noqa: E402
import stall_signal as ss  # noqa: E402
from games import emulator_manager as em  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402
from test_rewind_cores import PSX, Rig, rows  # noqa: E402

N64 = "mupen64plus_next_libretro.so"
SILENT = "EmulatorError: RetroArch network command did not respond: GET_STATUS (timed out)"


def n64_rig() -> Rig:
    rig = Rig("state", N64)
    rig.emu._n64_core = N64
    return rig


class HoldSave(unittest.TestCase):
    def test_n64_sends_no_scratch_save(self):
        rig = n64_rig()
        try:
            last = time.monotonic()
            rig.det.on_quiet(last + 0.41, last)                       # a silence: today's save point
            rig.rw.b9.save(last, last + 1.27, "stall")                # the stall's save, called directly
            end = time.monotonic() + 1.0
            while (len([r for r in rows(rig.rec) if r["event"] == "state_save_skipped"]) < 2
                   and time.monotonic() < end):
                time.sleep(0.01)
            self.assertEqual(rig.rw.b9.saves_skipped_n64, 2)
            self.assertEqual(rig.rw.b9.saves, 0)
            self.assertEqual(rig.core.log, [])                         # nothing reached the core
            skipped = [r for r in rows(rig.rec) if r["event"] == "state_save_skipped"]
            self.assertEqual(sorted((r["reason"], r["core"], r["kind"]) for r in skipped),
                             sorted([(rc.N64_SKIP, N64, "silence"), (rc.N64_SKIP, N64, "stall")]))
        finally:
            rig.stop()

    def test_ps1_saves_as_today(self):
        rig = Rig("state", PSX)
        try:
            last = time.monotonic()
            rig.det.on_quiet(last + 0.41, last)
            self.assertEqual(rig.wait_saves(1), 1)
            self.assertEqual(rig.core.log, [f"SAVE_STATE_SLOT {rc.SLOT}"])
            self.assertEqual(rig.rw.b9.saves_skipped_n64, 0)
        finally:
            rig.stop()


class HoldRelease(unittest.TestCase):
    def test_n64_release_is_a_plain_resume(self):
        rig = n64_rig()
        try:
            last = time.monotonic() - 1.2
            rig.pause_for_hold(last, last + 1.05)
            row = rig.rw.rewind(rig.rec, "stall_end")
            self.assertEqual(row["event"] if "event" in row else rows(rig.rec)[-1]["event"], "rewind_skipped")
            self.assertEqual(rows(rig.rec)[-1]["reason"], rc.N64_RELEASE)
            self.assertNotIn("slot", rows(rig.rec)[-1])
            self.assertEqual(rig.core.log, [])                          # no PAUSE_TOGGLE, no LOAD_STATE_SLOT
        finally:
            rig.stop()

    def test_ps1_release_loads_as_today(self):
        rig = Rig("state", PSX)
        try:
            last = time.monotonic() - 0.41
            rig.det.on_quiet(last + 0.41, last)
            rig.wait_saves(1)
            rig.pause_for_hold(last, last + 1.05)
            rig.rw.rewind(rig.rec, "input_release")
            self.assertEqual(rows(rig.rec)[-1]["event"], "input_release")
            self.assertEqual(rig.core.log[1:3], ["PAUSE_TOGGLE", f"LOAD_STATE_SLOT {rc.SLOT}"])
        finally:
            rig.stop()


# --- the slot-0 capture (the user's SAVE, the recovery save) ---------------------------------------------------

def capture_manager(n64_core, status="PLAYING", pauses=True):
    m = object.__new__(em.EmulatorManager)
    m._n64_core = n64_core
    m.active_game = {"system": "n64" if n64_core else "ps1", "relative_path": "x/stem.z64"}
    calls = []
    state = {"s": status}

    def net(cmd, expect_response=False, timeout=None, retries=None):
        calls.append(cmd)
        if cmd == "PAUSE_TOGGLE" and pauses:
            state["s"] = "PAUSED" if state["s"] == "PLAYING" else "PLAYING"
        return None                                                     # the save is not acknowledged (stops it)

    def status_fn():
        calls.append("GET_STATUS")
        return state["s"]

    def wait(wanted, timeout=1.5):
        calls.append(f"wait:{wanted}")
        if state["s"] != wanted:
            raise em.EmulatorError(f"RetroArch did not reach {wanted}")
        return wanted

    m._retroarch_network_request = net
    m._retroarch_network_status = status_fn
    m._wait_for_retroarch_state = wait
    m.record_save_state_probe_event = lambda event, **kw: calls.append(f"probe:{event}")
    m._active_state_stem = lambda: "stem"
    m._save_state_probe_snapshot = lambda: {}
    m._retroarch_session_log_position = lambda: 0
    m._retroarch_session_log_since = lambda offset: ""
    return m, calls


class Capture(unittest.TestCase):
    def run_capture(self, m):
        with self.assertRaises(em.EmulatorError):
            m._capture_slot0_state(probe_action="t", probe_slot=1)

    def test_n64_playing_is_paused_saved_and_resumed(self):
        m, calls = capture_manager(N64)
        self.run_capture(m)
        core = [c for c in calls if not c.startswith("probe:manager_action") and not c.startswith("probe:save_state_failure")]
        self.assertEqual(core, ["GET_STATUS", "PAUSE_TOGGLE", "wait:PAUSED", "probe:n64_paused_for_save",
                                "SAVE_STATE_SLOT 0", "PAUSE_TOGGLE", "wait:PLAYING"])

    def test_n64_already_paused_no_toggle(self):
        m, calls = capture_manager(N64, status="PAUSED")
        self.run_capture(m)
        self.assertNotIn("PAUSE_TOGGLE", calls)
        self.assertIn("SAVE_STATE_SLOT 0", calls)

    def test_n64_that_will_not_pause_is_refused_unsaved(self):
        m, calls = capture_manager(N64, pauses=False)
        with self.assertRaises(em.EmulatorError) as cm:
            m._capture_slot0_state(probe_action="t", probe_slot=1)
        self.assertIn("N64: the core did not pause for the save", str(cm.exception))
        self.assertNotIn("SAVE_STATE_SLOT 0", calls)

    def test_ps1_as_today(self):
        for core in (None,):
            m, calls = capture_manager(core)
            self.run_capture(m)
            self.assertEqual([c for c in calls if not c.startswith("probe:")], ["SAVE_STATE_SLOT 0"])
        m, calls = capture_manager(None)
        del m._n64_core                                                 # a manager built without __init__ (old tests)
        self.run_capture(m)
        self.assertEqual([c for c in calls if not c.startswith("probe:")], ["SAVE_STATE_SLOT 0"])


# --- the silent-port bound on the stall resume ------------------------------------------------------------------

class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def bound_rig(n64: bool, answer_on_try: int | None = None, rewinder: bool = True):
    root = Path(tempfile.mkdtemp(prefix="b61_rec_"))
    tries = []

    def resume_game():
        tries.append(1)
        if answer_on_try is not None and len(tries) >= answer_on_try:
            return {}
        raise em.EmulatorError(SILENT.split(": ", 1)[1])

    rec = ldr.LinkDropRecovery(
        root, pause_game=lambda: None, resume_game=resume_game, save_recovery_state=lambda: {},
        restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
        end_session=lambda: None, client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})
    rec._state = ldr.STATE_PAUSED_RECOVERING
    rec._state_since = time.monotonic()
    rec._last_desync_reason = ss.REASON
    emu = types.SimpleNamespace(_n64_core=N64 if n64 else None, process=types.SimpleNamespace(pid=os.getpid()))
    rewinds = []
    if rewinder:
        rec._input_hold_rewind = types.SimpleNamespace(emulator=emu, rewind=lambda r, via: rewinds.append(via))
    clock = Clock()
    sig = ss.StallSignal(rec, 400, clock=clock, threaded=False)
    return rec, sig, clock, tries, rewinds


def drive(sig, clock, seconds=60.0, every=1.4):
    end = clock.t + seconds
    while clock.t < end:
        sig.resume("stall_quiet", None)
        clock.t += every


def events(rec):
    p = rec.log_path()
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


class Bound(unittest.TestCase):
    def test_n64_silent_port_backs_off_after_three(self):
        rec, sig, clock, tries, rewinds = bound_rig(True)
        drive(sig, clock)
        ev = events(rec)
        names = [r["event"] for r in ev]
        self.assertEqual(names[:3], ["stall_resume_failed", "stall_resume_failed", "command_port_silent"])
        self.assertEqual(names.count("command_port_silent"), 1)
        self.assertLessEqual(len(tries), 3 + 6)                         # ~43 tries at 1.4 s without the bound
        self.assertGreaterEqual(len(tries), 3 + 5)
        silent = ev[2]
        self.assertEqual((silent["fails"], silent["backoff_s"]), (3, ss.N64_BACKOFF_S))
        self.assertIsNotNone(silent["retroarch"])
        later = [r for r in ev[3:] if r["event"] == "stall_resume_failed"]
        self.assertTrue(later and all(r["backoff_s"] == ss.N64_BACKOFF_S and r["skipped"] >= 6 for r in later))
        self.assertEqual(len(rewinds), len(tries))                      # a skipped call makes no rewind call

    def test_a_late_answer_resumes(self):
        rec, sig, clock, tries, _ = bound_rig(True, answer_on_try=5)
        drive(sig, clock, seconds=40.0)
        ev = events(rec)
        resumed = [r for r in ev if r["event"] == "resumed"]
        self.assertEqual(len(resumed), 1)
        self.assertEqual(resumed[0]["after_silent_fails"], 4)
        self.assertEqual(rec._state, ldr.STATE_PLAYING)
        self.assertIsNone(sig._silent)

    def test_ps1_every_try_and_every_failure_as_today(self):
        rec, sig, clock, tries, _ = bound_rig(False)
        drive(sig, clock)
        ev = events(rec)
        self.assertEqual(len(tries), 43)
        self.assertEqual({r["event"] for r in ev}, {"stall_resume_failed"})
        self.assertEqual(len(ev), 43)
        self.assertTrue(all("backoff_s" not in r for r in ev))

    def test_no_rewinder_is_today(self):
        rec, sig, clock, tries, _ = bound_rig(True, rewinder=False)
        drive(sig, clock)
        self.assertEqual(len(tries), 43)

    def test_a_new_process_starts_unbounded(self):
        rec, sig, clock, tries, _ = bound_rig(True)
        drive(sig, clock, seconds=6.0)
        self.assertIsNotNone(sig._silent)
        rec._input_hold_rewind.emulator.process = types.SimpleNamespace(pid=os.getpid() + 1)
        n = len(tries)
        sig.resume("stall_quiet", None)
        self.assertEqual(len(tries), n + 1)
        self.assertEqual(sig._silent["fails"], 1)


class Absent(unittest.TestCase):
    def test_a_fresh_manager_is_not_n64(self):
        m = em.EmulatorManager(Path(tempfile.mkdtemp(prefix="b61_proj_")))
        self.assertIsNone(m._n64_core)


if __name__ == "__main__":
    unittest.main()
