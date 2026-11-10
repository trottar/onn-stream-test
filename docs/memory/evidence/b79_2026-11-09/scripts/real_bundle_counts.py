#!/usr/bin/env python3
"""B79: the real bundle and the drive's headers, read-only, counts only (no id, no title, no code name printed).
For each GameCube title the hub lists (the paths file's folder, B69's listing rules), read the disc id from its
header, then the names Dolphin's bundled files give for it (7z, into memory)."""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "companion"))
import gamecube_session as gc
import gc_cheats
folder = gc.read_dir(REPO)
appimage = gc.find_appimage(REPO)
titles = gc.list_titles(folder)
ids = with_codes = total = ar = gecko = 0
for t in titles:
    gid = gc_cheats.disc_id(t["path"])
    if not gid:
        continue
    ids += 1
    codes = gc_cheats.codes_for(gid, lambda n: gc_cheats.read_bundled(appimage, n))
    if codes:
        with_codes += 1
    total += len(codes)
    ar += sum(c["kind"] == "ar" for c in codes)
    gecko += sum(c["kind"] == "gecko" for c in codes)
print(f"GameCube titles listed: {len(titles)}; disc id read: {ids}; with at least one bundled code: {with_codes}; "
      f"codes in all: {total} (Action Replay {ar}, Gecko {gecko})")
