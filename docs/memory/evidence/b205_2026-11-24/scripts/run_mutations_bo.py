#!/usr/bin/env python3
"""Queue BO: B205's mutation — the synthetic glyphs counted toward the gates (merged into the real cells before every
measure); exact anchor, found once, else ANCHOR MISSING and not run; the test that must catch it runs once.
usage: run_mutations_bo.py <work copy> <out file> <scratch>"""
import shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
E = "tools/h7_endscreen.py"
MUT = [("M1_a_synthetic_glyph_counted_toward_a_cell", E,
        [('''                      for k in keys]).astype(np.float32) if keys else empty)    # synthetic weigh at most as the real
    own_of = {''', '''                      for k in keys]).astype(np.float32) if keys else empty)    # synthetic weigh at most as the real
    cells = {k: list(cells[k]) + list(train.get(k, [])) for k in keys}
    own_of = {''')],
        ["tests.b205_synthetic_digits.test_b205.Gates.test_2_a_far_synthetic_glyph_never_widens_a_digits_own_spread"])]
lines = []
for name, path, edits, tests in MUT:
    work = SCR / name
    shutil.copytree(W, work, ignore=shutil.ignore_patterns("__pycache__"))
    f = work / path
    text = f.read_text()
    if any(text.count(a) != 1 for a, _b in edits):
        lines.append(f"{name}: ANCHOR MISSING — not run"); continue
    for a, b in edits:
        text = text.replace(a, b)
    f.write_text(text)
    p = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", *tests], cwd=work, capture_output=True,
                       text=True, timeout=600)
    tail = [ln for ln in p.stderr.splitlines() if ln.startswith(("Ran", "OK", "FAILED"))]
    why = [ln for ln in p.stderr.splitlines() if ln.startswith(("AssertionError", "FAIL:", "ERROR:"))][:2]
    lines.append(f"{name}: {'CAUGHT' if p.returncode != 0 else 'NOT CAUGHT'} ({' '.join(tail)}) {' | '.join(why)}")
OUT.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
