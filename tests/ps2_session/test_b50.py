#!/usr/bin/env python3
"""B50 (host): H3-P2's PS2 fixes -- the audio wait vs. PINE on a fake PCSX2 timeline, the formatted memory cards, the
tear-free present keys, the SDL3 binding names, the keeper's PS2 label, the P2 capture window. Fakes only (no PCSX2,
no BIOS, no title, no real folder); the whole directory runs in well under 10 s.

    python3 -m unittest discover -s tests/ps2_session -v
"""

from __future__ import annotations

import json
import signal
import struct
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401  (B53: this run's temp dirs removed at exit)
sys.path.insert(0, str(ROOT / "tools"))

import ps2_session as ps2  # noqa: E402
import ps2_memcard as mc  # noqa: E402
import diag_read as dr  # noqa: E402
import diag_check as dc  # noqa: E402
import ps2_p2_window as win  # noqa: E402


class FakePCSX2:
    """PCSX2's startup order (its own H3-P2 log: the audio stream, then the VM's init, then PINE) with the game logs'
    gaps: the window found, the sink-input 0.3 s later (0.1-0.3 s in H3-P2), PINE 0.1 s after that. The stream is
    created only by a running process; SIGSTOP freezes everything."""

    WINDOW, AUDIO, PINE = 1.40, 1.70, 1.80

    def __init__(self, pine_never=False):
        self.t = 0.0
        self.stopped = False
        self.audio = False
        self.paused = False
        self.pine_never = pine_never
        self.hotkeys = 0

    def _advance(self, d):
        if not self.stopped and not self.audio and self.t < self.AUDIO <= self.t + d:
            self.audio = True                      # the stream is created only by a running process
        self.t += d

    def sleep(self, d):
        self._advance(d)

    def clock(self):
        return self.t

    def run(self, cmd, **kw):
        out = ""
        if "search" in cmd:
            out = "77\n" if self.t >= self.WINDOW else ""
        elif cmd[:3] == ["pactl", "list", "sink-inputs"]:
            out = 'application.process.id = "4242"\n' if self.audio else ""
        elif cmd[:2] == ["xdotool", "key"] and not self.stopped and self.t >= self.PINE:
            self.paused = not self.paused
            self.hotkeys += 1
        self._advance(0.005)
        return types.SimpleNamespace(stdout=out)

    def status(self):
        if self.stopped or self.pine_never or self.t < self.PINE:
            return None
        return ps2.PINE_PAUSED if self.paused else ps2.PINE_RUNNING

    def kill(self, pid, sig):
        if sig == signal.SIGSTOP:
            self.stopped = True
        elif sig == signal.SIGCONT:
            self.stopped = False


def handoff(fake, wait_audio=True, pine_late_s=None):
    """The launch's steps (the window, A's audio wait) then the plugin's paused handoff."""
    s = ps2.Session(4242, lambda line: None, run=fake.run, status=fake.status, kill=fake.kill, sleep=fake.sleep,
                    clock=fake.clock)
    old = ps2.PINE_LATE_S
    if pine_late_s is not None:
        ps2.PINE_LATE_S = pine_late_s
    try:
        assert s.wait_window() == "77"
        waited = s.wait_audio() if wait_audio else None
        how = s.pause()
    finally:
        ps2.PINE_LATE_S = old
    return how, waited


class AudioWaitVsPine(unittest.TestCase):
    def test_the_wait_and_pine_late_is_the_hotkey_with_the_audio_present(self):
        f = FakePCSX2()
        how, waited = handoff(f)
        self.assertEqual(how, "hotkey")
        self.assertTrue(f.audio and f.paused and not f.stopped)
        self.assertIsNotNone(waited)

    def test_the_wait_and_pine_never_is_sigstop_after_the_audio_exists(self):
        f = FakePCSX2(pine_never=True)
        how, _ = handoff(f)
        self.assertEqual(how, "sigstop")
        self.assertTrue(f.audio and f.stopped)              # the picture frozen, the audio stream present

    def test_the_wait_alone_without_the_pine_poll_is_still_ok(self):
        f = FakePCSX2()
        how, _ = handoff(f, pine_late_s=0.0)
        self.assertTrue(f.audio)                            # A's change alone already fixes the defect
        self.assertEqual(how, "sigstop")

    def test_b49_no_wait_and_pine_late_reproduces_the_defect(self):
        f = FakePCSX2()
        how, _ = handoff(f, wait_audio=False, pine_late_s=0.0)
        self.assertEqual(how, "sigstop")
        f.sleep(60.0)                                       # a whole minute later: still no stream
        self.assertFalse(f.audio)                           # "Game stream isn't ready": no sink-input, ever

    def test_the_wait_is_bounded(self):
        f = FakePCSX2()
        f.stopped = True                                    # a PCSX2 that never makes its stream
        s = ps2.Session(4242, lambda line: None, run=f.run, status=f.status, kill=f.kill, sleep=f.sleep, clock=f.clock)
        self.assertIsNone(s.wait_audio(bound=ps2.AUDIO_WAIT_S))
        self.assertGreaterEqual(f.t, ps2.AUDIO_WAIT_S)


class MemoryCards(unittest.TestCase):
    NOW = 1_762_560_000.0

    def test_a_formatted_card_reads_back_formatted(self):
        data = mc.format_card(self.NOW)
        self.assertEqual(len(data), 8_650_752)
        r = mc.check(data)
        self.assertTrue(r["formatted"], r["problems"])
        self.assertEqual(r["free_clusters"], mc.ALLOC_END - 1)
        self.assertEqual(data[:28], b"Sony PS2 Memory Card Format ")
        self.assertEqual(data[0x1C:0x23], mc.VERSION)
        self.assertEqual(struct.unpack_from("<HHHHIIIIII", data, 0x28),
                         (512, 2, 16, 0xFF00, 8192, 41, 8135, 0, 1023, 1022))
        self.assertEqual(struct.unpack_from("<I", data, 0x50)[0], 8)
        self.assertEqual(data[0x150:0x152], bytes((2, 0x52)))
        self.assertEqual(mc.format_card(self.NOW), data)    # deterministic for a given time

    def test_the_unformatted_and_the_corrupt_are_caught(self):
        self.assertFalse(mc.check(b"\xFF" * mc.CARD_BYTES)["formatted"])
        self.assertTrue(mc.is_unformatted(b"\xFF" * mc.CARD_BYTES))
        good = bytearray(mc.format_card(self.NOW))
        bad = bytearray(good)
        bad[100] ^= 0x01                                    # a superblock data byte: its ECC no longer matches
        self.assertIn("ecc on 1 page(s)", mc.check(bytes(bad))["problems"])
        bad2 = bytearray(good)
        bad2[0] = ord("X")
        self.assertFalse(mc.check(bytes(bad2))["formatted"])
        self.assertFalse(mc.check(b"\x00" * 10)["formatted"])

    def test_the_ecc_tables_equal_pcsx2s_own(self):
        # the first 80 bytes of the column-parity table in PCSX2 2.8.2's binary (the full 2 x 256 compared in
        # docs/memory/evidence/b50_2026-11-08/ecc_table_check.txt)
        pcsx2 = bytes.fromhex(
            "0007161125223334343322251116070043445552666170777770616652554443"
            "5255444377706166666170774344555211160700343322252522333400071611"
            "61667770444352555552434470776661")
        self.assertEqual(mc.COLUMN_MASKS[:80], pcsx2)
        self.assertEqual(mc.PARITY[:8], bytes((0, 1, 1, 0, 1, 0, 0, 1)))
        self.assertEqual(mc.ecc128(b"\xFF" * 128), bytes((0x77, 0x7F, 0x7F)))
        # the Hamming property: a lone odd-parity byte at index i is located by the line parities (lp1 = i, lp0 = ~i)
        for i in range(128):
            chunk = bytearray(128)
            chunk[i] = 0x01
            cp, lp0, lp1 = mc.ecc128(bytes(chunk))
            self.assertEqual((lp1 ^ 0x7F, lp0 ^ 0x7F, cp ^ 0x77), (i, ~i & 0x7F, mc.COLUMN_MASKS[1]))

    def test_ensure_cards_never_touches_a_card_with_data(self):
        d = Path(tempfile.mkdtemp())
        (d / "Mcd002.ps2").write_bytes(b"\xFF" * mc.CARD_BYTES)
        user = bytearray(mc.format_card(self.NOW))
        user[5000] = 0x42
        (d / "Mcd003.ps2").write_bytes(bytes(user))
        r = mc.ensure_cards(d, ["Mcd001.ps2", "Mcd002.ps2", "Mcd003.ps2"], self.NOW)
        self.assertEqual(r, {"Mcd001.ps2": "created", "Mcd002.ps2": "formatted", "Mcd003.ps2": "kept"})
        self.assertTrue(mc.check((d / "Mcd001.ps2").read_bytes())["formatted"])
        self.assertTrue(mc.check((d / "Mcd002.ps2").read_bytes())["formatted"])
        self.assertEqual((d / "Mcd003.ps2").read_bytes(), bytes(user))
        self.assertEqual(mc.ensure_cards(d, ["Mcd001.ps2"], self.NOW), {"Mcd001.ps2": "kept"})
        self.assertFalse(list(d.glob("*.tmp")))


class IniKeys(unittest.TestCase):
    def test_vsync_mailbox_and_the_card_slots(self):
        s = ps2.settings_for(Path("/proj"), "image.bin", None, 2, False)
        self.assertEqual((s["EmuCore/GS"]["VsyncEnable"], s["EmuCore/GS"]["DisableMailboxPresentation"]),
                         ("true", "false"))
        self.assertEqual(s["MemoryCards"], {"Slot1_Enable": "true", "Slot1_Filename": "Mcd001.ps2",
                                            "Slot2_Enable": "true", "Slot2_Filename": "Mcd002.ps2"})

    def test_every_binding_is_a_name_pcsx2_accepts(self):
        accepted = ps2.SDL_BUTTONS | ps2.SDL_AXES
        for players, tap in ((1, False), (2, False), (4, True)):
            secs = ps2.pad_sections(players, tap)
            bound = [v for k, sec in secs.items() if k.startswith("Pad") and k != "Pad" for kk, v in sec.items()
                     if kk != "Type"]
            self.assertEqual(len(bound), 24 * players)
            for v in bound:
                prefix, name = v.split("/", 1)
                self.assertRegex(prefix, r"^SDL-[0-3]$")
                self.assertIn(name, accepted, v)
                self.assertNotIn(name, {"A", "B", "X", "Y"})
        self.assertEqual({n for n in dict(ps2.DS2_BINDINGS).values()} - accepted, set())
        self.assertEqual(len(ps2.DS2_BINDINGS), 24)          # every DualShock 2 button and stick direction


class Keeper(unittest.TestCase):
    def logs(self, with_ps2_row=True, ps2_log=True):
        root = Path(tempfile.mkdtemp())
        games = root / "games"
        games.mkdir()
        rows = [
            {"at_utc": "2026-11-08T02:00:00.000Z", "event": "remote_config", "class": "lan"},
            {"at_utc": "2026-11-08T02:00:05.000Z", "event": "session_started"},
            {"at_utc": "2026-11-08T02:10:05.000Z", "event": "session_ended"},
            {"at_utc": "2026-11-08T02:12:10.000Z", "event": "remote_config", "class": "lan"},
        ]
        if with_ps2_row:
            rows.append({"at_utc": "2026-11-08T02:12:15.000Z", "event": "ps2_session", "ps2_mode": True,
                         "save_states": "off"})
        rows += [{"at_utc": "2026-11-08T02:12:16.000Z", "event": "session_started"},
                 {"at_utc": "2026-11-08T02:22:16.000Z", "event": "session_ended"}]
        (games / "native_stream_recovery.log").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        (games / "20261107-205900-game_ps1_04ff1234.log").write_text("x\n")      # a PS1 launch (local time, NY)
        if ps2_log:
            (games / "20261107-211207-ps2.log").write_text("x\n")
        logs = dr.Logs()
        logs.add_live(root)
        return dr.Analysis(logs, datetime(2026, 11, 8, 1, 0), datetime(2026, 11, 8, 3, 0), ZoneInfo("America/New_York"))

    def test_a_ps2_session_is_labelled_ps2_and_a_ps1_one_as_before(self):
        an = self.logs()
        rows = [an.session_row(s) for s in an.sessions]
        self.assertEqual([(r["core"], r.get("system")) for r in rows], [("beetle-psx-hw", None), ("pcsx2", "ps2")])
        self.assertNotIn("system", rows[0])
        self.assertEqual(rows[1]["title"], "PS2")
        self.assertEqual(dr.Analysis.ps1_reference(rows), [rows[0]])

    def test_the_row_alone_or_the_log_alone_label_it(self):
        for kw in ({"ps2_log": False}, {"with_ps2_row": False}):
            an = self.logs(**kw)
            self.assertEqual(an.session_row(an.sessions[1]).get("system"), "ps2", kw)

    def test_the_keepers_copier_takes_the_ps2_log(self):
        import trip_log_keeper as tlk
        self.assertTrue(tlk.GAME_LOG.match("20261107-211207-ps2.log"))
        self.assertTrue(tlk.GAME_LOG.match("20261107-205900-game_ps1_04ff1234.log"))
        self.assertTrue(dr.is_game_log("20261107-211207-ps2.log"))

    def test_diag_check_prints_a_seventh_line_only_for_a_ps2_newest_row(self):
        d = Path(tempfile.mkdtemp())
        p = d / "sessions.jsonl"
        self.assertIsNone(dc.line_last_session(p))
        p.write_text(json.dumps({"core": "beetle-psx-hw", "end_utc": "2026-11-08T02:10:05Z"}) + "\n")
        self.assertIsNone(dc.line_last_session(p))
        with p.open("a") as fh:
            fh.write(json.dumps({"core": "pcsx2", "system": "ps2", "end_utc": "2026-11-08T02:22:16Z",
                                 "hitch_s_per_10min": 0.0}) + "\n")
        self.assertEqual(dc.line_last_session(p),
                         "last session: ps2 (pcsx2) 2026-11-08T02:22:16Z, hitch s / 10 min 0.0")


class CaptureWindow(unittest.TestCase):
    T0 = datetime(2026, 11, 8, 2, 0, 0, tzinfo=timezone.utc)

    def at(self, s):
        return self.T0 + timedelta(seconds=s)

    def test_minute_3_when_clear(self):
        p = win.plan([self.at(0)], [], self.at(10))
        self.assertEqual((p["start_utc"], p["wait_s"], p["fallback"]), ("2026-11-08T02:03:00Z", 170, False))

    def test_pushed_past_a_back_and_a_new_release(self):
        # a Back at 3:20, the Resume's release at 3:40: the capture starts >= 60 s after 3:40 and >= 90 s after 3:20
        p = win.plan([self.at(0), self.at(220)], [self.at(200)], self.at(100))
        self.assertEqual(p["start_utc"], "2026-11-08T02:04:50Z")
        self.assertFalse(p["fallback"])

    def test_the_fallback_is_minute_3(self):
        pauses = [self.at(s) for s in range(120, 700, 60)]
        p = win.plan([self.at(0)], pauses, self.at(0))
        self.assertEqual((p["start_utc"], p["fallback"]), ("2026-11-08T02:03:00Z", True))

    def test_check_after_a_back_inside(self):
        self.assertTrue(win.valid(self.at(180), [self.at(0)], []))
        self.assertFalse(win.valid(self.at(180), [self.at(0)], [self.at(260)]))     # P7f's case
        self.assertFalse(win.valid(self.at(30), [self.at(0)], []))                   # too soon after the release

    def test_the_cli_reads_the_two_logs(self):
        d = Path(tempfile.mkdtemp())
        (d / "rec.log").write_text(json.dumps({"at_utc": "2026-11-08T02:00:00.000Z", "event": "session_started"}) + "\n")
        (d / "g-ps2.log").write_text("2026-11-08T02:02:30.000Z PS2 pause: hotkey\n")
        starts, pauses = win.read_events(d / "rec.log", d / "g-ps2.log")
        self.assertEqual((len(starts), len(pauses)), (1, 1))
        self.assertEqual(win.plan(starts, pauses, self.at(0))["start_utc"], "2026-11-08T02:04:00Z")


if __name__ == "__main__":
    unittest.main()
