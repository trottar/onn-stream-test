#!/usr/bin/env python3
"""Queue BN: B204's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not run) in a
copy of the work copy; the test that must catch it runs once; FAIL expected (BM's runner, reused).
usage: run_mutations_bn.py <work copy> <out file> <scratch>"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T, E = "tools/party_add_game.py", "tools/h7_endscreen.py"
K = "tests.b204_every_number.test_b204."
MUT = [
    ("M1_the_stats_added_into_the_sum", T,
     [('''    return list(cells[:getattr(cells, "periods", len(cells))])''', '''    return list(cells)''')],
     [K + "Reading.test_3_the_sum_over_the_periods_only"]),
    ("M2_another_size_never_counted", E,
     [('''    return (two is not None and same < two), round(same, 4), (round(two, 4) if two is not None else None)''',
       '''    return False, round(same, 4), (round(two, 4) if two is not None else None)''')],
     [K + "Sizes.test_1_one_font_counted"]),
    ("M3_another_size_always_counted", E,
     [('''    return (two is not None and same < two), round(same, 4), (round(two, 4) if two is not None else None)''',
       '''    return True, round(same, 4), (round(two, 4) if two is not None else None)''')],
     [K + "Sizes.test_2_two_faces_not_counted"]),
]
lines = []
for name, path, edits, tests in MUT:
    work = SCR / name
    shutil.copytree(W, work, ignore=shutil.ignore_patterns("__pycache__"))
    f = work / path
    text = f.read_text()
    if any(text.count(a) != 1 for a, _b in edits):
        lines.append(f"{name}: ANCHOR MISSING — not run")
        continue
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
