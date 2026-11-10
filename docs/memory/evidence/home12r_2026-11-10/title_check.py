#!/usr/bin/env python3
"""HOME-12R title check (ART-1R's): no title, game id, serial-like token or path from the hub's records appears in the given files.
Reads the hub's metadata / cheat records (local) and prints counts and file names only."""
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1]); files = [Path(p) for p in sys.argv[2:]]
needles = set()
md = json.loads((root / "data/games/metadata.json").read_text())["games"]
ch = json.loads((root / "data/games/cheats.json").read_text()).get("games", {})
for rec in list(md.values()) + list(ch.values()):
    for k in ("id", "scanned_title", "canonical_title", "relative_path"):
        v = str(rec.get(k) or "").strip()
        if len(v) >= 6: needles.add(v.casefold())
    m = rec.get("match") or {}
    for k in ("canonical_title", "source_key"):
        v = str(m.get(k) or "").strip()
        if len(v) >= 6: needles.add(v.casefold())
    for k in ("developer", "publisher"):
        v = str((m.get("metadata") or {}).get(k) or "").strip()
        if len(v) >= 4: needles.add(v.casefold())
# system / maker names that are also the systems' own names (e.g. a publisher equal to a console maker) are not titles
SYSTEM_WORDS = {"nintendo", "sony", "sega", "playstation", "gamecube", "nintendo 64"}
dropped = sorted(x for x in needles if x in SYSTEM_WORDS); needles -= set(dropped)
print(f"excluded as system names: {len(dropped)}")
hits = 0
for f in files:
    t = f.read_text(errors="replace").casefold()
    n = sum(1 for x in needles if x in t)
    hits += n
    print(("HIT " if n else "OK  ") + str(f) + (f" ({n})" if n else ""))
print(f"needles {len(needles)}; files {len(files)}; hits {hits}")
