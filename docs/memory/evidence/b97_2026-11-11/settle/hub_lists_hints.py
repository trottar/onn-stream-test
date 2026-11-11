#!/usr/bin/env python3
"""B97: what tools/h7_cheat_hints.py reads from the hub's cached PS1 and SNES lists, in place — counts only (no name,
title, id, address, value or path printed): lists with any hint; hint lines by kind; lists where P1 and P2 hints of
one kind and one width exist (a pair the search would test directly); of those, lists with a pair whose code names
match once the player tag is removed. usage: hub_lists_hints.py <repo>"""
import collections, json, sys
from pathlib import Path
REPO = Path(sys.argv[1])
sys.path.insert(0, str(REPO / "tools"))
import h7_cheat_hints as ch
man = json.loads((REPO / "data/games/cheats.json").read_text())["games"]
for system in ("ps1", "snes"):
    lists = with_hints = with_pair = with_named_pair = 0
    kinds = collections.Counter(); skipped = collections.Counter(); unreadable = 0
    for rec in man.values():
        if not isinstance(rec, dict) or rec.get("status") != "cached" or rec.get("system") != system:
            continue
        for f in rec.get("files", []):
            p = REPO / f.get("local_path", "")
            if not p.is_file():
                continue
            lists += 1
            r = ch.read_hints(p, system)
            unreadable += bool(r["unreadable"])
            skipped.update(r["skipped"])
            if not r["hints"]:
                continue
            with_hints += 1
            kinds.update(h["kind"] for h in r["hints"])
            by = collections.defaultdict(lambda: collections.defaultdict(list))
            for h in r["hints"]:
                by[(h["kind"], h["bytes"])][h["player"]].append(h["pair_group"])
            pair = [k for k, v in by.items() if "P1" in v and "P2" in v]
            with_pair += bool(pair)
            with_named_pair += any(set(by[k]["P1"]) & set(by[k]["P2"]) for k in pair)
    print(f"{system}: lists {lists} (unreadable {unreadable}); lists with any hint {with_hints}; hint lines by kind "
          f"{dict(kinds)}; lists with a P1 / P2 pair of one kind and width {with_pair}, of them with matching code "
          f"names {with_named_pair}; codes skipped {dict(skipped)}")
