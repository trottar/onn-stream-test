#!/usr/bin/env python3
"""Queue BB: B157's and B158's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not
run) in a copy of the work copy; the suites that must catch it run once; FAIL expected.
usage: run_mutations.py <work copy> <repo> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, REPO, OUT, SCR = (Path(a) for a in sys.argv[1:5])
os.environ["H7_GIT_REPO"] = str(REPO)
T = "tools/party_add_game.py"
MUT = [
    ("margin_bar_loosened", T, [('"margin_needed_min": (0.0796,', '"margin_needed_min": (0.05,')], ["b157_add_game"]),
    ("predecessor_gate_skipped", T, [('    v = load_verdict(code, stage)\n    if not v or v.get("verdict") != "PASS":',
                                      '    v = {"verdict": "PASS", "inputs": inputs_digest}\n    if not v or v.get("verdict") != "PASS":')],
     ["b157_add_game"]),
    ("paused_cell_always_met", T, [('len(reads) >= BARS["paused_reads_min"][0] and all(reads))', 'True)')], ["b157_add_game"]),
    ("files_cell_always_met", T, [('    cells.add("every file after = before", len(changed), 0, not changed)',
                                   '    cells.add("every file after = before", len(changed), 0, True)')], ["b157_add_game"]),
    ("guard_off", T, [('        low = text.casefold()\n        for n in self.names:', '        low = text.casefold()\n        for n in []:')],
     ["b157_add_game"]),
    ("no_restart_guard", T, [('        why = users_session()\n        if why is not None:', '        why = None\n        if why is not None:')],
     ["b157_add_game"]),
    ("winner_seat_wrong", "companion/party_minigame.py",
     [('won = {"winner": mg["seats"][port - 1]} if port is not None else {}', 'won = {"winner": port} if port is not None else {}')],
     ["b158_winner_only"]),
    ("winner_with_scores_listed", "companion/party_minigame.py",
     [('if side.get("result") != "winner" or "scores" in side or "places_to_scores" in side or not 2 <= n <= 4:',
       'if side.get("result") != "winner" or not 2 <= n <= 4:')], ["b158_winner_only"]),
]
lines = []
ONLY = sys.argv[5:]                       # optional: run only these mutations
for name, rel, pairs, suites in MUT:
    if ONLY and name not in ONLY:
        continue
    M = SCR / f"mut_{name}"
    shutil.rmtree(M, ignore_errors=True)
    shutil.copytree(W, M, ignore=shutil.ignore_patterns("__pycache__"))
    p = M / rel
    s = p.read_text()
    missing = [old for old, _ in pairs if s.count(old) != 1]
    if missing:
        lines.append(f"{name} ({rel}): ANCHOR MISSING - not run")
        shutil.rmtree(M, ignore_errors=True)
        continue
    for old, new in pairs:
        s = s.replace(old, new)
    p.write_text(s)
    for t in suites:
        env = {k: v for k, v in os.environ.items() if k not in ("PRIVYPARTY_GODOT", "PRIVYPARTY_REPO")}
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", f"tests/{t}"], cwd=M, env=env,
                           capture_output=True, text=True, timeout=1800)
        summ = " ".join(ln for ln in r.stderr.splitlines()
                        if ln.startswith(("Ran", "OK", "FAILED", "FAIL:", "ERROR:")))[:600]
        lines.append(f"{name} ({rel}) -> {t}: {summ}")
    shutil.rmtree(M, ignore_errors=True)
lines.append(f"temp dirs left: {len(os.listdir(os.environ.get('TMPDIR', '/tmp')))}")
Path(OUT).write_text("\n".join(lines) + "\n")
print("\n".join(lines))
