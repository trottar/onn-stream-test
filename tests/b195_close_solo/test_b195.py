#!/usr/bin/env python3
"""B196 / B197 (host): close names what changed — by root, kind and hashed name — before it ends the befores, the hub's
own slots 8 and 9 left out by kind and root; solo's real-match switches (the go and the end) must be read, a practice's
may be listed. B157's solo fixture and B162's made-up logs (a made-up binding, hub and title; the hub never reached).

- `Close`: the hub's slot 9 and its picture (and slot 8) changed -> close PASS, the page saying what was left out;
  a user's slot and its picture changed and a rules file new -> close FAIL, each named by root and kind (never a name)
  in the cell, the page and `recorded`, then the befores ended; a before written by older code (sha only) still
  compared.
- `Solo`: the go listed (the end came sooner than 4 s after it) -> not met; the end's S failing -> S not met, the
  real-match cell met; the line after a practice says to wait on the load screen before pressing ✕.
Temp dirs removed (B157's fixture).

    python3 -m unittest discover -s tests/b195_close_solo -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b162_solo_safe"))
import test_b162 as b162  # noqa: E402  (its Unit fixture's methods, reused; its tests are not collected here)

_tool = b162._tool
REAL = "the real match's go and end read for S (a practice's may be listed)"
S = "S: sound within 4 s of each switch, underruns rising <= 20 a row"


class Close(unittest.TestCase):
    setUp = b162.Unit.setUp
    tearDown = b162.Unit.tearDown
    close_ready = b162.Unit.close_ready

    def slots(self, b) -> Path:
        d = self.tmp / "proj/data/games/retroarch/states/Beetle PSX HW"
        d.mkdir(parents=True, exist_ok=True)
        stem = Path(b.get("relative_path") or "Made Up (USA).cue").stem
        for suf in (".state", ".state.png", ".state1", ".state1.png", ".state8", ".state9", ".state9.png"):
            (d / f"{stem}{suf}").write_text(f"before {suf}")
        return d / stem

    def close(self):
        rc, text = _tool("close", "T93")
        v = json.loads((self.tmp / "ev/T93/close.json").read_text())
        return rc, text, v, (self.tmp / "ev/T93/close.md").read_text()

    def test_1_the_hubs_slots_left_out(self):
        import party_add_game as pag
        b = self.close_ready()
        stem = self.slots(b)
        (self.tmp / "home/T93/files_before.json").write_text(json.dumps(pag.files_digest(b)))
        for suf in (".state8", ".state9", ".state9.png"):
            Path(f"{stem}{suf}").write_text("the hub wrote it during the match")
        rc, text, v, page = self.close()
        self.assertEqual(rc, 0, text + json.dumps(v))
        cell = {c["cell"]: c for c in v["cells"]}["every file = bench's before"]
        self.assertEqual(cell["read"], [])
        self.assertIn("Changed since bench's before: none.", page)
        self.assertIn("Left out of the comparison: the hub's own slots 8 and 9 and their pictures", page)

    def test_2_a_users_slot_named_before_the_befores_end(self):
        import party_add_game as pag
        b = self.close_ready()
        stem = self.slots(b)
        (self.tmp / "home/T93/files_before.json").write_text(json.dumps(pag.files_digest(b)))
        Path(f"{stem}.state1").write_text("the user saved over slot 1")
        Path(f"{stem}.state1.png").write_text("its picture")
        pag.rules_folder().mkdir(parents=True, exist_ok=True)
        (pag.rules_folder() / "a-made-up-new.party.json").write_text("{}")
        rc, text, v, page = self.close()
        self.assertEqual(rc, 1, text)
        cell = {c["cell"]: c for c in v["cells"]}["every file = bench's before"]
        got = sorted((c["root"], c["kind"], c["is"]) for c in cell["read"])
        self.assertEqual(got, [("rules", "a rules file", "new"), ("states", "a user's slot 1", "changed"),
                               ("states", "a user's slot 1 picture", "changed")])
        self.assertTrue(all(len(c["file"]) == 16 for c in cell["read"]))
        self.assertEqual(v["recorded"]["changed"], cell["read"])
        self.assertIn("a user's slot 1 in states (", page)
        self.assertIn("a rules file in rules (", page)
        self.assertNotIn("Made Up", page + json.dumps(v) + text)
        self.assertNotIn("made-up-new", page + json.dumps(v) + text)
        self.assertFalse((self.tmp / "home/T93/files_before.json").exists())      # then ended (B172)

    def test_3_a_before_of_older_code_still_compared(self):
        import party_add_game as pag
        b = self.close_ready()
        stem = self.slots(b)
        old = {k: v[0] for k, v in pag.files_digest(b).items()}                   # sha only, as before B196
        (self.tmp / "home/T93/files_before.json").write_text(json.dumps(old))
        Path(f"{stem}.state").write_text("a SAVE rewrote slot 0")
        rc, text, v, _page = self.close()
        self.assertEqual(rc, 1, text)
        cell = {c["cell"]: c for c in v["cells"]}["every file = bench's before"]
        self.assertEqual([(c["root"], c["kind"]) for c in cell["read"]],
                         [("states", "slot 0 (every SAVE rewrites it)")])


class Solo(unittest.TestCase):
    setUp = b162.Unit.setUp
    tearDown = b162.Unit.tearDown
    logs = b162.Unit.logs
    switch_logs = b162.Unit.switch_logs
    verdict = b162.Unit.verdict

    def test_1_the_go_listed_not_met(self):
        rc, _ = self.switch_logs([(0, 1.3, "minigame", True, True), (20, 1.3, "board", False, True),
                                  (40, 1.3, "minigame", False, True), (42, 1.3, "board", False, True)])
        v, c = self.verdict()
        self.assertEqual(c[REAL]["read"]["listed"], ["3 (the go)"])
        self.assertFalse(c[REAL]["met"])
        self.assertEqual(rc, 1)

    def test_2_the_ends_s_failing(self):
        rc, _ = self.switch_logs([(0, 1.3, "minigame", True, False), (2.6, 1.3, "board", False, True),
                                  (30, 1.3, "minigame", False, True), (60, 1.3, "board", False, False)])
        v, c = self.verdict()
        self.assertTrue(c[REAL]["met"])
        self.assertEqual(c[S]["read"], [True, True, False])                       # the board, the go, the end
        self.assertFalse(c[S]["met"])
        self.assertEqual(rc, 1)

    def test_3_the_line_after_a_practice(self):
        import party_add_game as pag
        b = {"players": 2}
        line = pag.solo_lines(b)[1]
        self.assertIn("leave it with the Select button (Share), then wait a few seconds on the load screen before "
                      "pressing ✕ to play it for real", line)
        self.assertIn("before pressing A to play", pag.solo_lines(b, "xbox")[1])


if __name__ == "__main__":
    unittest.main()
