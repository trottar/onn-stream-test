#!/usr/bin/env python3
"""B162 (host): the add-a-game tool's solo, safe for many titles — through the real HTTP server on loopback, behind
PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1 (the companion's part); the tool's reads on made-up logs.

`Harness` (B114's harness, its `b162` mode, `b162_scenario.py`): two made-up two-player titles and a four-player one
listed → `solo` of one sets the one-title setting: the list has it alone for two players, the four-player one as it
was; one `minigame_only` row (no name); a non-loopback caller refused (nothing cleared); nothing written to a file by
the setting. A match of the other title → `solo --read`: **the title cell not met, named**; the setting cleared by
`--read` (one row). Three two-player titles → the one under test is the only two-player entry at 20 reads of 20; a
match of it → the title cell met. Cleared by `close` (one row) and by a new layer (a restart). Nothing named in
anything the tool wrote or printed.
`FlagsAndUsers`: B114's `today` mode, each flag absent, HEAD's companion against mine — every route's bytes the same
(`party-minigame-only` included: unknown on both); `today` and `cheat_today` with both flags — the same bytes but the
new route's own answer.
`Unit` (made-up logs, a made-up hub): the title cell; a quick switch listed, not read, and named on the page; three
read → not met; a changed in-game save recorded and close PASS, any other changed file close FAIL; the lines for
`sony`, `xbox`, mixed and no row, two and four players; the setting not taken → REFUSED, no line for the user; the
setting set by solo and cleared by `--read` and by `close`. Temp dirs removed.

    python3 -m unittest discover -s tests/b162_solo_safe -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b157_add_game"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
sys.path.insert(0, str(ROOT / "tools"))
import test_b114 as b114  # noqa: E402  (its harness; its tests are not collected here)
import test_b124 as b124  # noqa: E402
import test_b157 as b157t  # noqa: E402  (its SoloReads fixture, reused)
import made_up_hub  # noqa: E402

HEAD = "58497ab8"
MASK = re.compile(r'(?<![A-Za-z_])\d+\.\d+|\b\d{4,}\b|\d{4}-\d\d-\d\dT[0-9:.]+Z?')
_IDS: dict = {}


def masked(step: dict) -> tuple:
    return step["code"], MASK.sub("<n>", b114.CLOCK.sub("<ms>", step["raw"]))


def extra(work, frames):
    return {"tools": str(ROOT / "tools"), "b162_dir": str(HERE), "kilo": _IDS[("n64", "Alpha Racer (USA)")],
            "bravo": _IDS[("n64", "Bravo Kart (USA) (Rev 1)")]}


class Harness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        try:
            _IDS.clear()
            _IDS.update(ids)
            b124.IDS.clear()
            b124.IDS.update(ids)
            cls.s = b114.run(root, b114.BOTH, ids, "b162", timeout=900, extra=extra)["steps"]
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_0_no_error(self):
        self.assertIsNone(self.s.get("b162_error"), self.s.get("b162_error"))

    def test_1_two_listed_the_one_under_test_alone(self):
        s = self.s
        two = lambda lst: sorted(t for n, t in lst if n == 2)
        four = lambda lst: sorted(t for n, t in lst if n == 4)
        self.assertEqual(s["solo_set"]["rc"], 3, s["solo_set"])
        self.assertEqual(two(s["list_before"]), ["Alpha Racer (USA)", "Juliet Run (USA)"])
        self.assertEqual(two(s["list_set"]), ["Juliet Run (USA)"])
        self.assertEqual(four(s["list_set"]), four(s["list_before"]))
        self.assertEqual(four(s["list_set"]), ["Bravo Kart (USA) (Rev 1)"])
        self.assertTrue(s["files_same_after_set"])                 # memory only: no file written by the setting
        self.assertEqual(len(s["only_rows_set"]), 1)
        self.assertEqual({k: v for k, v in s["only_rows_set"][0].items() if k != "time_unix"},
                         {"step": "minigame_only", "on": True, "players": 2})
        self.assertIn("loopback", s["only_not_loopback"] or "")
        self.assertEqual(s["list_after_refused"], s["list_set"])

    def test_2_a_match_of_the_other_is_not_met(self):
        s = self.s
        self.assertGreaterEqual(s["launch_logs"], 1)                # the harness's launches are logged by the manager
        self.assertEqual(s["read_other"]["rc"], 1)
        self.assertIn("the mini game played was this title", s["read_other_v"]["bad"])
        got = s["read_other_v"]["cells"]["the mini game played was this title"]
        self.assertEqual(got["this title"], 0)
        self.assertGreaterEqual(got["another"], 1)

    def test_3_cleared_by_read(self):
        s = self.s
        self.assertEqual(s["list_after_read"], s["list_before"])
        self.assertEqual([{k: v for k, v in r.items() if k != "time_unix"} for r in s["only_rows_read"]],
                         [{"step": "minigame_only", "on": False}])

    def test_4_three_listed_the_one_under_test_always(self):
        s = self.s
        self.assertEqual(len(s["three_before"]), 3)
        self.assertEqual(s["solo_set3"]["rc"], 3, s["solo_set3"])
        self.assertEqual(s["reads3"], [["Alpha Racer (USA)"]] * 20)
        self.assertNotIn("the mini game played was this title", s["read_this_v"]["bad"])
        got = s["read_this_v"]["cells"]["the mini game played was this title"]
        self.assertEqual(got["another"], 0)
        self.assertGreaterEqual(got["this title"], 1)
        self.assertEqual(s["three_after_read"], s["three_before"])

    def test_5_cleared_by_close_and_by_a_restart(self):
        s = self.s
        self.assertEqual(s["before_close"], ["Juliet Run (USA)"])
        self.assertEqual(s["close"]["rc"], 0, (s["close"], s["close_v"]))
        self.assertEqual(s["after_close"], s["three_before"])
        self.assertEqual([r.get("on") for r in s["only_rows_close"]], [False])
        self.assertEqual(s["before_restart"], ["Juliet Run (USA)"])
        self.assertEqual(s["after_restart"], s["three_before"])

    def test_6_no_name_written_or_printed(self):
        text = self.s["texts"].casefold()
        for n in self.s["names"]:
            self.assertNotIn(str(n).casefold(), text)
        for r in self.s["only_rows_all"]:
            self.assertEqual(set(r) - {"step", "on", "players", "time_unix"}, set(), r)


class FlagsAndUsers(unittest.TestCase):
    """The flags absent: today, byte for byte, HEAD's companion against mine. Both flags set: the users' routes the
    same (the setting is never set by them)."""

    def run_mode(self, mode, env, rev=None):
        code = b114.code_of(rev) if rev else None
        if rev and code is None:
            self.skipTest("git is absent")
        root, ids = b114.b99.tree(code)
        try:
            return b114.run(root, env, ids, mode)["steps"]
        finally:
            shutil.rmtree(root, ignore_errors=True)
            if code is not None:
                shutil.rmtree(code, ignore_errors=True)

    def test_each_flag_absent_is_heads(self):
        F = {**b114.b85.FLAGS, **b114.ADOPTED}
        for env in ({**F, "PRIVYHUB_PARTY": "1"}, {**F, "PRIVYHUB_H7": "1"}, F, {**F, "PRIVYHUB_PARTY": "1", "PRIVYHUB_H7": "0"}):
            base, mine = self.run_mode("today", env, HEAD), self.run_mode("today", env)
            routes = [k for k in base if isinstance(base[k], dict) and "code" in base[k] and "raw" in base[k]]
            self.assertIn("only", routes)
            for k in routes:
                self.assertEqual(masked(mine[k]), masked(base[k]), (sorted(env), k))
            self.assertIn("Unknown Games plugin", base["only"]["body"]["error"])
            self.assertEqual(mine["ports_today"], base["ports_today"])
            self.assertEqual(mine["b139_users_cfg"], base["b139_users_cfg"])

    def test_users_sessions_with_both_flags(self):
        for mode in ("today", "cheat_today"):
            base, mine = self.run_mode(mode, b114.BOTH, HEAD), self.run_mode(mode, b114.BOTH)
            routes = [k for k in base if isinstance(base[k], dict) and "code" in base[k] and "raw" in base[k]]
            self.assertGreaterEqual(len(routes), 9, mode)
            for k in routes:
                if k == "only":                                 # the new route: unknown on HEAD, answered here
                    self.assertIn("Unknown Games plugin", base[k]["body"]["error"])
                    self.assertEqual(mine[k]["body"], {"ok": True, "only": False})
                    continue
                self.assertEqual(masked(mine[k]), masked(base[k]), (mode, k))
            if mode == "today":
                self.assertEqual(mine["ports_today"], base["ports_today"])
                self.assertEqual(mine["b139_users_cfg"], base["b139_users_cfg"])


def _tool(*argv):
    import party_add_game as pag
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pag.main([str(a) for a in argv])
    return rc, buf.getvalue()


class Unit(unittest.TestCase):
    """B157's solo fixture (a made-up binding, logs and hub), with B162's cases."""
    setUp = b157t.SoloReads.setUp
    tearDown = b157t.SoloReads.tearDown
    logs = b157t.SoloReads.logs
    read = b157t.SoloReads.read

    def verdict(self):
        v = json.loads((self.tmp / "ev/T93/solo.json").read_text())
        return v, {c["cell"]: c for c in v["cells"]}

    def launch_logs(self, *games):
        g = self.tmp / "proj/logs/games"
        for p in g.glob("*.log"):                        # the launches only (not the heartbeat's, the encoder's)
            if re.match(r"^\d{8}-\d{6}-", p.name) and not p.name.endswith("-party.log"):
                p.unlink()
        for i, gid in enumerate(games):
            (g / (time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time() + i)) + f"-{gid}.log")).write_text("x\n")

    # --- the title cell
    def test_title_cell(self):
        for games, met, read in ((("madeupgame1",), True, {"this title": 1, "another": 0}),
                                 (("madeupgame2",), False, {"this title": 0, "another": 1}),
                                 (("madeupgame1", "madeupgame2"), False, {"this title": 1, "another": 1}),
                                 ((), False, {"this title": 0, "another": 0})):
            (self.tmp / "home/T93/solo_mark.json").write_text(json.dumps(
                {"party": 0, "heartbeat": 0, "video": 0, "video_bytes": 0, "board_log": None, "board_lines": 0,
                 "since_unix": time.time() - 5}))
            self.logs()
            self.launch_logs(*games)
            rc, text = _tool("solo", "T93", "--read", "--winner", 1)
            v, c = self.verdict()
            self.assertEqual(c["the mini game played was this title"]["met"], met, games)
            self.assertEqual(c["the mini game played was this title"]["read"], read, games)
            self.assertEqual(rc, 0 if met else 1, (games, text))
            self.assertNotIn("madeupgame", json.dumps(v) + text)

    def test_launches_before_the_mark_not_counted(self):
        self.logs()
        self.launch_logs("madeupgame2")
        old = self.tmp / "proj/logs/games" / "20200101-000000-madeupgame2.log"
        next(p for p in (self.tmp / "proj/logs/games").glob("*-madeupgame2.log")).rename(old)
        (self.tmp / "proj/logs/games" / (time.strftime("%Y%m%d-%H%M%S") + "-madeupgame1.log")).write_text("x\n")
        (self.tmp / "home/T93/solo_mark.json").write_text(json.dumps(
            {"party": 0, "heartbeat": 0, "video": 0, "video_bytes": 0, "board_log": None, "board_lines": 0,
             "since_unix": time.time() - 5}))
        rc, _ = _tool("solo", "T93", "--read", "--winner", 1)
        self.assertEqual(rc, 0)

    # --- S as B150 words it
    def switch_logs(self, spec):
        """spec: [(T offset, seconds, window, practice?, heartbeat rows?)] — one switch each."""
        import datetime as dt
        import party_add_game as pag
        g = self.tmp / "proj/logs/games"
        t0 = 1_800_000_000.0
        rows = [{"step": "minigame_launch", "keys_written": True, "time_unix": t0}]
        hb, enc = [], []
        for off, sec, window, practice, beats in spec:
            t = t0 + off
            rows.append({"step": "minigame_stream", "planned": True, "switched": True, "seconds": sec, "time_unix": t,
                         "window": window})
            if practice:
                rows.append({"step": "minigame_playing", "practice": True, "time_unix": t})
            enc.append("encoder argv: x" + (",drawtext=" + pag.BAND if practice else ""))
            for k in range(1, 4 if beats else 0):
                ts = dt.datetime.fromtimestamp(t + k * 0.9, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                hb.append({"received_at_utc": ts, "audio_queue_depth": 3, "audio_underruns": k,
                           "audio_max_arrival_gap_ms": 500})
        rows.append({"step": "minigame_ended", "class": "end_P1", "scores": [1, 0], "winner": 1,
                     "time_unix": t0 + spec[-1][0] + 5})
        (g / "party.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        (g / "native_stream_heartbeat.log").write_text("\n".join(json.dumps(r) for r in hb) + "\n")
        (g / "native_video_alpha.log").write_text("\n".join(enc) + "\n")
        lines = ["cards 1, chose 0", "practice", "load screen again", "start", "scores [1, 0] for seats 1,2"]
        (g / "20990101-000000-party.log").write_text("".join(f"PrivyParty: hub mini game: {x}\n" for x in lines))
        (g / (time.strftime("%Y%m%d-%H%M%S") + "-madeupgame1.log")).write_text("x\n")
        (self.tmp / "home/T93/solo_mark.json").write_text(json.dumps(
            {"party": 0, "heartbeat": 0, "video": 0, "video_bytes": 0, "board_log": None, "board_lines": 0,
             "since_unix": time.time() - 5}))
        return _tool("solo", "T93", "--read", "--winner", 1)

    def test_a_quick_switch_listed_not_read(self):
        # a practice left 2.6 s after its hand-over (the next switch began 1.3 s after the first's T): no heartbeat
        # row there — listed, not read; five read
        rc, text = self.switch_logs([(0, 1.3, "minigame", True, False), (2.6, 1.3, "board", False, True),
                                     (20, 1.3, "minigame", True, True), (40, 1.3, "board", False, True),
                                     (60, 1.3, "minigame", False, True), (90, 1.3, "board", False, True)])
        v, c = self.verdict()
        self.assertEqual(c["switches read for S (the next starts 4 s or more after)"]["read"], [5, 1])
        self.assertTrue(c["switches read for S (the next starts 4 s or more after)"]["met"])
        self.assertTrue(c["S: sound within 4 s of each switch, underruns rising <= 20 a row"]["met"])
        self.assertTrue(c["audio_max_arrival_gap_ms at each switch"]["met"])
        self.assertEqual(rc, 0, text + (self.tmp / "ev/T93/solo.md").read_text())
        page = (self.tmp / "ev/T93/solo.md").read_text()
        self.assertIn("Listed, not read", page)
        self.assertIn("switch 1 (to the minigame, 1.3 s; the next began 1.3 s after)", page)

    def test_three_read_not_met(self):
        rc, _ = self.switch_logs([(0, 1.3, "minigame", True, False), (2.6, 1.3, "board", False, True),
                                  (30, 1.3, "minigame", False, True), (60, 1.3, "board", False, True)])
        v, c = self.verdict()
        self.assertEqual(c["switches read for S (the next starts 4 s or more after)"]["read"], [3, 1])
        self.assertFalse(c["switches read for S (the next starts 4 s or more after)"]["met"])
        self.assertEqual(rc, 1)

    # --- the lines
    def heartbeat(self, classes):
        rows = [{"received_at_utc": "2026-01-01T00:00:00.000Z", "audio_queue_depth": 1}]
        if classes is not None:
            rows.append({"received_at_utc": "2026-01-01T00:00:02.000Z", "pad_slots": [
                {"slot": i, "pad": f"{i:06x}", "class": c} for i, c in enumerate(classes)]})
            rows.append({"received_at_utc": "2026-01-01T00:00:04.000Z", "pad_slots": []})   # pads gone: the last with pads counts
        (self.tmp / "proj/logs/games/native_stream_heartbeat.log").write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def test_lines_by_pad_class(self):
        import party_add_game as pag
        for classes, words, must, must_not in ((["sony", "sony"], "playstation", ["△", "✕", "Select button (Share)"], ["Y ", "View"]),
                                               (["xbox", "generic"], "xbox", ["press Y", "press A", "View button (Back)"], ["△", "✕"]),
                                               (["sony", "xbox"], "both", ["△ (Y on an Xbox pad)", "✕ (A on an Xbox pad)", "View on an Xbox pad"], []),
                                               (None, "playstation", ["△", "✕"], ["View"])):
            self.heartbeat(classes)
            self.assertEqual(pag.pad_words(pag.pad_classes()), words, classes)
            rc, text = _tool("solo", "T93")
            self.assertEqual(rc, 3, text)
            for w in must:
                self.assertIn(w, text, classes)
            for w in must_not:
                self.assertNotIn(w, text, classes)
            self.assertIn("you alone with two pads, or two of you", text)
            self.assertIn("at least ten seconds", text)
            self.assertIn("if two cards show, stop and tell me", text)
        four = pag.solo_lines({"players": 4}, "playstation")
        self.assertIn("four people, or you with four pads", four[0])
        self.assertIn("P3 or P4", four[2])

    # --- the setting
    def test_setting_set_then_cleared_by_read_and_close(self):
        rc, _ = _tool("solo", "T93")
        self.assertEqual(rc, 3)
        self.assertEqual(self.hub.only, {"game": "madeupgame1", "players": 2})
        self.read()
        self.assertIsNone(self.hub.only)
        self.assertIn("POST party-minigame-only clear", self.hub.calls)
        _tool("solo", "T93")
        self.assertIsNotNone(self.hub.only)
        self.close_ready()
        _tool("close", "T93")
        self.assertIsNone(self.hub.only)

    def test_setting_not_taken_nothing_asked(self):
        self.hub.take_only = False                              # a companion without the route
        rc, text = _tool("solo", "T93")
        self.assertEqual(rc, 2, text)
        self.assertIn("the one-title setting was not taken", text)
        self.assertNotIn("YOU, now", text)
        self.assertFalse((self.tmp / "home/T93/solo_mark.json").exists())

    # --- close: the in-game saves recorded, never a cell
    def close_ready(self, cheat=False):
        import party_add_game as pag
        ctl = self.tmp / "systemctl"
        ctl.write_text("#!/bin/sh\nif [ \"$1\" = \"--user\" ] && [ \"$2\" = \"list-units\" ]; then\n"
                       "  echo 'privyhub-companion.service loaded active running x'\n"
                       "  echo 'privyhub-diag.service loaded active running x'\nfi\nexit 0\n")
        ctl.chmod(0o755)
        os.environ["PRIVYHUB_ADD_GAME_SYSTEMCTL"] = str(ctl)
        b = json.loads((self.tmp / "home/T93/binding.json").read_text())
        for p in (self.tmp / "dropins").glob("*.conf"):
            if p.name in pag.FLAG_FILES:
                p.unlink()
        b["found_lines"] = pag.digest(pag._companion_lines())
        if cheat:
            b["cheat"] = {"source_index": 0, "enabled_cheat_indexes": [1], "profile_id": "AB" * 32}
        (self.tmp / "home/T93/binding.json").write_text(json.dumps(b))
        return b

    def test_close_records_in_game_saves(self):
        import party_add_game as pag
        b = self.close_ready(cheat=True)
        proj = self.tmp / "proj/data/games/retroarch"
        prof = proj / "cheat_profiles/madeupgame1" / ("AB" * 32)
        (prof / "saves/Beetle PSX HW").mkdir(parents=True)
        (prof / "states/Beetle PSX HW").mkdir(parents=True)
        (prof / "saves/Beetle PSX HW/Made Up (USA).srm").write_text("in-game save 1")
        (prof / "states/Beetle PSX HW/Made Up (USA).state1").write_text("the user's slot 1")
        (proj / "saves/Beetle PSX HW").mkdir(parents=True)
        (proj / "saves/Beetle PSX HW/Made Up (USA).srm").write_text("own in-game save")
        (proj / "saves/Beetle PSX HW/Another (USA).srm").write_text("another title's save")
        (self.tmp / "home/T93/files_before.json").write_text(json.dumps(pag.files_digest(b)))
        pag.saves_before("T93", b, again=True)
        (prof / "saves/Beetle PSX HW/Made Up (USA).srm").write_text("in-game save 1, after a match")
        (proj / "saves/Beetle PSX HW/Made Up (USA).srm").write_text("own in-game save, after a match")
        rc, text = _tool("close", "T93")
        v = json.loads((self.tmp / "ev/T93/close.json").read_text())
        self.assertEqual(rc, 0, text + json.dumps(v))
        self.assertEqual(v["recorded"]["in_game_saves"], [{"save": "under the setup 1", "is": "changed"},
                                                          {"save": "own 1", "is": "changed"}])
        self.assertNotIn("in-game", " ".join(c["cell"] for c in v["cells"]))      # never a cell
        page = (self.tmp / "ev/T93/close.md").read_text()
        self.assertIn("under the setup 1: changed; own 1: changed", page)
        self.assertNotIn("Made Up", page + json.dumps(v) + text)
        (prof / "states/Beetle PSX HW/Made Up (USA).state1").write_text("the user's slot 1, changed")
        rc, text = _tool("close", "T93")
        v = json.loads((self.tmp / "ev/T93/close.json").read_text())
        self.assertEqual(rc, 1, text)
        self.assertIn("every file = bench's before", [c["cell"] for c in v["cells"] if not c["met"]])


if __name__ == "__main__":
    unittest.main()
