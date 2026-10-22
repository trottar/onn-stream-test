#!/usr/bin/env python3
"""B3: flag absent = today, host side. For each function holding a B3 guarded statement, its AST with those
statements removed equals the predecessor's (predecessors/: HEAD's client_feedback / stream_telemetry /
native_stream_heartbeat, B2's plugins/games.py). Additive: the flags, `_normalize_link`, `_link_telemetry`,
`LINK_FIELDS`, one `import os` each in three modules. Writes proof_flag_absent.md.

    B3_ROOT=<a copy holding companion/> python3 -B proof_flag_absent.py
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B3_ROOT", str(HERE.parents[3])))
B3_TESTS = ("_LINK_REPORT and isinstance(root.get('link'), dict)", "_LINK_REPORT and isinstance(report.get('link'), dict)",
            "LINK_FIELDS is not None", "_LINK_FIELDS is not None")


class Strip(ast.NodeTransformer):
    def visit_If(self, node):
        self.generic_visit(node)
        return None if ast.unparse(node.test) in B3_TESTS else node


def fdefs(src):
    return {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


def holders(src):
    return [n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)
            and any(isinstance(x, ast.If) and ast.unparse(x.test) in B3_TESTS for x in ast.walk(n))]


def dump(src, name):
    return [ast.dump(n) for n in ast.walk(Strip().visit(ast.parse(src))) if isinstance(n, ast.FunctionDef) and n.name == name]


FILES = {"companion/diagnostics/client_feedback.py": "companion_diagnostics_client_feedback.py",
         "companion/diagnostics/stream_telemetry.py": "companion_diagnostics_stream_telemetry.py",
         "companion/games/native_stream_heartbeat.py": "companion_games_native_stream_heartbeat.py",
         "companion/plugins/games.py": "companion_plugins_games.py"}
lines = ["# B3 flag absent (host): the hooked functions, B3's guarded statements removed, against the predecessors", "",
         "| file | function | identical | new definitions (additive) |", "| --- | --- | --- | --- |"]
ok = True
for rel, pred in FILES.items():
    now, before = (ROOT / rel).read_text(), (HERE / "predecessors" / pred).read_text()
    new = sorted(fdefs(now) - fdefs(before))
    for name in [h for h in holders(now) if h in fdefs(before)]:
        same = dump(now, name) == dump(before, name) and bool(dump(before, name))
        ok &= same
        lines.append(f"| `{rel}` | `{name}` | {'**identical**' if same else 'DIFFERS'} | {', '.join(new) or '—'} |")
lines += ["", f"**{'MET' if ok else 'NOT MET'}**"]
(HERE / "proof_flag_absent.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
raise SystemExit(0 if ok else 1)
