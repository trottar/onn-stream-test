#!/usr/bin/env python3
"""B97 settle, third pass (run inline at 16:44Z, kept here and re-run): the code types per written form in the hub's
cached PS1 lists, and whether any 80 / 30 address is at or above 2 MiB. Counts only; no name, title, id, address,
value or path printed. usage: settle_types_per_form.py <repo>"""
import collections, json, re, sys
from pathlib import Path
REPO = Path(sys.argv[1])
man = json.loads((REPO / "data/games/cheats.json").read_text())["games"]
t = collections.defaultdict(collections.Counter); hi = collections.Counter()
for rec in man.values():
    if not isinstance(rec, dict) or rec.get("status") != "cached" or rec.get("system") != "ps1": continue
    for f in rec["files"]:
        p = REPO / f["local_path"]
        if not p.is_file(): continue
        for line in p.read_text(errors="replace").splitlines():
            m = re.match(r'\s*cheat(\d+)_code\s*=\s*"?(.*?)"?\s*$', line)
            if not m or not m.group(2): continue
            code = m.group(2).strip(); tok = re.findall(r"[0-9A-Fa-f?]+", code)
            form = ("'$' + 12 hex" if code.startswith("$") else "8 hex ':' 4 hex" if ":" in code else
                    "4-hex chunks" if all(len(x) == 4 for x in tok) else
                    "8 hex + 4 hex" if all(len(x) in (8, 4) for x in tok) else "other")
            if form == "4-hex chunks":
                for i in range(0, len(tok) - 2, 3):
                    t[form][tok[i][:2].upper()] += 1
            for x in tok:
                if len(x) in (8, 12):
                    t[form][x[:2].upper()] += 1
                    if x[:2].upper() in ("80", "30") and "?" not in x[2:8]:
                        hi["at or above 2 MiB" if int(x[2:8], 16) >= 0x200000 else "below 2 MiB"] += 1
for k, v in t.items():
    print(f"{k}: lines by type " + ", ".join(f"{a} {b}" for a, b in v.most_common(8)))
print("type 80 / 30 addresses:", dict(hi))
