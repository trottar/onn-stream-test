#!/usr/bin/env python3
"""B9 (host): what B9 changes against B8's tree (predecessors/).
1. hold_rewind.py, input_hold.py: the WHOLE module's AST with the B9 items removed equals the predecessor's. Removed:
   each `if` whose test starts with a B9 guard, the additive class attributes `b9` / `state_mark`.
2. stall_signal.py: the WHOLE module's AST equals the predecessor's once two nodes take the predecessor's values: the
   module docstring and `DEFAULT_MS`'s value (B9's one intended change: `1` = 400). Nothing else differs.
Flag absent (PRIVYHUB_INPUT_HOLD_REWIND / PRIVYHUB_STALL_SIGNAL unset): neither module is imported (B4's and B7's own
FlagAbsent tests); `rewind_cores` is imported only for `1` / `state` (tests/rewind_cores FlagAbsent).

    B9_ROOT=<a copy holding companion/> python3 -B proof_flag_absent_host.py
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B9_ROOT", str(HERE.parents[3])))
GUARDED = ("companion/hold_rewind.py", "companion/input_hold.py")
GUARD_PREFIXES = (
    "raw in ('all', 'state')",
    "(environ.get(FLAG_ENV) or '').strip() in ('1', 'state')",
    "self.b9 is not None",
    "self.state_mark is not None",
)
ADDED_ATTRS = {"b9", "state_mark"}


def is_item(node):
    if isinstance(node, ast.If):
        return ast.unparse(node.test).startswith(GUARD_PREFIXES)
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


def main() -> int:
    lines = ["# B9 (host) — against B8's tree (predecessors/)", "",
             "| file | method | B9 items | whole module vs predecessor |", "| --- | --- | --- | --- |"]
    ok = True
    for rel in GUARDED:
        new, old = ast.parse((ROOT / rel).read_text()), ast.parse((HERE / "predecessors" / rel).read_text())
        s = Strip()
        same = ast.dump(s.visit(new)) == ast.dump(old)
        ok &= same
        lines.append(f"| `{rel}` | guarded items removed | {len(s.removed)}: {'; '.join(f'`{r}`' for r in s.removed)} | "
                     f"**{'identical' if same else 'DIFFERENT'}** |")
    rel = "companion/stall_signal.py"
    new, old = ast.parse((ROOT / rel).read_text()), ast.parse((HERE / "predecessors" / rel).read_text())
    changed = []
    if ast.dump(new.body[0]) != ast.dump(old.body[0]):
        changed.append("the module docstring")
        new.body[0] = old.body[0]
    for i, n in enumerate(new.body):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DEFAULT_MS" for t in n.targets):
            o = [m for m in old.body if isinstance(m, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "DEFAULT_MS" for t in m.targets)][0]
            changed.append(f"DEFAULT_MS {ast.unparse(o.value)} -> {ast.unparse(n.value)}")
            new.body[i] = o
    same = ast.dump(new) == ast.dump(old)
    ok &= same
    lines.append(f"| `{rel}` | two nodes set back | {'; '.join(changed)} | **{'identical' if same else 'DIFFERENT'}** |")
    lines += ["", f"Result: **{'ALL IDENTICAL' if ok else 'NOT IDENTICAL'}** (beyond the stated changes)."]
    (HERE / "proof_flag_absent_host.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
