#!/usr/bin/env python3
"""B93 (queue AG's runner + a read-only runtime/ link and the base config): Queue AG's mutation runner (queue AF's, the CHEATS.md copy kept optional): each mutation is one exact text
replacement in one file of a fresh copy of <source>'s companion/, tools/, tests/ (plus docs/CHEATS.md from
<cheats_md> for B81's docs test); the suite is run on that copy and must FAIL for the mutation to count as caught.
The copy is removed after each mutation; nothing in the tree or the source is changed.

usage: mutate.py <source copy> <cheats_md> <mutations.json> <suite dir> <suite pattern>
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

src, cheats_md = Path(sys.argv[1]), Path(sys.argv[2])
muts = json.loads(Path(sys.argv[3]).read_text())
suite, pattern = sys.argv[4], sys.argv[5]
caught = 0
for m in muts:
    work = Path(tempfile.mkdtemp(prefix="b_q21ag_mut_"))
    try:
        for d in ("companion", "tools", "tests"):
            shutil.copytree(src / d, work / d, ignore=shutil.ignore_patterns("__pycache__", "build", ".gradle"))
        (work / "runtime").symlink_to(src / "runtime")          # B93: RetroArch and its cores, read only
        (work / "data/games/retroarch").mkdir(parents=True)
        shutil.copy2(src / "data/games/retroarch/retroarch.cfg", work / "data/games/retroarch/retroarch.cfg")
        (work / "docs").mkdir()
        if cheats_md.is_file():
            shutil.copy2(cheats_md, work / "docs/CHEATS.md")
        f = work / m["file"]
        text = f.read_text()
        n = text.count(m["old"])
        if n != 1:
            print(f"{m['id']} SKIP (the text occurs {n} times)")
            continue
        f.write_text(text.replace(m["old"], m["new"]))
        r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", suite, "-p", pattern],
                           cwd=work, capture_output=True, text=True, timeout=1800)
        tail = [l for l in r.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
        ok = r.returncode != 0
        caught += ok
        print(f"{m['id']} {'CAUGHT' if ok else 'MISSED'} ({' '.join(tail)}) -- {m['why']}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
print(f"caught {caught} / {len(muts)}")
