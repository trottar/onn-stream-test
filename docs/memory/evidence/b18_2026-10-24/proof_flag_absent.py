#!/usr/bin/env python3
"""B18: absent = today.
Host:
- games/link_drop_recovery.py, plugins/games.py: the whole module's AST with B18's items removed (the class attribute
  `_session_end`; each `if` whose test starts with `self._session_end is not None` or
  `getattr(self._recovery, '_session_end', None) is not None`) equals the predecessor's. Without
  PRIVYHUB_INPUT_HOLD_REWIND=state nothing sets `_session_end`, so both hooks are false.
- rewind_cores.py (B9's module, imported only with PRIVYHUB_INPUT_HOLD_REWIND) and stall_signal.py (B7's, only with
  PRIVYHUB_STALL_SIGNAL): listed, not claimed identical.
Client: NativeStreamActivity.kt only added lines (the bye's block: `if (isFinishing) { stallMonitor?.let { … } }`, a
no-op without the property: `stallMonitor` null); StallSignal.kt's StallMonitor exists only with the property.
    B18_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B18_ROOT", str(HERE.parents[3])))
PREFIXES = ("self._session_end is not None", "getattr(self._recovery, '_session_end', None) is not None")

class Strip(ast.NodeTransformer):
    def __init__(self): self.removed = []
    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if (isinstance(item, ast.If) and ast.unparse(item.test).startswith(PREFIXES)) or (
                            isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == "_session_end"):
                        self.removed.append(ast.unparse(item).splitlines()[0][:100]); continue
                    if isinstance(item, ast.AST): item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node

out = ["# B18 — absent = today", "", "| file | B18 items removed | AST then = predecessor |", "| --- | --- | --- |"]
ok = True
for rel, pred in (("companion/games/link_drop_recovery.py", "link_drop_recovery.py"), ("companion/plugins/games.py", "games.py")):
    s = Strip(); t = s.visit(ast.parse((ROOT / rel).read_text()))
    same = ast.dump(t) == ast.dump(ast.parse((HERE / "predecessors" / pred).read_text()))
    ok &= same and len(s.removed) >= 1
    out.append(f"| `{rel}` | {len(s.removed)}: " + "; ".join(f"`{r}`" for r in s.removed) + f" | **{'identical' if same else 'DIFFERENT'}** |")
out.append("")
for rel, pred, why in (("companion/rewind_cores.py", "rewind_cores.py", "B9's module, imported only with PRIVYHUB_INPUT_HOLD_REWIND"),
                       ("companion/stall_signal.py", "stall_signal.py", "B7's module, imported only with PRIVYHUB_STALL_SIGNAL"),
                       ("PrivyHub/app/src/main/java/streaming/StallSignal.kt", "StallSignal.kt", "the StallMonitor exists only with debug.privyhub.stall_signal")):
    a = (HERE / "predecessors" / pred).read_text().splitlines(); b = (ROOT / rel).read_text().splitlines()
    d = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    out.append(f"- `{rel}` ({why}): +{sum(l[0] == '+' for l in d)} −{sum(l[0] == '-' for l in d)}, listed in `b18.diff`.")
J = "PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt"
a = (HERE / "predecessors/NativeStreamActivity.kt").read_text().splitlines(); b = (ROOT / J).read_text().splitlines()
rem, add = [], []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if tag in ("replace", "delete"): rem += a[i1:i2]
    if tag in ("replace", "insert"): add += b[j1:j2]
FORMS = {"if (isFinishing) {", "stallMonitor?.let { m ->", "m.requestBye()", "val until = System.nanoTime() + 60_000_000L",
         "while (m.byesSent == 0L && System.nanoTime() < until) {", "Thread.sleep(5L)"}
bad = [l for l in add if l.strip() and not l.strip().startswith("//") and not re.fullmatch(r"[\})]+", l.strip()) and l.strip() not in FORMS]
client_ok = not rem and not bad
ok &= client_ok
out += ["", f"- `{J}`: {len(rem)} removed, {len(add)} added, {len(bad)} outside the forms. Without the property "
        "`stallMonitor` is null: the block is `if (isFinishing) { null?.let {…} }`, which does nothing.", "",
        f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**.", "", "```"] + add + ["```"]
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
sys.exit(0 if ok else 1)
