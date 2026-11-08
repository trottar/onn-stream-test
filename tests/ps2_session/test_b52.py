#!/usr/bin/env python3
"""B52 (host): the PS2 load runs the game from the state -- MTVU off in the ini; the load held until the game's ELF
is up; "confirmed" = the window's picture moving after the resume, PINE running and no `TLB Miss`; otherwise PS1's
error shape ("The game did not resume from the save") with the game left paused. Everything faked (B51's PINE socket
double, a fake PCSX2 window and log); no PCSX2, no BIOS, no title.

    python3 -m unittest discover -s tests/ps2_session -v
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401  (B53: this run's temp dirs removed at exit)
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ps2_session as ps2  # noqa: E402
from games import emulator_manager as em  # noqa: E402
import test_b51 as b51  # noqa: E402

ELF = "[    3.2] ELF Loading: <elf>, Game CRC = 00000000, EntryPoint = 0x00100008\n"


class Base(b51.Base):
    def manager(self, picture="moving", tlb=False, elf=True, elf_on_resume=False):
        d = self.double()
        if not elf:
            d.emulog.write_text("[    0.1] PCSX2 log start\n")
        m, lines, kills = b51.session_manager(d)
        fake = m._fake
        orig_grab, orig_run = fake.grab, fake.run

        def grab(w):
            if picture == "moving":
                return orig_grab(w)
            if picture == "black":
                fake.frame += 1
                return bytes([fake.frame % 256] + [0] * (ps2.GRAB_W * ps2.GRAB_H - 1))   # distinct, all near-black
            return bytes([90] * (ps2.GRAB_W * ps2.GRAB_H))          # static: one picture

        def run(cmd, **kw):
            r = orig_run(cmd, **kw)
            if cmd[:2] == ["xdotool", "key"] and not fake.paused:
                with open(d.emulog, "a") as fh:
                    if elf_on_resume and ELF not in d.emulog.read_text():
                        fh.write(ELF)
                    if tlb and "Loaded state" in d.emulog.read_text():
                        fh.write("[   15.3] TLB Miss, pc=0x0 addr=0x0 [store]\n")
            return r
        fake.grab, fake.run = grab, run
        m._ps2.grab, m._ps2.run = grab, run
        m.save_state(1)
        return m, d, lines


class Picture(Base):
    def test_a_moving_picture_is_confirmed(self):
        m, d, lines = self.manager()
        r = m.load_state(1)
        self.assertEqual((r["confirmed"], r["verification"], r["paused"]), (True, "picture", True))
        self.assertEqual(d.requests[-1], struct.pack("<IBB", 6, 0x0A, 1))
        self.assertTrue(any(l.startswith("PS2 load: slot 1 pine 0x0a ok; picture ok") for l in lines))
        self.assertTrue(m._fake.paused)                           # paused again after the check

    def test_a_static_picture_is_ps1s_error_and_the_game_left_paused(self):
        m, _, lines = self.manager(picture="static")
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(1)
        self.assertEqual(str(cm.exception), "The game did not resume from the save")
        self.assertTrue(m._fake.paused)
        self.assertTrue(m._paused)
        self.assertTrue(any("picture static 5.0s" in l for l in lines))

    def test_a_black_picture_is_static(self):
        m, _, lines = self.manager(picture="black")
        with self.assertRaises(em.EmulatorError):
            m.load_state(1)
        self.assertTrue(any("picture static" in l for l in lines))

    def test_a_tlb_miss_is_a_fault(self):
        m, _, lines = self.manager(tlb=True)
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(1)
        self.assertEqual(str(cm.exception), "The game did not resume from the save")
        self.assertTrue(any("picture fault" in l for l in lines))
        self.assertTrue(m._fake.paused)


class ElfHold(Base):
    def test_a_load_before_the_elf_runs_pcsx2_to_it_then_loads(self):
        m, d, lines = self.manager(elf=False, elf_on_resume=True)
        r = m.load_state(1)
        self.assertTrue(r["confirmed"])
        self.assertIn(ELF.strip(), d.emulog.read_text())
        self.assertTrue(any("picture ok" in l for l in lines))

    def test_no_elf_within_the_bound_is_the_starting_error(self):
        m, d, lines = self.manager(elf=False, elf_on_resume=False)
        n = len(d.requests)
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(1)
        self.assertEqual(str(cm.exception), "The game is still starting; play a moment, then load again")
        self.assertEqual(len(d.requests), n)                       # no load sent
        self.assertTrue(m._fake.paused)


class Ini(unittest.TestCase):
    def test_mtvu_off(self):
        s = ps2.settings_for(Path("/proj"), "image.bin", None, 2, False)
        self.assertEqual(s["EmuCore/Speedhacks"], {"vuThread": "false"})
        out = ps2.ini_merge("[EmuCore/Speedhacks]\nvuThread = true\nfastCDVD = false\n", s)
        self.assertEqual(ps2.ini_get(out, "EmuCore/Speedhacks", "vuThread"), "false")
        self.assertEqual(ps2.ini_get(out, "EmuCore/Speedhacks", "fastCDVD"), "false")   # PCSX2's own keys kept


if __name__ == "__main__":
    unittest.main()
