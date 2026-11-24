#!/usr/bin/env python3
"""Queue BM: no name of T92 in the files this queue wrote. Loaded in process from T92's binding (off the repo, read
only), never printed: its title (whole, and without its bracketed parts), its game id, its game file's name and stem,
and its setup's id when it has one. Case-folded, as a substring for ids and the file's name, as whole words for the
title. Prints OK / FAIL per file, never the value."""
import json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
b = json.loads((Path.home() / "privyhub_h7" / "add_game" / "T92" / "binding.json").read_text())
words, subs = set(), set()
title = str(b.get("title") or "")
for t in (title, re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", title)):
    t = " ".join(t.split())
    if len(t) >= 5:
        words.add(t.casefold())
for v in (b.get("game"), (b.get("cheat") or {}).get("profile_id")):
    if v and len(str(v)) >= 6:
        subs.add(str(v).casefold())
rel = Path(str(b.get("relative_path") or ""))
for v in (rel.name, rel.stem):
    if len(v) >= 6:
        subs.add(v.casefold())
fails = 0
for f in [Path(p).resolve() for p in sys.argv[1:]]:
    text = f.read_text(errors="replace").casefold()
    bad = any(s in text for s in subs) or any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", text) for w in words)
    print(("FAIL" if bad else "OK  "), f.relative_to(REPO))
    fails += bad
print("FAILS", fails)
