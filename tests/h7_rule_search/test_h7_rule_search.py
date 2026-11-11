#!/usr/bin/env python3
"""B94 (host): the win-rule search on synthetic fixtures (no game).

States are made on `fixtures.py`'s PS-X EXE and SNES ROM — SNES with B93's own `--make-state --write`, one session
per state at different moments; PS1 in ONE paused session (written, saved, written, saved: the core's own time-varying
bytes the same in every state — made at different moments they sometimes fit a template by chance, see the record): a planted per-player
block (a round counter and a level), decoys (a block where P1 is larger in every state; a block that fits begin + a
P1-won end but not a P2-won end), and noise (the SNES program's frame counter and xorshift buffer; on PS1, whose fixture
code does not run headless, random bytes written per state). The search reads each state paused, 3 loads, through
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

TWO = {"begin": {"rounds": (0, 0), "level": (120, 120), "d_counter": (3, 3), "d_level": (100, 100)},
       "P1": {"rounds": (2, 1), "level": (37, 0), "d_counter": (7, 2), "d_level": (40, 0)},
       "P2": {"rounds": (1, 2), "level": (0, 55), "d_counter": (6, 4), "d_level": (30, 0)}}
FOUR = {"begin": {"rounds": (0, 0, 0, 0), "level": (120, 120, 120, 120)},
        "P3": {"rounds": (1, 0, 2, 1), "level": (0, 0, 60, 0)},
        "P1": {"rounds": (2, 1, 0, 0), "level": (45, 0, 0, 0)},
        "P4": {"rounds": (0, 1, 1, 2), "level": (0, 0, 0, 70)}}


def u16(v: int) -> str:
    return v.to_bytes(2, "little").hex()


def writes(plan: dict, facts: dict, seed: int, noise: bool) -> list[str]:
    w = []
    for k, (r, lv) in enumerate(zip(facts["rounds"], facts["level"])):
        base = plan["block"] + k * plan["stride"]
        w += [f"{base + plan['rounds']:#x}={u16(r)}", f"{base + plan['level']:#x}={u16(lv)}"]
    if "d_counter" in facts:
        for k, v in enumerate((9, 4)):                                   # P1 larger in every state
            w.append(f"{plan['decoy_always_p1'] + k * plan['decoy_stride']:#x}={u16(v)}")
        for k, (c, lv) in enumerate(zip(facts["d_counter"], facts["d_level"])):
            base = plan["decoy_two_states"] + k * plan["decoy_stride"]
            w += [f"{base:#x}={u16(c)}", f"{base + 4:#x}={u16(lv)}"]
    if noise:                                                            # PS1: the fixture's code does not run headless
        rnd = random.Random(seed)
        for lo, hi in plan["noise"]:
            w.append(f"{lo:#x}={bytes(rnd.randrange(256) for _ in range(hi - lo)).hex()}")
    return w


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
        return [{"label": "begin" if n == "begin" else "end", "winner": None if n == "begin" else n,
                 "mem": self.read[n][0], "stable": self.read[n][1]} for n in names]

    def planted(self, players: int) -> dict:
        return [hex(self.plan["block"] + k * self.plan["stride"] + self.plan["rounds"]) for k in range(players)]


@unittest.skipUnless(proof.APP.is_file() and display_env(), "RetroArch or a display is absent")
class PS1TwoPlayers(Base):
    def test_loads_are_stable(self):
        for name, (_mem, stable) in self.read.items():
            self.assertTrue(bool(stable.all()), name)                   # paused loads: every byte the same

    def test_three_states_decide_the_planted_rule(self):
        out = search.search(self.states("begin", "P1", "P2"), 2)
        self.assertTrue(out["decided"], out.get("not_decided"))
        self.assertEqual(out["template"], "a")
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(2))
        self.assertEqual(out["templates"]["a"]["count"], 1)
        self.assertEqual(out["templates"]["b"]["count"], 1)               # the planted level also fits, alone
        level = [hex(self.plan["block"] + k * self.plan["stride"] + self.plan["level"]) for k in range(2)]
        self.assertEqual([p["address"] for p in out["also_fits"][0]["rule"]["players"]], level)

    def test_begin_and_one_end_is_not_decided_and_includes_the_planted_rule(self):
        out = search.search(self.states("begin", "P1"), 2)
        self.assertFalse(out["decided"])
        self.assertGreater(out["not_decided"]["counts"]["a"], 1)
        self.assertGreater(out["not_decided"]["counts"]["b"], 1)
        self.assertIsNone(out["not_decided"]["counts"]["c"])              # not testable with one winner
        self.assertIn("P2", out["not_decided"]["would_split"])
        self.assertNotIn("rule", out)
        search.SHOWN, old = ALL, search.SHOWN
        try:
            full = search.search(self.states("begin", "P1"), 2)
        finally:
            search.SHOWN = old
        found = [[p["address"] for p in c["rule"]["players"]] for c in full["templates"]["a"]["candidates"]]
        self.assertIn(self.planted(2), found)
        decoy = [hex(self.plan["decoy_two_states"] + k * self.plan["decoy_stride"]) for k in range(2)]
        self.assertIn(decoy, found)                                       # the decoy fits two states…

    def test_a_decoy_never_ranks_above_the_planted_rule_once_p2_is_in(self):
        search.SHOWN, old = ALL, search.SHOWN
        try:
            out = search.search(self.states("begin", "P1", "P2"), 2)
        finally:
            search.SHOWN = old
        for t in ("a", "b"):
            addrs = [int(p["address"], 16) for c in out["templates"][t]["candidates"] for p in c["rule"]["players"]]
            for d in (self.plan["decoy_two_states"], self.plan["decoy_always_p1"]):
                self.assertFalse(any(d <= a < d + 2 * self.plan["decoy_stride"] for a in addrs), (t, addrs))  # …not three

    def test_the_cli_and_its_time_on_2_mib(self):
        listed = self.tmp / "states.json"
        listed.write_text(json.dumps([{"state": str(self.files[n]), "label": "begin" if n == "begin" else "end",
                                       "winner": None if n == "begin" else n} for n in ("begin", "P1", "P2")]))
        r = subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--content", str(self.rom), "--system", "ps1",
                            "--states", str(listed), "--time"], capture_output=True, text=True, env=self.env, timeout=600)
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertTrue(out["decided"], out)
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(2))
        print(f"\nB94 time, PS1 2 MiB, 3 states x 3 loads: {out['seconds']}", file=sys.stderr)
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
        out = search.search(self.states("begin", "P3", "P1"), 4)       # two ends: the counter is not decided…
        self.assertEqual(out["templates"]["a"]["count"], 2)               # (a half-stride block also fits)
        self.assertEqual([p["address"] for p in out["templates"]["a"]["candidates"][0]["rule"]["players"]],
                         self.planted(4))                                 # ranked first (every player's field changes)
        self.assertTrue(out["decided"])                                   # …the level is: one candidate
        self.assertEqual(out["template"], "b")
        self.assertEqual([p["address"] for p in out["rule"]["players"]],
                         [hex(self.plan["block"] + k * self.plan["stride"] + self.plan["level"]) for k in range(4)])
        out = search.search(self.states("begin", "P3", "P1", "P4"), 4)  # an end won by a fourth player splits them
        self.assertTrue(out["decided"], out.get("not_decided"))
        self.assertEqual((out["template"], out["templates"]["a"]["count"]), ("a", 1))
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(4))


@unittest.skipUnless(proof.APP.is_file() and display_env(), "RetroArch or a display is absent")
class SnesTwoPlayers(Base):
    system = "snes"
    plan = F.SNES
    noise = False                                    # the program's own frame counter and buffer

    def test_the_noise_runs_and_the_planted_rule_is_decided(self):
        b, e = self.read["begin"][0], self.read["P1"][0]
        self.assertNotEqual(b[0x1000:0x1400], e[0x1000:0x1400])            # the buffer differs between states
        out = search.search(self.states("begin", "P1", "P2"), 2)
        self.assertTrue(out["decided"], out.get("not_decided"))
        self.assertEqual([p["address"] for p in out["rule"]["players"]], self.planted(2))


class NoEmulator(unittest.TestCase):
    def mem(self, pairs: dict[int, int], size: int = 4096) -> bytes:
        m = bytearray(size)
        for a, v in pairs.items():
            m[a] = v
        return bytes(m)

    def test_unstable_addresses_are_dropped(self):
        def st(label, winner, pairs, unstable=()):
            s = np.ones(4096, dtype=bool)
            for a in unstable:
                s[a] = False
            return {"label": label, "winner": winner, "mem": self.mem(pairs), "stable": s}
        planted = {0x100: 0, 0x110: 0}
        p1 = {0x100: 2, 0x110: 1}
        p2 = {0x100: 1, 0x110: 2}
        decoy = {0x200: 5, 0x204: 5}, {0x200: 6, 0x204: 4}, {0x200: 4, 0x204: 6}   # fits all three, but unstable
        states = [st("begin", None, {**planted, **decoy[0]}, unstable=[0x200]),
                  st("end", "P1", {**p1, **decoy[1]}), st("end", "P2", {**p2, **decoy[2]})]
        out = search.search(states, 2)
        addrs = [[p["address"] for p in c["rule"]["players"]] for c in out["templates"]["a"]["candidates"]]
        self.assertEqual(addrs, [["0x100", "0x110"]])
        self.assertTrue(out["decided"])
        self.assertGreater(out["unstable_bytes"], 0)
        states[0]["stable"][0x200] = True                                   # stable → it fits as well: two, not decided
        out = search.search(states, 2)
        self.assertEqual(out["templates"]["a"]["count"], 2)

    def test_needs_a_begin_and_an_end(self):
        with self.assertRaises(search.SearchError):
            search.search([{"label": "end", "winner": "P1", "mem": bytes(16), "stable": np.ones(16, dtype=bool)}], 2)


if __name__ == "__main__":
    unittest.main()
