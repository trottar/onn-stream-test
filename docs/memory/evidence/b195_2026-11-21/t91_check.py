#!/usr/bin/env python3
"""Queue BJ: no private name of T91 in the files this queue wrote — loaded in process from its add_game binding (read
only) and never printed: its game id, title, relative path, content id and the find words' lines. Case-folded, as a
substring (each >= 5 characters; the title's words >= 5 characters each too). Prints OK / FAIL per file, never the value."""
import json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
b = json.loads((Path.home() / "privyhub_h7" / "add_game" / "T91" / "binding.json").read_text())
names = {str(b.get(k) or "") for k in ("game", "title", "relative_path", "content")}
names |= {Path(str(b.get("relative_path") or "")).stem}
names |= {w for w in re.findall(r"[A-Za-z0-9']+", str(b.get("title") or "")) if len(w) >= 5}
names = {n.casefold() for n in names if len(n) >= 5}
fails = 0
for f in [Path(p).resolve() for p in sys.argv[1:]]:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.suffix in (".png", ".npz") or p.name.endswith("_check.txt"):
            continue
        text = p.read_text(errors="replace").casefold()
        bad = any(n in text for n in names)
        print(("FAIL" if bad else "OK"), p.relative_to(REPO))
        fails += bad
print("FAILS", fails)
