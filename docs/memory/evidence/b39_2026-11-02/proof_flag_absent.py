#!/usr/bin/env python3
"""B39: flag absent = today. Every line B39 adds to or removes from NativeStreamActivity.kt sits where only a non-null
`surfaceHold` (debug.privyhub.surface_hold set) reaches it; SurfaceHold.kt is constructed only then. Usage:
proof_flag_absent.py BASE_ACTIVITY NEW_ACTIVITY"""
import difflib, re, sys
base, new = (open(p).read().splitlines() for p in sys.argv[1:3])
def ctx(lines, i):
    """the enclosing hold-only context of line i, or None"""
    for j in range(i, -1, -1):
        l = lines[j]
        if re.match(r"    private fun (beginSurfaceHold|endSurfaceHold)\(", l): return l.strip().split("(")[0]
        if re.match(r"    private val holdExpiry", l):
            # after the null check
            body = lines[j:i + 1]
            return "holdExpiry (after `val h = surfaceHold ?: return@Runnable`)" if any("val h = surfaceHold ?: return@Runnable" in b for b in body) else None
        if re.match(r"    override fun onDestroy", l):
            blk = [k for k in range(j, i + 1) if lines[k].strip().startswith("surfaceHold?.let { h ->")]
            # the block's body (12 spaces) and its own closing brace (8 spaces, the line itself)
            if blk and all(lines[k].startswith("            ") or lines[k].strip() == "" or (k == i and lines[k] == "        }")
                           for k in range(blk[-1] + 1, i + 1)):
                return "onDestroy's `surfaceHold?.let { h -> … }`"
            return None
        if re.match(r"    (private |override |internal )?(fun|val|var) ", l): return None
    return None
bad = 0; n = 0
sm = difflib.SequenceMatcher(None, base, new, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal": continue
    for k in range(i1, i2):
        n += 1; c = ctx(base, k); print(f"- base:{k+1} [{c}] {base[k].strip()}"); bad += c is None
    for k in range(j1, j2):
        n += 1; c = ctx(new, k); print(f"+ new:{k+1} [{c}] {new[k].strip()}"); bad += c is None
# the callers: the two functions and the runnable are reached only through a non-null surfaceHold
calls = [l.strip() for l in new if re.search(r"\b(beginSurfaceHold|endSurfaceHold)\(it", l) or "postDelayed(holdExpiry" in l]
print("callers:", calls)
ok_calls = all("surfaceHold?.let" in c or c.startswith("uiHandler.postDelayed(holdExpiry") for c in calls)
print(f"changed lines {n}, outside a hold-only context {bad}; callers guarded: {ok_calls}")
print("PROVEN" if bad == 0 and ok_calls and n > 0 else "NOT PROVEN")
