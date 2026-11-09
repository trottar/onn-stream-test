#!/usr/bin/env python3
"""B68: one list entry per multi-disc PS1 title already in the hub's library -- an `.m3u` per set written beside its
discs (the list already hides what an `.m3u` names, and titles the set from its name). Behind PRIVYHUB_IMPORT=1.

    PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py plan  [--json]
    PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py apply [--migrate-states]
    PRIVYHUB_IMPORT=1 python3 tools/library_m3u.py undo

- A set: the library's PS1 `.cue` / `.chd` files of one title (B56's "(Disc N)" rule, the same folder), 2 or more
  discs numbered 1..n. Reported, never planned: `disc_gap`, `covered` (a disc another `.m3u` names), `already` (the
  same `.m3u` is there), `m3u_differs` (an `.m3u` of that name with other lines; left alone).
- **Never moves, renames or deletes a disc.** The `.m3u` is placed with B56's no-overwrite link.
- **An `.m3u` is a new list entry** (a new id and a new content name): the save states and in-game memory cards made
  on a disc entry would not show on the set. The plan counts them; `apply --migrate-states` copies them to the set's
  name (the newest per slot / per card across the set's discs; never over an existing file; the originals kept).
- `undo` removes only what `apply` recorded, and only while its bytes still match.
- The log (`data/import/logs/library_m3u_<UTC>.log`) holds counts, labels (S1...) and codes only.

Design: docs/memory/evidence/b68_2026-11-09/design_written_before_code.md (hashed before this code).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_usb as iu  # noqa: E402  (B56's disc rule, names, m3u bytes, no-overwrite placement, game check)

REPO = Path(__file__).resolve().parents[1]
FLAG_ENV = iu.FLAG_ENV
LIBRARY = "games/ps1"
STATES = "data/games/retroarch/states"
SAVES = "data/games/retroarch/saves"
SLOT_INDEX = "data/games/retroarch/privyhub_state_slots.json"
PLAN = "data/import/m3u_plan.json"
APPLIED = "data/import/m3u_applied.json"
DISC_EXT = (".cue", ".chd")
CARD_EXT = (".srm", ".mcr")
SLOTS = (1, 2, 3)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def _covered(lib: Path) -> set[Path]:
    """Every file an existing `.m3u` names (the list's own rule)."""
    out: set[Path] = set()
    for m in lib.rglob("*.m3u"):
        if m.name.startswith("."):
            continue
        for raw in m.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                out.add((m.parent / line).resolve())
    return out


def _states_of(root: Path, stem: str) -> dict[int, Path]:
    found: dict[int, Path] = {}
    base = root / STATES
    if base.is_dir():
        for n in SLOTS:
            for p in base.rglob(f"{stem}.state{n}"):
                if p.is_file() and (n not in found or p.stat().st_mtime > found[n].stat().st_mtime):
                    found[n] = p
    return found


def _cards_of(root: Path, stem: str) -> list[Path]:
    base = root / SAVES
    return sorted(p for ext in CARD_EXT for p in base.rglob(f"{stem}{ext}") if p.is_file()) if base.is_dir() else []


def make_plan(root: Path = REPO) -> dict[str, Any]:
    root = Path(root)
    lib = root / LIBRARY
    covered = _covered(lib) if lib.is_dir() else set()
    groups: dict[tuple[Path, str], list[Path]] = {}
    if lib.is_dir():
        for p in sorted(lib.rglob("*"), key=lambda q: str(q).casefold()):
            if p.is_file() and not p.name.startswith(".") and p.suffix.casefold() in DISC_EXT \
                    and iu.disc_number(p) is not None:
                groups.setdefault((p.parent, iu.title_key(p)), []).append(p)
    index = _read_json(root / SLOT_INDEX).get("games", {})
    sets, reported = [], []
    for (folder, _key), members in sorted(groups.items(), key=lambda kv: str(kv[0][0]).casefold() + kv[0][1]):
        if len(members) < 2:
            continue
        members.sort(key=lambda e: (iu.disc_number(e) or 0, e.suffix.casefold()))
        label = f"S{len(sets) + len(reported) + 1}"
        numbers = [iu.disc_number(e) for e in members]
        title = " ".join(iu.DISC_RE.sub(" ", iu.clean_name(members[0])).split())
        m3u = folder / f"{title}.m3u"
        lines = [e.name for e in members]
        code = None
        if numbers != list(range(1, len(members) + 1)):
            code = "disc_gap"
        elif any(e.resolve() in covered for e in members) and not m3u.exists():
            code = "covered"
        elif m3u.exists():
            code = "already" if m3u.read_bytes() == iu.m3u_bytes(lines) else "m3u_differs"
        if code:
            reported.append({"label": label, "code": code, "discs": len(members)})
            if code != "already":
                continue                                          # `already`: planned for its migration only
        m3u_rel = _rel(root, m3u)
        new_id = iu.stable_id("ps1", m3u_rel)
        disc_ids = [iu.stable_id("ps1", _rel(root, e)) for e in members]
        # the migration it would do: per slot the newest state across the discs; the newest card per extension
        states: dict[int, Path] = {}
        for e in members:
            for n, p in _states_of(root, e.stem).items():
                if n not in states or p.stat().st_mtime > states[n].stat().st_mtime:
                    states[n] = p
        cards: dict[str, Path] = {}
        for e in members:
            for p in _cards_of(root, e.stem):
                ext = p.suffix.casefold()
                if ext not in cards or p.stat().st_mtime > cards[ext].stat().st_mtime:
                    cards[ext] = p
        copies = []
        for n, p in sorted(states.items()):
            for src in (p, p.with_name(p.name + ".png")):
                if src.is_file():
                    dst = src.with_name(src.name.replace(src.name.split(".state")[0], m3u.stem, 1))
                    copies.append({"kind": "state" if src == p else "thumb", "slot": n, "src": _rel(root, src),
                                   "dst": _rel(root, dst), "skip": dst.exists()})
        for ext, p in sorted(cards.items()):
            dst = p.with_name(m3u.stem + p.suffix)
            copies.append({"kind": "card", "src": _rel(root, p), "dst": _rel(root, dst), "skip": dst.exists()})
        slot_src = {}
        for did in disc_ids:
            for n, s in (index.get(did, {}).get("slots") or {}).items():
                if n not in slot_src or (s.get("modified_unix_ms") or 0) > (slot_src[n][1].get("modified_unix_ms") or 0):
                    slot_src[n] = (did, s)
        sets.append({"label": label, "m3u": m3u_rel, "lines": lines, "discs": len(members), "id": new_id,
                     "m3u_present": code == "already",
                     "disc_ids": disc_ids, "title": title, "copies": copies,
                     "slot_entries": {n: s for n, (_d, s) in slot_src.items()},
                     "stores": {"slot_entries": sum(len(index.get(d, {}).get("slots") or {}) for d in disc_ids)}})
    return {"schema": "privyhub_library_m3u_plan_v1", "created_utc": iu.now_utc(), "sets": sets, "reported": reported}


def _read_json(p: Path) -> dict[str, Any]:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def apply_plan(plan: Mapping[str, Any], root: Path = REPO, *, migrate: bool = False) -> dict[str, Any]:
    root = Path(root)
    fresh = make_plan(root)                                       # re-checked: only what is still planned
    still = {s["m3u"]: s for s in fresh["sets"]}
    done: list[dict[str, Any]] = []
    out = {"written": 0, "already": len([r for r in fresh["reported"] if r["code"] == "already"]),
           "copied": 0, "not_migrated": 0, "sets": len(plan.get("sets", []))}
    for s in plan.get("sets", []):
        cur = still.get(s["m3u"])
        if cur is None or cur["lines"] != s["lines"]:
            continue
        final = root / s["m3u"]
        data = iu.m3u_bytes(s["lines"])
        if not cur.get("m3u_present"):
            created: list[Path] = []
            try:
                iu._place(iu._bytes_writer(data), final, final.parent / f".m3u-{s['label']}.part", _sha(data), created)
            except FileExistsError:
                continue
            done.append({"kind": "m3u", "path": s["m3u"], "sha256": _sha(data)})
            out["written"] += 1
        pending = [c for c in cur["copies"] if not c["skip"]]
        if not migrate:
            out["not_migrated"] += len(pending) + len(cur["slot_entries"])
            continue
        for c in pending:
            src, dst = root / c["src"], root / c["dst"]
            if dst.exists():
                continue
            shutil.copy2(src, dst)
            done.append({"kind": c["kind"], "path": c["dst"], "sha256": iu.sha256(dst)})
            out["copied"] += 1
        if cur["slot_entries"]:
            idx = _read_json(root / SLOT_INDEX)
            games = idx.setdefault("games", {})
            if cur["id"] not in games:
                slots = {}
                for n, e in cur["slot_entries"].items():
                    e = dict(e)
                    old = str(e.get("state_file", ""))
                    if old:
                        name = Path(old).name
                        e["state_file"] = str(Path(old).with_name(name.replace(name.split(".state")[0], Path(s["m3u"]).stem, 1)).as_posix())
                    slots[n] = e
                games[cur["id"]] = {"game_key": cur["id"], "game_relative_path": s["m3u"], "game_system": "ps1",
                                    "game_title": cur["title"], "slots": slots}
                iu.write_json_atomic(root / SLOT_INDEX, idx)
                done.append({"kind": "slot_index", "id": cur["id"]})
                out["copied"] += len(slots)
    rec = _read_json(root / APPLIED)
    rec.setdefault("applied", []).extend(done)
    if done:
        iu.write_json_atomic(root / APPLIED, rec)
    return out


def undo(root: Path = REPO) -> dict[str, Any]:
    root = Path(root)
    rec = _read_json(root / APPLIED)
    kept, out = [], {"removed": 0, "left_changed": 0}
    for d in rec.get("applied", []):
        if d["kind"] == "slot_index":
            idx = _read_json(root / SLOT_INDEX)
            if idx.get("games", {}).pop(d["id"], None) is not None:
                iu.write_json_atomic(root / SLOT_INDEX, idx)
                out["removed"] += 1
            continue
        p = root / d["path"]
        if p.is_file() and iu.sha256(p) == d["sha256"]:
            p.unlink()
            out["removed"] += 1
        elif p.exists():
            out["left_changed"] += 1
            kept.append(d)
    rec["applied"] = kept
    iu.write_json_atomic(root / APPLIED, rec)
    return out


def log(root: Path, command: str, rows: Mapping[str, Any]) -> Path:
    d = Path(root) / "data/import/logs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"library_m3u_{iu.now_utc().replace(':', '').replace('-', '')}.log"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"command": command, **rows}, sort_keys=True) + "\n")
    return p


def _summary(plan: Mapping[str, Any]) -> dict[str, Any]:
    return {"sets": [{"label": s["label"], "discs": s["discs"], "m3u_present": s.get("m3u_present", False),
                      "would_copy": {k: sum(1 for c in s["copies"] if c["kind"] == k and not c["skip"])
                                     for k in ("state", "thumb", "card")},
                      "slot_entries": len(s["slot_entries"])} for s in plan["sets"]],
            "reported": [{"label": r["label"], "code": r["code"], "discs": r["discs"]} for r in plan["reported"]]}


def main(argv: list[str] | None = None, *, root: Path = REPO, environ: Mapping[str, str] | None = None,
         game_active=None) -> int:
    env = os.environ if environ is None else environ
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("plan", "apply", "undo"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--migrate-states", action="store_true")
    a = ap.parse_args(argv)
    if (env.get(FLAG_ENV) or "").strip() != "1":
        print(f"library_m3u: {FLAG_ENV}=1 is required; nothing done")
        return 9
    root = Path(root)
    active = iu.game_active if game_active is None else game_active
    if a.command == "plan":
        plan = make_plan(root)
        if a.json:
            iu.write_json_atomic(root / PLAN, plan)
        s = _summary(plan)
        for x in s["sets"]:
            moves = x["would_copy"]["state"] + x["would_copy"]["card"] + x["slot_entries"]
            if x["m3u_present"] and not moves:
                continue                                          # reported below as `already`
            print(f"{x['label']}: " + ("its .m3u is in place" if x["m3u_present"] else f"one entry for {x['discs']} discs") +
                  (f"; {moves} saved file(s) / slot(s) on its discs would no longer show unless migrated" if moves else ""))
        for r in s["reported"]:
            print(f"{r['label']}: {r['code']} ({r['discs']} discs)")
        print(f"{sum(1 for x in s['sets'] if not x['m3u_present'])} set(s) planned, {len(s['reported'])} reported")
        log(root, "plan", s)
        return 0
    if active():
        print("library_m3u: a game is running; nothing done")
        return 6
    if a.command == "apply":
        plan = _read_json(root / PLAN) or make_plan(root)
        out = apply_plan(plan, root, migrate=a.migrate_states)
        print(f"written {out['written']}, already {out['already']}, copied {out['copied']}")
        if out["not_migrated"]:
            print(f"{out['not_migrated']} card / state file(s) or slot(s) would no longer show; "
                  "run again with --migrate-states")
        log(root, "apply", {**out, "migrate_states": a.migrate_states})
        return 0
    out = undo(root)
    print(f"removed {out['removed']}, left (changed since) {out['left_changed']}")
    log(root, "undo", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
