#!/usr/bin/env python3
"""B32 (client): flag absent = today, from the source. Usage: proof_flag_absent.py PREDECESSOR_DIR COPY_ROOT.

The activity: `surfaceHold` is a `by lazy` that is null without the property (SurfaceHoldFlag.parse(null) = null; the
JVM test pins it). So every added line must (a) sit behind `surfaceHold?.` / `surfaceHold != null` / a `surfaceHold?.let`,
or (b) be inside the new declaration block (the lazy, its fields, its private functions, the three framework overrides
that call `super` first and then only `surfaceHold?.`), whose private functions and the sender's `neutralize()` are
called only from (a) lines. The one removed line is today's `if (decoder == null) {`, kept as the `else if` branch.
Prints the classification of every added line; exits 1 on anything unclassified."""
import difflib, re, sys
from pathlib import Path
pred, root = Path(sys.argv[1]), Path(sys.argv[2])
A = "PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt"
S = "PrivyHub/app/src/main/java/streaming/NativeControllerSender.kt"
old = (pred / Path(A).name).read_text().splitlines()
new = (root / A).read_text().splitlines()
added, removed = [], []
for op in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
    tag, i1, i2, j1, j2 = op
    if tag in ("replace", "delete"):
        removed += old[i1:i2]
    if tag in ("replace", "insert"):
        added += [(j, new[j]) for j in range(j1, j2)]
fails = 0
print("removed lines:", [r.strip() for r in removed])
if [r.strip() for r in removed] != ["if (decoder == null) {"]:
    print("FAIL removed lines"); fails += 1
blk0 = next(i for i, l in enumerate(new) if "// B32: the hold, only with debug.privyhub.surface_hold" in l)
blk1 = next(i for i, l in enumerate(new) if l.strip() == "override fun dispatchKeyEvent(")
GUARD = re.compile(r"surfaceHold\?\.|surfaceHold != null|surfaceHold\?\.let")
cont = 0
for j, l in added:
    s = l.strip()
    if blk0 <= j < blk1:
        cls = "block (declarations; called only from guarded lines)"
    elif not s or s.startswith("//"):
        cls = "blank / comment"
    elif GUARD.search(s):
        cls = "guarded"
    elif s in ("buildHeldDecoder(sps, pps)", "} else if (decoder == null) {", "return true", "}"):
        cls = "inside a guarded branch (the line above)"
    elif s == "heldSurface = surface" or s.startswith("if (surfaceHold != null)"):
        cls = "guarded"
    else:
        cls = "UNCLASSIFIED"; fails += 1
    print(f"{j + 1:5d} {cls:55s} {s[:100]}")
# the block's functions are called only from guarded lines (or from inside the block)
for fn in ("beginSurfaceHold", "endSurfaceHold", "buildHeldDecoder", "registerHoldDeviceListener",
           "unregisterHoldDeviceListener", "holdExpiry", "heldSurface", "heldDecoderLock", "holdDeviceListener"):
    for j, l in enumerate(new):
        if fn in l and not (blk0 <= j < blk1) and not GUARD.search(l) and l.strip() not in ("heldSurface = surface",) \
                and "buildHeldDecoder(sps, pps)" != l.strip():
            print(f"FAIL {fn} used unguarded at {j + 1}: {l.strip()}"); fails += 1
calls = [l.strip() for l in new if "neutralize()" in l]
print("neutralize() call sites:", calls)
if not all(GUARD.search(c) or "controllerSender?.neutralize()" == c for c in calls):
    fails += 1
# the bare `controllerSender?.neutralize()` sits inside beginSurfaceHold (the block)
for j, l in enumerate(new):
    if l.strip() == "controllerSender?.neutralize()" and not (blk0 <= j < blk1):
        print("FAIL neutralize outside the block at", j + 1); fails += 1
sold = (pred / Path(S).name).read_text(); snew = (root / S).read_text()
print("sender: only appended:", snew.startswith(sold[:-2]) and "fun neutralize()" in snew[len(sold) - 2:])
print("FAILS", fails)
sys.exit(1 if fails else 0)
