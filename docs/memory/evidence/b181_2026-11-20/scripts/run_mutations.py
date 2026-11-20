#!/usr/bin/env python3
"""Queue BH: B181-B183's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not run)
in a copy of the work copy; the test classes that must catch it run once; FAIL expected.
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T, C = "tools/party_add_game.py", "companion/party_minigame.py"
K, H = "tests.b181_every_digit.test_b181.", "tests.b178_score_kind.test_b178."
MUT = [
    ("the_sum_check_skipped", T, [('''"each side's cells = its final", not bad):''', '''"each side's cells = its final", True):''')],
     [K + "LineScore"]),
    ("a_pass_with_a_digit_unlearnt", T,
     [('''{"shown by fewer than two saves": few}, {"shown by fewer than two saves": []}, not few)''',
       '''{"shown by fewer than two saves": few}, {"shown by fewer than two saves": []}, True)''')], [K + "FinalsOnly"]),
    ("the_give_up_waits", C, [('''            if r.get("state") == "unreadable":''', '''            if False:''')],
     [H + "Hub"]),
    ("the_look_skipped", T,
     [('''                cells.add("the last look: every glyph is the digit it was read as", "not given (label/digits.png)",
                          "look=all", False)''', '''                cells.add("the last look: every glyph is the digit it was read as", "not given (label/digits.png)",
                          "look=all", True)'''),
      ('''                cells.add("the last look: every glyph is the digit it was read as", look["bad"] or "all", "all",
                          not look["bad"])''', '''                cells.add("the last look: every glyph is the digit it was read as", look["bad"] or "all", "all",
                          True)''')], [K + "LastLook"]),
]
ONLY = sys.argv[4:]
lines = []
for name, rel, pairs, suites in MUT:
    if ONLY and not any(name.startswith(o) for o in ONLY):
        continue
    M = SCR / ("mut_" + name)
    shutil.rmtree(M, ignore_errors=True)
    shutil.copytree(W, M, ignore=shutil.ignore_patterns("__pycache__"))
    p = M / rel
    s = p.read_text()
    missing = [old for old, _ in pairs if s.count(old) != 1]
    if missing:
        lines.append(f"{name} ({rel}) -> ANCHOR MISSING, not run: {missing[0][:60]!r}")
        shutil.rmtree(M, ignore_errors=True)
        continue
    for old, new in pairs:
        s = s.replace(old, new)
    p.write_text(s)
    r = subprocess.run(["timeout", "3600", sys.executable, "-W", "ignore", "-m", "unittest", *suites], cwd=M,
                       capture_output=True, text=True)
    got = " ".join(ln for ln in (r.stdout + r.stderr).splitlines()
                   if ln.startswith(("Ran", "OK", "FAILED", "FAIL:", "ERROR:")))
    lines.append(f"{name} ({rel}) -> {' '.join(suites)}: {got}")
    shutil.rmtree(M, ignore_errors=True)
lines.append(f"temp dirs left: {len(os.listdir(os.environ.get('TMPDIR', '/tmp')))}")
Path(OUT).write_text("\n".join(lines) + "\n")
print("\n".join(lines))
