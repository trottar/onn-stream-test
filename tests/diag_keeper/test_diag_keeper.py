#!/usr/bin/env python3
"""B36: the diagnostics keeper on a fake log dir that rotates (temp dirs under /tmp only; no stream, no network, no
companion; the samplers, the journal and the peer count are fakes; the clock is fake -- the run's sleep advances it).
The only deletions are the retention rule's, inside the tests' own /tmp roots.

    python3 -m unittest discover -s tests/diag_keeper -v
"""

from __future__ import annotations

import ipaddress
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "diag_read"))
import diag_keeper as dk  # noqa: E402
import trip_log_keeper as tlk  # noqa: E402
import diag_fixture as fx  # noqa: E402

V4 = str(ipaddress.ip_address(0xC6336414))                       # a documentation-range address


def unix(y, mo, d, h=0, mi=0, s=0):
    return datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc).timestamp()


class Clock:
    def __init__(self, t):
        self.t = t
        self.hooks = []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += max(s, 0.5)
        for h in list(self.hooks):
            h(self.t)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="b36_keeper_"))
        self.logs = self.tmp / "logs"
        self.games = self.logs / "games"
        (self.games / "stream_log_archive").mkdir(parents=True)
        (self.games / "decoder_sessions").mkdir()
        self.root = self.tmp / "privyhub_diag"
        self.clock = Clock(unix(2026, 10, 30, 23, 50))
        self.summaries = []

    def keeper(self, summary="fake", copy_s=300.0, sample_s=60.0):
        def fake(end):
            self.summaries.append((self.clock(), end))
            return {"end_utc": end, "players": 2, "note": f"from {V4}"}
        return dk.DiagKeeper(self.root, logs_root=self.logs, summary=fake if summary == "fake" else summary,
                             redactor=tlk.Redactor(lambda: []), overlay=lambda: {"connected": True, "path": "direct"},
                             session=lambda: {"state": "idle"}, journal=lambda s, u: b"", peers=lambda: 1,
                             clock=self.clock, sleep=self.clock.sleep, copy_s=copy_s, sample_s=sample_s)

    def write(self, rel, text, mode="a"):
        p = self.logs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, mode) as fh:
            fh.write(text)

    def stop_at(self, t):
        self.clock.hooks.append(lambda now: (self.root / "STOP").touch() if now >= t else None)

    def joined(self, key):
        out = b""
        for day in sorted(os.listdir(self.root)):
            d = self.root / day / "raw" / key
            if dk.DAY.match(day) and d.is_dir():
                for f in sorted(os.listdir(d)):
                    out += (d / f).read_bytes()
        return out


class TheCopy(Base):
    def test_day_dirs_roll_at_utc_midnight_without_losing_a_byte(self):
        k = self.keeper()
        written = []

        def feed(now):
            line = f'{{"at_utc": "{tlk.utc(now)}", "event": "x", "n": {len(written)}}}\n'
            written.append(line)
            self.write("games/native_stream_recovery.log", line)
        self.write("games/native_stream_recovery.log", "before the start\n")
        self.clock.hooks.append(feed)
        self.stop_at(unix(2026, 10, 31, 0, 20))
        self.assertEqual(k.run(), "STOP")
        days = sorted(d for d in os.listdir(self.root) if dk.DAY.match(d))
        self.assertEqual(days, ["2026-10-30", "2026-10-31"])
        self.assertEqual(self.joined("games__native_stream_recovery.log").decode(), "".join(written))
        self.assertTrue((self.root / "2026-10-30" / "manifest.sha256").read_text())
        self.assertTrue((self.root / "2026-10-31" / "samples" / "overlay.jsonl").is_file())
        self.assertIn("done (STOP)", (self.root / "status.txt").read_text())

    def test_the_vod_logs_are_copied_and_redacted(self):
        k = self.keeper()
        self.stop_at(self.clock() + 400)
        self.clock.hooks.append(lambda now: self.write("vod_range.jsonl", f'{{"peer": "{V4}", "bytes": 1}}\n')
                                if not (self.logs / "vod_range.jsonl").exists() else None)
        self.write("vod_client.jsonl", "")
        self.clock.hooks.append(lambda now: self.write("vod_client.jsonl", '{"event": "vod_retry"}\n')
                                if (self.logs / "vod_client.jsonl").stat().st_size == 0 else None)
        k.run()
        self.assertEqual(self.joined("vod_client.jsonl"), b'{"event": "vod_retry"}\n')
        got = self.joined("vod_range.jsonl").decode()
        self.assertNotIn(V4, got)
        self.assertIn("<ipv4>", got)

    def test_a_restart_of_the_unit_resumes_at_the_saved_offset(self):
        self.write("games/native_stream_heartbeat.log", "old\n")
        k = self.keeper()
        self.write("games/native_stream_heartbeat.log", "")
        self.clock.hooks.append(lambda now: self.write("games/native_stream_heartbeat.log", "a\n") if now < self.clock.t0 + 100 else None)
        self.clock.t0 = self.clock()
        self.stop_at(self.clock() + 200)
        k.run()
        first = self.joined("games__native_stream_heartbeat.log")
        (self.root / "STOP").rename(self.tmp / "STOP.used")              # A's step to run again (a rename, not a deletion)
        self.write("games/native_stream_heartbeat.log", "while down\n")   # written while the unit was stopped
        self.clock.hooks = []
        k2 = self.keeper()
        self.stop_at(self.clock() + 400)
        k2.run()
        self.assertEqual(self.joined("games__native_stream_heartbeat.log"), first + b"while down\n")
        self.assertNotIn(b"old", self.joined("games__native_stream_heartbeat.log"))

    def test_a_new_file_after_the_restart_is_read_from_its_end(self):
        self.write("games/native_stream_heartbeat.log", "a\n")
        k = self.keeper()
        self.stop_at(self.clock() + 100)
        k.run()
        (self.root / "STOP").rename(self.tmp / "STOP.used")
        os.replace(self.games / "native_stream_heartbeat.log", self.games / "stream_log_archive" / "native_stream_heartbeat.log.1")
        self.write("games/native_stream_heartbeat.log", "new file, before the second start\n")
        self.clock.hooks = []
        k2 = self.keeper()
        self.clock.hooks.append(lambda now: self.write("games/native_stream_heartbeat.log", "after\n")
                                if b"after" not in (self.games / "native_stream_heartbeat.log").read_bytes() else None)
        self.stop_at(self.clock() + 400)
        k2.run()
        self.assertEqual(self.joined("games__native_stream_heartbeat.log"), b"after\n")

    def test_a_sigterm_ends_with_a_final_copy_and_leaves_no_stop_file(self):
        k = self.keeper()
        self.clock.hooks.append(lambda now: self.write("games/native_stream_recovery.log", "x\n"))
        self.clock.hooks.append(lambda now: setattr(k, "term", True) if now > self.clock.t0 + 30 else None)
        self.clock.t0 = self.clock()
        self.assertEqual(k.run(), "SIGTERM")
        self.assertFalse((self.root / "STOP").exists())
        self.assertTrue(self.joined("games__native_stream_recovery.log"))

    def test_the_root_may_not_be_inside_the_repo(self):
        with self.assertRaises(SystemExit):
            dk.DiagKeeper(dk.REPO / "docs" / "privyhub_diag_test_never_created", logs_root=self.logs,
                          redactor=tlk.Redactor(lambda: []))
        self.assertFalse((dk.REPO / "docs" / "privyhub_diag_test_never_created").exists())


class TheSummary(Base):
    def test_a_session_ended_writes_one_row_90_s_later(self):
        self.write("games/native_stream_recovery.log", "")
        k = self.keeper()
        ended = {}

        def end(now):
            if not ended and now > self.clock.t0 + 120:
                ended["at"] = now
                self.write("games/native_stream_recovery.log",
                           json.dumps({"at_utc": tlk.utc(now), "event": "session_ended"}) + "\n")
        self.clock.t0 = self.clock()
        self.clock.hooks.append(end)
        self.stop_at(self.clock() + 400)
        k.run()
        self.assertEqual(len(self.summaries), 1)
        at, _ = self.summaries[0]
        self.assertGreaterEqual(at - ended["at"], dk.SUMMARY_DELAY_S)
        self.assertLess(at - ended["at"], dk.SUMMARY_DELAY_S + 2 * 60 + 1)
        rows = [json.loads(x) for x in (self.root / "sessions.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["players"], 2)
        self.assertNotIn(V4, rows[0]["note"])

    def test_not_written_before_the_delay(self):
        self.write("games/native_stream_recovery.log", "")
        k = self.keeper()
        self.clock.hooks.append(lambda now: self.write("games/native_stream_recovery.log",
                                                       json.dumps({"at_utc": tlk.utc(now), "event": "session_ended"}) + "\n")
                                if not (self.games / "native_stream_recovery.log").stat().st_size else None)
        self.stop_at(self.clock() + 61)
        k.run()
        self.assertEqual(self.summaries, [])
        self.assertEqual(len(k.pending), 1)

    def test_the_real_summary_from_the_live_logs(self):
        fx.write_live(self.logs)
        row = dk.live_summary(self.logs, self.root, fx.iso(fx.at(300)))
        self.assertEqual((row["players"], row["slot_map"]), (2, {"0": "pad-a", "1": "pad-b"}))
        # at session 1's summary the next session still runs: its report (the client's cause) has not come yet;
        # B32's surface_lost row is there; session 2's own row carries the cause from its report
        self.assertIsNone(row["restarts"][0]["trigger"])
        self.assertEqual(row["restarts"][0]["surface_lost"][0]["reason"], "pause")
        row2 = dk.live_summary(self.logs, self.root, fx.iso(fx.at(480)))
        self.assertEqual(row2["restart_cause"]["trigger"], "surface")
        self.assertIsNone(row["restart_cause"])
        self.assertEqual(row["rewinds"], ["10:02:00 resume (no_loss)"])
        self.assertEqual(row["rung_history"], ["10:03:00 4000->5000 in place"])
        for col in ("start_utc", "length_s", "core", "title", "players", "slot_map", "path_class", "rung_history",
                    "lost_post_fec", "rtt_p50_ms", "rtt_p95_ms", "rendered_fps_med", "resyncs", "pauses", "holds",
                    "stalls", "restarts", "hitch_s", "hitch_s_per_10min", "silences_per_10min", "underruns"):
            self.assertIn(col, row)
        self.assertEqual(dk.live_summary(self.logs, self.root, "2026-10-30T12:00:00.000Z")["error"], "session not found")

    def test_a_failing_summary_writes_its_error_and_the_keeper_goes_on(self):
        self.write("games/native_stream_recovery.log", "")

        def boom(end):
            raise KeyError("x")
        k = self.keeper(summary=boom)
        self.clock.hooks.append(lambda now: self.write("games/native_stream_recovery.log",
                                                       json.dumps({"at_utc": tlk.utc(now), "event": "session_ended"}) + "\n")
                                if not (self.games / "native_stream_recovery.log").stat().st_size else None)
        self.stop_at(self.clock() + 400)
        self.assertEqual(k.run(), "STOP")
        rows = [json.loads(x) for x in (self.root / "sessions.jsonl").read_text().splitlines()]
        self.assertEqual(rows[0]["error"], "KeyError")


class TheRetention(unittest.TestCase):
    def test_only_whole_day_dirs_older_than_30_days(self):
        root = Path(tempfile.mkdtemp(prefix="b36_retention_"))         # the only deletions: inside this /tmp root
        outside = Path(tempfile.mkdtemp(prefix="b36_retention_target_"))
        (outside / "keep.txt").write_text("k")
        for name in ("2026-10-31", "2026-10-01", "2026-09-30", "2025-01-01"):
            (root / name / "raw").mkdir(parents=True)
            (root / name / "raw" / "f.txt").write_text("x")
        (root / "notadate").mkdir()
        (root / "2026-13-45").mkdir()                                   # date-shaped, not a date
        (root / "2020-01-01").write_text("a file named like a date")
        os.symlink(outside, root / "2020-01-02")                        # a symlink named like a date
        (root / "nested").mkdir()
        (root / "nested" / "2020-01-03").mkdir()
        (root / "sessions.jsonl").write_text("{}\n")
        removed = dk.retention(root, unix(2026, 10, 31, 12))
        self.assertEqual(sorted(r["removed"] for r in removed), ["2025-01-01", "2026-09-30"])
        self.assertEqual(sorted(os.listdir(root)), ["2020-01-01", "2020-01-02", "2026-10-01", "2026-10-31", "2026-13-45",
                                                    "nested", "notadate", "retention.jsonl", "sessions.jsonl"])
        self.assertTrue((outside / "keep.txt").is_file())
        self.assertTrue((root / "nested" / "2020-01-03").is_dir())
        rows = [json.loads(x) for x in (root / "retention.jsonl").read_text().splitlines()]
        self.assertEqual({r["removed"]: r["files"] for r in rows}, {"2025-01-01": 1, "2026-09-30": 1})

    def test_the_run_applies_it_at_the_start_and_at_the_date_change(self):
        tmp = Path(tempfile.mkdtemp(prefix="b36_retention_run_"))
        logs = tmp / "logs"
        (logs / "games").mkdir(parents=True)
        root = tmp / "diag"
        for name in ("2026-09-29", "2026-09-30", "2026-10-01"):
            (root / name).mkdir(parents=True)
        clock = Clock(unix(2026, 10, 30, 23, 55))
        k = dk.DiagKeeper(root, logs_root=logs, summary=lambda e: {}, redactor=tlk.Redactor(lambda: []),
                          overlay=lambda: {}, session=lambda: {}, journal=lambda s, u: b"", peers=lambda: 0,
                          clock=clock, sleep=clock.sleep)
        self.assertTrue((root / "2026-09-30").is_dir())
        clock.hooks.append(lambda now: (root / "STOP").touch() if now > unix(2026, 10, 31, 0, 10) else None)
        k.run()
        self.assertFalse((root / "2026-09-29").exists())                 # at the start (10-30: older than 30 days)
        self.assertFalse((root / "2026-09-30").exists())                 # at the date change (10-31)
        self.assertTrue((root / "2026-10-01").is_dir())
        self.assertEqual(k.removed, 2)


class TheUnit(unittest.TestCase):
    def test_the_unit_text_is_the_file_in_tools(self):
        self.assertEqual((ROOT / "tools" / "privyhub-diag.service").read_text(), dk.UNIT_TEXT)
        self.assertIn("ExecStart=/usr/bin/python3 -B %h/Projects/onn-stream-test/tools/diag_keeper.py", dk.UNIT_TEXT)
        self.assertIn("WantedBy=default.target", dk.UNIT_TEXT)


if __name__ == "__main__":
    unittest.main()
