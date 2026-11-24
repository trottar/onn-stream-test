#!/usr/bin/env python3
"""B210 (host): the hub keeps what it read — at the end of every `score` or `letters` mini game, ended or given up on
an unreadable final screen, the pictures its reader ended on (or could not read), what it read, the seats and the
time, off the repo under the title's code; the newest 200 a title; only with PRIVYHUB_PARTY=1. No title; made-up
pictures (B178's); temp dirs removed.

- `Hub`: B114's harness, its `b210` mode (B178's hub scenario as it is, then the played/ folders): two endings 10-6
  (seats 1,2 and 2,1), a tie 14-14, two unreadable finals -> those five among the kept (bench's own endings too), each with its read, its seats, the time and
  1-3 pictures; no run-time name in any read.json.
- `Off`: `_keep_result` with PRIVYHUB_PARTY absent writes nothing; the watch holds no picture without it; a
  winner title keeps nothing; the ring keeps the newest 200.

    python3 -m unittest discover -s tests/b210_keep_result -v
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "companion")]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b123_h7_n64_start", "b157_add_game",
            "b178_score_kind", "b181_every_digit"):
    sys.path.insert(0, str(ROOT / "tests" / sub))


class Hub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_b114 as b114
        import test_b124 as b124
        import line_capture as lc
        root, ids = b114.b99.tree()
        try:
            b124.IDS.clear()
            b124.IDS.update(ids)

            def extra(work, frames):
                lc.frames(frames)
                return {"tools": str(ROOT / "tools"), "b178_dir": str(ROOT / "tests" / "b178_score_kind"),
                        "b181_dir": str(ROOT / "tests" / "b181_every_digit"), "b210_dir": str(HERE)}
            cls.s = b114.run(root, b114.BOTH, ids, "b210", extra=extra, timeout=1200)["steps"]
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_0_no_error(self):
        self.assertNotIn("b178_error", self.s, self.s.get("b178_error"))
        self.assertNotIn("played_error", self.s, self.s.get("played_error"))

    def test_1_every_score_ending_kept(self):
        """The hub part's five (two ended 10-6, a tie, two unreadable) among what was kept; bench's own mini games
        (part 1, through the same actor) are kept too — every one a score ending; one `result_kept` row each."""
        got = [(p["read"]["state"], json.dumps(p["read"]["scores"]), json.dumps(p["read"]["seats"]))
               for p in self.s["played"]]
        for want in [("ended", "[10, 6]", "[1, 2]"), ("ended", "[10, 6]", "[2, 1]"), ("ended", "[14, 14]", "[1, 2]"),
                     ("given_up", "null", "[1, 2]"), ("given_up", "null", "[1, 2]")]:
            self.assertIn(want, got)
            got.remove(want)
        for state, scores, _seats in got:                  # the rest: bench's endings, each read with its numbers
            self.assertEqual(state, "ended")
            self.assertEqual(len(json.loads(scores)), 2)
        self.assertEqual(self.s["result_rows"], ["result_kept"] * len(self.s["played"]))

    def test_2_each_kept_with_its_pictures_read_time_and_code(self):
        for p in self.s["played"]:
            self.assertRegex(p["code"], r"^T\d\d$")
            self.assertTrue(1 <= p["pictures"] <= 3, p)
            self.assertEqual(len(p["read"]["reads"]), p["pictures"])
            self.assertRegex(p["read"]["utc"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
            self.assertEqual(p["read"]["result"], "score")
            if p["read"]["state"] == "given_up":
                self.assertTrue(all(r.get("end_unread") for r in p["read"]["reads"]), p)

    def test_3_no_run_time_name(self):
        for p in self.s["played"]:
            for n in self.s["played_names"]:
                self.assertNotIn(str(n).casefold(), p["text"].casefold())


class Off(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="b210_"))
        (self.tmp / "rules").mkdir()
        (self.tmp / "home" / "T97").mkdir(parents=True)
        (self.tmp / "home" / "T97" / "binding.json").write_text(json.dumps({"game": "madeupgame"}))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def owner(self, party: bool, result: str = "score"):
        import party_minigame as pm
        (self.tmp / "rules" / "madeupgame.party.json").write_text(json.dumps({"players": 2, "result": result}))
        env = {"PRIVYHUB_H7_RULES": str(self.tmp / "rules"), "PRIVYHUB_ADD_GAME_HOME": str(self.tmp / "home")}
        if party:
            env["PRIVYHUB_PARTY"] = "1"
        rows = []
        o = types.SimpleNamespace(environ=env, row=rows.append)
        o._code_of = types.MethodType(pm.PartyMinigames._code_of, o)
        return pm, o, rows

    def mg(self):
        return {"entry": {"game": "madeupgame"}, "state": "ended", "class": "end", "scores": [3, 1], "winner": 1,
                "why": None, "seats": [1, 2]}

    def runner(self):
        from PIL import Image
        return types.SimpleNamespace(end_pictures=lambda: [(Image.new("L", (64, 48), 9), {"class": "end"})] * 3)

    def played(self):
        return sorted((self.tmp / "home" / "T97" / "played").glob("*")) if (self.tmp / "home" / "T97" / "played").is_dir() else []

    def test_1_flag_absent_writes_nothing(self):
        pm, o, rows = self.owner(False)
        pm.PartyMinigames._keep_result(o, self.mg(), self.runner())
        self.assertEqual((self.played(), rows), ([], []))

    def test_2_flag_set_keeps_under_the_code(self):
        pm, o, rows = self.owner(True)
        pm.PartyMinigames._keep_result(o, self.mg(), self.runner())
        self.assertEqual(len(self.played()), 1)
        self.assertEqual(len(list(self.played()[0].glob("f*.jpg"))), 3)
        self.assertEqual(rows, [{"step": "result_kept", "code": "T97", "pictures": 3}])

    def test_3_a_winner_title_keeps_nothing(self):
        pm, o, rows = self.owner(True, "winner")
        pm.PartyMinigames._keep_result(o, self.mg(), self.runner())
        self.assertEqual(self.played(), [])

    def test_4_the_newest_200(self):
        pm, o, rows = self.owner(True)
        base = self.tmp / "home" / "T97" / "played"
        for i in range(205):
            (base / f"20200101T0000{i:03d}Z").mkdir(parents=True)
        pm.PartyMinigames._keep_result(o, self.mg(), self.runner())
        names = sorted(p.name for p in base.iterdir())
        self.assertEqual(len(names), pm.PLAYED_KEEP)
        self.assertEqual(pm.PLAYED_KEEP, 200)
        self.assertNotIn("20200101T0000000Z", names)

    def test_5_the_watch_holds_nothing_without_the_flag(self):
        import h7_minigame as hm
        src = Path(hm.__file__).read_text()
        i = src.index('w.setdefault("_end_seen"')
        self.assertIn('self._environ.get("PRIVYHUB_PARTY") == "1"', src[i - 400:i])
        o = types.SimpleNamespace(_lock=__import__("threading").Lock(), _watch={"game": "x"})
        self.assertEqual(hm.MiniGame.end_pictures(o), [])


if __name__ == "__main__":
    unittest.main()
