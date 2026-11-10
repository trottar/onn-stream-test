#!/usr/bin/env python3
"""Queue AC (B74's title check, extended): no title, game id, disc id, serial or CRC in the files this queue wrote.
Loaded in process and never printed: B74's names (the drive's N64 / GameCube / PS2 stems and folder names, the hub's
library stems, the paths file's values, Dolphin's game ids from its StateSaves / Cache names), plus for this queue:
the GameCube disc ids read from the drive's headers (B79's reader), the PS2 serials and CRCs in PCSX2's kept logs
(B80's reader), and the hub's game ids (the keys of data/games/metadata.json and library_state.json). A name of 5 or
more characters (ids / serials / CRCs at any length >= 6) found as a whole word, case-folded, is a FAIL. Prints OK /
FAIL per file, never the value."""
import json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "companion"))
kv = dict(l.split("=", 1) for l in (REPO / "runtime/h3_p1_paths.txt").read_text().splitlines() if "=" in l)
names = {v.strip() for v in kv.values() if v.strip()}
drive = Path(kv["GAMES_DIR"].strip()).parent
for folder in [drive / s for s in ("n64", "gamecube", "ps2")] + [REPO / "games"]:
    if folder.is_dir():
        names |= {p.stem for p in folder.rglob("*") if p.is_file()}
        names |= {p.name for p in folder.rglob("*") if p.is_dir() and p.parent != REPO / "games"}
for sub in ("StateSaves", "Cache"):
    d = REPO / "data/games/gamecube/user" / sub
    if d.is_dir():
        names |= {p.name.split(".")[0] for p in d.iterdir() if p.is_file() and p.name.split(".")[0] != "lastState"}
names = {n.casefold() for n in names if len(n) >= 5}
ids = set()
import gamecube_session as gc, gc_cheats, ps2_patches
for t in gc.list_titles(gc.read_dir(REPO)):
    g = gc_cheats.disc_id(t["path"])
    if g:
        ids |= {g.casefold()}
for serial, crc in ps2_patches.ids_from_logs(REPO / "data/games/ps2/logs").values():
    ids |= {serial.casefold(), crc.casefold()}
for f in ("data/games/metadata.json", "data/games/library_state.json"):
    try:
        data = json.loads((REPO / f).read_text())
        ids |= {k.casefold() for k in (data.get("games") or {})}
    except (OSError, ValueError):
        pass
names |= {i for i in ids if len(i) >= 6}
fails = 0
for f in [Path(p).resolve() for p in sys.argv[1:]]:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.name in ("title_check.txt", "redact_check.txt") or "__pycache__" in p.parts:
            continue
        text = p.read_text(errors="replace").casefold()
        bad = any(re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", text) for n in names)
        print(("FAIL title" if bad else "OK"), p.relative_to(REPO))
        fails += bad
print("FAILS", fails, "(names loaded:", len(names), ")" if False else ")")
