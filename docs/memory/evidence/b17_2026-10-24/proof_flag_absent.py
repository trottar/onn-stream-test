#!/usr/bin/env python3
"""B17: absent = today.
Host: plugins/games.py's AST with B17's items removed (the assignment `guard_end = …` and every `if guard_end:`) equals
HEAD 7f3f71d's. Without the parameter `guard_end` is False, so neither `if` runs and the response gains no key.
Client: NativeStreamActivity.kt vs HEAD: every added line in a stated form, and exactly three changed lines, each the
same as today without the property:
  `it.start()` -> `if (!guardHoldsAudio) it.start()`   (guardHoldsAudio = `restartGuard?.prepareStart() == true`: false)
  B11's `restart?.let { … flush … }` -> `restart?.let { p -> restartGuard?.beginViaStart(p) }`   (restart null: no-op)
  `"?port=$VIDEO_PORT",` -> `… + (if (restart != null) "&guard_end=1" else ""),`   (restart null: the same string)
RestartGuard.kt's changes are reached only through `restartGuard` (null without the property).
    B17_ROOT=<root> python3 -B proof_flag_absent.py"""
import ast, difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B17_ROOT", str(HERE.parents[3])))

class Strip(ast.NodeTransformer):
    removed = []
    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if (isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name)
                            and item.targets[0].id == "guard_end") or (isinstance(item, ast.If) and ast.unparse(item.test) == "guard_end"):
                        Strip.removed.append(ast.unparse(item).splitlines()[0])
                        continue
                    if isinstance(item, ast.AST):
                        item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node

new = Strip().visit(ast.parse((ROOT / "companion/plugins/games.py").read_text()))
host_ok = ast.dump(new) == ast.dump(ast.parse((HERE / "predecessors/games.py").read_text())) and len(Strip.removed) == 3

J = "PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt"
code = lambda t: [l for l in t.splitlines() if not l.strip().startswith("//")]   # comment-only lines set aside
old = code((HERE / "predecessors/NativeStreamActivity.kt").read_text()); cur = code((ROOT / J).read_text())
comments_added = len([l for l in (ROOT / J).read_text().splitlines() if l.strip().startswith("//")]) - len(
    [l for l in (HERE / "predecessors/NativeStreamActivity.kt").read_text().splitlines() if l.strip().startswith("//")])
pairs, added, removed = [], [], []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, cur, autojunk=False).get_opcodes():
    if tag == "replace":
        pairs += list(zip(old[i1:i2], cur[j1:j2])); removed += old[i1:i2][len(cur[j1:j2]):]; added += cur[j1:j2][len(old[i1:i2]):]
    elif tag == "delete":
        removed += old[i1:i2]
    elif tag == "insert":
        added += cur[j1:j2]
CHANGED = {("it.start()", "if (!guardHoldsAudio) it.start()"),
           ("restart?.let { p -> restartGuard?.flush(p, { r -> postRestartReport(host, r) }, { postRestartStop(host) }) }",
            "restart?.let { p -> restartGuard?.beginViaStart(p) }"),
           ('"?port=$VIDEO_PORT",', '"?port=$VIDEO_PORT" + (if (restart != null) "&guard_end=1" else ""),')}
pair_set = {(a.strip(), b.strip()) for a, b in pairs}
ADDED = {"val guardHoldsAudio = restartGuard?.prepareStart() == true", "restart?.let { p ->", "restart?.let { p -> restartGuard?.beginViaStart(p) }",
         'restartGuard?.noteStartResponse(json.optBoolean("guard_end", false))',
         'thread(start = true, isDaemon = true, name = "PrivyHub-Guard-Report") {',
         "restartGuard?.reportAfterStart(p) { r -> postRestartReport(host, r) }"}
bad = [l for l in added if l.strip() and not l.strip().startswith("//") and not re.fullmatch(r"[\})]+", l.strip())
       and l.strip() not in ADDED]
client_ok = pair_set == CHANGED and not removed and not bad
out = ["# B17 — absent = today", "",
       f"- **Host** `companion/plugins/games.py`: the AST with B17's {len(Strip.removed)} items removed = HEAD's: "
       f"**{'identical' if host_ok else 'DIFFERENT'}** ({'; '.join(Strip.removed)}).",
       f"- **Client** `NativeStreamActivity.kt`: {len(added)} added lines, {len(pairs)} changed (the three stated: "
       f"**{'yes' if pair_set == CHANGED else 'NO'}**), {len(removed)} removed, {len(bad)} outside the forms; "
       f"{comments_added} comment-only lines added (set aside before the diff).", "",
       f"Result: **{'PROVEN' if host_ok and client_ok else 'NOT PROVEN'}**.", "", "Changed lines:", "```"]
out += [f"- {a.strip()}\n+ {b.strip()}" for a, b in pairs] + ["```", "", "Added lines:", "```"] + added + ["```"]
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:6]))
sys.exit(0 if host_ok and client_ok else 1)
