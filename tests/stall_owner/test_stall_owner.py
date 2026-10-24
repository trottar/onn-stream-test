#!/usr/bin/env python3
"""B12: `PRIVYHUB_INPUT_HOLD_REWIND=1` = `state` for every core; the stall's resume inside the one owner
(`PRIVYHUB_STALL_RESUME=1`). B2 / B4 / B6 / B7 / B8 / B9's tests keep their own files.

    python3 -m unittest discover -s tests/stall_owner -v

B9's loopback fake core (SAVE / LOAD_STATE_SLOT, GET_STATUS, PAUSE_TOGGLE), the real recovery, B4's real Rewinder with
B9's Cores, B7's real StallSignal (its worker driven by hand), B12's StallOwner. A fake client: stall datagrams from the
client's own 150 ms, every 50 ms.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "rewind_cores"))

import hold_rewind as hr  # noqa: E402
import rewind_cores as rc  # noqa: E402
import stall_owner as so  # noqa: E402
import stall_signal as ss  # noqa: E402
import test_rewind_cores as b9  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

PSX, SNES = b9.PSX, b9.SNES


class Down:
    """A `@down` drop: the client's last frame at t0; its stalls arrive every 50 ms from age 150."""

    def __init__(self, mode="1", core=SNES, owner=True):
        self.rig = b9.Rig(mode, core)
        self.rec = self.rig.rec
        self.restarts = 0
        self.rec._restart_encoder = self._restart
        self.rec._pause_game = self._pause
        self.rec._resume_game = self._resume
        self.sig = ss.StallSignal(self.rec, ss.parse("1")[0], threaded=False)
        self.rec._client_stall = self.sig
        self.own = so.StallOwner() if owner else None
        if owner:
            self.rec._stall_owner = self.own
        self.seq = 0
        self.t0 = time.monotonic()

    def _restart(self):
        self.restarts += 1
        self.rec.calls.append("restart")
        return {}

    def _pause(self):
        self.rec.calls.append("pause")
        self.rig.core.playing = False
        self.rig.emu._paused = True

    def _resume(self):
        self.rec.calls.append("resume")
        self.rig.core.playing = True
        self.rig.emu._paused = False

    def stall(self, age_ms, gate=False, kind=ss.KIND_STALL, real=False):
        """real: handled at the client's own time (t0 + age), as before the pause."""
        self.seq += 1
        if real:
            wait = self.t0 + age_ms / 1000.0 - time.monotonic()
            if wait > 0:
                time.sleep(wait)
        rx = time.monotonic()
        self.sig.handle((kind, gate, self.seq, 5000 + self.seq, int(age_ms)), rx)

    def until_paused(self):
        """Stalls at ages 150, 200, ... in real time until the host pauses (B9's 400)."""
        self.t0 = time.monotonic()
        age = 150
        while self.rec._state == "PLAYING" and age <= 800:
            self.stall(age, real=True)
            age += 50
        return age - 50

    def v2_eligible(self, pause_age_s):
        """The pause this old, the client present, two heartbeats with a stale and rising output: v2's restart
        conditions (D-BASE-R3a) met; one monitor tick."""
        now = time.monotonic()
        with self.rec._lock:
            self.rec._state_since = now - pause_age_s
            self.rec._client_present_since = now - pause_age_s
            self.rec._heartbeat_history = [(now - 0.5, 1500), (now - 0.01, 2500)]
        with self.rig.rw._lock:                                    # B4's pending follows its pause's key
            if self.rig.rw._pending is not None:
                self.rig.rw._pending["key"] = self.rec._state_since
        self.rec._tick()

    def events(self):
        return [(r["event"], r.get("trigger") or r.get("via")) for r in b9.rows(self.rec)]

    def stop(self):
        self.rig.stop()


class StateForEveryCore(unittest.TestCase):
    BASE = 'video_vsync = "true"\n'

    def test_one_is_state_and_rewind_is_the_allow_list(self):
        one = {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_REWIND": "1"}
        self.assertEqual(rc.mode(one), "state")
        for core in (SNES, PSX, "bsnes_libretro.so"):
            self.assertEqual(hr.apply_session_config(self.BASE, core, one), self.BASE)       # no rewind keys at all
        rw = dict(one, PRIVYHUB_INPUT_HOLD_REWIND="rewind")
        self.assertEqual(rc.mode(rw), "allow")
        self.assertEqual(hr.parse(rw), (True, None))
        self.assertEqual(hr.apply_session_config(self.BASE, SNES, rw), self.BASE + hr.config_block(SNES, rw))
        self.assertEqual(hr.apply_session_config(self.BASE, PSX, rw), self.BASE)

    def test_snes9x_saves_at_400_and_loads_at_the_release_with_the_cost_stated(self):
        rig = b9.Rig("1", SNES)
        try:
            self.assertIsNotNone(rig.det.state_mark)
            last = time.monotonic() - 0.41
            t = time.monotonic()
            rig.det.on_quiet(last + 0.41, last)
            self.assertEqual(rig.wait_saves(1), 1)
            save_rt_ms = (time.monotonic() - t) * 1000.0
            rig.pause_for_hold(last, last + 1.05)
            row = rig.rw.rewind(rig.rec, "input_release")
            self.assertEqual(b9.rows(rig.rec)[-1]["event"], "input_release")
            self.assertEqual((row["method"], row["core"]), ("state", SNES))
            self.assertTrue(20 <= row["net_unattended_frames"] <= 30, row)
            self.assertEqual(rig.core.loads, [True])
            print(f"\n[cost] fake core: SAVE_STATE_SLOT 9 request -> ack -> row {save_rt_ms:.1f} ms; "
                  f"LOAD (PAUSE_TOGGLE + LOAD_STATE_SLOT 9 + GET_STATUS) {row['rewind_ms']} ms; "
                  f"snes9x state {hr.STATE_BYTES[SNES]} B")
        finally:
            rig.stop()


class StallResume(unittest.TestCase):
    def test_down_pause_at_400_no_restart_one_resume_with_the_stall_load(self):
        d = Down()
        try:
            age = d.until_paused()
            self.assertEqual(age, 400)
            self.assertEqual(d.rec.calls, ["pause"])
            d.rig.wait_saves(1)
            saved = [r for r in b9.rows(d.rec) if r["event"] == "state_saved"]
            self.assertEqual((len(saved), saved[0]["kind"]), (1, "stall"))
            for a in range(450, 4000, 50):                         # the drop goes on; the client is present
                d.stall(a)
            for s in (2.5, 3.5, 4.5):
                d.v2_eligible(s)
            self.assertEqual(d.restarts, 0)                        # v2 held off: no restart, no escalation
            self.assertNotIn("recovery_escalation", [e[0] for e in d.events()])
            # the client's gate: its ready first (the plugin's ready action: B12, then today's note)
            self.assertTrue(d.own.ready_resume(d.rec))
            out = d.rec.note_gameplay_released()
            self.assertEqual(out, {"recovered": True, "from_state": "stall_resumed"})
            rel = [r for r in b9.rows(d.rec) if r["event"] == "input_release"]
            self.assertEqual((len(rel), rel[0]["method"], rel[0]["via"]), (1, "state", "client_ready_stall"))
            self.assertTrue(20 <= rel[0]["net_unattended_frames"] <= 30, rel[0])      # B16: the save at the 400-ms signal
            self.assertEqual(d.rig.core.loads, [True])                               # into a running core
            for i in range(6):
                d.stall(20, gate=True)                             # the gate over fresh output
            d.stall(15, kind=ss.KIND_END)
            ev = d.events()
            self.assertEqual([e for e in ev if e[0] in ("desync_pause", "resumed")],
                             [("desync_pause", "client_stall"), ("resumed", "client_ready_stall")])
            self.assertEqual(d.rec.calls, ["pause", "resume"])
            self.assertIn(("client_ready_after_stall", None), ev)
            self.assertIn(("stall_end_late", None), ev)
            self.assertEqual(len([e for e in ev if e[0] == "stall_gate_after_resume"]), 1)
        finally:
            d.stop()

    def test_stall_end_first_is_b7s_resume_with_the_load(self):
        d = Down()
        try:
            d.until_paused()
            d.stall(10, kind=ss.KIND_END)
            self.assertEqual(d.rec.calls, ["pause", "resume"])
            rel = [r for r in b9.rows(d.rec) if r["event"] == "input_release"]
            self.assertEqual((rel[0]["method"], rel[0]["via"]), ("state", "stall_end"))
        finally:
            d.stop()

    def test_the_long_stall_v2_owns_it_once(self):
        d = Down()
        try:
            d.until_paused()
            d.v2_eligible(3.0)
            self.assertEqual(d.restarts, 0)
            d.v2_eligible(5.5)                                     # the pause is now past v2's 5 s
            key = d.rec._state_since
            d.rec._tick()
            self.assertEqual(d.rec._state_since, key)
            ho = [e for e in d.events() if e[0] == "stall_handover_v2"]
            self.assertEqual(len(ho), 1)
            self.assertEqual(d.restarts, 1)                        # v2's own restart, once its backoff allows
        finally:
            d.stop()

    def test_absent_is_today_restart_and_a_second_pause(self):
        d = Down(owner=False)
        try:
            d.until_paused()
            d.v2_eligible(2.5)
            self.assertEqual(d.restarts, 1)                        # BENCH-R3 B: v2 restarts under the stall
            d.rec.note_gameplay_released()                         # the gate's plain resume (no load)
            d.stall(20, gate=True)                                 # ... and the client's gate pauses again
            ev = [e for e in d.events() if e[0] in ("desync_pause", "resumed")]
            self.assertEqual(ev, [("desync_pause", "client_stall"), ("resumed", None), ("desync_pause", "client_stall")])
        finally:
            d.stop()

    def test_a_hold_episode_is_left_to_b8(self):
        d = Down()
        try:
            class B8:
                key = None

                def ignore_stall(self, *a):
                    return False

                def note_stall(self, *a):
                    pass

                def late_stall_end(self, *a):
                    return False
            d.rec._input_hold_b8 = B8()
            d.until_paused()
            B8.key = d.rec._state_since
            self.assertFalse(d.own.ready_resume(d.rec))
            self.assertFalse(d.own.holds_v2(d.rec, time.monotonic()))
        finally:
            d.stop()


class TheFlag(unittest.TestCase):
    def test_enabled_needs_the_stall_signal(self):
        self.assertEqual(so.enabled({}), (False, None))
        self.assertEqual(so.enabled({"PRIVYHUB_STALL_RESUME": "1", "PRIVYHUB_STALL_SIGNAL": "1"}), (True, None))
        self.assertFalse(so.enabled({"PRIVYHUB_STALL_RESUME": "1"})[0])
        self.assertFalse(so.enabled({"PRIVYHUB_STALL_RESUME": "on", "PRIVYHUB_STALL_SIGNAL": "1"})[0])

    def test_not_imported_absent(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        env["PRIVYHUB_STALL_SIGNAL"] = "1"
        code = ("import sys; sys.path.insert(0, 'companion'); from games import link_drop_recovery as l; "
                "import stall_signal; print('stall_owner' in sys.modules, l.LinkDropRecovery._stall_owner)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(out.stdout.strip(), "False None", out.stderr[-400:])

    def test_hook_shapes(self):
        def ifs(rel, text):
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test).startswith(text)]
        self.assertEqual(len(ifs("stall_signal.py", "getattr(self.recovery, '_stall_owner', None) is not None")), 2)
        self.assertEqual(len(ifs("games/link_drop_recovery.py", "self._stall_owner is not None")), 1)
        self.assertEqual(len(ifs("plugins/games.py", "_stall_owner is not None")), 2)


if __name__ == "__main__":
    unittest.main()
