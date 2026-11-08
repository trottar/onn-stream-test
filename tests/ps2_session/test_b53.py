#!/usr/bin/env python3
"""B53 (host): PCSX2's own log per launch -- `-logfile data/games/ps2/logs/<UTC launch>-pcsx2.log`, 30-day retention,
copied by the keeper (raw/ps2logs__<name>/), counted per PS2 session by diag_read. Fake trees only; the temp dirs are
removed at the run's end (_tmp_cleanup).

    python3 -m unittest discover -s tests/ps2_session -v
"""

from __future__ import annotations

import calendar
import json
import sys
import tempfile
import time
import types
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "tools"))
import _tmp_cleanup  # noqa: E402,F401

import ps2_session as ps2  # noqa: E402
import trip_log_keeper as tlk  # noqa: E402
import diag_read as dr  # noqa: E402

T0 = calendar.timegm((2026, 11, 8, 8, 0, 0))          # 2026-11-08T08:00:00Z


class Name(unittest.TestCase):
    def test_the_name_is_the_utc_launch_time(self):
        p = ps2.pcsx2_log_for_launch(Path("/proj"), T0)
        self.assertEqual(p, Path("/proj/data/games/ps2/logs/20261108T080000Z-pcsx2.log"))

    def test_the_command_carries_it_before_the_title(self):
        log = Path("/proj/data/games/ps2/logs/20261108T080000Z-pcsx2.log")
        cmd = ps2.command(Path("/a.AppImage"), Path("/proj"), Path("/g/one.chd"), logfile=log)
        self.assertEqual(cmd[5:], ["-logfile", str(log), "--", "/g/one.chd"])
        self.assertNotIn("-logfile", ps2.command(Path("/a.AppImage"), Path("/proj"), Path("/g/one.chd")))

    def test_the_30_day_retention(self):
        d = Path(tempfile.mkdtemp(prefix="b53_"))
        old = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(T0 - 31 * 86400)) + "-pcsx2.log"
        young = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(T0 - 29 * 86400)) + "-pcsx2.log"
        for n in (old, young, "notes.txt", "emulog.txt"):
            (d / n).write_text("x")
        self.assertEqual(ps2.prune_pcsx2_logs(d, T0), [old])
        self.assertEqual(sorted(p.name for p in d.iterdir()), sorted([young, "notes.txt", "emulog.txt"]))


class KeeperCopy(unittest.TestCase):
    def test_a_new_pcsx2_log_is_copied_and_one_present_at_the_start_is_not(self):
        root = Path(tempfile.mkdtemp(prefix="b53_"))
        (root / "logs" / "games").mkdir(parents=True)
        ps2logs = root / "data" / "games" / "ps2" / "logs"
        ps2logs.mkdir(parents=True)
        (ps2logs / "20261108T070000Z-pcsx2.log").write_text("[    0.1] before the keeper\n")
        out = root / "diag"
        k = tlk.Keeper(out, float("inf"), 0.0, logs_root=root / "logs", overlay=lambda: {}, session=lambda: {},
                       journal=lambda a, b: b"", peers=lambda: 0, clock=lambda: T0)
        k.begin()
        (ps2logs / "20261108T080000Z-pcsx2.log").write_text("[    3.2] ELF Loading: <elf>\n[    9.0] Read Abort\n")
        k.copy()
        kept = sorted(p.relative_to(out / "raw").parts[0] for p in (out / "raw").rglob("*") if p.is_file())
        self.assertEqual(kept, ["ps2logs__20261108T080000Z-pcsx2.log"])
        text = next((out / "raw" / "ps2logs__20261108T080000Z-pcsx2.log").iterdir()).read_text()
        self.assertIn("Read Abort", text)

    def test_no_pcsx2_folder_is_todays_keeper(self):
        root = Path(tempfile.mkdtemp(prefix="b53_"))
        (root / "logs" / "games").mkdir(parents=True)
        k = tlk.Keeper(root / "diag", float("inf"), 0.0, logs_root=root / "logs", overlay=lambda: {},
                       session=lambda: {}, journal=lambda a, b: b"", peers=lambda: 0, clock=lambda: T0)
        k.begin()
        k.copy()
        self.assertFalse(any(k_.startswith("ps2logs/") for k_ in k.tails))
        self.assertEqual(k.seen["ps2_logs"], set())


class Counts(unittest.TestCase):
    def tree(self, with_log=True, ps2=True):
        root = Path(tempfile.mkdtemp(prefix="b53_"))
        games = root / "logs" / "games"
        games.mkdir(parents=True)
        rows = [{"at_utc": "2026-11-08T08:00:01.000Z", "event": "remote_config", "class": "lan"}]
        if ps2:
            rows.append({"at_utc": "2026-11-08T08:00:04.000Z", "event": "ps2_session", "ps2_mode": True})
        rows += [{"at_utc": "2026-11-08T08:00:05.000Z", "event": "session_started"},
                 {"at_utc": "2026-11-08T08:10:00.000Z", "event": "session_ended"}]
        (games / "native_stream_recovery.log").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        if with_log:
            logs = root / "data" / "games" / "ps2" / "logs"
            logs.mkdir(parents=True)
            (logs / "20261108T080000Z-pcsx2.log").write_text(
                "[    1.4] McdSlot 0 [File]: Mcd001.ps2 [8 MB, Formatted]\n"
                "[    1.5] McdSlot 1 [File]: Mcd002.ps2 [8 MB, Formatted]\n"
                "[    3.2] ELF Loading: <elf>, Game CRC = 00000000, EntryPoint = 0x00100008\n"
                "[  300.0] Read Abort\n"
                "[  301.0] CDVD read err, retrying... (attempt 1 of 3)\n"
                "[  400.0] OSD [SaveStateToSlot]: Saved state to slot 1.\n"
                "[  450.0] OSD [LoadStateFromSlot]: Loaded state from slot 1.\n"
                "[  450.5] TLB Miss, pc=0x0 addr=0x0 [load]\n"
                "[ 9000.0] Read Abort\n")                     # after the session: not counted
        lg = dr.Logs()
        lg.add_live(root / "logs")
        return dr.Analysis(lg, datetime(2026, 11, 8, 7, 0), datetime(2026, 11, 8, 9, 0))

    def test_the_counts_per_session(self):
        an = self.tree()
        r = an.session_row(an.sessions[0])
        self.assertEqual(r["system"], "ps2")
        self.assertEqual(r["pcsx2_log"], {"read_errors": 2, "invalid_binding": 0, "card_formatted": 2,
                                          "card_unformatted": 0, "tlb_miss": 1, "state_saved": 1, "state_loaded": 1,
                                          "elf": 1})
        self.assertIn("## PCSX2 logs (B53)", dr.render(an, "t", [], False))

    def test_no_log_or_a_ps1_session_has_no_key(self):
        an = self.tree(with_log=False)
        self.assertNotIn("pcsx2_log", an.session_row(an.sessions[0]))
        an2 = self.tree(ps2=False)
        self.assertNotIn("pcsx2_log", an2.session_row(an2.sessions[0]))
        self.assertNotIn("## PCSX2 logs (B53)", dr.render(an, "t", [], False))     # no log: today's report


if __name__ == "__main__":
    unittest.main()
