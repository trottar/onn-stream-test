#!/usr/bin/env python3
"""B16 (host): against HEAD efa4240 (predecessors/).
1. plugins/games.py: the WHOLE module's AST with B16's one item removed (the `if` whose test is
   `getattr(self._recovery, '_stall_owner', None) is not None`) equals the predecessor's. With PRIVYHUB_STALL_RESUME absent the plugin
   never imports stall_owner and LinkDropRecovery's class attribute `_stall_owner` stays None (B12), so the `if` is
   false and the start response carries no `stall_resume` key: byte for byte.
2. stall_owner.py (B12's module, imported only with PRIVYHUB_STALL_RESUME=1 and the stall signal): listed, not
   claimed identical -- the save from the signal (age >= threshold, synchronous before B7's pause), v2's newest-datagram
   rule, `client_hint`, the config row's three fields, the docstring.

    B16_ROOT=<a copy holding companion/> python3 -B proof_flag_absent_host.py
"""
from __future__ import annotations

import ast
import difflib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B16_ROOT", str(HERE.parents[3])))
GUARD = "getattr(self._recovery, '_stall_owner', None) is not None"


class Strip(ast.NodeTransformer):
    def __init__(self):
        self.removed = []

    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if isinstance(item, ast.If) and ast.unparse(item.test) == GUARD:
                        self.removed.append(ast.unparse(item).replace("\n", " | ")[:140])
                        continue
                    if isinstance(item, ast.AST):
                        item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node


def dump(src):
    return ast.dump(ast.parse(src), include_attributes=False)


out = ["# B16 (host) — the flags absent = HEAD efa4240", ""]
new = (ROOT / "companion/plugins/games.py").read_text()
old = (HERE / "predecessors/games.py").read_text()
s = Strip()
tree = s.visit(ast.parse(new))
same = ast.dump(tree, include_attributes=False) == dump(old)
out += ["| file | B16 items removed | the module's AST then = HEAD's |", "| --- | --- | --- |",
        f"| `companion/plugins/games.py` | {len(s.removed)}: `{s.removed[0] if s.removed else ''}` | "
        f"**{'identical' if same else 'DIFFERENT'}** |", ""]
so_new = (ROOT / "companion/stall_owner.py").read_text().splitlines()
so_old = (HERE / "predecessors/stall_owner.py").read_text().splitlines()
diff = list(difflib.unified_diff(so_old, so_new, "a/companion/stall_owner.py", "b/companion/stall_owner.py",
                                 lineterm="", n=0))
plus = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
minus = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
out += [f"`companion/stall_owner.py` (B12's module, imported only with the flag): +{plus} −{minus}, listed:", "",
        "```diff"] + diff + ["```", "", f"Result: **{'PROVEN' if same and len(s.removed) == 1 else 'NOT PROVEN'}** "
        "(the plugin byte for byte without the flags; the module is not imported without them — "
        "`tests/stall_owner` `test_not_imported_absent`)."]
(HERE / "proof_flag_absent_host.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:6]))
sys.exit(0 if same and len(s.removed) == 1 else 1)
