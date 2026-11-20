#!/usr/bin/env python3
"""Queue BF: B175's and B176's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not
run) in a copy of the work copy; the suites that must catch it run once; FAIL expected.
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T = "tools/party_add_game.py"
S175 = "b175_left_out"
MUT = [
    ("left_out_cell_always_met", T, [("            cells.add(f\"left out: {role}\", read, want, ok)",
                                     "            cells.add(f\"left out: {role}\", read, want, True)"),
                                    ("                cells.add(f\"left out: {role}\", why, want, False)",
                                     "                cells.add(f\"left out: {role}\", why, want, True)")], [S175]),
    ("left_out_save_still_among_the_sources", T,
     [("        runs = {r: v for r, v in labels[\"runs\"].items() if r not in members}",
       "        runs = dict(labels[\"runs\"])")], [S175]),
    ("margin_alone_always_met", T,
     [('              m is not None and float(m) >= BARS["margin_needed_min"][0])', "              True)")], [S175]),
    ("same_picture_measure_off", T, [("            if d < SAME_PICTURE[0]:", "            if False:")], [S175]),
    ("wrong_role_without_the_relabel_check", T,
     [("                if _relabel_fixes(es, b, pics, labels, role, other):", "                if True:"),
      ("            if wrong or full_ok or info[\"others\"] < 2 or met.get(f\"left out: {role}\", True):",
       "            if wrong or info[\"others\"] < 1 or met.get(f\"left out: {role}\", True):")], [S175]),
    ("wrong_role_line_still_asks", T,
     [("    for role, other in sorted((wrong or {}).items()):        # B176: first, a save in the wrong role — nothing asked",
       "    for role, other in []:")], [S175]),
]
lines = []
ONLY = sys.argv[4:]
for name, rel, pairs, suites in MUT:
    if ONLY and not any(name.startswith(o) for o in ONLY):
        continue
    M = SCR / ("mut_" + name.split()[0])
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
        r = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", f"tests/{t}"], cwd=M,
                           env=env, capture_output=True, text=True, timeout=2400)
        summ = " ".join(ln for ln in r.stderr.splitlines() if ln.startswith(("Ran", "OK", "FAILED", "FAIL:", "ERROR:")))[:700]
        lines.append(f"{name} ({rel}) -> {t}: {summ}")
        print(lines[-1], flush=True)
    shutil.rmtree(M, ignore_errors=True)
lines.append(f"temp dirs left: {len(os.listdir(os.environ.get('TMPDIR', '/tmp')))}")
Path(OUT).write_text("\n".join(lines) + "\n")
print("\n".join(lines[-1:]))
