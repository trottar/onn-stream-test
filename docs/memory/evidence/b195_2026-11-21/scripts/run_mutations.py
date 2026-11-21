#!/usr/bin/env python3
"""Queue BK: B196 / B197's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not
run) in a copy of the work copy; the test that must catch it runs once; FAIL expected (BI's runner, reused).
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T, E = "tools/party_add_game.py", "tools/h7_endscreen.py"
K = "tests.b195_close_solo.test_b195."
MUT = [
    ("M1_the_befores_ended_before_the_comparison", T,
     [('''    changed = None
    if before is not None:                                   # bench ran: its before''',
       '''    end_solo_mark(code)
    before = read_json(home(code) / "files_before.json")
    changed = None
    if before is not None:                                   # bench ran: its before''')],
     [K + "Close.test_2_a_users_slot_named_before_the_befores_end"]),
    ("M2_a_users_slot_left_out", T,
     [('''            if rname in ("states", "setups' states") and any(kind.startswith(f"the hub's slot {n}") for n in HUB_SLOTS):''',
       '''            if rname in ("states", "setups' states") and "slot" in kind:''')],
     [K + "Close.test_2_a_users_slot_named_before_the_befores_end"]),
    ("M3_met_with_the_go_unread", T,
     [('''              BARS["real_switches_read"][0], real == BARS["real_switches_read"][0])''',
       '''              BARS["real_switches_read"][0], "the end" in real)''')],
     [K + "Solo.test_1_the_go_listed_not_met"]),
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
    lines.append(f"{name}: {'CAUGHT' if p.returncode != 0 else 'NOT CAUGHT'} ({' '.join(tail)})")
    shutil.rmtree(work, ignore_errors=True)
left = list((SCR / "tmp").iterdir()) if (SCR / "tmp").exists() else []
lines.append(f"temp dirs left: {len(left)}")
OUT.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
