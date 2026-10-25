#!/usr/bin/env python3
"""B22: absent = today.
Host: plugins/games.py's whole AST with B22's items removed equals the predecessor's (HEAD 13ccff5 + B21). Removed:
`_restart_fast = None`; each `if` whose test starts with `(os.environ.get('PRIVYHUB_RESTART_FAST')` or
`_restart_fast is not None` -- replaced by its `else` body when it has one (the start's: today's
`self._native_stream.start(...)`). Absent, `_restart_fast` is None, so each such test is false and the else runs.
companion/restart_fast.py is new and imported only under the flag. native_stream.py unchanged (git diff empty).
Client: NativeStreamActivity.kt against the predecessor (= the CONFIRMED APK 20e3e339's sources): every added line
listed with what it does when `restartFast` is null (no host key) -- and the one changed line.
    B22_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, difflib, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B22_ROOT", str(HERE.parents[3])))
PREFIXES = ("(os.environ.get('PRIVYHUB_RESTART_FAST')", "_restart_fast is not None")

class Strip(ast.NodeTransformer):
    def __init__(self): self.removed = []
    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if isinstance(item, ast.If) and ast.unparse(item.test).startswith(PREFIXES):
                        self.removed.append(ast.unparse(item.test)[:110] + (" -> its else" if item.orelse else ""))
                        for x in item.orelse:
                            keep.append(self.visit(x) if isinstance(x, ast.AST) else x)
                        continue
                    if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name) \
                            and item.targets[0].id == "_restart_fast":
                        self.removed.append(ast.unparse(item)[:100]); continue
                    if isinstance(item, ast.AST): item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node

out = ["# B22 — absent = today", ""]
s = Strip(); t = s.visit(ast.parse((ROOT / "companion/plugins/games.py").read_text()))
same = ast.dump(t) == ast.dump(ast.parse((HERE / "predecessors/games.py").read_text()))
ns_diff = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "companion/native_stream.py"], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
out += ["## Host", "",
        f"- `companion/plugins/games.py`: {len(s.removed)} B22 items removed — " + "; ".join(f"`{r}`" for r in s.removed)
        + f" → AST **{'identical' if same else 'DIFFERENT'}** to the predecessor's.",
        f"- `companion/native_stream.py`: `git diff HEAD` {'empty' if not ns_diff else 'NOT EMPTY: ' + ns_diff}.",
        "- `companion/restart_fast.py`: new, imported only under the flag (`tests/restart_fast` `test_nothing_imported`).", ""]
ok = same and len(s.removed) == 4 and not ns_diff

# client
old = (HERE / "predecessors/NativeStreamActivity.kt").read_text().splitlines()
new = (ROOT / "PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt").read_text().splitlines()
added, removed, hunks = [], [], []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
    if tag in ("replace", "delete"): removed += old[i1:i2]
    if tag in ("replace", "insert"):
        added += new[j1:j2]
        hunks.append((j1 + 1, [l for l in new[j1:j2] if l.strip() and not l.strip().startswith("//")]))
def kind(first):
    x = first.strip()
    if x.startswith("restartFast?.let { uiHandler.removeCallbacks"): return "startSession: removes a tick that is not posted and sets null a field that is null"
    if x.startswith("val ssrcAtStart"): return "a read of the receiver's counter at a guarded start; consumed only inside the key's block"
    if x.startswith("if (restart != null) {"): return "the key's block: `restartFast` set only when the response carries `restart_fast.armed` true"
    if x.startswith("restartFast?.reportDone"): return "null-safe: nothing without the key"
    if x.startswith("if (restart != null && restartFast == null)"): return "CHANGED line: = today's when `restartFast` is null"
    if x.startswith("restartFast?.let {") or x.startswith("restartFast?.let { r ->"): return "a `restartFast?.let` block: skipped without the key"
    if x.startswith("@Volatile") or "private var restartFast: RestartFast? = null" in first: return "declarations: the field (null), the tick and its inputs (run only from the key's paths)"
    if x.startswith("restartFast?.noteRelease") or x.startswith("if (restartFast?.takeAudio()"): return "null-safe: nothing without the key"
    return "UNCLASSIFIED"
code = [l for l in added if l.strip() and not l.strip().startswith("//")]
out += ["## Client (`NativeStreamActivity.kt`)", "",
        f"- removed lines: {len(removed)} — " + "; ".join(f"`{r.strip()}`" for r in removed),
        f"- added code lines (not blank / comment): {len(code)}, in {len(hunks)} hunks", "",
        "| hunk (new line) | code lines | first line | without the host key |", "| --- | --- | --- | --- |"]
unclassified = 0
for at, lines in hunks:
    if not lines:
        continue
    k = kind(lines[0])
    if k == "UNCLASSIFIED" and any("private var restartFast: RestartFast? = null" in l for l in lines):
        k = kind("@Volatile") + " (difflib aligned its first `}` with the preceding block's)"
    unclassified += k == "UNCLASSIFIED"
    out.append(f"| {at} | {len(lines)} | `{lines[0].strip()[:90].replace('|', '/')}` | {k} |")
rem_ok = [r.strip() for r in removed] == ["if (restart != null) audioReceiver?.start()"]
out += ["", f"- the one removed line is today's rebuilt-audio start, now `if (restart != null && restartFast == null)`: "
        f"{'yes' if rem_ok else 'NO'}.",
        "- `restartFast` is assigned a non-null value in one place only: inside `if (restart != null)` when the response "
        "carries `restart_fast.armed` true (a host with `PRIVYHUB_RESTART_FAST=1`); `restart_guard 0` → no guard → "
        "`restart` null.", ""]
ok &= rem_ok and unclassified == 0
out.append(f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}** (host: AST; client: every added line is null-safe on "
           "`restartFast`, a read, or reached only with the key; the changed line equals today's without it).")
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n"); print("\n".join(out)); sys.exit(0 if ok else 1)
