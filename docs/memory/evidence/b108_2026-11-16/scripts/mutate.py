#!/usr/bin/env python3
"""B101 (B96-B100's runner, unchanged; queue AI's B94 runner, the runtime source split out): each mutation is one exact text replacement in one file
of a fresh copy of <source>'s companion/, tools/, tests/ (the source: the /tmp snapshot of the item's tree); RetroArch
and its cores linked read-only from <repo>/runtime and the base config copied from <repo>; the suite is run on that copy
and must FAIL for the mutation to count as caught. The copy is removed after each mutation; nothing in the tree or the
source is changed.

usage: mutate.py <source copy> <repo> <mutations.json> <suite dir[,suite dir...]> <suite pattern>

Queue AN (B104 / B105): B101's runner with one change — several suite dirs (comma-separated) are run in turn for each
mutation, and the mutation counts as caught when any of them fails; H7_GIT_REPO passed through for the flag-absent
comparisons; the temp prefix b_q27ao_mut_.
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
    work = Path(tempfile.mkdtemp(prefix="b_q27ao_mut_"))
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
        ok, tail = False, []
        for one in suite.split(","):
            r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", one, "-p", pattern],
                               cwd=work, capture_output=True, text=True, timeout=3600)
            tail += [one.split("/")[-1] + ":"] + [l for l in r.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
            if r.returncode != 0:
                ok = True
                break
        caught += ok
        print(f"{m['id']} {'CAUGHT' if ok else 'MISSED'} ({' '.join(tail)}) -- {m['why']}", flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
print(f"caught {caught} / {len(muts)}")
