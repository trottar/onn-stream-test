#!/usr/bin/env python3
"""Queue BM: B200's and B201's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not
run) in a copy of the work copy; the test that must catch it runs once; FAIL expected (BL's runner, reused).
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T, E = "tools/party_add_game.py", "tools/h7_endscreen.py"
K = "tests.b200_drawn_places.test_b200."
F = "tests.b201_find.test_b201."
MUT = [
    ("M1_the_same_shape_rule_skipped", E,
     [('''    if holds(None):
        return True, []''', '''    if True:
        return True, []''')],
     [K + "Panel.test_1_a_panel_never_taken"]),
    ("M2_a_drawn_number_read_by_its_value", E,
     [('''    def __str__(self) -> str:
        return self.text''', '''    def __str__(self) -> str:
        return str(int(self))''')],
     [K + "Drawn.test_1_read_as_drawn_label_and_learn_pass"]),
    ("M3_the_off_line_search_skipped", E,
     [('''            got, miss = _offline_column(first, want, taken + [p_ for p_ in cols if p_ is not None])''',
       '''            got, miss = [], runs''')],
     [K + "Drawn.test_1_read_as_drawn_label_and_learn_pass"]),
    ("M4_off_line_digits_counted_for_the_finals", T,
     [('''            if x is not None and (pl is None or pl.get("group") in fg):''', '''            if x is not None:''')],
     [K + "Counted.test_1_small_cells_teach_no_final_digit"]),
    ("M5_the_words_ignored", T,
     [('''        got = [n for n in nodes if rule(n)]''', '''        got = list(nodes)''')],
     [F + "Words.test_1_a_part_of_the_name"]),
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
