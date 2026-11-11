#!/usr/bin/env python3
"""B95 (host): B93's tool reads a state as it stands — no frame run — and names "no winner yet" apart from a tie.

On B93's counters fixture (two counters that advance every frame, P1 twice as fast in mode 0): states made with the
tool's own `--make-state` (now written and saved paused) holding begin (equal), P1 ahead, P2 ahead. `--as-is --runs 3`
must name none / P1 / P2, 3 of 3, with the values exactly as written (any frame run would move them: 0 frames). The
rule logic and the runs' agreement without an emulator. RetroArch headless (B61's form); skipped without it or a
display. Temp dirs removed at exit.

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
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOL = ROOT / "tools" / "h7_minigame_proof.py"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))
import fixture_counters  # noqa: E402
import h7_minigame_proof as proof  # noqa: E402
from test_h7_proof import display_env  # noqa: E402

RULE = {"players": [{"name": "P1", "address": "0x0100", "bytes": 2}, {"name": "P2", "address": "0x0102", "bytes": 2}],
        "winner": "max", "memory": "ram", "none_when": "equal"}
STATES = {"begin": (5, 5, None), "P1": (9, 4, "P1"), "P2": (3, 8, "P2")}


class Logic(unittest.TestCase):
    def test_none_when_equal_floor_and_tie(self):
        r = proof.parse_rule(RULE)
        self.assertEqual(proof.answer(r, {"P1": 5, "P2": 5}), (None, "no winner yet"))
        self.assertEqual(proof.answer(r, {"P1": 9, "P2": 4}), ("P1", None))
        tie = proof.parse_rule({k: v for k, v in RULE.items() if k != "none_when"})
        self.assertEqual(proof.answer(tie, {"P1": 5, "P2": 5}), ("tie", None))         # B93's answer, unchanged
        floor = proof.parse_rule({**RULE, "none_when": {"floor": 0}})
        self.assertEqual(proof.answer(floor, {"P1": 0, "P2": 0}), (None, "no winner yet"))
        self.assertEqual(proof.answer(floor, {"P1": 3, "P2": 3}), ("tie", None))
        with self.assertRaises(proof.ProofError):
            proof.parse_rule({**RULE, "none_when": "same"})

    def test_the_single_field_form(self):
        r = proof.parse_rule({"address": "0x200", "bytes": 1, "values": {"P1": 1, "P2": 2}, "none_value": 0})
        self.assertEqual(proof.answer(r, {"field": 0}), (None, "no winner yet"))
        self.assertEqual(proof.answer(r, {"field": 2}), ("P2", None))
        self.assertEqual(proof.answer(r, {"field": 7})[0], "unknown")

    def test_a_disagreement_is_reported_not_hidden(self):
        runs = iter([{"system": "snes", "winner": "P1", "values": {"P1": 2, "P2": 1}},
                     {"system": "snes", "winner": "P2", "values": {"P1": 1, "P2": 2}},
                     {"system": "snes", "winner": "P1", "values": {"P1": 2, "P2": 1}}])
        with mock.patch.object(proof, "run_once", lambda *a, **k: next(runs)):
            out = proof.run_proof(Path("x"), "snes", Path("s"), 0, RULE, True, 3)
        self.assertEqual((out["agreement"], out["winner"]), ("2 of 3", "disagree"))
        self.assertEqual([x["winner"] for x in out["per_run"]], ["P1", "P2", "P1"])


@unittest.skipUnless(proof.APP.is_file() and (proof.CORES / "snes9x_libretro.so").is_file() and display_env(),
                     "RetroArch, snes9x or a display is absent")
class AsIs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = display_env()
        cls.tmp = Path(tempfile.mkdtemp(prefix="h7_b95_"))
        cls.rom = cls.tmp / "Made Up Counters.sfc"
        cls.rom.write_bytes(fixture_counters.build())
        cls.rule = cls.tmp / "rule.json"
        cls.rule.write_text(json.dumps(RULE))
        cls.states = {}
        for name, (p1, p2, _w) in STATES.items():
            out = cls.tmp / f"{name}.state"
            o = cls.cli("--make-state", out, "--after", "0.5", "--write", f"0x0100={p1.to_bytes(2, 'little').hex()}",
                        "--write", f"0x0102={p2.to_bytes(2, 'little').hex()}")
            assert o.get("state_written"), o
            cls.states[name] = out

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def cli(cls, *args) -> dict:
        r = subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--content", str(cls.rom), "--system", "snes",
                            *[str(a) for a in args]], capture_output=True, text=True, env=cls.env, timeout=300)
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_as_is_names_none_p1_p2_three_of_three_with_no_frame_run(self):
        for name, (p1, p2, winner) in STATES.items():
            out = self.cli("--state", self.states[name], "--as-is", "--runs", "3", "--rule", self.rule)
            self.assertEqual(out["agreement"], "3 of 3", out)
            self.assertEqual(out["winner"], winner, out)
            if winner is None:
                self.assertEqual(out["reason"], "no winner yet")
            for run in out["per_run"]:
                self.assertEqual(run["values"], {"P1": p1, "P2": p2})    # as written: 0 frames ran (bound 0)

    def test_seconds_zero_is_as_is(self):
        out = self.cli("--state", self.states["P2"], "--seconds", "0", "--rule", self.rule)
        self.assertTrue(out.get("as_is"))
        self.assertEqual((out["winner"], out["values"]), ("P2", {"P1": 3, "P2": 8}))

    def test_a_running_read_moves_the_values(self):                      # the control: frames do run without --as-is
        out = self.cli("--state", self.states["begin"], "--seconds", "0.5", "--rule", self.rule)
        self.assertGreater(out["values"]["P1"], 5)
        self.assertEqual(out["winner"], "P1")                             # mode 0: P1 runs at double rate

    def test_a_corrupt_state_is_an_error(self):
        bad = self.tmp / "bad.state"
        bad.write_bytes(b"#RZIPv\x01#" + os.urandom(3000))
        out = self.cli("--state", bad, "--as-is", "--rule", self.rule)
        self.assertIn("error", out)
        self.assertNotIn("winner", out)

    def test_a_state_the_core_refuses_is_an_error(self):
        import zlib                                                      # a well-formed container RetroArch reads (N > 0
        data = os.urandom(10000)                                        # bytes) that the core then refuses
        comp = zlib.compress(data)
        refused = self.tmp / "refused.state"
        refused.write_bytes(b"#RZIPv\x01#" + (131072).to_bytes(4, "little") + len(data).to_bytes(8, "little")
                            + len(comp).to_bytes(4, "little") + comp)
        out = self.cli("--state", refused, "--as-is", "--rule", self.rule)
        self.assertIn("failed to load", out.get("error", ""), out)
        self.assertNotIn("winner", out)

if __name__ == "__main__":
    unittest.main()
