#!/usr/bin/env python3
"""B14 (host): PRIVYHUB_LINK_REPORT absent = the predecessors byte for byte, and with it set an older client's
heartbeat (no `link_notice` key) records nothing new. plugins/games.py (vs B12's) and games/native_stream_heartbeat.py
(vs HEAD 3eb900c): the WHOLE module's AST with the B14 items removed equals the predecessor's. Removed: each `if`
whose test starts with a B14 guard, `_link_notice = None`. Every B14 statement is guarded by `_link_notice is not None`
(imported only with PRIVYHUB_LINK_REPORT=1) or by `'link_notice' in values` (a key only the notice's client sends).
    B14_ROOT=<a copy holding companion/> python3 -B proof_flag_absent_host.py"""
from __future__ import annotations

import ast
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B14_ROOT", str(HERE.parents[3])))
FILES = ("companion/plugins/games.py", "companion/games/native_stream_heartbeat.py")
GUARDS = ("_link_notice is not None", "'link_notice' in values", "(os.environ.get('PRIVYHUB_LINK_REPORT') or '').strip() == '1'")


def is_item(node):
    if isinstance(node, ast.If):
        t = ast.unparse(node.test)
        if t.startswith(GUARDS[2]):
            return "import link_notice" in ast.unparse(node)
        return t.startswith(GUARDS[:2])
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id == "_link_notice"
    return False


class Strip(ast.NodeTransformer):
    def __init__(self):
        self.removed = []

    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if isinstance(item, ast.AST) and is_item(item):
                        self.removed.append(ast.unparse(item).splitlines()[0][:90])
                        continue
                    if isinstance(item, ast.AST):
                        item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                setattr(node, field, self.visit(value))
        return node


lines = ["# B14 (host) — flag absent = the predecessors (whole-module AST, B14 items removed)", "",
         "| file | B14 items removed | whole module vs predecessor |", "| --- | --- | --- |"]
ok = True
for rel in FILES:
    new, old = ast.parse((ROOT / rel).read_text()), ast.parse((HERE / "predecessors" / rel).read_text())
    s = Strip()
    same = ast.dump(s.visit(new)) == ast.dump(old)
    ok &= same
    lines.append(f"| `{rel}` | {len(s.removed)}: {'; '.join(f'`{r}`' for r in s.removed)} | **{'identical' if same else 'DIFFERENT'}** |")
lines += ["", f"Result: **{'ALL IDENTICAL' if ok else 'NOT IDENTICAL'}**. New file `companion/link_notice.py` is imported only "
          "with `PRIVYHUB_LINK_REPORT=1` (`tests/link_notice` FlagAbsent)."]
(HERE / "proof_flag_absent_host.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
raise SystemExit(0 if ok else 1)
