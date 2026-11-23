#!/usr/bin/env python3
"""B157: add a party mini game by one scripted path — one command per stage, for a title known only by its code.

    python3 tools/party_add_game.py register <code> --players N --system ps1|n64|snes
                                             --result winner|places|score|letters [--word <the word>]
                                             [--max-score N]  (B198: a score title's highest final one side reaches)
                                             (--find <words> | --rules-players N) [--setup none|slot1]
                                             [--collect role=slot ...] [--check]
    python3 tools/party_add_game.py label <code> [<role>=<P1>-<P2>,<P1>-<P2> ...] [<role>=<P1>-<P2>,user]
                                             (B178: a `score` title — the session reads each end save's final score
                                             from <role>.1.png / <role>.2.png in the title's add_game folder, label/;
                                             the tool checks every reading; B191: a `letters` title —
                                             <role>=<P1>/<P2>,<P1>/<P2>, each player's corner)
    python3 tools/party_add_game.py learn <code> [--check]
    python3 tools/party_add_game.py rehearse <code> [--collect role=slot ...]   (B163: a title already in the rules
                                             folder; a role its kept folder lacks taken from the user's slot, read only)
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

B171: an ending may have up to four saves (end_P1, end_P1_2 ... end_P1_4; end_r<row>_2 ...), each one more run for the
learner (its class the role without the suffix); register asks two per ending from the start (`winner`); when learn's
separable / margin / unknown / replay cells are not met, its page says in one plain line which save to add next (or,
at four saves an ending, that the end screens cannot be told apart this way) — the same bars every time. rehearse
takes a kept extra ending the real rules end on as one more source, and keeps the saves it collects. B172: close (and
register) end the solo mark and the befores.

B178: `--result score` — a title whose final screen shows each side's number (points, a count) and the winner is the
side with more. The `label` stage puts two pictures of every end save's final screen (two ticks apart; and the crop of
each side's number once the places are known) in the title's add_game folder, label/ (off the repo); the session
reads them with its own vision and passes the numbers in; the tool checks every reading (the two readings the same,
the role's player ahead, the numbers at one place in every save, read back by a reader learnt without that save) and
names a save to read again, or, the second time, asks for the user's numbers. learn learns each side's number's place
and the title's own digits (h7_endscreen's spec version 4), reads every save with a spec learnt without it, and asks
for a save showing a digit the others do not. The sidecar `{"players": n, "result": "score"}`; the hub passes the real
numbers, the winner the side ahead, a tie a draw.

B198: `--max-score N` (score only, kept in the binding) — the highest final one side reaches at the user's settings.
learn's every-digit cell then needs only the digits a number 0..N can show (finals and line-score cells, each learnt
as today); the others are recorded "not expected", never a cell; its line names only expected digits. The spec carries
N: at the hub a final above N is unknown (`end_unread`), given up by B182's rule, never a guess. Without it: today.

B191 / B192: `--result letters --word <the word>` — a title whose match is lost by the player whose letters (one per
miss, in that player's corner) spell the word; the other player won. Two players only (four: refused, the line says
why). The label stage as the score kind's: the session reads each player's corner on two pictures of every end save;
the tool checks the two readings, each corner against the word, the role (end_Pk: the other player spelled it), the
corners at one place, a reader learnt without each save, and the last look (label/letters.png). learn learns h7_endscreen's
version-5 spec with B192's synthetic training (training only; every gate reads the real saves); the sidecar
`{"players": 2, "result": "letters"}`: the hub's winner entry.

Run-time places (each replaceable, for the tests): PRIVYHUB_H7_RULES (the rules folder), PRIVYHUB_ADD_GAME_HOME
(~/privyhub_h7/add_game), PRIVYHUB_ADD_GAME_EVIDENCE (the repo's docs/memory/evidence/add_game),
PRIVYHUB_ADD_GAME_PROJECT (the hub's project root: logs, slot indexes, the session config), PRIVYHUB_ADD_GAME_HUB
(http://127.0.0.1:8765), PRIVYHUB_ADD_GAME_DROPINS (the companion's drop-in folder), PRIVYHUB_ADD_GAME_SYSTEMCTL
(systemctl), PRIVYHUB_ADD_GAME_KEPT_ROOT (~/privyhub_h7: the kept folders that must not change), PARTY_ADD_GAME_CAPTURE
(module:function giving the pictures).
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import importlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
STAGES = ("register", "label", "learn", "rehearse", "bench", "solo", "close")
CODE = re.compile(r"^T\d\d$")
SYSTEMS = {"ps1", "n64", "snes"}                       # h7-start's systems (B103 / B123)
NOT_YET = {"ps2": "PS2: no paused load, no frame advance for a held title yet (B159)",
           "gamecube": "GameCube: no paused load confirmation, no frame advance yet (B159)"}
SAVES_PER_ENDING_MAX = 4      # B171: the most saves of one ending the tool asks for (T88's three sittings, plus one); not a bar
ROLE = re.compile(r"^(begin|other\d*|end_P[1-4](_[2-4])?|end_r[1-4]{2,4}(_[2-4])?)$")     # B171: end_P1_2 ... end_P1_4
SUFFIX = re.compile(r"_([2-4])$")
SAME_PICTURE = (1.0, "64 x 48 grey, mean |difference| of the screens that stay; H7-V1: one state run twice, 391 of 400 "
                     "frames under 1.0")          # B176: under this, two saves of one ending are one match (not a bar)
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
    "listed_within_s": (4.0, "B150's S: a switch whose next switch starts sooner is listed, not read"),
    "s_span_s": (30.0, "B150's S: from a switch to the next one's start, or 30 s"),
    "switches_read_min": (4, "B162: four planned (a practice in and out, the go, the end); B197: the planned count's bar"),
    "real_switches_read": (["the go", "the end"], "B197: the real match's two switches read for S; a practice's may be "
                                                  "listed (the user readied sooner than 4 s after it)"),
    "flag_lines_task": (20, "PP-H4: twenty lines with the two flags"),
    "flag_lines_found": (18, "the eighteen adopted lines"),
    "synthetic_held_wrong_max": (0, "B192: the training's own bar — every held-out synthetic picture read; it never "
                                    "counts toward a pass"),
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


def finish(code: str, stage: str, cells: Cells, inputs: str, write: bool = True, note: str = "",
           recorded: dict | None = None) -> int:
    v = {"schema": 1, "stage": stage, "code": code, "verdict": "PASS" if cells.passed else "FAIL", "inputs": inputs,
         "cells": cells.rows}
    if recorded is not None:                                 # B162: recorded beside the cells, never a cell
        v["recorded"] = recorded
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
                   "setup": bool(b.get("cheat")), "kept": kept, "game": hashlib.sha256(b["game"].encode()).hexdigest(),
                   **({"word": b.get("word")} if b["result"] == "letters" else {}),      # B191
                   **({"max_score": b["max_score"]} if b.get("max_score") is not None else {})})   # B198: only when given


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


def _roles_needed(players: int, result: str, per_ending: int = 2) -> list[str]:
    """B171: two saves of every ending from the start (`winner`), each from a different match; rehearse asks one for
    learn to run at all (per_ending=1). `places`: the rows that cover every place (each row another match already)."""
    if result not in ("winner", "score", "letters"):         # B178 / B191: as a winner title's
        return ["begin", "other"]
    return ["begin", "other"] + [f"end_P{k}" + ("" if n == 1 else f"_{n}") for k in range(1, players + 1)
                                 for n in range(1, per_ending + 1)]


def next_role(ending: str, have) -> str | None:
    """B171: the ending's next free role (end_P1, end_P1_2 ... end_P1_4); None at the cap."""
    for n in range(1, SAVES_PER_ENDING_MAX + 1):
        role = ending if n == 1 else f"{ending}_{n}"
        if role not in have:
            return role
    return None


def end_solo_mark(code: str) -> None:
    """B172: the solo mark and the befores end (the tool's own files in the title's add_game folder), so the next
    solo writes its own and reads only its own rows."""
    for name in ("solo_mark.json", "files_before.json", "saves_before.json"):
        (home(code) / name).unlink(missing_ok=True)


def cmd_register(code: str, a: dict) -> int:
    cells, b, inputs = _register(code, a)
    return finish(code, "register", cells, inputs, write=not a["check"])


def _register(code: str, a: dict) -> tuple[Cells, dict, str]:
    players, system, result = int(a["players"]), str(a["system"]).casefold(), str(a["result"])
    check = a["check"]
    cells = Cells()
    word = str(a.get("word") or "").upper()
    if a.get("word") and result != "letters":
        raise Usage("--word is for --result letters")
    if result == "letters" and not word:
        raise Usage("--result letters needs --word <the word>")
    max_score = a.get("max_score")                            # B198: a score title's highest final, one side
    if max_score is not None and result != "score":
        raise Usage("--max-score is for --result score")
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
    cells.add("result kind", result, ["winner", "places", "score", "letters"],
              result in ("winner", "places", "score", "letters"))
    if max_score is not None:                                # B198
        ok = bool(re.match(r"^[0-9]{1,4}$", str(max_score))) and 1 <= int(max_score) <= 9999
        cells.add("the highest score one side reaches (--max-score)", str(max_score), "a whole number 1-9999", ok)
        if ok:
            b["max_score"] = int(max_score)
    if result == "letters":                                   # B191
        b["word"] = word
        cells.add("the word", word, "2-12 letters A-Z", bool(re.match(r"^[A-Z]{2,12}$", word)))
        if not cells.add("a letters title has two players", players, 2, players == 2):
            cells.add("why not", FOUR_LETTERS, "-", False)
    if system == "ps1" and players == 4 and not b.get("described"):
        on = ps1_four_on(b["game"])
        cells.add("four-player PS1: the title's four-player setting on", on, True, on)
    old_b = read_json(binding_path(code), {}) or {}
    collected = dict(old_b.get("collected") or {})           # B187: each collected role's slot and the slot's time
    if not check and a.get("collect"):                      # the user's slots copied to the kept folder (read only)
        kf = kept_folder(code)
        kf.mkdir(parents=True, exist_ok=True)
        for item in a["collect"]:
            role, _, slot = item.partition("=")
            if not ROLE.match(role) or slot not in ("1", "2", "3"):
                raise Usage(f"--collect role=slot (roles begin, other, other2, end_P1..4, end_r<places>; slots 1-3)")
            src = _slot_file(b, int(slot))
            data = src.read_bytes()
            write_if_changed(kf / f"{role}.state", data)
            collected[role] = {"slot": int(slot), "saved": src.stat().st_mtime,       # B187: for the ask's words
                               "sha": hashlib.sha256(data).hexdigest()}
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
            rows = sorted({_role_class(k)[5:] for k in kept if k.startswith("end_r")})     # B171: end_r1234_2 is row 1234
            ok_rows = [r for r in rows if len(r) == players and sorted(r) == [str(i) for i in range(1, players + 1)]]
            cover = all({r[c] for r in ok_rows} == {str(i) for i in range(1, players + 1)} for c in range(players))
            cells.add("results rows: every place in every column", sorted(ok_rows), "each column sees 1..n",
                      bool(ok_rows) and len(ok_rows) == len(rows) and cover)
        ends = {f"end_P{i}" for i in range(1, players + 1)}                       # B171: a third / fourth save allowed
        extra = [k for k in kept if k.startswith("end_") and _role_class(k) not in ends
                 and result in ("winner", "score", "letters")]
        cells.add("no ending of another kind", extra, [], not extra)
    flag_lines = _companion_lines()
    b["found_lines"] = digest(flag_lines)
    cells.add("the companion's lines as found", len(flag_lines), BARS["flag_lines_found"][0],
              len(flag_lines) == BARS["flag_lines_found"][0] or b.get("described"))
    inputs = register_inputs(b, kept)
    b["register_inputs"] = inputs
    if collected:
        b["collected"] = {r: v for r, v in collected.items() if v.get("sha") == kept_states(code).get(r)}
    if not check:
        write_if_changed(binding_path(code), json.dumps(b, indent=1, sort_keys=True) + "\n")
        end_solo_mark(code)                                  # B172: a mark an earlier use left unclosed ends here
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
    return SUFFIX.sub("", role)                              # B171: end_P1_2 is a save of end_P1


class PicturesFailed(Exception):
    """B167: the picture source did not give a run's pictures — its reason, name-free, and where its log is."""

    def __init__(self, role: str, reason: str, words: str):
        self.role, self.reason, self.words = role, reason, words
        super().__init__(f"{reason}: {words}")

    def read(self) -> str:
        return (f"{self.role}: {self.reason}: {self.words} (RetroArch's own log: logs/{self.role}.retroarch.log in the "
                "title's add_game folder)")


def logs_folder(code: str) -> Path:
    """B167: RetroArch's own logs (they name the game): the title's add_game folder, never the repo."""
    return _env_path("PRIVYHUB_ADD_GAME_LOGS", home(code) / "logs")


def _call_capture(cap, state: Path, b: dict, run: Path, role: str, code: str):
    """The picture source for one run; any failure as PicturesFailed with the source's own reason (B167)."""
    import inspect
    kw = {}
    try:
        if "log_to" in inspect.signature(cap).parameters:
            kw["log_to"] = logs_folder(code) / f"{role}.retroarch.log"
    except (TypeError, ValueError):
        pass
    try:
        return cap(state, b, run, CAPTURE_SECONDS, CAPTURE_EVERY, **kw)
    except Exception as exc:
        reason = getattr(exc, "reason", None)
        words = getattr(exc, "words", None)
        if not reason or not words:
            reason, words = "exited", f"the picture source failed ({type(exc).__name__})"
            try:                                             # its trace beside RetroArch's log, off the repo
                import traceback
                logs_folder(code).mkdir(parents=True, exist_ok=True)
                (logs_folder(code) / f"{role}.picture_source_error.txt").write_text(traceback.format_exc())
            except OSError:
                pass
        raise PicturesFailed(role, str(reason), str(words)) from None


def _pictures(code: str, b: dict, kept: dict) -> Path:
    """Every kept state's run (made once for these kept states; again only if they change)."""
    pics = home(code) / "pictures"
    mark = pics / "made_from.json"
    made = read_json(mark)
    if made == kept:
        return pics
    made = {r: h for r, h in (made if isinstance(made, dict) else {}).items() if kept.get(r) == h}
    pics.mkdir(parents=True, exist_ok=True)
    for child in sorted(pics.iterdir()):                     # B171: a save's run kept while its state is the same
        if child.is_dir() and (child.name not in made or not (child / "index.csv").is_file()):
            shutil.rmtree(child)                             # the tool's own pictures of a save no longer kept
            made.pop(child.name, None)
    cap = None
    for role in sorted(kept):
        run = pics / role
        if role in made and run.is_dir():
            continue
        cap = cap or _capture_fn()
        run.mkdir(parents=True)
        try:
            rows = _call_capture(cap, kept_folder(code) / f"{role}.state", b, run, role, code)
        except PicturesFailed:
            shutil.rmtree(run, ignore_errors=True)           # never reused half made
            raise
        with (run / "index.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["seconds", "file"])
            for t, name in rows:
                w.writerow([f"{t:.2f}", name])
        made[role] = kept[role]
        write_if_changed(mark, json.dumps(made, sort_keys=True))
    write_if_changed(mark, json.dumps(kept, sort_keys=True))
    return pics


def _small(path: Path):
    from PIL import Image
    import numpy as np
    with Image.open(path) as im:
        return np.asarray(im.convert("L").resize((64, 48)), dtype=np.int16)


def _near(a, b) -> bool:
    """B140's measure: fewer than MOVED_SHARE of the 64x48 grey cells changed by more than MOVED_GREY."""
    return float((abs(a - b) > MOVED_GREY).mean()) < MOVED_SHARE


def _anchor(small: list) -> int:
    """The frame most of a run stays near (B140's measure; the earliest on a tie): the screen that stays (B167)."""
    near = [[_near(a, b) for b in small] for a in small]
    return max(range(len(small)), key=lambda i: (sum(near[i]), -i))


HELD_S = 3.0                                                 # B184: a final screen is the first picture held 3 s


def _anchor_held(small: list, times: list) -> int:
    """B184: a final screen's anchor — the first picture from which every picture over the next HELD_S seconds is near
    it (B140's measure) and the run reaches HELD_S past it, still near; none -> B167's `_anchor`."""
    for i in range(len(small)):
        span = [j for j in range(i, len(small)) if times[j] <= times[i] + HELD_S]
        after = [j for j in range(len(small)) if times[j] >= times[i] + HELD_S]
        if not after:
            break
        if all(_near(small[i], small[j]) for j in span) and _near(small[i], small[after[0]]):
            return i
    return _anchor(small)


def _for_reader(im, spec: dict):
    """The picture as a reader takes it: grey, as today; in colour for a version-5 spec (B191: the corners' colours)."""
    return im.convert("RGB") if spec.get("version") == 5 else im.convert("L")


def _matches(pics: Path, kept) -> tuple[dict, list]:
    """B176: each ending's saves grouped by match — two saves whose screens that stay are the same picture (under
    SAME_PICTURE) are one match. -> ({role: the first role of its match}, [[a, b, mean difference] for each such pair])."""
    import numpy as np
    shot = {}
    for role in sorted(r for r in kept if r.startswith("end_")):
        rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((pics / role / "index.csv").open())]
        if rows:
            small = [_small(pics / role / f) for _t, f in rows]
            shot[role] = small[_anchor_held(small, [t for t, _f in rows])]       # B184
    group = {r: r for r in shot}
    pairs = []
    roles = sorted(shot, key=lambda r: (_role_class(r), r != _role_class(r), r))
    for i, a in enumerate(roles):
        for b_ in roles[i + 1:]:
            if _role_class(a) != _role_class(b_):
                continue
            d = float(np.abs(shot[a] - shot[b_]).mean())
            if d < SAME_PICTURE[0]:
                pairs.append([a, b_, round(d, 2)])
                ga, gb = group[a], group[b_]
                for r in group:
                    if group[r] == gb:
                        group[r] = ga
    return group, pairs


def _labels(pics: Path, kept: dict, es, cls_of: dict | None = None) -> dict:
    """Labels from the state each picture came from — never by eye (B178: a `score` title's end saves by the numbers
    the label stage checked, `cls_of`). B167: a begin / end run's screen is the frame most
    of the run stays near (B140's measure; the earliest on a tie) — the screen that stays, whether the save was made a
    moment before it settled or the game moves on later; a frame not near it is `ignore`. Consecutive frames of one
    label are one range (the learner halves each range)."""
    runs, classes = {}, {}
    for role in sorted(kept):
        cls = (cls_of or {}).get(role) or _role_class(role)
        classes[cls] = cls
        rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((pics / role / "index.csv").open())]
        labs = [cls] * len(rows)
        if cls != "other" and rows:
            small = [_small(pics / role / f) for _t, f in rows]
            anchor = (_anchor_held(small, [t for t, _f in rows]) if role.startswith("end_")      # B184: a final
                      else _anchor(small))                                                     # screen held 3 s
            labs = [cls if _near(small[anchor], small[j]) else "ignore" for j in range(len(small))]
        spans = []
        for (t, f), lab in zip(rows, labs):
            if spans and spans[-1]["label"] == lab:
                spans[-1]["to"] = t
            else:
                spans.append({"from": t, "to": t, "label": lab})
        runs[role] = spans
    classes["ignore"] = "ignore"
    return {"classes": classes, "runs": runs}


def _spec_cells(cells: Cells, spec: dict) -> None:
    if spec.get("version") == SCORE_VERSION:                 # B178: the score kind's own cells
        _score_spec_cells(cells, spec)
        return
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
                r = reader.read(_for_reader(im, spec), now=t)
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


def _replay_all(es, spec: dict, arrays: dict, run: Path) -> list:
    """B175: a save's pictures through one Reader and Ended as learn's replays read them (the begin loaded first):
    every end it says — [(seconds from its first picture, class, places)]."""
    from PIL import Image
    rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((run / "index.csv").open())]
    now = [0.0]
    reader = es.Reader(spec, arrays, clock=lambda: now[0])
    ended = es.Ended(spec)
    ended.start_loaded()
    said = []
    for t, f in rows:
        now[0] = t
        with Image.open(run / f) as im:
            r = reader.read(_for_reader(im, spec), now=t)
        done = ended.feed(r["class"], r.get("places"))
        if done:
            said.append((round(t - rows[0][0], 2), done, list(ended.places) if ended.places else None))
    return said


def _left_out_cells(cells: Cells, es, b: dict, pics: Path, kept, labels: dict, group: dict) -> dict:
    """B175: every ending's every save — the spec learnt without its match's saves (learn's own call), then each of
    them replayed through it: met when it ends as its own ending within ended_within_s and never as another. One cell
    per save. -> {role: {"other": another ending it ended as, or None; "others": the ending's other matches}}."""
    out: dict = {}
    tmp = pics / "left_out_labels.json"
    bar = BARS["ended_within_s"][0]
    for gid in sorted(set(group.values())):
        members = sorted(r for r in group if group[r] == gid)
        cls = _role_class(gid)
        others = len({group[r] for r in group if _role_class(r) == cls and group[r] != gid})
        if b["result"] == "places":
            others = len({group[r] for r in group if group[r] != gid})
        runs = {r: v for r, v in labels["runs"].items() if r not in members}
        still = {x["label"] for v in runs.values() for x in v} | {"ignore"}      # a row with no save left: not a class
        lab = {"classes": {c: t for c, t in labels["classes"].items() if c in still}, "runs": runs}
        spec = arrays = None
        why = None
        if others == 0:
            why = "its ending's only match"
        else:
            try:
                write_if_changed(tmp, json.dumps(lab, sort_keys=True))
                spec, arrays, _rep = es.learn(pics, tmp, "first", name=b["game"])
            except ValueError as exc:                           # the learner's own refusal, said as the read
                why = f"not learnt without it: {str(exc)[:80]}"
            finally:
                tmp.unlink(missing_ok=True)
        for role in members:
            want = f"{_role_class(role)} within <= {bar} s, never another"
            if why:
                cells.add(f"left out: {role}", why, want, False)
                out[role] = {"other": None, "others": others}
                continue
            said = _replay_all(es, spec, arrays, pics / role)
            row = [int(c) for c in cls[5:]] if cls.startswith("end_r") else None
            own = [x for x in said if (x[1] == cls if row is None else x[2] == row)]
            wrong = [x for x in said if x not in own]
            first = said[0] if said else None
            ok = bool(said) and not wrong and said[0][0] <= bar
            read = None if first is None else ([first[1], first[0]] if row is None else [first[2], first[0]])
            cells.add(f"left out: {role}", read, want, ok)
            other = next((x[1] for x in wrong if row is None and x[1] not in ("start", "other")), None)
            out[role] = {"other": other, "others": others}
    return out


def _held_out_wrong(es, spec: dict, arrays: dict, pics: Path, labels: dict, kept) -> dict:
    """B176: {role: another ending} for a save whose held-out frames (second halves) the full spec reads as another
    ending (not unknown)."""
    from PIL import Image
    out = {}
    ends = set(spec.get("end_classes") or [])
    for role in sorted(r for r in kept if r.startswith("end_P")):
        cls = _role_class(role)
        lab = {"classes": labels["classes"], "runs": {role: labels["runs"][role]}}
        for c, fs in es.labelled_frames(pics, lab, "second").items():
            for f in fs:
                with Image.open(f) as im:
                    got = es.read(spec, arrays, _for_reader(im, spec))["class"]
                if got in ends and got != cls:
                    out.setdefault(role, got)
    return out


def _relabel_fixes(es, b: dict, pics: Path, labels: dict, role: str, other: str) -> bool:
    """B176: the spec learnt from every save with `role` labelled `other` instead meets learn's own bars (every class
    separable, margin_needed, held-out unknown, nothing read as another class) — the mark of a save in the wrong role."""
    lab = json.loads(json.dumps(labels))
    for x in lab["runs"][role]:
        if x["label"] != "ignore":
            x["label"] = other
    tmp = pics / "relabel_labels.json"
    try:
        write_if_changed(tmp, json.dumps(lab, sort_keys=True))
        spec, arrays, _rep = es.learn(pics, tmp, "first", name=b["game"])
        sc = es.score(pics, tmp, spec, arrays, "second")
    except ValueError:
        return False
    finally:
        tmp.unlink(missing_ok=True)
    m = spec.get("margin_needed")
    held = {c: row for c, row in (sc.get("confusion") or {}).items() if c not in ("other", "ignore")}
    n = sum(sum(row.values()) for row in held.values()) or 1
    unknown = sum(row.get("unknown", 0) + row.get("other", 0) for row in held.values())
    wrong = sum(cnt for c, row in held.items() for k, cnt in row.items() if k not in (c, "unknown", "other"))
    sep = spec.get("separable") or {}
    return (bool(sep) and all(sep.values()) and m is not None and m >= BARS["margin_needed_min"][0]
            and unknown / n <= BARS["unknown_share_max"][0] and wrong <= BARS["wrong_class_max"][0])


ASK_CELLS = ("every class separable", "margin_needed", "held-out frames read unknown (share)")
ASK_REPLAY = (": ended as itself", ": ended within", ": never ended", ": recognised within")


def one_more_save(b: dict, cells: Cells, kept, conf: dict | None = None,
                  then: str = "register <code> … --collect <role>=<slot> and learn <code> again",
                  group: dict | None = None, pairs: list | None = None, wrong: dict | None = None) -> tuple[str, dict] | None:
    """B171: when learn's separable / margin / unknown / replay cells are not met — one plain line: the ending that
    needs one more save from a different match (its next role), or, at the cap, that the end screens cannot be told
    apart this way. None when none of those cells failed. The bars are the same every time."""
    code = b["code"]
    for role, other in sorted((wrong or {}).items()):        # B176: first, a save in the wrong role — nothing asked
        line = (f"A save may be in the wrong role: {role} reads as {other}. Check which player won that match; "
                "collect it again under the right role.")
        return line, {"wrong role": [role, other], "line": line}
    for a, b_, _d in pairs or []:                            # B176: then the same match saved twice
        line = f"{a} and {b_} look like the same match saved twice: save {b_} again from another match."
        return line, {"same match twice": [a, b_], "line": line}
    asked = [r for r in cells.rows if not r["met"] and (r["cell"] in ASK_CELLS or r["cell"].endswith(ASK_REPLAY)
                                                         or r["cell"].startswith("left out: "))]
    if not asked:
        return None
    if b["result"] == "places":
        n = sum(1 for k in kept if k.startswith("end_r"))
        if n >= SAVES_PER_ENDING_MAX * b["players"]:
            return _cannot(code, ["every results row"], n)
        line = (f"One more save: a results screen from a match not saved yet; collect it as end_r<its row>, or "
                f"end_r<its row>_<n> when that row is kept already, then learn {code} again.")
        return line, {"one more save": "end_r<its row>", "line": line}
    endings = sorted({_role_class(k) for k in kept if k.startswith("end_P")})
    named: set = set()
    for r in asked:
        c = r["cell"]
        if c == "every class separable":
            named |= {x for x in (r["read"] or []) if x in endings}
        elif c == "held-out frames read unknown (share)":
            named |= {x for x, row in (conf or {}).items()
                      if x in endings and (row.get("unknown", 0) + row.get("other", 0)) > 0}
        elif c.startswith("left out: "):                    # B175: the ending of a save not read when left out
            named |= {x for x in [_role_class(c[len("left out: "):])] if x in endings}
        elif c.endswith(ASK_REPLAY):
            named |= {x for x in [_role_class(c.split(": ", 1)[0])] if x in endings}
    named = named or set(endings)                            # margin alone, or only the start: every ending
    g = group or {}
    count = {e: len({g.get(k, k) for k in kept if k.startswith("end_P") and _role_class(k) == e}) for e in named}
    open_ = sorted((count[e], e) for e in named if count[e] < SAVES_PER_ENDING_MAX)
    if not open_:
        return _cannot(code, sorted(named), SAVES_PER_ENDING_MAX)
    ending = open_[0][1]
    role = next_role(ending, kept)
    line = (f"One more save: {role} — the screen after a match player {ending[5:]} won, from a match not saved yet "
            f"(other characters or another stage than its saves kept); save it to a free slot, then "
            + then.replace("<code>", code).replace("<role>", role) + ".")
    return line, {"one more save": role, "line": line}


def _cannot(code: str, endings: list, n: int) -> tuple[str, dict]:
    line = (f"The end screens cannot be told apart this way: {', '.join(endings)} have {n} saves each from different "
            "matches and learn still does not meet its bars. Instead: another mode whose end screen shows who won by "
            "player, or save each ending on another screen that shows it, and start the title's saves again.")
    return line, {"cannot be told apart": endings, "line": line}


def _sidecar(b: dict, spec: dict) -> dict:
    side: dict = {"players": b["players"]}
    if b["result"] == "winner":
        side["result"] = "winner"                            # B158
    if b["result"] == "score":
        side["result"] = "score"                             # B178
    if b["result"] == "letters":
        side["result"] = "letters"                           # B191
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
                                     or spec.get("version") == es.VERSION_PLACES or side.get("result") == "winner"
                                     or (side.get("result") == "score" and spec.get("version") == SCORE_VERSION)
                                     or (side.get("result") == "letters" and spec.get("version") == es.VERSION_LETTERS)))
        cells.add("sidecar as the listing needs it", ok, True, ok)
        return finish(code, "learn", cells, learn_inputs(code, b), write=not a["check"])
    kept = kept_states(code)
    require(code, "register", register_inputs(b, kept))
    if b["result"] in ("score", "letters"):                  # B178 / B191: the label stage's PASS for these readings
        require(code, "label", label_inputs(code, b))
    try:
        pics = _pictures(code, b, kept)
    except PicturesFailed as exc:                            # B167: said as a cell, never a trace
        cells.add("pictures made", exc.read(), "every kept state's pictures", False)
        return finish(code, "learn", cells, learn_inputs(code, b))
    if b["result"] == "score":                               # B178: each side's number
        return _learn_score(code, b, kept, pics, es)
    if b["result"] == "letters":                             # B191: each player's letters
        return _learn_letters(code, b, kept, pics, es)
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
    conf: dict = {}
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
    group, pairs = _matches(pics, kept)                      # B176: saves that are the same picture are one match
    cells.add("no two saves of one ending the same picture", pairs,
              f">= {SAME_PICTURE[0]} grey ({SAME_PICTURE[1]})", not pairs)
    left = _left_out_cells(cells, es, b, pics, kept, labels, group)     # B175: a match the spec did not learn from
    wrong: dict = {}
    if b["result"] == "winner" and spec.get("version") != es.VERSION_PLACES:
        wrong = _held_out_wrong(es, spec, arrays, pics, labels, kept)
        full_ok = all(r["met"] for r in cells.rows if r["cell"] in ASK_CELLS)  # the spec from every save sound
        met = {r["cell"]: r["met"] for r in cells.rows}
        ends = sorted({_role_class(k) for k in kept if k.startswith("end_P")})
        for role, info in sorted(left.items()):             # B176: a left-out save not read as its own, its ending
            if wrong or full_ok or info["others"] < 2 or met.get(f"left out: {role}", True):   # two other matches,
                continue                                    # the spec from every save not sound (a mislabel spoils it)
            for other in [info["other"]] if info["other"] else [e for e in ends if e != _role_class(role)]:
                if _relabel_fixes(es, b, pics, labels, role, other):   # and only that save's other label mends it
                    wrong[role] = other
                    break
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
                return finish(code, "learn", cells, inputs)       # not an ending's save: no line
        if not (made.get("from") == digest(kept) and spec_path.is_file() and sha(spec_path) == made.get("spec")):
            es.save_spec(spec, arrays, spec_path)
        write_if_changed(begin, (kept_folder(code) / "begin.state").read_bytes())
        write_if_changed(side_path, side)
        b["learnt"] = {"from": digest(kept), "spec": sha(spec_path)}
        write_if_changed(binding_path(code), json.dumps(b, indent=1, sort_keys=True) + "\n")
        return finish(code, "learn", cells, inputs)
    ask = one_more_save(b, cells, kept, conf, group=group, pairs=pairs, wrong=wrong)   # B171 / B175 / B176: one line
    rc = finish(code, "learn", cells, inputs, note=ask[0] if ask else "", recorded=ask[1] if ask else None)
    if ask:
        out(ask[0])
    return rc


def learn_inputs(code: str, b: dict) -> str:
    if b.get("described"):
        return digest({"register": b["register_inputs"], "described": True})
    if b.get("result") in ("score", "letters"):              # B178 / B191: the readings the label stage checked
        return digest({"register": b["register_inputs"], "kept": kept_states(code), "labels": readings(code)})
    return digest({"register": b["register_inputs"], "kept": kept_states(code)})


# --- B178: label — the session reads each end save's final score; the tool checks every reading -----------------------
SCORE_VERSION = 4                                            # h7_endscreen's version-4 spec (each side's number)
SIDE = r"(?:(?:\d{1,4}|_)(?:\+(?:\d{1,4}|_))*=)?\d{1,4}"     # B181: a side's final, or its line score 9+2+2+2+_+_=15
READING = re.compile(rf"^{SIDE}(?:-{SIDE}){{1,3}}$")
LOOK = re.compile(r"^look=(all|[0-9]:\d+(?:\.\d+)*)$")      # B183: the last look's answer
LEFT_OUT_TRIES = 2                                           # a save named this often after the session read it again:
                                                             # the user is asked for its numbers (not a bar)
NO_PLACE = "*"                                               # B185: a column the reader has no place for (no other save
                                                             # fills it)
ACROSS_MARGIN = 0.05                                         # B186: a title's across-save glyph spread may be at most its
                                                             # within-save spread + this (T90: across 0.401, within 0.418,
                                                             # two digits >= 0.656; queue BI's settle) — not a bar in BARS
ASK_REASONS = ("readings", "sum")                            # B187: the only reasons a save is asked of the user


def label_path(code: str) -> Path:
    return home(code) / "label.json"


def label_folder(code: str) -> Path:
    """The pictures the session reads (off the repo, in the title's add_game folder)."""
    return home(code) / "label"


def label_record(code: str) -> dict:
    rec = read_json(label_path(code), {}) or {}
    rec.setdefault("saves", {})
    return rec


def readings(code: str) -> dict:
    """{role: [its readings]} as checked (with the state each was read from), for the stages' inputs."""
    return {r: {"sha": v.get("sha"), "readings": v.get("readings"), "by": v.get("by")}
            for r, v in sorted(label_record(code)["saves"].items())}


def label_inputs(code: str, b: dict) -> str:
    return digest({"register": b["register_inputs"], "kept": kept_states(code), "labels": readings(code)})


def _sides(text: str) -> list[tuple[list, int]]:
    """B181: a reading's sides, P1 first: (its cells left to right — int, or None for a blank — , its final)."""
    out = []
    for side in text.split("-"):
        cells, eq, fin = side.rpartition("=")
        out.append(([None if x == "_" else int(x) for x in cells.split("+")] if eq else [], int(fin)))
    return out


def _text(sides) -> str:
    return "-".join(("+".join("_" if c is None else str(int(c)) for c in cells) + "=" if cells else "") + str(int(fin))
                    for cells, fin in sides)


def _finals(text: str) -> list[int]:
    return [fin for _c, fin in _sides(text)]


def _all_numbers(text: str) -> list[int]:
    return [x for cells, fin in _sides(text) for x in [*cells, fin] if x is not None]


def _numbers(code: str, role: str) -> list[int] | None:
    v = label_record(code)["saves"].get(role)
    return _finals(v["readings"][0]) if v and v.get("readings") else None


def _score_class(text: str) -> str:
    return "end_s" + text


def _side_words(n: int, cells: bool = False) -> str:
    return "-".join((f"<P{i} cells>=" if cells else "") + f"<P{i}>" for i in range(1, n + 1))


def parse_readings(items: list[str], players: int) -> dict:
    """role=<P1>-<P2>,<P1>-<P2> (the session's two readings, from <role>.1 and <role>.2) or role=<P1>-<P2>,user; B181:
    a side's line score as its cells and its final, 9+2+2+2+_+_=15 (`_` a blank cell)."""
    got = {}
    for item in items:
        role, _, val = item.partition("=")
        parts = val.split(",")
        if not (ROLE.match(role) and role.startswith("end_P")) or len(parts) != 2:
            raise Usage(f"label <code> <role>=<P1>-<P2>,<P1>-<P2> (or ,user): {item}")
        if not READING.match(parts[0]) or not (parts[1] == "user" or READING.match(parts[1])):
            raise Usage(f"a reading is each side's numbers, P1 first, joined by '-' (a line score: cells joined by "
                        f"'+', '_' for a blank, '=' the final): {item}")
        rd = [_text(_sides(parts[0]))] + ([] if parts[1] == "user" else [_text(_sides(parts[1]))])
        if any(len(_sides(x)) != players for x in rd):
            raise Usage(f"a reading names {players} sides: {item}")
        got[role] = {"readings": rd, "by": "user" if parts[1] == "user" else "session"}
    return got


def _two_pictures(pics: Path, role: str) -> list[str]:
    """The screen that stays (learn's own anchor; B184: a final screen's, the first held still 3 s) and the picture
    two ticks later still on it (else the nearest one on it two ticks away, else the next)."""
    rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((pics / role / "index.csv").open())]
    if not rows:
        return []
    small = [_small(pics / role / f) for _t, f in rows]
    i = _anchor_held(small, [t for t, _f in rows])
    near = [j for j in range(len(rows)) if _near(small[i], small[j])]
    later = [j for j in near if j >= i + 2] or [j for j in near if abs(j - i) >= 2] or [j for j in near if j != i] or [i]
    return [rows[i][1], rows[later[0]][1]]


def _crops(es, pics: Path, role: str, first: str, places: list, out: Path) -> list[str]:
    """Each side's number, cut from the picture at its learnt place, four times larger."""
    from PIL import Image
    with Image.open(pics / role / first) as im:
        a = es.score_picture(im)
    made = []
    for k, pl in enumerate(places, 1):
        h = pl["bot"] - pl["top"] + 1
        pad = h
        box = (max(0, pl["x0"] - pad), max(0, pl["top"] - h // 2), min(a.shape[1], pl["x1"] + pad + 1),
               min(a.shape[0], pl["bot"] + h // 2 + 1))
        crop = Image.fromarray(a.astype("uint8")).crop(box)
        crop.resize((crop.width * 4, crop.height * 4), Image.BICUBIC).save(out / f"{role}.P{k}.png")
        made.append(f"{role}.P{k}.png")
    return made


def _replay_scores(es, spec: dict, arrays: dict, run: Path) -> list:
    """B178: a save's pictures through one Reader and Ended (the begin loaded first): its end —
    [(seconds from its first picture, class, the numbers, the picture it ended on)]."""
    from PIL import Image
    rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((run / "index.csv").open())]
    now = [0.0]
    reader = es.Reader(spec, arrays, clock=lambda: now[0])
    ended = es.Ended(spec)
    ended.start_loaded()
    said = []
    for t, f in rows:
        now[0] = t
        with Image.open(run / f) as im:
            r = reader.read(_for_reader(im, spec), now=t)
        done = ended.feed(r["class"], r.get("scores"))
        if done:
            said.append((round(t - rows[0][0], 2), done, list(ended.scores) if ended.scores is not None else None, f))
            break
    return said


def _read_all(es, spec: dict, arrays: dict, run: Path, want: str, direct: bool = False) -> tuple[list, list | None]:
    """B181: the save's end through the spec (its finals, as the hub reads them) and, on the picture it ended on, every
    learnt line-score column -> (said, [(cells read — int, "_" blank, text with "?" not read, B185's "*" a column with
    no place: no save the spec was learnt from fills it — , final) per side]). B186: a replay that never ends (a final
    holding a digit the spec has no template for) reads its finals and columns at their places on the save's first
    labelled picture instead (a final read in part is text with "?"); `said` stays empty (`direct`: learn's
    left-out cell and the label stage's read-back)."""
    from PIL import Image
    said = _replay_scores(es, spec, arrays, run)
    if said:
        finals, f = said[0][2], said[0][3]
    elif not direct:
        return said, None
    else:
        two = _two_pictures(run.parent, run.name)
        if not two or not (spec.get("score") or {}).get("places"):
            return said, None
        f = two[0]
        with Image.open(run / f) as im:
            rd = es.read_scores(es.score_picture(im), spec["score"], arrays["digit_refs"])["read"]
        finals = [("_" if not x else int(x) if "?" not in x else x) for x in rd]
    sides = _sides(want)
    cols = None
    if any(cells for cells, _fin in sides):
        with Image.open(run / f) as im:
            cols = es.read_columns(es.score_picture(im), spec["score"], arrays["digit_refs"])
    got = []
    for k, (cells, _fin) in enumerate(sides):
        colk = (cols[k] if cols and k < len(cols) else []) if cells else []
        got.append(([("_" if cells[c] is None else NO_PLACE) if c >= len(colk) or colk[c] is None
                     else "_" if colk[c] == "_" else colk[c] for c in range(len(cells))],
                    finals[k] if k < len(finals) else "_"))
    return said, got


def _got_text(got) -> str:
    return "-".join(("+".join(str(c) for c in cells) + "=" if cells else "") + str(fin) for cells, fin in got)


def _judge(want: str, got, only=()) -> tuple[str, dict]:
    """B185 / B186: a save's reading against what a reader read -> (how, shown only here). how: 'same' (every number
    as labelled, but for what is shown only here), 'contradicted' (a number read as another, a blank read as a number,
    a number read as blank), or 'unread' (a glyph not read whose digit is not in `only`). Shown only here:
    {"digits": the digits of `only` not read, "columns": "P<k> column <c>" for a filled cell in a column the reader
    has no place for (no other save fills it — never a misread)}."""
    if got is None:
        return "unread", {}
    diff = unread = False
    digs, cols = set(), []
    for k, ((wc, wf), (gc, gf)) in enumerate(zip(_sides(want), got)):
        for c, (w, g) in enumerate([*zip(wc, gc), (wf, gf)]):
            if g == NO_PLACE:
                if w is not None:
                    cols.append(f"P{k + 1} column {c + 1}")
            elif g == "_":
                diff |= w is not None
            elif isinstance(g, str):
                if w is None or len(g) != len(str(w)):
                    diff = True
                    continue
                for gch, wch in zip(g, str(w)):
                    if gch == "?":
                        if wch in only:
                            digs.add(wch)
                        else:
                            unread = True
                    elif gch != wch:
                        diff = True
            else:
                diff |= w is None or int(g) != int(w)
    here = {k: v for k, v in (("digits", sorted(digs)), ("columns", cols)) if v}
    return ("contradicted" if diff else "unread" if unread else "same"), here


def _fill(want: str, got, mine) -> list | None:
    """B186: a glyph not read whose digit is learnt from this save alone (`mine`, each of its glyphs read back by its
    own other glyphs) is that digit."""
    if got is None or not mine:
        return got
    out = []
    for (wc, wf), (gc, gf) in zip(_sides(want), got):
        row = []
        for w, g in [*zip(wc, gc), (wf, gf)]:
            if isinstance(g, str) and "?" in g and w is not None and len(g) == len(str(w)):
                t = "".join(wch if gch == "?" and wch in mine else gch for gch, wch in zip(g, str(w)))
                g = int(t) if "?" not in t else t
            row.append(g)
        out.append((row[:-1], row[-1]))
    return out


def _digits_of(text: str) -> set:
    return {c for x in _all_numbers(text) for c in str(int(x))}


def _only_here(role: str, members, texts: dict) -> list[str]:
    """The digits this save's numbers show that no other end save's (outside its match) do."""
    others = set().union(*[_digits_of(v) for r, v in texts.items() if r not in members] or [set()])
    return sorted(_digits_of(texts[role]) - others)


def _learn_without(es, b: dict, pics: Path, labels: dict, members) -> tuple:
    """The spec learnt without these saves (learn's own call). -> (spec, arrays, why not or None)."""
    runs = {r: v for r, v in labels["runs"].items() if r not in members}
    still = {x["label"] for v in runs.values() for x in v} | {"ignore"}
    lab = {"classes": {c: t for c, t in labels["classes"].items() if c in still}, "runs": runs}
    tmp = pics / "left_out_labels.json"
    try:
        write_if_changed(tmp, json.dumps(lab, sort_keys=True))
        spec, arrays, _rep = es.learn(pics, tmp, "first", name=b["game"])
    except ValueError as exc:
        return None, None, f"not learnt without it: {str(exc)[:80]}"
    finally:
        tmp.unlink(missing_ok=True)
    if not spec.get("usable") or not (spec.get("score") or {}).get("found"):
        return spec, arrays, "not learnt without it: the score places or the digits not found"
    return spec, arrays, None


def _one_save_digits(es, spec: dict, pics: Path, labels: dict, texts: dict) -> dict:
    """B186: for every digit only one end save shows, whether it is learnt from that save alone: the save shows it at
    least twice, each glyph read back as it by templates learnt from the other saves' glyphs and the save's own other
    glyphs of that digit (never the glyph under test, by its place, in any picture), and the title's across-save
    spread within its within-save spread + ACROSS_MARGIN. -> {"digits": {d: {"save", "glyphs", "read back",
    "learnt"}}, "spread": {"across", "within", "bar", "met"}}."""
    sc = spec.get("score") or {}
    if not sc.get("found"):
        return {"digits": {}, "spread": None}
    frames = es.labelled_frames(pics, labels, "first")
    paths: dict = {}
    for c, ps in frames.items():
        for p_ in ps:
            if p_.parent.name in texts:
                paths.setdefault(p_.parent.name, []).append(p_)
    glyphs = {}
    for role, ps in paths.items():
        sides = _sides(texts[role])
        glyphs[role] = es.save_glyphs(sc, [fin for _c, fin in sides], [cl for cl, _f in sides], sorted(ps))
    across, within, na, nw = es.spread_across_within(
        {r: [(g[3], g[4]) for g in gs if g[0] == 0] for r, gs in glyphs.items()})
    met = across is not None and within is not None and across <= within + ACROSS_MARGIN
    spread = {"across": across, "within": within, "pairs": [na, nw],
              "bar": f"across <= within + {ACROSS_MARGIN}", "met": met}
    shows = {d: [r for r, t in texts.items() if d in _digits_of(t)] for d in "0123456789"}
    out = {}
    for d in "0123456789":
        if len(shows[d]) != 1 or shows[d][0] not in glyphs:
            continue
        role = shows[d][0]
        mine = [g for g in glyphs[role] if g[3][-1] == d]
        tests = [g for g in mine if g[0] == 0]
        others: dict = {}
        seen: dict = {}
        for r, gs in glyphs.items():
            if r == role:
                continue
            for g in gs:
                others.setdefault(g[3], []).append(g[4])
            for key in {g[3] for g in gs}:
                seen[key] = seen.get(key, 0) + 1
        back = 0
        for t in tests:
            own = [g[4] for g in mine if g[3] == t[3] and (g[1], g[2]) != (t[1], t[2])]
            back += es.read_glyph_with(others, seen, t[3], own, t[4]) == d
        out[d] = {"save": role, "glyphs": len(tests), "read back": back,
                  "learnt": len(tests) >= 2 and back == len(tests) and met}
    return {"digits": out, "spread": spread}


def _read_back(es, b: dict, pics: Path, labels: dict, role: str, want: str):
    """Every number a reader learnt without this save reads on its pictures (`_read_all`), or None."""
    spec, arrays, why = _learn_without(es, b, pics, labels, [role])
    if spec is None or why:
        return None
    return _read_all(es, spec, arrays, pics / role, want, direct=True)[1]


def _mend(w, g):
    """What the other saves' reader read, its unread glyphs ("?") and its columns with no place ("*") as labelled."""
    if g == "_":
        return None
    if g == NO_PLACE or not isinstance(g, str):
        return w if g == NO_PLACE else g
    if w is None or len(g) != len(str(w)):
        return w
    return int("".join(wch if gch == "?" else gch for gch, wch in zip(g, str(w))))


def _culprit(es, b: dict, pics: Path, kept: dict, ends: list, texts: dict, contradicted: dict) -> str | None:
    """The one contradicted save whose reading, replaced by what the others' reader read, lets every other contradicted
    save read back as labelled; None when no single one does."""
    for x in sorted(contradicted):
        got = contradicted[x]
        mended = [([_mend(w, g) for w, g in zip(wc, gc)], _mend(wf, gf))
                  for (wc, wf), (gc, gf) in zip(_sides(texts[x]), got)]
        t2 = {**texts, x: _text(mended)}
        labels2 = _labels(pics, kept, es, {r: _score_class(t2[r]) for r in ends})
        if all(_judge(t2[y], _read_back(es, b, pics, labels2, y, t2[y]), _only_here(y, [y], t2))[0] == "same"
               for y in sorted(contradicted) if y != x):
            return x
    return None


def _sheet(es, spec: dict, pics: Path, ends: list, texts: dict, folder: Path) -> dict:
    """B183: every glyph of every labelled number (one picture of each save), grouped by the digit it was read as, in
    one picture (label/digits.png): a row per digit, its tiles numbered 1… -> {digit: [the save of each tile]}."""
    from PIL import Image, ImageDraw, ImageFont
    sc = spec["score"]
    tiles: dict = {}
    for role in ends:
        with Image.open(pics / role / _two_pictures(pics, role)[0]) as im:
            a = es.score_picture(im)
        sides = _sides(texts[role])
        spots = [(pl, sides[k][1]) for k, pl in enumerate(sc["places"])]
        for k, cols in enumerate(sc.get("columns") or []):
            for c, pl in enumerate(cols):
                if pl is not None and c < len(sides[k][0]) and sides[k][0][c] is not None:
                    spots.append((pl, sides[k][0][c]))
        for pl, v in spots:
            gl = es.place_glyphs(a, pl)
            if not gl or len(gl) != len(str(v)):
                continue
            for ch, g in zip(str(v), gl):
                crop = a[max(0, pl["top"] - 2):pl["bot"] + 3, max(0, g[1] - 2):g[3] + 3]
                tiles.setdefault(ch, []).append((role, crop))
    if not tiles:
        return {}
    s_ = max(2, 48 // max(c.shape[0] for v in tiles.values() for _r, c in v))
    th = max(c.shape[0] for v in tiles.values() for _r, c in v) * s_
    tw = max(c.shape[1] for v in tiles.values() for _r, c in v) * s_
    font = ImageFont.load_default(size=22)
    small = ImageFont.load_default(size=14)
    width = 60 + max(len(v) for v in tiles.values()) * (tw + 10)
    sheet = Image.new("L", (width, len(tiles) * (th + 30) + 10), 255)
    d = ImageDraw.Draw(sheet)
    for i, dg in enumerate(sorted(tiles)):
        y = 6 + i * (th + 30)
        d.text((10, y + th // 2 - 12), dg, fill=0, font=font)
        for j, (_r, crop) in enumerate(tiles[dg]):
            x = 60 + j * (tw + 10)
            sheet.paste(Image.fromarray(crop.astype("uint8")).resize((crop.shape[1] * s_, crop.shape[0] * s_),
                                                                     Image.NEAREST), (x, y))
            d.text((x, y + th + 4), str(j + 1), fill=0, font=small)
    sheet.save(folder / "digits.png")
    return {dg: [r for r, _c in v] for dg, v in sorted(tiles.items())}


def ask_folder() -> Path:
    """B187: where the one picture in doubt is put for Cowork to show the user — this repo's logs/ (git-ignored)."""
    return _env_path("PRIVYHUB_ADD_GAME_ASK", project() / "logs" / "add_game_ask")


def _column_words(c: int, n: int) -> str:
    return (["Q1", "Q2", "Q3", "Q4", "OT1", "OT2"][c] if n == 6 else f"cell {c + 1}")


def _when_saved(code: str, b: dict, role: str) -> str:
    """B187: when and where the save was made — register --collect's slot and the slot file's time (the hub's clock),
    else when the tool kept it."""
    import time as _t
    got = (b.get("collected") or {}).get(role) or {}
    kept = kept_folder(code) / f"{role}.state"
    if got.get("sha") == (sha(kept) if kept.is_file() else None) and got.get("saved"):
        at = _t.strftime("%I:%M %p", _t.localtime(float(got["saved"]))).lstrip("0").lower()
        return f"saved at {at} to slot {got['slot']}"
    at = _t.strftime("%I:%M %p", _t.localtime(kept.stat().st_mtime)).lstrip("0").lower() if kept.is_file() else "?"
    return f"kept at {at} (its slot not recorded)"


def _ask_line(code: str, b: dict, rec: dict, role: str, why: str, texts: dict, folder: Path) -> tuple[str, str]:
    """B187: the ask to the user — the save by its match, the cells in doubt in the line score's own form, the one
    picture in doubt copied for Cowork to show. -> (the line printed, the line written down: the final left out)."""
    rd = rec["saves"][role]["readings"]
    k = int(role[5])
    one, two = _sides(rd[0]), _sides(rd[-1])
    fin1 = "-".join(str(f_) for _c, f_ in one)
    fin2 = "-".join(str(f_) for _c, f_ in two)
    final = fin1 + (f" (or {fin2})" if fin2 != fin1 else "")
    blank_elsewhere = {(j, c) for r, t in texts.items() if r != role
                       for j, (cl, _f) in enumerate(_sides(t)) for c, x in enumerate(cl) if x is None}
    overtime = any(x is not None and (j, c) in blank_elsewhere for j, (cl, _f) in enumerate(one)
                   for c, x in enumerate(cl))
    match = f"the match player {k} won {{final}}{' in overtime' if overtime else ''}, {_when_saved(code, b, role)}"
    doubt = []
    for j, ((c1, f1), (c2, f2)) in enumerate(zip(one, two)):
        bad_sum = why == "sum" and c1 and sum(x for x in c1 if x is not None) != f1
        cols = [c for c in range(len(c1)) if why == "readings" and (c >= len(c2) or c1[c] != c2[c])]
        cols = list(range(len(c1))) if bad_sum else cols
        fin = bad_sum or (why == "readings" and f1 != f2)
        if cols or fin:
            doubt.append(f"player {j + 1}'s " + ", ".join([_column_words(c, len(c1)) for c in cols]
                                                          + (["final"] if fin else [])))
    cells_words = "; ".join(doubt) or "every number"
    pic = ask_folder() / f"{code}_{role}.png"
    pic.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(folder / f"{role}.1.png", pic)
    form = _side_words(b["players"], any(cl for cl, _f in one))
    tail = (f": {cells_words}, as its final stats screen shows them. YOU, now: ask Cowork to show you the picture "
            f"of that match; then reply with its scores. Then label {code} {role}={form},user — the whole line "
            f"score, the user's numbers in those cells (the picture: logs/add_game_ask/{code}_{role}.png, "
            f"git-ignored).")
    return ("Ask the user about " + match.format(final=final) + tail,
            "Ask the user about " + match.format(final="<its final as read: run time only>") + tail)


def cmd_label(code: str, a: dict) -> int:
    b = load_binding(code)
    if b.get("result") == "letters":                         # B191
        return _label_letters(code, b, a)
    if b.get("result") != "score":
        raise Refused("label is for a title registered with --result score or letters")
    kept = kept_states(code)
    require(code, "register", register_inputs(b, kept))
    _private_paths()
    es = _endscreen()
    rec = label_record(code)
    ends = sorted(r for r in kept if r.startswith("end_P"))
    items = a.get("readings") or []
    looks = [x for x in items if x.startswith("look=")]
    for x in looks:
        if not LOOK.match(x):
            raise Usage(f"the last look: look=all, or look=<digit>:<tile numbers joined by '.'>: {x}")
    given = parse_readings([x for x in items if not x.startswith("look=")], b["players"])
    for role in given:
        if role not in kept:
            raise Usage(f"{role} is not a kept end save")
    lined_now = any(_sides(v["readings"][0])[0][0] for r, v in rec["saves"].items() if v.get("readings")
                    and kept.get(r) == v.get("sha") and r not in given) or any(
        _sides(v["readings"][0])[0][0] for v in given.values())
    for role, v in given.items():                            # B187: a line-score title's answer is a line score
        if v["by"] == "user" and lined_now and not all(cl for cl, _f in _sides(v["readings"][0])):
            raise Usage(f"the user's answer is the line score's own form — every side's cells, then '=' and its "
                        f"final ({_side_words(b['players'], True)}): {role}")
    for role in list(rec["saves"]):                          # a save changed or gone: its readings and counts end
        if rec["saves"][role].get("sha") != kept.get(role):
            del rec["saves"][role]
    for role, v in given.items():
        old = rec["saves"].get(role) or {}
        rec["saves"][role] = {"sha": kept[role], "readings": v["readings"], "by": v["by"],
                              "named": old.get("named", 0), "again": bool(old.get("named")),
                              "named_for": dict(old.get("named_for") or {})}
    cells = Cells()
    try:
        pics = _pictures(code, b, kept)
    except PicturesFailed as exc:
        cells.add("pictures made", exc.read(), "every kept state's pictures", False)
        return finish(code, "label", cells, label_inputs(code, b))
    folder = label_folder(code)                              # the pictures the session reads (off the repo)
    folder.mkdir(parents=True, exist_ok=True)
    shown = {}
    for role in ends:
        two = _two_pictures(pics, role)
        for i, f in enumerate(two, 1):
            from PIL import Image
            with Image.open(pics / role / f) as im:
                im.convert("RGB").save(folder / f"{role}.{i}.png")
        shown[role] = two
        if rec.get("places"):
            _crops(es, pics, role, two[0], rec["places"], folder)
    missing = [r for r in ends if r not in rec["saves"]]
    cells.add("every end save read", missing, [], not missing)
    named: dict = {}
    reason: dict = {}                                        # B187: why each save was named (ASK_REASONS asked)

    def name(role_: str, words_: str, why_: str) -> None:
        if role_ not in named:
            named[role_], reason[role_] = words_, why_
    n = b["players"]
    for role in ends:
        v = rec["saves"].get(role)
        if not v:
            continue
        rd = v["readings"]
        same = v["by"] == "user" or (len(rd) == 2 and rd[0] == rd[1])
        if not cells.add(f"{role}: the two readings the same", rd, "the same numbers from both pictures", same):
            name(role, "its two readings differ", "readings")
        k = int(role[5])
        nums = _finals(rd[0])
        ahead = all(nums[k - 1] > x for j, x in enumerate(nums) if j != k - 1)
        if not cells.add(f"{role}: the role's player ahead", nums, f"P{k} more than every other side", ahead):
            name(role, f"P{k} is not ahead in it", "ahead")
        sums = [(k_ + 1, sum(x for x in cl if x is not None), fin) for k_, (cl, fin) in enumerate(_sides(rd[0])) if cl]
        if sums:                                             # B181: each side's cells add up to its final
            bad = [x for x in sums if x[1] != x[2]]
            if not cells.add(f"{role}: the cells add up to the finals", [[s_, f_] for _k, s_, f_ in sums],
                             "each side's cells = its final", not bad):
                name(role, f"P{bad[0][0]}'s cells add up to {bad[0][1]}, not its final {bad[0][2]}", "sum")
    texts = {r: rec["saves"][r]["readings"][0] for r in ends if r in rec["saves"]}
    recorded: dict = {"pictures": {r: [f"{r}.1.png", f"{r}.2.png"] for r in ends}}
    look_for = digest({r: texts.get(r) for r in ends})
    if not missing:
        labels = _labels(pics, kept, es, {r: _score_class(texts[r]) for r in ends})
        spec, arrays, why = _learn_without(es, b, pics, labels, [])
        found = bool(spec) and bool((spec.get("score") or {}).get("found"))
        broken = (spec or {}).get("score", {}).get("not_found") or {}
        cells.add("the numbers at one place in every save", "found" if found else broken, "found", found)
        for where, saves in sorted(broken.items()):
            side, _, col = where.partition(".")
            what = (f"P{side}'s number" if not col else f"P{side}'s number of cells" if col == "cells"
                    else f"P{side}'s cell {col}")
            for role in saves:
                name(role, f"{what} does not fit where the other saves have it", "place")
        if found:
            rec["places"] = spec["score"]["places"]
            for role in ends:
                _crops(es, pics, role, shown[role][0], rec["places"], folder)
            contradicted, unread = {}, []
            for role in ends:                                # 4: read back by a reader learnt without it
                got = _read_back(es, b, pics, labels, role, texts[role])
                only = _only_here(role, [role], texts)
                how, here = _judge(texts[role], got, only)   # B185: a column no other save fills, shown only here
                if got is None and only:
                    how, here = "same", {"digits": only}
                cell = f"{role}: read back by a reader learnt without it"
                words_ = ("not read" if got is None else _got_text(got)) + (
                    " (shown only here: " + "; ".join(", ".join(v) for v in here.values()) + ")" if here else "")
                bar_ = f"{texts[role]}, but for a digit or a column no other save shows"
                if here:
                    recorded.setdefault("shown only here", {})[role] = here
                if how == "same":
                    cells.add(cell, words_, bar_, True)
                elif how == "contradicted":
                    cells.add(cell, words_, bar_, False)
                    contradicted[role] = got
                else:
                    cells.add(cell, words_, bar_, False)
                    unread.append(role)
            # one misread label spoils the other saves' readers too: name the save whose own reading, put right,
            # clears the rest; a save not read is named only when nothing else is
            culprit = _culprit(es, b, pics, kept, ends, texts, contradicted) if len(contradicted) > 1 else None
            for role, got in sorted(contradicted.items()):
                if culprit is None or role == culprit:
                    name(role, "a reader learnt from the other saves reads it as " + _got_text(got), "read back")
            if not named:
                for role in unread:
                    name(role, "a reader learnt from the other saves does not read it", "read back")
            # B183: the last look — every glyph by the digit it was read as, one picture; the session's answer
            rows = _sheet(es, spec, pics, ends, texts, folder)
            if looks and rec.get("tiles", {}).get("for") == look_for:
                bad: dict = {}
                for x in looks:
                    ans = x[len("look="):]
                    if ans == "all":
                        continue
                    dg, _, idx = ans.partition(":")
                    for i in idx.split("."):
                        if dg not in rows or not 1 <= int(i) <= len(rows[dg]):
                            raise Usage(f"no tile {i} in the row of {dg} at the last look")
                        bad.setdefault(dg, []).append(int(i))
                rec["look"] = {"for": look_for, "bad": {d_: sorted(set(v)) for d_, v in bad.items()}}
            rec["tiles"] = {"for": look_for, "rows": rows}
            look = rec.get("look") if (rec.get("look") or {}).get("for") == look_for else None
            if look is None:
                cells.add("the last look: every glyph is the digit it was read as", "not given (label/digits.png)",
                          "look=all", False)
            else:
                cells.add("the last look: every glyph is the digit it was read as", look["bad"] or "all", "all",
                          not look["bad"])
                for dg, idx in sorted(look["bad"].items()):
                    for i in idx:
                        name(rows[dg][i - 1], f"a glyph read as {dg} is not one, at the last look", "look")
            recorded["sheet"] = {d_: len(v) for d_, v in rows.items()}
    line = line_rec = ""
    for role in ends:                                        # how often each save was named after a reading again
        v = rec["saves"].get(role)
        if v is not None and role in named and role in given:
            v["named"] = v.get("named", 0) + 1
            v.setdefault("named_for", {})[reason[role]] = v.get("named_for", {}).get(reason[role], 0) + 1
        if v is not None:
            v.pop("again", None)
    if named and (rec.get("look") or {}).get("bad"):
        rec.pop("look", None)                                # the saves read again: a new look after
    write_if_changed(label_path(code), json.dumps(rec, indent=1, sort_keys=True) + "\n")
    lined = any(_sides(t)[0][0] for t in texts.values())
    words = _side_words(n, lined)
    if missing:
        line = (f"Read the final score on each end save's two pictures in the title's add_game folder, label/ "
                f"(<role>.1.png and <role>.2.png), each side's number, P1 first — with a line score, each side's cells "
                f"left to right joined by '+' ('_' for a blank cell) then '=' and its final; then label {code} "
                + " ".join(f"{r}={words},{words}" for r in missing) + " (the first reading from .1, the second from .2).")
        recorded["read"] = missing
    elif named:
        user = [r for r in sorted(named) if rec["saves"][r]["by"] == "user"]
        cnt = {r: (rec["saves"][r].get("named_for") or {}).get(reason[r], 0) for r in named}
        twice = [r for r in sorted(named) if reason[r] in ASK_REASONS and cnt[r] >= LEFT_OUT_TRIES and r not in user]
        stuck = [r for r in sorted(named) if reason[r] not in ASK_REASONS and cnt[r] >= LEFT_OUT_TRIES
                 and r not in user]
        if user:
            r = user[0]
            line = (f"{r} cannot be read as the user says ({named[r]}): collect it again from another match "
                    f"P{r[5]} won, then register {code} … --collect {r}=<slot>, label {code} and learn {code} again.")
            recorded["collect again"] = r
        elif twice:                                          # B187: the ask, plain, with the picture
            r = twice[0]
            line, line_rec = _ask_line(code, b, rec, r, reason[r], texts, folder)
            recorded["ask the user"] = {"save": r, "why": reason[r], "picture": f"logs/add_game_ask/{code}_{r}.png"}
        elif stuck:                                          # B187: never the user, never a new match
            r = stuck[0]
            line = (f"Stop: {r} ({named[r]}) after it was read again twice. Do not ask the user and do not ask for "
                    f"another match: take this line back to the chat (Cowork).")
            recorded["back to the chat"] = r
        else:
            crops = bool(rec.get("places"))
            line = ("Read again: " + "; ".join(f"{r} ({named[r]})" for r in sorted(named)) + ". Their pictures in "
                    "label/ (<role>.1.png, <role>.2.png" + (", and each side's number cut out: <role>.P1.png, <role>.P2.png" if crops
                                                    else "") + f"); then label {code} "
                    + " ".join(f"{r}={words},{words}" for r in sorted(named)) + ".")
            recorded["read again"] = sorted(named)
    elif not cells.passed and any(r["cell"].startswith("the last look") and not r["met"] for r in cells.rows):
        line = (f"Look at label/digits.png: a row for each digit, every glyph read as that digit, numbered under it. "
                f"If every glyph in every row is its row's digit: label {code} look=all. Else name the ones that are "
                f"not: label {code} look=<digit>:<numbers joined by '.'> (one look= for each such row).")
        recorded["look"] = "asked"
    line_rec = line_rec or line                              # B187: the final as read is never written down
    if line:
        recorded["line"] = line_rec
    rc = finish(code, "label", cells, label_inputs(code, b), note=line_rec, recorded=recorded)
    if line:
        out(line)
    return rc


# --- B178: learn for a `score` title ------------------------------------------------------------------------------------
def expected_digits(b: dict) -> list[str]:
    """B198: the digits a number 0..N can show (N the binding's `max_score`); without it every digit 0-9 (today)."""
    n = b.get("max_score")
    if n is None:
        return list("0123456789")
    return sorted({c for k in range(int(n) + 1) for c in str(k)})


def _every_digit_cell(b: dict) -> str:
    """learn's every-digit cell: today's name without `--max-score`; B198's with it."""
    if b.get("max_score") is None:
        return "every digit 0-9 read by a reader learnt without each save that shows it"
    return (f"every digit that can occur up to {int(b['max_score'])} ({', '.join(expected_digits(b))}) read by a reader "
            "learnt without each save that shows it")


def _score_spec_cells(cells: Cells, spec: dict) -> None:
    sc = spec.get("score") or {}
    cells.add("spec usable", bool(spec.get("usable")), True, bool(spec.get("usable")))
    cells.add("the score places found", "found" if sc.get("found") else sc.get("not_found"), "found", bool(sc.get("found")))
    bad = sorted(k for k, v in (sc.get("separable") or {}).items() if not v)
    cells.add("every digit separable", bad, [], bool(sc.get("keys")) and not bad)
    m = sc.get("margin_needed")
    cells.add("digit margin_needed", m, f">= {BARS['margin_needed_min'][0]} ({BARS['margin_needed_min'][1]})",
              m is not None and float(m) >= BARS["margin_needed_min"][0])


def _learn_score(code: str, b: dict, kept: dict, pics: Path, es) -> int:
    cells = Cells()
    ends = sorted(r for r in kept if r.startswith("end_P"))
    texts = {r: label_record(code)["saves"][r]["readings"][0] for r in ends}
    nums_of = {r: _finals(t) for r, t in texts.items()}
    labels = _labels(pics, kept, es, {r: _score_class(t) for r, t in texts.items()})
    write_if_changed(pics / "labels.json", json.dumps(labels, sort_keys=True))
    r = rules_folder()
    spec_path = r / f"{b['game']}.endscreen.json"
    made = b.get("learnt") or {}
    key = digest({"kept": kept, "labels": readings(code),
                  **({"max_score": b["max_score"]} if b.get("max_score") is not None else {})})   # B198: only when given
    if made.get("from") == key and spec_path.is_file() and sha(spec_path) == made.get("spec"):
        spec, arrays = es.load_spec(spec_path)
    else:
        spec, arrays, _rep = es.learn(pics, pics / "labels.json", "first", name=b["game"])
        if b.get("max_score") is not None and isinstance(spec.get("score"), dict):
            spec["score"]["max_score"] = int(b["max_score"])  # B198: the hub gives up a final above it
    _score_spec_cells(cells, spec)
    sc = es.score_scores(pics, pics / "labels.json", spec, arrays, "second")
    held = {c: row for c, row in sc["rows"].items() if c != "other"}
    wrong = sum(row["wrong"] for row in held.values())
    unknown = sum(row["unknown"] + row["other"] for row in held.values())
    n = sum(row["n"] for row in held.values()) or 1
    cells.add("held-out frames read as another class", wrong, BARS["wrong_class_max"][0], wrong <= BARS["wrong_class_max"][0])
    cells.add("held-out frames read unknown (share)", round(unknown / n, 4), f"<= {BARS['unknown_share_max'][0]}",
              unknown / n <= BARS["unknown_share_max"][0])
    cells.add("other read as a screen", sc.get("other_read_as_screen"), BARS["other_as_screen_max"][0],
              (sc.get("other_read_as_screen") or 0) <= BARS["other_as_screen_max"][0])
    in_time: dict = {}                                       # B186: the full reader's own end, per end save
    for role in sorted(kept):                                # the replays (the begin, other, every end save)
        cls = _role_class(role)
        said = _replay_scores(es, spec, arrays, pics / role) if cls not in ("start",) else []
        if cls == "start":
            from PIL import Image
            rows = [(float(x["seconds"]), x["file"]) for x in csv.DictReader((pics / role / "index.csv").open())]
            now = [0.0]
            reader, ended = es.Reader(spec, arrays, clock=lambda: now[0]), es.Ended(spec)
            got, first = None, None
            for t, f in rows:
                now[0] = t
                with Image.open(pics / role / f) as im:
                    rd = reader.read(_for_reader(im, spec), now=t)
                first = t if rd["class"] == "start" and first is None else first
                if ended.feed(rd["class"], rd.get("scores")) and got is None:
                    got = t
            cells.add(f"{role}: never ended", got is None, True, got is None)
            cells.add(f"{role}: recognised within", first, f"<= {BARS['start_within_s'][0]} s",
                      first is not None and first <= BARS["start_within_s"][0])
        elif cls == "other":
            cells.add(f"{role}: never ended", not said, True, not said)
        else:
            want = nums_of[role]
            got = said[0] if said else None
            cells.add(f"{role}: ended as itself", None if got is None else got[2], want,
                      got is not None and got[2] == want)
            cells.add(f"{role}: ended within", None if got is None else got[0], f"<= {BARS['ended_within_s'][0]} s",
                      got is not None and got[0] <= BARS["ended_within_s"][0])
            if got is not None and got[2] == want and got[0] <= BARS["ended_within_s"][0]:
                in_time[role] = got[0]
    group, pairs = _matches(pics, kept)                      # B176: saves that are the same picture are one match
    cells.add("no two saves of one ending the same picture", pairs,
              f">= {SAME_PICTURE[0]} grey ({SAME_PICTURE[1]})", not pairs)
    only: dict = {}
    bar = BARS["ended_within_s"][0]
    one = _one_save_digits(es, spec, pics, labels, texts)    # B186: a digit one save shows several times
    from_one = {d: v for d, v in one["digits"].items() if v["learnt"]}
    shown_here: dict = {}
    for gid in sorted(set(group.values())):                  # B175 for numbers (B181: every number of the save)
        members = sorted(x for x in group if group[x] == gid)
        lo_spec, lo_arr, why = _learn_without(es, b, pics, labels, members)
        mine = [d for d, v in from_one.items() if v["save"] in members]
        for role in members:
            name = f"left out: {role}"
            bar_words = (f"{texts[role]} (every number) within <= {bar} s, never other numbers (a digit only it shows "
                         "read with its own other glyphs; a column only it fills shown only here)")
            here = [d for d in _only_here(role, members, texts) if d not in from_one]
            if why:
                cells.add(name, why, bar_words, False)
                only[role] = here
                continue
            said, got = _read_all(es, lo_spec, lo_arr, pics / role, texts[role], direct=True)
            got = _fill(texts[role], got, mine)
            how, here_ = _judge(texts[role], got, mine)       # B185 / B186
            if here_:
                shown_here[role] = here_
            took = said[0][0] if said else in_time.get(role)  # the full reader's own end when its final holds one
            ok = got is not None and how == "same" and took is not None and took <= bar
            cells.add(name, None if got is None else [_got_text(got) + (
                " (shown only here: " + "; ".join(", ".join(v) for v in here_.values()) + ")" if here_ else ""),
                took if said else f"{took} (the full reader's)"], bar_words, ok)
            if not ok:
                only[role] = here
    learnt = sorted(k[-1] for k in (spec.get("score") or {}).get("keys") or [])
    shows = {d: sum(1 for t in texts.values() if d in _digits_of(t)) for d in "0123456789"}
    expected = expected_digits(b)                             # B198: only the digits 0..N can show (0-9 without it)
    few = [d for d in expected if shows[d] < 2 and d not in from_one]
    read_ = {"shown by fewer than two saves": few}
    if b.get("max_score") is not None:
        read_["not expected (above the highest score)"] = [d for d in "0123456789" if d not in expected]
    if one["digits"]:                                        # B186: what one save alone showed, and the spread
        read_["learnt from one save"] = {d: f"{v['glyphs']} glyphs in {v['save']}, {v['read back']} read back"
                                         + ("" if v["learnt"] else " — not learnt") for d, v in one["digits"].items()}
        read_["across-save spread"] = one["spread"]
    cells.add(_every_digit_cell(b), read_, {"shown by fewer than two saves": []}, not few)   # B181 / B186 / B198
    recorded = {"digits": {"in two saves or more": [d for d in "0123456789" if shows[d] >= 2],
                           "in one save": [d for d in "0123456789" if shows[d] == 1],
                           "learnt from one save": sorted(from_one),
                           "never": [d for d in "0123456789" if shows[d] == 0]},
                "digits learnt": learnt}
    if b.get("max_score") is not None:                       # B198: recorded, never a cell
        recorded["digits"]["expected"] = expected
        recorded["digits"]["not expected"] = [d for d in "0123456789" if d not in expected]
        above = sorted(r_ for r_, t_ in texts.items() if any(x > int(b["max_score"]) for x in _all_numbers(t_)))
        if above:
            recorded["above the highest score"] = above
    if shown_here:
        recorded["shown only here"] = shown_here
    inputs = learn_inputs(code, b)
    if cells.passed:                                         # only a passing title reaches the rules folder
        begin = r / _begin_name(b)
        side_path = r / f"{b['game']}.party.json"
        side = json.dumps(_sidecar(b, spec), indent=1, sort_keys=True) + "\n"
        for p_, want in ((begin, (kept_folder(code) / "begin.state").read_bytes()), (side_path, side.encode())):
            if p_.exists() and p_.read_bytes() != want and not made:
                cells.add("rules folder: no other title's file overwritten", False, True, False)
                return finish(code, "learn", cells, inputs, recorded=recorded)
        if not (made.get("from") == key and spec_path.is_file() and sha(spec_path) == made.get("spec")):
            es.save_spec(spec, arrays, spec_path)
        write_if_changed(begin, (kept_folder(code) / "begin.state").read_bytes())
        write_if_changed(side_path, side)
        b["learnt"] = {"from": key, "spec": sha(spec_path)}
        write_if_changed(binding_path(code), json.dumps(b, indent=1, sort_keys=True) + "\n")
        return finish(code, "learn", cells, inputs, recorded=recorded)
    lined = any(_sides(t)[0][0] for t in texts.values())
    ask = _score_line(b, cells, kept, only, group, pairs, few, lined)
    if ask:
        recorded.update(ask[1])
    rc = finish(code, "learn", cells, inputs, note=ask[0] if ask else "", recorded=recorded)
    if ask:
        out(ask[0])
    return rc


def _score_line(b: dict, cells: Cells, kept, only: dict, group: dict, pairs: list, few: list | None = None,
                lined: bool = False) -> tuple[str, dict] | None:
    """B178 / B181: the line for one more save — the digits fewer than two saves show (and any a save left out was not
    read for), named; else B171's line."""
    code = b["code"]
    for a_, b_, _d in pairs or []:                           # B176: the same match saved twice first
        line = f"{a_} and {b_} look like the same match saved twice: save {b_} again from another match."
        return line, {"same match twice": [a_, b_], "line": line}
    digits = sorted(set(few or []) | set().union(*[set(v) for v in only.values()] or [set()]))
    digits = [d for d in digits if d in expected_digits(b)]  # B198: only digits that can occur
    if digits:
        endings = [f"end_P{k}" for k in range(1, b["players"] + 1)]
        roles = [x for x in (next_role(e, kept) for e in endings) if x]
        if not roles:
            return _cannot(code, endings, SAVES_PER_ENDING_MAX)
        words = ", ".join(digits[:-1]) + (" or " if len(digits) > 1 else "") + digits[-1]
        where = (f"whose line score shows {words} (in any quarter, overtime or final, either side)"
                 if lined else f"whose final score shows {words} (either side's number)")
        line = (f"One more save: a match either player won {where}; the more of them the better — save the screen "
                f"after it to a free slot, then register {code} … --collect <role>=<slot> with the role of the player "
                f"who won (" + ", ".join(f"{x} if P{x[5]} won" for x in roles) + f"), label {code} and learn {code} "
                f"again. {len(digits)} digit{'s are' if len(digits) != 1 else ' is'} still short ({words}); if one "
                "is still short after that match, learn asks for one more.")     # B188: never "one is enough"
        return line, {"one more save": roles, "digits asked": digits, "line": line}
    return one_more_save(b, cells, kept, None, group=group, pairs=pairs)



# --- B191 / B192: a word spelled by the player who lost (`--result letters --word <the word>`) ---------------------------
LETTERS_READING = re.compile(r"^(?:[A-Z-]{1,12}|_)(?:/(?:[A-Z-]{1,12}|_)){1,3}$")
LOOK_LETTERS = re.compile(r"^look=(all|[A-Z-]:\d+(?:\.\d+)*)$")
FOUR_LETTERS = ("a four-player letters title is not built: the player who spelled the word lost, but which of the other "
                "three won is not on that screen — winner-only would name a winner the game never showed; the hub "
                "could honestly report only \"port k lost\", and the board has no such result")


def _letters_side_fits(side: str, word: str) -> bool:
    """A corner as read fits the word: '_' (nothing shown), or as long as the word with each place its letter or '-'."""
    return side == "_" or (len(side) == len(word) and all(c in (w, "-") for c, w in zip(side, word)))


def parse_letters(items: list[str], players: int) -> dict:
    """role=<P1>/<P2>,<P1>/<P2> — each player's corner, its letters left to right ('-' a not-yet mark, '_' nothing),
    from <role>.1.png and <role>.2.png."""
    got = {}
    for item in items:
        role, _, val = item.partition("=")
        parts = val.split(",")
        if not (ROLE.match(role) and role.startswith("end_P")) or len(parts) != 2:
            raise Usage(f"label <code> <role>=<P1>/<P2>,<P1>/<P2>: {item}")
        if not all(LETTERS_READING.match(x) for x in parts):
            raise Usage(f"a reading is each player's letters, P1 first, joined by '/' (capitals; '-' for a not-yet "
                        f"mark, '_' when the corner shows nothing): {item}")
        if any(len(x.split("/")) != players for x in parts):
            raise Usage(f"a reading names {players} players: {item}")
        got[role] = {"readings": parts, "by": "session"}
    return got


def _letters_inputs_of(pics: Path, kept: dict) -> tuple:
    """The begin's and the mid-match save's screen pictures (learn's own labels: the frames near each run's anchor),
    and each end save's two label pictures."""
    labels = _labels(pics, kept, _endscreen())
    def frames(role, want):
        rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((pics / role / "index.csv").open())]
        ranges = labels["runs"][role]
        return [str(pics / role / f) for t, f in rows
                if any(x["label"] == want and x["from"] - 1e-6 <= t <= x["to"] + 1e-6 for x in ranges)]
    starts = frames("begin", "start")
    others = [p for role in sorted(kept) if role.startswith("other") for p in frames(role, "other")]
    ends = {r: [str(pics / r / f) for f in _two_pictures(pics, r)] for r in sorted(kept) if r.startswith("end_P")}
    return starts, others, ends


def _learn_letters_spec(es, b: dict, pics: Path, kept: dict, sides: dict, without=(), name: str = ""):
    starts, others, ends = _letters_inputs_of(pics, kept)
    use = {r: p for r, p in ends.items() if r not in without}
    return es.learn_letters(starts, others, use, {r: sides[r] for r in use}, b["word"], b["players"], name=name)


def _letters_sides_of(code: str) -> dict:
    rec = label_record(code)
    return {r: v["readings"][0].split("/") for r, v in rec["saves"].items() if v.get("readings")}


def _letters_read(es, spec: dict, arrays: dict, path) -> list | None:
    """One picture's corners as a fresh reader reads them (None: the spec has no corners)."""
    from PIL import Image
    rd = es.Reader(spec, arrays)
    if not getattr(rd, "found", False):
        return None
    with Image.open(path) as im:
        return rd.sides(im.convert("RGB"))


def _letters_sheet(es, spec: dict, arrays: dict, ends: dict, sides: dict, folder: Path) -> dict:
    """B191's last look: every glyph of every labelled corner (one picture of each save), grouped by the letter it was
    read as, in one picture (label/letters.png): a row per letter, its tiles numbered 1… -> {letter: [save of each]}."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    lt = spec["letters"]
    rd = es.Reader(spec, arrays)
    tiles: dict = {}
    for role in sorted(ends):
        with Image.open(ends[role][0]) as im:
            a = es.letters_area(im)
        for p in sorted(rd.places):
            st = sides[role][p - 1]
            m, gl = es.letters_glyphs(a, rd.places[p], rd.bins[p], rd.glyph_min)
            if st == "_" or len(gl) != len(st):
                continue
            x0, y0, _x1, _y1 = rd.places[p]
            for ch, g in zip(st, gl):
                crop = a[max(0, y0 + g[0] - 2):y0 + g[2] + 3, max(0, x0 + g[1] - 2):x0 + g[3] + 3]
                tiles.setdefault(ch, []).append((role, crop))
    if not tiles:
        return {}
    s_ = 2
    th = max(c.shape[0] for v in tiles.values() for _r, c in v) * s_
    tw = max(c.shape[1] for v in tiles.values() for _r, c in v) * s_
    font = ImageFont.load_default(size=22)
    small = ImageFont.load_default(size=14)
    width = 60 + max(len(v) for v in tiles.values()) * (tw + 10)
    sheet = Image.new("RGB", (width, len(tiles) * (th + 30) + 10), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, ch in enumerate(sorted(tiles)):
        y = 6 + i * (th + 30)
        d.text((10, y + th // 2 - 12), ch, fill=(0, 0, 0), font=font)
        for j, (_r, crop) in enumerate(tiles[ch]):
            x = 60 + j * (tw + 10)
            sheet.paste(Image.fromarray(np.clip(crop, 0, 255).astype("uint8")).resize(
                (crop.shape[1] * s_, crop.shape[0] * s_), Image.NEAREST), (x, y))
            d.text((x, y + th + 4), str(j + 1), fill=(0, 0, 0), font=small)
    sheet.save(folder / "letters.png")
    del lt
    return {ch: [r for r, _c in v] for ch, v in sorted(tiles.items())}


def _label_letters(code: str, b: dict, a: dict) -> int:
    kept = kept_states(code)
    require(code, "register", register_inputs(b, kept))
    es = _endscreen()
    word, n = b["word"], b["players"]
    rec = label_record(code)
    ends = sorted(r for r in kept if r.startswith("end_P"))
    items = a.get("readings") or []
    looks = [x for x in items if x.startswith("look=")]
    for x in looks:
        if not LOOK_LETTERS.match(x):
            raise Usage(f"the last look: look=all, or look=<letter>:<tile numbers joined by '.'>: {x}")
    given = parse_letters([x for x in items if not x.startswith("look=")], n)
    for role in given:
        if role not in kept:
            raise Usage(f"{role} is not a kept end save")
    for role in list(rec["saves"]):
        if rec["saves"][role].get("sha") != kept.get(role):
            del rec["saves"][role]
    for role, v in given.items():
        old = rec["saves"].get(role) or {}
        rec["saves"][role] = {"sha": kept[role], "readings": v["readings"], "by": "session",
                              "named": old.get("named", 0), "named_for": dict(old.get("named_for") or {})}
    cells = Cells()
    try:
        pics = _pictures(code, b, kept)
    except PicturesFailed as exc:
        cells.add("pictures made", exc.read(), "every kept state's pictures", False)
        return finish(code, "label", cells, label_inputs(code, b))
    folder = label_folder(code)
    folder.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    for role in ends:
        for i, f in enumerate(_two_pictures(pics, role), 1):
            with Image.open(pics / role / f) as im:
                im.convert("RGB").save(folder / f"{role}.{i}.png")
    missing = [r for r in ends if r not in rec["saves"]]
    cells.add("every end save read", missing, [], not missing)
    named: dict = {}
    reason: dict = {}

    def name(role_: str, words_: str, why_: str) -> None:
        if role_ not in named:
            named[role_], reason[role_] = words_, why_
    for role in ends:
        v = rec["saves"].get(role)
        if not v:
            continue
        rd = v["readings"]
        if not cells.add(f"{role}: the two readings the same", rd, "the same letters from both pictures", rd[0] == rd[1]):
            name(role, "its two readings differ", "readings")
        sd = rd[0].split("/")
        fits = all(_letters_side_fits(s, word) for s in sd)
        if not cells.add(f"{role}: each corner fits the word", sd,
                         f"{len(word)} places, each the word's letter there or '-' (or '_': nothing shown)", fits):
            name(role, "a corner does not fit the word", "fits")
        k = int(role[5])
        spelled = [s == word for s in sd]
        agree = (not spelled[k - 1]) and sum(spelled) == 1
        if not cells.add(f"{role}: the role agreeing", ["spelled" if x else "not spelled" for x in spelled],
                         f"P{k} won: the other player's letters spell the word, P{k}'s do not", agree):
            name(role, f"its letters do not say P{k} won", "role")
    sides = {r: rec["saves"][r]["readings"][0].split("/") for r in ends if r in rec["saves"]}
    recorded: dict = {"pictures": {r: [f"{r}.1.png", f"{r}.2.png"] for r in ends}}
    look_for = digest({r: sides.get(r) for r in ends})
    if not missing and not named:
        spec, arrays, rep = _learn_letters_spec(es, b, pics, kept, sides)
        lt = spec["letters"]
        found = bool(lt.get("found")) and "places" in lt
        cells.add("the letters at one place in every save", "found" if found else lt.get("not_found") or "not learnt",
                  "found", found)
        if found:
            starts, others, all_ends = _letters_inputs_of(pics, kept)
            for role in ends:                                # read back by a reader learnt without it (real only)
                s2, a2, _r2 = _learn_letters_spec(es, b, pics, kept, sides, without=(role,))
                got = None
                if s2["letters"].get("found") and "places" in s2["letters"]:
                    got = [_letters_read(es, s2, a2, p) for p in all_ends[role]]
                ok = got is not None and all(g == sides[role] for g in got)
                if not cells.add(f"{role}: read back by a reader learnt without it",
                                 "not learnt without it" if got is None else ["/".join(x if x else "?" for x in g)
                                                                             for g in got],
                                 "/".join(sides[role]), ok):
                    name(role, "a reader learnt from the other saves "
                         + ("cannot be learnt without it" if got is None else "reads it otherwise"), "read back")
            rows = _letters_sheet(es, spec, arrays, all_ends, sides, folder)
            if looks and rec.get("tiles", {}).get("for") == look_for:
                bad: dict = {}
                for x in looks:
                    ans = x[len("look="):]
                    if ans == "all":
                        continue
                    ch, _, idx = ans.partition(":")
                    for i in idx.split("."):
                        if ch not in rows or not 1 <= int(i) <= len(rows[ch]):
                            raise Usage(f"no tile {i} in the row of {ch} at the last look")
                        bad.setdefault(ch, []).append(int(i))
                rec["look"] = {"for": look_for, "bad": {c_: sorted(set(v)) for c_, v in bad.items()}}
            rec["tiles"] = {"for": look_for, "rows": rows}
            look = rec.get("look") if (rec.get("look") or {}).get("for") == look_for else None
            if look is None:
                cells.add("the last look: every glyph is the letter it was read as", "not given (label/letters.png)",
                          "look=all", False)
            else:
                cells.add("the last look: every glyph is the letter it was read as", look["bad"] or "all", "all",
                          not look["bad"])
                for ch, idx in sorted(look["bad"].items()):
                    for i in idx:
                        name(rows[ch][i - 1], f"a glyph read as {ch} is not one, at the last look", "look")
            recorded["sheet"] = {c_: len(v) for c_, v in rows.items()}
    for role in ends:
        v = rec["saves"].get(role)
        if v is not None and role in named and role in given:
            v["named"] = v.get("named", 0) + 1
            v.setdefault("named_for", {})[reason[role]] = v.get("named_for", {}).get(reason[role], 0) + 1
    if named and (rec.get("look") or {}).get("bad"):
        rec.pop("look", None)
    write_if_changed(label_path(code), json.dumps(rec, indent=1, sort_keys=True) + "\n")
    form = "/".join(f"<P{i}>" for i in range(1, n + 1))
    line = ""
    if missing:
        line = (f"Read each player's letters in its corner on each end save's two pictures in the title's add_game "
                f"folder, label/ (<role>.1.png and <role>.2.png), P1 first, joined by '/': the letters left to right in "
                f"capitals, '-' for each not-yet mark, '_' if the corner shows nothing; then label {code} "
                + " ".join(f"{r}={form},{form}" for r in missing) + " (the first reading from .1, the second from .2).")
        recorded["read"] = missing
    elif named:
        twice = [r for r in sorted(named) if (rec["saves"][r].get("named_for") or {}).get(reason[r], 0) >= LEFT_OUT_TRIES]
        if twice:
            r = twice[0]
            line = (f"Stop: {r} ({named[r]}) after it was read again twice. Do not ask the user and do not ask for "
                    f"another match: take this line back to the chat (Cowork).")
            recorded["back to the chat"] = r
        else:
            line = ("Read again: " + "; ".join(f"{r} ({named[r]})" for r in sorted(named)) + ". Their pictures in "
                    f"label/ (<role>.1.png, <role>.2.png); then label {code} "
                    + " ".join(f"{r}={form},{form}" for r in sorted(named)) + ".")
            recorded["read again"] = sorted(named)
    elif not cells.passed and any(r["cell"].startswith("the last look") and not r["met"] for r in cells.rows):
        line = (f"Look at label/letters.png: a row for each letter ('-' the not-yet marks), every glyph read as that "
                f"letter, numbered under it. If every glyph in every row is its row's letter: label {code} look=all. "
                f"Else name the ones that are not: label {code} look=<letter>:<numbers joined by '.'> (one look= for "
                f"each such row).")
        recorded["look"] = "asked"
    if line:
        recorded["line"] = line
    rc = finish(code, "label", cells, label_inputs(code, b), note=line, recorded=recorded)
    if line:
        out(line)
    return rc


def _letters_replay(es, spec: dict, arrays: dict, run: Path, start_loaded: bool, scenes: list | None = None) -> tuple:
    """A run's pictures through one fresh reader and B102's Ended, in colour (B191) -> (first start read s, [(s, end)]).
    `scenes`: the moving-screen gate — every read, the run's own corners' boxes kept and the rest of the picture taken
    in turn from these (the title's other saves' pictures): a screen that changes under letters that stay."""
    from PIL import Image
    import numpy as np
    rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((run / "index.csv").open())]
    now = [0.0]
    reader = es.Reader(spec, arrays, clock=lambda: now[0])
    ended = es.Ended(spec)
    if start_loaded:
        ended.start_loaded()
    first_start, said = None, []
    for i, (t, f) in enumerate(rows):
        now[0] = t
        with Image.open(run / f) as im:
            im = im.convert("RGB")
            if scenes:
                im = _scene_under(es, spec, im, scenes[i % len(scenes)])
            r = reader.read(im, now=t)
        if r["class"] == spec["start_class"] and first_start is None:
            first_start = round(t - rows[0][0], 2)
        done = ended.feed(r["class"], None)
        if done and not said:
            said.append((round(t - rows[0][0], 2), done))
    return first_start, said


def _scene_under(es, spec: dict, im, scene: Path):
    """The picture's corners' boxes (at the game's area) over another real picture of the title."""
    from PIL import Image
    import numpy as np
    a = es.letters_area(im)
    with Image.open(scene) as sc:
        b = es.letters_area(sc)
    for box in (spec["letters"].get("places") or {}).values():
        x0, y0, x1, y1 = box
        b[y0:y1, x0:x1] = a[y0:y1, x0:x1]
    return Image.fromarray(np.clip(b, 0, 255).astype("uint8"))


def _learn_letters(code: str, b: dict, kept: dict, pics: Path, es) -> int:
    cells = Cells()
    sides = _letters_sides_of(code)
    r = rules_folder()
    spec_path = r / f"{b['game']}.endscreen.json"
    spec, arrays, rep = _learn_letters_spec(es, b, pics, kept, sides, name=b["game"])
    lt = spec["letters"]
    found = bool(lt.get("found")) and "places" in lt
    cells.add("spec usable", bool(spec.get("usable")), True, bool(spec.get("usable")))
    cells.add("the letters at one place in every save", "found" if found else lt.get("not_found"), "found", found)
    tr = rep.get("synthetic") or {}
    recorded: dict = {"synthetic": {k: tr.get(k) for k in ("seed", "held_out", "trained", "backgrounds", "rounds",
                                                           "held_out_wrong_of")} | {"seconds": rep.get("learn_s")}}
    held_wrong = tr.get("held_out_wrong")
    cells.add("every held-out synthetic picture read (training's own bar; never counts toward a pass)",
              {"held out": tr.get("held_out"), "read wrong or not read": held_wrong, "trained on": tr.get("trained")},
              f"<= {BARS['synthetic_held_wrong_max'][0]} ({BARS['synthetic_held_wrong_max'][1]})",
              held_wrong is not None and held_wrong <= BARS["synthetic_held_wrong_max"][0])
    ends = sorted(x for x in kept if x.startswith("end_P"))
    if found:
        for role in sorted(kept):                            # the real saves' own pictures, as the hub reads them
            cls = _role_class(role)
            first_start, said = _letters_replay(es, spec, arrays, pics / role, cls != "start")
            if cls == "start":
                cells.add(f"{role}: never ended", not said, True, not said)
                cells.add(f"{role}: recognised within", first_start, f"<= {BARS['start_within_s'][0]} s",
                          first_start is not None and first_start <= BARS["start_within_s"][0])
            elif cls == "other":
                cells.add(f"{role}: never ended", not said, True, not said)
            else:
                cells.add(f"{role}: ended as itself", said[0][1] if said else None, cls, bool(said) and said[0][1] == cls)
                cells.add(f"{role}: ended within", said[0][0] if said else None, f"<= {BARS['ended_within_s'][0]} s",
                          bool(said) and said[0][0] <= BARS["ended_within_s"][0])
        moving = {}
        firsts = {x: pics / x / _two_pictures(pics, x)[0] for x in sorted(kept)}
        for role in ends:                                   # a moving screen never ended
            scenes = [firsts[x] for x in sorted(firsts) if x != role]
            _fs, said = _letters_replay(es, spec, arrays, pics / role, True, scenes=scenes)
            if said:
                moving[role] = said[0][1]
        cells.add("a moving screen never ended (each end save's corners as they are, the rest of the picture taken in "
                  "turn from the title's other saves every read)", moving or "never", "never", not moving)
        _starts, _others, all_ends = _letters_inputs_of(pics, kept)
        for role in ends:                                   # left out: a spec learnt without it, its real pictures
            s2, a2, _r2 = _learn_letters_spec(es, b, pics, kept, sides, without=(role,))
            cls = _role_class(role)
            ok2 = bool(s2["letters"].get("found")) and "places" in s2["letters"] and bool(s2.get("usable"))
            got_l = [_letters_read(es, s2, a2, p) for p in all_ends[role]] if ok2 else None
            _fs, said = _letters_replay(es, s2, a2, pics / role, True) if ok2 else (None, [])
            right = (ok2 and bool(said) and said[0][1] == cls and said[0][0] <= BARS["ended_within_s"][0]
                     and all(g == sides[role] for g in got_l))
            cells.add(f"left out: {role}",
                      "not learnt without it" if not ok2 else [said[0][1] if said else None,
                                                               said[0][0] if said else None,
                                                               ["/".join(x if x else "?" for x in g) for g in got_l]],
                      f"{cls} within <= {BARS['ended_within_s'][0]} s, never another, letters {'/'.join(sides[role])}",
                      right)
    group, pairs = _matches(pics, kept)
    cells.add("no two saves of one ending the same picture", pairs,
              f">= {SAME_PICTURE[0]} grey ({SAME_PICTURE[1]})", not pairs)
    inputs = learn_inputs(code, b)
    if cells.passed:
        begin = r / _begin_name(b)
        side_path = r / f"{b['game']}.party.json"
        side = json.dumps(_sidecar(b, spec), indent=1, sort_keys=True) + "\n"
        made = b.get("learnt") or {}
        for p, want in ((begin, (kept_folder(code) / "begin.state").read_bytes()), (side_path, side.encode())):
            if p.exists() and p.read_bytes() != want and not made:
                cells.add("rules folder: no other title's file overwritten", False, True, False)
                return finish(code, "learn", cells, inputs, recorded=recorded)
        es.save_spec(spec, arrays, spec_path)
        write_if_changed(begin, (kept_folder(code) / "begin.state").read_bytes())
        write_if_changed(side_path, side)
        b["learnt"] = {"from": digest(kept), "spec": sha(spec_path)}
        write_if_changed(binding_path(code), json.dumps(b, indent=1, sort_keys=True) + "\n")
        return finish(code, "learn", cells, inputs, recorded=recorded)
    line, rec2 = _letters_line(b, cells, kept, tr, pairs)
    recorded.update(rec2)
    rc = finish(code, "learn", cells, inputs, note=line, recorded=recorded)
    out(line)
    return rc


def _letters_line(b: dict, cells: Cells, kept, tr: dict, pairs: list) -> tuple[str, dict]:
    """One plain line: what learn asks of a letters title, and why — and whether synthetic training could cover it."""
    code = b["code"]
    bad = [x["cell"] for x in cells.rows if not x["met"]]
    for a_, b_, _d in pairs or []:
        line = f"{a_} and {b_} look like the same match saved twice: save {b_} again from another match."
        return line, {"same match twice": [a_, b_], "line": line}
    if any(c.startswith("the letters at one place") for c in bad):
        line = ("No corner could be cut clean from these saves (no two saves show a player's same letters over "
                "different pictures, and no corner is plain): synthetic training cannot make that, it only trains on "
                "letters already cut. One more save: a match either player won whose corners show the same letters "
                "as another save's over another background — save the screen after it to a free slot, then register "
                f"{code} … --collect <role>=<slot> (end_P1_<n> if P1 won, end_P2_<n> if P2 won), label {code} and "
                f"learn {code} again.")
        return line, {"line": line, "one more save": "a corner cut clean"}
    if any(c.startswith("every held-out synthetic") for c in bad):
        who = ", ".join(tr.get("held_out_wrong_of") or []) or "the saves"
        line = (f"Synthetic training did not reach every held-out picture (the letters of {who} over some of the "
                "title's own backgrounds): a background in the letters' own colours hides them. More saves of these "
                "backgrounds would not fix it; take this line back to the chat (Cowork). At the hub such a match ends "
                "with no result, never a guess.")
        return line, {"line": line, "back to the chat": "synthetic"}
    lo = [c[len("left out: "):] for c in bad if c.startswith("left out: ")]
    if lo:
        line = (f"{', '.join(lo)}: a reader learnt without {'it' if len(lo) == 1 else 'each'} does not read "
                f"{'it' if len(lo) == 1 else 'them'} as {'its' if len(lo) == 1 else 'their'} own. Synthetic training "
                "already covers new backgrounds; what is missing is a letter or a corner only that save shows. One "
                f"more save: a match whose corners show the same letters as {lo[0]}'s, saved to a free slot, then "
                f"register {code} … --collect <role>=<slot>, label {code} and learn {code} again.")
        return line, {"line": line, "one more save": lo}
    line = ("learn did not meet: " + "; ".join(bad) + ". Take this line back to the chat (Cowork).")
    return line, {"line": line, "back to the chat": bad}


# --- B163: rehearse — learn's whole real path on a title already added, into a scratch rules folder --------------------------
SCRATCH_ENV = ("PRIVYHUB_H7_RULES", "PRIVYHUB_ADD_GAME_HOME", "PRIVYHUB_ADD_GAME_EVIDENCE", "PRIVYHUB_ADD_GAME_LOGS")


def kept_source(code: str) -> Path:
    """The title's kept H7 folder (read only): ~/privyhub_h7/<code in lower case>."""
    return _env_path("PRIVYHUB_ADD_GAME_KEPT_ROOT", Path.home() / "privyhub_h7") / code.lower()


def rehearse_roles(code: str) -> dict:
    """The kept states as the tool's roles, by name: begin; other* / mid* -> other, other2 ...; end_p<k> -> end_P<k>;
    end_p<k>_<x> -> another ending of end_P<k> (read, not a learning role); results_<n> -> an ending whose row the real
    rules read (a role end_r<row> for a `places` title)."""
    src = kept_source(code)
    files = sorted(p for p in src.iterdir() if p.is_file() and p.suffix == ".state") if src.is_dir() else []
    roles: dict = {}
    extra: dict = {}
    results: list = []
    unused: list = []
    for p in files:
        stem = p.name[:-6]
        m_end = re.match(r"^end_p([1-4])$", stem)
        m_more = re.match(r"^end_p([1-4])_[a-z0-9]+$", stem)
        if stem == "begin":
            roles["begin"] = p
        elif re.match(r"^(other|mid)[a-z0-9_]*$", stem):
            roles["other" if "other" not in roles else f"other{sum(1 for r in roles if r.startswith('other')) + 1}"] = p
        elif m_end:
            roles[f"end_P{m_end.group(1)}"] = p
        elif m_more:
            extra[stem] = (p, f"end_P{m_more.group(1)}")
        elif re.match(r"^results_[0-9]+$", stem):
            results.append(p)
        else:
            unused.append(p.name)
    return {"roles": roles, "extra": extra, "results": results, "unused": unused}


def _read_run(es, spec: dict, arrays: dict, run: Path):
    """A run's pictures read as learn's replays read them (the begin loaded first): [class, places] once ended."""
    from PIL import Image
    rows = [(float(r["seconds"]), r["file"]) for r in csv.DictReader((run / "index.csv").open())]
    now = [0.0]
    reader = es.Reader(spec, arrays, clock=lambda: now[0])
    ended = es.Ended(spec)
    ended.start_loaded()
    for t, f in rows:
        now[0] = t
        with Image.open(run / f) as im:
            r = reader.read(_for_reader(im, spec), now=t)
        done = ended.feed(r["class"], r.get("places"))
        if done:
            return [done, list(ended.places) if ended.places else None]
    return None


def _capture_run(state: Path, b: dict, run: Path) -> None:
    run.mkdir(parents=True, exist_ok=True)
    rows = _call_capture(_capture_fn(), state, b, run, run.name, b["code"])
    with (run / "index.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seconds", "file"])
        for t, name in rows:
            w.writerow([f"{t:.2f}", name])


def _rules_shas() -> dict:
    r = rules_folder()
    return {p.name: sha(p) for p in sorted(r.iterdir()) if p.is_file()} if r.is_dir() else {}


def _rehearse_in(code, b, sb, es, rspec, rarr, scratch, found, roles, extra, said_rows, missing, cells,
                 promoted=None, not_end=None, rec_learn=None) -> None:
    """rehearse's work inside the scratch (the environment pointed at it and put back by the caller)."""
    label_rec = read_json(label_path(code)) if b["result"] == "score" else None     # B178: read before the switch
    for name, (p, want) in sorted(extra.items()):          # B171: a kept extra ending the real rules end on as its own
        if not want or not want.startswith("end_P"):        # is one more source; one they do not stays read, not a role
            continue
        run = scratch / "extra" / name
        _capture_run(p, sb, run)
        got = _read_run(es, rspec, rarr, run)
        role = next_role(want, roles) if got is not None and got[0] == want else None
        if role:
            roles[role] = p
            del extra[name]
            if promoted is not None:
                promoted[name] = role
        elif not_end is not None:
            not_end.append(name)
    for p in found["results"]:                            # a results screen: its row as the real rules read it
        run = scratch / "extra" / p.name[:-6]
        _capture_run(p, sb, run)
        got = _read_run(es, rspec, rarr, run)
        row = "".join(str(x) for x in (got[1] or [])) if got else ""
        ok_row = len(row) == b["players"] and sorted(row) == [str(i) for i in range(1, b["players"] + 1)]
        if b["result"] == "places" and ok_row and f"end_r{row}" not in roles:
            roles[f"end_r{row}"] = p
            said_rows[p.name] = f"end_r{row}"
        else:
            extra[p.name[:-6]] = (p, None)
    need = _roles_needed(b["players"], b["result"], per_ending=1)   # what learn cannot run without
    missing.extend(r for r in need if r not in roles)
    if b["result"] == "places":
        rows_ = [r[5:] for r in roles if r.startswith("end_r")]
        if not all({r[c] for r in rows_} == {str(i) for i in range(1, b["players"] + 1)} for c in range(b["players"])):
            missing.append("results rows with every place in every column (have " + (", ".join(sorted(rows_)) or "none") + ")")
    os.environ.update({"PRIVYHUB_ADD_GAME_LOGS": str(logs_folder(code))})     # B167: beside the scratch, kept
    os.environ.update({"PRIVYHUB_H7_RULES": str(scratch / "rules"), "PRIVYHUB_ADD_GAME_HOME": str(scratch / "home"),
                       "PRIVYHUB_ADD_GAME_EVIDENCE": str(scratch / "evidence")})   # put back by the caller
    (scratch / "rules").mkdir()
    kf = kept_folder(code)
    kf.mkdir(parents=True)
    for role, p in roles.items():
        shutil.copyfile(p, kf / f"{role}.state")             # the kept copies; the kept folder only read
    sb["register_inputs"] = register_inputs(sb, kept_states(code))
    write_if_changed(binding_path(code), json.dumps(sb, indent=1, sort_keys=True) + "\n")
    write_if_changed(verdict_path(code, "register"),
                     json.dumps({"verdict": "PASS", "inputs": sb["register_inputs"]}) + "\n")
    if b["result"] == "score" and label_rec is not None:     # B178: the readings the title's label stage checked
        kept_now = kept_states(code)
        rec = {"saves": {r: v for r, v in (label_rec.get("saves") or {}).items() if kept_now.get(r) == v.get("sha")},
               "places": label_rec.get("places")}
        write_if_changed(label_path(code), json.dumps(rec, indent=1, sort_keys=True) + "\n")
        if all(r in rec["saves"] for r in kept_now if r.startswith("end_P")):
            write_if_changed(verdict_path(code, "label"),
                             json.dumps({"verdict": "PASS", "inputs": label_inputs(code, sb)}) + "\n")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            cmd_learn(code, {"check": False})             # learn's whole real path, into the scratch rules
        learnt = load_verdict(code, "learn") or {}
        if rec_learn is not None:                            # B171: learn's line, said as rehearse takes the save
            rec_learn["v"] = learnt
            line = str((learnt.get("recorded") or {}).get("line") or "")      # B175: the line learn recorded
            rec_learn["line"] = re.sub(r"then (register \S+ … --collect (\S+)=<slot> and )?learn (\S+) again",
                                       lambda m: f"then rehearse {m.group(3)} --collect "
                                                 f"{m.group(2) or 'end_r<its row>'}=<slot>", line)
        for r in learnt.get("cells", []):
            cells.add(f"learn: {r['cell']}", r["read"], r["bar"], r["met"])
        cells.add("learn's verdict in the scratch", learnt.get("verdict"), "PASS", learnt.get("verdict") == "PASS")
    except Exception as exc:                                   # the capture or the learner failed: said, not hidden
        cells.add("learn ran in the scratch", f"{type(exc).__name__}: {str(exc)[:120]}", "no error", False)
    spec_path = rules_folder() / f"{b['game']}.endscreen.json"
    sspec = es.load_spec(spec_path) if spec_path.is_file() else None
    endings = {r: (home(code) / "pictures" / r, _role_class(r)) for r in roles if r.startswith("end_")}
    for name, (p, want) in sorted(extra.items()):
        run = scratch / "extra" / name
        if not (run / "index.csv").is_file():
            _capture_run(p, sb, run)
        endings[name] = (run, want)
    for name, (run, want) in sorted(endings.items()):
        got_real = _read_run(es, rspec, rarr, run) if (run / "index.csv").is_file() else None
        got_scr = _read_run(es, sspec[0], sspec[1], run) if sspec and (run / "index.csv").is_file() else None
        own = (got_real is not None and (want is None or got_real[0] == want or
                                         (want.startswith("end_r") and got_real[1] == [int(c) for c in want[5:]])))
        if name in roles:                                    # a learning role: ended, the same, its own ending
            cells.add(f"{name}: the scratch rules read it as the real rules", [got_scr, got_real],
                      "the same, ended, its own ending", got_scr is not None and got_scr == got_real and own)
        else:                                                # B167: a kept extra: exactly as the real rules read it
            cells.add(f"{name}: the scratch rules read it as the real rules", [got_scr, got_real],
                      "the same (an ending the real rules end on: its own)", sspec is not None and got_scr == got_real
                      and (got_real is None or own))


def cmd_rehearse(code: str, a: dict) -> int:
    b = load_binding(code)
    if not b.get("described"):
        raise Refused("rehearse is for a title already in the rules folder (registered with --rules-players)")
    require(code, "learn", learn_inputs(code, b))
    _private_paths()
    found = rehearse_roles(code)
    if not found["roles"] and not found["extra"] and not found["results"] and not a.get("collect"):
        raise Refused(f"no kept states for {code}: nothing to rehearse")
    rel = _game_relpath(b)
    if not rel:
        raise Refused("the hub did not give the game file for this title (is the companion up?)")
    shown = {r: p.name for r, p in found["roles"].items()}
    rules_begin = rules_folder() / _begin_name(b)            # B167: the begin the title's mini game starts from
    if rules_begin.is_file():
        if "begin" in found["roles"] and sha(found["roles"]["begin"]) != sha(rules_begin):
            found["unused"].append(f"{found['roles']['begin'].name} (not the begin its mini game starts from)")
        found["roles"]["begin"] = rules_begin
        shown["begin"] = "the rules folder's begin"
    own = kept_folder(code)                                  # B171: the saves rehearse collected (the tool's, off the
    for item in a.get("collect") or []:                     # repo); a role the kept folder lacks: the user's slot, read only
        role, _, slot = item.partition("=")
        if not ROLE.match(role) or role in found["roles"] or slot not in ("1", "2", "3"):
            raise Usage("rehearse --collect role=slot: a role its kept folder lacks (e.g. other=2), slots 1-3")
        data = _slot_file({**b, "relative_path": rel}, int(slot)).read_bytes()
        own.mkdir(parents=True, exist_ok=True)
        write_if_changed(own / f"{role}.state", data)        # kept: the user may save over the slot now
        shown[role] = f"slot {slot}"
    collected = set()
    for p in sorted(own.glob("*.state")) if own.is_dir() else []:
        role = p.name[:-6]
        if ROLE.match(role) and role not in found["roles"]:
            found["roles"][role] = p
            shown.setdefault(role, "a save collected before")
            collected.add(role)
    es = _endscreen()
    real = rules_folder()
    rspec, rarr = es.load_spec(real / f"{b['game']}.endscreen.json")          # the real rules, read only
    kept_in = {p.name: sha(p) for p in sorted(kept_source(code).iterdir()) if p.is_file()} if kept_source(code).is_dir() else {}
    kept_in.update({f"slot:{r}": sha(p) for r, p in found["roles"].items() if r in collected})
    inputs = digest({"register": b["register_inputs"], "kept": kept_in})
    shas_before = _rules_shas()
    cells = Cells()
    sb = {"code": code, "game": b["game"], "players": b["players"], "system": b["system"], "result": b["result"],
          "cheat": b.get("cheat"), "relative_path": rel, "title": "", "content": str(project() / rel)}
    scratch = Path(tempfile.mkdtemp(prefix="rehearse_", dir=str(home(code))))
    roles = dict(found["roles"])
    extra = dict(found["extra"])
    said_rows: dict = {}
    old_env = {k: os.environ.get(k) for k in SCRATCH_ENV}
    missing: list = []
    promoted: dict = {}
    not_end: list = []
    rec_learn: dict = {}
    try:
        _rehearse_in(code, b, sb, es, rspec, rarr, scratch, found, roles, extra, said_rows, missing, cells,
                     promoted, not_end, rec_learn)
    except PicturesFailed as exc:                                  # B167: an ending's pictures, with its reason
        cells.add("rehearse's pictures made", exc.read(), "every kept ending's pictures", False)
    except Exception as exc:                                       # anything else in the scratch: a cell, not a trace
        cells.add("rehearse ran in the scratch", type(exc).__name__, "no error", False)
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(scratch, ignore_errors=True)
    shas_after = _rules_shas()
    changed = [n for n in set(shas_before) | set(shas_after) if shas_before.get(n) != shas_after.get(n)]
    cells.add("the real rules folder: every file's sha256 before = after", [len(shas_before), len(shas_after), len(changed)],
              "the same files, 0 changed", not changed)
    cells.add("the scratch removed", not scratch.exists(), True, not scratch.exists())
    below = [r for r in _roles_needed(b["players"], b["result"]) if r.startswith("end_") and r not in roles]
    rec = {"roles": {r: shown.get(r, p.name) for r, p in sorted(roles.items())}, "missing": missing,
           "endings read, not a role": sorted(extra), "unused": found["unused"], "rows read by the real rules": said_rows,
           "below two saves per ending": below}
    note = ("Roles (kept file -> role): " + ", ".join(f"{shown.get(r, p.name)} -> {r}" for r, p in sorted(roles.items())) +
            ". Missing: " + (", ".join(missing) or "none") + ". Endings read, not a role: " +
            (", ".join(f"{x} (not an end screen to the real rules)" if x in not_end else x for x in sorted(extra))
             or "none") + ". Below two saves per ending (a new title's minimum): " + (", ".join(below) or "none") + ".")
    asked = (rec_learn.get("v") or {}).get("recorded") or {}
    line = rec_learn.get("line") or ""
    if line:                                                 # B171: learn's line, as rehearse takes the save
        rec.update({k: asked[k] for k in ("one more save", "cannot be told apart", "wrong role", "same match twice")
                    if k in asked})
        note += "\n\n" + line
    rc = finish(code, "rehearse", cells, inputs, note=note, recorded=rec)
    if line:
        out(line)
    return rc


# --- the files that must not change (before = after) ------------------------------------------------------------------------
SLOT_FILE = re.compile(r"\.state(\d*)(\.png)?$")
HUB_SLOTS = (8, 9)          # B196: the hub's own scratch slots — 8 its load copy (B169), 9 its hold scratch (B9 / B12)
LEFT_OUT = ("the hub's own slots 8 and 9 and their pictures, under states and setups' states (the onn offers the user "
            "slots 1-3 only; RetroArch writes 9 only on the hub's own SAVE_STATE_SLOT 9 while a game plays, 8 only by "
            "the hub's load copy)")


def file_kind(name: str, root: str) -> str:
    """B196: what kind of file it is, from its suffix and its root only (never its name)."""
    if root in ("rules",):
        return "a rules file"
    if root in ("this title's kept folder", "a kept H7 folder"):
        return "a kept state"
    m = SLOT_FILE.search(name)
    if m:
        n, pic = int(m.group(1) or 0), " picture" if m.group(2) else ""
        if 1 <= n <= 3:
            return f"a user's slot {n}{pic}"
        if n == 0:
            return f"slot 0{pic} (every SAVE rewrites it)"
        if n in HUB_SLOTS:
            return f"the hub's slot {n}{pic}"
        return f"slot {n}{pic}"
    return "an in-game save" if name.endswith(".srm") else "another file"


def files_digest(b: dict) -> dict:
    """sha256 of the title's user slots and slot pictures (both indexes), every rules file, the kept folders (names
    hashed: no name is kept). B196: each with its root and kind ([sha, root, kind]); the hub's own slots 8 and 9 and
    their pictures left out (LEFT_OUT)."""
    roots = [("states", project() / "data/games/retroarch/states"),
             ("setups' states", project() / "data/games/retroarch/cheat_profiles"),
             ("rules", rules_folder()), ("this title's kept folder", home(b["code"]) / "kept")]
    h7 = _env_path("PRIVYHUB_ADD_GAME_KEPT_ROOT", Path.home() / "privyhub_h7")      # the kept H7 folders
    roots += [("a kept H7 folder", p) for p in sorted(h7.iterdir()) if p.is_dir() and p.name not in ("rules", "add_game")] \
        if h7.is_dir() else []
    out_ = {}
    for rname, root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            kind = file_kind(p.name, rname)
            if rname in ("states", "setups' states") and any(kind.startswith(f"the hub's slot {n}") for n in HUB_SLOTS):
                continue
            out_[hashlib.sha256(str(p.relative_to(root.parent)).encode()).hexdigest()[:16]] = [sha(p), rname, kind]
    return out_


def _sha_of(v):
    """A before's entry: [sha, root, kind] (B196), or the sha alone (a before written by older code)."""
    return v[0] if isinstance(v, list) else v


def files_changed(before: dict, after: dict, skip=()) -> list[dict]:
    """B196: every file whose sha differs, with its root, kind and hashed name — changed, new or gone."""
    out_ = []
    for k in sorted(set(before) | set(after)):
        if k in skip or _sha_of(before.get(k)) == _sha_of(after.get(k)):
            continue
        meta = after.get(k) if isinstance(after.get(k), list) else before.get(k)
        root, kind = (meta[1], meta[2]) if isinstance(meta, list) else ("not known", "not known")
        out_.append({"root": root, "kind": kind, "file": k,
                     "is": "new" if k not in before else "gone" if k not in after else "changed"})
    return out_


# --- B162: the title's own in-game saves (recorded before and after, never a cell) -------------------------------------------
SAVES = "data/games/retroarch/saves"


def _game_relpath(b: dict) -> str:
    """The game file's path in the library: the binding's, or (a title already in the rules folder) the hub's
    `details` for its id — in memory, never written."""
    rel = str(b.get("relative_path") or "")
    if not rel and b.get("game"):
        rel = str(hub("GET", "details", {"id": b["game"]}, timeout=10)["body"].get("relative_path") or "")
        GUARD.add(rel, Path(rel.replace("\\", "/")).stem)
    return rel


def ingame_saves(b: dict) -> dict:
    """{hashed name: {"kind": "setup" | "own", "sha": ...}}: every file under the title's setup's saves/ (files_digest's
    own names for them) and every file in the hub's saves/<core>/ whose stem is the game file's."""
    root = project()
    out_: dict = {}
    if b.get("cheat"):
        profiles = root / "data/games/retroarch/cheat_profiles"
        d = profiles / b["game"] / b["cheat"]["profile_id"] / "saves"
        if d.is_dir():
            for p in sorted(d.rglob("*")):
                if p.is_file():
                    out_[hashlib.sha256(str(p.relative_to(profiles.parent)).encode()).hexdigest()[:16]] = \
                        {"kind": "setup", "sha": sha(p)}
    rel = _game_relpath(b)
    stem = Path(rel.replace("\\", "/")).stem if rel else ""
    d = root / SAVES
    if stem and d.is_dir():
        for p in sorted(d.glob("*/*")):
            if p.is_file() and p.stem == stem:
                out_[hashlib.sha256(str(p.relative_to(d.parent)).encode()).hexdigest()[:16]] = {"kind": "own", "sha": sha(p)}
    return out_


def saves_before(code: str, b: dict, again: bool) -> None:
    path = home(code) / "saves_before.json"
    if again or not path.is_file():
        write_if_changed(path, json.dumps(ingame_saves(b), sort_keys=True))


def saves_recorded(before: dict | None, after: dict) -> list:
    """Each in-game save named by kind and number only, as changed / unchanged / new / gone."""
    if before is None:
        return [{"save": "-", "is": "no before (neither bench nor solo's lines ran)"}]
    rows = []
    for kind, word in (("setup", "under the setup"), ("own", "own")):
        keys = sorted(k for k in set(before) | set(after) if (before.get(k) or after.get(k))["kind"] == kind)
        for i, k in enumerate(keys, 1):
            b0, a0 = before.get(k), after.get(k)
            state = ("new" if b0 is None else "gone" if a0 is None else
                     "changed" if b0["sha"] != a0["sha"] else "unchanged")
            rows.append({"save": f"{word} {i}", "is": state})
    return rows


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
    saves_before(code, b, again=True)                         # B162: the title's in-game saves, recorded
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
        want_cls = (_role_class(ending) if ending.startswith("end_P") and side.get("result") != "score"
                    else "end")                              # B171: end_P1_2 ends as end_P1; B178: a score title, end
        if side.get("result") == "score":                    # B178: the numbers the label stage checked, the winner
            exp_scores = _numbers(code, ending)              # the seat of the side ahead (seats 1..n: port k = seat k)
            top = max(exp_scores)
            exp_winner = exp_scores.index(top) + 1 if exp_scores.count(top) == 1 else None
        else:
            exp_scores, exp_winner = _expected(b, side, _role_class(ending))
        cells.add(f"{ending}: ended with its class", [got.get("state"), got.get("class")], ["ended", want_cls],
                  got.get("state") == "ended" and got.get("class") == want_cls)
        cells.add(f"{ending}: scores", got.get("scores"), exp_scores, got.get("scores") == exp_scores)
        if exp_winner is not None or side.get("result") == "score":
            cells.add(f"{ending}: winner", got.get("winner"), exp_winner, got.get("winner") == exp_winner)
        cells.add(f"{ending}: ended within (s)", took, f"<= {BARS['ended_after_load_s'][0]}",
                  took <= BARS["ended_after_load_s"][0])
        hub("POST", "party-minigame-end")
        _wait(lambda x: x.get("closed") or x.get("state") == "none", 20)
        launch = next((x for x in party_rows(r1) if x.get("step") == "minigame_launch"), {})
        cells.add(f"{ending}: keys_written", launch.get("keys_written"), True, launch.get("keys_written") is True)
    hub("POST", "stop")
    after = files_digest(b)
    changed = files_changed(before, after)                       # B196: each named by root and kind
    cells.add("every file after = before", changed, [], not changed)
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


PAD_WORDS = {                                                  # B162: the buttons by the pads' class
    "playstation": {"practice": "△", "play": "✕", "back": "the Select button (Share)"},
    "xbox": {"practice": "Y", "play": "A", "back": "the View button (Back)"},
    "both": {"practice": "△ (Y on an Xbox pad)", "play": "✕ (A on an Xbox pad)",
             "back": "the Select button (Share; View on an Xbox pad)"},
}


def pad_classes() -> list[str] | None:
    """The `class` of each pad in the onn's last heartbeat row with pads in `pad_slots`; None when there is none."""
    p = project() / LOGS["heartbeat"]
    try:
        with p.open("rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4_000_000))
            tail = f.read().decode(errors="replace").splitlines()
    except OSError:
        return None
    for ln in reversed(tail):
        if '"pad_slots"' not in ln:
            continue
        try:
            slots = json.loads(ln).get("pad_slots")
        except ValueError:
            continue
        if isinstance(slots, list) and slots:
            return [str(x.get("class") or "") for x in slots if isinstance(x, dict)]
    return None


def pad_words(classes: list[str] | None) -> str:
    """PlayStation words for `sony`, Xbox words otherwise, both if mixed, PlayStation if no row yet."""
    if not classes:
        return "playstation"
    sony = [c == "sony" for c in classes]
    return "playstation" if all(sony) else "xbox" if not any(sony) else "both"


def solo_lines(b: dict, words: str = "playstation") -> list[str]:
    n = b["players"]
    who = "you alone with two pads, or two of you" if n == 2 else "four people, or you with four pads"
    w = PAD_WORDS[words]
    return [
        "YOU, now: open Games, 'PrivyParty (1)', Launch on Companion, Start Fresh; play the board with "
        f"{who} until a mini game for {n} comes up (this game, the only card shown; if two cards show, stop and "
        "tell me).",
        f"YOU, now: on its load screen press {w['practice']} for a practice, stay in it at least ten seconds, leave "
        f"it with {w['back']}, then wait a few seconds on the load screen before pressing {w['play']} to play it for "
        "real, and play it to its end.",
        "YOU, now: when you are back on the board, reply with who won (P1, P2" + (", P3 or P4" if n == 4 else "") + ").",
    ]


LAUNCH_LOG = re.compile(r"^(\d{8}-\d{6})-(.+)\.log$")
NOT_A_LAUNCH = ("party", "ps2", "gamecube")                   # the board's, PCSX2's and Dolphin's own logs


def launched_since(since: float) -> list[str]:
    """The game id of every RetroArch launch logged at or after `since` (the manager's <time>-<game id>.log)."""
    out_ = []
    for p in sorted((project() / "logs/games").glob("*.log")):
        m = LAUNCH_LOG.match(p.name)
        if not m or m.group(2) in NOT_A_LAUNCH:
            continue
        try:
            t = time.mktime(time.strptime(m.group(1), "%Y%m%d-%H%M%S"))
        except (ValueError, OverflowError):
            continue
        if t >= int(since):
            out_.append(m.group(2))
    return out_


def only_clear() -> dict:
    """B162: the one-title setting cleared on the hub (solo --read, close)."""
    return hub("POST", "party-minigame-only", {"clear": "1"}, timeout=10)


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
        only = hub("POST", "party-minigame-only", {"game": b["game"]}, timeout=10)    # B162: this title alone
        listed = [m for m in (hub("GET", "party-minigames")["body"].get("minigames") or [])
                  if m.get("players") == b["players"]]
        if (only["code"] != 200 or only["body"].get("only") is not True or only["body"].get("players") != b["players"]
                or len(listed) != 1 or (b.get("title") and listed[0].get("title") != b["title"])):
            only_clear()
            raise Refused(f"the one-title setting was not taken (the hub lists {len(listed)} titles for "
                          f"{b['players']} players): nothing asked of the user")
        saves_before(code, b, again=False)                   # B162: the in-game saves' before, if bench left none
        bl = _board_log()
        mark = {k: _count(project() / v) for k, v in LOGS.items()}
        mark["since_unix"] = time.time()                     # B162: the launches after this are the solo's
        mark["board_log"] = bl.name if bl else None
        mark["board_lines"] = _count(bl) if bl else 0
        mark["video_bytes"] = (project() / LOGS["video"]).stat().st_size if (project() / LOGS["video"]).is_file() else 0
        if not mark_path.is_file():
            # B169: solo's first run writes the files' before bench writes (a title already added has no bench; a new
            # title's bench before is kept), so close compares the users' files after every solo
            fb = home(code) / "files_before.json"
            if b.get("described") or not fb.is_file():
                write_if_changed(fb, json.dumps(files_digest(b), sort_keys=True))
            write_if_changed(mark_path, json.dumps(mark, sort_keys=True))
        for ln in solo_lines(b, pad_words(pad_classes())):
            out(ln)
        out(f"solo {code}: WAITING — after the user's reply: solo {code} --read --winner <seat>")
        return 3
    only_clear()                                             # B162: the setting cleared first, whatever the cells
    mark = read_json(mark_path)
    if not mark:
        raise Refused("solo's lines were not given yet: run solo first")
    if str(a["winner"]).strip().lower() == "draw":            # B178: a score title's tie (the board's draw)
        if b.get("result") != "score":
            raise Usage("--winner draw is for a score title")
        winner = None
    else:
        winner = int(a["winner"])
    cells = Cells()
    ids = launched_since(float(mark.get("since_unix") or 0))  # B162: compared in memory, neither id written
    this = sum(1 for g in ids if g == str(b["game"])[:80])
    cells.add("the mini game played was this title", {"this title": this, "another": len(ids) - this},
              "this title >= 1, another 0", this >= 1 and len(ids) == this)
    rows = party_rows(mark["party"])
    sw = [x for x in rows if x.get("step") == "minigame_stream" and x.get("planned")]
    cells.add("planned switches", len(sw), f">= {BARS['switches_read_min'][0]} (a practice in and out, the go, the end)",
              len(sw) >= BARS["switches_read_min"][0])
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
    starts = [None if t is None else t - float(x.get("seconds") or 0) for t, x in zip(times, sw)]
    read_i, listed = [], []                                  # B162: B150's S — a switch followed within 4 s is listed
    for i, t in enumerate(times):
        nxt = starts[i + 1] if i + 1 < len(sw) else None
        if t is not None and nxt is not None and nxt - t < BARS["listed_within_s"][0]:
            listed.append(i)
        else:
            read_i.append(i)
    go = max((i for i, x in enumerate(sw) if x.get("window") == "minigame"), default=None)     # B197: the real match
    end = next((i for i, x in enumerate(sw) if go is not None and i > go and x.get("window") == "board"), None)
    role = {i: ("the go" if i == go else "the end" if i == end else "a practice's") for i in range(len(sw))}
    real = [r for r, i in (("the go", go), ("the end", end)) if i is not None and i in read_i]
    cells.add("the real match's go and end read for S (a practice's may be listed)",
              {"read": [f"{i + 1} ({role[i]})" for i in read_i], "listed": [f"{i + 1} ({role[i]})" for i in listed]},
              BARS["real_switches_read"][0], real == BARS["real_switches_read"][0])
    for i in read_i:
        t = times[i]
        nxt = starts[i + 1] if i + 1 < len(sw) else None
        until = (t or 0) + BARS["s_span_s"][0] if nxt is None else min(nxt, (t or 0) + BARS["s_span_s"][0])
        after = [(ts, r) for ts, r in hbt if t is not None and ts is not None and t <= ts < until]
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
    card = next((re.match(r"^cards (\d+), chose", ln) for ln in blines if re.match(r"^cards (\d+), chose", ln)), None)
    n_cards = int(card.group(1)) if card else None             # B169: the one-title setting, by the board's own line
    cells.add("the board showed one card", n_cards, 1, n_cards == 1)
    ended = [x for x in rows if x.get("step") == "minigame_ended"]
    last = ended[-1] if ended else {}
    hub_winner = last.get("winner")
    if hub_winner is None and last.get("scores"):
        sc = last["scores"]
        hub_winner = sc.index(max(sc)) + 1 if sc.count(max(sc)) == 1 else None
    cells.add("the hub's result = the winner the user named", hub_winner, winner, hub_winner == winner)
    note = ""
    if listed:
        note = "Listed, not read (the next switch began less than 4 s after): " + "; ".join(
            f"switch {i + 1} ({role[i]}, to the {sw[i].get('window') or '?'}, {sw[i].get('seconds')} s; the next began "
            f"{round(starts[i + 1] - times[i], 2)} s after)" for i in listed) + "."
    return finish(code, "solo", cells, digest({"after": before_solo, "mark": mark, "winner": winner}), note=note)


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
    only_clear()                                             # B162: the one-title setting cleared (if the hub is up)
    hub("POST", "stop")
    lines = flags(False)
    cells.add("the companion's lines", lines, BARS["flag_lines_found"][0], lines == BARS["flag_lines_found"][0])
    cells.add("the lines as found at register", digest(_companion_lines()) == b.get("found_lines"), True,
              digest(_companion_lines()) == b.get("found_lines"))
    units = _active_units()
    cells.add("active units", units, ["privyhub-companion", "privyhub-diag"],
              units == ["privyhub-companion", "privyhub-diag"])
    before = read_json(home(code) / "files_before.json")
    s_before = read_json(home(code) / "saves_before.json")   # B162: the title's in-game saves, recorded only
    s_after = ingame_saves(b)
    saves = saves_recorded(s_before, s_after)
    own_saves = set(s_after) | set(s_before or {})
    changed = None
    if before is not None:                                   # bench ran: its before
        after = files_digest(b)
        changed = files_changed(before, after, skip=own_saves)   # B196: each by root, kind and hashed name
        cells.add("every file = bench's before", changed, [], not changed)
    note = "The title's own in-game saves (recorded, never a cell): " + (
        "; ".join(f"{r['save']}: {r['is']}" for r in saves) if saves else "none found") + "."
    if changed is not None:                                  # B196: what changed, in the page, before anything ends
        note += (" Changed since bench's before: " + ("; ".join(f"{c['kind']} in {c['root']} ({c['file']}, {c['is']})"
                                                               for c in changed) if changed else "none")
                 + ". Left out of the comparison: " + LEFT_OUT + ".")
    rc = finish(code, "close", cells, digest({"register": b.get("register_inputs"), "before": digest(before)}),
                note=note, recorded={"in_game_saves": saves, **({"changed": changed} if changed is not None else {})})
    end_solo_mark(code)                                      # B172: then the next solo writes its own mark and befores
    for pic in sorted(ask_folder().glob(f"{code}_*.png")):   # B187: the picture shown to the user, removed
        pic.unlink()
    return rc


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
    a: dict = {"check": False, "collect": [], "read": False, "readings": []}
    i = 0
    while i < len(rest):
        k = rest[i]
        if stage == "label" and "=" in k and not k.startswith("--"):     # B178: the session's readings
            a["readings"].append(k)
            i += 1
            continue
        if k in ("--check", "--read"):
            a[k[2:]] = True
            i += 1
            continue
        if k in ("--players", "--system", "--result", "--find", "--rules-players", "--setup", "--collect", "--winner",
                 "--word", "--max-score") \
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
        return {"label": cmd_label, "learn": cmd_learn, "rehearse": cmd_rehearse, "bench": cmd_bench,
                "solo": cmd_solo, "close": cmd_close}[stage](code, a)
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
