#!/usr/bin/env python3
"""B32: the client's `surface_lost` row, host side.

    python3 -m unittest discover -s tests/surface_lost -v

The real parser and the real LinkDropRecovery writing its recovery log in a temp root; the real heartbeat handler's
block run from games.py's own source (its AST), with a fake recovery; no key = nothing imported (a fresh process).
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import surface_lost_row as slr  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

HELD = ('{"seq":1,"reason":"pad_system_key","bound_ms":12000,"paused_before_ms":1720,"focus_lost_before_ms":1730,'
        '"top_lost_before_ms":-1,"user_leave":false,"interactive":true,"keys":["110:pad:c","96:pad:p"],'
        '"devices":["removed:pad:400"],"outcome":"held","away_ms":2027,"first_frame_ms":180}')


class FakeRecovery:
    def __init__(self):
        self.rows = []

    def _log(self, event, **fields):
        self.rows.append({"event": event, **fields})


def _recovery(root: Path) -> ldr.LinkDropRecovery:
    import inspect
    sig = inspect.signature(ldr.LinkDropRecovery.__init__)
    kwargs = {}
    for name, p in sig.parameters.items():
        if name == "self":
            continue
        if name == "project_root":
            kwargs[name] = root
        elif p.default is inspect.Parameter.empty:
            kwargs[name] = (lambda *a, **k: None)
    return ldr.LinkDropRecovery(**kwargs)


class Parse(unittest.TestCase):
    def test_the_held_row_whole(self):
        row = slr.parse(HELD)
        self.assertEqual(row["outcome"], "held")
        self.assertEqual(row["reason"], "pad_system_key")
        self.assertEqual(row["away_ms"], 2027)
        self.assertEqual(row["keys"], ["110:pad:c", "96:pad:p"])
        self.assertEqual(row["devices"], ["removed:pad:400"])
        self.assertIs(row["interactive"], True)
        self.assertEqual(row["first_frame_ms"], 180)

    def test_junk_and_overlong_give_nothing(self):
        for raw in (None, "", "x", "[]", '{"outcome":"bogus"}', '{"reason":"unknown"}', "{" + "a" * 1100 + "}"):
            self.assertIsNone(slr.parse(raw), raw)

    def test_unknown_keys_text_and_bad_values_dropped(self):
        addr = ".".join(str(x) for x in (10, 0, 0, 1))      # an address-shaped value, built from integers
        row = slr.parse('{"outcome":"restarted","reason":"a name","away_ms":"12","note":"' + addr + '",'
                        '"keys":["110:pad:c","ssid:pad:c",5],"devices":["added:pad:x"],"user_leave":"yes"}')
        self.assertEqual(row["reason"], "unknown")
        self.assertNotIn("away_ms", row)
        self.assertNotIn("note", row)
        self.assertNotIn("user_leave", row)
        self.assertEqual(row["keys"], ["110:pad:c"])
        self.assertEqual(row["devices"], [])
        self.assertNotIn(addr, json.dumps(row))


class Written(unittest.TestCase):
    def test_one_recovery_row_in_the_real_log(self):
        with tempfile.TemporaryDirectory() as d:
            rec = _recovery(Path(d))
            self.assertTrue(slr.note(rec, HELD, 41))
            self.assertFalse(slr.note(rec, "junk", 42))
            lines = [json.loads(x) for x in rec.log_path().read_text().splitlines()]
            self.assertEqual(len(lines), 1)
            r = lines[0]
            self.assertEqual(r["event"], "surface_lost")
            self.assertEqual(r["heartbeat_sequence"], 41)
            self.assertEqual(r["outcome"], "held")
            self.assertEqual(r["away_ms"], 2027)


class TheHandlerBlock(unittest.TestCase):
    """games.py's own `if "surface_lost" in query:` block, run as written with a fake recovery."""

    def _block(self) -> ast.If:
        tree = ast.parse((ROOT / "companion" / "plugins" / "games.py").read_text())
        found = [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test) == "'surface_lost' in query"]
        self.assertEqual(len(found), 1)
        return found[0]

    def _run(self, query: dict) -> list:
        class Self:
            _recovery = FakeRecovery()

            @staticmethod
            def _first(q, key, default=""):
                v = q.get(key)
                return v[0] if v else default
        me = Self()
        code = compile(ast.Module(body=[self._block()], type_ignores=[]), "games_block", "exec")
        exec(code, {}, {"query": query, "self": me, "values": {"sequence": 7}})
        return me._recovery.rows

    def test_the_key_one_row(self):
        rows = self._run({"surface_lost": [HELD], "sequence": ["7"]})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event"], "surface_lost")
        self.assertEqual(rows[0]["heartbeat_sequence"], 7)

    def test_no_key_no_row(self):
        self.assertEqual(self._run({"sequence": ["7"]}), [])

    def test_the_block_sits_after_the_heartbeat_is_written(self):
        src = (ROOT / "companion" / "plugins" / "games.py").read_text()
        self.assertLess(src.index("result = append_native_stream_heartbeat("), src.index('if "surface_lost" in query:'))
        self.assertEqual(src.count("surface_lost_row"), 3)   # the import (twice) and the call


class Absent(unittest.TestCase):
    def test_a_fresh_process_imports_nothing(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys; sys.path.insert(0, 'companion'); import plugins.games; "
                "print('surface_lost_row' in sys.modules)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(out.stdout.strip().splitlines()[-1:], ["False"], out.stderr[-800:])

    def test_the_heartbeat_whitelist_is_unchanged(self):
        src = (ROOT / "companion" / "games" / "native_stream_heartbeat.py").read_text()
        self.assertNotIn("surface_lost", src)


if __name__ == "__main__":
    unittest.main()
