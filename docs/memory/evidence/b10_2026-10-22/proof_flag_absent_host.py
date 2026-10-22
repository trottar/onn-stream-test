#!/usr/bin/env python3
"""B10 (host): PRIVYHUB_LOSS_GUARD absent = the predecessors byte for byte. For each changed companion file, the WHOLE
module's AST with the B10 items removed equals the predecessor's (native_session_io.py, native_stream_heartbeat.py:
HEAD 0f4b551; plugins/games.py: B8's). Removed: each `if` whose test starts with a B10 guard, the module-level
`_keyframe_request` / `_LOSS_GUARD_FIELDS` / `LOSS_GUARD_FIELDS` assignments, the additive class attribute
`_keyframe_request` and the new method `set_keyframe_request`. Writes proof_flag_absent_host.md.

    B10_ROOT=<a copy holding companion/> python3 -B proof_flag_absent_host.py
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B10_ROOT", str(HERE.parents[3])))
FILES = ("companion/native_session_io.py", "companion/plugins/games.py", "companion/games/native_stream_heartbeat.py")
GUARD_PREFIXES = (
    "self._keyframe_request is not None",
    "_keyframe_request is not None",
    "_LOSS_GUARD_FIELDS is not None",
    "LOSS_GUARD_FIELDS is not None",
    "(os.environ.get('PRIVYHUB_LOSS_GUARD') or '').strip()",
)
ADDED_ATTRS = {"_keyframe_request"}
ADDED_NAMES = {"_keyframe_request", "_LOSS_GUARD_FIELDS", "LOSS_GUARD_FIELDS"}
ADDED_FUNCS = {"set_keyframe_request"}


def is_item(node: ast.AST) -> bool:
    if isinstance(node, ast.If):
        return ast.unparse(node.test).startswith(GUARD_PREFIXES)
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id in ADDED_NAMES
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id in ADDED_ATTRS
    if isinstance(node, ast.FunctionDef):
        return node.name in ADDED_FUNCS
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
                        self.removed.append(ast.unparse(item).splitlines()[0][:100])
                        continue
                    if isinstance(item, ast.AST):
                        item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node


def main() -> int:
    lines = ["# B10 (host) — flag absent = the predecessors (whole-module AST, B10 items removed)", "",
             "| file | B10 items removed | whole module vs predecessor |", "| --- | --- | --- |"]
    ok_all = True
    for rel in FILES:
        new = ast.parse((ROOT / rel).read_text())
        old = ast.parse((HERE / "predecessors" / rel).read_text())
        s = Strip()
        same = ast.dump(s.visit(new)) == ast.dump(old)
        ok_all &= same
        lines.append(f"| `{rel}` | {len(s.removed)}: {'; '.join(f'`{r}`' for r in s.removed)} | "
                     f"**{'identical' if same else 'DIFFERENT'}** |")
    lines += ["", f"Result: **{'ALL IDENTICAL' if ok_all else 'NOT IDENTICAL'}**.", "",
              "New file `companion/keyframe_request.py` is imported only with `PRIVYHUB_LOSS_GUARD` set; "
              "`tests/keyframe_request` FlagAbsent: a fresh process has no `keyframe_request` in `sys.modules`, the "
              "bridge's attribute and `LOSS_GUARD_FIELDS` are None; a `PHK1` datagram is a bad packet as today."]
    (HERE / "proof_flag_absent_host.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
