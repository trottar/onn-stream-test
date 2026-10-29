#!/usr/bin/env python3
"""B28: PRIVYHUB_REMOTE absent = today, byte for byte. plugins/games.py's whole AST with B28's three items removed
equals HEAD's (42a2ab6): the assignment `_remote_umbrella = None`, the `if` whose test starts with
`(os.environ.get('PRIVYHUB_REMOTE')`, and each `if` whose test starts with `_remote_umbrella is not None` (no else).
Absent, each test is false. companion/remote_umbrella.py is new and imported only under the line; every module it
touches is byte-identical to HEAD.
    B28_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, hashlib, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B28_ROOT", str(HERE.parents[3])))
PREFIXES = ("(os.environ.get('PRIVYHUB_REMOTE')", "_remote_umbrella is not None")

class Strip(ast.NodeTransformer):
    def __init__(self): self.removed = []; self.with_else = 0
    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if isinstance(item, ast.If) and ast.unparse(item.test).startswith(PREFIXES):
                        self.removed.append(ast.unparse(item.test)[:90]); self.with_else += bool(item.orelse); continue
                    if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name) \
                            and item.targets[0].id == "_remote_umbrella":
                        self.removed.append(ast.unparse(item)[:90]); continue
                    if isinstance(item, ast.AST): item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node

s = Strip(); t = s.visit(ast.parse((ROOT / "companion/plugins/games.py").read_text()))
same = ast.dump(t) == ast.dump(ast.parse((HERE / "predecessors/games.py").read_text()))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
mods = ("start_rung.py", "remote_ladder.py", "remote_cap.py", "wan_telemetry.py", "link_recovery_wan.py",
        "adaptive_bitrate_live.py", "native_stream.py", "privyhub_service.py")
ident = {m: sha(ROOT / "companion" / m) == sha(HERE / "predecessors" / m) for m in mods}
git = subprocess.run(["git", "diff", "--stat", "HEAD", "--"] + [f"companion/{m}" for m in mods]
                     + ["companion/diagnostics/c3_linux_actuator_probe.py"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
ok = same and len(s.removed) == 4 and s.with_else == 0 and all(ident.values()) and not git
out = ["# B28 — `PRIVYHUB_REMOTE` absent = today", "",
       f"- `companion/plugins/games.py`: {len(s.removed)} B28 items removed — " + "; ".join(f"`{r}`" for r in s.removed)
       + f" (with an else: {s.with_else}) → AST **{'identical' if same else 'DIFFERENT'}** to HEAD 42a2ab6's.",
       *[f"- `companion/{m}`: sha256 **{'identical' if v else 'DIFFERENT'}** to HEAD's." for m, v in ident.items()],
       f"- those and the actuator probe: `git diff HEAD` {'empty' if not git else 'NOT EMPTY: ' + git}.",
       "- `companion/remote_umbrella.py`: new, imported only when `PRIVYHUB_REMOTE` reads `1` "
       "(`tests/remote_umbrella` `test_nothing_imported_without_the_line`: absent, `0`, `yes` → not imported).",
       "- With the line, a LAN-class session: every hook's global None (today's code path); "
       "`test_a_lan_session_is_todays_in_every_reader` (argv and ladder rows field for field as with no umbrella).", "",
       f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**."]
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n"); print("\n".join(out)); sys.exit(0 if ok else 1)
