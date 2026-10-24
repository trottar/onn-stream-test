#!/usr/bin/env python3
"""B20: PRIVYHUB_LINK_RECOVERY absent = today. For plugins/games.py, games/emulator_manager.py and tools/e3_state.py:
the whole module's AST with B20's items removed equals the predecessor's. Removed: the assignment `_link_recovery = None`
and each `if` whose test starts with `(os.environ.get('PRIVYHUB_LINK_RECOVERY')`, `_link_recovery is not None` or
`any(x.startswith('PRIVYHUB_LINK_RECOVERY=')`. Absent, each of those tests is false, so nothing is imported, set, logged
or printed. companion/link_recovery.py is new and imported only under them.
    B20_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B20_ROOT", str(HERE.parents[3])))
PREFIXES = ("(os.environ.get('PRIVYHUB_LINK_RECOVERY')", "_link_recovery is not None", "any((x.startswith('PRIVYHUB_LINK_RECOVERY=')")

class Strip(ast.NodeTransformer):
    def __init__(self): self.removed = []
    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if (isinstance(item, ast.If) and ast.unparse(item.test).startswith(PREFIXES)) or (
                            isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name)
                            and item.targets[0].id == "_link_recovery"):
                        self.removed.append(ast.unparse(item).splitlines()[0][:100]); continue
                    if isinstance(item, ast.AST): item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node

out = ["# B20 — absent = today", "", "| file | B20 items removed | AST then = predecessor |", "| --- | --- | --- |"]
ok = True
for rel, pred in (("companion/plugins/games.py", "games.py"), ("companion/games/emulator_manager.py", "emulator_manager.py"),
                  ("tools/e3_state.py", "e3_state.py")):
    s = Strip(); t = s.visit(ast.parse((ROOT / rel).read_text()))
    same = ast.dump(t) == ast.dump(ast.parse((HERE / "predecessors" / pred).read_text()))
    ok &= same and bool(s.removed)
    out.append(f"| `{rel}` | {len(s.removed)}: " + "; ".join(f"`{r}`" for r in s.removed) + f" | **{'identical' if same else 'DIFFERENT'}** |")
out += ["", "`companion/link_recovery.py` is new, imported only under the umbrella's tests "
        "(`tests/link_recovery` `test_absent_nothing_read_nothing_imported`).", "",
        f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**."]
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n")
print("\n".join(out)); sys.exit(0 if ok else 1)
