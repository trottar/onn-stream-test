#!/usr/bin/env python3
"""B66 (tools / host row): UX-R3's hold-resume split (a hold's `resumed` second and the next two counted apart; the
bar's number the rest; `hitch_s` itself today's), diag_check's last-session line for N64 / PS2 with the bar, and the
`launch_ports` row after a launch. B36's fixture evening, extended; temp dirs removed at exit.

    python3 -m unittest discover -s tests/b66_hitch_split -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "diag_read"))

import diag_read as dr  # noqa: E402
import diag_check as dc  # noqa: E402
import diag_fixture as fx  # noqa: E402

NY = ZoneInfo("America/New_York")
ORIG = fx.logs


def analysis(extra_rows):
    def logs():
        out = ORIG()
        out["native_stream_recovery.log"] += "".join(fx.rec(s, e, **kw) + "\n" for s, e, kw in extra_rows)
        return out
    fx.logs = logs
    try:
        kd = fx.write_keeper_dir(Path(tempfile.mkdtemp(prefix="b66_read_")) / fx.DAY)
    finally:
        fx.logs = ORIG
    lg = dr.Logs()
    lg.add_keeper_dir(kd)
    return dr.Analysis(lg, datetime(2026, 10, 30, 9, 0), datetime(2026, 10, 30, 11, 0), NY)


class Split(unittest.TestCase):
    def test_today_without_a_hold_resume(self):
        r1 = analysis([]).session_row(analysis([]).sessions[0])
        self.assertEqual((r1["hitch_s"], r1["hitch_s_per_10min"]), (4, 8.0))         # B36's numbers unchanged
        self.assertEqual((r1["hold_resume_s"], r1["hitch_s_bar"], r1["hitch_s_bar_per_10min"]), (0, 4, 8.0))

    def test_a_hold_resume_second_is_counted_apart(self):
        # the R hitch is at 10:01:40 (fixture second 100): a hold's resume at 99.6 covers 99, 100, 101
        an = analysis([(99.6, "resumed", {"via": "stall_end", "from_state": "PAUSED_RECOVERING"})])
        r1 = an.session_row(an.sessions[0])
        self.assertEqual((r1["hitch_s"], r1["hold_resume_s"], r1["hitch_s_bar"]), (4, 1, 3))
        self.assertEqual(r1["hitch_s_bar_per_10min"], 6.0)
        md = dr.render(an, "t", [datetime(2026, 10, 30, 10, 1, 40)], False)
        self.assertIn("hold-resume s", md)
        self.assertIn("bar hitch s / 10 min", md)
        self.assertRegex(md, r"\| 10:01:40 \| Rh \|")

    def test_not_a_hold_and_the_window(self):
        an = analysis([(149.6, "resumed", {"via": "client_ready"}),            # a link recovery: not a hold
                       (96.9, "resumed", {"via": "stall_quiet"})])               # covers 96-98, the R hitch at 100: no
        r1 = an.session_row(an.sessions[0])
        self.assertEqual((r1["hold_resume_s"], r1["hitch_s_bar"]), (0, 4))
        self.assertTrue(dr.is_hold_resume("client_ready_stall"))
        self.assertTrue(dr.is_hold_resume("hold_return_stall"))
        self.assertFalse(dr.is_hold_resume("client_ready"))


class CheckLine(unittest.TestCase):
    def line(self, row):
        p = Path(tempfile.mkdtemp(prefix="b66_chk_")) / "sessions.jsonl"
        p.write_text(json.dumps(row) + "\n")
        return dc.line_last_session(p)

    def test_n64_ps2_and_ps1(self):
        n64 = {"core": "mupen64plus-next", "end_utc": "x", "hitch_s_per_10min": 6.6, "hitch_s_bar_per_10min": 3.3,
               "hold_resume_s": 1}
        self.assertEqual(self.line(n64), "last session: n64 (mupen64plus-next) x, hitch s / 10 min 6.6 "
                                         "(bar 3.3 / 10 min, hold-resume 1 s)")
        ps2 = {"system": "ps2", "core": "pcsx2", "end_utc": "y", "hitch_s_per_10min": 1.0}
        self.assertEqual(self.line(ps2), "last session: ps2 (pcsx2) y, hitch s / 10 min 1.0")   # an old row: today
        self.assertIsNone(self.line({"core": "beetle-psx-hw", "hitch_s_per_10min": 0.0}))


class LaunchRow(unittest.TestCase):
    def plugin(self, payload, raise_exc=False):
        import importlib.util
        spec = importlib.util.spec_from_file_location("g66", str(ROOT / "companion/plugins/games.py"))
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)
        rows = []
        p = object.__new__(G.GamesPlugin)
        p._recovery = types.SimpleNamespace(_log=lambda e, **k: rows.append({"event": e, **k}))
        sess = {"players_chosen": 4, "ports": 4, "multitap": False, "multitap_available": False, "source": "join"}

        def launch(game, **kw):
            if raise_exc:
                raise RuntimeError("no")
            return payload
        p._emulator = types.SimpleNamespace(launch=launch, _launch_kind=None, _players_session=sess,
                                            _last_device_args=["--device=1:1", "--device=2:1"],
                                            active_game={"system": "n64"})
        p._find_game_by_id = lambda gid: {"id": gid, "system": "n64"}
        p._parse_cheat_launch_request = lambda q: (None, None)
        return p, rows

    def test_the_row(self):
        p, rows = self.plugin({"n64_session": {"layout": "face_c", "remap_binds": 8}})
        p.handle_post("launch", "id=game_n64_x&players_joined=2")
        lp = [r for r in rows if r["event"] == "launch_ports"]
        self.assertEqual(len(lp), 1)
        r = lp[0]
        self.assertEqual((r["system"], r["kind"], r["device_args"]), ("n64", "retroarch", ["--device=1:1", "--device=2:1"]))
        self.assertEqual((r["ports_set"]["players"], r["ports_set"]["source"]), (4, "join"))
        self.assertEqual((r["layout"], r["remap_binds"], r["players_joined"]), ("face_c", 8, "2"))

    def test_a_failed_launch_writes_none(self):
        p, rows = self.plugin({}, raise_exc=True)
        with self.assertRaises(Exception):
            p.handle_post("launch", "id=game_n64_x")
        self.assertEqual([r for r in rows if r["event"] == "launch_ports"], [])


if __name__ == "__main__":
    unittest.main()
