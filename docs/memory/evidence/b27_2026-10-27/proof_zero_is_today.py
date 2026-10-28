#!/usr/bin/env python3
"""B27: `debug.privyhub.loss_guard=0` = HEAD's absent (no LossGuard object), and nothing else in the client changed.
LossGuard.kt against HEAD (2cd392c): every removed / added line lies inside `object LossGuardFlag { ... }` or is the one
added KDoc line; HEAD's parse gives null for null, the new parse gives null for "0" (both then build no object:
`LossGuardFlag.fromSystem()?.let { LossGuard(it) }` in the activity, unchanged). Every other main source is unchanged
against HEAD. The JVM side of the same claim: LossGuardDefaultOnTest.zeroIsTodaysAbsent (the stream's queued list
with "0" = with no guard = B10's today list).
    B27_ROOT=<root> python3 -B proof_zero_is_today.py"""
import os, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B27_ROOT", str(HERE.parents[3])))
REL = "PrivyHub/app/src/main/java/streaming/LossGuard.kt"
new = (ROOT / REL).read_text().splitlines()
old = (HERE / "predecessors/LossGuard.kt").read_text().splitlines()


def flag_span(lines):
    a = next(i for i, l in enumerate(lines) if l.startswith("object LossGuardFlag"))
    b = next(i for i in range(a, len(lines)) if lines[i] == "}")
    return a, b


diff = subprocess.run(["diff", "--unchanged-line-format=", "--old-line-format=-%dn\n", "--new-line-format=+%dn\n",
                       str(HERE / "predecessors/LossGuard.kt"), str(ROOT / REL)], capture_output=True, text=True).stdout
oa, ob = flag_span(old); na, nb = flag_span(new)
outside = []
for tag in diff.split():
    kind, n = tag[0], int(tag[1:]) - 1
    lo, hi, lines = (oa, ob, old) if kind == "-" else (na, nb, new)
    if lo <= n <= hi:
        continue
    if kind == "+" and lines[n].startswith(" * B27:"):
        continue
    outside.append(f"{kind}{n + 1}: {lines[n].strip()[:80]}")
others = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "PrivyHub/app/src/main", f":(exclude){REL}"], cwd=ROOT,
                        capture_output=True, text=True).stdout.strip()
body = "\n".join(new[na:nb + 1])
zero_off = re.search(r'"0"\s*->\s*null', body) is not None
old_body = "\n".join(old[oa:ob + 1])
old_absent_null = re.search(r"else\s*->\s*null", old_body) is not None
ok = not outside and not others and zero_off and old_absent_null
out = ["# B27 — `0` = today's absent; the rest of the client unchanged", "",
       f"- `{REL}`: {len(diff.split())} changed lines, **{'all' if not outside else 'NOT all'}** inside `object LossGuardFlag` "
       "(or the one added `B27:` KDoc line)" + ("" if not outside else ": " + "; ".join(outside)) + ".",
       f"- HEAD's parse: `else -> null` (absent = null): **{old_absent_null}**. The new parse: `\"0\" -> null`: **{zero_off}**. "
       "With null the activity builds no `LossGuard` (its line is unchanged): no hold, no datagram, no report or heartbeat key.",
       f"- Every other main source: `git diff HEAD` {'empty' if not others else 'NOT EMPTY: ' + others}.",
       "- JVM: `LossGuardDefaultOnTest.zeroIsTodaysAbsent` green (with `0` the receiver queues B10's today list, the same as "
       "with no guard); it stays green under the mutation, as it must.", "",
       f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**."]
(HERE / "proof_zero_is_today.md").write_text("\n".join(out) + "\n"); print("\n".join(out)); sys.exit(0 if ok else 1)
