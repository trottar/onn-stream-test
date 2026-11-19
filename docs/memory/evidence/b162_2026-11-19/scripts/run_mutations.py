#!/usr/bin/env python3
"""Queue BC: B162's and B163's mutations — each one change (exact anchors, each found once, else ANCHOR MISSING and not
run) in a copy of the work copy; the suites that must catch it run once; FAIL expected.
usage: run_mutations.py <work copy> <repo> <out file> <scratch> [only ...]"""
import os, shutil, subprocess, sys
from pathlib import Path
W, REPO, OUT, SCR = (Path(a) for a in sys.argv[1:5])
os.environ["H7_GIT_REPO"] = str(REPO)
T = "tools/party_add_game.py"
PM = "companion/party_minigame.py"
G = "companion/plugins/games.py"
MUT = [
    ("list_filter_off", PM, [("        if only is not None:                     # B162: the title under test alone",
                              "        if False:                     # B162: the title under test alone")], ["b162_solo_safe"]),
    ("route_loopback_off", G, [('''        if action == "party-minigame-only" and _party_minigame is not None:
            if str(client_ip or "") not in _h7_minigame.LOOPBACK:''', '''        if action == "party-minigame-only" and _party_minigame is not None:
            if False:''')], ["b162_solo_safe"]),
    ("title_cell_always_met", T, [('"this title >= 1, another 0", this >= 1 and len(ids) == this)',
                                   '"this title >= 1, another 0", True)')], ["b162_solo_safe"]),
    ("every_switch_read", T, [('        if t is not None and nxt is not None and nxt - t < BARS["listed_within_s"][0]:',
                               '        if False:')], ["b162_solo_safe"]),
    ("in_game_saves_compared", T, [("before.get(k) != after.get(k) and k not in own_saves)",
                                    "before.get(k) != after.get(k))")], ["b162_solo_safe"]),
    ("xbox_words_never", T, [('    return "playstation" if all(sony) else "xbox" if not any(sony) else "both"',
                              '    return "playstation"')], ["b162_solo_safe"]),
    ("clear_on_read_skipped", T, [("    only_clear()                                             # B162: the setting cleared first",
                                   "    pass                                                     # B162: the setting cleared first")],
     ["b162_solo_safe"]),
    ("clear_on_close_skipped", T, [("    only_clear()                                             # B162: the one-title setting cleared",
                                    "    pass                                                     # B162: the one-title setting cleared")],
     ["b162_solo_safe"]),
    ("rehearse_into_real_rules", T, [('    os.environ.update({"PRIVYHUB_H7_RULES": str(scratch / "rules"),',
                                      '    os.environ.update({"PRIVYHUB_H7_RULES": str(rules_folder()),')], ["b163_rehearse"]),
    ("ending_cell_always_met", T, [('"the same, ended, its own ending", got_scr is not None and got_scr == got_real and as_role)',
                                    '"the same, ended, its own ending", True)')], ["b163_rehearse"]),
    ("scratch_kept", T, [("        shutil.rmtree(scratch, ignore_errors=True)\n    shas_after",
                          "        pass\n    shas_after")], ["b163_rehearse"]),
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
