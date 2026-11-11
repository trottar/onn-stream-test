"""B99 (H7): the live read — who is ahead in the game the hub is running now, read from its memory by a kept rule.

Only with PRIVYHUB_H7=1 (`plugins/games.py` imports this module then; absent / 0 = today: the route does not exist).
`GET /plugins/games/h7-read` → for the running RetroArch game (PS1, SNES, N64) the rule
`<rules folder>/<the hub's game id>.json` (B93's rule JSON; the folder `~/privyhub_h7/rules` or PRIVYHUB_H7_RULES) is
read through the companion's own RetroArch command path, holding the manager's lock (the save / load / launch / status
paths' lock): GET_STATUS, then one READ_CORE_RAM / READ_CORE_MEMORY per field — nothing else is sent (no pause, save,
load, write or cheat). The whole read is bounded (READ_BOUND s); at most one read per FLOOR s (a sooner call gets the
last answer with its age). Every read sent is one row in logs/games/h7_reads.jsonl.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

LOCK_WAIT = 0.3          # s: the manager's lock waited for at most this long (a save or a load holds it)
READ_BOUND = 0.6         # s: the whole read (the lock, GET_STATUS and every field) — past it, not read
FLOOR = 0.25             # s: at most one read per FLOOR; a sooner call gets the last answer with its age
SYSTEMS = ("ps1", "snes", "n64")
LOG_RELATIVE = "logs/games/h7_reads.jsonl"
_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class Busy(RuntimeError):
    """A plain error answered as 502 (the service maps RuntimeError so)."""


def enabled(environ=os.environ) -> bool:
    return (environ.get("PRIVYHUB_H7") or "").strip() == "1"


def rules_folder(environ=os.environ) -> Path:
    override = (environ.get("PRIVYHUB_H7_RULES") or "").strip()
    return Path(override).expanduser() if override else Path.home() / "privyhub_h7" / "rules"


def parse_rule(rule: Any) -> dict:
    """B93's rule JSON, checked as tools/h7_minigame_proof.parse_rule checks it. ValueError on anything else."""
    if not isinstance(rule, dict):
        raise ValueError("the rule is not a JSON object")
    memory = rule.get("memory", "ram")
    if memory not in ("ram", "memory"):
        raise ValueError("memory is ram or memory")
    if "address" in rule and not rule.get("players"):              # B94's single winner field
        n = int(rule.get("bytes", 1))
        if n not in (1, 2, 4) or not isinstance(rule.get("values"), dict) or len(rule["values"]) < 2:
            raise ValueError("a single-field rule needs 1, 2 or 4 bytes and a value per winner")
        return {"fields": [{"name": "field", "address": int(str(rule["address"]), 0), "bytes": n,
                            "endian": rule.get("endian", "little")}],
                "values": {str(k): int(v) for k, v in rule["values"].items()},
                "none_value": None if rule.get("none_value") is None else int(rule["none_value"]), "memory": memory}
    players = rule.get("players")
    if not isinstance(players, list) or len(players) < 2:
        raise ValueError("the rule needs at least two players")
    fields = []
    for p in players:
        n = int(p.get("bytes", 1))
        if n not in (1, 2, 4):
            raise ValueError("a player's value is 1, 2 or 4 bytes")
        if p.get("endian", "little") not in ("little", "big"):
            raise ValueError("endian is little or big")
        fields.append({"name": str(p["name"]), "address": int(str(p["address"]), 0), "bytes": n,
                       "endian": p.get("endian", "little")})
    if rule.get("winner", "max") not in ("max", "min"):
        raise ValueError("winner is max or min")
    none_when = rule.get("none_when")
    if not (none_when is None or none_when == "equal"
            or (isinstance(none_when, dict) and isinstance(none_when.get("floor"), int))):
        raise ValueError('none_when is "equal" or {"floor": V}')
    return {"fields": fields, "winner": rule.get("winner", "max"), "none_when": none_when, "memory": memory}


def answer(r: dict, values: dict[str, int]) -> tuple[str | None, str | None]:
    """B93 / B95's reading: (winner, reason) — reason "no winner yet", "tie" or a single field's unknown value."""
    if "values" in r:
        v = values["field"]
        if r["none_value"] is not None and v == r["none_value"]:
            return None, "no winner yet"
        hits = [k for k, x in r["values"].items() if x == v]
        return (hits[0], None) if len(hits) == 1 else (None, "a value the rule does not name")
    nw = r.get("none_when")
    if nw == "equal" and len(set(values.values())) == 1:
        return None, "no winner yet"
    if isinstance(nw, dict) and all(v <= nw["floor"] for v in values.values()):
        return None, "no winner yet"
    best = (max if r["winner"] == "max" else min)(values.values())
    top = [k for k, v in values.items() if v == best]
    return (top[0], None) if len(top) == 1 else (None, "tie")


class LiveRead:
    def __init__(self, emulator: Any, project_path, environ=os.environ, clock=time.monotonic):
        self._emu = emulator
        self._project_path = project_path
        self._environ = environ
        self._clock = clock
        self._lock = threading.Lock()
        self._last: tuple[float, str, dict] | None = None

    # --- the route ---------------------------------------------------------------------------------------------------
    def read(self) -> dict:
        game, system, kind = self._running()
        if game is None:
            return {"ok": True, "running": False}
        if kind == "pcsx2":
            raise ValueError("reading a PS2 game's memory is not supported yet")
        if kind == "dolphin":
            raise ValueError("reading a GameCube game's memory is not supported yet")
        if system not in SYSTEMS:
            raise ValueError("reading this system's game memory is not supported yet")
        rule = self._rule(game)
        with self._lock:
            now = self._clock()
            if self._last is not None and self._last[1] == game and now - self._last[0] < FLOOR:
                return dict(self._last[2], cached=True, age_ms=round((now - self._last[0]) * 1000.0, 1))
            try:
                out = self._read(game, rule)
            except (Busy, RuntimeError) as exc:
                self._row({"game": game, "error": str(exc)})
                self._last = None
                raise
            self._last = (self._clock(), game, out)
            return dict(out)

    def _running(self) -> tuple[str | None, str | None, str | None]:
        emu = self._emu
        if not emu.lock.acquire(timeout=LOCK_WAIT):
            raise Busy("the game is busy (a save or a load); not read")
        try:
            emu._refresh_process()
            proc = emu.process
            if proc is None or proc.poll() is not None or not isinstance(emu.active_game, dict):
                return None, None, None
            return (str(emu.active_game.get("id", "")), str(emu.active_game.get("system", "")),
                    getattr(emu, "_launch_kind", None))
        finally:
            emu.lock.release()

    def _rule(self, game: str) -> dict:
        if not _ID.match(game) or game in (".", ".."):
            raise ValueError("no rule for this game")
        path = rules_folder(self._environ) / f"{game}.json"
        if not path.is_file():
            raise ValueError("no rule for this game")
        try:
            return parse_rule(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"the rule for this game cannot be read: {exc}") from exc

    def _read(self, game: str, rule: dict) -> dict:
        emu = self._emu
        t0 = self._clock()
        if not emu.lock.acquire(timeout=LOCK_WAIT):
            raise Busy("the game is busy (a save or a load); not read")
        try:
            def left() -> float:
                rest = READ_BOUND - (self._clock() - t0)
                if rest <= 0.02:
                    raise Busy("the game's memory did not answer in time; not read")
                return rest

            status = self._ask(emu, "GET_STATUS", left())
            if not status.upper().startswith("GET_STATUS "):
                raise Busy("an unexpected answer from RetroArch; not read")
            paused = status.upper().startswith("GET_STATUS PAUSED")
            word = "READ_CORE_RAM" if rule["memory"] == "ram" else "READ_CORE_MEMORY"
            values: dict[str, int] = {}
            for f in rule["fields"]:
                text = self._ask(emu, f"{word} {f['address']:x} {f['bytes']}", left())
                parts = text.split()
                if len(parts) >= 3 and parts[0] == word and parts[2] == "-1":
                    raise Busy(f"the game's memory has no address {f['address']:#x}")
                if (len(parts) != f["bytes"] + 2 or parts[0] != word
                        or int(parts[1], 16) != f["address"]):
                    raise Busy("an unexpected answer from RetroArch; not read")
                raw = bytes(int(b, 16) for b in parts[2:])
                values[f["name"]] = int.from_bytes(raw, f["endian"])
        except ValueError as exc:                               # a malformed hex answer
            raise Busy("an unexpected answer from RetroArch; not read") from exc
        finally:
            emu.lock.release()
        read_ms = round((self._clock() - t0) * 1000.0, 1)
        winner, reason = answer(rule, values)
        out = {"ok": True, "game": game, "running": True, "paused": paused, "values": values, "winner": winner,
               "reason": reason, "read_ms": read_ms}
        self._row({"game": game, "values": values, "winner": winner, "reason": reason, "paused": paused,
                   "read_ms": read_ms})
        return out

    @staticmethod
    def _ask(emu: Any, command: str, wait: float) -> str:
        try:
            text = emu._retroarch_network_request(command, expect_response=True, timeout=wait, retries=1)
        except RuntimeError as exc:                             # EmulatorError: no answer within the wait
            raise Busy("the game's memory did not answer in time; not read") from exc
        if not text:
            raise Busy("the game's memory did not answer in time; not read")
        return text

    def _row(self, fields: dict) -> None:
        try:
            path = Path(self._project_path(LOG_RELATIVE))
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"time_unix": round(time.time(), 3), **fields}, sort_keys=True) + "\n")
        except OSError:
            pass
