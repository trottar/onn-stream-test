#!/usr/bin/env python3
"""B94 + B96 + B97 (host): the win-rule search on synthetic fixtures (no game).

States are made on `fixtures.py`'s PS-X EXE and SNES ROM — SNES with B93's own `--make-state --write`, one session
per state at different moments; PS1 in ONE paused session (written, saved, written, saved: the core's own time-varying
bytes the same in every state — made at different moments they sometimes fit a template by chance, see B94's record): a planted per-player
block (a round counter and a level), decoys (a block where P1 is larger in every state; a block that fits begin + a
P1-won end but not a P2-won end), and noise (the SNES program's frame counter and xorshift buffer; on PS1, whose fixture
code does not run headless, random bytes written per state). B96: five and six states (begin; two ends per winner with
different planted details; a second begin), a mirror of the planted block, decoys that fit three states and fail a
fourth, a single-field decoy, a per-player score pair; B97: made-up cheat lists (`fixtures.cht`) as hints, and (b2).
The search reads each state paused, 3 loads, through
`tools/h7_rule_search.py`'s own reader; RetroArch headless (B61's form). Skipped without RetroArch or a display.
Temp dirs removed at exit.

    python3 -m unittest discover -s tests/h7_rule_search -v
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "h7_minigame_proof"))
import fixtures as F  # noqa: E402
import h7_minigame_proof as proof  # noqa: E402
import h7_rule_search as search  # noqa: E402
from test_h7_proof import display_env  # noqa: E402

TOOL = ROOT / "tools" / "h7_rule_search.py"
PROOF = ROOT / "tools" / "h7_minigame_proof.py"
ALL = 10 ** 6

# the planted facts per state; "d_*" the decoys (2 players only): d_counter / d_level fit begin + P1 and fail P2 (B94);
# t_counter / t_level fit begin + P1 + P2 and fail P1b; c_single 255 / 0 / 1 reads P2 at P1b; score: no template fits
TWO = {"begin": {"rounds": (0, 0), "level": (120, 120), "d_counter": (3, 3), "d_level": (100, 100),
                 "t_counter": (0, 0), "t_level": (90, 90), "c_single": 255, "score": (0, 0)},
       "P1": {"rounds": (2, 1), "level": (37, 0), "d_counter": (7, 2), "d_level": (40, 0),
              "t_counter": (3, 1), "t_level": (20, 0), "c_single": 0, "score": (0x02FF, 0x02F0)},
       "P2": {"rounds": (1, 2), "level": (0, 55), "d_counter": (6, 4), "d_level": (30, 0),
              "t_counter": (1, 3), "t_level": (0, 20), "c_single": 1, "score": (0x0310, 0x0320)},
       "P1b": {"rounds": (2, 0), "level": (80, 0), "d_counter": (5, 1), "d_level": (50, 0),
               "t_counter": (1, 3), "t_level": (0, 20), "c_single": 1, "score": (0x0480, 0x0470)},
       "P2b": {"rounds": (0, 2), "level": (25, 90), "d_counter": (2, 5), "d_level": (0, 60),
               "t_counter": (0, 3), "t_level": (0, 30), "c_single": 1, "score": (0x0510, 0x05A0)},
       "begin2": {"rounds": (0, 0), "level": (120, 120), "d_counter": (3, 3), "d_level": (100, 100),
                  "t_counter": (0, 0), "t_level": (90, 90), "c_single": 255, "score": (0, 0)}}
FOUR = {"begin": {"rounds": (0, 0, 0, 0), "level": (120, 120, 120, 120)},
        "P3": {"rounds": (1, 0, 2, 1), "level": (0, 0, 60, 0)},
        "P1": {"rounds": (2, 1, 0, 0), "level": (45, 0, 0, 0)},
        "P3b": {"rounds": (0, 1, 2, 0), "level": (0, 0, 40, 0)},
        "P1b": {"rounds": (2, 0, 1, 1), "level": (90, 0, 0, 0)},
        "P4": {"rounds": (0, 1, 1, 2), "level": (0, 0, 0, 70)}}


def u16(v: int) -> str:
    return v.to_bytes(2, "little").hex()


def writes(plan: dict, facts: dict, seed: int, noise: bool) -> list[str]:
    w = []
    for k, (r, lv) in enumerate(zip(facts["rounds"], facts["level"])):
        for at in (plan["block"], plan["block"] + plan["mirror"]):           # B96: the block and its mirror
            base = at + k * plan["stride"]
            w += [f"{base + plan['rounds']:#x}={u16(r)}", f"{base + plan['level']:#x}={u16(lv)}"]
    if "d_counter" in facts:
        for k, v in enumerate((9, 4)):                                   # P1 larger in every state
            w.append(f"{plan['decoy_always_p1'] + k * plan['decoy_stride']:#x}={u16(v)}")
        for name, at in (("d", plan["decoy_two_states"]), ("t", plan["decoy_three"])):
            for k, (c, lv) in enumerate(zip(facts[f"{name}_counter"], facts[f"{name}_level"])):
                base = at + k * plan["decoy_stride"]
                w += [f"{base:#x}={u16(c)}", f"{base + 4:#x}={u16(lv)}"]
        w.append(f"{plan['c_decoy']:#x}={facts['c_single']:02x}")
        for k, v in enumerate(facts["score"]):
            w.append(f"{plan['score'] + k * plan['score_stride']:#x}={u16(v)}")
    if noise:                                                            # PS1: the fixture's code does not run headless
        rnd = random.Random(seed)
        for lo, hi in plan["noise"]:
            w.append(f"{lo:#x}={bytes(rnd.randrange(256) for _ in range(hi - lo)).hex()}")
    return w


def label_of(name: str) -> tuple[str, str | None]:
    return ("begin", None) if name.startswith("begin") else ("end", name[:2])


class Base(unittest.TestCase):
    system = "ps1"
    plan = F.PS1
    sets = TWO
    noise = True

    @classmethod
    def setUpClass(cls):
        cls.env = display_env()
        cls.tmp = Path(tempfile.mkdtemp(prefix="h7_search_test_"))
        cls.rom = cls.tmp / ("Made Up Fight.exe" if cls.system == "ps1" else "Made Up Fight.sfc")
        cls.rom.write_bytes(F.psx_exe() if cls.system == "ps1" else F.snes())
        cls.files, cls.read = {}, {}
        if cls.noise:     # PS1: every state from one paused session (the core's own time-varying bytes the same in all)
            old_env = dict(os.environ)
            os.environ.update(cls.env)
            s = proof.Session(cls.rom, cls.system, cls.tmp / "make")
            try:
                s.wait_playing()
                time.sleep(0.5)
                s.pause()
                for n, (name, facts) in enumerate(cls.sets.items()):
                    for w in writes(cls.plan, facts, n + 1, cls.noise):
                        addr, data = w.split("=")
                        s.send(f"WRITE_CORE_RAM {int(addr, 0):x} " + " ".join(f"{b:02x}" for b in bytes.fromhex(data)))
                        time.sleep(0.05)
                    out = cls.tmp / f"{name}.state"
                    s.save_state(out)
                    cls.files[name] = out
            finally:
                s.close()
                os.environ.clear(); os.environ.update(old_env)
        for n, (name, facts) in enumerate(cls.sets.items() if not cls.noise else ()):
            out = cls.tmp / f"{name}.state"
            args = [sys.executable, "-I", "-B", str(PROOF), "--content", str(cls.rom), "--system", cls.system,
                    "--make-state", str(out), "--after", str(0.5 + 0.4 * n)]   # a different moment per state
            for x in writes(cls.plan, facts, n + 1, cls.noise):
                args += ["--write", x]
            r = subprocess.run(args, capture_output=True, text=True, env=cls.env, timeout=120)
            assert json.loads(r.stdout.strip().splitlines()[-1]).get("state_written"), r.stdout + r.stderr[-800:]
            cls.files[name] = out
        old = dict(os.environ)
        os.environ.update(cls.env)
        try:
            for name, path in cls.files.items():
                mem, stable = search.read_state(cls.rom, cls.system, path, 3)
                cls.read[name] = (mem, stable)
        finally:
            os.environ.clear(); os.environ.update(old)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def states(self, *names) -> list[dict]:
        return [{"label": label_of(n)[0], "winner": label_of(n)[1], "mem": self.read[n][0], "stable": self.read[n][1]}
                for n in names]

    def planted(self, players: int, field: str = "rounds") -> list[str]:
        return [hex(self.plan["block"] + k * self.plan["stride"] + self.plan[field]) for k in range(players)]

    def full(self, *names, players: int = 2, **kw) -> dict:
        search.SHOWN, old = ALL, search.SHOWN
        try:
            return search.search(self.states(*names), players, **kw)
        finally:
            search.SHOWN = old

    def hints(self) -> list[dict]:                                      # B97: the made-up cheat list's hints
        path = self.tmp / f"{self.system}.cht"
        path.write_text(F.cht(self.system))
        return search.load_hints(path, self.system)[0]

    @staticmethod
    def addrs(rules: list[dict]) -> list[list[str]]:
        return [[p["address"] for p in r["rule"]["players"]] for r in rules]


@unittest.skipUnless(proof.APP.is_file() and display_env(), "RetroArch or a display is absent")
class PS1TwoPlayers(Base):
    def test_loads_are_stable(self):
        for name, (_mem, stable) in self.read.items():
            self.assertTrue(bool(stable.all()), name)                   # paused loads: every byte the same

    def test_three_states_are_weak_and_the_planted_family_passes(self):
        out = self.full("begin", "P1", "P2")
        a = out["templates"]["a"]
        self.assertFalse(out["decided"])
        self.assertEqual(out["evidence"], "weak")
        self.assertEqual(a["evidence"]["level"], "weak")
        self.assertEqual((a["evidence"]["folds_run"], a["evidence"]["folds_skipped"]), (0, 2))
        self.assertEqual(a["evidence"]["would_make_strong"], "one more 'end' won by P1 and one more 'end' won by P2")
        self.assertEqual(out["not_decided"]["would_make_strong"], a["evidence"]["would_make_strong"])
        self.assertIn(self.planted(2), self.addrs(a["passing"]))          # the planted family among those passing
        self.assertIn(self.planted(2, "level"), self.addrs(out["templates"]["b"]["passing"]))
        self.assertNotIn("rule", out)
        decoy = [hex(self.plan["decoy_three"] + k * self.plan["decoy_stride"]) for k in range(2)]
        self.assertEqual(self.addrs(a["passing"])[0], decoy)              # by the order alone, the decoy ranks first

    def test_three_states_keep_b94s_content(self):
        out = self.full("begin", "P1", "P2")                            # B94: the planted rule among the candidates
        found = [r for f in out["templates"]["a"]["families"] for r in [f["rule"]]]
        self.assertIn(self.planted(2), self.addrs([{"rule": r} for r in found]))
        self.assertGreaterEqual(out["templates"]["a"]["count"], out["templates"]["a"]["families_found"])

    def test_five_states_are_strong_the_planted_family_the_answer(self):
        out = self.full("begin", "P1", "P2", "P1b", "P2b")
        a = out["templates"]["a"]
        self.assertTrue(out["decided"], out.get("not_decided"))
        self.assertEqual((out["evidence"], out["template"]), ("strong", "a"))
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(2))
        self.assertEqual((a["evidence"]["level"], a["evidence"]["folds_run"], a["evidence"]["folds_skipped"]),
                         ("strong", 4, 0))
        self.assertIsNone(a["evidence"]["would_make_strong"])
        top = a["passing"][0]
        mirror = hex(self.plan["block"] + self.plan["mirror"] + self.plan["rounds"])
        self.assertIn(f"2@{mirror}", top["member_reads"])                 # the mirror in the planted family…
        self.assertGreaterEqual(top["members"], 2)
        self.assertNotIn([mirror, hex(int(mirror, 16) + self.plan["stride"])], self.addrs(a["families"]))  # …counted once
        for t in ("a", "b"):                                               # the decoys not on all five states…
            addrs = [int(x, 16) for r in self.addrs(out["templates"][t]["families"]) for x in r]
            for d in (self.plan["decoy_three"], self.plan["decoy_two_states"], self.plan["decoy_always_p1"]):
                self.assertFalse(any(d <= x < d + 2 * self.plan["decoy_stride"] for x in addrs), (t, addrs))
        fold = next(r for r in a["folds"] if r["held_out"] == 3)          # …and failing the fold that holds out P1b
        decoy = [hex(self.plan["decoy_three"] + k * self.plan["decoy_stride"]) for k in range(2)]
        self.assertIn(decoy, [[p["address"] for p in r["players"]] for r in fold["did_not_name_first"]])
        lvl = next(r for r in out["templates"]["b"]["folds"] if r["held_out"] == 3)
        self.assertIn([hex(int(x, 16) + 4) for x in decoy], [[p["address"] for p in r["players"]]
                                                              for r in lvl["did_not_name_first"]])

    def test_six_states_with_a_second_begin(self):
        out = self.full("begin", "P1", "P2", "P1b", "P2b", "begin2")
        self.assertTrue(out["decided"])
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(2))

    def test_a_fold_without_another_example_is_skipped_and_counted(self):
        out = self.full("begin", "P1", "P1b", "P2")
        a = out["templates"]["a"]
        self.assertEqual((a["evidence"]["folds_run"], a["evidence"]["folds_skipped"]), (2, 1))
        skipped = [r for r in a["folds"] if r["skipped"]]
        self.assertEqual((skipped[0]["winner"], skipped[0]["why"]), ("P2", "no other 'end' won by P2"))
        self.assertEqual(a["evidence"]["level"], "weak")
        self.assertIn("P2", a["evidence"]["words"])
        self.assertEqual(a["evidence"]["would_make_strong"], "one more 'end' won by P2")
        self.assertFalse(out["decided"])

    def test_one_winner_only_is_never_strong(self):                    # addendum 1
        out = self.full("begin", "P1", "P1b")
        self.assertFalse(out["decided"])
        self.assertNotEqual(out["templates"]["a"]["evidence"]["level"], "strong")
        self.assertIn("won by P2", out["not_decided"]["would_make_strong"])

    def test_template_c_tightened_counts_before_and_after(self):
        old = search.C_PLAYER_VALUES
        try:
            search.C_PLAYER_VALUES = False
            before = self.full("begin", "P1", "P2")["templates"]["c"]["count"]
        finally:
            search.C_PLAYER_VALUES = old
        out = self.full("begin", "P1", "P2")
        after = out["templates"]["c"]["count"]
        print(f"\nB96 (c) on the PS1 fixture, begin + P1 + P2: {before} candidates before, {after} after", file=sys.stderr)
        self.assertLess(after, before)
        c = [f["rule"] for f in out["templates"]["c"]["families"]]
        hit = [r for r in c if r["address"] == hex(self.plan["c_decoy"])]
        self.assertTrue(hit)                                               # the single-field decoy fits three states
        self.assertEqual(hit[0]["values"], {"P1": 0, "P2": 1})
        self.assertEqual(hit[0]["none_value"], 255)
        five = self.full("begin", "P1", "P2", "P1b", "P2b")
        fold = next(r for r in five["templates"]["c"]["folds"] if r["held_out"] == 3)
        self.assertIn(hex(self.plan["c_decoy"]), [r["address"] for r in fold["did_not_name_first"]])
        self.assertNotIn(hex(self.plan["c_decoy"]), [f["rule"]["address"] for f in five["templates"]["c"]["families"]])

    def test_begin_and_one_end_is_not_decided_and_includes_the_planted_rule(self):
        out = search.search(self.states("begin", "P1"), 2)
        self.assertFalse(out["decided"])
        self.assertGreater(out["not_decided"]["counts"]["a"], 1)
        self.assertGreater(out["not_decided"]["counts"]["b"], 1)
        self.assertIsNone(out["not_decided"]["counts"]["c"])              # not testable with one winner
        self.assertIn("P2", out["not_decided"]["would_split"])
        self.assertNotIn("rule", out)
        full = self.full("begin", "P1")
        found = self.addrs(full["templates"]["a"]["families"])
        self.assertIn(self.planted(2), found)
        decoy = [hex(self.plan["decoy_two_states"] + k * self.plan["decoy_stride"]) for k in range(2)]
        self.assertIn(decoy, found)                                       # the decoy fits two states…

    def test_a_decoy_never_ranks_above_the_planted_rule_once_p2_is_in(self):
        out = self.full("begin", "P1", "P2")
        for t in ("a", "b"):
            addrs = [int(x, 16) for r in self.addrs(out["templates"][t]["families"]) for x in r]
            for d in (self.plan["decoy_two_states"], self.plan["decoy_always_p1"]):
                self.assertFalse(any(d <= a < d + 2 * self.plan["decoy_stride"] for a in addrs), (t, addrs))  # …not three

    def test_hints_rank_the_planted_family_first_with_three_states(self):
        decoy = [hex(self.plan["decoy_three"] + k * self.plan["decoy_stride"]) for k in range(2)]
        plain = self.full("begin", "P1", "P2")
        self.assertEqual(self.addrs(plain["templates"]["a"]["passing"])[0], decoy)           # by the order alone
        out = self.full("begin", "P1", "P2", hints=self.hints())
        self.assertEqual(self.addrs(out["templates"]["a"]["passing"])[0], self.planted(2))   # hinted: first
        self.assertTrue(out["templates"]["a"]["passing"][0]["hinted"])
        self.assertEqual(self.addrs(out["templates"]["b"]["passing"])[0], self.planted(2, "level"))
        self.assertFalse(out["decided"])                                                     # still weak

    def test_the_decoy_hint_fails_and_the_score_pair_is_tested_directly(self):
        dw = [hex(self.plan["decoy_two_states"] + k * self.plan["decoy_stride"]) for k in range(2)]
        sc = [hex(self.plan["score"] + k * self.plan["score_stride"]) for k in range(2)]
        out = self.full("begin", "P1", "P2", hints=self.hints())
        rows = {tuple(p["address"] for p in s["rule"]["players"]): s for s in out["hinted_sets"]["sets"]}
        self.assertFalse(rows[tuple(dw)]["holds"])
        self.assertIn(2, rows[tuple(dw)]["failing_states"])                                  # P2's end
        self.assertNotIn(dw, [a for t in out["templates"].values() for a in self.addrs(t["passing"])])
        five = self.full("begin", "P1", "P2", "P1b", "P2b", hints=self.hints())
        rows = {tuple(p["address"] for p in s["rule"]["players"]): s for s in five["hinted_sets"]["sets"]}
        self.assertTrue(rows[tuple(sc)]["holds"])
        self.assertEqual(rows[tuple(sc)]["found_by"], [])                                    # no template found it
        self.assertEqual(rows[tuple(sc)]["values_per_state"][1], [0x02FF, 0x02F0])
        self.assertTrue(rows[tuple(self.planted(2))]["holds"])
        self.assertEqual(rows[tuple(self.planted(2))]["found_by"], ["a"])
        self.assertTrue(five["decided"])
        self.assertEqual((five["template"], [p["address"] for p in five["rule"]["players"]]), ("a", self.planted(2)))

    def test_b2_finds_the_level_where_the_loser_is_above_0(self):
        out = self.full("begin", "P1", "P2", "P1b", "P2b")                 # P2b: the loser at 25
        level = self.planted(2, "level")
        self.assertIn(level, self.addrs(out["templates"]["b2"]["passing"]))
        self.assertNotIn(level, self.addrs(out["templates"]["b"]["families"]))
        self.assertEqual(out["templates"]["b2"]["evidence"]["level"], "strong")
        self.assertEqual(out["template"], "a")

    def test_b98_accept_loose_is_b97_byte_for_byte_and_the_ranking_pick(self):
        import test_b98_acceptance as b98
        old = b98.b97_search()
        if old is None:
            self.skipTest("git or B97's commit is absent")
        hints = self.hints()
        cases = [(self.states(*names), 2, h) for names in (("begin", "P1", "P2"), ("begin", "P1", "P2", "P1b", "P2b"))
                 for h in (None, hints)]
        b98.loose_equal(self, old, cases)
        out = search.search(self.states("begin", "P1", "P2", "P1b", "P2b"), 2)          # B98's own answer
        self.assertTrue(out["accepted"])
        self.assertEqual(out["ranking_pick"], out["templates"][out["template"]]["passing_count"] > 1)

    def test_the_cli_and_its_time_on_2_mib(self):
        listed = self.tmp / "states.json"
        names = ("begin", "P1", "P2", "P1b", "P2b")
        listed.write_text(json.dumps([{"state": str(self.files[n]), "label": label_of(n)[0], "winner": label_of(n)[1]}
                                      for n in names]))
        cht = self.tmp / "cli.cht"
        cht.write_text(F.cht("ps1"))
        r = subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--content", str(self.rom), "--system", "ps1",
                            "--states", str(listed), "--time", "--hints", str(cht)], capture_output=True, text=True,
                           env=self.env, timeout=900)
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertTrue(out["decided"], out)
        self.assertEqual(out["evidence"], "strong")
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(2))
        self.assertEqual(out["hints"]["read"], 11)                                          # B97: --hints
        self.assertTrue(out["templates"]["a"]["passing"][0]["hinted"])
        self.assertNotIn("Zorvak", r.stdout)
        print(f"\nB96 time, PS1 2 MiB, 5 states x 3 loads: {out['seconds']}", file=sys.stderr)
        self.assertLess(out["seconds"]["search"], 60)

    def test_a_state_that_fails_to_load_is_an_error_never_a_rule(self):
        import zlib
        data = os.urandom(10000)
        comp = zlib.compress(data)
        cases = {"corrupt": b"#RZIPv\x01#" + os.urandom(4000),                  # read as 0 bytes
                 "refused": b"#RZIPv\x01#" + (131072).to_bytes(4, "little") + len(data).to_bytes(8, "little")
                            + len(comp).to_bytes(4, "little") + comp}           # read, then refused by the core
        for name, raw in cases.items():
            bad = self.tmp / f"{name}.state"
            bad.write_bytes(raw)
            listed = self.tmp / f"{name}.json"
            listed.write_text(json.dumps([{"state": str(bad), "label": "begin", "winner": None},
                                          {"state": str(self.files["P1"]), "label": "end", "winner": "P1"}]))
            r = subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--content", str(self.rom), "--system", "ps1",
                                "--states", str(listed), "--loads", "1"], capture_output=True, text=True, env=self.env,
                               timeout=300)
            out = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertEqual(r.returncode, 2, name)
            self.assertIn("error", out, name)
            self.assertNotIn("rule", out, name)
            if name == "refused":
                self.assertIn("failed to load", out["error"])


@unittest.skipUnless(proof.APP.is_file() and display_env(), "RetroArch or a display is absent")
class PS1FourPlayers(Base):
    sets = FOUR

    def test_the_four_player_set(self):
        out = self.full("begin", "P3", "P1", players=4)                  # each winner once: weak
        self.assertFalse(out["decided"])
        self.assertEqual(out["templates"]["a"]["evidence"]["level"], "weak")
        self.assertEqual(self.addrs(out["templates"]["a"]["passing"])[0], self.planted(4))   # ranked first
        self.assertIn(self.planted(4, "level"), self.addrs(out["templates"]["b"]["passing"]))
        self.assertEqual(out["templates"]["a"]["evidence"]["would_make_strong"],
                         "one more 'end' won by P1 and one more 'end' won by P3")
        out = self.full("begin", "P3", "P1", "P3b", "P1b", players=4)    # two ends per winner seen: strong
        self.assertTrue(out["decided"], out.get("not_decided"))
        self.assertEqual(out["template"], "a")
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(4))
        out = self.full("begin", "P3", "P1", "P3b", "P1b", "P4", players=4)   # a winner seen once again: weak
        self.assertFalse(out["decided"])
        self.assertEqual(out["templates"]["a"]["evidence"]["would_make_strong"], "one more 'end' won by P4")
        self.assertEqual(out["templates"]["a"]["evidence"]["folds_skipped"], 1)


@unittest.skipUnless(proof.APP.is_file() and display_env(), "RetroArch or a display is absent")
class SnesTwoPlayers(Base):
    system = "snes"
    plan = F.SNES
    noise = False                                    # the program's own frame counter and buffer

    def test_the_noise_runs_and_five_states_decide_the_planted_rule(self):
        b, e = self.read["begin"][0], self.read["P1"][0]
        self.assertNotEqual(b[0x1000:0x1400], e[0x1000:0x1400])            # the buffer differs between states
        three = self.full("begin", "P1", "P2")
        self.assertEqual(three["evidence"], "weak")
        self.assertIn(self.planted(2), self.addrs(three["templates"]["a"]["passing"]))
        out = self.full("begin", "P1", "P2", "P1b", "P2b", "begin2")
        self.assertTrue(out["decided"], out.get("not_decided"))
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(2))
        mirror = hex(self.plan["block"] + self.plan["mirror"] + self.plan["rounds"])
        self.assertIn(f"2@{mirror}", out["templates"]["a"]["passing"][0]["member_reads"])
        hinted = self.full("begin", "P1", "P2", hints=self.hints())                    # B97: 1-byte SNES hints
        self.assertEqual(self.addrs(hinted["templates"]["a"]["passing"])[0], self.planted(2))
        self.assertTrue(hinted["templates"]["a"]["passing"][0]["hinted"])


class NoEmulator(unittest.TestCase):
    def mem(self, pairs: dict[int, int], size: int = 4096) -> bytes:
        m = bytearray(size)
        for a, v in pairs.items():
            m[a] = v
        return bytes(m)

    def st(self, label, winner, pairs, unstable=(), size=4096):
        s = np.ones(size, dtype=bool)
        for a in unstable:
            s[a] = False
        return {"label": label, "winner": winner, "mem": self.mem(pairs, size), "stable": s}

    def test_unstable_addresses_are_dropped(self):
        planted = {0x100: 0, 0x110: 0}
        p1 = {0x100: 2, 0x110: 1}
        p2 = {0x100: 1, 0x110: 2}
        decoy = {0x200: 5, 0x204: 5}, {0x200: 6, 0x204: 4}, {0x200: 4, 0x204: 6}   # fits all three, but unstable
        states = [self.st("begin", None, {**planted, **decoy[0]}, unstable=[0x200]),
                  self.st("end", "P1", {**p1, **decoy[1]}), self.st("end", "P2", {**p2, **decoy[2]})]
        out = search.search(states, 2)
        addrs = [[p["address"] for p in c["rule"]["players"]] for c in out["templates"]["a"]["families"]]
        self.assertEqual(addrs, [["0x100", "0x110"]])
        self.assertEqual(out["evidence"], "weak")
        self.assertGreater(out["unstable_bytes"], 0)
        states[0]["stable"][0x200] = True                                   # stable → it fits as well: two
        out = search.search(states, 2)
        self.assertEqual(out["templates"]["a"]["count"], 2)

    def five(self, extra: dict[str, dict[int, int]]) -> list[dict]:
        facts = {"begin": (0, 0), "P1": (2, 1), "P2": (1, 2), "P1b": (2, 0), "P2b": (0, 2)}
        out = []
        for n, (x, y) in facts.items():
            pairs = {0x100: x, 0x110: y, **extra.get(n, {})}
            out.append(self.st(*(("begin", None) if n == "begin" else ("end", n[:2])), pairs))
        return out

    def test_the_window_joins_a_copy_at_0x100_and_not_at_0x101(self):
        facts = {"begin": (0, 0), "P1": (2, 1), "P2": (1, 2), "P1b": (2, 0), "P2b": (0, 2)}
        for off, joined in ((search.WINDOW, True), (search.WINDOW + 1, False)):
            extra = {n: {0x100 + off: x, 0x110 + off: y} for n, (x, y) in facts.items()}
            out = search.search(self.five(extra), 2)
            fams = out["templates"]["a"]["families"]
            first = fams[0]
            self.assertEqual([p["address"] for p in first["rule"]["players"]], ["0x100", "0x110"])  # the lowest: rule
            copy = f"2@{0x100 + off:#x}"
            own = [f for f in fams if f["rule"]["players"][0]["address"] == hex(0x100 + off)]
            if joined:
                self.assertIn(copy, first["member_reads"])
                self.assertEqual(first["members"], 2)
                self.assertEqual(own, [])
            else:
                self.assertNotIn(copy, first["member_reads"])
                self.assertEqual(first["members"], 1)
                self.assertEqual(len(own), 1)                                         # its own family

    def test_a_copy_with_other_values_is_another_family(self):
        facts = {"begin": (0, 0), "P1": (3, 1), "P2": (1, 2), "P1b": (2, 0), "P2b": (0, 2)}   # P1's end differs
        extra = {n: {0x140: x, 0x150: y} for n, (x, y) in facts.items()}
        fams = search.search(self.five(extra), 2)["templates"]["a"]["families"]
        self.assertNotIn("2@0x140", fams[0]["member_reads"])
        self.assertTrue([f for f in fams if f["rule"]["players"][0]["address"] == "0x140"])

    def test_overlapping_reads_are_one_family(self):
        out = search.search(self.five({}), 2)
        fam = out["templates"]["a"]["families"]
        self.assertEqual(len(fam), 1)
        self.assertEqual(fam[0]["rule"]["players"][0]["bytes"], 2)                    # the wider read at one base
        self.assertIn("1@0x100", fam[0]["member_reads"])
        self.assertTrue(out["decided"])

    def test_overlapping_reads_whose_both_bytes_change_are_one_family(self):
        facts = {"begin": (0x3C78, 0x3C78), "P1": (0x2050, 0), "P2": (0, 0x1460), "P1b": (0x1010, 0), "P2b": (0, 0x2222)}
        states = []
        for n, (x, y) in facts.items():
            pairs = {0x100: x & 0xFF, 0x101: x >> 8, 0x110: y & 0xFF, 0x111: y >> 8}
            states.append(self.st(*(("begin", None) if n == "begin" else ("end", n[:2])), pairs))
        b = search.search(states, 2)["templates"]["b"]
        self.assertGreaterEqual(b["count"], 3)                                         # B94's merge keeps three reads
        self.assertEqual(b["families_found"], 1)                                       # B96: one place, one family
        self.assertEqual(b["families"][0]["rule"]["players"][0], {"name": "P1", "address": "0x100", "bytes": 2,
                                                                   "endian": "little"})
        self.assertIn("1@0x101", b["families"][0]["member_reads"])

    def test_the_order_and_the_template_order(self):
        facts = {"begin": (0, 0), "P1": (2, 1), "P2": (1, 2), "P1b": (2, 0), "P2b": (0, 2)}
        extra = {n: {0x801: x, 0x803: y} for n, (x, y) in facts.items()}                # unaligned, stride 2
        out = search.search(self.five(extra), 2)
        first = out["templates"]["a"]["passing"][0]["rule"]["players"]
        self.assertEqual([p["address"] for p in first], ["0x100", "0x110"])            # stride 16 beats stride 2…
        self.assertEqual(search._order({"hinted": False, "all_vary": True,
                                        "rule_member": {"size": 2, "base": 0x801, "stride": 2}})[3:5], (True, True))
        self.assertLess(search._order({"hinted": True, "all_vary": False, "rule_member": {"size": 1, "base": 9, "stride": 3}}),
                        search._order({"hinted": False, "all_vary": True, "rule_member": {"size": 2, "base": 0, "stride": 4}}))

    def test_folds_on_random_2_mib_time(self):
        rng = np.random.default_rng(7)
        n = 0x200000
        states = [{"label": lab, "winner": w, "mem": rng.integers(0, 256, n, dtype=np.uint8).tobytes(),
                   "stable": np.ones(n, dtype=bool)}
                  for lab, w in (("begin", None), ("end", "P1"), ("end", "P2"), ("end", "P1"), ("end", "P2"))]
        t0 = time.monotonic()
        out = search.search(states, 2)
        took = time.monotonic() - t0
        print(f"\nB96 time, the pure search with 4 folds, random 2 MiB x 5 states: {took:.2f} s", file=sys.stderr)
        self.assertLess(took, 60)
        self.assertEqual(len(out["templates"]["a"]["folds"]), 4)

    def test_needs_a_begin_and_an_end(self):
        with self.assertRaises(search.SearchError):
            search.search([{"label": "end", "winner": "P1", "mem": bytes(16), "stable": np.ones(16, dtype=bool)}], 2)


if __name__ == "__main__":
    unittest.main()
