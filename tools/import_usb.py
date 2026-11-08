#!/usr/bin/env python3
"""B56: H0 import slice 1a -- PS1 titles (and a real PS1 BIOS) from a USB stick into the hub's existing library.

**Behind `PRIVYHUB_IMPORT=1`: without it every command refuses (exit 9) and nothing is read or written.**
Design: `docs/memory/evidence/b56_2026-11-08/design_written_before_code.md` (hashed before this code), on B45's
contract `docs/memory/architecture/H0_IMPORT_CONTRACT_DESIGN_2026-11-06.md`. The user's steps: `docs/IMPORT.md`.

    python3 tools/import_usb.py inspect <mount>        # what is on the stick (no hashing; writes nothing)
    python3 tools/import_usb.py plan <mount>           # hash, validate, duplicates, space -> data/import/plans/<UTC>.json
    python3 tools/import_usb.py apply [<plan>]         # copy what the plan accepted, atomically; the marks; the log
    python3 tools/import_usb.py verify [<plan>]        # re-hash what apply placed (read-only)

The stick is only read. The library is `<repo>/games/ps1/` (no other target can be given); the BIOS folder is the
PS1 core's, `data/games/retroarch/system/`. The terminal shows labels (`T1`, `T2`, ...) unless `--names`; the plan
(local, under the git-ignored `data/`) holds names; the log under `data/import/logs/` holds counts and labels only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

FLAG_ENV = "PRIVYHUB_IMPORT"
REPO = Path(__file__).resolve().parents[1]
IMPORT_DIR = "PrivyHub-Import"
SYSTEM = "ps1"
LIB_REL = Path("games") / "ps1"
BIOS_REL = Path("data") / "games" / "retroarch" / "system"
DATA_REL = Path("data") / "import"
MARKS_NAME = "marks.json"
BIOS_FILES = {"scph5500.bin": "JP", "scph5501.bin": "US", "scph5502.bin": "EU"}
BIOS_SIZE = 524_288
SECTOR = 2352
SPACE_MARGIN = 1.10
BLOCK = 1 << 20
NAME_MAX = 200
STATUS_URL = "http://127.0.0.1:8765/plugins/games/status"
LIST_EXT = {".chd", ".cue", ".m3u", ".iso"}         # what the plugin lists for PS1 (an .m3u hides what it names)
DISC_RE = re.compile(r"\s*[\(\[]\s*dis[ck]\s*(\d+)(?:\s*of\s*\d+)?\s*[\)\]]", re.IGNORECASE)
FILE_RE = re.compile(r'^\s*FILE\s+(?:"([^"]+)"|(\S+))\s+\S+', re.IGNORECASE)
TRACK_RE = re.compile(r"^\s*TRACK\s+(\d+)\s+(\S+)", re.IGNORECASE)

EXIT_OK, EXIT_USAGE, EXIT_NOTHING, EXIT_PARTIAL, EXIT_VERIFY, EXIT_SOURCE, EXIT_SPACE, EXIT_ACTIVE, EXIT_FLAG = (
    0, 2, 3, 4, 5, 6, 7, 8, 9)

OPENBIOS_WARNING = ("A real BIOS changes the firmware every PS1 game starts with: a save state made before (under "
                    "OpenBIOS) may not load after. Memory-card saves are not affected.")

# test hook: called after each file's copy as (cid, n); a raise there is a failure midway
_FAIL_HOOK: Callable[[str, int], None] | None = None


class Usage(Exception):
    pass


# --- the plugin's own rules (games.py _clean_name / _stable_id), restated; a test holds them equal ---------------------

def clean_name(path: Path) -> str:
    name = path.stem.replace("_", " ").strip()
    if not name:
        return path.name
    cleaned = " ".join(name.split())
    letters = [c for c in cleaned if c.isalpha()]
    if letters and (all(c.islower() for c in letters) or all(c.isupper() for c in letters)):
        cleaned = cleaned.title()
    return cleaned


def stable_id(system: str, relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").casefold()
    return f"game_{system}_{hashlib.sha1(f'{system}:{normalized}'.encode('utf-8')).hexdigest()[:16]}"


def title_key(path: Path) -> str:
    return " ".join(DISC_RE.sub(" ", clean_name(path)).split()).casefold()


def disc_number(path: Path) -> int | None:
    m = DISC_RE.search(path.stem)
    return int(m.group(1)) if m else None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(BLOCK)
            if not b:
                return h.hexdigest()
            h.update(b)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# --- the stick ----------------------------------------------------------------------------------------------------------

def find_root(mount: str | Path) -> Path:
    m = Path(mount)
    if m.name == IMPORT_DIR and m.is_dir():
        return m
    if (m / IMPORT_DIR).is_dir():
        return m / IMPORT_DIR
    raise Usage(f"no {IMPORT_DIR}/ folder at that mount")


def bad_name(name: str) -> bool:
    return len(name.encode("utf-8", "replace")) > NAME_MAX or any(ord(c) < 32 or ord(c) == 127 for c in name)


def parse_cue(cue: Path) -> tuple[list[tuple[str, Path | None]], str | None, str | None]:
    """([(the FILE name, its path or None)], the first track's mode, an error code)."""
    try:
        text = cue.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], None, "unreadable"
    files: list[tuple[str, Path | None]] = []
    first_mode = None
    for line in text.splitlines():
        m = FILE_RE.match(line)
        if m:
            name = m.group(1) or m.group(2)
            files.append((name, None))
            continue
        t = TRACK_RE.match(line)
        if t and first_mode is None:
            first_mode = t.group(2).upper()
    out: list[tuple[str, Path | None]] = []
    for name, _ in files:
        n = name.replace("\\", "/")
        if n.startswith("/") or ".." in Path(n).parts or re.match(r"^[A-Za-z]:", n):
            return out, first_mode, "cue_outside"
        p = cue.parent / n
        if p.is_file() and not p.is_symlink():
            out.append((name, p))
            continue
        siblings = {s.name.casefold(): s for s in p.parent.iterdir()} if p.parent.is_dir() else {}
        if p.name.casefold() in siblings:
            return out, first_mode, "cue_case_mismatch"
        return out, first_mode, "cue_missing_file"
    if not out:
        return out, first_mode, "cue_missing_file"
    return out, first_mode, None


def scan_stick(root: Path) -> dict[str, Any]:
    """inspect: candidates and rejections from PrivyHub-Import/games/ps1/, the BIOS report, the other folders."""
    games = root / "games" / SYSTEM
    out: dict[str, Any] = {"candidates": [], "rejected": [], "ignored_hidden": 0, "other_systems": [],
                           "bios": scan_bios(root / "bios" / SYSTEM)}
    gdir = root / "games"
    if gdir.is_dir():
        out["other_systems"] = sorted(p.name for p in gdir.iterdir() if p.is_dir() and p.name != SYSTEM)
    if not games.is_dir():
        return out
    files: list[Path] = []
    for p in sorted(games.rglob("*"), key=lambda q: str(q).casefold()):
        if p.name.startswith("."):
            if p.is_file():
                out["ignored_hidden"] += 1
            continue
        if any(part.startswith(".") for part in p.relative_to(games).parts[:-1]):
            continue
        if p.is_symlink():
            out["rejected"].append({"source": p, "reason": "symlink"})
            continue
        if p.is_file():
            if bad_name(p.name):
                out["rejected"].append({"source": p, "reason": "bad_name"})
                continue
            files.append(p)
    by_ext: dict[str, list[Path]] = {}
    for p in files:
        by_ext.setdefault(p.suffix.casefold(), []).append(p)

    claimed: dict[Path, list[Path]] = {}
    cues: dict[Path, dict[str, Any]] = {}
    for cue in by_ext.get(".cue", []):
        refs, mode, err = parse_cue(cue)
        cues[cue] = {"refs": [p for _, p in refs if p is not None], "mode": mode, "error": err}
        for p in cues[cue]["refs"]:
            claimed.setdefault(p.resolve(), []).append(cue)
    twice = {c for owners in claimed.values() if len(owners) > 1 for c in owners}

    def entry_unit(e: Path) -> dict[str, Any]:
        if e.suffix.casefold() == ".cue":
            c = cues.get(e) or {"refs": [], "mode": None, "error": "cue_missing_file"}
            return {"entry": e, "kind": "cue", "files": [e] + list(c["refs"]), "mode": c["mode"],
                    "error": "bin_claimed_twice" if e in twice else c["error"]}
        return {"entry": e, "kind": "chd", "files": [e], "mode": None, "error": None}

    used: set[Path] = set()
    # a stick .m3u: its discs are one candidate
    for m3u in by_ext.get(".m3u", []):
        discs, err = [], None
        for raw in m3u.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            p = m3u.parent / line
            if ".." in Path(line).parts or line.startswith("/") or not p.is_file() or \
                    p.suffix.casefold() not in (".chd", ".cue"):
                err = err or "m3u_bad_entry"
                continue
            discs.append(entry_unit(p))
        used.update(d["entry"] for d in discs)
        used.add(m3u)
        out["candidates"].append({"kind": "m3u_set", "entry": m3u, "discs": discs, "make_m3u": False,
                                  "title": clean_name(m3u), "error": err or next((d["error"] for d in discs
                                                                                  if d["error"]), None)})
    # discs grouped by "(Disc N)" (same folder, same title) -> one candidate with an .m3u made on the hub
    entries = [e for e in by_ext.get(".chd", []) + by_ext.get(".cue", []) if e not in used]
    groups: dict[tuple[Path, str], list[Path]] = {}
    for e in entries:
        if disc_number(e) is not None:
            groups.setdefault((e.parent, title_key(e)), []).append(e)
    for (folder, _key), members in sorted(groups.items(), key=lambda kv: str(kv[0][0]).casefold() + kv[0][1]):
        if len(members) < 2:
            continue
        members.sort(key=lambda e: (disc_number(e) or 0, e.suffix.casefold()))
        numbers = [disc_number(e) for e in members]
        title = " ".join(DISC_RE.sub(" ", clean_name(members[0])).split())
        discs = [entry_unit(e) for e in members]
        err = None if numbers == list(range(1, len(members) + 1)) else "multidisc_gap"
        used.update(members)
        out["candidates"].append({"kind": "m3u_set", "entry": folder / f"{title}.m3u", "discs": discs,
                                  "make_m3u": True, "title": title,
                                  "error": err or next((d["error"] for d in discs if d["error"]), None)})
    for e in entries:
        if e in used:
            continue
        u = entry_unit(e)
        out["candidates"].append({"kind": "chd" if u["kind"] == "chd" else "cue_set", "entry": e, "discs": [u],
                                  "make_m3u": False, "title": clean_name(e), "error": u["error"]})
    for iso in by_ext.get(".iso", []):
        out["candidates"].append({"kind": "iso", "entry": iso, "discs": [{"entry": iso, "kind": "iso",
                                                                          "files": [iso], "mode": None,
                                                                          "error": None}],
                                  "make_m3u": False, "title": clean_name(iso), "error": None})
    for p in by_ext.get(".pbp", []):
        out["rejected"].append({"source": p, "reason": "pbp_not_supported"})
    for p in by_ext.get(".bin", []):
        if p.resolve() not in claimed:
            out["rejected"].append({"source": p, "reason": "bin_without_cue"})
    for ext, ps in by_ext.items():
        if ext not in (".chd", ".cue", ".m3u", ".iso", ".pbp", ".bin"):
            out["rejected"].extend({"source": p, "reason": "unknown_type"} for p in ps)
    out["candidates"].sort(key=lambda c: str(c["entry"]).casefold())
    for i, c in enumerate(out["candidates"], 1):
        c["label"] = f"T{i}"
    return out


def scan_bios(folder: Path) -> list[dict[str, Any]]:
    found = []
    if not folder.is_dir():
        return found
    for p in sorted(folder.iterdir(), key=lambda q: q.name.casefold()):
        if not p.is_file() or p.is_symlink() or p.name.startswith("."):
            continue
        name = p.name.casefold()
        region = BIOS_FILES.get(name)
        size = p.stat().st_size
        found.append({"source": p, "name": name, "region": region, "bytes": size,
                      "real": region is not None and size == BIOS_SIZE})
    return found


def core_bios(project_root: Path) -> list[str]:
    """The core folder's real BIOS files (by name and size), as region labels."""
    d = project_root / BIOS_REL
    out = []
    for name, region in BIOS_FILES.items():
        p = d / name
        try:
            if p.is_file() and p.stat().st_size == BIOS_SIZE:
                out.append(region)
        except OSError:
            pass
    return out


# --- validation (plan) ----------------------------------------------------------------------------------------------

def check_chd(p: Path) -> str | None:
    with open(p, "rb") as fh:
        head = fh.read(16)
    if len(head) < 16 or head[:8] != b"MComprHD":
        return "bad_header"
    version = int.from_bytes(head[12:16], "big")
    return None if version in (4, 5) else "bad_header"


def check_cue_unit(unit: Mapping[str, Any]) -> str | None:
    refs = unit["files"][1:]
    for p in refs:
        if p.stat().st_size % SECTOR:
            return "bad_header"
    mode = (unit.get("mode") or "").upper()
    off = {"MODE2/2352": 24, "MODE1/2352": 16}.get(mode)
    if off is None:
        return "not_ps1_disc"
    with open(refs[0], "rb") as fh:
        fh.seek(16 * SECTOR + off)
        pvd = fh.read(40)
    if pvd[:6] != b"\x01CD001" or not pvd[8:40].decode("ascii", "replace").strip().startswith("PLAYSTATION"):
        return "not_ps1_disc"
    return None


def check_unit(unit: Mapping[str, Any]) -> str | None:
    if unit.get("error"):
        return unit["error"]
    if unit["kind"] == "chd":
        return check_chd(unit["entry"])
    if unit["kind"] == "cue":
        return check_cue_unit(unit)
    return None


# --- the library ----------------------------------------------------------------------------------------------------

def library(project_root: Path) -> dict[str, Any]:
    """The PS1 entries as the plugin lists them (an .m3u hides what it names), every file's size, the titles."""
    lib = project_root / LIB_REL
    out: dict[str, Any] = {"entries": [], "sizes": {}, "titles": {}}
    if not lib.is_dir():
        return out
    files = [p for p in lib.rglob("*") if p.is_file() and not p.name.startswith(".")]
    for p in files:
        try:
            out["sizes"].setdefault(p.stat().st_size, []).append(p)
        except OSError:
            pass
    listed = [p for p in files if p.suffix.casefold() in LIST_EXT]
    hidden: set[Path] = set()
    for m in (p for p in listed if p.suffix.casefold() == ".m3u"):
        for raw in m.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                hidden.add((m.parent / line).resolve())
    for p in sorted(listed, key=lambda q: str(q).casefold()):
        if p.resolve() in hidden and p.suffix.casefold() != ".m3u":
            continue
        rel = (LIB_REL / p.relative_to(lib)).as_posix()
        e = {"path": p, "rel": rel, "id": stable_id(SYSTEM, rel), "format": p.suffix.casefold().lstrip("."),
             "title_key": title_key(p)}
        out["entries"].append(e)
        out["titles"].setdefault(e["title_key"], []).append(e)
    return out


class HashCache:
    def __init__(self) -> None:
        self.d: dict[Path, str] = {}

    def __call__(self, p: Path) -> str:
        r = p.resolve()
        if r not in self.d:
            self.d[r] = sha256(p)
        return self.d[r]


def library_entry_for(lib: Mapping[str, Any], f: Path) -> str | None:
    """The listed entry a library file belongs to (itself, or the cue in its folder that names it)."""
    for e in lib["entries"]:
        if e["path"].resolve() == f.resolve():
            return e["id"]
    for e in lib["entries"]:
        if e["format"] == "cue" and e["path"].parent == f.parent:
            refs, _, _ = parse_cue(e["path"])
            if any(p is not None and p.resolve() == f.resolve() for _, p in refs):
                return e["id"]
    return None


# --- plan -----------------------------------------------------------------------------------------------------------

def make_plan(mount: str | Path, project_root: Path, *, free_bytes: Callable[[Path], int] | None = None) -> dict[str, Any]:
    root = find_root(mount)
    st = scan_stick(root)
    lib = library(project_root)
    hashes = HashCache()
    lib_dir = project_root / LIB_REL
    games_root = root / "games" / SYSTEM
    cands: list[dict[str, Any]] = []
    seen_content: dict[tuple, str] = {}
    stick_chd_titles = {title_key(c["entry"]) for c in st["candidates"] if c["kind"] == "chd" and not c["error"]}
    stick_chd_titles |= {c["title"].casefold() for c in st["candidates"]
                         if c["kind"] == "m3u_set" and all(d["kind"] == "chd" for d in c["discs"])}
    lib_chd_titles = {k for k, es in lib["titles"].items() if any(e["format"] == "chd" for e in es)}

    for c in st["candidates"]:
        entry: Path = c["entry"]
        rel_entry = (LIB_REL / entry.relative_to(games_root)).as_posix()
        key = title_key(entry) if c["kind"] != "m3u_set" else c["title"].casefold()
        item: dict[str, Any] = {"label": c["label"], "kind": c["kind"], "title": c["title"],
                                "cid": "c_" + hashlib.sha256(rel_entry.encode()).hexdigest()[:12],
                                "entry_target": rel_entry, "game_id": stable_id(SYSTEM, rel_entry),
                                "files": [], "make_m3u": None, "decision": "accept", "reason": None,
                                "duplicate_of": None}
        cands.append(item)
        if c["kind"] == "iso":
            item["files"] = [{"source": str(entry), "target_rel": rel_entry, "bytes": entry.stat().st_size,
                              "sha256": None, "role": "entry"}]
            if key in lib_chd_titles or key in stick_chd_titles:
                item.update(decision="duplicate", reason="duplicate: chd present")
            else:
                item.update(decision="reject", reason="iso_not_launchable")
            continue
        err = c["error"] or next((check_unit(d) for d in c["discs"] if check_unit(d)), None)
        files: list[dict[str, Any]] = []
        for d in c["discs"]:
            for f in d["files"]:
                role = "entry" if f == d["entry"] else "track"
                if c["kind"] == "m3u_set" and role == "entry":
                    role = "disc"
                files.append({"source": str(f), "target_rel": (LIB_REL / f.relative_to(games_root)).as_posix(),
                              "bytes": f.stat().st_size if f.exists() else 0, "sha256": None, "role": role})
        if c["kind"] == "m3u_set":
            lines = [Path(d["entry"]).relative_to(entry.parent).as_posix() for d in c["discs"]]
            if c["make_m3u"]:
                item["make_m3u"] = {"target_rel": rel_entry, "lines": lines}
            else:
                files.append({"source": str(entry), "target_rel": rel_entry, "bytes": entry.stat().st_size,
                              "sha256": None, "role": "playlist"})
        # the entry last: tracks / discs first, then the playlist
        files.sort(key=lambda f: {"track": 0, "disc": 1, "entry": 2, "playlist": 3}[f["role"]])
        item["files"] = files
        if err:
            item.update(decision="reject", reason=err)
            continue
        for f in files:
            f["sha256"] = hashes(Path(f["source"]))
        # the content: the data files (a .chd, a cue's tracks), never a cue sheet's or a playlist's text
        data = [f for f in files if f["role"] != "playlist" and Path(f["source"]).suffix.casefold() != ".cue"]
        content = tuple(sorted((f["bytes"], f["sha256"]) for f in data))
        # against the library by hash, size-gated
        matched_ids = []
        for f in data:
            hit = None
            for lp in lib["sizes"].get(f["bytes"], []):
                if hashes(lp) == f["sha256"]:
                    hit = lp
                    break
            if hit is None:
                matched_ids = None
                break
            matched_ids.append(library_entry_for(lib, hit))
        if matched_ids:
            item.update(decision="duplicate", reason="duplicate: already in the library",
                        duplicate_of=next((i for i in matched_ids if i), None))
            continue
        # inside the stick: the same content twice, the first by path kept
        if content in seen_content:
            item.update(decision="duplicate", reason="duplicate: same content on the stick",
                        duplicate_of=seen_content[content])
            continue
        seen_content[content] = item["label"]
        # by title: two entries for one title would split saves and play counts (a library .iso alone gives way to a
        # .chd: it is hidden instead)
        same = lib["titles"].get(key, [])
        chd_like = c["kind"] == "chd" or (c["kind"] == "m3u_set" and all(
            Path(f["source"]).suffix.casefold() == ".chd" for f in files if f["role"] == "disc"))
        if same and not (chd_like and all(e["format"] == "iso" for e in same)):
            item.update(decision="duplicate", reason="duplicate: title present", duplicate_of=same[0]["id"])
            continue
        # the target exists with other bytes: never renamed, never overwritten
        clash = any((project_root / f["target_rel"]).exists() for f in files)
        if item["make_m3u"] and (project_root / item["make_m3u"]["target_rel"]).exists():
            clash = True
        if clash:
            item.update(decision="reject", reason="target_exists_different")
            continue

    # hide: a library .iso whose title has a .chd (in the library, or accepted here)
    accepted_chd = {title_key(Path(i["entry_target"])) if i["kind"] == "chd" else i["title"].casefold()
                    for i in cands if i["decision"] == "accept" and (i["kind"] == "chd" or (
                        i["kind"] == "m3u_set" and all(Path(f["source"]).suffix.casefold() == ".chd"
                                                       for f in i["files"] if f["role"] == "disc")))}
    hide = {e["id"]: "chd present" for e in lib["entries"]
            if e["format"] == "iso" and (e["title_key"] in lib_chd_titles or e["title_key"] in accepted_chd)}

    # BIOS: real files on the stick not already in the core's folder
    core_has = core_bios(project_root)
    bios = []
    for b in st["bios"]:
        entry = {"name": b["name"], "region": b["region"], "bytes": b["bytes"], "source": str(b["source"])}
        if not b["real"]:
            entry.update(decision="reject", reason="bios_unknown")
        elif b["region"] in core_has or (project_root / BIOS_REL / b["name"]).exists():
            entry.update(decision="duplicate", reason="already in the core's BIOS folder")
        else:
            entry.update(decision="accept", reason=None, sha256=sha256(b["source"]))
        bios.append(entry)

    need = sum(f["bytes"] for i in cands if i["decision"] == "accept" for f in i["files"])
    need += sum(b["bytes"] for b in bios if b["decision"] == "accept")
    target_fs = lib_dir if lib_dir.exists() else project_root
    free = (free_bytes or _free_bytes)(target_fs)
    plan = {
        "schema": "privyhub.import.plan/1",
        "created_utc": now_utc(),
        "source_root": str(root),
        "library_root": LIB_REL.as_posix(),
        "candidates": cands,
        "rejected": [{"source": str(r["source"]), "reason": r["reason"]} for r in st["rejected"]],
        "ignored_hidden": st["ignored_hidden"],
        "other_systems": st["other_systems"],
        "hide": hide,
        "bios": {"stick": bios, "core_has_real": core_has,
                 "openbios_fallback": not core_has and not any(b["decision"] == "accept" for b in bios)},
        "space": {"needed_bytes": need, "free_bytes": free, "ok": free >= need * SPACE_MARGIN},
        "totals": {d: sum(1 for i in cands if i["decision"] == d) for d in ("accept", "duplicate", "reject")},
    }
    plan["totals"]["rejected_files"] = len(plan["rejected"])
    return plan


def _free_bytes(p: Path) -> int:
    s = os.statvfs(p)
    return s.f_bavail * s.f_frsize


# --- apply / verify -------------------------------------------------------------------------------------------------

def _fsync_dir(d: Path) -> None:
    try:
        fd = os.open(d, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def _place(write: Callable[[Any], str], final: Path, part: Path, want: str | None, created: list[Path]) -> None:
    """Write to the part (hashing), fsync, verify, link into place (never over a file), remove the part."""
    fh = open(part, "xb")                   # FileExistsError on a stale part: not ours, never removed
    created.append(part)
    with fh:
        got = write(fh)
        fh.flush()
        os.fsync(fh.fileno())
    _fsync_dir(part.parent)
    if want is not None and got != want:
        raise RuntimeError("verify")
    os.link(part, final)                    # FileExistsError if the final exists: no overwrite
    created.append(final)
    os.unlink(part)
    created.remove(part)


def _copier(src: Path) -> Callable[[Any], str]:
    def write(fh: Any) -> str:
        h = hashlib.sha256()
        with open(src, "rb") as s:
            while True:
                b = s.read(BLOCK)
                if not b:
                    return h.hexdigest()
                h.update(b)
                fh.write(b)
    return write


def _bytes_writer(data: bytes) -> Callable[[Any], str]:
    def write(fh: Any) -> str:
        fh.write(data)
        return hashlib.sha256(data).hexdigest()
    return write


def _mkdirs(d: Path, made: list[Path]) -> None:
    missing = []
    p = d
    while not p.exists():
        missing.append(p)
        p = p.parent
    for m in reversed(missing):
        m.mkdir()
        made.append(m)


def _rollback(created: list[Path], made: list[Path]) -> None:
    for p in reversed(created):
        try:
            p.unlink()
        except FileNotFoundError:
            pass
    for d in sorted(made, key=lambda q: len(q.parts), reverse=True):
        try:
            d.rmdir()
        except OSError:
            pass


def m3u_bytes(lines: Iterable[str]) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


def game_active(url: str = STATUS_URL) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.0) as r:
            return bool(json.loads(r.read().decode("utf-8", "replace")).get("active", False))
    except Exception:
        return False


def apply_plan(plan: dict[str, Any], project_root: Path, *, while_playing: bool = False,
               active: Callable[[], bool] = game_active, now_ms: int | None = None,
               free_bytes: Callable[[Path], int] | None = None) -> tuple[int, dict[str, Any]]:
    if not while_playing and active():
        return EXIT_ACTIVE, {"error": "a game is active"}
    try:
        os.nice(10)
    except OSError:
        pass
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    results: list[dict[str, Any]] = []
    todo = [c for c in plan["candidates"] if c["decision"] == "accept"]
    for c in todo:
        for f in c["files"]:
            try:
                src = Path(f["source"])
                if src.stat().st_size != f["bytes"] or sha256(src) != f["sha256"]:
                    c["_skip"] = "source_changed"
                    break
            except OSError:
                c["_skip"] = "source_unreadable"
                break
    need = sum(f["bytes"] for c in todo if "_skip" not in c for f in c["files"])
    need += sum(b["bytes"] for b in plan["bios"]["stick"] if b["decision"] == "accept")
    lib_dir = project_root / LIB_REL
    free = (free_bytes or _free_bytes)(lib_dir if lib_dir.exists() else project_root)
    if free < need * SPACE_MARGIN:
        return EXIT_SPACE, {"error": "not enough space", "needed_bytes": need, "free_bytes": free}
    placed: list[dict[str, Any]] = []
    source_error = False
    for c in todo:
        if "_skip" in c:
            results.append({"label": c["label"], "kind": c["kind"], "result": c["_skip"]})
            source_error = source_error or c["_skip"] == "source_unreadable"
            continue
        created: list[Path] = []
        made: list[Path] = []
        try:
            for n, f in enumerate(c["files"]):
                final = project_root / f["target_rel"]
                _mkdirs(final.parent, made)
                part = final.parent / f".import-{c['cid']}-{n}.part"
                _place(_copier(Path(f["source"])), final, part, f["sha256"], created)
                if _FAIL_HOOK is not None:
                    _FAIL_HOOK(c["cid"], n)
            if c.get("make_m3u"):
                m = c["make_m3u"]
                final = project_root / m["target_rel"]
                data = m3u_bytes(m["lines"])
                _place(_bytes_writer(data), final, final.parent / f".import-{c['cid']}-m3u.part",
                       hashlib.sha256(data).hexdigest(), created)
            placed.append({"label": c["label"], "game_id": c["game_id"],
                           "files": [{"target_rel": f["target_rel"], "sha256": f["sha256"]} for f in c["files"]] +
                           ([{"target_rel": c["make_m3u"]["target_rel"],
                              "sha256": hashlib.sha256(m3u_bytes(c["make_m3u"]["lines"])).hexdigest()}]
                            if c.get("make_m3u") else [])})
            results.append({"label": c["label"], "kind": c["kind"], "result": "placed",
                            "files": len(c["files"]) + (1 if c.get("make_m3u") else 0),
                            "bytes": sum(f["bytes"] for f in c["files"])})
        except Exception as exc:
            _rollback(created, made)
            reason = ("verify_failed" if str(exc) == "verify" else
                      "target_exists" if isinstance(exc, FileExistsError) else
                      "source_unreadable" if isinstance(exc, OSError) else "failed")
            source_error = source_error or reason == "source_unreadable"
            results.append({"label": c["label"], "kind": c["kind"], "result": reason})
    # the BIOS: each real file not in the core's folder, the same atomic way
    bios_done = []
    for b in plan["bios"]["stick"]:
        if b["decision"] != "accept":
            continue
        created, made = [], []
        final = project_root / BIOS_REL / b["name"]
        try:
            _mkdirs(final.parent, made)
            _place(_copier(Path(b["source"])), final, final.parent / f".import-bios-{b['region']}.part",
                   b.get("sha256"), created)
            bios_done.append(b["region"])
        except Exception:
            _rollback(created, made)
    # the marks the list reads: NEW for 7 days, the hidden .iso
    marks_path = project_root / DATA_REL / MARKS_NAME
    marks = read_marks(marks_path)
    for p in placed:
        marks["new"][p["game_id"]] = now_ms
    for gid, why in plan.get("hide", {}).items():
        marks["hide"][gid] = why
    if placed or plan.get("hide"):
        write_json_atomic(marks_path, marks)
    summary = {
        "results": results, "placed": placed, "bios_copied": bios_done,
        "hidden": len(plan.get("hide", {})),
        "totals": {"placed": len(placed), "failed": sum(1 for r in results if r["result"] != "placed"),
                   "duplicate": plan["totals"]["duplicate"], "reject": plan["totals"]["reject"]},
    }
    if any(r["result"] == "verify_failed" for r in results):
        code = EXIT_VERIFY
    elif source_error:
        code = EXIT_SOURCE
    elif any(r["result"] != "placed" for r in results):
        code = EXIT_PARTIAL
    elif not todo and not bios_done and plan["totals"]["duplicate"] == 0 and not plan.get("hide"):
        code = EXIT_NOTHING
    else:
        code = EXIT_OK
    return code, summary


def verify_applied(applied: Mapping[str, Any], project_root: Path) -> tuple[int, list[dict[str, Any]]]:
    out = []
    for p in applied.get("placed", []):
        bad = 0
        for f in p["files"]:
            t = project_root / f["target_rel"]
            if not t.is_file() or sha256(t) != f["sha256"]:
                bad += 1
        out.append({"label": p["label"], "files": len(p["files"]), "result": "ok" if not bad else "mismatch"})
    return (EXIT_OK if all(r["result"] == "ok" for r in out) else EXIT_VERIFY), out


# --- marks, log, files ----------------------------------------------------------------------------------------------

def read_marks(path: Path) -> dict[str, Any]:
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(m, dict):
            return {"schema": "privyhub.import.marks/1", "new": dict(m.get("new") or {}),
                    "hide": dict(m.get("hide") or {})}
    except (OSError, ValueError):
        pass
    return {"schema": "privyhub.import.marks/1", "new": {}, "hide": {}}


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def sanitized_rows(command: str, plan: Mapping[str, Any], summary: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Counts and labels only: no filename, title, folder, hash, mount path or volume name."""
    rows = [{"event": command, "utc": now_utc(), "totals": dict(plan.get("totals", {})),
             "hidden_iso": len(plan.get("hide", {})), "ignored_hidden": plan.get("ignored_hidden", 0),
             "other_systems": len(plan.get("other_systems", []))}]
    for c in plan.get("candidates", []):
        rows.append({"label": c["label"], "kind": c["kind"], "files": len(c["files"]) + (1 if c.get("make_m3u") else 0),
                     "bytes": sum(f["bytes"] for f in c["files"]), "decision": c["decision"],
                     "reason": _reason_code(c.get("reason"))})
    reasons: dict[str, int] = {}
    for r in plan.get("rejected", []):
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    if reasons:
        rows.append({"rejected_files_by_reason": reasons})
    b = plan.get("bios", {})
    rows.append({"bios_stick": sorted((x.get("region") or "unknown") + ":" + x["decision"] for x in b.get("stick", [])),
                 "bios_core_has": list(b.get("core_has_real", []))})
    if summary is not None:
        for r in summary.get("results", []):
            rows.append({"label": r["label"], "result": r["result"], "files": r.get("files"), "bytes": r.get("bytes")})
        rows.append({"bios_copied": list(summary.get("bios_copied", [])), "summary": dict(summary.get("totals", {}))})
    return rows


def _reason_code(reason: str | None) -> str | None:
    """A reason as a code ("duplicate: chd present" -> "duplicate_chd_present"); never a name."""
    return None if reason is None else reason.replace(": ", "_").replace(" ", "_")


def write_log(project_root: Path, rows: list[dict[str, Any]]) -> Path:
    d = project_root / DATA_REL / "logs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{now_utc()}.jsonl"
    with open(p, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return p


def latest(project_root: Path, sub: str) -> Path | None:
    d = project_root / DATA_REL / sub
    files = sorted(d.glob("*.json")) if d.is_dir() else []
    return files[-1] if files else None


# --- the terminal ---------------------------------------------------------------------------------------------------

def mb(n: int) -> str:
    return f"{n / 1_000_000:.0f} MB"


def print_inspect(st: Mapping[str, Any], names: bool, project_root: Path) -> None:
    print(f"PS1 candidates: {len(st['candidates'])}")
    for c in st["candidates"]:
        n = sum(len(d["files"]) for d in c["discs"])
        extra = f"  {c['title']}" if names else ""
        print(f"  {c['label']}  {c['kind']:8s} {n} file(s){' + an .m3u made on the hub' if c['make_m3u'] else ''}"
              f"{'  REJECT ' + c['error'] if c['error'] else ''}{extra}")
    if st["rejected"]:
        print(f"Rejected files: {len(st['rejected'])}")
        for r in st["rejected"]:
            print(f"  {r['reason']}" + (f"  {Path(r['source']).name}" if names else ""))
    if st["ignored_hidden"]:
        print(f"Hidden files ignored: {st['ignored_hidden']}")
    if st["other_systems"]:
        print(f"Other system folders (not in this slice): {len(st['other_systems'])}")
    real = [b for b in st["bios"] if b["real"]]
    print(f"BIOS on the stick: {', '.join(b['region'] for b in real) if real else 'none'}"
          f"{'; ' + str(len(st['bios']) - len(real)) + ' other file(s) not used' if len(st['bios']) > len(real) else ''}")
    has = core_bios(project_root)
    print(f"BIOS in the PS1 core's folder: {', '.join(has) if has else 'none (the core uses its built-in OpenBIOS)'}")


def print_plan(plan: Mapping[str, Any], names: bool) -> None:
    for c in plan["candidates"]:
        size = sum(f["bytes"] for f in c["files"])
        extra = f"  {c['title']}" if names else ""
        print(f"  {c['label']}  {c['kind']:8s} {len(c['files']) + (1 if c.get('make_m3u') else 0)} file(s) "
              f"{mb(size):>8s}  {c['decision'].upper()}{'  ' + c['reason'] if c['reason'] else ''}{extra}")
    t = plan["totals"]
    print(f"Accept {t['accept']}, duplicate {t['duplicate']}, reject {t['reject']}; "
          f"{t['rejected_files']} other file(s) rejected")
    if plan["hide"]:
        print(f"Hidden from the list: {len(plan['hide'])} library .iso (a .chd of the same title exists)")
    acc = [b for b in plan["bios"]["stick"] if b["decision"] == "accept"]
    if acc:
        print(f"BIOS to copy: {', '.join(b['region'] for b in acc)}.  {OPENBIOS_WARNING}")
    elif plan["bios"]["openbios_fallback"]:
        print("BIOS: none to copy; PlayStation keeps its built-in OpenBIOS (the list shows \"(OpenBIOS)\")")
    s = plan["space"]
    print(f"Space: {mb(s['needed_bytes'])} needed, {mb(s['free_bytes'])} free: {'ok' if s['ok'] else 'NOT ENOUGH'}")


# --- main -----------------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None, *, project_root: Path = REPO, environ: Mapping[str, str] | None = None,
         active: Callable[[], bool] = game_active, free_bytes: Callable[[Path], int] | None = None) -> int:
    environ = os.environ if environ is None else environ
    if (environ.get(FLAG_ENV) or "").strip() != "1":
        print(f"{FLAG_ENV}=1 is not set: nothing was read or written.", file=sys.stderr)
        return EXIT_FLAG
    ap = argparse.ArgumentParser(prog="import_usb.py")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("inspect", "plan"):
        p = sub.add_parser(name)
        p.add_argument("mount")
        p.add_argument("--names", action="store_true")
    for name in ("apply", "verify"):
        p = sub.add_parser(name)
        p.add_argument("plan", nargs="?")
        p.add_argument("--names", action="store_true")
        if name == "apply":
            p.add_argument("--while-playing", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return EXIT_USAGE
    try:
        if args.command == "inspect":
            st = scan_stick(find_root(args.mount))
            print_inspect(st, args.names, project_root)
            return EXIT_OK if st["candidates"] else EXIT_NOTHING
        if args.command == "plan":
            plan = make_plan(args.mount, project_root, free_bytes=free_bytes)
            path = project_root / DATA_REL / "plans" / f"{plan['created_utc']}.json"
            write_json_atomic(path, plan)
            log = write_log(project_root, sanitized_rows("plan", plan, None))
            print_plan(plan, args.names)
            print(f"Plan: {path.relative_to(project_root)}   log: {log.relative_to(project_root)}")
            if not plan["space"]["ok"]:
                return EXIT_SPACE
            return EXIT_OK if plan["totals"]["accept"] or plan["totals"]["duplicate"] or plan["hide"] or any(
                b["decision"] == "accept" for b in plan["bios"]["stick"]) else EXIT_NOTHING
        plan_path = Path(args.plan) if args.plan else latest(project_root, "plans")
        if plan_path is None or not plan_path.is_file():
            print("no plan: run plan first", file=sys.stderr)
            return EXIT_USAGE
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        applied_path = project_root / DATA_REL / "applied" / plan_path.name
        if args.command == "apply":
            code, summary = apply_plan(plan, project_root, while_playing=args.while_playing, active=active,
                                       free_bytes=free_bytes)
            if "results" in summary:
                write_json_atomic(applied_path, {"plan": plan_path.name, "placed": summary["placed"],
                                                 "bios_copied": summary["bios_copied"]})
                log = write_log(project_root, sanitized_rows("apply", plan, summary))
                for r in summary["results"]:
                    print(f"  {r['label']}  {r['result']}")
                if summary["bios_copied"]:
                    print(f"BIOS copied: {', '.join(summary['bios_copied'])}.  {OPENBIOS_WARNING}")
                print(f"Placed {summary['totals']['placed']}, failed {summary['totals']['failed']}; "
                      f"log: {log.relative_to(project_root)}")
            else:
                print(summary.get("error", "refused"), file=sys.stderr)
            return code
        if not applied_path.is_file():
            print("nothing applied for that plan", file=sys.stderr)
            return EXIT_USAGE
        code, rows = verify_applied(json.loads(applied_path.read_text(encoding="utf-8")), project_root)
        for r in rows:
            print(f"  {r['label']}  {r['result']} ({r['files']} file(s))")
        write_log(project_root, [{"event": "verify", "utc": now_utc()}] + rows)
        return code
    except Usage as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
