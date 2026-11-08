#!/usr/bin/env python3
"""B51 (host): PrivyHub's SAVE / LOAD buttons for a PS2 session through PINE (MsgSaveState 0x09 / MsgLoadState 0x0A,
read from PCSX2 2.8.2's binary), answering exactly as the PS1 path. A PINE socket double (a real Unix socket thread)
records every request and writes the state file as PCSX2 does. No PCSX2, no BIOS, no title, no real folder.

    python3 -m unittest discover -s tests/ps2_session -v
"""

from __future__ import annotations

import io
import json
import signal
import socket
import struct
import sys
import tempfile
import threading
import types
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401  (B53: this run's temp dirs removed at exit)

import ps2_session as ps2  # noqa: E402
from games import emulator_manager as em  # noqa: E402

FAKE_STEM = "FAKE-00000 (0BADF00D)"


def zip_bytes(n: int = 4096) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("eeMemory.bin", b"\x00" * n)
    return buf.getvalue()


class PineDouble:
    """A Unix-socket PINE server: answers each message with [u32 5][u8 result]; on a save it writes the slot's .p2s
    (as PCSX2's zip thread would), on a load it appends PCSX2's log line -- each only when told to."""

    def __init__(self, root: Path, result=ps2.PINE_OK, write_file=True, log_line=True, answer=True):
        self.root = root
        self.path = root / "pcsx2.sock"
        self.result, self.write_file, self.log_line, self.answer = result, write_file, log_line, answer
        self.requests: list[bytes] = []
        self.sstates = root / "data/games/ps2/sstates"
        self.emulog = ps2.pcsx2_log_path(root)
        self.sstates.mkdir(parents=True, exist_ok=True)
        self.emulog.parent.mkdir(parents=True, exist_ok=True)
        # B52: the game booted in this launch (PCSX2's ELF line), so a load goes straight on
        self.emulog.write_text("[    0.1] PCSX2 log start\n[    3.2] ELF Loading: <elf>, Game CRC = 00000000, EntryPoint = 0x00100008\n")
        self.srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.srv.bind(str(self.path))
        self.srv.listen(4)
        self.t = threading.Thread(target=self.serve, daemon=True)
        self.t.start()

    def serve(self):
        while True:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            with c:
                head = c.recv(4)
                if len(head) < 4:
                    continue
                size = struct.unpack("<I", head)[0]
                body = b""
                while len(body) < size - 4:
                    body += c.recv(size - 4 - len(body))
                self.requests.append(head + body)
                op, slot = body[0], (body[1] if len(body) > 1 else None)
                if op == ps2.MSG_SAVE_STATE and self.result == ps2.PINE_OK and self.write_file:
                    f = self.sstates / f"{FAKE_STEM}.{slot:02d}.p2s"
                    if f.exists():                    # PCSX2's BackupSavestate: the old one kept, a new file written
                        f.replace(f.with_name(f.name + ".backup"))
                    f.write_bytes(zip_bytes())
                if op == ps2.MSG_LOAD_STATE and self.result == ps2.PINE_OK and self.log_line:
                    with open(self.emulog, "a") as fh:
                        fh.write(f"[   12.0] Loaded state from slot {slot}.\n")
                if self.answer:
                    c.sendall(struct.pack("<IB", 5, self.result))

    def close(self):
        self.srv.close()


class FakeProc:
    pid = 4242
    returncode = None
    stdin = None

    def poll(self):
        return None


class FakePcsx2:
    """B52: the hotkey toggles the pause (PINE reads it); the window's picture moves only while running."""

    def __init__(self, status=ps2.PINE_PAUSED):
        self.paused = status != ps2.PINE_RUNNING
        self.fixed = status            # None = PINE silent
        self.frame = 0

    def run(self, cmd, **kw):
        if cmd[:2] == ["xdotool", "key"]:
            self.paused = not self.paused
        return types.SimpleNamespace(stdout="77\n" if "search" in cmd else "")

    def status(self):
        if self.fixed is None:
            return None
        return ps2.PINE_PAUSED if self.paused else ps2.PINE_RUNNING

    def grab(self, window):
        if not self.paused:
            self.frame += 1
        return bytes([(self.frame * 37 + i) % 200 + 40 for i in range(ps2.GRAB_W * ps2.GRAB_H)])


def session_manager(pine: PineDouble, paused_by="hotkey", status=ps2.PINE_PAUSED):
    m = em.EmulatorManager(pine.root, config_path=(ROOT / "companion/games/config/emulators.json"))
    lines, kills, clock = [], [], [0.0]
    fake = FakePcsx2(status)
    m.process = FakeProc()
    m.active_game = {"id": "game_ps2_fake", "system": "ps2", "title": "made-up", "relative_path": "ps2/one.chd"}
    m._launch_kind = "pcsx2"
    m._paused = True
    m._ps2 = ps2.Session(4242, lines.append, run=fake.run, status=fake.status,
                         kill=lambda pid, sig: kills.append(int(sig)),
                         sleep=lambda d: clock.__setitem__(0, clock[0] + d), clock=lambda: clock[0],
                         pine_path=pine.path, grab=fake.grab, log_path=pine.emulog)
    m._fake = fake
    m._ps2.paused_by = paused_by
    return m, lines, kills


class Base(unittest.TestCase):
    def setUp(self):
        self.old = em._ps2
        em._ps2 = ps2                         # what PRIVYHUB_PS2=1 sets at import
        self.root = Path(tempfile.mkdtemp(prefix="b51_"))

    def tearDown(self):
        em._ps2 = self.old

    def double(self, **kw):
        d = PineDouble(self.root, **kw)
        self.addCleanup(d.close)
        return d


class Codes(unittest.TestCase):
    def test_the_message_codes_are_the_binarys(self):
        # PCSX2 2.8.2, PINEServer::MainLoop's jump table (evidence/b51_2026-11-08/pine_opcodes.txt):
        # 0x09 -> VMManager::SaveStateToSlot, 0x0a -> VMManager::LoadStateFromSlot, 0x0f -> the status
        self.assertEqual((ps2.MSG_SAVE_STATE, ps2.MSG_LOAD_STATE, ps2.MSG_STATUS), (0x09, 0x0A, 0x0F))
        self.assertEqual((ps2.PINE_OK, ps2.PINE_FAIL), (0x00, 0xFF))


class Save(Base):
    def test_save_sends_0x09_and_the_slot_and_answers_as_ps1(self):
        d = self.double()
        m, lines, _ = session_manager(d)
        r = m.save_state(2)
        self.assertEqual(d.requests, [struct.pack("<IBB", 6, 0x09, 2)])
        for k, v in (("action", "save_state"), ("slot", 2), ("accepted", True), ("confirmed", True),
                     ("replaced_existing", False), ("overwrite_requires_confirmation", False)):
            self.assertEqual(r[k], v, k)
        self.assertEqual(r["state_file"], f"data/games/ps2/sstates/{FAKE_STEM}.02.p2s")
        self.assertTrue(r["slot_detail"]["exists"])
        self.assertEqual(r["slot_detail"]["source"], "privyhub_game_slot_index")      # PS1's own index
        self.assertGreater(r["slot_detail"]["size_bytes"], 0)
        self.assertIn("modified_unix_ms", r["slot_detail"])
        self.assertTrue(any(l.startswith("PS2 save: slot 2 pine 0x09 ok; file complete") for l in lines))
        # the Game State list (status) shows it like a PS1 slot; slots 1 / 3 empty
        details = {x["slot"]: x["exists"] for x in m.status()["save_state_slot_details"]}
        self.assertEqual(details, {1: False, 2: True, 3: False})
        # a second save of the slot replaces it, said as PS1 says it
        self.assertTrue(m.save_state(2)["replaced_existing"])

    def test_a_pine_failure_is_ps1s_error_never_the_refusal(self):
        for kw, text in (({"result": ps2.PINE_FAIL}, "PCSX2 did not acknowledge the save state"),
                         ({"answer": False}, "PCSX2 did not acknowledge the save state"),
                         ({"write_file": False}, "PrivyHub could not verify the saved PS2 state")):
            root = Path(tempfile.mkdtemp(prefix="b51_"))
            d = PineDouble(root, **kw)
            self.addCleanup(d.close)
            m, lines, _ = session_manager(d)
            with self.assertRaises(em.EmulatorError) as cm:
                m.save_state(1)
            self.assertEqual(str(cm.exception), text)
            self.assertNotIn("not available", str(cm.exception))

    def test_a_sigstop_pause_is_turned_into_the_hotkey_pause_first(self):
        d = self.double()
        seq = [ps2.PINE_RUNNING, ps2.PINE_PAUSED]
        m, lines, kills = session_manager(d, paused_by="sigstop", status=None)
        m._ps2.status = lambda: seq.pop(0) if len(seq) > 1 else seq[0]
        m.save_state(1)
        self.assertEqual(kills, [int(signal.SIGCONT)])
        self.assertEqual(m._ps2.paused_by, "hotkey")
        self.assertIn("PS2 pause: hotkey (for a state message)", lines)

    def test_no_pine_after_sigcont_refuses_and_freezes_again(self):
        d = self.double()
        m, lines, kills = session_manager(d, paused_by="sigstop", status=None)
        with self.assertRaises(em.EmulatorError):
            m.save_state(1)
        self.assertEqual(kills, [int(signal.SIGCONT), int(signal.SIGSTOP)])
        self.assertEqual(d.requests, [])


class Load(Base):
    def test_load_sends_0x0a_and_answers_as_ps1(self):
        d = self.double()
        m, lines, _ = session_manager(d)
        m.save_state(3)
        r = m.load_state(3)
        self.assertEqual(d.requests[-1], struct.pack("<IBB", 6, 0x0A, 3))
        # B52 (disclosed): "confirmed" is the picture moving after the resume, not PCSX2's log line
        for k, v in (("action", "load_state"), ("slot", 3), ("accepted", True), ("confirmed", True),
                     ("verification", "picture"), ("paused", True)):
            self.assertEqual(r[k], v, k)
        self.assertTrue(r["slot_detail"]["exists"])
        self.assertTrue(any(l.startswith("PS2 load: slot 3 pine 0x0a ok; picture ok") for l in lines))
        self.assertTrue(m._fake.paused)                     # left paused, as PS1's load

    def test_without_pcsx2s_log_line_the_picture_still_decides(self):
        # B52 (disclosed): B51 read `visual_required` here; the picture check now decides
        d = self.double(log_line=False)
        m, _, _ = session_manager(d)
        m.save_state(1)
        r = m.load_state(1)
        self.assertEqual((r["confirmed"], r["verification"]), (True, "picture"))

    def test_ps1s_messages_for_an_empty_slot_not_paused_and_a_pine_failure(self):
        d = self.double()
        m, _, _ = session_manager(d)
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(2)
        self.assertEqual(str(cm.exception), "No save state exists in Slot 2")
        m._paused = False
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(2)
        self.assertEqual(str(cm.exception), "Load State requires the game to be paused")
        m._paused = True
        m.save_state(2)
        d.result = ps2.PINE_FAIL
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(2)
        self.assertEqual(str(cm.exception), "PCSX2 did not acknowledge the load state")

    def test_after_a_stop_and_relaunch_the_slot_is_still_listed(self):
        d = self.double()
        m, _, _ = session_manager(d)
        m.save_state(1)
        m2, _, _ = session_manager(d)          # a new session of the same title (the index on the hub)
        self.assertTrue(m2._save_state_slot_detail(1)["exists"])
        self.assertTrue(m2.load_state(1)["confirmed"])


class Ps1Untouched(Base):
    def test_a_retroarch_session_never_takes_the_pine_branch(self):
        m = em.EmulatorManager(self.root, config_path=(ROOT / "companion/games/config/emulators.json"))
        called = []
        m._pcsx2_save_state = lambda *a, **k: called.append("save")
        m._pcsx2_load_state = lambda *a, **k: called.append("load")
        for call in (lambda: m.save_state(1), lambda: m.load_state(1)):
            try:
                call()
            except Exception:
                pass                            # no RetroArch running here: today's own error
        self.assertEqual(called, [])
        self.assertIsNone(m._launch_kind)


if __name__ == "__main__":
    unittest.main()
