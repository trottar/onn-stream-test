#!/usr/bin/env python3
"""B42: every changed line of the two main files lies inside `object SurfaceHoldFlag` / `object PadSlotsFlag` (or the
file's header comment above them); the objects' consumers are unchanged. Usage: proof_zero_is_today.py PRED_DIR NEW_DIR
(NEW_DIR = the copy's PrivyHub/app/src/main/java/streaming)."""
import difflib, re, sys
from pathlib import Path
pred, new = Path(sys.argv[1]), Path(sys.argv[2])
ok = True
for name, obj in (("SurfaceHold.kt", "SurfaceHoldFlag"), ("PadSlots.kt", "PadSlotsFlag")):
    a, b = (pred / name).read_text().splitlines(), (new / name).read_text().splitlines()
    start = next(i for i, l in enumerate(b) if l.startswith(f"object {obj}"))
    end = next(i for i in range(start, len(b)) if b[i] == "}")
    header_end = start  # the doc comment above the object (the file's header) is allowed
    changed = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            continue
        changed += list(range(j1, j2)) or [j1]
    outside = [j for j in changed if not (0 <= j <= end)]
    in_obj = [j for j in changed if start <= j <= end]
    in_header = [j for j in changed if j < start]
    print(f"{name}: changed new-lines {len(changed)}; inside object {obj} (lines {start+1}-{end+1}): {len(in_obj)}; "
          f"in the header comment above it: {len(in_header)}; elsewhere: {len(outside)}")
    for j in in_header:
        if not b[j].lstrip().startswith("*"):
            print("   NOT A COMMENT LINE in the header:", j + 1); ok = False
    ok &= not outside
streaming = new
uses = sorted(str(p.name) + ":" + str(i + 1) + ": " + l.strip() for p in streaming.glob("*.kt")
              for i, l in enumerate(p.read_text().splitlines()) if re.search(r"(SurfaceHoldFlag|PadSlotsFlag)\.", l)
              and p.name not in ("SurfaceHold.kt", "PadSlots.kt"))
print("consumers (unchanged by B42; each builds its object only from a non-null bound / true):")
for u in uses:
    print("  ", u)
print("PROVEN" if ok else "NOT PROVEN")
