#!/usr/bin/env python3
"""B157: add a party mini game by one scripted path — one command per stage, for a title known only by its code.

    python3 tools/party_add_game.py register <code> --players N --system ps1|n64|snes --result winner|places
                                             (--find <words> | --rules-players N) [--setup none|slot1]
                                             [--collect role=slot ...] [--check]
    python3 tools/party_add_game.py learn <code> [--check]
    python3 tools/party_add_game.py bench <code>
    python3 tools/party_add_game.py solo  <code> [--read --winner <seat>]
    python3 tools/party_add_game.py close <code>

Every stage: one verdict; exit 0 only on PASS (1 FAIL, 2 refused or a usage error, 3 waiting: solo's lines); a
verdict file docs/memory/evidence/add_game/<code>/<stage>.json and a page <stage>.md (every cell: read / bar / met);
refused when the stage before has no PASS for the same inputs; run twice on the same inputs -> the same verdict,
nothing written twice; no title, game id, profile id or path in anything written to the repo or printed (a guard
refuses). The private things between stages (the game id, its system, its setup, the game file) are in
~/privyhub_h7/add_game/<code>/binding.json, beside the rules folder, off the repo. Every bar is in BARS with where it
comes from; nothing here judges a picture. Design: docs/memory/evidence/b157_2026-11-18/design_written_before_code.md.

Run-time places (each replaceable, for the tests): PRIVYHUB_H7_RULES (the rules folder), PRIVYHUB_ADD_GAME_HOME
(~/privyhub_h7/add_game), PRIVYHUB_ADD_GAME_EVIDENCE (the repo's docs/memory/evidence/add_game),
PRIVYHUB_ADD_GAME_PROJECT (the hub's project root: logs, slot indexes, the session config), PRIVYHUB_ADD_GAME_HUB
(http://127.0.0.1:8765), PRIVYHUB_ADD_GAME_DROPINS (the companion's drop-in folder), PRIVYHUB_ADD_GAME_SYSTEMCTL
(systemctl), PRIVYHUB_ADD_GAME_KEPT_ROOT (~/privyhub_h7: the kept folders that must not change), PARTY_ADD_GAME_CAPTURE
(module:function giving the pictures).
"""
from __future__ import annotations

import csv
import hashlib
import importlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
STAGES = ("register", "learn", "bench", "solo", "close")
CODE = re.compile(r"^T\d\d$")
SYSTEMS = {"ps1", "n64", "snes"}                       # h7-start's systems (B103 / B123)
NOT_YET = {"ps2": "PS2: no paused load, no frame advance for a held title yet (B159)",
           "gamecube": "GameCube: no paused load confirmation, no frame advance yet (B159)"}
ROLE = re.compile(r"^(begin|other\d*|end_P[1-4]|end_r[1-4]{2,4})$")
FLAG_FILES = {"h7.conf": "PRIVYHUB_H7=1", "party.conf": "PRIVYHUB_PARTY=1"}
UNIT = "privyhub-companion.service"

# Every bar, with where it comes from (T88's and T89's own numbers, or the hub's own constants).
BARS = {
    "margin_needed_min": (0.0796, "T89's kept spec (the lower of T88 0.0921 / T89 0.0796)"),
    "unknown_share_max": (0.105, "T88's worst source: 34 of 38 frames read right, the rest unknown"),
    "wrong_class_max": (0, "T88 and T89: no frame read as another class"),
    "other_as_screen_max": (0, "T88 and T89: 0"),
    "places_wrong_max": (0, "T89: 0"),
    "ended_within_s": (2.0, "B122 / H7-V4: ended 2.0 s after the end screen's first picture at K = 3"),
    "start_within_s": (8.0, "h7_minigame.RECOGNISE_S"),
    "prepare_s_max": (6.0, "H7-V6b's bar for T89 (the larger of T88 5 s / T89 6 s)"),
    "paused_reads_min": (5, "PP-H4 part 1 read 11-18 a hold; at least 5 before the go"),
    "ended_after_load_s": (8.0, "H7-V5's bench bar: ended within 8 s of a hand load"),
    "switch_s_max": (1.6, "B153's bound"),
    "arrival_gap_ms_max": (1200, "B153's bound"),
    "sound_within_s": (4.0, "B150's S: audio_queue_depth > 0 within 4 s of a switch"),
    "underrun_rise_max": (20, "B150's S: underruns rising at most 20 a row"),
    "flag_lines_task": (20, "PP-H4: twenty lines with the two flags"),
    "flag_lines_found": (18, "the eighteen adopted lines"),
}
CAPTURE_SECONDS, CAPTURE_EVERY = 20.0, 0.5             # H7-V1's cadence; 40 pictures a state
MOVED_SHARE, MOVED_GREY = 0.20, 16                     # B140's BEGIN_MOVED: the screen moved on (64x48 cells)
PRACTICE_BOUND_S = 100.0                               # the hub's 90-s practice and its way back
HOLD_READS_S = 6.0                                     # the hold read before the go (>= paused_reads_min reads)
ADVANCE_S = 1.0


class Refused(Exception):
    pass


class Usage(Exception):
    pass


# --- places ------------------------------------------------------------------------------------------------------------
def _env_path(name: str, default: Path) -> Path:
    v = os.environ.get(name, "").strip()
    return Path(v) if v else default


def rules_folder() -> Path:
    return _env_path("PRIVYHUB_H7_RULES", Path.home() / "privyhub_h7" / "rules")


def home(code: str) -> Path:
    return _env_path("PRIVYHUB_ADD_GAME_HOME", Path.home() / "privyhub_h7" / "add_game") / code


def evidence(code: str) -> Path:
    return _env_path("PRIVYHUB_ADD_GAME_EVIDENCE", REPO / "docs" / "memory" / "evidence" / "add_game") / code


def project() -> Path:
    return _env_path("PRIVYHUB_ADD_GAME_PROJECT", REPO)


def hub_base() -> str:
    return os.environ.get("PRIVYHUB_ADD_GAME_HUB", "http://127.0.0.1:8765").rstrip("/") + "/plugins/games/"


# --- the guard: no run-time name in anything written to the repo or printed ---------------------------------------------
class Guard:
    def __init__(self):
        self.names: set[str] = set()

    def add(self, *values) -> None:
        for v in values:
            v = str(v or "").strip()
            if len(v) >= 4:
                self.names.add(v)
                self.names.add(v.casefold())

    def check(self, text: str) -> str:
        low = text.casefold()
        for n in self.names:
            if n.casefold() in low:
                raise Refused("a run-time name would be written or printed; nothing written")
        return text


GUARD = Guard()


def _private_paths() -> None:
    GUARD.add(str(Path.home()), str(rules_folder()), str(project()))


def out(text: str) -> None:
    print(GUARD.check(text))


# --- files ---------------------------------------------------------------------------------------------------------------
def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_if_changed(path: Path, data: bytes | str) -> bool:
    """Writes only when the bytes differ (run twice: nothing written twice). True when written."""
    raw = data.encode() if isinstance(data, str) else data
    if path.is_file() and path.read_bytes() == raw:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(raw)
    tmp.replace(path)
    return True


def read_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


# --- the hub -------------------------------------------------------------------------------------------------------------
def hub(method: str, action: str, query: dict | None = None, timeout: float = 30.0) -> dict:
    url = hub_base() + action + ("?" + urllib.parse.urlencode(query) if query else "")
    req = urllib.request.Request(url, method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"code": r.status, "body": json.loads(r.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode() or "{}")
        except ValueError:
            body = {}
        return {"code": e.code, "body": body}
    except (urllib.error.URLError, OSError, ValueError):
        return {"code": 0, "body": {}}


# --- cells and verdicts ----------------------------------------------------------------------------------------------------
class Cells:
    def __init__(self):
        self.rows: list[dict] = []

    def add(self, cell: str, read, bar, met: bool) -> bool:
        self.rows.append({"cell": cell, "read": read, "bar": bar, "met": bool(met)})
        return bool(met)

    @property
    def passed(self) -> bool:
        return bool(self.rows) and all(r["met"] for r in self.rows)


def verdict_path(code: str, stage: str) -> Path:
    return evidence(code) / f"{stage}.json"


def load_verdict(code: str, stage: str) -> dict | None:
    return read_json(verdict_path(code, stage))


def require(code: str, stage: str, inputs_digest: str) -> None:
    """Refused unless `stage` has a PASS for these inputs."""
    v = load_verdict(code, stage)
    if not v or v.get("verdict") != "PASS":
        raise Refused(f"{stage} has no PASS for {code}: run it first")
    if v.get("inputs") != inputs_digest:
        raise Refused(f"{stage}'s PASS was for other inputs (they changed since): run {stage} again")


def finish(code: str, stage: str, cells: Cells, inputs: str, write: bool = True, note: str = "") -> int:
    v = {"schema": 1, "stage": stage, "code": code, "verdict": "PASS" if cells.passed else "FAIL", "inputs": inputs,
         "cells": cells.rows}
    text = GUARD.check(json.dumps(v, indent=1, sort_keys=True) + "\n")
    lines = [f"# {code} — {stage}: {v['verdict']}", "",
             "Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.", "",
             "| cell | read | bar | met |", "| --- | --- | --- | --- |"]
    for r in cells.rows:
        lines.append(f"| {r['cell']} | {json.dumps(r['read'], sort_keys=True)} | {json.dumps(r['bar'])} | "
                     f"{'yes' if r['met'] else '**no**'} |")
    if note:
        lines += ["", note]
    page = GUARD.check("\n".join(lines) + "\n")
    if write:
        write_if_changed(verdict_path(code, stage), text)
        write_if_changed(evidence(code) / f"{stage}.md", page)
    bad = [r["cell"] for r in cells.rows if not r["met"]]
    out(f"{stage} {code}: {v['verdict']} ({len(cells.rows)} cells" + (f"; not met: {', '.join(bad)}" if bad else "")
        + ")" + ("" if write else " — check only, nothing written"))
    return 0 if cells.passed else 1


# --- the binding (private, off the repo) ------------------------------------------------------------------------------------
def binding_path(code: str) -> Path:
    return home(code) / "binding.json"


def load_binding(code: str) -> dict:
    b = read_json(binding_path(code))
    if not isinstance(b, dict):
        raise Refused(f"register has no PASS for {code}: run it first")
    _guard_binding(b)
    return b


def _guard_binding(b: dict) -> None:
    GUARD.add(b.get("game"), b.get("title"), b.get("content"), b.get("relative_path"),
              (b.get("cheat") or {}).get("profile_id"), ((b.get("cheat") or {}).get("profile_id") or "")[:12])


def kept_folder(code: str) -> Path:
    return home(code) / "kept"


def kept_states(code: str) -> dict[str, str]:
    f = kept_folder(code)
    if not f.is_dir():
        return {}
    return {p.name[:-6]: sha(p) for p in sorted(f.iterdir()) if p.suffix == ".state" and ROLE.match(p.name[:-6])}


def register_inputs(b: dict, kept: dict) -> str:
    return digest({"code": b["code"], "players": b["players"], "system": b["system"], "result": b["result"],
                   "setup": bool(b.get("cheat")), "kept": kept, "game": hashlib.sha256(b["game"].encode()).hexdigest()})


# --- register ------------------------------------------------------------------------------------------------------------
def _companion_lines() -> list[str]:
    d = _env_path("PRIVYHUB_ADD_GAME_DROPINS", Path.home() / ".config" / "systemd" / "user" / f"{UNIT}.d")
    lines = []
    if d.is_dir():
        for p in sorted(d.glob("*.conf")):
            for ln in p.read_text().splitlines():
                ln = ln.strip()
                if ln.startswith("Environment=") and "PRIVYHUB_" in ln:
                    lines.append(ln[len("Environment="):])
    return sorted(lines)


def _find_title(system: str, words: str) -> dict:
    r = hub("GET", "games", {"system": system, "q": words})
    nodes = list({str(n.get("id")): n for n in (r["body"].get("nodes") or [])
                  if n.get("node_type") == "game"}.values())   # one game listed twice is one game
    if r["code"] != 200:
        raise Refused("the hub did not answer the library (is the companion up?)")
    exact = [n for n in nodes if str(n.get("name") or n.get("title") or "").casefold() == words.casefold()]
    nodes = exact if len(exact) == 1 else nodes             # the whole name given: that one
    if len(nodes) != 1:
        raise Refused(f"{len(nodes)} titles match: give more (or less) of the name")
    n = nodes[0]
    d = hub("GET", "details", {"id": n["id"]})["body"]
    rel = str(d.get("relative_path") or "")
    return {"game": str(n["id"]), "title": str(n.get("name") or d.get("title") or ""), "relative_path": rel,
            "content": str(project() / rel) if rel else ""}           # the game file: project-relative (games/)


def _setup_slot1(game: str) -> dict | None:
    r = hub("POST", "cheat-profiles", {"id": game})
    profs = [p for p in (r["body"].get("profiles") or []) if 1 in (p.get("occupied_slots") or [])]
    if len(profs) != 1:
        raise Refused(f"{len(profs)} setups have slot 1 filled for this title: exactly one is needed")
    p = profs[0]
    return {"source_index": int(p["source_index"]), "enabled_cheat_indexes": sorted(p["enabled_cheat_indexes"]),
            "profile_id": str(p["profile_id"]).upper()}


def _slot_file(b: dict, slot: int) -> Path:
    """The user's own slot `slot` for this title (the setup's slot index when there is one), read only."""
    root = project()
    if b.get("cheat"):
        prof = root / "data/games/retroarch/cheat_profiles" / b["game"] / b["cheat"]["profile_id"]
        index = prof / "privyhub_state_slots.json"
        bases = [root, prof, prof / "states"]
    else:
        index = root / "data/games/retroarch/privyhub_state_slots.json"
        bases = [root]
    games = (read_json(index, {}) or {}).get("games") or {}
    key = b["system"].casefold() + "::" + b["relative_path"].replace("\\", "/").casefold()
    rec = ((games.get(key) or {}).get("slots") or {}).get(str(slot))
    if not isinstance(rec, dict) or not rec.get("state_file"):
        raise Refused(f"slot {slot} is empty for this title")
    for base in bases:
        p = base / str(rec["state_file"])
        if p.is_file():
            return p
    raise Refused(f"slot {slot}'s file is not there")


def ps1_four_on(game: str) -> bool:
    """B63: the title's own four-player setting (the hub's controller overrides, `games` -> <id> -> ps1_multitap)."""
    over = read_json(project() / "data/games/retroarch/controller_overrides.json", {}) or {}
    entry = (over.get("games") or {}).get(game) if isinstance(over, dict) else None
    return isinstance(entry, dict) and entry.get("ps1_multitap") == "port1"


def _roles_needed(players: int, result: str) -> list[str]:
    return ["begin", "other"] + ([f"end_P{k}" for k in range(1, players + 1)] if result == "winner" else [])


def cmd_register(code: str, a: dict) -> int:
    cells, b, inputs = _register(code, a)
    return finish(code, "register", cells, inputs, write=not a["check"])


def _register(code: str, a: dict) -> tuple[Cells, dict, str]:
    players, system, result = int(a["players"]), str(a["system"]).casefold(), str(a["result"])
    check = a["check"]
    cells = Cells()
    if a.get("rules_players"):                              # a title already in the rules folder (T88 / T89)
        n = int(a["rules_players"])
        sides = [p for p in sorted(rules_folder().glob("*.party.json"))
                 if (read_json(p, {}) or {}).get("players") == n]
        if len(sides) != 1:
            raise Refused(f"{len(sides)} titles in the rules folder have {n} players: exactly one is needed")
        game = sides[0].name[: -len(".party.json")]
        side = read_json(sides[0], {})
        b = {"code": code, "game": game, "players": players, "system": system, "result": result,
             "cheat": side.get("cheat"), "relative_path": "", "title": "", "content": "", "described": True}
    else:
        if not a.get("find"):
            raise Usage("--find <words> or --rules-players <n>")
        GUARD.add(a["find"])
        found = _find_title(system, a["find"])
        b = {"code": code, "players": players, "system": system, "result": result, **found}
        _guard_binding(b)
        b["cheat"] = _setup_slot1(b["game"]) if a.get("setup") == "slot1" else None
    _guard_binding(b)
    cells.add("system can hold a party mini game", system, sorted(SYSTEMS), system in SYSTEMS)
    if system in NOT_YET:
        cells.add("why not", NOT_YET[system], "-", False)
    cells.add("players", players, "2 or 4 (the board has no three-player hub game)", players in (2, 4))
    cells.add("result kind", result, ["winner", "places"], result in ("winner", "places"))
    if system == "ps1" and players == 4 and not b.get("described"):
        on = ps1_four_on(b["game"])
        cells.add("four-player PS1: the title's four-player setting on", on, True, on)
    if not check and a.get("collect"):                      # the user's slots copied to the kept folder (read only)
        kf = kept_folder(code)
        kf.mkdir(parents=True, exist_ok=True)
        for item in a["collect"]:
            role, _, slot = item.partition("=")
            if not ROLE.match(role) or slot not in ("1", "2", "3"):
                raise Usage(f"--collect role=slot (roles begin, other, other2, end_P1..4, end_r<places>; slots 1-3)")
            data = _slot_file(b, int(slot)).read_bytes()
            write_if_changed(kf / f"{role}.state", data)
    if b.get("described"):                                  # its rules folder as it is: the files the listing needs
        r = rules_folder()
        begin = r / (f"{b['game']}.{b['cheat']['profile_id'][:12].upper()}.state" if b.get("cheat") else f"{b['game']}.state")
        cells.add("begin state in the rules folder", begin.is_file() and begin.stat().st_size > 0, True,
                  begin.is_file() and begin.stat().st_size > 0)
        spec = read_json(r / f"{b['game']}.endscreen.json")
        cells.add("spec in the rules folder", spec is not None, True, spec is not None)
        kept = {}
    else:
        kept = kept_states(code)
        need = _roles_needed(players, result)
        missing = [x for x in need if x not in kept]
        cells.add("kept states present", sorted(kept), need + (["end_r<rows>"] if result == "places" else []),
                  not missing)
        if missing:
            cells.add("missing", missing, [], False)
        cells.add("kept states distinct", len(set(kept.values())), len(kept), len(set(kept.values())) == len(kept))
        empty = [k for k in kept if (kept_folder(code) / f"{k}.state").stat().st_size == 0]
        cells.add("kept states not empty", empty, [], not empty)
        if result == "places":
            rows = [k[5:] for k in kept if k.startswith("end_r")]
            ok_rows = [r for r in rows if len(r) == players and sorted(r) == [str(i) for i in range(1, players + 1)]]
            cover = all({r[c] for r in ok_rows} == {str(i) for i in range(1, players + 1)} for c in range(players))
            cells.add("results rows: every place in every column", sorted(ok_rows), "each column sees 1..n",
                      bool(ok_rows) and len(ok_rows) == len(rows) and cover)
        extra = [k for k in kept if k.startswith("end_") and k not in need and result == "winner"]
        cells.add("no ending of another kind", extra, [], not extra)
    flag_lines = _companion_lines()
    b["found_lines"] = digest(flag_lines)
    cells.add("the companion's lines as found", len(flag_lines), BARS["flag_lines_found"][0],
              len(flag_lines) == BARS["flag_lines_found"][0] or b.get("described"))
    inputs = register_inputs(b, kept)
    b["register_inputs"] = inputs
    if not check:
        write_if_changed(binding_path(code), json.dumps(b, indent=1, sort_keys=True) + "\n")
    return cells, b, inputs


# --- learn ---------------------------------------------------------------------------------------------------------------
def _endscreen():
    sys.path.insert(0, str(TOOLS))
    import h7_endscreen
    return h7_endscreen


def _capture_fn():
    spec = os.environ.get("PARTY_ADD_GAME_CAPTURE", "party_add_game_capture:capture")
    mod, _, fn = spec.partition(":")
    sys.path.insert(0, str(TOOLS))
    return getattr(importlib.import_module(mod), fn)


def _role_class(role: str) -> str:
    if role == "begin":
        return "start"
    if role.startswith("other"):
        return "other"
    return role


def _pictures(code: str, b: dict, kept: dict) -> Path:
    """Every kept state's run (made once for these kept states; again only if they change)."""
    pics = home(code) / "pictures"
    mark = pics / "made_from.json"
    if read_json(mark) == kept:
        return pics
    if pics.exists():
        shutil.rmtree(pics)                                  # the tool's own pictures of other kept states
    cap = _capture_fn()
    for role in sorted(kept):
        run = pics / role
        run.mkdir(parents=True)
        rows = cap(kept_folder(code) / f"{role}.state", b, run, CAPTURE_SECONDS, CAPTURE_EVERY)
        with (run / "index.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["seconds", "file"])
            for t, name in rows:
                w.writerow([f"{t:.2f}", name])
    write_if_changed(mark, json.dumps(kept, sort_keys=True))
    return pics


def _small(path: Path):
    from PIL import Image
    import numpy as np
    with Image.open(path) as im:
        return np.asarray(im.convert("L").resize((64, 48)), dtype=np.int16)


def _labels(pics: Path, kept: dict, es) -> dict:
    """Labels from the state each picture came from — never by eye. A begin / end frame whose 64x48 grey copy has
    MOVED_SHARE of its cells changed by more than MOVED_GREY from its run's first frame (B140's measure) is `ignore`
    (the screen moved on). Consecutive frames of one label are one range (the learner halves each range)."""
    runs, classes = {}, {}
    for role in sorted(kept):
        cls = _role_class(role)
        classes[cls] = cls
        rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((pics / role / "index.csv").open())]
        first, spans = None, []
        for t, f in rows:
            lab = cls
            if cls != "other":
                v = _small(pics / role / f)
                first = v if first is None else first
                if float((abs(v - first) > MOVED_GREY).mean()) >= MOVED_SHARE:
                    lab = "ignore"
            if spans and spans[-1]["label"] == lab:
                spans[-1]["to"] = t
            else:
                spans.append({"from": t, "to": t, "label": lab})
        runs[role] = spans
    classes["ignore"] = "ignore"
    return {"classes": classes, "runs": runs}


def _spec_cells(cells: Cells, spec: dict) -> None:
    sep = spec.get("separable") or ((spec.get("places") or {}).get("separable") or {})
    cells.add("spec usable", bool(spec.get("usable", True)), True, bool(spec.get("usable", True)))
    cells.add("every class separable", sorted(k for k, v in sep.items() if not v), [],
              bool(sep) and all(sep.values()))
    m = spec.get("margin_needed") or (spec.get("places") or {}).get("margin_needed")
    cells.add("margin_needed", m, f">= {BARS['margin_needed_min'][0]} ({BARS['margin_needed_min'][1]})",
              m is not None and float(m) >= BARS["margin_needed_min"][0])


def _replay_cells(cells: Cells, es, spec: dict, arrays: dict, pics: Path, kept: dict, labels: dict) -> None:
    from PIL import Image
    for role in sorted(kept):
        cls = _role_class(role)
        rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((pics / role / "index.csv").open())]
        now = [0.0]
        reader = es.Reader(spec, arrays, clock=lambda: now[0])
        ended = es.Ended(spec)
        if cls != "start":
            ended.start_loaded()                             # as the hub's load of the begin
        got, first_start = None, None
        for t, f in rows:
            now[0] = t
            with Image.open(pics / role / f) as im:
                r = reader.read(im.convert("L"), now=t)
            if r["class"] == "start" and first_start is None:
                first_start = t
            done = ended.feed(r["class"], r.get("places"))
            if done and got is None:
                got = (t, done, list(ended.places) if ended.places else None)
        if cls == "start":
            cells.add(f"{role}: never ended", got is None, True, got is None)
            cells.add(f"{role}: recognised within", first_start, f"<= {BARS['start_within_s'][0]} s",
                      first_start is not None and first_start <= BARS["start_within_s"][0])
        elif cls == "other":
            cells.add(f"{role}: never ended", got is None, True, got is None)
        else:
            want_places = [int(c) for c in cls[5:]] if cls.startswith("end_r") else None
            right = got is not None and (got[1] == cls or (want_places is not None and got[2] == want_places))
            cells.add(f"{role}: ended as itself", None if got is None else (got[1], got[2]), cls, right)
            cells.add(f"{role}: ended within", None if got is None else round(got[0] - rows[0][0], 2),
                      f"<= {BARS['ended_within_s'][0]} s",
                      got is not None and got[0] - rows[0][0] <= BARS["ended_within_s"][0])


def _sidecar(b: dict, spec: dict) -> dict:
    side: dict = {"players": b["players"]}
    if b["result"] == "winner":
        side["result"] = "winner"                            # B158
    if b.get("cheat"):
        side["cheat"] = b["cheat"]
    return side


def _begin_name(b: dict) -> str:
    return f"{b['game']}.{b['cheat']['profile_id'][:12].upper()}.state" if b.get("cheat") else f"{b['game']}.state"


def cmd_learn(code: str, a: dict) -> int:
    cells = Cells()
    es = _endscreen()
    described = False
    if not a["check"]:
        b = load_binding(code)
        described = bool(b.get("described"))
        if described:                                        # T88 / T89 as they are: register's PASS needed
            require(code, "register", b["register_inputs"])
    if a["check"] or described:                              # the kept spec's own numbers; the rules never written
        if a["check"]:
            if not a.get("rules_players"):
                raise Usage("learn --check describes a title in the rules folder: --rules-players <n> and register's "
                            "options")
            reg, b, _inputs = _register(code, a)             # register's check, in memory
            if not reg.passed:
                raise Refused("register --check is not PASS for these options")
        r = rules_folder()
        spec, arrays = es.load_spec(r / f"{b['game']}.endscreen.json")
        _spec_cells(cells, spec)
        npz = r / spec["arrays"]
        cells.add("the arrays' sha256", sha(npz) == spec.get("arrays_sha256"), True, sha(npz) == spec.get("arrays_sha256"))
        side = read_json(r / f"{b['game']}.party.json", {})
        n = side.get("players")
        ok = (n == b["players"] and (("scores" in side and sorted(side["scores"]) == sorted(spec["end_classes"]))
                                     or spec.get("version") == es.VERSION_PLACES or side.get("result") == "winner"))
        cells.add("sidecar as the listing needs it", ok, True, ok)
        return finish(code, "learn", cells, learn_inputs(code, b), write=not a["check"])
    kept = kept_states(code)
    require(code, "register", register_inputs(b, kept))
    pics = _pictures(code, b, kept)
    labels = _labels(pics, kept, es)
    write_if_changed(pics / "labels.json", json.dumps(labels, sort_keys=True))
    r = rules_folder()
    spec_path = r / f"{b['game']}.endscreen.json"
    made = b.get("learnt") or {}
    if made.get("from") == digest(kept) and spec_path.is_file() and sha(spec_path) == made.get("spec"):
        spec, arrays = es.load_spec(spec_path)               # learnt before from these states: not again
    else:
        spec, arrays, _rep = es.learn(pics, pics / "labels.json", "first", name=b["game"])
    _spec_cells(cells, spec)
    fn = es.score_places if spec.get("version") == es.VERSION_PLACES else es.score
    sc = fn(pics, pics / "labels.json", spec, arrays, "second")
    if spec.get("version") == es.VERSION_PLACES:
        rows = sc.get("rows") or {}
        wrong = sum(v.get("wrong", 0) for v in rows.values())
        unknown = sum(v.get("unknown", 0) for v in rows.values())
        n = sum(v.get("n", 0) for v in rows.values()) or 1
        cells.add("places_wrong", sc.get("places_wrong"), BARS["places_wrong_max"][0],
                  sc.get("places_wrong", 1) <= BARS["places_wrong_max"][0])
    else:
        conf = sc.get("confusion") or {}
        held = {c: row for c, row in conf.items() if c not in ("other", "ignore")}
        wrong = sum(cnt for c, row in held.items() for k, cnt in row.items() if k not in (c, "unknown", "other"))
        unknown = sum(row.get("unknown", 0) + row.get("other", 0) for row in held.values())
        n = sum(sum(row.values()) for row in held.values()) or 1
    cells.add("held-out frames read as another class", wrong, BARS["wrong_class_max"][0], wrong <= BARS["wrong_class_max"][0])
    cells.add("held-out frames read unknown (share)", round(unknown / n, 4), f"<= {BARS['unknown_share_max'][0]}",
              unknown / n <= BARS["unknown_share_max"][0])
    cells.add("other read as a screen", sc.get("other_read_as_screen"), BARS["other_as_screen_max"][0],
              (sc.get("other_read_as_screen") or 0) <= BARS["other_as_screen_max"][0])
    _replay_cells(cells, es, spec, arrays, pics, kept, labels)
    if b["result"] == "winner" and spec.get("version") == es.VERSION_PLACES:
        pass                                                 # winner read from a row of places (B158)
    elif b["result"] == "places":
        cells.add("a row of places learnt", spec.get("version") == es.VERSION_PLACES, True,
                  spec.get("version") == es.VERSION_PLACES)
    inputs = learn_inputs(code, b)
    if cells.passed:                                         # only a passing title reaches the rules folder
        begin = r / _begin_name(b)
        side_path = r / f"{b['game']}.party.json"
        side = json.dumps(_sidecar(b, spec), indent=1, sort_keys=True) + "\n"
        for p, want in ((begin, (kept_folder(code) / "begin.state").read_bytes()), (side_path, side.encode())):
            if p.exists() and p.read_bytes() != want and not made:
                cells.add("rules folder: no other title's file overwritten", False, True, False)
                return finish(code, "learn", cells, inputs)
        if not (made.get("from") == digest(kept) and spec_path.is_file() and sha(spec_path) == made.get("spec")):
            es.save_spec(spec, arrays, spec_path)
        write_if_changed(begin, (kept_folder(code) / "begin.state").read_bytes())
        write_if_changed(side_path, side)
        b["learnt"] = {"from": digest(kept), "spec": sha(spec_path)}
        write_if_changed(binding_path(code), json.dumps(b, indent=1, sort_keys=True) + "\n")
    return finish(code, "learn", cells, inputs)


def learn_inputs(code: str, b: dict) -> str:
    if b.get("described"):
        return digest({"register": b["register_inputs"], "described": True})
    return digest({"register": b["register_inputs"], "kept": kept_states(code)})


# --- the files that must not change (before = after) ------------------------------------------------------------------------
def files_digest(b: dict) -> dict:
    """sha256 of the title's user slots and slot pictures (both indexes), every rules file, the kept folders (names
    hashed: no name is kept)."""
    roots = [project() / "data/games/retroarch/states", project() / "data/games/retroarch/cheat_profiles",
             rules_folder(), home(b["code"]) / "kept"]
    h7 = _env_path("PRIVYHUB_ADD_GAME_KEPT_ROOT", Path.home() / "privyhub_h7")      # the kept H7 folders
    roots += [p for p in sorted(h7.iterdir()) if p.is_dir() and p.name not in ("rules", "add_game")] if h7.is_dir() else []
    out_ = {}
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and not p.name.endswith(".state8"):
                out_[hashlib.sha256(str(p.relative_to(root.parent)).encode()).hexdigest()[:16]] = sha(p)
    return out_


# --- the flags --------------------------------------------------------------------------------------------------------------
def _systemctl(*args: str) -> int:
    cmd = os.environ.get("PRIVYHUB_ADD_GAME_SYSTEMCTL", "systemctl").split() + ["--user", *args]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120).returncode


def _dropins() -> Path:
    return _env_path("PRIVYHUB_ADD_GAME_DROPINS", Path.home() / ".config" / "systemd" / "user" / f"{UNIT}.d")


def users_session() -> str | None:
    """Why the companion must not be restarted now (the user's own game or stream), else None. A hub that does not
    answer has nothing running to protect."""
    st = hub("GET", "status", timeout=5)
    ns = hub("GET", "native-stream-status", timeout=5)
    if ns["code"] == 200 and ns["body"].get("active"):
        return "a client's stream is up"
    if st["code"] == 200 and st["body"].get("active") and st["body"].get("launch_kind") != "godot":
        return "a game other than the board is running"
    return None


def flags(on: bool) -> int:
    d = _dropins()
    if any((d / name).is_file() != on for name in FLAG_FILES):   # a restart is needed: never in the user's session
        why = users_session()
        if why is not None:
            raise Refused(f"{why}: the companion is not restarted, nothing changed")
    changed = False
    for name, line in FLAG_FILES.items():
        p = d / name
        if on and not p.is_file():
            write_if_changed(p, f"[Service]\nEnvironment={line}\n")
            changed = True
        if not on and p.is_file():
            p.unlink()
            changed = True
    if changed:
        _systemctl("daemon-reload")
        _systemctl("restart", UNIT)
        end = time.monotonic() + 60
        while time.monotonic() < end and hub("GET", "status", timeout=3)["code"] != 200:
            time.sleep(0.5)
    return len(_companion_lines())


# --- RetroArch's own command port (read after the launch answers) ------------------------------------------------------------
def ra_port() -> int | None:
    cfg = project() / "data/games/retroarch/config/privyhub-session.cfg"
    try:
        m = re.search(r'(?m)^network_cmd_port\s*=\s*"?(\d+)"?', cfg.read_text())
    except OSError:
        return None
    return int(m.group(1)) if m else None


def ra(cmd: str, port: int | None, answer: bool = True, timeout: float = 0.5) -> str:
    if port is None:
        return ""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(cmd.encode(), ("127.0.0.1", port))
        if not answer:
            return ""
        return s.recvfrom(4096)[0].decode(errors="replace")
    except OSError:
        return ""
    finally:
        s.close()


# --- bench -------------------------------------------------------------------------------------------------------------
def party_rows(since: int = 0) -> list[dict]:
    p = project() / "logs/games/party.jsonl"
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out_ = []
    for ln in lines[since:]:
        try:
            out_.append(json.loads(ln))
        except ValueError:
            pass
    return out_


def _count(p: Path) -> int:
    try:
        return len(p.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return 0


def _wait(pred, bound: float, every: float = 0.25):
    end = time.monotonic() + bound
    last = None
    while time.monotonic() < end:
        last = hub("GET", "party-minigame-result")["body"]
        if pred(last):
            return last
        time.sleep(every)
    return last


def _token(b: dict) -> str | None:
    lst = hub("GET", "party-minigames")["body"].get("minigames") or []
    want = [m for m in lst if m.get("players") == b["players"] and (not b.get("title") or m.get("title") == b["title"])]
    return want[0]["id"] if len(want) == 1 else None


def _board_up() -> list:
    """The board as the session: [up, how] — already up, or launched (its answer's code and error)."""
    st = hub("GET", "status")["body"]
    if st.get("launch_kind") == "godot":
        return [True, "already up"]
    nodes = hub("GET", "games", {"system": "party"})["body"].get("nodes") or []
    board = next((n["id"] for n in nodes if n.get("node_type") == "game"), None)
    if board is None:
        return [False, "no board in the library"]
    r = hub("POST", "launch", {"id": board})
    hub("POST", "bench-release")
    end = time.monotonic() + 30
    while time.monotonic() < end:
        if hub("GET", "status")["body"].get("launch_kind") == "godot":
            return [True, f"launched {r['code']}"]
        time.sleep(0.5)
    return [False, f"launch {r['code']}: {str(r['body'].get('error') or '')[:100]}"]


def _held_ready(token: str, seats: str) -> tuple[dict, dict | None]:
    r = hub("POST", "party-minigame-start", {"id": token, "seats": seats, "bench": "1", "hold": "1"})
    res = _wait(lambda x: x.get("phase") == "ready" or x.get("state") in ("ended", "given_up"), 30)
    return r, res


def _scratch_load(b: dict, kept_file: Path, port: int | None) -> Path | None:
    """The ending to the title's scratch slot 8 beside its slot 1 (as A's hand loads), then LOAD_STATE_SLOT 8."""
    try:
        slot1 = _slot_file(b, 1)
    except Refused:
        return None
    scratch = slot1.with_name(re.sub(r"\.state\d*$", ".state8", slot1.name))
    shutil.copyfile(kept_file, scratch)
    if b["system"] == "n64":                                 # B123: an N64 load only into a paused core
        ra("PAUSE_TOGGLE", port, answer=False)
        time.sleep(0.2)
    ra("LOAD_STATE_SLOT 8", port)
    if b["system"] == "n64":
        time.sleep(0.2)
        ra("PAUSE_TOGGLE", port, answer=False)
    return scratch


def bench_inputs(code: str, b: dict) -> str:
    r = rules_folder()
    files = [r / f"{b['game']}.endscreen.json", r / f"{b['game']}.party.json", r / _begin_name(b)]
    return digest({"learn": learn_inputs(code, b), "rules": [sha(p) if p.is_file() else None for p in files]})


def cmd_bench(code: str, a: dict) -> int:
    b = load_binding(code)
    if b.get("described"):
        raise Refused("a title already in the rules folder had its bench in its own task: go on with solo")
    require(code, "learn", learn_inputs(code, b))
    _private_paths()
    cells = Cells()
    lines = flags(True)
    cells.add("the companion's lines with the two flags", lines, BARS["flag_lines_task"][0],
              lines == BARS["flag_lines_task"][0])
    before = files_digest(b)
    write_if_changed(home(code) / "files_before.json", json.dumps(before, sort_keys=True))
    up = _board_up()
    if not cells.add("the board up as the session", up, [True, "…"], up[0]):
        return finish(code, "bench", cells, bench_inputs(code, b))
    token = _token(b)
    if not cells.add("the title listed by party-minigames", token is not None, True, token is not None):
        return finish(code, "bench", cells, bench_inputs(code, b))
    seats = ",".join(str(i) for i in range(1, b["players"] + 1))
    kept = kept_states(code)
    endings = sorted(k for k in kept if k.startswith("end_"))
    side = read_json(rules_folder() / f"{b['game']}.party.json", {})
    # 1. a held start, PAUSED to the go, no reload, keys_written; a practice by time, ready again
    r0 = len(party_rows())
    start, res = _held_ready(token, seats)
    cells.add("held start answered", [start["code"], str(start["body"].get("error") or "")[:120]], [200, ""],
              start["code"] == 200)
    rows = party_rows(r0)
    ready = next((x for x in rows if x.get("step") == "minigame_ready"), {})
    cells.add("held start ready", [(res or {}).get(k) for k in ("phase", "state", "why")], ["ready", "starting", None],
              (res or {}).get("phase") == "ready")
    cells.add("prepare_s", ready.get("prepare_s"), f"<= {BARS['prepare_s_max'][0]}",
              ready.get("prepare_s") is not None and ready["prepare_s"] <= BARS["prepare_s_max"][0])
    launch = next((x for x in rows if x.get("step") == "minigame_launch"), {})
    cells.add("keys_written", launch.get("keys_written"), True, launch.get("keys_written") is True)
    port = ra_port()
    reads = []
    end = time.monotonic() + HOLD_READS_S
    while time.monotonic() < end:
        reads.append("PAUSED" in ra("GET_STATUS", port))
        time.sleep(1.0)
    cells.add("PAUSED at every read to the go", f"{sum(reads)}/{len(reads)}",
              f"all, >= {BARS['paused_reads_min'][0]}", len(reads) >= BARS["paused_reads_min"][0] and all(reads))
    watches = [x for x in party_rows(r0) if x.get("step") == "minigame_watch"]
    cells.add("no reload before the go", len(watches), 1, len(watches) == 1)
    hub("POST", "party-minigame-go", {"practice": "1"})
    _wait(lambda x: x.get("state") == "playing", 20)
    back = _wait(lambda x: x.get("phase") == "ready" or x.get("state") in ("ended", "given_up"), PRACTICE_BOUND_S, 0.5)
    rows = party_rows(r0)
    pend = next((x for x in rows if x.get("step") == "minigame_practice_end"), {})
    again = [x for x in rows if x.get("step") == "minigame_ready" and x.get("after_practice")]
    cells.add("practice ended by time", pend.get("by"), "time", pend.get("by") == "time")
    cells.add("ready again after the practice", (back or {}).get("phase"), "ready",
              (back or {}).get("phase") == "ready" and bool(again))
    cells.add("ready again within", again[0].get("prepare_s") if again else None, f"<= {BARS['prepare_s_max'][0]}",
              bool(again) and again[0].get("prepare_s", 99) <= BARS["prepare_s_max"][0])
    hub("POST", "party-minigame-end")
    _wait(lambda x: x.get("closed") or x.get("state") == "none", 20)
    # 2. each kept ending: a held start, the real go, the ending loaded -> ended with its class and scores
    for ending in endings:
        r1 = len(party_rows())
        _start, res = _held_ready(token, seats)
        hub("POST", "party-minigame-go")
        _wait(lambda x: x.get("state") == "playing", 20)
        time.sleep(ADVANCE_S)
        port = ra_port()
        t_load = time.monotonic()
        scratch = _scratch_load(b, kept_folder(code) / f"{ending}.state", port)
        got = _wait(lambda x: x.get("state") in ("ended", "given_up"), BARS["ended_after_load_s"][0] + 2, 0.2) or {}
        took = round(time.monotonic() - t_load, 2)
        if scratch is not None:
            scratch.unlink(missing_ok=True)
        want_cls = ending if ending.startswith("end_P") else "end"
        exp_scores, exp_winner = _expected(b, side, ending)
        cells.add(f"{ending}: ended with its class", [got.get("state"), got.get("class")], ["ended", want_cls],
                  got.get("state") == "ended" and got.get("class") == want_cls)
        cells.add(f"{ending}: scores", got.get("scores"), exp_scores, got.get("scores") == exp_scores)
        if exp_winner is not None:
            cells.add(f"{ending}: winner", got.get("winner"), exp_winner, got.get("winner") == exp_winner)
        cells.add(f"{ending}: ended within (s)", took, f"<= {BARS['ended_after_load_s'][0]}",
                  took <= BARS["ended_after_load_s"][0])
        hub("POST", "party-minigame-end")
        _wait(lambda x: x.get("closed") or x.get("state") == "none", 20)
        launch = next((x for x in party_rows(r1) if x.get("step") == "minigame_launch"), {})
        cells.add(f"{ending}: keys_written", launch.get("keys_written"), True, launch.get("keys_written") is True)
    hub("POST", "stop")
    after = files_digest(b)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    cells.add("every file after = before", len(changed), 0, not changed)
    return finish(code, "bench", cells, bench_inputs(code, b))


def _expected(b: dict, side: dict, ending: str) -> tuple[list, int | None]:
    n = b["players"]
    if ending.startswith("end_P"):
        k = int(ending[5:])
        if side.get("result") == "winner" or "scores" not in side:
            return [1 if j == k - 1 else 0 for j in range(n)], (k if side.get("result") == "winner" else None)
        return list(side["scores"][ending]), None
    places = [int(c) for c in ending[5:]]
    p2s = [1] + [0] * (n - 1) if side.get("result") == "winner" else side.get("places_to_scores", list(range(n, 0, -1)))
    return [p2s[q - 1] for q in places], (places.index(1) + 1 if side.get("result") == "winner" else None)


# --- solo ---------------------------------------------------------------------------------------------------------------
LOGS = {"party": "logs/games/party.jsonl", "heartbeat": "logs/games/native_stream_heartbeat.log",
        "video": "logs/games/native_video_alpha.log"}
BAND = "PRACTICE — press Select (Share) to go back"


def _board_log() -> Path | None:
    logs = sorted((project() / "logs/games").glob("*-party.log"))
    return logs[-1] if logs else None


def solo_lines(b: dict) -> list[str]:
    n = b["players"]
    who = "you and one more person" if n == 2 else "four people"
    return [
        "YOU, now: open Games, 'PrivyParty (1)', Launch on Companion, Start Fresh; play the board with "
        f"{who} until a mini game for {n} comes up (this game).",
        "YOU, now: on its load screen press △ for a practice, leave it with the Select button (Share on a "
        "PlayStation pad), then press ✕ to play it for real and play it to its end.",
        "YOU, now: when you are back on the board, reply with who won (P1, P2" + (", P3 or P4" if n == 4 else "") + ").",
    ]


def solo_after(code: str, b: dict) -> str:
    """solo follows bench's PASS — or, for a title already in the rules folder (T88 / T89), learn's."""
    if b.get("described"):
        require(code, "learn", learn_inputs(code, b))
        return learn_inputs(code, b)
    require(code, "bench", bench_inputs(code, b))
    return bench_inputs(code, b)


def cmd_solo(code: str, a: dict) -> int:
    b = load_binding(code)
    before_solo = solo_after(code, b)
    _private_paths()
    mark_path = home(code) / "solo_mark.json"
    if not a.get("read"):
        n_lines = flags(True)                                # the bench flags for the task (bench put them on)
        if n_lines != BARS["flag_lines_task"][0]:
            raise Refused(f"the companion has {n_lines} lines, not {BARS['flag_lines_task'][0]}: nothing asked of the user")
        bl = _board_log()
        mark = {k: _count(project() / v) for k, v in LOGS.items()}
        mark["board_log"] = bl.name if bl else None
        mark["board_lines"] = _count(bl) if bl else 0
        mark["video_bytes"] = (project() / LOGS["video"]).stat().st_size if (project() / LOGS["video"]).is_file() else 0
        if not mark_path.is_file():
            write_if_changed(mark_path, json.dumps(mark, sort_keys=True))
        for ln in solo_lines(b):
            out(ln)
        out(f"solo {code}: WAITING — after the user's reply: solo {code} --read --winner <seat>")
        return 3
    mark = read_json(mark_path)
    if not mark:
        raise Refused("solo's lines were not given yet: run solo first")
    winner = int(a["winner"])
    cells = Cells()
    rows = party_rows(mark["party"])
    sw = [x for x in rows if x.get("step") == "minigame_stream" and x.get("planned")]
    cells.add("planned switches", len(sw), ">= 4 (a practice in and out, the go, the end)", len(sw) >= 4)
    cells.add("every planned switch switched", all(x.get("switched") for x in sw), True,
              bool(sw) and all(x.get("switched") for x in sw))
    secs = [x.get("seconds") for x in sw]
    cells.add("every planned switch's seconds", secs, f"<= {BARS['switch_s_max'][0]}",
              bool(secs) and all(s is not None and s <= BARS["switch_s_max"][0] for s in secs))
    hb = []
    for ln in (project() / LOGS["heartbeat"]).read_text(errors="replace").splitlines()[mark["heartbeat"]:] \
            if (project() / LOGS["heartbeat"]).is_file() else []:
        try:
            hb.append(json.loads(ln))
        except ValueError:
            pass
    hbt = [(_utc(r.get("received_at_utc")), r) for r in hb]
    s_ok, gaps = [], []
    times = [x.get("time_unix") for x in sw]
    for i, t in enumerate(times):
        nxt = times[i + 1] if i + 1 < len(times) else None
        after = [(ts, r) for ts, r in hbt if ts is not None and ts >= t and (nxt is None or ts < nxt)]
        sound = any((r.get("audio_queue_depth") or 0) > 0 for ts, r in after if ts - t <= BARS["sound_within_s"][0])
        und = [r.get("audio_underruns") for ts, r in after if r.get("audio_underruns") is not None]
        rise = max([y - x for x, y in zip(und, und[1:])] or [0])
        s_ok.append(sound and rise <= BARS["underrun_rise_max"][0])
        gap = next((r.get("audio_max_arrival_gap_ms") for ts, r in after), None)
        gaps.append(gap)
    cells.add("S: sound within 4 s of each switch, underruns rising <= 20 a row", s_ok, "all", bool(s_ok) and all(s_ok))
    cells.add("audio_max_arrival_gap_ms at each switch", gaps, f"<= {BARS['arrival_gap_ms_max'][0]}",
              bool(gaps) and all(g is not None and g <= BARS["arrival_gap_ms_max"][0] for g in gaps))
    vid = project() / LOGS["video"]
    enc = []
    if vid.is_file():
        with vid.open("rb") as f:
            f.seek(mark.get("video_bytes", 0))
            enc = [ln for ln in f.read().decode(errors="replace").splitlines() if ln.startswith("encoder argv:")]
    practices = [x for x in rows if x.get("step") == "minigame_playing" and x.get("practice")]
    band = sum(1 for ln in enc if BAND in ln)
    cells.add("the band in the practices' encoder lines only", [band, len(practices)], "band lines = practices >= 1",
              band == len(practices) and band >= 1)
    launch = next((x for x in rows if x.get("step") == "minigame_launch"), {})
    cells.add("keys_written", launch.get("keys_written"), True, launch.get("keys_written") is True)
    bl = _board_log()
    blines = []
    if bl is not None:
        skip = mark["board_lines"] if bl.name == mark.get("board_log") else 0
        blines = [ln.split("PrivyParty: hub mini game: ", 1)[1] for ln in
                  bl.read_text(errors="replace").splitlines()[skip:] if "PrivyParty: hub mini game: " in ln]
    order = [("cards", r"^cards \d+, chose"), ("practice", r"^practice$"), ("load screen again", r"^load screen again$"),
             ("start", r"^start$"), ("scores", r"^scores \[")]
    pos, seen = 0, []
    for name, pat in order:
        k = next((i for i in range(pos, len(blines)) if re.match(pat, blines[i])), None)
        seen.append(name if k is not None else f"{name}: missing")
        pos = (k + 1) if k is not None else pos
    cells.add("the board's lines in order", seen, [x for x, _ in order], seen == [x for x, _ in order])
    ended = [x for x in rows if x.get("step") == "minigame_ended"]
    last = ended[-1] if ended else {}
    hub_winner = last.get("winner")
    if hub_winner is None and last.get("scores"):
        sc = last["scores"]
        hub_winner = sc.index(max(sc)) + 1 if sc.count(max(sc)) == 1 else None
    cells.add("the hub's result = the winner the user named", hub_winner, winner, hub_winner == winner)
    return finish(code, "solo", cells, digest({"after": before_solo, "mark": mark, "winner": winner}))


def _utc(s) -> float | None:
    if not s:
        return None
    try:
        import datetime as dt
        return dt.datetime.strptime(str(s).replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
    except ValueError:
        return None


# --- close ----------------------------------------------------------------------------------------------------------------
def cmd_close(code: str, a: dict) -> int:
    """Always, last — also after a stop: it needs only the binding (no stage's PASS)."""
    b = load_binding(code)
    _private_paths()
    cells = Cells()
    hub("POST", "stop")
    lines = flags(False)
    cells.add("the companion's lines", lines, BARS["flag_lines_found"][0], lines == BARS["flag_lines_found"][0])
    cells.add("the lines as found at register", digest(_companion_lines()) == b.get("found_lines"), True,
              digest(_companion_lines()) == b.get("found_lines"))
    units = _active_units()
    cells.add("active units", units, ["privyhub-companion", "privyhub-diag"],
              units == ["privyhub-companion", "privyhub-diag"])
    before = read_json(home(code) / "files_before.json")
    if before is not None:                                   # bench ran: its before
        after = files_digest(b)
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        cells.add("every file = bench's before", len(changed), 0, not changed)
    return finish(code, "close", cells, digest({"register": b.get("register_inputs"), "before": digest(before)}))


def _active_units() -> list[str]:
    cmd = os.environ.get("PRIVYHUB_ADD_GAME_SYSTEMCTL", "systemctl").split()
    names = set()
    for scope in (["--user"], []):
        try:
            r = subprocess.run(cmd + scope + ["list-units", "privyhub-*", "--state=active", "--no-legend", "--plain"],
                               capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            continue
        for ln in r.stdout.splitlines():
            w = ln.split()
            if w and w[0].startswith("privyhub-"):
                names.add(w[0].rsplit(".", 1)[0])
    return sorted(names)


# --- the command line ---------------------------------------------------------------------------------------------------
def parse(argv: list[str]) -> tuple[str, str, dict]:
    if len(argv) < 2 or argv[0] not in STAGES or not CODE.match(argv[1]):
        raise Usage(__doc__.split("\n\n")[1])
    stage, code, rest = argv[0], argv[1], argv[2:]
    a: dict = {"check": False, "collect": [], "read": False}
    i = 0
    while i < len(rest):
        k = rest[i]
        if k in ("--check", "--read"):
            a[k[2:]] = True
            i += 1
            continue
        if k in ("--players", "--system", "--result", "--find", "--rules-players", "--setup", "--collect", "--winner") \
                and i + 1 < len(rest):
            key = k[2:].replace("-", "_")
            if key == "collect":
                a["collect"].append(rest[i + 1])
            else:
                a[key] = rest[i + 1]
            i += 2
            continue
        raise Usage(f"unknown: {k}")
    if stage == "register" or (stage == "learn" and a["check"]):
        for need in ("players", "system", "result"):
            if need not in a:
                raise Usage(f"register needs --{need}")
    if stage == "solo" and a["read"] and "winner" not in a:
        raise Usage("solo --read needs --winner <seat>")
    return stage, code, a


def main(argv: list[str]) -> int:
    try:
        stage, code, a = parse(argv)
        _private_paths()
        if stage == "register":
            return cmd_register(code, a)
        return {"learn": cmd_learn, "bench": cmd_bench, "solo": cmd_solo, "close": cmd_close}[stage](code, a)
    except Usage as exc:
        print(f"usage: {exc}", file=sys.stderr)
        return 2
    except Refused as exc:
        try:
            out(f"{argv[0] if argv else '?'}: REFUSED — {exc}")
        except Refused:
            print("REFUSED — a run-time name would be printed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
