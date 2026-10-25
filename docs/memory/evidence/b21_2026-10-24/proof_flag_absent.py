#!/usr/bin/env python3
"""B21: PRIVYHUB_LINK_RECOVERY absent = today. plugins/games.py: the whole module's AST with B20's items removed (B20's
stripper: `_link_recovery = None` and each `if` whose test starts with `(os.environ.get('PRIVYHUB_LINK_RECOVERY')` or
`_link_recovery is not None`) equals the predecessor's with the same items removed. Present, the two ASTs differ only
in the row's call (apply -> config_row), listed. companion/link_recovery.py is imported only under the umbrella;
its apply() returns / effects equal the predecessor's (tests/link_recovery/test_config_row.py).
Also: the predecessor's row, reproduced in a fresh process (CL-B12's reading) against the new one.
    B21_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, difflib, json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B21_ROOT", str(HERE.parents[3])))
PREFIXES = ("(os.environ.get('PRIVYHUB_LINK_RECOVERY')", "_link_recovery is not None")

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

new_src = (ROOT / "companion/plugins/games.py").read_text(); old_src = (HERE / "predecessors/games.py").read_text()
s1, s2 = Strip(), Strip()
a = ast.dump(s1.visit(ast.parse(new_src))); b = ast.dump(s2.visit(ast.parse(old_src)))
same = a == b and s1.removed == s2.removed and len(s1.removed) == 3
present = [l for l in difflib.unified_diff(ast.unparse(ast.parse(old_src)).splitlines(), ast.unparse(ast.parse(new_src)).splitlines(), lineterm="", n=0)
           if l[:1] in "+-" and not l.startswith(("+++", "---"))]
CH = """
import sys, os, json, importlib.util
sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location('g', sys.argv[2]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
lr = m._link_recovery
print(json.dumps(lr.config_row(os.environ) if hasattr(lr, 'config_row') else lr.apply(os.environ)))
"""
env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}; env["PRIVYHUB_LINK_RECOVERY"] = "1"
def row(companion_dir, games):
    r = subprocess.run([sys.executable, "-B", "-c", CH, str(companion_dir), str(games)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
    return r.stdout.strip().splitlines()[-1] if r.returncode == 0 else "ERR " + r.stderr[-300:]
# the predecessor's row: a scratch companion dir = the tree's companion with the two predecessor files over it
import shutil, tempfile
tmp = Path(tempfile.mkdtemp(prefix="b21_pred_"))
shutil.copytree(ROOT / "companion", tmp / "companion", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copy(HERE / "predecessors/link_recovery.py", tmp / "companion/link_recovery.py")
shutil.copy(HERE / "predecessors/games.py", tmp / "companion/plugins/games.py")
old_row = row(tmp / "companion", tmp / "companion/plugins/games.py")
new_row = row(ROOT / "companion", ROOT / "companion/plugins/games.py")
out = ["# B21 — absent = today", "",
       f"- `companion/plugins/games.py`, B20's items removed from both: {len(s1.removed)} / {len(s2.removed)} — "
       + "; ".join(f"`{r}`" for r in s1.removed) + f" → **{'identical' if same else 'DIFFERENT'}**.",
       "- Present, the ASTs (unparsed) differ only in:", *[f"  - `{l}`" for l in present],
       "- `companion/link_recovery.py`: imported only under the umbrella (B20's `test_absent_nothing_read_nothing_imported`, "
       "B21's `test_absent_no_row`); `apply` returns / environ effects = the predecessor's (`test_apply_returns_and_effect_equal_the_predecessor`).",
       "", "The row under the umbrella alone, fresh process, the service's import order (`plugins/games.py` → `emulator_manager` first):",
       f"- predecessor (13ccff5; a scratch copy under `/tmp/b21_pred_*`): `{old_row}`",
       f"- B21: `{new_row}`", ""]
ok = same and len(present) == 2 and "config_row" in present[1] and json.loads(new_row)["implied"] and not json.loads(old_row)["implied"]
out.append(f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**.")
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n"); print("\n".join(out)); sys.exit(0 if ok else 1)
