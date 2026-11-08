#!/usr/bin/env python3
"""B59: no title in the files this task wrote. The names are loaded in process and never printed: the stems of the
drive's N64, GameCube and PS2 folders (from the gitignored paths file), the hub's library stems and the folders below
its system folders, and the paths file's values. The system folders themselves (`games/snes`, …) are system names,
not titles, and are not loaded. A stem of 5 or more characters found (case-folded, as a whole word) in a file is a FAIL. Prints OK / FAIL per
file, never the value."""
import re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
kv = dict(l.split("=", 1) for l in (REPO / "runtime/h3_p1_paths.txt").read_text().splitlines() if "=" in l)
names = {v.strip() for v in kv.values() if v.strip()}
drive = Path(kv["GAMES_DIR"].strip()).parent
for folder in [drive / s for s in ("n64", "gamecube", "ps2")] + [REPO / "games"]:
    if folder.is_dir():
        names |= {p.stem for p in folder.rglob("*") if p.is_file()}
        names |= {p.name for p in folder.rglob("*") if p.is_dir() and p.parent != REPO / "games"}
names = {n.casefold() for n in names if len(n) >= 5}
fails = 0
for f in [Path(p).resolve() for p in sys.argv[1:]]:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.name in ("title_check.txt", "redact_check.txt"):
            continue
        text = p.read_text(errors="replace").casefold()
        bad = any(re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", text) for n in names)
        print(("FAIL title" if bad else "OK"), p.relative_to(REPO))
        fails += bad
print("FAILS", fails)
