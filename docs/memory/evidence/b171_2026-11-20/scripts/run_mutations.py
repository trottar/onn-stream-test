#!/usr/bin/env python3
"""Queue BE: B171's and B172's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not
run) in a copy of the work copy; the suites that must catch it run once; FAIL expected.
usage: run_mutations.py <work copy> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, OUT, SCR = (Path(a) for a in sys.argv[1:4])
T = "tools/party_add_game.py"
S171 = "b171_more_saves"
MUT = [
    ("margin_always_met (a weak spec passes)", T,
     [('              m is not None and float(m) >= BARS["margin_needed_min"][0])', "              True)")],
     [S171, "b163_rehearse"]),
    ("learn_bars_off (a weak spec passes: separable, margin, unknown always met)", T,
     [("              bool(sep) and all(sep.values()))", "              True)"),
      ('              m is not None and float(m) >= BARS["margin_needed_min"][0])', "              True)"),
      ('              unknown / n <= BARS["unknown_share_max"][0])', "              True)")], [S171]),
    ("no_line_written (no role named)", T,
     [("    ask = one_more_save(b, cells, kept, conf)", "    ask = None")], [S171]),
    ("suffix_kept_as_a_class", T,
     [('    return SUFFIX.sub("", role)                              # B171: end_P1_2 is a save of end_P1',
       "    return role")], [S171]),
    ("cap_off", T, [("    open_ = sorted((count[e], e) for e in named if count[e] < SAVES_PER_ENDING_MAX)",
                     "    open_ = sorted((count[e], e) for e in named)")], [S171]),
    ("register_one_per_ending", T, [("def _roles_needed(players: int, result: str, per_ending: int = 2)",
                                     "def _roles_needed(players: int, result: str, per_ending: int = 1)")], [S171]),
    ("every_extra_promoted", T,
     [("        role = next_role(want, roles) if got is not None and got[0] == want else None",
       "        role = next_role(want, roles)")], [S171]),
    ("ask_names_a_kept_role", T, [("    role = next_role(ending, kept)", "    role = ending")], [S171]),
    ("pictures_all_made_again", T, [("        if role in made and run.is_dir():\n            continue\n", "")], [S171]),
    ("rehearse_reads_by_role_not_class", T,
     [('    endings = {r: (home(code) / "pictures" / r, _role_class(r)) for r in roles if r.startswith("end_")}',
       '    endings = {r: (home(code) / "pictures" / r, r) for r in roles if r.startswith("end_")}')],
     [S171, "b163_rehearse"]),
    ("close_keeps_the_mark (B172)", T,
     [("    end_solo_mark(code)                                      # B172: the next solo writes its own mark and befores",
       "    pass")], [S171]),
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
