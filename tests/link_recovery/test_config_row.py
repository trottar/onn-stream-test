#!/usr/bin/env python3
"""B21: the `link_recovery_config` row reports the import-time `apply()` (the process's first, whichever import site
ran it), with no second `apply` at the plugin's wire; `reapply` lists what a re-application would add now ([]).

    python3 -m unittest discover -s tests/link_recovery -v

Fresh processes in the service's import order (`plugins/games.py` loaded alone, which imports `emulator_manager`
first; constructing nothing). The row line itself is taken from `GamesPlugin.__init__`'s AST (its
`if _link_recovery is not None:` block) and run against a fake recovery log.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import link_recovery as lr  # noqa: E402

SIX = sorted(lr.STACK)
# B20's apply as at 13ccff5, verbatim (the predecessor; also in evidence/b21_2026-10-24/predecessors/)
PRED_APPLY = '''
def apply(environ):
    add = implied(environ)
    explicit = {k: environ[k] for k in STACK if k in environ and k not in add}
    for k, v in add.items():
        environ.setdefault(k, v)
    return {"umbrella": on(environ), "implied": sorted(add), "explicit": explicit}
'''

CHILD = r"""
import ast, json, os, sys, types, importlib.util
sys.path.insert(0, 'companion')
spec = importlib.util.spec_from_file_location('b21_games', 'companion/plugins/games.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
out = {'imported': 'link_recovery' in sys.modules, 'plugin_has': m._link_recovery is not None}
if m._link_recovery is not None:
    out['row'] = m._link_recovery.config_row(os.environ)
    # the row line itself, from GamesPlugin.__init__
    tree = ast.parse(open('companion/plugins/games.py').read())
    init = next(n for c in tree.body if isinstance(c, ast.ClassDef) and c.name == 'GamesPlugin'
                for n in c.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
    blocks = [n for n in init.body if isinstance(n, ast.If) and ast.unparse(n.test) == '_link_recovery is not None']
    out['blocks'] = len(blocks)
    out['block_src'] = ast.unparse(blocks[0])
    rows = []
    rec = types.SimpleNamespace(_log=lambda event, **kw: rows.append({'event': event, **kw}))
    before = dict(os.environ)
    exec(compile(ast.Module(body=blocks, type_ignores=[]), 'games_init_block', 'exec'),
         {**vars(m), 'self': types.SimpleNamespace(_recovery=rec)})
    out['rows'] = rows
    out['environ_unchanged'] = dict(os.environ) == before
    out['six_in_environ'] = {k: os.environ.get(k) for k in m._link_recovery.STACK}
print(json.dumps(out))
"""


def child(env_extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    env.update(env_extra)
    out = subprocess.run([sys.executable, "-B", "-c", CHILD], cwd=ROOT, env=env, capture_output=True, text=True,
                         timeout=300)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def fresh_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TheRowReportsTheImport(unittest.TestCase):
    def test_umbrella_alone_implied_six_explicit_none(self):
        out = child({"PRIVYHUB_LINK_RECOVERY": "1"})
        want = {"umbrella": True, "implied": SIX, "explicit": {}, "at": "import", "reapply": []}
        self.assertEqual(out["row"], want)
        self.assertEqual(out["blocks"], 1)
        self.assertIn("config_row(os.environ)", out["block_src"])
        self.assertNotIn("apply(", out["block_src"])
        self.assertEqual(out["rows"], [{"event": "link_recovery_config", **want}])
        self.assertTrue(out["environ_unchanged"])
        self.assertEqual(out["six_in_environ"], {k: "1" for k in SIX})

    def test_an_explicit_line_is_explicit(self):
        out = child({"PRIVYHUB_LINK_RECOVERY": "1", "PRIVYHUB_STALL_RESUME": "0"})
        want = {"umbrella": True, "implied": [k for k in SIX if k != "PRIVYHUB_STALL_RESUME"],
                "explicit": {"PRIVYHUB_STALL_RESUME": "0"}, "at": "import", "reapply": []}
        self.assertEqual(out["rows"], [{"event": "link_recovery_config", **want}])
        self.assertEqual(out["six_in_environ"]["PRIVYHUB_STALL_RESUME"], "0")

    def test_the_six_by_hand_are_explicit(self):
        out = child({"PRIVYHUB_LINK_RECOVERY": "1", **{k: "1" for k in SIX}})
        self.assertEqual(out["row"], {"umbrella": True, "implied": [], "explicit": {k: "1" for k in SIX},
                                      "at": "import", "reapply": []})

    def test_umbrella_not_one_implies_nothing(self):
        out = child({"PRIVYHUB_LINK_RECOVERY": "0"})
        self.assertEqual(out["row"], {"umbrella": False, "implied": [], "explicit": {}, "at": "import",
                                      "reapply": []})
        self.assertEqual(out["six_in_environ"], {k: None for k in SIX})

    def test_absent_no_row(self):
        out = child({})
        self.assertEqual(out, {"imported": False, "plugin_has": False})


class InProcess(unittest.TestCase):
    def setUp(self):
        self.m = fresh_module(ROOT / "companion" / "link_recovery.py", "b21_lr")

    def test_first_is_kept_once(self):
        env = {"PRIVYHUB_LINK_RECOVERY": "1"}
        first = self.m.apply(env)
        self.assertEqual(first["implied"], SIX)
        self.assertEqual(self.m.apply(env)["implied"], [])
        self.assertEqual(self.m.apply(env)["implied"], [])
        row = self.m.config_row(env)
        self.assertEqual((row["implied"], row["explicit"], row["at"], row["reapply"]), (SIX, {}, "import", []))

    def test_config_row_writes_nothing(self):
        env = {"PRIVYHUB_LINK_RECOVERY": "1"}
        row = self.m.config_row(env)
        self.assertEqual(env, {"PRIVYHUB_LINK_RECOVERY": "1"})
        self.assertEqual(row, {"umbrella": True, "implied": SIX, "explicit": {}, "at": "none", "reapply": SIX})

    def test_reapply_names_a_change_after_import(self):
        env = {"PRIVYHUB_LINK_RECOVERY": "1"}
        self.m.apply(env)
        del env["PRIVYHUB_STALL_SIGNAL"]
        self.assertEqual(self.m.config_row(env)["reapply"], ["PRIVYHUB_STALL_SIGNAL"])

    def test_apply_returns_and_effect_equal_the_predecessor(self):
        ns = {"implied": lr.implied, "on": lr.on, "STACK": lr.STACK}
        exec(PRED_APPLY, ns)
        pred = type("Pred", (), {"apply": staticmethod(ns["apply"])})
        for start in ({}, {"PRIVYHUB_LINK_RECOVERY": "1"}, {"PRIVYHUB_LINK_RECOVERY": "1", "PRIVYHUB_INPUT_HOLD": "0"},
                      {"PRIVYHUB_LINK_RECOVERY": "0"}, {"PRIVYHUB_LINK_RECOVERY": " 1 "},
                      {"PRIVYHUB_LINK_RECOVERY": "1", **{k: "1" for k in SIX}}):
            a, b = dict(start), dict(start)
            for _ in range(3):
                self.assertEqual(self.m.apply(a), pred.apply(b), start)
                self.assertEqual(a, b, start)


if __name__ == "__main__":
    unittest.main()
