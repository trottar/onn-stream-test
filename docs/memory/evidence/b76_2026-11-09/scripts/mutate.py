#!/usr/bin/env python3
"""Queue AC's mutation runner (B76-B81): each mutation is one exact text replacement in one file of a fresh copy of
companion/, tools/, tests/ (from the working tree); the item's suite is run on that copy and must FAIL for the
mutation to count as caught. The copy is removed after each mutation; nothing in the tree is changed.

usage: mutate.py <mutations.json> <suite dir> <suite pattern>
mutations.json: [{"id": "M1", "file": "companion/...", "old": "...", "new": "...", "why": "..."}]
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
muts = json.loads(Path(sys.argv[1]).read_text())
suite, pattern = sys.argv[2], sys.argv[3]
caught = 0
for m in muts:
    work = Path(tempfile.mkdtemp(prefix="b_q19ac_mut_"))
    try:
        for d in ("companion", "tools", "tests"):
            shutil.copytree(REPO / d, work / d, ignore=shutil.ignore_patterns("__pycache__", "build", ".gradle"))
        if (REPO / "docs/CHEATS.md").is_file():   # B81's docs test reads it (added after B76-B80's runs)
            (work / "docs").mkdir()
            shutil.copy2(REPO / "docs/CHEATS.md", work / "docs/CHEATS.md")
        f = work / m["file"]
        text = f.read_text()
        n = text.count(m["old"])
        if n != 1:
            print(f"{m['id']} SKIP (the text occurs {n} times)")
            continue
        f.write_text(text.replace(m["old"], m["new"]))
        r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", suite, "-p", pattern],
                           cwd=work, capture_output=True, text=True, timeout=900)
        tail = [l for l in r.stderr.splitlines() if l.startswith(("Ran ", "OK", "FAILED"))]
        ok = r.returncode != 0
        caught += ok
        print(f"{m['id']} {'CAUGHT' if ok else 'MISSED'} ({' '.join(tail)}) -- {m['why']}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
print(f"caught {caught} / {len(muts)}")
