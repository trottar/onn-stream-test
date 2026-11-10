#!/usr/bin/env python3
"""B85: the hub's own cheat lists before / after the clean-up, counts only. Each cached RetroArch file the manifest
names becomes the source the manager would list (index + name, its local path), is run through cheat_clean.clean()
from the given companion/ copy, and only counts are printed (per system: entries before, shown after, hidden by kind,
folded parts, variants; the biggest list before / after). No name, title, id or path printed.
usage: hub_before_after.py <companion dir>"""
import collections, json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, sys.argv[1])
import cheat_clean
man = json.loads((REPO / "data/games/cheats.json").read_text())["games"]
agg = collections.defaultdict(collections.Counter); big = collections.defaultdict(lambda: [0, 0])
for rec in man.values():
    if not isinstance(rec, dict) or rec.get("status") != "cached": continue
    system = rec.get("system", "?")
    for f in rec.get("files", []):
        lp = f.get("local_path", "")
        p = REPO / lp
        if not p.is_file(): continue
        descs = {}
        for line in p.read_text(errors="replace").splitlines():
            m = re.match(r'\s*cheat(\d+)_desc\s*=\s*"?(.*?)"?\s*$', line)
            if m: descs[int(m.group(1))] = m.group(2)
        src = {"source_index": 0, "provider": "libretro", "local_path": lp,
               "entries": [{"index": i, "description": d, "enabled": False} for i, d in sorted(descs.items())]}
        s = cheat_clean.clean({"system": system, "sources": [src]}, REPO)["sources"][0]
        a = agg[system]; a["files"] += 1; a["before"] += s["raw_count"]; a["after"] += s["shown_count"]
        for k, v in s["hidden"].items(): a["hidden_" + k] += v
        a["folded_parts"] += s["folded_parts"]
        a["variants"] += sum(1 for e in s["entries"] if e["variant_of"] is not None)
        a["player_sections"] += sum(1 for e in s["entries"] if e["group"].startswith("player"))
        a["other_section"] += sum(1 for e in s["entries"] if e["group"] == "other")
        if s["raw_count"] > big[system][0]: big[system] = [s["raw_count"], s["shown_count"]]
for system in sorted(agg):
    a = agg[system]
    print(f"{system}: files {a['files']}; entries before {a['before']} -> shown after {a['after']}; hidden: header "
          f"{a['hidden_header']}, trigger {a['hidden_trigger']}, enabler (applied with any pick) {a['hidden_enabler']}, "
          f"duplicate {a['hidden_duplicate']}; split parts folded {a['folded_parts']}; shown as variants {a['variants']};"
          f" in a player section {a['player_sections']}; under Other {a['other_section']}; the biggest list "
          f"{big[system][0]} -> {big[system][1]}")
