#!/usr/bin/env python3
"""B8: the hold / stall ownership at the link's return. B2 / B4 / B6 / B7's tests are untouched.

    python3 -m unittest discover -s tests/input_hold_b8 -v

The real LinkDropRecovery (fake pause / resume), B2's real dispatcher, B4's real Rewinder (a fake NCI: every REWIND
counted, GET_STATUS PLAYING), B6's real tuning, B7's real StallSignal (its worker driven by hand), B8's Ownership --
all on one fake clock based on time.monotonic(), so the frame counts are exact.
"""

from __future__ import annotations

import ast
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import hold_ownership as ho  # noqa: E402
import hold_rewind as hr  # noqa: E402
import hold_tuning as ht  # noqa: E402
import input_hold as ih  # noqa: E402
import stall_signal as ss  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

ON = {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_B6": "1", "PRIVYHUB_STALL_SIGNAL": "1",
      "PRIVYHUB_INPUT_HOLD_B8": "1"}


class Clock:
    def __init__(self):
        self.t = time.monotonic()

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += max(0.0, s)


class FakeNci:
    def __init__(self, log):
        self.log = log

    def send(self, cmd):
        self.log.append(cmd)

    def status(self, timeout):
        return "GET_STATUS PLAYING snes9x,game"

    def close(self):
        pass


class FakeEmu:
    _network_cmd_port = 1
    lock = None


class FakeCtrl:
    def _neutralize(self):
        pass


class Rig:
    def __init__(self, b8=True, b6=True):
        self.clock = Clock()
        self.calls = []
        self.nci = []
        self.root = Path(tempfile.mkdtemp(prefix="b8_rec_"))
        self.rec = ldr.LinkDropRecovery(
            self.root, pause_game=lambda: self.calls.append("pause"), resume_game=lambda: self.calls.append("resume"),
            save_recovery_state=lambda: {}, restart_encoder=lambda: {}, full_start_encoder=lambda: {},
            stream_active=lambda: True, end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
            recovery_save_detail=lambda: {})
        self.rec._state = ldr.STATE_PLAYING
        self.rec._state_since = time.monotonic()
        self.rw = hr.Rewinder(FakeEmu(), FakeCtrl(), 72, clock=self.clock, sleep=self.clock.sleep,
                              nci_factory=lambda port: FakeNci(self.nci))
        self.rec._input_hold_rewind = self.rw
        self.t = ht.Tuning(950, clock=self.clock) if b6 else None
        if b6:
            self.rec._input_hold_b6 = self.t
        self.sig = ss.StallSignal(self.rec, 150, clock=self.clock, sleep=self.clock.sleep, threaded=False)
        self.rec._client_stall = self.sig
        self.own = ho.Ownership(clock=self.clock) if b8 else None
        if b8:
            self.rec._input_hold_b8 = self.own
        self.disp = ih.HoldDispatcher(self.rec, lambda: False, clock=self.clock, sleep=self.clock.sleep,
                                      threaded=False)
        self.seq = 0

    # --- the fake client and link ----------------------------------------------------------------------------------

    def at(self, dt):
        self.clock.t = self.t0 + dt

    def hold(self, onset_dt=0.0, detect_ms=955.0, pause_ms=95.0):
        """The uplink goes silent at onset; the detector fires detect_ms later; the pause is confirmed pause_ms on."""
        self.t0 = self.clock.t - onset_dt
        self.at(onset_dt + detect_ms / 1000.0)
        self.disp.put(("hold", detect_ms))
        self.at(onset_dt + (detect_ms + pause_ms) / 1000.0)
        self.disp.handle(("hold", detect_ms))

    def stall(self, dt, age, gate=False, kind=ss.KIND_STALL):
        self.at(dt)
        self.seq += 1
        self.sig.handle((kind, gate, self.seq, 5000 + self.seq, int(age)), self.clock())

    def packet_back(self, dt):
        self.at(dt)
        self.disp.handle(("release", dt * 1000.0))

    def heartbeat(self, dt, age):
        self.at(dt)
        with self.rec._lock:
            self.rec._heartbeat_history.append((self.clock(), int(age)))
            del self.rec._heartbeat_history[:-2]

    def tick(self, dt):
        self.at(dt)
        self.rec._tick()

    def rows(self):
        p = self.rec.log_path()
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def events(self):
        return [(r["event"], r.get("trigger") or r.get("via")) for r in self.rows()]

    def row(self, event, via=None):
        return [r for r in self.rows() if r["event"] == event and (via is None or r.get("via") == via)]


def both(rig, stall_lead_ms=70.0, blackout_s=4.0):
    """@both: the client's last frame stall_lead_ms before the uplink silence; at the return the first stall carries
    the output's age (the blackout + the lead), then the first controller packet."""
    rig.hold()
    ret = blackout_s
    rig.stall(ret, blackout_s * 1000.0 + stall_lead_ms)          # the handover (B7 takes the hold over)
    rig.packet_back(ret + 0.002)                                  # the return
    rig.stall(ret + 0.05, blackout_s * 1000.0 + stall_lead_ms + 50, gate=True)
    return ret


class TheFlag(unittest.TestCase):
    def test_enabled(self):
        self.assertEqual(ho.enabled({}), (False, None))
        self.assertEqual(ho.enabled(ON), (True, None))
        for drop in ("PRIVYHUB_INPUT_HOLD", "PRIVYHUB_INPUT_HOLD_B6", "PRIVYHUB_STALL_SIGNAL"):
            env = {k: v for k, v in ON.items() if k != drop}
            on, why = ho.enabled(env)
            self.assertFalse(on)
            self.assertTrue(why.startswith("ignored"), why)
        self.assertEqual(ho.enabled(dict(ON, PRIVYHUB_INPUT_HOLD_B8="yes"))[0], False)

    def test_wire_needs_b6_and_b7_wired(self):
        rig = Rig(b8=False)
        rig.rw.cap = 62
        self.assertIsNotNone(ho.wire(rig.rec, None, ON))
        self.assertEqual(rig.rw.cap, 72)                          # B6's 62 + 10
        self.assertEqual(rig.row("input_hold_b8_config")[0]["rewind_cap"], 72)
        rig2 = Rig(b8=False, b6=False)
        self.assertIsNone(ho.wire(rig2.rec, None, ON))
        self.assertTrue(rig2.row("input_hold_b8_config")[0]["ignored"])

    def test_cap_and_buffer(self):
        self.assertEqual(ho.rewind_cap(ON, 62), 72)
        self.assertEqual(ho.rewind_cap(dict(ON, PRIVYHUB_INPUT_HOLD_REWIND_CAP="40"), 40), 40)
        self.assertEqual(ho.rewind_cap({k: v for k, v in ON.items() if k != "PRIVYHUB_INPUT_HOLD_B8"}, 62), 62)
        env = dict(ON, PRIVYHUB_INPUT_HOLD_REWIND="1")
        block = hr.config_block("snes9x_libretro.so", env)
        mib = 1024 * 1024
        self.assertIn(f'rewind_buffer_size = "{math.ceil(823_536 * 74 / mib) * mib}"', block)   # 59 MiB
        env.pop("PRIVYHUB_INPUT_HOLD_B8")
        self.assertIn(f'rewind_buffer_size = "{math.ceil(823_536 * 64 / mib) * mib}"', hr.config_block(
            "snes9x_libretro.so", env))                                                         # B6's, unchanged


class AtBoth(unittest.TestCase):
    def test_one_resume_at_the_first_fresh_heartbeat_and_one_rewind_of_pre_hold_plus_stall(self):
        rig = Rig()
        ret = both(rig)
        self.assertEqual(rig.calls, ["pause"])
        rig.heartbeat(ret - 1.0, 4000)                            # before the return: not this
        rig.tick(ret + 0.10)
        rig.heartbeat(ret + 0.3, 1800)                            # after, but the output still stale: not yet
        rig.tick(ret + 0.35)
        self.assertEqual(rig.calls, ["pause"])
        rig.heartbeat(ret + 1.3, 40)                              # the first fresh report after the return
        rig.tick(ret + 1.35)
        self.assertEqual(rig.calls, ["pause", "resume"])
        ev = rig.events()
        self.assertEqual(ev[:3], [("desync_pause", "input_hold"), ("input_hold_handover", "client_stall"),
                                  ("input_hold_carry", None)])
        self.assertEqual([e for e in ev if e[0] in ("resumed", "desync_pause")],
                         [("desync_pause", "input_hold"), ("resumed", "hold_return_stall")])
        rw = rig.row("input_release", "hold_return_stall")
        self.assertEqual(len(rw), 1)
        # pre-hold: onset -> the confirmed pause 1,050 ms = 63 frames, less B4's 4 = 59; the stall's own: 70 ms = 4
        self.assertEqual((rw[0]["pre_hold_frames"], rw[0]["stall_frames"]), (59, 4))
        self.assertEqual(rw[0]["requested_frames"], 63)
        self.assertEqual(rw[0]["rewound_frames"], 63)
        self.assertGreaterEqual(rig.nci.count("REWIND"), 63)     # B4 sends one every half frame
        carry = rig.row("input_hold_carry")[0]
        self.assertEqual((carry["pre_hold_frames"], carry["stall_frames"]), (59, 4))
        res = rig.row("resumed", "hold_return_stall")[0]
        self.assertEqual(res["output_age_ms"], 40)
        self.assertEqual(res["packets_back_to_resume_ms"], 1348)
        # the client's gate still sends gate-bit stalls over fresh output: ignored, no second pause
        for i in range(10):
            rig.stall(ret + 1.4 + 0.05 * i, 20, gate=True)
        self.assertEqual(rig.calls, ["pause", "resume"])
        self.assertEqual(len(rig.row("stall_gate_after_return")), 1)
        # the late stall_end: a logged no-op
        rig.stall(ret + 2.2, 15, kind=ss.KIND_END)
        late = rig.row("stall_end_late")
        self.assertEqual(len(late), 1)
        self.assertEqual(late[0]["ignored_gate_stalls"], 10)
        self.assertEqual(rig.calls, ["pause", "resume"])
        self.assertEqual(rig.row("stall_end_after_gate"), [])
        # the client's ready after the resume: B6's client_ready_after_hold, as B6 wrote it -- not a session
        out = rig.rec.note_gameplay_released()
        self.assertEqual(out, {"recovered": True, "from_state": "hold_resumed"})
        self.assertEqual(len(rig.row("client_ready_after_hold")), 1)
        self.assertEqual(rig.row("session_started"), [])
        # B6's cap rule: the handed-over hold was not counted as released
        self.assertEqual(len(rig.t._released), 0)

    def test_the_gate_ready_first_resumes_with_the_hold_rewind_not_without(self):
        rig = Rig()
        ret = both(rig)
        rig.at(ret + 0.9)
        # the plugin's ready action: B8 first (the core still paused), then its own resume if paused (it is not),
        # then the recovery's note
        self.assertTrue(rig.own.ready_resume(rig.rec))
        out = rig.rec.note_gameplay_released()
        self.assertEqual(out, {"recovered": True, "from_state": "hold_resumed"})
        self.assertEqual(len(rig.row("client_ready_after_hold")), 1)
        self.assertEqual(rig.row("session_started"), [])
        self.assertEqual(rig.calls, ["pause", "resume"])
        rw = rig.row("input_release", "client_ready_hold")
        self.assertEqual((rw[0]["pre_hold_frames"], rw[0]["stall_frames"], rw[0]["requested_frames"]), (59, 4, 63))
        rig.heartbeat(ret + 1.3, 40)
        rig.tick(ret + 1.35)                                      # nothing left to resume
        self.assertEqual(rig.calls, ["pause", "resume"])
        rig.stall(ret + 1.4, 20, gate=True)
        self.assertEqual(rig.calls, ["pause", "resume"])

    def test_b7_alone_reproduces_bench_r2_b1(self):
        """The same sequence with B8 absent: the ready resumes without the rewind, a gate stall pauses again, and only
        that pause's own frames are rewound at stall_end (BENCH-R2 §3 b1)."""
        rig = Rig(b8=False)
        ret = both(rig)
        rig.at(ret + 1.9)
        rig.calls.append("resume")                                # the plugin's ready action resumes the core
        rig.rec.note_gameplay_released()
        rig.stall(ret + 1.95, 6, gate=True)
        rig.stall(ret + 2.2, 15, kind=ss.KIND_END)
        self.assertEqual(rig.calls, ["pause", "resume", "pause", "resume"])
        rw = [r for r in rig.rows() if r["event"] in ("input_release", "rewind_failed")]
        self.assertEqual(len(rw), 1)
        self.assertLessEqual(rw[0]["requested_frames"], 12)       # the second pause's own, not the ~57 pre-hold

    def test_stall_end_before_the_fresh_heartbeat_is_b7s_resume_with_the_carried_rewind(self):
        rig = Rig()
        ret = both(rig)
        rig.stall(ret + 0.4, 10, kind=ss.KIND_END)
        self.assertEqual(rig.calls, ["pause", "resume"])
        rw = rig.row("input_release", "stall_end")
        self.assertEqual(rw[0]["requested_frames"], 63)
        rig.heartbeat(ret + 1.3, 40)
        rig.tick(ret + 1.35)
        self.assertEqual(rig.calls, ["pause", "resume"])

    def test_a_stale_output_stall_after_the_return_still_pauses(self):
        rig = Rig()
        ret = both(rig)
        rig.heartbeat(ret + 1.3, 40)
        rig.tick(ret + 1.35)
        rig.stall(ret + 3.0, 400)                                 # a new downlink drop: B7 acts
        self.assertEqual(rig.calls, ["pause", "resume", "pause"])
        self.assertEqual(rig.events()[-2:], [("desync_pause", "client_stall"), ("client_stall", None)])

    def test_no_stall_at_the_return_is_b2s_release_and_the_gate_stalls_after_it_are_ignored(self):
        rig = Rig()
        rig.hold()
        rig.packet_back(4.0)                                      # no stall within B7's 60 ms: B2's release
        self.assertEqual(rig.calls, ["pause", "resume"])
        self.assertEqual(len(rig.row("input_release", "input_release")), 1)
        rig.stall(4.1, 30, gate=True)
        self.assertEqual(rig.calls, ["pause", "resume"])
        rig.stall(4.6, 10, kind=ss.KIND_END)
        self.assertEqual(len(rig.row("stall_end_late")), 1)

    def test_the_episode_expires(self):
        rig = Rig()
        ret = both(rig)
        rig.heartbeat(ret + 1.3, 40)
        rig.tick(ret + 1.35)
        rig.stall(ret + 1.35 + ho.EPISODE_S + 3.0, 20, gate=True)  # long after: B7's own rule again
        self.assertEqual(rig.calls, ["pause", "resume", "pause"])


class AtDown(unittest.TestCase):
    def run_down(self, b8):
        rig = Rig(b8=b8)
        rig.t0 = rig.clock.t
        rig.stall(1.00, 160)
        rig.stall(1.05, 210)
        rig.stall(3.00, 5, kind=ss.KIND_END)
        return rig

    def test_stall_only_is_b7_exactly(self):
        on, off = self.run_down(True), self.run_down(False)
        self.assertEqual(on.events(), off.events())
        self.assertEqual(on.calls, ["pause", "resume"])
        self.assertEqual(on.events(), [("desync_pause", "client_stall"), ("client_stall", None),
                                       ("input_release", "stall_end"), ("resumed", "stall_end")])
        a = on.row("input_release")[0]
        b = off.row("input_release")[0]
        self.assertNotIn("pre_hold_frames", a)
        self.assertEqual(a["requested_frames"], b["requested_frames"])


class RateLimit(unittest.TestCase):
    def test_b6_cap_counts_released_holds_only(self):
        rig = Rig()
        for i in range(ht.CAP_RELEASED):
            rig.hold(onset_dt=0.0)
            rig.packet_back(1.5)
            self.assertEqual(rig.rec._state, "PLAYING")
        self.assertEqual(rig.t.disarms, 1)
        rig2 = Rig()
        for i in range(ht.CAP_RELEASED + 2):
            rig2.clock.t += 30.0
            ret = both(rig2)
            rig2.heartbeat(ret + 1.3, 40)
            rig2.tick(ret + 1.35)
            rig2.stall(ret + 1.5, 10, kind=ss.KIND_END)
            self.assertEqual(rig2.rec._state, "PLAYING")
        self.assertEqual(rig2.t.disarms, 0)
        self.assertEqual(len(rig2.row("resumed", "hold_return_stall")), ht.CAP_RELEASED + 2)
        self.assertEqual(len(rig2.row("stall_end_late")), ht.CAP_RELEASED + 2)


class FlagAbsent(unittest.TestCase):
    def test_not_imported(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys; sys.path.insert(0, 'companion'); from games import link_drop_recovery as l; "
                "import stall_signal, hold_rewind; "
                "print('hold_ownership' in sys.modules, l.LinkDropRecovery._input_hold_b8)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(out.stdout.strip(), "False None", out.stderr[-400:])

    def test_hook_shapes(self):
        def ifs(rel, text):
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test).startswith(text)]
        self.assertEqual(len(ifs("games/link_drop_recovery.py", "self._input_hold_b8 is not None")), 3)
        self.assertEqual(len(ifs("stall_signal.py", "getattr(self.recovery, '_input_hold_b8', None) is not None")), 3)
        self.assertEqual(len(ifs("hold_rewind.py", "'b8' in pending")), 1)
        self.assertEqual(len(ifs("plugins/games.py", "_hold_ownership is not None")), 2)


if __name__ == "__main__":
    unittest.main()
