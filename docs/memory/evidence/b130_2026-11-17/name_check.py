#!/usr/bin/env python3
"""Queue AS: no character name or cheat name in the files this queue wrote. The words (the two character names and the
cheat's name that RetroArch's notice showed on the two C2 pictures looked at) are read from a file off the repo, given
as argv[1], never printed; whole words, case-folded. Prints OK / HIT (count) per file, never the word."""
import re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
words = [w.strip().casefold() for w in Path(sys.argv[1]).read_text().splitlines() if w.strip()]
hits = 0
for f in [Path(p).resolve() for p in sys.argv[2:]]:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.name.endswith("_check.txt"):
            continue
        text = p.read_text(errors="replace").casefold()
        n = sum(len(re.findall(r"(?<![\w])" + re.escape(w) + r"(?![\w])", text)) for w in words)
        print(("HIT (%d)" % n if n else "OK "), p.relative_to(REPO))
        hits += bool(n)
print("HITS", hits)
