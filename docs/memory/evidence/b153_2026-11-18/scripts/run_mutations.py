#!/usr/bin/env python3
"""Queue BA: B153's and B155's mutations — each one change (one or more exact anchors, each found once, else the
mutation is reported ANCHOR MISSING and not run) in a copy of the work copy; the suites that must catch it run once;
FAIL expected. usage: run_mutations.py <work copy> <repo> <out file> <scratch>"""
import os, shutil, subprocess, sys
from pathlib import Path
W, REPO, OUT, SCR = (Path(a) for a in sys.argv[1:5])
os.environ["H7_GIT_REPO"] = str(REPO)
MUT = [
    ("not_armed", "companion/party_minigame.py",
     [("        self._arm_fast(ns, int(pid))                         # B153", "        pass  #")],
     ["b153_party_switch_length"]),
    ("capture_term_kept", "companion/native_session_io.py",
     [("        if now:   # B153: SIGKILL at once\n            self._kill_process_now(process)",
       "        if now:   # B153: SIGKILL at once\n            self._kill_process(process)")],
     ["b153_party_switch_length"]),
    ("sound_after_the_check", "companion/native_stream.py",
     [("        if fast:   # B153: a planned switch's new sound starts now", "        if False:  # (mutation)"),
      ("        if not fast:\n            self._start_session_io_locked(", "        if True:\n            self._start_session_io_locked(")],
     ["b153_party_switch_length"]),
    ("any_pid_taken", "companion/native_stream.py",
     [("        armed = getattr(self, \"_party_switch_pid\", None)\n        self._party_switch_pid = None\n"
       "        return armed is not None and armed == int(process_id)",
       "        armed = getattr(self, \"_party_switch_pid\", None)\n        self._party_switch_pid = None\n"
       "        return armed is not None")],
     ["b153_party_switch_length"]),
    ("keys_not_read", "companion/party_minigame.py",
     [("            if assigned != [f'{key} = \"{value}\"']:", "            if False:")],
     ["b155_party_keys_written"]),
    ("keys_from_the_arm", "companion/party_minigame.py",
     [("        keys = bool(mg.get(\"keys_written\"))", "        keys = True")],
     ["b155_party_keys_written"]),
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
