#!/usr/bin/env python3
"""H7 (B97): hints from a game's own cheat list — the RAM addresses its per-player codes write.

    python3 tools/h7_cheat_hints.py --system ps1|snes --cheats <file.cht> [--counts]

The file is a cheat list in the hub's stored form (RetroArch's `.cht`: `cheatN_desc = "…"`, `cheatN_code = "…"`).
A code is a hint when its description names ONE player and it writes a constant to RAM:
  PS1 (GameShark lines `TTAAAAAA VVVV`, written '+'-joined, ':'-joined, or as 4-hex chunks three per line): type 80 →
      2 bytes, value VVVV; type 30 → 1 byte, value VV; the address AAAAAA & 0x1FFFFF (a RAM offset as the search reads
      it). Other types are not constant writes (the line skipped). The '$' + 12-hex form is another device's — skipped.
  SNES (`7E`/`7F` bank, `aaaaaavv`, `aaaaaa:vv` or `aaaaaa=vv`): 1 byte at (bank - 0x7E) * 0x10000 + aaaa; banks
      00-3F / 80-BF with aaaa < 0x2000 → the low work RAM; Game Genie and ROM banks skipped.
A value with '?' (chosen by the user) → value null; the address is still a hint.
The player: "P1", "P 1", "1P", "Player 1", "player one", "1st player" (case-folded); a description naming two different
players, or none, is skipped (counted). The kind, whole words, level-like first: level {health, energy, life, lives,
hp, power, vitality, stamina}; tally {round(s), win(s), victory/victories, score, points, ko(s)}; else other.

THE DESCRIPTION TEXT IS USED AT RUN TIME ONLY: the output carries the player, the address, the width, the value, the
kind, the code's index, its line and a pair group (codes whose descriptions are equal once the player tag is removed
share a number) — never the text. An unreadable, empty or non-cheat file gives no hints and the reason (never an error).
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

_CHT = re.compile(r'\s*cheat(\d+)_(desc|code)\s*=\s*"?(.*?)"?\s*$')
_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "1st": 1, "2nd": 2, "3rd": 3, "4th": 4}
_PLAYER = re.compile(r"(?<![a-z0-9])(?:p\s?([1-4])|([1-4])\s?p|player\s*([1-4])|player\s+(one|two|three|four)"
                     r"|(1st|2nd|3rd|4th)\s+player)(?![a-z0-9])")
LEVEL = ("health", "energy", "life", "lives", "hp", "power", "vitality", "stamina")
TALLY = ("round", "rounds", "win", "wins", "victory", "victories", "score", "points", "ko", "kos")


def players_named(desc: str) -> set[int]:
    out = set()
    for m in _PLAYER.finditer(desc.casefold()):
        g = next(x for x in m.groups() if x)
        out.add(_WORDS[g] if g in _WORDS else int(g))
    return out


def kind_of(desc: str) -> str:
    words = set(re.findall(r"[a-z]+", desc.casefold()))
    if words & set(LEVEL):
        return "level"
    if words & set(TALLY):
        return "tally"
    return "other"


def _stem(desc: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", _PLAYER.sub(" ", desc.casefold())))


def _ps1_lines(code: str) -> list[tuple[str, str]] | None:
    """[(TTAAAAAA, VVVV)] for the three readable forms; None for a form this tool does not read."""
    if "$" in code:
        return None
    tok = re.findall(r"[0-9A-Fa-f?]+", code)
    if tok and all(len(x) == 4 for x in tok) and len(tok) % 3 == 0:
        return [(tok[i] + tok[i + 1], tok[i + 2]) for i in range(0, len(tok), 3)]
    if tok and len(tok) % 2 == 0 and all(len(tok[i]) == 8 and len(tok[i + 1]) == 4 for i in range(0, len(tok), 2)):
        return [(tok[i], tok[i + 1]) for i in range(0, len(tok), 2)]
    return None


def _ps1_writes(code: str) -> tuple[list[dict], str | None]:
    lines = _ps1_lines(code)
    if lines is None:
        return [], "a form this tool does not read"
    out = []
    for n, (a, v) in enumerate(lines):
        t = a[:2].upper()
        if t not in ("80", "30") or "?" in a:
            continue
        size = 2 if t == "80" else 1
        value = None if "?" in v else int(v, 16) & (0xFFFF if size == 2 else 0xFF)
        out.append({"address": int(a[2:], 16) & 0x1FFFFF, "bytes": size, "value": value, "line": n})
    return out, None if out else "no constant RAM write"


def _snes_writes(code: str) -> tuple[list[dict], str | None]:
    out = []
    for n, part in enumerate(x for x in re.split(r"[+\s]+", code.strip()) if x):
        m = re.fullmatch(r"([0-9A-Fa-f]{2})([0-9A-Fa-f]{4})[:=]?([0-9A-Fa-f?]{2})", part)
        if not m:
            continue
        bank, addr = int(m.group(1), 16), int(m.group(2), 16)
        if bank in (0x7E, 0x7F):
            ram = (bank - 0x7E) * 0x10000 + addr
        elif (bank <= 0x3F or 0x80 <= bank <= 0xBF) and addr < 0x2000:
            ram = addr
        else:
            continue
        value = None if "?" in m.group(3) else int(m.group(3), 16)
        out.append({"address": ram, "bytes": 1, "value": value, "line": n})
    return out, None if out else "no constant RAM write"


def read_hints(path: Path | str, system: str) -> dict:
    """{"hints": [...], "codes": n, "skipped": {reason: n}, "unreadable": None | why} — never raises on a bad file."""
    empty = {"hints": [], "codes": 0, "skipped": {}}
    try:
        text = Path(path).read_text(errors="strict")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return dict(empty, unreadable=f"the file could not be read ({type(exc).__name__})")
    entries: dict[int, dict] = {}
    for line in text.splitlines():
        m = _CHT.match(line)
        if m:
            entries.setdefault(int(m.group(1)), {})[m.group(2)] = m.group(3)
    if not entries:
        return dict(empty, unreadable="no cheat entries in the file")
    writes = _ps1_writes if system == "ps1" else _snes_writes
    hints, skipped, stems = [], collections.Counter(), {}
    codes = 0
    for idx in sorted(entries):
        desc, code = entries[idx].get("desc", ""), entries[idx].get("code", "")
        if not code.strip():
            continue
        codes += 1
        named = players_named(desc)
        if not named:
            skipped["no player"] += 1
            continue
        if len(named) > 1:
            skipped["several players"] += 1
            continue
        ws, why = writes(code)
        if not ws:
            skipped[why] += 1
            continue
        group = stems.setdefault(_stem(desc), len(stems))
        p, kind = named.pop(), kind_of(desc)
        for w in ws:
            hints.append({"player": f"P{p}", "address": hex(w["address"]), "bytes": w["bytes"], "value": w["value"],
                          "kind": kind, "code": idx, "line": w["line"], "pair_group": group})
    return {"hints": hints, "codes": codes, "skipped": dict(skipped), "unreadable": None}


def counts(res: dict) -> dict:
    """Counts only (no address): by player and kind — the form a record carries."""
    by: dict = collections.defaultdict(collections.Counter)
    for h in res["hints"]:
        by[h["player"]][h["kind"]] += 1
    return {"codes": res["codes"], "hint_lines": len(res["hints"]),
            "codes_hinted": len({h["code"] for h in res["hints"]}),
            "by_player_kind": {p: dict(c) for p, c in sorted(by.items())}, "skipped": res["skipped"],
            "unreadable": res.get("unreadable")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--system", required=True, choices=("ps1", "snes"))
    ap.add_argument("--cheats", required=True, type=Path)
    ap.add_argument("--counts", action="store_true", help="counts by player and kind only (no address)")
    a = ap.parse_args(argv)
    res = read_hints(a.cheats, a.system)
    print(json.dumps(counts(res) if a.counts else res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
