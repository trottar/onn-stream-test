#!/usr/bin/env python3
"""B34: flag absent = today, byte for byte. Usage: proof_flag_absent.py BASE_COPY ITEM_COPY

1. Each edited file, with the B34 lines taken out (the added lines dropped; the one changed line -- the start query's
   `+ padSlotsQuery()` -- put back), equals the base bytes: B34 adds code, it removes or reorders none.
2. Every added code line is reached only through a null `padSlots` (client: `padSlots?.` / `padSlotsQuery()` which is
   "" for null / the declarations) or a `"pad_slots" in query` / `field in values` guard (host), listed per line.
3. Absent on each side: the client builds `padSlots` only when `PadSlotsFlag.parse(...)` is true (`stable` only;
   PadSlotsTest.theFlagIsStableOnly); the host's no-key behaviour is tests/pad_slots `test_no_key_is_today` and
   `test_a_fresh_process_without_the_key_imports_nothing` (run below)."""
import difflib, subprocess, sys
from pathlib import Path
base, item = Path(sys.argv[1]), Path(sys.argv[2])
FILES = ["PrivyHub/app/src/main/java/streaming/NativeControllerSender.kt",
         "PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt",
         "companion/plugins/games.py", "companion/games/native_stream_heartbeat.py"]
ok = True
for f in FILES:
    a = (base / f).read_text().splitlines(keepends=True)
    b = (item / f).read_text().splitlines(keepends=True)
    out, added, changed = [], [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out += a[i1:i2]
        elif op == "insert":
            added += b[j1:j2]
        elif op == "replace":
            changed.append((a[i1:i2], b[j1:j2]))
            out += a[i1:i2]
        else:
            print("REMOVED lines in", f); ok = False
    same = "".join(out) == "".join(a)
    print(f"{f}: added {len(added)} lines, changed {len(changed)} hunk(s); without them == base: {same}")
    ok &= same
    for old, new in changed:
        for o, n in zip(old, new):
            print("   changed:", o.strip(), "\n        ->", n.strip())
            ok &= n.replace(" + padSlotsQuery()", "") == o
    for line in added:
        s = line.strip()
        if not s or s.startswith("//") or s.startswith("#"):
            continue
        print("   +", s[:150])
print("== the host's no-key tests")
r = subprocess.run([sys.executable, "-m", "unittest", "-v",
                    "test_pad_slots.PadSlotsHost.test_no_key_is_today",
                    "test_pad_slots.PadSlotsHost.test_a_fresh_process_without_the_key_imports_nothing"],
                   cwd=item / "tests" / "pad_slots", capture_output=True, text=True)
print(r.stderr.strip().splitlines()[-1])
ok &= r.returncode == 0
print("ABSENT = TODAY:", "PROVEN" if ok else "NOT PROVEN")
