#!/usr/bin/env python3
"""B80: the hub's own PCSX2 logs and bundle, read-only, counts only (no serial, CRC, title or file name printed;
the hub's id cache is NOT written: ids_from_logs is called directly)."""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "companion"))
import ps2_session as ps2
import ps2_patches as pp
titles = ps2.list_titles(ps2.read_paths(REPO)["games_dir"])
ids = pp.ids_from_logs(REPO / ps2.DATA_DIR / "logs")
app = ps2.find_appimage(REPO)
known = offered = 0
counts = {"ws": 0, "ni": 0, "60": 0}
for t in titles:
    hit = ids.get(Path(t["relative"]).name)
    if not hit:
        continue
    known += 1
    av = pp.available(pp.bundle_groups(app, *hit))
    offered += bool(av)
    for k in av:
        counts[k] += 1
print(f"PS2 titles listed: {len(titles)}; serial/CRC seen in PCSX2's kept logs: {known}; with a bundled patch: "
      f"{offered} (widescreen {counts['ws']}, no interlacing {counts['ni']}, 60 fps {counts['60']})")
