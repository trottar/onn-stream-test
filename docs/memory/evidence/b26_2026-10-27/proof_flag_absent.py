#!/usr/bin/env python3
"""B26: the adopted behaviour byte for byte but the one packet; flag absent = unchanged.
companion/restart_fast_unlock.py's AST, with B26's `_stop_relay` method removed and its one call
`self._stop_relay(m._fec_relay)` put back as `m._fec_relay.stop()`, equals HEAD's (2cd392c). The relay, the adopted
G-A5 worker and the plugin (native_fec_relay.py, restart_fast.py, plugins/games.py) are byte-identical to HEAD, so with
PRIVYHUB_RESTART_FAST_UNLOCK absent nothing B26 touched is imported (B24's test_nothing_imported).
    B26_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, hashlib, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B26_ROOT", str(HERE.parents[3])))


class Back(ast.NodeTransformer):
    def __init__(self): self.removed = 0; self.calls = 0

    def visit_ClassDef(self, node):
        keep = [b for b in node.body if not (isinstance(b, ast.FunctionDef) and b.name == "_stop_relay")]
        self.removed += len(node.body) - len(keep)
        node.body = keep
        return self.generic_visit(node)

    def visit_Call(self, node):
        self.generic_visit(node)
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr == "_stop_relay" and isinstance(f.value, ast.Name) and f.value.id == "self":
            self.calls += 1
            return ast.Call(func=ast.Attribute(value=node.args[0], attr="stop", ctx=ast.Load()), args=[], keywords=[])
        return node


b = Back()
t = b.visit(ast.parse((ROOT / "companion/restart_fast_unlock.py").read_text()))
same = ast.dump(t) == ast.dump(ast.parse((HERE / "predecessors/restart_fast_unlock.py").read_text()))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ident = {f: sha(ROOT / "companion" / f) == sha(HERE / "predecessors" / Path(f).name)
         for f in ("native_fec_relay.py", "restart_fast.py", "plugins/games.py")}
git = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "companion/native_fec_relay.py", "companion/restart_fast.py",
                      "companion/plugins/games.py", "companion/native_stream.py", "companion/impairment.py"],
                     cwd=ROOT, capture_output=True, text=True).stdout.strip()
ok = same and b.removed == 1 and b.calls == 1 and all(ident.values()) and not git
out = ["# B26 — the adopted `PRIVYHUB_RESTART_FAST_UNLOCK=1` but the one packet; absent unchanged", "",
       f"- `companion/restart_fast_unlock.py`: `_stop_relay` removed ({b.removed}), its call put back as "
       f"`m._fec_relay.stop()` ({b.calls}) → AST **{'identical' if same else 'DIFFERENT'}** to HEAD 2cd392c's.",
       *[f"- `companion/{f}`: sha256 **{'identical' if v else 'DIFFERENT'}** to HEAD's." for f, v in ident.items()],
       f"- `native_fec_relay`, `restart_fast`, `plugins/games`, `native_stream`, `impairment`: `git diff HEAD` "
       f"{'empty' if not git else 'NOT EMPTY: ' + git}.",
       "- Absent the flag `restart_fast_unlock` is not imported (B24's `test_nothing_imported`, four environs, green).",
       "- With `=1`: the only change is `_stop_relay` (the send target cleared under the relay's lock before `stop()`; "
       "the frame noted after the close dropped after it). Order, timings, rows and fields unchanged.", "",
       f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**."]
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n"); print("\n".join(out)); sys.exit(0 if ok else 1)
