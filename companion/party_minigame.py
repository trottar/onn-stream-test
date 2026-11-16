"""B110: the hub's party mini game — an emulator title played from inside the board game, its result read from the
title's own end screen, everything handed back.

Only with PRIVYHUB_PARTY=1 (the board as the game session, B108) **and** PRIVYHUB_H7=1 (the end-screen watcher and
the rules folder, B103 / B105): `plugins/games.py` imports this module then; either absent = today (no route).

  GET  party-minigames            the titles whose rules folder holds a version-2 spec, a kept begin state and a
                                  sidecar <game id>.party.json ({"players": n, "scores": {end class: [n numbers]}});
                                  ids opaque to the board
  POST party-minigame-start       ?id=<token>&seats=a,b — answers at once ("starting"); a worker: the board's session
                                  set aside (it keeps running), the title launched by the manager, paused, the pads
                                  routed (seat a's pad → port 1 …), the stream switched to the title (if up), B103's
                                  start (the begin state, the watch), the pause released → "playing"
  GET  party-minigame-result      starting / playing (recognised) / ended (class, scores in the order of the seats
                                  given) / given_up (why) — never a guess
  POST party-minigame-end         the watch stopped, the title stopped, the route cleared, the board's session back,
                                  the stream switched back (if up); safe to call twice; also done by the hub itself
                                  when the board dies, END / another launch reach stop, or the caller does not come back

One row per step in the party log (logs/games/party.jsonl), field names and numbers only.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

import h7_live_read as live
import party_session as party

PLAY_LIMIT_S = 900.0        # a match not ended within this is given up (a draw to the board)
UNKNOWN_LIMIT_S = 30.0      # an unknown screen read this long running is given up
POLL_GONE_S = 120.0         # no result call this long while playing: the caller is gone, the hub ends it
END_WAIT_S = 60.0           # no end call this long after a final state: the hub ends it
TICK = 0.5
FINAL = ("ended", "given_up")


class PartyMinigames:
    def __init__(self, plugin: Any, environ=os.environ, clock=time.monotonic):
        self.p = plugin
        self.emu = plugin._emulator
        self.environ = environ
        self.clock = clock
        self._salt = os.urandom(8)
        self._lock = threading.Lock()
        self.mg: dict | None = None            # the current (or last) mini game
        self.play_limit_s, self.unknown_limit_s = PLAY_LIMIT_S, UNKNOWN_LIMIT_S
        self.poll_gone_s, self.end_wait_s, self.tick = POLL_GONE_S, END_WAIT_S, TICK
        self.stream_needed = True               # B112's bench sets False (no stream, no switch)

    # --- rows ---------------------------------------------------------------------------------------------------------
    def row(self, fields: dict) -> None:
        party.row(self.emu._project_path, fields)

    # --- the list -----------------------------------------------------------------------------------------------------
    def _token(self, game: str) -> str:
        return "mg_" + hashlib.sha256(self._salt + game.encode()).hexdigest()[:12]

    def _entries(self) -> dict[str, dict]:
        """{token: {"game", "players", "scores", "classes"}} for every title that has all three files."""
        folder = live.rules_folder(self.environ)
        out: dict[str, dict] = {}
        try:
            names = sorted(p.name for p in folder.iterdir())
        except OSError:
            return out
        from h7_minigame import endscreen
        for name in names:
            if not name.endswith(".endscreen.json"):
                continue
            game = name[: -len(".endscreen.json")]
            if not live._ID.match(game):
                continue
            try:
                spec, _arrays = endscreen().load_spec(folder / name)
                state = folder / f"{game}.state"
                if not state.is_file() or state.stat().st_size <= 0:
                    continue
                side = json.loads((folder / f"{game}.party.json").read_text(encoding="utf-8"))
                n = int(side["players"])
                scores = {str(k): [int(x) if float(x).is_integer() else float(x) for x in v]
                          for k, v in dict(side["scores"]).items()}
                ends = list(spec["end_classes"])
                if n < 1 or n > 4 or sorted(scores) != sorted(ends) or any(len(v) != n for v in scores.values()):
                    continue
                if self.p._find_game_by_id(game) is None:
                    continue
            except Exception:
                continue
            out[self._token(game)] = {"game": game, "players": n, "scores": scores, "start_class": spec["start_class"]}
        return out

    def listing(self) -> dict:
        return {"ok": True, "minigames": [{"id": t, "players": e["players"]} for t, e in sorted(self._entries().items())]}

    # --- start --------------------------------------------------------------------------------------------------------
    def start(self, token: str, seats_text: str, bench: bool = False) -> dict:
        self.stream_needed = not bench           # B112: with the bench word, the watcher runs with no stream
        if not party.active(self.emu):
            self.row({"step": "minigame_refused", "why": "the board game is not the running session"})
            raise ValueError("the board game is not the running session")
        with self._lock:
            if self.mg is not None and not self.mg["closed"]:
                raise ValueError("a mini game is already on")
        entry = self._entries().get(str(token or "").strip())
        if entry is None:
            raise ValueError("no such mini game")
        try:
            seats = [int(x) for x in str(seats_text or "").split(",") if x.strip()]
        except ValueError:
            raise ValueError("seats are numbers 1-4, comma-separated") from None
        if len(seats) != entry["players"] or len(set(seats)) != len(seats) or not all(1 <= s <= 4 for s in seats):
            raise ValueError(f"this mini game takes {entry['players']} different seats, 1-4")
        mg = {"state": "starting", "seats": seats, "entry": entry, "recognised": None, "class": None,
              "scores": None, "why": None, "t0": self.clock(), "last_poll": self.clock(), "final_at": None,
              "stash": None, "launched": False, "routed": False, "ended_by": None, "closed": False}
        with self._lock:
            self.mg = mg
        self.row({"step": "minigame_start", "seats": seats, "players": entry["players"]})
        threading.Thread(target=self._run, args=(mg,), daemon=True, name="party-minigame").start()
        return {"ok": True, "state": "starting", "seats": seats}

    def _bridge(self):
        try:
            return self.p._native_stream._session_io.controller
        except Exception:
            return None

    def _switch_stream(self, which: str) -> None:
        if not self.stream_needed or not self.p._recovery_stream_active():
            self.row({"step": "minigame_stream", "window": which, "switched": False, "why": "the stream is not up"})
            return
        t0 = self.clock()
        try:
            self.p._recovery_full_start_encoder()
            self.row({"step": "minigame_stream", "window": which, "switched": True,
                      "seconds": round(self.clock() - t0, 3)})
        except Exception as exc:
            self.row({"step": "minigame_stream", "window": which, "switched": False, "why": str(exc)[:160]})

    def _final(self, mg: dict, state: str, **fields) -> None:
        with self._lock:
            if mg["state"] in FINAL or mg["closed"]:
                return
            mg.update(state=state, final_at=self.clock(), **fields)
        self.row({"step": "minigame_" + state, **{k: v for k, v in fields.items() if k in ("class", "scores", "why")}})

    def _run(self, mg: dict) -> None:
        emu = self.emu
        try:
            with emu.lock:                       # the start, serialised with stop / Home / the onn's reads
                if mg["state"] != "starting":
                    return
                mg["stash"] = emu._party_stash_begin()
                emu._party_mg_stop_hook = lambda: self._end_by_stop(mg)
                game = self.p._find_game_by_id(mg["entry"]["game"])
                emu.launch(game)
                mg["launched"] = True
                self.row({"step": "minigame_launch", "pid_owned": True})
                emu.pause()
                bridge = self._bridge()
                if bridge is not None:
                    bridge.set_party_route({s - 1: k for k, s in enumerate(mg["seats"])})
                    mg["routed"] = True
                self.row({"step": "minigame_route", "ports": {str(k + 1): s for k, s in enumerate(mg["seats"])},
                          "routed": mg["routed"]})
                self._switch_stream("minigame")
                runner = self.p._h7_minigame_runner()
                runner.start("1", "", bench=not self.stream_needed)
                self.row({"step": "minigame_watch", "loaded": True})
                emu.resume()
                with self._lock:
                    if mg["state"] == "starting":
                        mg["state"] = "playing"
                self.row({"step": "minigame_playing"})
        except Exception as exc:
            self._final(mg, "given_up", why=f"the mini game did not start: {str(exc)[:160]}")
        self._watch(mg)

    # --- the watch ----------------------------------------------------------------------------------------------------
    def _watch(self, mg: dict) -> None:
        runner = self.p._h7_minigame_runner()
        unknown_since = None
        while True:
            time.sleep(self.tick)
            with self._lock:
                if self.mg is not mg or mg["closed"]:
                    return
                state = mg["state"]
            now = self.clock()
            stash = mg.get("stash") or {}
            board = stash.get("process")
            if board is not None and board.poll() is not None:
                self._final(mg, "given_up", why="the board stopped")
                self.end(by="hub: the board stopped")
                return
            if state in FINAL:
                if now - (mg["final_at"] or now) >= self.end_wait_s:
                    self.end(by="hub: no end call")
                    return
                continue
            if state != "playing":
                continue
            if now - mg["last_poll"] >= self.poll_gone_s:
                self._final(mg, "given_up", why="the board stopped asking")
                continue
            if now - mg["t0"] >= self.play_limit_s:
                self._final(mg, "given_up", why=f"no end within {self.play_limit_s:.0f} s")
                continue
            try:
                r = runner.result()
            except Exception:
                continue
            with self._lock:
                mg["recognised"] = r.get("recognised")
            if r.get("recognised") is False:
                self._final(mg, "given_up", why="the title's start screen was not recognised")
                continue
            if r.get("state") == "ended":
                cls = r.get("class")
                scores = mg["entry"]["scores"].get(cls)
                if scores is None:
                    self._final(mg, "given_up", why="an end the sidecar does not name")
                else:
                    self._final(mg, "ended", **{"class": cls, "scores": list(scores)})
                continue
            if r.get("state") in ("no_game", "idle", "no_spec"):
                self._final(mg, "given_up", why="the watch stopped")
                continue
            if r.get("class") == "unknown":
                unknown_since = unknown_since if unknown_since is not None else now
                if now - unknown_since >= self.unknown_limit_s:
                    self._final(mg, "given_up", why=f"an unknown screen for {self.unknown_limit_s:.0f} s")
            else:
                unknown_since = None

    # --- result / end -------------------------------------------------------------------------------------------------
    def result(self) -> dict:
        with self._lock:
            mg = self.mg
            if mg is None:
                return {"ok": True, "state": "none"}
            mg["last_poll"] = self.clock()
            return {"ok": True, "state": mg["state"], "seats": mg["seats"], "recognised": mg["recognised"],
                    "class": mg["class"], "scores": mg["scores"], "why": mg["why"], "closed": mg["closed"],
                    "since_s": round(self.clock() - mg["t0"], 1)}

    def end(self, by: str = "board") -> dict:
        emu = self.emu
        with emu.lock:
            with self._lock:
                mg = self.mg
                if mg is None:
                    return {"ok": True, "state": "none", "ended": False}
                if mg["closed"]:
                    return {"ok": True, "state": mg["state"], "scores": mg["scores"], "ended": True, "again": True}
            if mg["state"] not in FINAL:
                self._final(mg, "given_up", why=f"ended before a result ({by})")
            try:
                self.p._h7_minigame_runner().stop()
            except Exception:
                pass
            if emu._party_mg_stop_hook is not None:
                emu._party_mg_stop_hook = None
            if mg.get("launched") and emu._party_stash is not None and emu.process is not None:
                try:
                    emu.stop()                   # the title, RetroArch's own stop (the hook already cleared)
                except Exception as exc:
                    self.row({"step": "minigame_end", "title_stop_failed": str(exc)[:160]})
            if mg.get("routed"):
                bridge = self._bridge()
                if bridge is not None:
                    bridge.set_party_route(None)
            if emu._party_stash is not None:
                emu._party_stash_end()
                self.row({"step": "minigame_restore", "board_alive": emu.process is not None
                          and emu.process.poll() is None})
                if by != "stop":                     # END / another launch: the stream ends with the session anyway
                    self._switch_stream("board")
            with self._lock:
                mg["ended_by"] = by
                mg["closed"] = True
            self.row({"step": "minigame_end", "by": by})
            return {"ok": True, "state": mg["state"], "scores": mg["scores"], "ended": True}

    def _end_by_stop(self, mg: dict) -> dict:
        """The manager's stop with a mini game on (END, another launch, launch_orphaned): the mini game first, then
        the board's own stop (F10)."""
        self._final(mg, "given_up", why="ended from the onn")
        self.end(by="stop")
        return self.emu.stop()
