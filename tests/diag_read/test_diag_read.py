#!/usr/bin/env python3
"""B36: diag_read on a fake keeper dir (temp dirs only; read-only on its sources; no live log, no network).

    python3 -m unittest discover -s tests/diag_read -v
"""

from __future__ import annotations

import hashlib
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(HERE))
import diag_read as dr  # noqa: E402
import diag_fixture as fx  # noqa: E402

NY = ZoneInfo("America/New_York")


def tree_hash(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(Path(d).rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(d)).encode() + p.read_bytes())
    return h.hexdigest()


class TheRange(unittest.TestCase):
    NOW = datetime(2026, 10, 31, 15, 0, 0)          # 11:00 EDT

    def test_last_night_is_yesterday_17_to_today_08_local(self):
        lab, a, b = dr.parse_range("last night", self.NOW, NY)
        self.assertEqual((lab, a, b), ("last-night", datetime(2026, 10, 30, 21, 0), datetime(2026, 10, 31, 12, 0)))

    def test_last_night_across_the_dst_change(self):
        lab, a, b = dr.parse_range("Last  Night", datetime(2026, 11, 1, 18, 0), NY)   # Sunday 13:00 EST
        self.assertEqual((a, b), (datetime(2026, 10, 31, 21, 0), datetime(2026, 11, 1, 13, 0)))

    def test_today_is_local_midnight_to_now(self):
        self.assertEqual(dr.parse_range("today", self.NOW, NY), ("today", datetime(2026, 10, 31, 4, 0), self.NOW))

    def test_utc_ranges(self):
        self.assertEqual(dr.parse_range("2026-10-30 21:00..05:00", self.NOW, NY)[1:],
                         (datetime(2026, 10, 30, 21, 0), datetime(2026, 10, 31, 5, 0)))
        self.assertEqual(dr.parse_range("2026-10-30 21:00..23:30", self.NOW, NY)[1:],
                         (datetime(2026, 10, 30, 21, 0), datetime(2026, 10, 30, 23, 30)))
        self.assertEqual(dr.parse_range("2026-10-30 21:00..2026-10-31 06:10", self.NOW, NY)[1:],
                         (datetime(2026, 10, 30, 21, 0), datetime(2026, 10, 31, 6, 10)))
        self.assertEqual(dr.parse_range("trip", self.NOW, NY), ("trip", None, None))
        for bad in ("yesterday", "2026-10-30 21:00", "2026-10-31 05:00..2026-10-30 21:00"):
            with self.assertRaises(ValueError):
                dr.parse_range(bad, self.NOW, NY)


class TheRead(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="b36_read_"))
        self.kd = fx.write_keeper_dir(self.tmp / fx.DAY)
        self.before = tree_hash(self.kd)
        logs = dr.Logs()
        logs.add_keeper_dir(self.kd)
        self.an = dr.Analysis(logs, datetime(2026, 10, 30, 9, 0), datetime(2026, 10, 30, 11, 0), NY)

    def test_chunks_join_across_a_split_line_and_equal_the_live_layout(self):
        live = dr.Logs()
        live.add_live(fx.write_live(self.tmp / "logs"))
        k = dr.Logs()
        k.add_keeper_dir(self.kd)
        for name in dr.LOGS.values():
            self.assertEqual(k.data.get(name, b""), live.data.get(name, b""), name)
        self.assertEqual(len(k.reports), 1)
        self.assertEqual(k.game_logs, [fx.GAME_LOG])

    def test_two_sessions_their_columns(self):
        self.assertEqual(len(self.an.sessions), 2)
        r1, r2 = (self.an.session_row(s) for s in self.an.sessions)
        self.assertEqual((r1["title"], r1["core"], r1["path_class"]), ("PS1 golf", "beetle-psx-hw", "remote-direct"))
        self.assertEqual((r1["players"], r1["slot_map"]), (2, {"0": "pad-a", "1": "pad-b"}))
        self.assertEqual(r1["length_s"], 300)
        self.assertEqual(r1["rung_history"], ["10:03:00 4000->5000 in place"])
        self.assertEqual((r1["rtt_p50_ms"], r1["rtt_p95_ms"]), (120.0, 400.0))
        self.assertEqual(r1["hitch_s"], 4)
        self.assertEqual(r1["hitch_by"], {"R": 1, "C": 1, "G": 1, "L": 1})
        self.assertEqual(r1["hitch_s_per_10min"], 8.0)
        self.assertEqual((r1["silences"], r1["silences_user"]), (1, 0))
        self.assertEqual(r1["stalls"], ["10:02:00 420.0ms"])
        self.assertEqual(r1["pauses"], ["10:02:00 client_stall"])
        self.assertEqual(r1["rewinds"], ["10:02:00 resume (no_loss)"])
        self.assertEqual(r1["lost_post_fec"], 40)
        self.assertEqual(r1["underruns"], 1)
        self.assertEqual(r1["end_kind"], "client restart (restart_fast)")
        self.assertEqual(r1["surface_lost"][0]["reason"], "pause")
        self.assertEqual(len(r1["restarts"]), 1)
        self.assertEqual((r2["end_kind"], r2["silences"], r2["silences_user"], r2["players"]), ("user exit (bye)", 0, 1, None))
        self.assertEqual((r2["rtt_p50_ms"], r2["start_rung"]), (None, 4000))
        self.assertEqual(r2["restart_cause"]["away_ms"], 2000)

    def test_the_restart_and_its_cause(self):
        d = self.an.restart_detail(self.an.restarts[0])
        self.assertEqual((d["session"], d["title"], d["rung_before"], d["rung_after"]), (1, "PS1 golf", 5000, 4000))
        self.assertEqual((d["last_stepup_dt_s"], d["last_stepup_in_session"]), (120, True))
        self.assertEqual((d["trigger"], d["paused_ms"], d["away_ms"]), ("surface", 1500, 2000))
        self.assertEqual(d["surface_lost"][0]["keys"], ["BUTTON_MODE"])

    def test_the_markdown(self):
        text = dr.render(self.an, "test", [datetime(2026, 10, 30, 10, 2, 0)], around_saves=True)
        for h in ("## Sessions", "## Per 10 min", "## Every client restart, with its cause",
                  "## Every rewind, pause, hold and stall", "## Ladder transitions", "## Pad slots (B34)", "## VOD (B35)",
                  "## Per-second views (±60 s)", "### ±60 s around restart 2026-10-30T10:05:00Z",
                  "### ±60 s around stall 2026-10-30T10:02:00Z", "### ±60 s around the time 2026-10-30T10:02:00Z"):
            self.assertIn(h, text)
        self.assertIn("via stall_end, method resume, why no_loss", text)
        self.assertIn("| 10:03:00 | 4000 → 5000 | yes | remote |", text)
        self.assertIn("vod_error", text)
        self.assertIn("Range log: 2 requests, 1500 bytes; closes: eof 1, reset 1.", text)
        self.assertEqual(tree_hash(self.kd), self.before)                # the source untouched

    def test_main_writes_once_and_never_overwrites(self):
        out = self.tmp / "reads" / "r.md"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(dr.main(["2026-10-30", "09:00..11:00", "--source", str(self.kd), "--out", str(out)]), 0)
        first = out.read_bytes()
        self.assertIn(b"## Sessions", first)
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), \
                open(os.devnull, "w") as dn, unittest.mock.patch("sys.stderr", dn):
            dr.main(["2026-10-30 09:00..11:00", "--source", str(self.kd), "--out", str(out)])
        self.assertEqual(out.read_bytes(), first)
        p1 = dr.new_path(self.tmp / "reads", "x")
        p1.write_text("a")
        self.assertNotEqual(dr.new_path(self.tmp / "reads", "x"), p1)

    def test_trip_reads_the_trip_dir_span(self):
        lab, an = dr.build("trip", datetime(2026, 10, 31), trip_dir=self.kd, tz=NY)
        self.assertEqual(lab, "trip")
        self.assertEqual((an.t0, an.t1), (datetime(2026, 10, 30, 9, 59), datetime(2026, 10, 30, 10, 12)))
        self.assertEqual(len(an.sessions), 2)

    def test_default_sources_are_the_day_dirs_that_overlap(self):
        (self.tmp / "2026-09-01").mkdir()
        (self.tmp / "notes").mkdir()
        got = dr.keeper_dirs_for(self.tmp, datetime(2026, 10, 30, 9), datetime(2026, 10, 30, 11))
        self.assertEqual(got, [self.kd])
        lab, an = dr.build("2026-10-30 09:00..11:00", datetime(2026, 10, 31), root=self.tmp, tz=NY)
        self.assertEqual(len(an.sessions), 2)


import unittest.mock  # noqa: E402

if __name__ == "__main__":
    unittest.main()
