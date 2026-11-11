#!/usr/bin/env python3
"""B97 settle: the hub's cached PS1 (and SNES, for one line) cheat lists, read in place — counts only. For every code line
in every cached file the manifest names: its shape (the type digits, the address field's width, the value's width);
which types write a constant to RAM; and how many descriptions name a player, per pattern. No name, title, id, address,
value or path printed. usage: settle_ps1_forms.py <repo>"""
import collections, json, re, sys
from pathlib import Path
REPO = Path(sys.argv[1])
man = json.loads((REPO / "data/games/cheats.json").read_text())["games"]
PAT = {"player N": r"\bplayer\s*[1-4]\b", "PN": r"\bp\s?[1-4]\b", "NP": r"\b[1-4]\s?p\b",
       "Nst/Nnd player": r"\b(1st|2nd|3rd|4th)\s+player\b", "player one/two": r"\bplayer\s+(one|two|three|four)\b"}
for system in ("ps1", "snes"):
    files = shapes = 0
    shape = collections.Counter(); per_pat_codes = collections.Counter(); per_pat_lists = collections.Counter()
    lists_with_player = 0; codes = 0; named = 0; named_ram_const = 0
    for rec in man.values():
        if not isinstance(rec, dict) or rec.get("status") != "cached" or rec.get("system") != system:
            continue
        for f in rec.get("files", []):
            p = REPO / f.get("local_path", "")
            if not p.is_file():
                continue
            files += 1
            kv = {}
            for line in p.read_text(errors="replace").splitlines():
                m = re.match(r'\s*cheat(\d+)_(desc|code)\s*=\s*"?(.*?)"?\s*$', line)
                if m:
                    kv.setdefault(int(m.group(1)), {})[m.group(2)] = m.group(3)
            hit_list = set()
            for i, e in kv.items():
                code, desc = e.get("code", ""), e.get("desc", "")
                if not code:
                    continue
                codes += 1
                parts = [x for x in re.split(r"[+\s]+", code.strip()) if x]
                lines = [parts[j] + " " + parts[j + 1] for j in range(0, len(parts) - 1, 2)] if system == "ps1" else parts
                kinds = []
                for ln in lines:
                    if system == "ps1":
                        m = re.fullmatch(r"([0-9A-Fa-f]{2})([0-9A-Fa-f]{6}) ([0-9A-Fa-f]{4})", ln)
                        k = f"type {m.group(1).upper()}, address 6 hex, value 4 hex" if m else "other shape"
                    else:
                        if re.fullmatch(r"7[EF][0-9A-Fa-f]{4}[:=]?[0-9A-Fa-f]{2}", ln):
                            k = "RAM write, bank 7E/7F (PAR aaaaaavv or raw addr:val)"
                        elif re.fullmatch(r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}", ln):
                            k = "Game Genie xxxx-xxxx (ROM)"
                        elif re.fullmatch(r"[0-9A-Fa-f]{6}[:=]?[0-9A-Fa-f]{2}", ln):
                            k = "other bank aaaaaa(:)vv (ROM or other)"
                        else:
                            k = "other shape"
                    shape[k] += 1; kinds.append(k)
                d = desc.casefold()
                hits = [n for n, rx in PAT.items() if re.search(rx, d)]
                for n in hits:
                    per_pat_codes[n] += 1; hit_list.add(n)
                if hits:
                    named += 1
                    if system == "ps1" and kinds and all(k.startswith(("type 80", "type 30")) for k in kinds):
                        named_ram_const += 1
                    if system == "snes" and kinds and all(k.startswith("RAM write") for k in kinds):
                        named_ram_const += 1
            for n in hit_list:
                per_pat_lists[n] += 1
            lists_with_player += bool(hit_list)
    print(f"{system}: files {files}; codes {codes}; code lines by shape:")
    for k, v in shape.most_common():
        print(f"  {v:6d}  {k}")
    print(f"  codes whose description names a player: {named} (of them every line a constant RAM write: {named_ram_const});"
          f" lists carrying such codes: {lists_with_player} of {files}")
    for n in PAT:
        print(f"  pattern '{n}': codes {per_pat_codes[n]}, lists {per_pat_lists[n]}")
