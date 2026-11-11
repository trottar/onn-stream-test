#!/usr/bin/env python3
"""B96 (queue AI's B94 runner, the runtime source split out): each mutation is one exact text replacement in one file
of a fresh copy of <source>'s companion/, tools/, tests/ (the source: the /tmp snapshot of the item's tree); RetroArch
and its cores linked read-only from <repo>/runtime and the base config copied from <repo>; the suite is run on that copy
and must FAIL for the mutation to count as caught. The copy is removed after each mutation; nothing in the tree or the
source is changed.

usage: mutate.py <source copy> <repo> <mutations.json> <suite dir> <suite pattern>
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

src, repo = Path(sys.argv[1]), Path(sys.argv[2])
muts = json.loads(Path(sys.argv[3]).read_text())
suite, pattern = sys.argv[4], sys.argv[5]
caught = 0
for m in muts:
    work = Path(tempfile.mkdtemp(prefix="b_q22aj_mut_"))
    try:
        for d in ("companion", "tools", "tests"):
            shutil.copytree(src / d, work / d, ignore=shutil.ignore_patterns("__pycache__", "build", ".gradle"))
        (work / "runtime").symlink_to(repo / "runtime")
        (work / "data/games/retroarch").mkdir(parents=True)
        shutil.copy2(repo / "data/games/retroarch/retroarch.cfg", work / "data/games/retroarch/retroarch.cfg")
        f = work / m["file"]
        text = f.read_text()
        n = text.count(m["old"])
        if n != 1:
            print(f"{m['id']} SKIP (the text occurs {n} times)")
            continue
        f.write_text(text.replace(m["old"], m["new"]))
        r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", suite, "-p", pattern],
                           cwd=work, capture_output=True, text=True, timeout=3600)
        tail = [l for l in r.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
        ok = r.returncode != 0
        caught += ok
        print(f"{m['id']} {'CAUGHT' if ok else 'MISSED'} ({' '.join(tail)}) -- {m['why']}", flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
print(f"caught {caught} / {len(muts)}")
