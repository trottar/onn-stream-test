#!/usr/bin/env python3
"""B15 (client): debug.privyhub.restart_guard absent = today (da09e154's sources, HEAD efa4240).
NativeStreamActivity.kt vs predecessors/: (1) only added lines (difflib); (2) every added code line in an allowed form.
Without the property `restartGuard` is null (RestartGuardTest.flagTable / RestartGuardAllPathsTest: fromSystem() false
off-device), so `restartGuard?.attach(...)` evaluates nothing (Kotlin's `?.` skips the arguments: no file object, no
instance number), and `restartGuard?.handOver(...) { ... } == true` is `null == true`, false: its body never runs and
the lambda is never called. RestartGuard.kt's changes are reached only through `restartGuard`.
    B15_ROOT=<root with PrivyHub/> python3 -B proof_flag_absent_client.py"""
import difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B15_ROOT", str(HERE.parents[3])))
J = "PrivyHub/app/src/main/java/streaming"
ALLOWED = [r"^\s*//", r"^\s*$", r"^\s*[\})]\s*$",
           r"^\s*restartGuard\?\.attach\(FilePendingStore\(File\(noBackupFilesDir, RestartGuard\.STORE_FILE\)\),$",
           r"^\s*RestartGuardProcess\.nextInstance\(\), RestartGuardProcess\.mark\)$",
           r"^\s*if \(restartGuard\?\.handOver\(isChangingConfigurations, sessionStarted\) \{ cacheSessionReport\(\) \} == true\) \{$",
           r"^\s*thermalSampler\?\.stop\(\)$",
           r"^\s*sessionStarted = false$",
           r"^\s*stopLocalPipeline\(\)$",
           r"^\s*return$"]
name = "NativeStreamActivity.kt"
old = (HERE / "predecessors" / name).read_text().splitlines(); new = (ROOT / J / name).read_text().splitlines()
removed, added = [], []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
    if tag in ("replace", "delete"): removed += old[i1:i2]
    if tag in ("replace", "insert"): added += new[j1:j2]
bad = [l for l in added if not any(re.match(p, l) for p in ALLOWED)]
# the four body lines must sit inside the handOver if (the only `return` / pipeline lines added)
body_ok = sum(1 for l in added if re.match(r"^\s*return$", l)) == 1
ok = not removed and not bad and body_ok
out = ["# B15 (client) — property absent = today (only added lines, all in the allowed forms)", "",
       "| file | removed / changed | added | outside the forms |", "| --- | ---: | ---: | ---: |",
       f"| `{name}` | **{len(removed)}** | {len(added)} | **{len(bad)}** |", "",
       f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**. `thermalSampler?.stop()`, `sessionStarted = false`, "
       "`stopLocalPipeline()` and `return` are the body of the one `if (restartGuard?.handOver(...) == true)`, which "
       "is false without the property. `RestartGuard.kt` (B11's file, +B15) is reached only through `restartGuard`, "
       "null without the property.", "", "```"] + added + ["```"] + (["", "Outside:"] + bad if bad else [])
(HERE / "proof_flag_absent_client.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:8]))
sys.exit(0 if ok else 1)
