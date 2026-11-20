#!/usr/bin/env python3
"""Queue BG: B178's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not run) in a
copy of the work copy; the B178 test classes that must catch it run once; FAIL expected.
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T, E, C = "tools/party_add_game.py", "tools/h7_endscreen.py", "companion/party_minigame.py"
K = "tests.b178_score_kind.test_b178."
MUT = [
    ("score_read_from_a_spec_that_saw_the_save", T,
     [('''    """The spec learnt without these saves (learn's own call). -> (spec, arrays, why not or None)."""
    runs = {r: v for r, v in labels["runs"].items() if r not in members}''',
       '''    """The spec learnt without these saves (learn's own call). -> (spec, arrays, why not or None)."""
    runs = dict(labels["runs"])''')], [K + "Learn"]),
    ("a_tie_taken_as_a_win", C,
     [('won = mg["seats"][got.index(top)] if got.count(top) == 1 else None', 'won = mg["seats"][got.index(top)]')],
     [K + "Hub"]),
    ("an_unread_digit_guessed", E,
     [('            digs += best[len(place["group"]):] if ok else "?"', '            digs += best[len(place["group"]):]')],
     [K + "Reads"]),
    ("the_role_check_skipped", T,
     [("        ahead = all(nums[k - 1] > x for j, x in enumerate(nums) if j != k - 1)", "        ahead = True")],
     [K + "LabelChecks"]),
    ("one_reading_where_two_disagree", T,
     [('        same = v["by"] == "user" or (len(rd) == 2 and rd[0] == rd[1])', "        same = True")],
     [K + "LabelChecks"]),
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
