#!/usr/bin/env python3
"""Queue BI: B185-B188's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not run)
in a copy of the work copy; the test classes that must catch it run once; FAIL expected (B181's runner, reused).
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T = "tools/party_add_game.py"
K = "tests.b185_overtime.test_b185."
MUT = [
    ("a_one_save_column_refused", T,
     [('''                    cols.append(f"P{k + 1} column {c + 1}")''', '''                    diff = True''')],
     [K + "Overtime.test_1_one_overtime_save_counts"]),
    ("a_missing_sample_asked_of_the_user", T,
     [('''                        if wch in only:''', '''                        if False:'''),
      ('''ASK_REASONS = ("readings", "sum")''', '''ASK_REASONS = ("readings", "sum", "read back")''')],
     [K + "Overtime.test_4_t90s_shape"]),
    ("the_user_asked_for_a_read_back_contradiction", T,
     [('''ASK_REASONS = ("readings", "sum")''', '''ASK_REASONS = ("readings", "sum", "read back")''')],
     [K + "Ask.test_3_a_read_back_contradiction_is_never_asked"]),
    ("a_final_alone_taken", T,
     [('''        if v["by"] == "user" and lined_now and not all(cl for cl, _f in _sides(v["readings"][0])):''',
       '''        if False:''')],
     [K + "Ask.test_1_two_readings_differ_twice_then_the_user"]),
    ("a_digit_seen_once_counted", T,
     [('''            own = [g[4] for g in mine if g[3] == t[3] and (g[1], g[2]) != (t[1], t[2])]''',
       '''            own = [g[4] for g in mine if g[3] == t[3]]'''),
      ('''                  "learnt": len(tests) >= 2 and back == len(tests) and met}''',
       '''                  "learnt": len(tests) >= 1 and back == len(tests) and met}''')],
     [K + "OneSave.test_2_a_digit_one_save_shows_once"]),
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
