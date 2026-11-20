#!/usr/bin/env python3
"""B169 (host): two cells for the add-a-game tool's solo — on made-up logs, a made-up hub on loopback (B157's solo
fixture), nothing of the hub's read.

**The card count:** the board's own `cards <n>, chose …` line — `cards 1` → "the board showed one card" met; `cards 2`
→ not met, named; no card line → not met. **A title already added gets its files' before:** solo's first run writes
`files_before.json` (the users' slots, slot pictures, rules and kept folders), so close compares them — a user's slot
changed after the solo → close FAIL; only an in-game save changed → close PASS, recorded. **A new title's bench before
is kept** (solo does not overwrite it). Temp dirs removed.

    python3 -m unittest discover -s tests/b169_solo_cells -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b157_add_game", "b162_solo_safe"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
sys.path.insert(0, str(ROOT / "tools"))
import test_b157 as b157t  # noqa: E402  (its SoloReads fixture, reused)
import test_b162 as b162t  # noqa: E402  (its close fixture, reused)


def _tool(*argv):
    import party_add_game as pag
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pag.main([str(a) for a in argv])
    return rc, buf.getvalue()


class Cards(unittest.TestCase):
    setUp = b157t.SoloReads.setUp
    tearDown = b157t.SoloReads.tearDown
    logs = b157t.SoloReads.logs
    read = b157t.SoloReads.read

    def card_read(self, line):
        rc, text = self.read()
        g = self.tmp / "proj/logs/games/20990101-000000-party.log"
        lines = [ln for ln in g.read_text().splitlines() if "cards 1, chose 0" not in ln]
        if line:
            lines.insert(0, f"PrivyParty: hub mini game: {line}")
        g.write_text("\n".join(lines) + "\n")
        rc, text = _tool("solo", "T93", "--read", "--winner", 1)
        v = json.loads((self.tmp / "ev/T93/solo.json").read_text())
        return rc, {c["cell"]: c for c in v["cells"]}

    def test_one_card(self):
        rc, c = self.card_read("cards 1, chose 0")
        self.assertTrue(c["the board showed one card"]["met"])
        self.assertEqual(c["the board showed one card"]["read"], 1)
        self.assertEqual(rc, 0)

    def test_two_cards_not_met(self):
        rc, c = self.card_read("cards 2, chose 1")
        self.assertFalse(c["the board showed one card"]["met"])
        self.assertEqual(c["the board showed one card"]["read"], 2)
        self.assertEqual(rc, 1)

    def test_no_card_line_not_met(self):
        rc, c = self.card_read(None)
        self.assertFalse(c["the board showed one card"]["met"])
        self.assertIsNone(c["the board showed one card"]["read"])


class FilesBefore(unittest.TestCase):
    setUp = b157t.SoloReads.setUp
    tearDown = b157t.SoloReads.tearDown
    close_ready = b162t.Unit.close_ready

    def tree(self, described: bool):
        b = self.close_ready(cheat=True)
        b["described"] = described
        (self.tmp / "home/T93/binding.json").write_text(json.dumps(b))
        if described:                                         # solo after learn's PASS (a title already added)
            import party_add_game as pag
            (self.tmp / "ev/T93/learn.json").write_text(json.dumps({"verdict": "PASS",
                                                                     "inputs": pag.learn_inputs("T93", b)}))
        ra = self.tmp / "proj/data/games/retroarch"
        prof = ra / "cheat_profiles/madeupgame1" / ("AB" * 32)
        (prof / "saves/Beetle PSX HW").mkdir(parents=True)
        (prof / "states/Beetle PSX HW").mkdir(parents=True)
        (prof / "saves/Beetle PSX HW/Made Up (USA).srm").write_text("in-game save")
        (prof / "states/Beetle PSX HW/Made Up (USA).state1").write_text("the user's slot 1")
        return prof

    def test_a_title_already_added_gets_its_before(self):
        prof = self.tree(described=True)
        self.assertFalse((self.tmp / "home/T93/files_before.json").exists())
        rc, text = _tool("solo", "T93")
        self.assertEqual(rc, 3, text)
        self.assertTrue((self.tmp / "home/T93/files_before.json").is_file())
        (prof / "saves/Beetle PSX HW/Made Up (USA).srm").write_text("in-game save, after a match")
        rc, text = _tool("close", "T93")
        v = json.loads((self.tmp / "ev/T93/close.json").read_text())
        self.assertEqual(rc, 0, text + json.dumps(v))
        self.assertIn({"save": "under the setup 1", "is": "changed"}, v["recorded"]["in_game_saves"])
        self.assertIn("every file = bench's before", [c["cell"] for c in v["cells"]])
        (prof / "states/Beetle PSX HW/Made Up (USA).state1").write_text("the user's slot 1, saved over")
        rc, text = _tool("close", "T93")
        v = json.loads((self.tmp / "ev/T93/close.json").read_text())
        self.assertEqual(rc, 1, text)
        self.assertIn("every file = bench's before", [c["cell"] for c in v["cells"] if not c["met"]])

    def test_a_new_titles_bench_before_kept(self):
        self.tree(described=False)
        (self.tmp / "home/T93/files_before.json").write_text('{"made-up": "bench\'s before"}')
        rc, text = _tool("solo", "T93")
        self.assertEqual(rc, 3, text)
        self.assertEqual(json.loads((self.tmp / "home/T93/files_before.json").read_text()),
                         {"made-up": "bench's before"})


if __name__ == "__main__":
    unittest.main()
