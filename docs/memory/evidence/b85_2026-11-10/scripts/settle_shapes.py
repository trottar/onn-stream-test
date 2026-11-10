#!/usr/bin/env python3
"""B85's settle, part 2, counts only: the shapes behind the repeats, the bare player rows and the activators.
- a bare "P1".."P4" row: what comes before it (a no-code entry = a header; a bare row; a named cheat);
- the separators inside names (a backslash, " - ", ":"), which turn sub-options into separate entries;
- entries whose every code line is a conditional (N64 D0-D3: does nothing alone in a one-entry cheat);
- repeats: how many are a bare player row, how many follow a header (a sub-option), how many sit apart.
Nothing printed but counts."""
import collections, json, re
from pathlib import Path
REPO = Path(__file__).resolve().parents[5]
man = json.loads((REPO / "data/games/cheats.json").read_text())["games"]
BARE = re.compile(r"^\W*(p[1-4]|player\s*[1-4])\W*$", re.I)
ENABLER = re.compile(r"\(m\)|must\s*be\s*on|enable\s*code|enabler|master\s*code|\bactivator\b|key\s*code", re.I)
def parse(text):
    kv = {}
    for line in text.splitlines():
        m = re.match(r'\s*(cheat(\d+)_(desc|code|enable))\s*=\s*"?(.*?)"?\s*$', line)
        if m: kv.setdefault(int(m.group(2)), {})[m.group(3)] = m.group(4)
    return [kv[k] for k in sorted(kv)]
out = collections.defaultdict(collections.Counter)
for rec in man.values():
    if not isinstance(rec, dict) or rec.get("status") != "cached": continue
    s = out[rec.get("system", "?")]
    for f in rec.get("files", []):
        p = REPO / f.get("local_path", "")
        if not p.is_file(): continue
        items = parse(p.read_text(errors="replace"))
        seen = set(); last_header = False
        for i, it in enumerate(items):
            d = it.get("desc", ""); lines = [c.strip() for c in it.get("code", "").split("+") if c.strip()]
            prev = items[i - 1] if i else None
            if "\\" in d: s["name_has_backslash"] += 1
            if " - " in d: s["name_has_dash_sep"] += 1
            if ":" in d: s["name_has_colon"] += 1
            if not lines: s["no_code"] += 1
            cond_only = bool(lines) and all(c[:2].upper() in ("D0", "D1", "D2", "D3") for c in lines)
            if cond_only:
                s["conditional_only"] += 1
                if ENABLER.search(d): s["conditional_only_enabler_named"] += 1
            if ENABLER.search(d) and not cond_only: s["enabler_named_with_writes"] += 1
            if ENABLER.search(d) and any(c[:2].upper() in ("F0", "F1", "DE", "EE", "FF") for c in lines): s["enabler_named_boot_or_hw_type"] += 1
            if BARE.match(d):
                if prev is None: s["bare_first"] += 1
                elif not [c for c in prev.get("code", "").split("+") if c.strip()]: s["bare_after_header"] += 1
                elif BARE.match(prev.get("desc", "")): s["bare_after_bare"] += 1
                else: s["bare_after_named_cheat"] += 1
            key = re.sub(r"\s+", " ", d).strip().casefold()
            if key in seen:
                s["repeat"] += 1
                if BARE.match(d): s["repeat_bare_player"] += 1
                elif last_header: s["repeat_after_header"] += 1
            seen.add(key)
            last_header = (not lines) or (last_header and bool(BARE.match(d)))
for k in sorted(out): print(k, dict(out[k]))

# --- part 3: each repeat against the name's first occurrence (single-line codes): option vs other target ---------
def addr_val(code):
    m = re.match(r"\s*([0-9A-Fa-f]{8})\s+([0-9A-Fa-f?]{4})\s*$", code)
    return (m.group(1).upper(), m.group(2).upper()) if m else None
rep = collections.defaultdict(collections.Counter)
for rec in man.values():
    if not isinstance(rec, dict) or rec.get("status") != "cached": continue
    r = rep[rec.get("system", "?")]
    for f in rec.get("files", []):
        p = REPO / f.get("local_path", "")
        if not p.is_file(): continue
        first = {}
        for it in parse(p.read_text(errors="replace")):
            key = re.sub(r"\s+", " ", it.get("desc", "")).strip().casefold()
            av = addr_val(it.get("code", ""))
            if key in first:
                a0 = first[key]
                if av is None or a0 is None: r["multi_line_or_other"] += 1
                elif av == a0: r["identical_code"] += 1
                elif av[0] == a0[0]: r["same_address_other_value (an option)"] += 1
                elif av[1] == a0[1]: r["other_address_same_value (another target)"] += 1
                else: r["both_differ"] += 1
            else:
                first[key] = av
print("repeats vs the first occurrence:")
for k in sorted(rep): print(" ", k, dict(rep[k]))
