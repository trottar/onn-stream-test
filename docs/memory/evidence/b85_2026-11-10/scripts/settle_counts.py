#!/usr/bin/env python3
"""B85's settle, counts only: the hub's cached RetroArch cheat files (data/games/cheats.json's records) read in memory;
per system: files, entries, repeats (same cleaned name earlier in the file; same code vs different code), split parts
("n of m" / "part n"), enabler / activator names, P1-P4 tags, bare "P1" / "P2" rows, code types (the first byte of each
code line). Nothing printed but counts and code-type prefixes (two hex digits); no name, title, id or path."""
import collections, json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[5]
man = json.loads((REPO / "data/games/cheats.json").read_text())["games"]
ENABLER = re.compile(r"\(m\)|must\s*be\s*on|enable\s*code|enabler|master\s*code|\bactivator\b|key\s*code|\bmust\b", re.I)
ACTIV = re.compile(r"\bactivator\b|press|button", re.I)
PTAG = re.compile(r"(?<![A-Za-z0-9])(p[1-4]|[1-4]p|player\s*[1-4])(?![A-Za-z0-9])", re.I)
BARE = re.compile(r"^\W*(p[1-4]|player\s*[1-4])\W*$", re.I)
SPLIT = re.compile(r"\(?\b(\d+)\s*(of|/)\s*(\d+)\b\)?|\bpart\s*\d+\b", re.I)
def parse(text):
    kv = {}
    for line in text.splitlines():
        m = re.match(r'\s*(cheat(\d+)_(desc|code|enable))\s*=\s*"?(.*?)"?\s*$', line)
        if m: kv.setdefault(int(m.group(2)), {})[m.group(3)] = m.group(4)
    return [kv[k] for k in sorted(kv)]
def norm(d): return re.sub(r"\s+", " ", SPLIT.sub("", d)).strip().casefold()
stats = collections.defaultdict(collections.Counter)
types = collections.defaultdict(collections.Counter)
etypes = collections.defaultdict(collections.Counter)
biggest = collections.Counter()
for rec in man.values():
    if not isinstance(rec, dict) or rec.get("status") != "cached": continue
    sysid = rec.get("system", "?")
    for f in rec.get("files", []):
        p = REPO / f.get("local_path", "")
        if not p.is_file(): stats[sysid]["file_missing"] += 1; continue
        items = parse(p.read_text(errors="replace"))
        s = stats[sysid]; s["files"] += 1; s["entries"] += len(items)
        biggest[sysid] = max(biggest[sysid], len(items))
        seen = {}
        for it in items:
            d = it.get("desc", ""); code = it.get("code", "")
            lines = [c.strip() for c in code.split("+") if c.strip()]
            for c in lines: types[sysid][c[:2].upper()] += 1
            n = norm(d)
            if n in seen:
                s["repeat"] += 1
                s["repeat_same_code" if seen[n] == code else "repeat_diff_code"] += 1
            else: seen[n] = code
            if SPLIT.search(d): s["split_named"] += 1
            if ENABLER.search(d):
                s["enabler_named"] += 1
                if ACTIV.search(d): s["activator_named"] += 1
                for c in lines: etypes[sysid][c[:2].upper()] += 1
            if PTAG.search(d): s["player_tag"] += 1
            if BARE.match(d): s["bare_player_row"] += 1; s["bare_player_row_codes"] += len(lines)
            if not lines: s["no_code_entry"] += 1
for sysid in sorted(stats):
    print(sysid, dict(stats[sysid]), "biggest", biggest[sysid])
    print("  code types (all):", dict(types[sysid].most_common(14)))
    print("  code types (enabler-named):", dict(etypes[sysid].most_common(10)))
