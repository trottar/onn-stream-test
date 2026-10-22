#!/usr/bin/env python3
"""B2: flag absent = today. For each function holding a B2 statement, its AST with the guarded B2 statements removed
equals the predecessor's (predecessors/: B1's edited native_session_io.py and plugins/games.py, HEAD's
link_drop_recovery.py); the other changes are additive (a class attribute, a setter, two recovery methods, a constant,
a guarded import). Writes proof_flag_absent.md.

    B2_ROOT=<a copy holding companion/> python3 -B proof_flag_absent.py
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B2_ROOT", str(HERE.parents[3])))
B2_TESTS = ("self._input_hold is not None", "_input_hold is not None")


def is_b2(node: ast.If) -> bool:
    t = ast.unparse(node.test)
    return t in B2_TESTS or ("INPUT_HOLD" in t and "_last_desync_reason" in t and "trigger != INPUT_HOLD" in t)


class Strip(ast.NodeTransformer):
    def visit_If(self, node):
        self.generic_visit(node)
        return None if is_b2(node) else node


def holders(src: str) -> list[str]:
    out = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and any(isinstance(x, ast.If) and is_b2(x) for x in ast.walk(n)):
            out.append(n.name)
    return out


def dump(src: str, name: str) -> list[str]:
    tree = Strip().visit(ast.parse(src))
    return [ast.dump(n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]


def defs(src: str) -> set[str]:
    return {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


FILES = {"companion/native_session_io.py": "companion_native_session_io.py",
         "companion/plugins/games.py": "companion_plugins_games.py",
         "companion/games/link_drop_recovery.py": "companion_games_link_drop_recovery.py"}
lines = ["# B2 flag absent: the hooked functions, B2's guarded statements removed, against the predecessors", "",
         "| file | function | identical | new definitions (additive) |", "| --- | --- | --- | --- |"]
ok = True
for rel, pred in FILES.items():
    now, before = (ROOT / rel).read_text(), (HERE / "predecessors" / pred).read_text()
    new = sorted(defs(now) - defs(before))
    for name in [h for h in holders(now) if h in defs(before)]:   # a new function is additive, listed on the right
        same = dump(now, name) == dump(before, name) and bool(dump(before, name))
        ok &= same
        lines.append(f"| `{rel}` | `{name}` | {'**identical**' if same else 'DIFFERS'} | {', '.join(new) or '—'} |")
lines += ["", f"**{'MET' if ok else 'NOT MET'}**"]
(HERE / "proof_flag_absent.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
raise SystemExit(0 if ok else 1)
