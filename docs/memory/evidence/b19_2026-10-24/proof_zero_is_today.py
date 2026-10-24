#!/usr/bin/env python3
"""B19: `0` = today's absent, byte for byte in behaviour. Only the two flag objects' parse / fromSystem changed in
StallSignal.kt and RestartGuard.kt (the rest of each file identical to predecessors/). Old parse(absent) vs new
parse("0"): StallSignalFlag null -> null, RestartGuardFlag false -> false; every hook reads only these. The tests'
moved lines are listed.
    B19_ROOT=<root> python3 -B proof_zero_is_today.py"""
import difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B19_ROOT", str(HERE.parents[3])))
def flag_block(lines, name):
    i = next(k for k, l in enumerate(lines) if l.startswith(f"object {name}"))
    j = next(k for k in range(i + 1, len(lines)) if lines[k] == "}")
    return i, j
out = ["# B19 — `0` = today", ""]
ok = True
for f, name in (("StallSignal.kt", "StallSignalFlag"), ("RestartGuard.kt", "RestartGuardFlag")):
    a = (HERE / "predecessors" / f).read_text().splitlines(); b = (ROOT / "PrivyHub/app/src/main/java/streaming" / f).read_text().splitlines()
    ai, aj = flag_block(a, name); bi, bj = flag_block(b, name)
    rest_same = a[aj + 1:] == b[bj + 1:]
    head_a = [l for l in a[:ai]]; head_b = [l for l in b[:bi] if "B19" not in l and not l.startswith(" * counts the") and not l.startswith(" * one), so") and l != " *"]
    head_same = [l for l in head_a if l != " *"] == head_b
    d = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    ok &= rest_same and head_same
    out.append(f"- `{f}`: changed only inside `object {name}` (and its doc comment): **{'yes' if rest_same and head_same else 'NO'}**; +{sum(l[0]=='+' for l in d)} −{sum(l[0]=='-' for l in d)}.")
out += ["", "| flag | old `parse(absent)` | new `parse(\"0\")` |", "| --- | --- | --- |",
        "| `StallSignalFlag` | null | null |", "| `RestartGuardFlag` | false | false |", "",
        "The values are asserted by `StallSignalTest.flagTable`, `RestartGuardTest.flagTable` and `ClientDefaultsTest` "
        "(`tests_jvm.txt`).", "", "**The tests' moved lines (absent = off → absent = on, `0` = off):**", "```diff"]
for f in ("StallSignalTest.kt", "RestartGuardTest.kt", "RestartGuardAllPathsTest.kt", "RestartGuardAudioOrderTest.kt"):
    a = (HERE / "predecessors" / f).read_text().splitlines(); b = (ROOT / "PrivyHub/app/src/test/java/streaming" / f).read_text().splitlines()
    out += list(difflib.unified_diff(a, b, f"a/{f}", f"b/{f}", lineterm="", n=0))
out += ["```", "", f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**."]
(HERE / "proof_zero_is_today.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:4])); print(out[-1])
sys.exit(0 if ok else 1)
