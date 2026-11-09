import shutil, subprocess, sys, tempfile, os
from pathlib import Path
SRC = Path("/tmp/b_q17y_b69")
M = [
 ("M1 the pause key sent with a silent clock", "companion/gamecube_session.py",
  "        if tid is None or self.ticks(tid) is None or not self.window():\n            self.kill(self.pid, signal.SIGSTOP)                 # a silent clock: no key at all\n            self.paused_by = \"sigstop\"\n        elif self.key(PAUSE_KEY) and self.watch(tid, stand=True):",
  "        if self.key(PAUSE_KEY) and self.watch(tid, stand=True):"),
 ("M2 the plugin imports without the flag", "companion/plugins/games.py",
  "_gc_session = None\nif (os.environ.get(\"PRIVYHUB_GAMECUBE\") or \"\").strip() == \"1\":\n    import gamecube_session as _gc_session\n",
  "import gamecube_session as _gc_session\n"),
 ("M3 the rewind skip removed", "companion/hold_rewind.py",
  "            if getattr(self.emulator, \"_launch_kind\", None) == \"dolphin\" and not (",
  "            if False and not ("),
 ("M4 the size skip removed", "companion/gamecube_session.py",
  "MIN_TITLE_BYTES = 1 << 20", "MIN_TITLE_BYTES = 0"),
 ("M5 the save confirmed before the file stands", "companion/gamecube_session.py",
  "                if prev is None or prev[0] != sig:\n                    seen[name] = (sig, now)\n                elif",
  "                if False:\n                    pass\n                elif True or"),
]
base = Path(os.environ.get("TMPDIR", "/tmp"))
for title, rel, old, new in M:
    d = Path(tempfile.mkdtemp(prefix="b69_mut_", dir=base))
    for sub in ("companion", "tools", "tests"):
        shutil.copytree(SRC / sub, d / sub, ignore=shutil.ignore_patterns("__pycache__"))
    f = d / rel
    s = f.read_text()
    assert s.count(old) == 1, title
    f.write_text(s.replace(old, new))
    r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests/gamecube_session"], cwd=d,
                       capture_output=True, text=True, timeout=600)
    tail = [l for l in r.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
    failed = [l.split("(")[1].split(")")[0].split(".")[-1] if "(" in l else l for l in r.stderr.splitlines()
              if l.startswith(("FAIL:", "ERROR:"))]
    print(f"{title}: {'CAUGHT' if r.returncode else 'SURVIVED'} -- tests/gamecube_session: {' / '.join(tail)}; "
          f"failing: {', '.join(failed)}")
    shutil.rmtree(d)
