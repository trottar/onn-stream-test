#!/usr/bin/env python3
"""Queue AD: no title, game id, serial or path in the files this queue wrote. Loaded in process and never printed:
the paths file's values (folder paths); the hub's game ids (the keys of data/games/metadata.json and
library_state.json); the titles the hub's metadata already holds (scanned_title / canonical_title of its records);
the PS2 serials and CRCs in PCSX2's kept logs (B80's reader). Under queue AD's rule the drive and the library folders
are NOT listed (the real scan is A's dry run), so the three in-place systems' titles are not in the set; this queue's
files carry made-up titles only. A name of 5 or more characters (ids / serials / CRCs >= 6) found as a whole word,
case-folded, is a FAIL. Prints OK / FAIL per file, never the value."""
import json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "companion"))
names = set()
try:
    kv = dict(l.split("=", 1) for l in (REPO / "runtime/h3_p1_paths.txt").read_text().splitlines() if "=" in l)
    names |= {v.strip() for v in kv.values() if v.strip()}
except OSError:
    pass
ids = set()
for f in ("data/games/metadata.json", "data/games/library_state.json"):
    try:
        data = json.loads((REPO / f).read_text())
    except (OSError, ValueError):
        continue
    games = data.get("games") or {}
    ids |= {k.casefold() for k in games}
    for rec in games.values():
        if isinstance(rec, dict):
            for key in ("scanned_title", "canonical_title"):
                if rec.get(key):
                    names.add(str(rec[key]))
            m = rec.get("match") if isinstance(rec.get("match"), dict) else {}
            if m.get("canonical_title"):
                names.add(str(m["canonical_title"]))
import ps2_patches
for serial, crc in ps2_patches.ids_from_logs(REPO / "data/games/ps2/logs").values():
    ids |= {serial.casefold(), crc.casefold()}
names = {n.casefold() for n in names if len(n) >= 5} | {i for i in ids if len(i) >= 6}
fails = 0
for f in [Path(p).resolve() for p in sys.argv[1:]]:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.name in ("title_check.txt", "redact_check.txt"):
            continue
        text = p.read_text(errors="replace").casefold()
        hit = any(re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", text) for n in names)
        print(("FAIL" if hit else "OK  "), p.relative_to(REPO))
        fails += hit
print(f"checked against {len(names)} names / ids (none printed); FAILS {fails}")
