#!/usr/bin/env python3
"""B93 (host): H7's mini-game proof — load a state, run a fixed time, read memory, name the winner.

The rule's logic without an emulator; then the tool's own CLI (`tools/h7_minigame_proof.py`) with RetroArch headless on
a synthetic SNES ROM (B61's form; `fixture_counters.py`: two frame counters, a mode byte picks who runs at double
rate). The state is made by the tool's `--make-state` (boot, mode byte 1, save). Met: with the state P2 wins 3 / 3;
from boot P1 wins 3 / 3; an address with no memory is an error, never a winner. The emulator cases are skipped when
RetroArch or a display is absent. Temp dirs removed at exit.

    python3 -m unittest discover -s tests/h7_minigame_proof -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOL = ROOT / "tools" / "h7_minigame_proof.py"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))
import fixture_counters  # noqa: E402
import h7_minigame_proof as proof  # noqa: E402

RULE = {"players": [{"name": "P1", "address": "0x0100", "bytes": 2}, {"name": "P2", "address": "0x0102", "bytes": 2}],
        "winner": "max", "memory": "ram"}


def display_env() -> dict | None:
    env = dict(os.environ)
    if not env.get("DISPLAY"):
        try:
            pid = subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value", "privyhub-companion"],
                                 capture_output=True, text=True).stdout.strip()
            for kv in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
                k, _, v = kv.decode(errors="replace").partition("=")
                if k in ("DISPLAY", "XAUTHORITY"):
                    env[k] = v
        except (OSError, ValueError):
            return None
    return env if env.get("DISPLAY") else None


class Rule(unittest.TestCase):
    def test_the_winner(self):
        self.assertEqual(proof.decide({"P1": 5, "P2": 9}, "max"), "P2")
        self.assertEqual(proof.decide({"P1": 5, "P2": 9}, "min"), "P1")
        self.assertEqual(proof.decide({"P1": 7, "P2": 7}, "max"), "tie")

    def test_values_and_refusals(self):
        self.assertEqual(proof.value_of("READ_CORE_RAM 100 34 12", 0x100, 2, "little"), 0x1234)
        self.assertEqual(proof.value_of("READ_CORE_RAM 100 34 12", 0x100, 2, "big"), 0x3412)
        with self.assertRaises(proof.ProofError):
            proof.value_of("READ_CORE_RAM ffffff -1", 0xFFFFFF, 2, "little")
        with self.assertRaises(proof.ProofError):
            proof.value_of(None, 0x100, 1, "little")
        with self.assertRaises(proof.ProofError):
            proof.parse_rule({"players": [{"name": "P1", "address": "0x0"}]})       # one player
        with self.assertRaises(proof.ProofError):
            proof.parse_rule({**RULE, "winner": "most"})


@unittest.skipUnless(proof.APP.is_file() and (proof.CORES / "snes9x_libretro.so").is_file() and display_env(),
                     "RetroArch, snes9x or a display is absent")
class OnTheFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="h7_test_"))
        cls.rom = cls.tmp / "Made Up Counters.sfc"
        cls.rom.write_bytes(fixture_counters.build())
        cls.rule = cls.tmp / "rule.json"
        cls.rule.write_text(json.dumps(RULE))
        cls.env = display_env()
        cls.state = cls.tmp / "p2_fast.state"
        out = cls.cli("--make-state", cls.state, "--after", "1.0", "--write", "0x0104=01")
        assert out.get("state_written"), out

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def cli(cls, *args) -> dict:
        r = subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--content", str(cls.rom), "--system", "snes",
                            *[str(a) for a in args]], capture_output=True, text=True, env=cls.env, timeout=120)
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_with_the_state_p2_wins_repeatably(self):
        for _ in range(3):
            out = self.cli("--state", self.state, "--seconds", "2", "--rule", self.rule)
            self.assertTrue(out["state_loaded"], out)
            self.assertEqual(out["winner"], "P2", out)
            self.assertGreater(out["values"]["P2"], out["values"]["P1"])

    def test_from_boot_p1_wins_repeatably(self):
        for _ in range(3):
            out = self.cli("--no-state", "--seconds", "2", "--rule", self.rule)
            self.assertFalse(out["state_loaded"])
            self.assertEqual(out["winner"], "P1", out)

    def test_an_address_with_no_memory_is_an_error_not_a_winner(self):
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps({**RULE, "players": [RULE["players"][0], {"name": "P2", "address": "0xFFFFFF", "bytes": 2}]}))
        out = self.cli("--no-state", "--seconds", "1", "--rule", bad)
        self.assertIn("no memory answer", out.get("error", ""), out)
        self.assertNotIn("winner", out)


if __name__ == "__main__":
    unittest.main()
