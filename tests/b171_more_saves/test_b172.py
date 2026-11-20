#!/usr/bin/env python3
"""B172 (host): the solo mark ends at close — on made-up logs and a made-up hub on loopback (B157's solo fixture, B162's
close fixture), nothing of the hub's read.

- solo's lines write the mark; **close ends it with the files' and in-game saves' befores**; the next solo writes its
  own mark from the logs as they are then — **its read counts only its own rows** (the first solo's switches are not
  read again: "planned switches" 0 with no new rows).
- **register ends a mark an earlier use left unclosed** (T88's add_game folder holds one from the first use).
Temp dirs removed.

    python3 -m unittest discover -s tests/b171_more_saves -p 'test_b172.py' -v
"""
from __future__ import annotations

import contextlib
import io
import json
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

MARKS = ("solo_mark.json", "files_before.json", "saves_before.json")


def _tool(*argv):
    import party_add_game as pag
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pag.main([str(a) for a in argv])
    return rc, buf.getvalue()


class SoloMark(unittest.TestCase):
    setUp = b157t.SoloReads.setUp
    tearDown = b157t.SoloReads.tearDown
    logs = b157t.SoloReads.logs
    close_ready = b162t.Unit.close_ready

    def here(self):
        return {n: (self.tmp / "home/T93" / n).is_file() for n in MARKS}

    def test_close_ends_the_mark_and_the_next_solo_reads_only_its_own_rows(self):
        self.close_ready()
        rc, text = _tool("solo", "T93")
        self.assertEqual(rc, 3, text)
        first = json.loads((self.tmp / "home/T93/solo_mark.json").read_text())
        self.assertEqual(self.here(), {n: True for n in MARKS})
        self.logs()                                                   # the first solo's practice, go and end
        rc, text = _tool("solo", "T93", "--read", "--winner", 1)
        self.assertEqual(rc, 0, text + (self.tmp / "ev/T93/solo.md").read_text())
        rc, text = _tool("close", "T93")
        self.assertEqual(rc, 0, text)
        self.assertEqual(self.here(), {n: False for n in MARKS})       # ended at close
        rc, text = _tool("solo", "T93")                                # the next solo: its own mark
        self.assertEqual(rc, 3, text)
        second = json.loads((self.tmp / "home/T93/solo_mark.json").read_text())
        self.assertGreater(second["party"], first["party"])
        self.assertGreater(second["since_unix"], first["since_unix"])
        rc, text = _tool("solo", "T93", "--read", "--winner", 1)       # no new rows: nothing of the first solo's read
        c = {x["cell"]: x for x in json.loads((self.tmp / "ev/T93/solo.json").read_text())["cells"]}
        self.assertEqual(rc, 1)
        self.assertEqual(c["planned switches"]["read"], 0)

    def test_register_ends_a_mark_left_unclosed(self):
        rc, text = _tool("solo", "T93")
        self.assertEqual(rc, 3, text)
        self.assertTrue((self.tmp / "home/T93/solo_mark.json").is_file())
        rules = self.tmp / "rules"                                     # a title already in a made-up rules folder
        (rules / "madeupgame1.party.json").write_text(json.dumps({"players": 2, "result": "winner"}))
        (rules / "madeupgame1.state").write_text("made-up begin")
        (rules / "madeupgame1.endscreen.json").write_text("{}")
        rc, text = _tool("register", "T93", "--players", 2, "--system", "n64", "--result", "winner", "--rules-players", 2)
        self.assertEqual(self.here(), {n: False for n in MARKS}, text)


if __name__ == "__main__":
    unittest.main()
