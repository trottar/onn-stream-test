#!/usr/bin/env python3
"""Queue BL: B198's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not run) in a
copy of the work copy; the test that must catch it runs once; FAIL expected (BK's runner, reused).
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T, E = "tools/party_add_game.py", "tools/h7_endscreen.py"
K = "tests.b198_max_score.test_b198."
MUT = [
    ("M1_every_digit_0_9_required_anyway", T,
     [('''    n = b.get("max_score")
    if n is None:''', '''    n = b.get("max_score")
    if True:''')],
     [K + "Low.test_1_max_4_passes_without_5_to_9"]),
    ("M2_an_unexpected_digit_read_by_nearness", E,
     [('''            digs += best[len(place["group"]):] if ok else "?"
            if ok and len(idx) > 1:''', '''            digs += best[len(place["group"]):] if True else "?"
            if ok and len(idx) > 1:''')],
     [K + "Hub.test_1_a_final_of_7_never_read"]),
    ("M3_a_final_above_n_read", E,
     [('''            elif top is not None and max(sr["scores"]) > int(top):''', '''            elif False:''')],
     [K + "Hub.test_3_above_n_with_every_digit_learnt_given_up"]),
]
only = sys.argv[4:]
lines = []
for name, path, edits, tests in MUT:
    if only and name not in only:
        continue
    work = SCR / name
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(W, work, ignore=shutil.ignore_patterns("__pycache__"))
    f = work / path
    text = f.read_text()
    miss = [a for a, _b in edits if text.count(a) != 1]
    if miss:
        lines.append(f"{name}: ANCHOR MISSING ({len(miss)}) — not run")
        shutil.rmtree(work, ignore_errors=True)
        continue
    for a, b in edits:
        text = text.replace(a, b)
    f.write_text(text)
    env = dict(os.environ, TMPDIR=str(SCR / "tmp"))
    (SCR / "tmp").mkdir(parents=True, exist_ok=True)
    p = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", *tests], cwd=work, env=env,
                       capture_output=True, text=True, timeout=3600)
    tail = [ln for ln in p.stderr.splitlines() if ln.startswith(("Ran", "OK", "FAILED"))]
    why = [ln for ln in p.stderr.splitlines() if ln.startswith(("AssertionError", "FAIL:", "ERROR:"))][:2]
    lines.append(f"{name}: {'CAUGHT' if p.returncode != 0 else 'NOT CAUGHT'} ({' '.join(tail)}) {' | '.join(why)}")
    shutil.rmtree(work, ignore_errors=True)
left = list((SCR / "tmp").iterdir()) if (SCR / "tmp").exists() else []
lines.append(f"temp dirs left: {len(left)}")
OUT.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
