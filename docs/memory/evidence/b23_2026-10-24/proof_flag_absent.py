#!/usr/bin/env python3
"""B23: PRIVYHUB_LINK_RECOVERY_WAN absent = today. plugins/games.py's whole AST with B23's items removed equals the
predecessor's (HEAD 13ccff5 + B21 + B22). Removed: `_link_recovery_wan = None` and each `if` whose test starts with
`(os.environ.get('PRIVYHUB_LINK_RECOVERY_WAN')` or `_link_recovery_wan is not None` (none has an else). Absent, each
test is false. companion/link_recovery_wan.py is new and imported only under the flag; no other file changed by B23.
    B23_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B23_ROOT", str(HERE.parents[3])))
PREFIXES = ("(os.environ.get('PRIVYHUB_LINK_RECOVERY_WAN')", "_link_recovery_wan is not None")

class Strip(ast.NodeTransformer):
    def __init__(self): self.removed = []; self.with_else = 0
    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if isinstance(item, ast.If) and ast.unparse(item.test).startswith(PREFIXES):
                        self.removed.append(ast.unparse(item.test)[:110]); self.with_else += bool(item.orelse); continue
                    if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name) \
                            and item.targets[0].id == "_link_recovery_wan":
                        self.removed.append(ast.unparse(item)[:100]); continue
                    if isinstance(item, ast.AST): item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node

s = Strip(); t = s.visit(ast.parse((ROOT / "companion/plugins/games.py").read_text()))
same = ast.dump(t) == ast.dump(ast.parse((HERE / "predecessors/games.py").read_text()))
others = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "companion/native_stream.py", "companion/input_hold.py",
                         "companion/hold_tuning.py", "companion/stall_signal.py", "companion/stall_owner.py",
                         "companion/rewind_cores.py", "companion/remote_ladder.py", "companion/overlay"],
                        cwd=ROOT, capture_output=True, text=True).stdout.strip()
ok = same and len(s.removed) == 4 and s.with_else == 0 and not others
out = ["# B23 — absent = today", "",
       f"- `companion/plugins/games.py`: {len(s.removed)} B23 items removed — " + "; ".join(f"`{r}`" for r in s.removed)
       + f" (with an else: {s.with_else}) → AST **{'identical' if same else 'DIFFERENT'}** to the predecessor's (HEAD + B21 + B22).",
       f"- the modules B23 sets or reads (`input_hold`, `hold_tuning`, `stall_signal`, `stall_owner`, `rewind_cores`, "
       f"`remote_ladder`, `overlay/`, `native_stream`): `git diff HEAD` {'empty' if not others else 'NOT EMPTY: ' + others}.",
       "- `companion/link_recovery_wan.py`: new, imported only under the flag (`tests/link_recovery_wan` `test_nothing_imported`).",
       "", f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**."]
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n"); print("\n".join(out)); sys.exit(0 if ok else 1)
