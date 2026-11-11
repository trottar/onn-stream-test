#!/usr/bin/env python3
"""B97 settle, second pass: the PS1 code strings' written forms (hex masked) and the code types once every form is read
as (type, 6-hex address, 4-hex value). Counts only; no name, title, id, address, value or path printed.
usage: settle_ps1_forms2.py <repo>"""
import collections, json, re, sys
from pathlib import Path
REPO = Path(sys.argv[1])
man = json.loads((REPO / "data/games/cheats.json").read_text())["games"]
FORMS = [("8 hex + 4 hex, lines joined by '+'", r"[0-9A-Fa-f]{8}\+[0-9A-Fa-f?]{4}(\+[0-9A-Fa-f]{8}\+[0-9A-Fa-f?]{4})*"),
         ("'$' + 12 hex, lines joined by '+'", r"\$[0-9A-Fa-f]{8}[0-9A-Fa-f?]{4}(\+\$[0-9A-Fa-f]{8}[0-9A-Fa-f?]{4})*"),
         ("8 hex ':' 4 hex", r"[0-9A-Fa-f]{8}:[0-9A-Fa-f?]{4}(\+[0-9A-Fa-f]{8}:[0-9A-Fa-f?]{4})*"),
         ("4 hex chunks joined by '+' (multiple of 3)", r"[0-9A-Fa-f]{4}(\+[0-9A-Fa-f?]{4})+")]
def lines(code):
    t = re.findall(r"[0-9A-Fa-f?]+", code)
    if all(len(x) == 4 for x in t) and len(t) % 3 == 0:
        return [(t[i] + t[i + 1], t[i + 2]) for i in range(0, len(t), 3)]
    if all(len(x) == 12 for x in t):
        return [(x[:8], x[8:]) for x in t]
    if len(t) % 2 == 0 and all(len(t[i]) == 8 and len(t[i + 1]) == 4 for i in range(0, len(t), 2)):
        return [(t[i], t[i + 1]) for i in range(0, len(t), 2)]
    return None
form = collections.Counter(); typ = collections.Counter(); unread = 0; placeholder = 0; codes = 0; cache_files = 0
for rec in man.values():
    if not isinstance(rec, dict) or rec.get("status") != "cached" or rec.get("system") != "ps1": continue
    for f in rec["files"]:
        p = REPO / f["local_path"]
        if not p.is_file(): continue
        cache_files += 1
        for line in p.read_text(errors="replace").splitlines():
            m = re.match(r'\s*cheat(\d+)_code\s*=\s*"?(.*?)"?\s*$', line)
            if not m or not m.group(2): continue
            code = m.group(2).strip(); codes += 1
            form[next((n for n, rx in FORMS if re.fullmatch(rx, code)), "other")] += 1
            ls = lines(code)
            if ls is None: unread += 1; continue
            for a, v in ls:
                if "?" in a: unread += 1; continue
                if "?" in v: placeholder += 1
                typ[a[:2].upper()] += 1
print(f"ps1: files {cache_files}; codes {codes}; written forms:")
for k, v in form.most_common(): print(f"  {v:5d}  {k}")
print(f"  codes not read as lines: {unread}; lines with a value to choose ('?'): {placeholder}")
print("  lines by type (first two hex digits):", ", ".join(f"{k} {v}" for k, v in typ.most_common()))
