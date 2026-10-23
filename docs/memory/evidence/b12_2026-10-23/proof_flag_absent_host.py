#!/usr/bin/env python3
"""B12 (host): against HEAD 3eb900c (predecessors/).
1. link_drop_recovery.py, stall_signal.py, plugins/games.py: the WHOLE module's AST with the B12 items removed equals
   the predecessor's. Removed: each `if` whose test starts with a B12 guard, `_stall_owner = None`, the class attribute
   `_stall_owner`. PRIVYHUB_STALL_RESUME absent: stall_owner is never imported (tests/stall_owner FlagAbsent).
2. hold_rewind.py: the same with the added `if raw == 'rewind'` removed AND B9's two routing tuples set back from
   ('1', 'state', 'rewind') to ('1', 'state') -- the stated change (`rewind` routed through rewind_cores).
3. rewind_cores.py (B9's module, imported only with PRIVYHUB_INPUT_HOLD_REWIND set): listed, not claimed identical --
   `1` now maps to `state`, `rewind` to the allow-list; saves carry a `kind`; a stall save matches within 100 ms;
   the mark is set only on a detector with `on_quiet`.

    B12_ROOT=<a copy holding companion/> python3 -B proof_flag_absent_host.py
"""
from __future__ import annotations

import ast
import difflib
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B12_ROOT", str(HERE.parents[3])))
FILES = ("companion/games/link_drop_recovery.py", "companion/stall_signal.py", "companion/plugins/games.py",
         "companion/hold_rewind.py")
GUARD_PREFIXES = ("self._stall_owner is not None", "getattr(self.recovery, '_stall_owner', None) is not None",
                  "_stall_owner is not None", "(os.environ.get('PRIVYHUB_STALL_RESUME') or '').strip()",
                  "raw == 'rewind'")
ADDED = {"_stall_owner"}


def is_item(node):
    if isinstance(node, ast.If):
        return ast.unparse(node.test).startswith(GUARD_PREFIXES)
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id in ADDED
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id in ADDED
    return False


class Strip(ast.NodeTransformer):
    def __init__(self):
        self.removed, self.set_back = [], 0

    def visit_Tuple(self, node):
        if [getattr(e, "value", None) for e in node.elts] == ["1", "state", "rewind"]:
            node.elts = node.elts[:2]
            self.set_back += 1
        return node

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


def main() -> int:
    lines = ["# B12 (host) — against HEAD 3eb900c (predecessors/)", "",
             "| file | B12 items removed | tuples set back | whole module vs predecessor |", "| --- | --- | ---: | --- |"]
    ok = True
    for rel in FILES:
        new, old = ast.parse((ROOT / rel).read_text()), ast.parse((HERE / "predecessors" / rel).read_text())
        s = Strip()
        same = ast.dump(s.visit(new)) == ast.dump(old)
        ok &= same
        lines.append(f"| `{rel}` | {len(s.removed)}: {'; '.join(f'`{r}`' for r in s.removed)} | {s.set_back} | "
                     f"**{'identical' if same else 'DIFFERENT'}** |")
    rel = "companion/rewind_cores.py"
    d = [l for l in difflib.unified_diff((HERE / "predecessors" / rel).read_text().splitlines(),
                                         (ROOT / rel).read_text().splitlines(), lineterm="", n=0)
         if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    lines += ["", f"Result: **{'ALL IDENTICAL' if ok else 'NOT IDENTICAL'}** (beyond the stated tuples).", "",
              f"`{rel}` (B9's module; not imported without PRIVYHUB_INPUT_HOLD_REWIND): {len(d)} changed lines, all "
              "listed:", "", "```"] + d + ["```"]
    (HERE / "proof_flag_absent_host.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:10]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
