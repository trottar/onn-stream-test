#!/usr/bin/env python3
"""B55 (host): a PS2 session's automatic save states through PINE -- the slot-9 save (a silence or the client's
stall), its load at the hold's return / the stall resume (the picture checked after the recovery's resume), the link
give-up save to slot 8 and the recovery prompt's Resume / Copy / Discard. B51's PINE socket double, B52's fake window
and log; no PCSX2, no BIOS, no title.

    python3 -m unittest discover -s tests/ps2_session -v
"""

from __future__ import annotations

import json
import struct
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import ps2_session as ps2  # noqa: E402
import rewind_cores  # noqa: E402
from games import emulator_manager as em  # noqa: E402
import test_b51 as b51  # noqa: E402

STEM = b51.FAKE_STEM


class Rec:
    def __init__(self):
        self.rows = []

    def _log(self, event, **f):
        self.rows.append({"event": event, **f})

    def of(self, event):
        return [r for r in self.rows if r["event"] == event]


def rw():
    return types.SimpleNamespace(fps=60.0, _row=lambda recovery, event, fields, **extra: (
        recovery._log(event, **{**fields, **extra}), {**fields, **extra})[1])


class Base(b51.Base):
    def rig(self, picture="moving", tlb=False, **pine):
        d = self.double(**pine)
        m, lines, _ = b51.session_manager(d)
        fake = m._fake
        orig_grab, orig_run = fake.grab, fake.run

        def grab(w):
            if picture == "moving":
                return orig_grab(w)
            return bytes([90] * (ps2.GRAB_W * ps2.GRAB_H))          # static: one picture

        def run(cmd, **kw):
            r = orig_run(cmd, **kw)
            if tlb and cmd[:2] == ["xdotool", "key"] and not fake.paused and "Loaded state" in d.emulog.read_text():
                with open(d.emulog, "a") as fh:
                    fh.write("[   15.3] TLB Miss, pc=0x0 addr=0x0 [store]\n")
            return r
        fake.grab, fake.run = grab, run
        m._ps2.grab, m._ps2.run = grab, run
        rec = Rec()
        cores = rewind_cores.Cores("state", m, rec, clock=m._ps2.clock, threaded=False)
        spawned = []
        cores._spawn = spawned.append
        return m, d, lines, rec, cores, spawned

    def playing(self, m):
        m.resume()
        self.assertFalse(m._fake.paused)

    def hold(self, kind="silence", onset=10.0, pending_onset=None, **kw):
        m, d, lines, rec, cores, spawned = self.rig(**kw)
        self.playing(m)
        cores.save(onset, onset + 0.4, kind)
        m.pause()                                               # the hold / the stall owns a pause
        pending = {"onset": onset if pending_onset is None else pending_onset, "paused_at": onset + 1.0}
        row = cores.release(rw(), rec, {"via": "client_ready_stall" if kind == "stall" else "input_release"}, pending)
        return m, d, lines, rec, cores, spawned, row


class SlotNineSave(Base):
    def test_the_save_goes_through_pine_slot_9(self):
        m, d, lines, rec, cores, _ = self.rig()
        self.playing(m)
        cores.save(10.0, 10.4, "silence")
        self.assertEqual(d.requests[-1], struct.pack("<IBB", 6, 0x09, 9))
        row = rec.of("state_saved")[-1]
        self.assertEqual((row["slot"], row["core"], row["kind"], row["ps2_states"]), (9, "pcsx2", "silence", "pine"))
        self.assertTrue((d.sstates / f"{STEM}.09.p2s").is_file())
        self.assertIn("PS2 state save: slot 9 pine 0x09 ok (silence)", lines)
        self.assertFalse(m._fake.paused)                        # a running save: the game never paused for it

    def test_a_pine_failure_is_a_failed_save_row(self):
        m, d, lines, rec, cores, _ = self.rig(result=ps2.PINE_FAIL)
        self.playing(m)
        cores.save(10.0, 10.4, "stall")
        self.assertEqual(rec.of("state_save_failed")[-1]["ack"], "pine fail")
        self.assertFalse(cores.last_save["ok"])


class HoldReturn(Base):
    def test_the_hold_s_return_loads_slot_9_then_the_picture_after_the_resume(self):
        m, d, lines, rec, cores, spawned, row = self.hold()
        self.assertEqual(d.requests[-1], struct.pack("<IBB", 6, 0x0A, 9))
        self.assertEqual((rec.of("input_release")[-1]["ps2_states"], row["slot"], row["method"] if "method" in row
                          else "state", row["verification"], row["line"]), ("pine", 9, "state", "picture_after_resume",
                                                                           True))
        self.assertLessEqual(row["load_ms"], ps2.RELEASE_SHARE_S * 1000.0)
        self.assertTrue(m._fake.paused)                         # the release left the resume to the recovery
        self.playing(m)                                         # the recovery's resume
        self.assertEqual(len(spawned), 1)
        spawned[0]()
        check = rec.of("ps2_states")[-1]
        self.assertEqual((check["check"], check["verdict"], check["slot"]), ("picture", "ok", 9))
        self.assertEqual(rec.of("rewind_failed"), [])
        self.assertTrue(any(l.startswith("PS2 state load: slot 9 picture ok") for l in lines))
        self.assertIsNone(cores.last_save)                      # one load per save

    def test_the_stall_resume_loads_the_stall_save(self):
        m, d, lines, rec, cores, spawned, row = self.hold(kind="stall", onset=20.0, pending_onset=20.06)
        self.assertEqual(d.requests[-1], struct.pack("<IBB", 6, 0x0A, 9))
        self.assertEqual((rec.of("input_release")[-1]["via"], rec.of("input_release")[-1]["ps2_states"]),
                         ("client_ready_stall", "pine"))
        self.playing(m)
        spawned[0]()
        self.assertEqual(rec.of("ps2_states")[-1]["verdict"], "ok")

    def test_a_static_picture_is_the_ps1_shaped_rewind_failed_row(self):
        m, d, lines, rec, cores, spawned, row = self.hold(picture="static")
        self.playing(m)
        spawned[0]()
        self.assertEqual(rec.of("ps2_states")[-1]["verdict"], "static")
        self.assertEqual(rec.of("rewind_failed")[-1]["reason"], "the game did not resume from the save (picture static)")

    def test_a_tlb_miss_is_a_fault(self):
        m, d, lines, rec, cores, spawned, row = self.hold(tlb=True)
        self.playing(m)
        spawned[0]()
        self.assertEqual(rec.of("rewind_failed")[-1]["reason"], "the game did not resume from the save (picture fault)")

    def test_an_incomplete_file_resumes_without_a_load(self):
        m, d, lines, rec, cores, spawned, row = self.hold(write_file=False)
        self.assertNotIn(struct.pack("<IBB", 6, 0x0A, 9), d.requests)
        self.assertEqual(rec.of("rewind_skipped")[-1]["reason"], "the PS2 state file is not complete")
        self.assertEqual(spawned, [])


class ThroughTheRewinder(Base):
    def test_the_rewinder_hands_a_ps2_release_to_b9s_state_mode(self):
        import threading
        import hold_rewind
        m, d, lines, rec, cores, spawned = self.rig()
        self.playing(m)
        cores.save(10.0, 10.4, "silence")
        m.pause()
        r = object.__new__(hold_rewind.Rewinder)
        r._lock = threading.Lock()
        r.cap, r.b9, r.emulator, r.fps = 30, cores, m, 60.0
        r.counter_before = lambda pending: 50
        r._row = rw()._row
        rec._state_since = 7
        r._pending = {"key": 7, "onset": 10.0, "paused_at": 11.0}
        r.rewind(rec, "input_release")
        self.assertEqual(d.requests[-1], struct.pack("<IBB", 6, 0x0A, 9))
        self.assertEqual(rec.of("input_release")[-1]["ps2_states"], "pine")
        self.assertEqual(rec.of("rewind_skipped"), [])


class GiveUpAndPrompt(Base):
    def give_up(self, **kw):
        m, d, lines, rec, cores, spawned = self.rig(**kw)
        saved = m.save_recovery_state()                         # the give-up finds the game paused
        return m, d, lines, saved

    def test_the_give_up_save_is_slot_8_with_the_index(self):
        m, d, lines, saved = self.give_up()
        self.assertEqual(d.requests[-1], struct.pack("<IBB", 6, 0x09, 8))
        self.assertEqual(saved["ps2_states"], "pine")
        self.assertTrue(saved["state_file"].endswith(".08.p2s"))
        detail = m.recovery_state_detail()
        self.assertTrue(detail["exists"]); self.assertEqual(detail["game_id"], "game_ps2_fake")
        self.assertTrue(any(l.startswith("PS2 recovery save: slot 8 pine 0x09 ok; file complete") for l in lines))

    def test_the_give_up_row_carries_ps2_states(self):
        from games import link_drop_recovery as ldr
        import tempfile
        rec = ldr.LinkDropRecovery(Path(tempfile.mkdtemp(prefix="b55_")), pause_game=lambda: None,
                                   resume_game=lambda: None,
                                   save_recovery_state=lambda: {"state_file": "x.08.p2s", "ps2_states": "pine"},
                                   restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
                                   end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
                                   recovery_save_detail=lambda: {})
        rec._give_up_and_save()
        row = [json.loads(x) for x in rec.log_path().read_text().splitlines() if '"gave_up_saved"' in x][0]
        self.assertEqual((row["ps2_states"], row["state_file"]), ("pine", "x.08.p2s"))
        self.assertNotIn("save_skipped", row)

    def test_resume_loads_slot_8_with_the_picture_and_leaves_it_running(self):
        m, d, lines, saved = self.give_up()
        self.playing(m)                                          # the fresh launch, running (R3c2's option A)
        r = m.load_recovery_state_running()
        self.assertEqual(d.requests[-1], struct.pack("<IBB", 6, 0x0A, 8))
        self.assertEqual((r["verification"], r["ps2_states"]), ("picture", "pine"))
        self.assertFalse(m._fake.paused)
        self.assertTrue(any("PS2 recovery load: slot 8 pine 0x0a ok; picture ok" in l for l in lines))

    def test_resume_with_a_static_picture_is_ps1s_error(self):
        m, d, lines, saved = self.give_up(picture="static")
        self.playing(m)
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_recovery_state_running()
        self.assertEqual(str(cm.exception), "The game did not resume from the save")

    def test_copy_to_a_slot_and_discard(self):
        m, d, lines, saved = self.give_up()
        r = m.copy_recovery_state_to_slot(2)
        dest = d.sstates / f"{STEM}.02.p2s"
        self.assertEqual(dest.read_bytes(), (d.sstates / f"{STEM}.08.p2s").read_bytes())
        self.assertEqual((r["slot"], r["confirmed"]), (2, True))
        self.assertTrue(m._save_state_slot_detail(2)["exists"])
        gone = m.discard_recovery_state()
        self.assertTrue(gone["removed"])
        self.assertFalse((d.sstates / f"{STEM}.08.p2s").exists())
        self.assertTrue(dest.exists())                           # the copy stays
        self.assertFalse(m.recovery_state_detail()["exists"])


class RetroArchUntouched(unittest.TestCase):
    def test_a_retroarch_session_never_takes_a_pine_branch(self):
        rec = Rec()
        sent = []

        class Nci:
            def send(self, c):
                sent.append(c)

            def close(self):
                pass
        emu = types.SimpleNamespace(_launch_kind=None, _paused=False, _network_cmd_port=55355, _ps2=None)
        c = rewind_cores.Cores("state", emu, rec, threaded=False)
        c.nci_factory = lambda port: Nci()
        orig = rewind_cores._read
        rewind_cores._read = lambda nci, bound, prefix: "SAVE_STATE_SLOT 9"
        try:
            c.save(1.0, 1.4)
        finally:
            rewind_cores._read = orig
        self.assertEqual(sent, ["SAVE_STATE_SLOT 9"])
        self.assertNotIn("ps2_states", rec.of("state_saved")[-1])


if __name__ == "__main__":
    unittest.main()
