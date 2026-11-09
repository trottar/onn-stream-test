"""B70-B72 host mutations: each an exact one-place edit in a fresh copy of /tmp/b_q18z_work (companion/, tools/,
tests/) under TMPDIR (the main disk), the item's suite run, the copy removed. Usage: mutate_host.py b70|b71|b72"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path
SRC = Path("/tmp/b_q18z_work")
M = {
 "b70": [
  ("M1 the pointer drawn again by default (the helper always empty)", "companion/native_stream.py",
   '    if (os.environ.get(CAPTURE_POINTER_ENV) or "").strip() == "1":\n        return []\n',
   '    if True:\n        return []\n', "tests/b70_capture_pointer"),
  ("M2 the option after the input (-i) instead of before the window", "companion/native_stream.py",
   '            *_capture_pointer_args(),   # B70\n            "-window_id",\n            str(window_id),\n            "-i",\n            display,',
   '            "-window_id",\n            str(window_id),\n            "-i",\n            display,\n            *_capture_pointer_args(),',
   "tests/b70_capture_pointer"),
 ],
 "b71": [
  ("M1 the eject before the steps removed", "companion/disc_swap.py",
   "        self._cmd(EJECT)\n        m = self._await(EJECTED_RE)\n",
   "        m = EJECTED_RE.search('[Disc] Ejected virtual disc tray')\n", "tests/b71_disc_swap"),
  ("M2 the close after the steps removed", "companion/disc_swap.py",
   "        self.sleep(GAP_S)\n        if not self._close():\n",
   "        self.sleep(GAP_S)\n        if False:\n", "tests/b71_disc_swap"),
  ("M3 the pause toggled around the swap", "companion/games/emulator_manager.py",
   "                    result = swapper.run(start, target)\n",
   "                    self._retroarch_network_request('PAUSE_TOGGLE', expect_response=False)\n                    result = swapper.run(start, target)\n",
   "tests/b71_disc_swap"),
  ("M4 the one-disc guard removed (n >= 1)", "companion/disc_swap.py",
   '    return {"discs": n, "disc": 1} if n > 1 else None\n',
   '    return {"discs": n, "disc": 1} if n >= 1 else None\n', "tests/b71_disc_swap"),
  ("M5 a LOAD keeps the old disc (the unknown removed)", "companion/games/emulator_manager.py",
   '            self._disc_session["disc"] = None\n            if isinstance(payload, dict) and "discs" in payload:\n                payload["disc"] = None\n',
   '            pass\n', "tests/b71_disc_swap"),
 ],
 "b72": [
  ("M1 (b) the counter-reset second kept in the min", "tools/diag_read.py",
   "                if k not in getattr(self, \"fps_reset\", ()) and k not in getattr(self, \"hold_resume\", ()):\n",
   "                if k not in getattr(self, \"hold_resume\", ()):\n", "tests/b72_small_readings"),
  ("M2 (c) the dolphin window not used", "tools/diag_read.py",
   "                onset = self.gc_hold_onset(ts(r[\"at_utc\"]))\n", "                onset = None\n",
   "tests/b72_small_readings"),
  ("M3 (d) no 20 class", "tools/gc_frames.py", "SEGMENT_RATES = (20, 30, 60)", "SEGMENT_RATES = (30, 60)",
   "tests/b72_small_readings"),
  ("M3b (d) the 20 class in the per-second cut too (the design's first form)", "tools/gc_frames.py",
   "RATES = (30, 60)           #", "RATES = (20, 30, 60)       #", "tests/b72_small_readings"),
  ("M4 (e) the SDL hint not set", "companion/gamecube_session.py",
   "        env[hint] = \",\".join(have)\n", "        pass\n", "tests/b72_small_readings"),
  ("M5 (f) the picture check not awaited (the save pressed during it)", "companion/rewind_cores.py",
   "        idle = self._gc_idle()\n        if not idle.is_set():\n", "        idle = self._gc_idle()\n        if False:\n",
   "tests/b72_small_readings"),
  ("M6 (g) the whitelist opened (every reply key in the row)", "companion/plugins/games.py",
   "                for key in self.STATE_REPLY_KEYS:\n", "                for key in payload:\n",
   "tests/b72_small_readings"),
 ],
}
base = Path(os.environ.get("TMPDIR", "/tmp"))
for title, rel, old, new, suite in M[sys.argv[1]]:
    d = Path(tempfile.mkdtemp(prefix=f"{sys.argv[1]}_mut_", dir=base))
    for sub in ("companion", "tools", "tests"):
        shutil.copytree(SRC / sub, d / sub, ignore=shutil.ignore_patterns("__pycache__"))
    f = d / rel
    s = f.read_text()
    assert s.count(old) == 1, title
    f.write_text(s.replace(old, new))
    r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", suite], cwd=d,
                       capture_output=True, text=True, timeout=900)
    tail = [l for l in r.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
    failed = [l.split("(")[0].split(":", 1)[1].strip() if "(" in l else l for l in r.stderr.splitlines()
              if l.startswith(("FAIL:", "ERROR:"))]
    print(f"{title}: {'CAUGHT' if r.returncode else 'SURVIVED'} -- {suite}: {' / '.join(tail).replace(chr(10),' ')}; "
          f"failing: {', '.join(failed)}")
    shutil.rmtree(d)
