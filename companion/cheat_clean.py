"""B85: the cheat list cleaned for the TV, every system (the `cheat-catalog` handler; the launch expands it back).

RetroArch's cheat lists (PS1, SNES, N64) carry cheat-cartridge leftovers: lone joypad conditionals ("activators": a
`D0`-`D3` line with nothing after it — they write nothing on their own), "must be on" master codes, heading rows with no
code, bare "P1" / "P2" rows, split "1 of 3" parts and the same name repeated for another target. `clean()` hides what
writes nothing, applies the "must be on" codes with any selection (`requires`), folds split parts into one entry
(`parts`), names the bare rows and the player tags in plain words ("Player 1"), groups the entries (general /
player1-4 / other / yours) and lists a repeated name's other codes under the first as "variant n". `expand()` turns the
onn's picks back into the file's real indexes at the launch. The user's own files are left as they are; Dolphin's
names are tidied and grouped, nothing hidden.

`PRIVYHUB_CHEAT_CLEAN=0` = today's raw list and launch. Design:
docs/memory/evidence/b85_2026-11-10/design_written_before_code.md (hashed before this code).
"""

from __future__ import annotations

import copy
import os
import re
from pathlib import Path
from typing import Any, Mapping

KNOB_ENV = "PRIVYHUB_CHEAT_CLEAN"
RETROARCH_PROVIDERS = {"libretro"}
USER_PROVIDERS = {"user", "user_pnach"}
TIDY_ONLY_PROVIDERS = {"dolphin_bundled"}
CONDITIONAL_SYSTEMS = {"n64", "ps1"}

_REQUIRED_NAME = re.compile(r"\(m\)|must\s*be\s*on|enable\s*code|\benabler\b|master\s*code|key\s*code", re.I)
_CONDITIONAL = re.compile(r"^[Dd][0-3][0-9A-Fa-f]{6}\s+[0-9A-Fa-f?]{4}$")
_PLAYER_TAG = re.compile(r"(?<![A-Za-z0-9])(?:p\s?([1-4])|([1-4])\s?p|player\s*([1-4]))(?![A-Za-z0-9])", re.I)
_BARE_PLAYER = re.compile(r"^\W*(?:p\s?([1-4])|([1-4])\s?p|player\s*([1-4]))\W*$", re.I)
_SPLIT = re.compile(r"\s*[\(\[]?\s*(?:\bpart\s*(\d+)(?:\s*of\s*(\d+))?\b|\b(\d+)\s*of\s*(\d+)\b)\s*[\)\]]?", re.I)
_TRAILING_CODE = re.compile(r"\s*(?:[\(\[]\s*[0-9A-Fa-f]{8}(?:\s+[0-9A-Fa-f?]{4})?\s*[\)\]]|-\s*[0-9A-Fa-f]{8}(?:\s+[0-9A-Fa-f?]{4})?)\s*$")
_TRAILING_M = re.compile(r"\s*\(\s*m\s*\)\s*$", re.I)
_EMPTY_BRACKETS = re.compile(r"\s*(?:\(\s*\)|\[\s*\])")
_DANGLING = re.compile(r"[\s\-:,;/]+$")
_CHT_LINE = re.compile(r'\s*cheat(\d+)_(desc|code)\s*=\s*"?(.*?)"?\s*$')


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return str(env.get(KNOB_ENV, "")).strip() != "0"


def player_of(name: str) -> int | None:
    m = _PLAYER_TAG.search(name or "")
    if not m:
        return None
    return int(next(g for g in m.groups() if g))


def tidy(name: str) -> str:
    """The name as the TV shows it: one space, "Player n", no trailing code / (M) / empty brackets."""
    text = re.sub(r"\s+", " ", (name or "").replace("\\", " — ")).strip()
    for _ in range(3):
        before = text
        text = _TRAILING_M.sub("", text)
        text = _TRAILING_CODE.sub("", text)
        text = _EMPTY_BRACKETS.sub("", text)
        text = _DANGLING.sub("", text)
        if text == before:
            break
    text = _PLAYER_TAG.sub(lambda m: f"Player {next(g for g in m.groups() if g)}", text)
    return text.strip() or (name or "").strip()


def read_codes(project_root: Path, local_path: str) -> dict[int, list[str]] | None:
    """`{index: [code lines]}` from a cached `.cht` (inside the project only); None when it cannot be read."""
    if not local_path:
        return None
    root = Path(project_root).resolve()
    path = (root / local_path).resolve()
    try:
        path.relative_to(root)
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except (OSError, ValueError):
        return None
    codes: dict[int, list[str]] = {}
    for line in text.splitlines():
        m = _CHT_LINE.match(line)
        if m and m.group(2) == "code":
            codes[int(m.group(1))] = [c.strip() for c in m.group(3).split("+") if c.strip()]
    return codes


def _clean_retroarch(source: dict[str, Any], system: str, project_root: Path) -> dict[str, Any]:
    entries = [e for e in source.get("entries", []) if isinstance(e, dict)]
    codes = read_codes(project_root, str(source.get("local_path", "")))
    hidden = {"header": 0, "trigger": 0, "enabler": 0, "duplicate": 0}
    requires: list[int] = []
    shown: list[dict[str, Any]] = []
    for e in entries:
        index = int(e.get("index", -1))
        name = str(e.get("description", ""))
        lines = codes.get(index) if codes is not None else None
        if lines is not None and not lines:
            hidden["header"] += 1
            continue
        if lines and system in CONDITIONAL_SYSTEMS and all(_CONDITIONAL.match(c) for c in lines):
            hidden["trigger"] += 1
            continue
        if _REQUIRED_NAME.search(name):
            if lines:
                hidden["enabler"] += 1
                requires.append(index)
                continue
            shown.append({"index": index, "name": name, "group": "other", "code": None})
            continue
        shown.append({"index": index, "name": name, "group": None, "code": tuple(lines) if lines else None})

    # split parts ("Part 2", "(Part 3)", "2 of 3", anywhere in the name): folded into one entry when the same base
    # name has parts numbered 1..k, k >= 2 (the hub's lists: "Part n" groups)
    bases: dict[str, list[tuple[int, dict[str, Any], str]]] = {}
    for item in shown:
        m = _SPLIT.search(item["name"])
        if not m:
            continue
        number = int(m.group(1) or m.group(3))
        base = re.sub(r"\s+", " ", (item["name"][:m.start()] + " " + item["name"][m.end():])).strip()
        if base:
            bases.setdefault(base.casefold(), []).append((number, item, base))
    folded_parts = 0
    drop: set[int] = set()
    for members in bases.values():
        numbers = sorted(n for n, _i, _b in members)
        if len(members) < 2 or numbers != list(range(1, len(members) + 1)):
            continue
        members.sort(key=lambda x: x[0])
        first = members[0][1]
        first["parts"] = [it["index"] for _n, it, _b in members]
        first["name"] = members[0][2]
        for _n, it, _b in members[1:]:
            drop.add(it["index"])
            folded_parts += 1
    shown = [s for s in shown if s["index"] not in drop]

    # labels and groups; a bare "P1" row takes the last shown cheat's name
    context = ""
    for item in shown:
        bare = _BARE_PLAYER.match(item["name"])
        if bare:
            n = int(next(g for g in bare.groups() if g))
            item["label"] = f"{context} — Player {n}" if context else f"Player {n}"
            item["group"] = f"player{n}"
            continue
        item["label"] = tidy(item["name"])
        context = tidy(_DANGLING.sub("", _PLAYER_TAG.sub("", item["name"])).strip()) or item["label"]
        if item["group"] is None:
            p = player_of(item["name"])
            item["group"] = f"player{p}" if p else "general"

    # repeats of a label: identical code folded, a different code listed under the first as "variant n"
    firsts: dict[str, dict[str, Any]] = {}
    out: list[dict[str, Any]] = []
    followers: dict[int, list[dict[str, Any]]] = {}
    for item in shown:
        key = item["label"].casefold()
        first = firsts.get(key)
        if first is None:
            firsts[key] = item
            item["codes_seen"] = {item["code"]}
            out.append(item)
            continue
        if item["code"] is not None and item["code"] in first["codes_seen"]:
            hidden["duplicate"] += 1
            continue
        first["codes_seen"].add(item["code"])
        group = followers.setdefault(first["index"], [])
        item["variant_of"] = first["index"]
        item["label"] = f"{first['label']} — variant {len(group) + 2}"
        group.append(item)

    result: list[dict[str, Any]] = []
    for item in out:
        for it in [item] + followers.get(item["index"], []):
            result.append({
                "index": it["index"],
                "description": it["label"],
                "enabled": False,
                "group": it["group"],
                "parts": it.get("parts", [it["index"]]),
                "requires": list(requires),
                "variant_of": it.get("variant_of"),
            })
    cleaned = {k: v for k, v in source.items() if k != "entries"}
    cleaned.update({"entries": result, "clean": True, "raw_count": len(entries), "shown_count": len(result),
                    "hidden": hidden, "folded_parts": folded_parts, "requires": list(requires)})
    return cleaned


def _clean_light(source: dict[str, Any], group_all: str | None) -> dict[str, Any]:
    result = []
    for e in source.get("entries", []):
        if not isinstance(e, dict):
            continue
        name = str(e.get("description", ""))
        p = player_of(name)
        result.append({**e,
                       "description": name if group_all == "yours" else tidy(name),
                       "group": group_all or (f"player{p}" if p else "general"),
                       "parts": [int(e.get("index", -1))], "requires": [], "variant_of": None})
    cleaned = {k: v for k, v in source.items() if k != "entries"}
    cleaned.update({"entries": result, "clean": True, "raw_count": len(result), "shown_count": len(result),
                    "hidden": {"header": 0, "trigger": 0, "enabler": 0, "duplicate": 0}, "folded_parts": 0,
                    "requires": []})
    return cleaned


def clean(catalog: dict[str, Any], project_root: Path) -> dict[str, Any]:
    """The catalog the onn reads, cleaned (a new dict; the manager's catalog is not changed)."""
    if not isinstance(catalog, dict) or not isinstance(catalog.get("sources"), list):
        return catalog
    out = copy.deepcopy(catalog)
    system = str(catalog.get("system", "")).strip().casefold()
    sources = []
    for source in out["sources"]:
        if not isinstance(source, dict):
            sources.append(source)
            continue
        provider = str(source.get("provider", ""))
        if provider in USER_PROVIDERS:
            sources.append(_clean_light(source, "yours"))
        elif provider in TIDY_ONLY_PROVIDERS:
            sources.append(_clean_light(source, None))
        elif provider in RETROARCH_PROVIDERS:
            sources.append(_clean_retroarch(source, system, project_root))
        else:
            sources.append(source)
    out["sources"] = sources
    out["clean"] = True
    return out


def expand(cleaned: dict[str, Any], source_index: int | None, indexes: list[int] | None) -> list[int] | None:
    """The onn's picks → the file's real indexes: each shown entry's parts, plus the source's required codes."""
    if source_index is None or indexes is None:
        return indexes
    source = next((s for s in cleaned.get("sources", []) if isinstance(s, dict)
                   and int(s.get("source_index", -1)) == int(source_index)), None)
    if source is None or not source.get("clean"):
        return indexes
    parts = {int(e["index"]): [int(i) for i in e.get("parts", [e["index"]])] for e in source.get("entries", [])}
    real: list[int] = []
    for i in indexes:
        for j in parts.get(int(i), [int(i)]):
            if j not in real:
                real.append(j)
    if real:
        for j in source.get("requires", []):
            if int(j) not in real:
                real.append(int(j))
    return sorted(real)
