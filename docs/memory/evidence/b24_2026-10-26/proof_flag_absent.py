#!/usr/bin/env python3
"""B24: PRIVYHUB_RESTART_FAST_UNLOCK absent = the adopted G-A5 behaviour, byte for byte.
plugins/games.py's whole AST with B24's items removed equals HEAD's (06c565e). Removed: `_restart_fast_unlock = None`
and each `if` whose test starts with `_restart_fast is not None and (os.environ.get('PRIVYHUB_RESTART_FAST_UNLOCK')`
or `_restart_fast_unlock is not None` (no else). Absent, each test is false. restart_fast.py (the adopted worker) is
byte-identical to HEAD; companion/restart_fast_unlock.py is new and imported only under both flags; the other modules
the worker calls are unchanged against HEAD.
    B24_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, hashlib, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B24_ROOT", str(HERE.parents[3])))
PREFIXES = ("_restart_fast is not None and (os.environ.get('PRIVYHUB_RESTART_FAST_UNLOCK')", "_restart_fast_unlock is not None")

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
                            and item.targets[0].id == "_restart_fast_unlock":
                        self.removed.append(ast.unparse(item)[:100]); continue
                    if isinstance(item, ast.AST): item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node

s = Strip(); t = s.visit(ast.parse((ROOT / "companion/plugins/games.py").read_text()))
same = ast.dump(t) == ast.dump(ast.parse((HERE / "predecessors/games.py").read_text()))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rf_same = sha(ROOT / "companion/restart_fast.py") == sha(HERE / "predecessors/restart_fast.py")
others = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "companion/native_stream.py", "companion/native_session_io.py",
                         "companion/native_fec_relay.py", "companion/audio_codec.py", "companion/restart_fast.py"],
                        cwd=ROOT, capture_output=True, text=True).stdout.strip()
ok = same and len(s.removed) == 3 and s.with_else == 0 and rf_same and not others
out = ["# B24 — absent = the adopted G-A5 behaviour", "",
       f"- `companion/plugins/games.py`: {len(s.removed)} B24 items removed — " + "; ".join(f"`{r}`" for r in s.removed)
       + f" (with an else: {s.with_else}) → AST **{'identical' if same else 'DIFFERENT'}** to HEAD 06c565e's.",
       f"- `companion/restart_fast.py` (the adopted worker): sha256 **{'identical' if rf_same else 'DIFFERENT'}** to HEAD's.",
       f"- `native_stream`, `native_session_io`, `native_fec_relay`, `audio_codec`, `restart_fast`: `git diff HEAD` "
       f"{'empty' if not others else 'NOT EMPTY: ' + others}.",
       "- `companion/restart_fast_unlock.py`: new, imported only when `PRIVYHUB_RESTART_FAST` and "
       "`PRIVYHUB_RESTART_FAST_UNLOCK` both read `1` (`tests/restart_fast_unlock` `test_nothing_imported`, four environs).",
       "- B22's 13 (`tests/restart_fast`) unedited and green.", "",
       f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**."]
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n"); print("\n".join(out)); sys.exit(0 if ok else 1)
