#!/usr/bin/env python3
"""Queue BD: B167's and B169's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not
run) in a copy of the work copy; the suites that must catch it run once; FAIL expected.
usage: run_mutations.py <work copy> <repo> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, REPO, OUT, SCR = (Path(a) for a in sys.argv[1:5])
os.environ["H7_GIT_REPO"] = str(REPO)
T = "tools/party_add_game.py"
C = "tools/party_add_game_capture.py"
MUT = [
    ("reason_swallowed", T, [('        reason = getattr(exc, "reason", None)\n', '        reason = None\n')],
     ["b167_pictures_start"]),
    ("core_back_to_b95", C, [("        self.core = hub_core(system)", "        self.core = proof.SYSTEMS[system][0]")],
     ["b167_pictures_start"]),
    ("display_not_passed", C, [("        env.update(display)", "        pass")], ["b167_pictures_start"]),
    ("busy_check_off", C, [("            if hub_busy():", "            if False:")], ["b167_pictures_start"]),
    ("log_reasons_off", C, [("    for line, reason in LOG_REASONS:", "    for line, reason in ():")], ["b167_pictures_start"]),
    ("labels_first_frame", T, [("            anchor = max(range(len(small)), key=lambda i: (sum(near[i]), -i))",
                                "            anchor = 0")], ["b167_pictures_start"]),
    ("rules_begin_off", T, [("    if rules_begin.is_file():", "    if False:")], ["b163_rehearse"]),
    ("card_cell_always_met", T, [('    cells.add("the board showed one card", n_cards, 1, n_cards == 1)',
                                  '    cells.add("the board showed one card", n_cards, 1, True)')], ["b169_solo_cells"]),
    ("no_before_at_solo", T, [('            if b.get("described") or not fb.is_file():', '            if False:')],
     ["b169_solo_cells"]),
]
lines = []
ONLY = sys.argv[5:]
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
                           capture_output=True, text=True, timeout=2400)
        summ = " ".join(ln for ln in r.stderr.splitlines()
                        if ln.startswith(("Ran", "OK", "FAILED", "FAIL:", "ERROR:")))[:700]
        lines.append(f"{name} ({rel}) -> {t}: {summ}")
    shutil.rmtree(M, ignore_errors=True)
lines.append(f"temp dirs left: {len(os.listdir(os.environ.get('TMPDIR', '/tmp')))}")
Path(OUT).write_text("\n".join(lines) + "\n")
print("\n".join(lines))
