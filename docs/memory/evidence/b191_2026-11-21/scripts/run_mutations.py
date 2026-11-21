#!/usr/bin/env python3
"""Queue BJ: B191 / B192's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not
run) in a copy of the work copy; the test that must catch it runs once; FAIL expected (BI's runner, reused).
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T, E = "tools/party_add_game.py", "tools/h7_endscreen.py"
K = "tests.b191_letters.test_b191."
MUT = [
    ("M1_a_synthetic_picture_counted_as_proof", T,
     [('''            right = (ok2 and bool(said) and said[0][1] == cls and said[0][0] <= BARS["ended_within_s"][0]
                     and all(g == sides[role] for g in got_l))''',
       '''            right = bool(tr.get("every_held_out_read"))''')],
     [K + "Tool.test_5_left_out_reads_the_real_save"]),
    ("M2_a_background_read_as_a_letter", E,
     [('''        if t is None or need is None or float(dd[o[0]]) > t or margin < need or k not in (word[i], "-"):''',
       '''        if k not in (word[i], "-"):''')],
     [K + "Reads.test_4_background_shapes_never_letters"]),
    ("M3_a_guess_when_neither_spelled", E,
     [('''        if any(spelled):                                   # a word spelled is never the begin''',
       '''        if got and all(s is not None for s in got):'''),
      ('''                if sum(spelled) == 1:''', '''                if sum(spelled) <= 1:''')],
     [K + "Reads.test_1_neither_spelled_never_ends"]),
    ("M4_a_moving_screen_taken", E,
     [('''            if out["class"] in self.spec["end_classes"] and moved and self.prev_class == out["class"]:''',
       '''            if False:''')],
     [K + "Reads.test_5_a_moving_screen_never_ends"]),
]
only = sys.argv[4:]
lines = []
for name, path, edits, tests in MUT:
    if only and name not in only:
        continue
    work = SCR / name
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(W, work, ignore=shutil.ignore_patterns("__pycache__", "PrivyHub"))
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
    lines.append(f"{name}: {'CAUGHT' if p.returncode != 0 else 'NOT CAUGHT'} ({' '.join(tail)})")
    shutil.rmtree(work, ignore_errors=True)
left = list((SCR / "tmp").iterdir()) if (SCR / "tmp").exists() else []
lines.append(f"temp dirs left: {len(left)}")
OUT.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
