#!/usr/bin/env python3
"""B16: the stall resume's speed, and the saves -- inside `PRIVYHUB_STALL_RESUME=1` (+ `PRIVYHUB_INPUT_HOLD_REWIND=1`).

    python3 -m unittest discover -s tests/stall_resume_speed -v

B9's loopback fake core (SAVE / LOAD_STATE_SLOT, GET_STATUS, PAUSE_TOGGLE), the real recovery, B4's real Rewinder with
B9's Cores, B7's real StallSignal (its worker driven by hand), B6's Tuning, B8's Ownership, B12/B16's StallOwner, in
real time. A fake client: stall datagrams every 50 ms (from its own 150 ms; the gate bit from 1 s); after the return
its first frame one GOP (250 ms) later and its fast ready one 50-ms tick after that (the client side: FastReadyTest);
the ready delivered in the plugin's order (B8's, B12's, then today's note). The target rows are the design's
(`docs/memory/evidence/b16_2026-10-24/design_written_before_code.md`, hashed before this code).
"""

from __future__ import annotations

import ast
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "rewind_cores"))
sys.path.insert(0, str(ROOT / "tests" / "stall_owner"))

import hold_ownership as ho  # noqa: E402
import hold_tuning as ht  # noqa: E402
import stall_owner as so  # noqa: E402
import stall_signal as ss  # noqa: E402
import test_rewind_cores as b9  # noqa: E402
import test_stall_owner as b12  # noqa: E402

SNES = b9.SNES
GOP_S = 0.25            # GOP 15 at 60 fps: the client's first frame after the return
TICK_S = 0.05           # the client's fast-ready tick
BLACKOUT_5 = [1942, 3980]   # CL-B10 cell 3's stale heartbeat pair (the newer built before the return)


def ready(rec):
    """The plugin's ready action, in its order: B8's, B12's, then today's note."""
    if rec._input_hold_b8 is not None:
        rec._input_hold_b8.ready_resume(rec)
    if rec._stall_owner is not None:
        rec._stall_owner.ready_resume(rec)
    return rec.note_gameplay_released()


def sleep_until(t):
    wait = t - time.monotonic()
    if wait > 0:
        time.sleep(wait)


def events(rec):
    """The recovery log's events, the config rows left out."""
    return [r["event"] for r in b9.rows(rec) if not r["event"].endswith("_config")]


class DownR1(unittest.TestCase):
    def test_a_4s_down_drop_resumes_within_1s_of_the_return_no_restart_no_handover(self):
        d = b12.Down()
        try:
            onset = time.monotonic()
            d.t0 = onset
            age = 150
            while d.rec._state == "PLAYING" and age <= 800:          # the client's stalls from 150, in real time
                d.stall(age, real=True)
                age += 50
            self.assertEqual(age - 50, 400)
            self.assertEqual(events(d.rec)[:3], ["state_saved", "desync_pause", "client_stall"])   # the save, then the pause
            self.assertEqual(d.rig.rw.b9.saves, 1)
            ticks = {2.5: False, 3.5: False}
            while time.monotonic() < onset + 4.0:                    # the dark: the client still stalled, the gate up
                a = (time.monotonic() - onset) * 1000.0
                d.stall(a, gate=a >= 1000)
                paused_s = time.monotonic() - d.rec._state_since
                for at in ticks:
                    if not ticks[at] and paused_s >= at:
                        ticks[at] = True
                        with d.rec._lock:                           # v2's conditions met, blackout 5's heartbeats
                            d.rec._client_present_since = d.rec._state_since
                            now = time.monotonic()
                            d.rec._heartbeat_history = [(now - 2.0, BLACKOUT_5[0]), (now - 0.01, BLACKOUT_5[1])]
                        d.rec._tick()
                time.sleep(0.05)
            back = time.monotonic()                                  # the downlink returns
            sleep_until(back + GOP_S)
            d.stall(10, gate=True)                                   # the first frame: a fresh gate datagram
            sleep_until(back + GOP_S + TICK_S)
            out = ready(d.rec)                                       # the client's fast ready
            resumed_at = time.monotonic()
            self.assertEqual(out, {"recovered": True, "from_state": "stall_resumed"})
            self.assertLessEqual(resumed_at - back, 1.0)             # R1
            with d.rec._lock:                                        # a v2 tick after: blackout 5's stale pair again
                now = time.monotonic()
                d.rec._heartbeat_history = [(now - 2.0, BLACKOUT_5[0]), (now - 0.01, BLACKOUT_5[1])]
            d.rec._tick()
            evs = [e[0] for e in d.events()]
            self.assertNotIn("encoder_restart", evs)
            self.assertNotIn("stall_handover_v2", evs)
            self.assertEqual(d.restarts, 0)
            res = [e for e in d.events() if e[0] == "resumed"]
            self.assertEqual(res, [("resumed", "client_ready_stall")])
            rel = [r for r in b9.rows(d.rec) if r["event"] == "input_release"]
            self.assertEqual((len(rel), rel[0]["method"]), (1, "state"))
            self.assertTrue(20 <= rel[0]["net_unattended_frames"] <= 30, rel[0])
            self.assertEqual(d.rig.core.loads, [True])
            print(f"\n[R1] @down 4 s: return -> resume {int((resumed_at - back) * 1000)} ms (one GOP + one tick "
                  f"simulated, the host's ready -> resume with the load measured); net {rel[0]['net_unattended_frames']}; "
                  f"restarts 0, handovers 0")
        finally:
            d.stop()


class BothR2(unittest.TestCase):
    def test_a_4s_both_drop_resumes_within_1s_of_the_packets(self):
        rig = b9.Rig("1", SNES)
        try:
            rec = rig.rec

            def pause():
                rec.calls.append("pause")
                rig.core.playing = False
                rig.emu._paused = True

            def resume():
                rec.calls.append("resume")
                rig.core.playing = True
                rig.emu._paused = False
            rec._pause_game, rec._resume_game = pause, resume
            rec._input_hold_b6 = ht.Tuning(950)
            sig = ss.StallSignal(rec, ss.parse("1")[0], threaded=False)
            rec._client_stall = sig
            rec._input_hold_b8 = ho.Ownership()
            rec._stall_owner = so.StallOwner()
            onset = time.monotonic()                                 # the last controller packet and frame
            sleep_until(onset + 0.405)
            rig.det.on_quiet(onset + 0.405, onset)                   # B9's silence save at 400 ms (a signal >= 400)
            self.assertEqual(rig.wait_saves(1), 1)
            sleep_until(onset + 0.95)
            self.assertTrue(rec.note_input_hold(950))                # B2 / B6's hold at 950 ms
            rig.rw.set_pending(onset, time.monotonic(), rec)
            sleep_until(onset + 4.0)
            back = time.monotonic()                                  # the packets return, both ways
            sig.handle((ss.KIND_STALL, True, 1, 7000, 4000), back)   # the client's gate datagram: the handover
            rec.note_input_release(4000.0)                           # the first controller packet: B8's return
            sleep_until(back + GOP_S)
            sig.handle((ss.KIND_STALL, True, 2, 7001, 10), time.monotonic())
            sleep_until(back + GOP_S + TICK_S)
            ready(rec)                                               # the client's fast ready
            resumed_at = time.monotonic()
            self.assertLessEqual(resumed_at - back, 1.0)             # R2
            res = [(r["event"], r.get("via")) for r in b9.rows(rec) if r["event"] == "resumed"]
            self.assertEqual(res, [("resumed", "client_ready_hold")])
            rel = [r for r in b9.rows(rec) if r["event"] == "input_release"]
            self.assertEqual((len(rel), rel[0]["method"]), (1, "state"))
            self.assertTrue(20 <= rel[0]["net_unattended_frames"] <= 30, rel[0])
            self.assertEqual(rig.core.loads, [True])
            saves = [r for r in b9.rows(rec) if r["event"] == "state_saved"]
            self.assertEqual([s["kind"] for s in saves], ["silence"])
            print(f"\n[R2] @both 4 s: packets back -> resume {int((resumed_at - back) * 1000)} ms via client_ready_hold "
                  f"(today: the next fresh heartbeat, 427-2,130 ms in CL-B10 cell 2); net {rel[0]['net_unattended_frames']}")
        finally:
            rig.stop()


class SavesR3(unittest.TestCase):
    def test_no_save_under_the_400_ms_signal_and_one_at_it(self):
        d = b12.Down()
        try:
            for _episode in range(4):                                # four sub-400 client stalls (cell 2's 150-163)
                d.t0 = time.monotonic()
                for a in (150, 200, 250, 300, 350):
                    d.stall(a, real=True)
                d.stall(20, kind=ss.KIND_END)
                time.sleep(0.35)                                     # B7's quiet gap: the next is a new episode
            self.assertEqual(d.rig.rw.b9.saves, 0)
            self.assertEqual([r for r in b9.rows(d.rec) if r["event"] == "state_saved"], [])
            self.assertEqual(d.rec.calls, [])                        # no pause either
            self.assertEqual(d.until_paused(), 400)                  # a real stall: one save, then the pause
            self.assertEqual(d.rig.rw.b9.saves, 1)
            self.assertEqual(d.rig.rw.b9.saves_skipped_paused, 0)
            self.assertEqual(events(d.rec)[:2], ["state_saved", "desync_pause"])
        finally:
            d.stop()


class V2Rule(unittest.TestCase):
    def _paused(self):
        d = b12.Down()
        d.until_paused()
        return d

    def test_v2_takes_a_long_stall_only_while_the_newest_datagram_says_stalled(self):
        d = self._paused()
        try:
            d.stall(5200)                                            # the client still dark, just now
            d.v2_eligible(5.5)
            self.assertEqual([e[0] for e in d.events()].count("stall_handover_v2"), 1)
            self.assertEqual(d.restarts, 1)
        finally:
            d.stop()

    def test_no_v2_when_the_newest_datagram_is_fresh_or_old(self):
        d = self._paused()
        try:
            d.stall(12, gate=True)                                   # the client has frames: its ready follows
            d.v2_eligible(5.5)
            d.stall(5400)
            time.sleep(0.35)                                         # the newest datagram older than 300 ms
            d.v2_eligible(5.8)
            self.assertNotIn("stall_handover_v2", [e[0] for e in d.events()])
            self.assertEqual(d.restarts, 0)
        finally:
            d.stop()


class TheHint(unittest.TestCase):
    def test_the_start_response_key_only_with_the_owner(self):
        self.assertEqual(so.StallOwner.client_hint(), {"fast_ready": True})
        tree = ast.parse((ROOT / "companion" / "plugins" / "games.py").read_text())
        hooks = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                 and ast.unparse(n.test) == "getattr(self._recovery, '_stall_owner', None) is not None"]
        self.assertEqual(len(hooks), 1)
        self.assertEqual(ast.unparse(hooks[0].body[0]),
                         "payload['stall_resume'] = self._recovery._stall_owner.client_hint()")
        from games import link_drop_recovery as ldr
        self.assertIsNone(ldr.LinkDropRecovery._stall_owner)          # without the flag: no key

    def test_the_config_row_names_b16(self):
        rec = b9.recovery()
        rec._client_stall = object()
        o = so.wire(rec, None, {"PRIVYHUB_STALL_RESUME": "1", "PRIVYHUB_STALL_SIGNAL": "1"})
        self.assertIsNotNone(o)
        row = b9.rows(rec)[-1]
        self.assertEqual((row["event"], row["fast_ready"], row["save_from_signal"], row["v2_newest_s"]),
                         ("stall_resume_config", True, True, so.NEWEST_S))


if __name__ == "__main__":
    unittest.main()
