"""Queue BP's mutations, each in its own copy of tools/, companion/, tests/ (never the repo); an anchor that does not
match exactly once stops the run (loud)."""
import shutil, subprocess, sys, os
from pathlib import Path
REPO = Path(__file__).resolve().parents[5]
BASE = Path(Path.home() / "b208_scratch" / "mut_bq")
M = [
 ("a test variant in the templates", "tools/party_steps.py",
  '        made[sym] = {"draws": draws, "valid": len(variants)}\n',
  '        made[sym] = {"draws": draws, "valid": len(variants)}\n        syn[min(src)] = list(syn[min(src)]) + variants\n',
  "tests/b214_variants", "test_b214.Ask"),
 ("counted with fewer than eight", "tools/party_steps.py",
  "    enough = len(variants) >= VARIANTS_NEEDED\n", "    enough = True\n", "tests/b214_variants", "test_b214.Variants"),
 ("the SYN_OWN share not checked", "tools/party_steps.py",
  "        if not cut.any() or float((cut & own).sum()) / float(cut.sum()) < SYN_OWN:\n",
  "        if not cut.any():\n", "tests/b214_variants", "test_b214.Variants"),
 ("plan's ask without train's gate 2", "tools/party_steps.py",
  '    ask = g.get("ask") if "ask" in g else [x for x in syms if counts[x] == 0]\n',
  '    ask = [x for x in syms if counts[x] == 0]\n', "tests/b214_variants", "test_b214.Ask"),
 ("register's three saves for a title the old learn wrote", "tools/party_add_game.py",
  '    if isinstance(side, dict) and "code" not in side:\n        return False\n', "", "tests/b214_variants",
  "test_b214.Register"),
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
