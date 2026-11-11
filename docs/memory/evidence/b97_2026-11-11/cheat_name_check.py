#!/usr/bin/env python3
"""Queue AJ: no cheat name in the files this queue wrote. Loaded in process and never printed: every description in
every cheat list the hub has cached (data/games/cheats.json's files, any system). A description of 12 or more
characters found (case-folded, whitespace collapsed) in a file is a FAIL. Made-up fixture names live in the test code,
which is not passed to this check. Prints OK / FAIL per file, never the value."""
import json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
names = set()
man = json.loads((REPO / "data/games/cheats.json").read_text())["games"]
for rec in man.values():
    if not isinstance(rec, dict):
        continue
    for f in rec.get("files", []):
        p = REPO / f.get("local_path", "")
        if p.is_file():
            for m in re.finditer(r'cheat\d+_desc\s*=\s*"?(.*?)"?\s*$', p.read_text(errors="replace"), re.M):
                d = " ".join(m.group(1).casefold().split())
                if len(d) >= 12:
                    names.add(d)
fails = 0
for f in [Path(p).resolve() for p in sys.argv[1:]]:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.name.endswith("_check.txt"):
            continue
        text = " ".join(p.read_text(errors="replace").casefold().split())
        hit = any(n in text for n in names)
        print(("FAIL" if hit else "OK  "), p.relative_to(REPO))
        fails += hit
print(f"checked against {len(names)} cheat descriptions (none printed); FAILS {fails}")
