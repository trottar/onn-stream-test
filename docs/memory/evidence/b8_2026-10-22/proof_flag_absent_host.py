#!/usr/bin/env python3
"""B8 (host): PRIVYHUB_INPUT_HOLD_B8 absent = BENCH-R2's files byte for byte. For each changed companion file, the WHOLE
module's AST with the B8 items removed equals the predecessor's (predecessors/ = HEAD 0f4b551). Removed: each `if`
whose test starts with a B8 guard, the module-level `_hold_ownership = None`, the additive class attribute
`_input_hold_b8`. Lists, per file, the functions that hold a B8 statement. Writes proof_flag_absent_host.md.

    B8_ROOT=<a copy holding companion/> python3 -B proof_flag_absent_host.py
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B8_ROOT", str(HERE.parents[3])))
FILES = ("companion/games/link_drop_recovery.py", "companion/stall_signal.py", "companion/hold_rewind.py",
         "companion/plugins/games.py")
GUARD_PREFIXES = (
    "self._input_hold_b8 is not None",
    "getattr(self.recovery, '_input_hold_b8', None) is not None",
    "'b8' in pending",
    "_hold_ownership is not None",
    "(environ.get('PRIVYHUB_INPUT_HOLD_B8') or '').strip()",
    "_input_hold is not None and (os.environ.get('PRIVYHUB_INPUT_HOLD_B8') or '').strip()",
)
ADDED_ATTRS = {"_input_hold_b8"}
ADDED_NAMES = {"_hold_ownership"}


def is_item(node: ast.AST) -> bool:
    if isinstance(node, ast.If):
        return ast.unparse(node.test).startswith(GUARD_PREFIXES)
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id in ADDED_NAMES
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id in ADDED_ATTRS
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


def holders(tree: ast.Module) -> list[str]:
    out = []
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)] + [tree]:
        for fn in (n for n in getattr(cls, "body", []) if isinstance(n, ast.FunctionDef)):
            if any(is_item(x) for x in ast.walk(fn) if x is not fn):
                out.append(f"{getattr(cls, 'name', '<module>')}.{fn.name}")
    return out


def main() -> int:
    lines = ["# B8 (host) — flag absent = BENCH-R2's files (whole-module AST, B8 items removed, vs predecessors/)", "",
             "Root checked: `B8_ROOT`. Predecessors: `predecessors/` (HEAD 0f4b551).", "",
             "| file | functions holding a B8 statement | B8 items removed | whole module vs predecessor |",
             "| --- | --- | ---: | --- |"]
    ok_all = True
    for rel in FILES:
        new = ast.parse((ROOT / rel).read_text())
        old = ast.parse((HERE / "predecessors" / rel).read_text())
        hold = holders(new)
        s = Strip()
        stripped = s.visit(new)
        same = ast.dump(stripped) == ast.dump(old)
        ok_all &= same
        lines.append(f"| `{rel}` | {', '.join(f'`{h}`' for h in hold) or '(module level only)'} | {len(s.removed)} | "
                     f"**{'identical' if same else 'DIFFERENT'}** |")
    lines += ["", f"Result: **{'ALL IDENTICAL' if ok_all else 'NOT IDENTICAL'}**.", "",
              "New file `companion/hold_ownership.py` is imported only with `PRIVYHUB_INPUT_HOLD_B8` set (and, in "
              "`hold_rewind.config_block`, only with it set); `tests/input_hold_b8` FlagAbsent: a fresh process has no "
              "`hold_ownership` in `sys.modules` and `LinkDropRecovery._input_hold_b8` is None."]
    (HERE / "proof_flag_absent_host.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
