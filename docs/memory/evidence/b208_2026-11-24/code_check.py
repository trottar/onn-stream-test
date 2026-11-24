#!/usr/bin/env python3
"""Queue BP (queue BM's check, for T90, T91 and T92): no name of T90, T91 or T92 in the files this queue wrote. Loaded in
process from each one's binding (off the repo, read only), never printed: its title (whole, and without its bracketed
parts), its game id, its game file's name and stem, and its setup's id when it has one. Case-folded, as a substring for
ids and the file's name, as whole words for the title. Prints OK / FAIL per file, never the value."""
import json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
words, subs = set(), set()
for code in ("T90", "T91", "T92"):
    b = json.loads((Path.home() / "privyhub_h7" / "add_game" / code / "binding.json").read_text())
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
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.name.endswith("_check.txt"):
            continue
        text = p.read_text(errors="replace").casefold()
        bad = any(s in text for s in subs) or any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", text) for w in words)
        print(("FAIL" if bad else "OK  "), p.relative_to(REPO))
        fails += bad
print("FAILS", fails)
