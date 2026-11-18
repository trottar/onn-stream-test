#!/usr/bin/env python3
"""Queue AV: no game id or cheat setup id of the two party titles in the files this queue wrote. Loaded in process from
the rules folder (read only), never printed: each `<game id>.party.json`'s game id and its `cheat.profile_id` (whole,
and the 12-character prefix a setup's begin carries). Case-folded, as a substring (ids are long and specific).
Prints OK / FAIL per file, never the value."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
RULES = Path.home() / "privyhub_h7" / "rules"
ids = set()
for side in RULES.glob("*.party.json"):
    gid = side.name.split(".")[0]
    ids.add(gid.casefold())
    pid = str((json.loads(side.read_text()).get("cheat") or {}).get("profile_id") or "")
    if pid:
        ids |= {pid.casefold(), pid[:12].casefold()}
ids = {i for i in ids if len(i) >= 8}
fails = 0
for f in [Path(p).resolve() for p in sys.argv[1:]]:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.name.endswith("_check.txt"):
            continue
        text = p.read_text(errors="replace").casefold()
        hit = any(i in text for i in ids)
        print(("FAIL" if hit else "OK  "), p.relative_to(REPO))
        fails += hit
print(f"checked against {len(ids)} ids (none printed); FAILS {fails}")
