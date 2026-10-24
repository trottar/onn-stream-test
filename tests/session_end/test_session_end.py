#!/usr/bin/env python3
"""B18: no save and no hold once the session's end is known (inside `PRIVYHUB_INPUT_HOLD_REWIND=1`, `state`).

    python3 -m unittest discover -s tests/session_end -v

B9's loopback fake core and rig (the real recovery, B4's Rewinder with B9's Cores, B2's detector with B9's mark), B7's
real StallSignal (its worker by hand), B18's SessionEnd wired by B9's own `wire`. CL-B11 cells 2 / 3: at each window's
end the controller went silent, B9's save fired at 400 ms, then the client's report (+154-181 ms) and stop (+205-207).
The design: `docs/memory/evidence/b18_2026-10-24/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "rewind_cores"))

import rewind_cores as rc  # noqa: E402
import stall_signal as ss  # noqa: E402
import test_rewind_cores as b9  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

SNES = b9.SNES


class Teardown:
    def __init__(self):
        self.rig = b9.Rig("1", SNES)
        self.rec = self.rig.rec
        self.se = self.rec._session_end
        self.sig = ss.StallSignal(self.rec, ss.parse("1")[0], threaded=False)
        self.rec._client_stall = self.sig
        self.packets = 0
        self.se.packets = lambda: self.packets

    def quiet(self, onset, upto_s, step=0.01, produce=True):
        """The controller loop's timeouts after the last packet at `onset`: B2's detector (B9's mark first)."""
        t = onset
        while t <= onset + upto_s:
            if produce:
                self.packets += 1                                      # the stream's sender, every 10 ms
            self.rig.det.on_quiet(t, onset)
            t += step

    def events(self):
        return [r["event"] for r in b9.rows(self.rec) if not r["event"].endswith("_config")]

    def stop(self):
        self.rig.stop()


class NormalTeardown(unittest.TestCase):
    def test_the_bye_then_the_silence_no_save_no_hold_zero_state_saved(self):
        t = Teardown()
        try:
            self.assertIsNotNone(t.se)
            onset = time.monotonic()
            t.sig.handle((ss.KIND_BYE, False, 1, 40_000, 8), onset)      # the client's bye, then its sender stops
            t.quiet(onset, 0.62)                                         # the 400-ms mark passes; the stop at ~0.61 s
            self.assertFalse(t.rec.note_input_hold(955.0))               # B2's hold at ~950 ms: skipped
            t.rec.session_ended()                                        # the client's native-stream-stop
            self.assertEqual(t.rig.wait_saves(1, timeout=0.5), 0)
            ev = t.events()
            self.assertEqual(ev.count("state_saved"), 0)
            self.assertIn("session_end_bye", ev)
            skipped = [r for r in b9.rows(t.rec) if r["event"] == "state_save_skipped"]
            self.assertEqual([(s["reason"]) for s in skipped], ["client_bye"])
            self.assertIn("input_hold_skipped_ending", ev)
            self.assertNotIn("desync_pause", ev)
            self.assertEqual(t.rec.calls, [])
        finally:
            t.stop()

    def test_a_blackout_without_a_bye_saves_as_today(self):
        t = Teardown()
        try:
            onset = time.monotonic()
            t.quiet(onset, 0.45)
            self.assertEqual(t.rig.wait_saves(1), 1)
            self.assertEqual(t.events().count("state_saved"), 1)
        finally:
            t.stop()

    def test_the_stream_no_longer_produced_saves_nothing(self):
        t = Teardown()
        try:
            onset = time.monotonic()
            t.quiet(onset, 0.45, produce=False)                          # the sender's count flat
            self.assertEqual(t.rig.wait_saves(1, timeout=0.3), 0)
            skipped = [r for r in b9.rows(t.rec) if r["event"] == "state_save_skipped"]
            self.assertEqual([s["reason"] for s in skipped], ["stream_stopped"])
        finally:
            t.stop()

    def test_the_session_ended_saves_nothing(self):
        t = Teardown()
        try:
            t.rec.session_ended()
            onset = time.monotonic()
            t.quiet(onset, 0.45)
            self.assertEqual(t.rig.wait_saves(1, timeout=0.3), 0)
            self.assertEqual([r["reason"] for r in b9.rows(t.rec) if r["event"] == "state_save_skipped"],
                             ["state_ended"])
        finally:
            t.stop()

    def test_a_new_session_after_a_bye_saves_again(self):
        t = Teardown()
        try:
            t.sig.handle((ss.KIND_BYE, False, 1, 40_000, 8), time.monotonic())
            t.rec.session_ended()
            t.rec.session_started()                                      # the next session: a new PLAYING period
            onset = time.monotonic()
            t.quiet(onset, 0.45)
            self.assertEqual(t.rig.wait_saves(1), 1)
        finally:
            t.stop()


class TheWiring(unittest.TestCase):
    def test_b7_decodes_the_bye_and_ignores_it_without_b9(self):
        pkt = ss.PACKET.pack(ss.MAGIC, ss.KIND_BYE, 0, 0, 1, 2, 3)
        self.assertEqual(ss.decode(pkt), (3, False, 1, 2, 3))
        rec = b9.recovery()
        sig = ss.StallSignal(rec, 400, threaded=False)
        sig.handle((ss.KIND_BYE, False, 1, 2, 3), time.monotonic())
        self.assertEqual([r["event"] for r in b9.rows(rec)], [])
        self.assertEqual((sig.stalls, sig.ends), (0, 0))

    def test_only_the_state_path_wires_it(self):
        rig = b9.Rig("rewind", SNES)
        try:
            self.assertIsNone(rig.rec._session_end)
        finally:
            rig.stop()
        self.assertIsNone(ldr.LinkDropRecovery._session_end)

    def test_flag_absent_nothing_imported(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys; sys.path.insert(0, 'companion'); from games import link_drop_recovery as l; "
                "print('rewind_cores' in sys.modules, l.LinkDropRecovery._session_end)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(out.stdout.strip(), "False None", out.stderr[-400:])


if __name__ == "__main__":
    unittest.main()
