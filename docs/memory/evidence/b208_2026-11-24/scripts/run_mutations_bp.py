"""Queue BP's mutations, each in its own copy of tools/, companion/, tests/ (never the repo); an anchor that does not
match exactly once stops the run (loud)."""
import shutil, subprocess, sys, os
from pathlib import Path
REPO = Path(__file__).resolve().parents[5]
BASE = Path.home() / "b208_scratch" / "mut"
M = [
 ("a region the session did not name taken (the region's bounds ignored)", "tools/party_steps.py",
  "m = E._ink(a, pol, r, contrast)[y0:y1 + 1, x0:x1 + 1]", "m = E._ink(a, pol, r, contrast)",
  "tests/b208_survey", "test_b208.Survey"),
 ("a box the session did not name taken (the next box)", "tools/party_steps.py",
  "        x0, y0, x1, y1 = boxes[i - 1]\n", "        x0, y0, x1, y1 = boxes[min(i, len(boxes) - 1)]\n",
  "tests/b208_survey", "test_b208.Survey"),
 ("a search for a place (the place finder called by train)", "tools/party_steps.py",
  "    places = score_places(code, b, kept)\n    cells = pag.Cells()",
  "    places = score_places(code, b, kept)\n    E._find_place({}, {}, None)\n    cells = pag.Cells()",
  "tests/b208_survey", "test_b208.Path_"),
 ("a never-seen symbol counted (train)", "tools/party_steps.py",
  "    never = sorted(x for x in syms if counts.get(x, 0) == 0)\n    ask = sorted(set(never) | set(dropped))\n    cells.add(\"gate 3: every symbol the result can show learnt (none never seen)\", ask or \"all\", \"all\", not ask)\n    # the spec",
  "    never = []\n    ask = sorted(set(never) | set(dropped))\n    cells.add(\"gate 3: every symbol the result can show learnt (none never seen)\", ask or \"all\", \"all\", not ask)\n    # the spec",
  "tests/b208_survey", "test_b208.Path_"),
 ("a never-seen symbol not asked (plan)", "tools/party_steps.py",
  "    never = [x for x in syms if counts[x] == 0]", "    never = []", "tests/b208_survey", "test_b208.Path_"),
 ("a once-seen symbol counted with a synthetic variant not read", "tools/party_steps.py",
  "    b_ = bool(got) and all(g == sym for g in got)", "    b_ = True", "tests/b208_survey", "test_b208.Gates"),
 ("the bar moved", "tools/party_add_game.py", '"rigid_min": (0.0995,', '"rigid_min": (0.09,',
  "tests/b208_survey", "test_b208.Gates"),
 ("the hub keeps without the flag", "companion/party_minigame.py",
  '        if self.environ.get("PRIVYHUB_PARTY") != "1":\n            return\n        try:\n            game = mg["entry"]["game"]',
  '        try:\n            game = mg["entry"]["game"]', "tests/b210_keep_result", "test_b210.Off"),
 ("the watch holds pictures without the flag", "companion/h7_minigame.py",
  'if (self._environ.get("PRIVYHUB_PARTY") == "1" and spec.get("version") in (4, 5)',
  'if (spec.get("version") in (4, 5)', "tests/b210_keep_result", "test_b210.Off"),
]
only = sys.argv[1:]
for i, (name, f, a, b, suite, tests) in enumerate(M, 1):
    if only and str(i) not in only:
        continue
    d = BASE / f"m{i}"
    shutil.rmtree(d, ignore_errors=True)
    for sub in ("tools", "companion", "tests"):
        shutil.copytree(REPO / sub, d / sub, ignore=shutil.ignore_patterns("__pycache__"))
    p = d / f
    t = p.read_text()
    n = t.count(a)
    if n != 1:
        print(f"M{i} ANCHOR MISSED ({n}): {name}"); sys.exit(1)
    p.write_text(t.replace(a, b))
    env = dict(os.environ, TMPDIR=str(Path.home() / "b208_scratch" / "tmp"))
    r = subprocess.run([sys.executable, "-m", "unittest", tests], cwd=d / suite, env=env, capture_output=True, text=True,
                       timeout=1800)
    last = [ln for ln in r.stderr.splitlines() if ln.startswith(("OK", "FAILED", "Ran"))]
    print(f"M{i} {'CAUGHT' if r.returncode != 0 else 'NOT CAUGHT'}: {name} — {' / '.join(last)}")
    shutil.rmtree(d, ignore_errors=True)
