"""B110: the hub's party mini game — an emulator title played from inside the board game, its result read from the
title's own end screen, everything handed back.

Only with PRIVYHUB_PARTY=1 (the board as the game session, B108) **and** PRIVYHUB_H7=1 (the end-screen watcher and
the rules folder, B103 / B105): `plugins/games.py` imports this module then; either absent = today (no route).

  GET  party-minigames            the titles whose rules folder holds a version-2 spec, a kept begin state and a
                                  sidecar <game id>.party.json ({"players": n, "scores": {end class: [n numbers]}});
                                  ids opaque to the board
  POST party-minigame-start       ?id=<token>&seats=a,b — answers at once ("starting"); the mini game's own actor: the
                                  board's session set aside (it keeps running), the title launched by the manager,
                                  paused, the pads routed (seat a's pad → port 1 …), the stream switched to the title
                                  (if up), B103's start (the begin state, the watch), the pause released → "playing"
  GET  party-minigame-result      starting / playing (recognised) / ended (class, scores in the order of the seats
                                  given) / given_up (why) — never a guess
  POST party-minigame-end         taken at once; the actor: the watch stopped, the title stopped, the route cleared,
                                  the board's session back, the stream switched back (if up); safe to call twice;
                                  also done by the hub itself when the board dies, END / another launch reach stop,
                                  the caller does not come back, or the start is stuck

B114 (the hang PP-H3's second mini game hit): **no lock is held across a launch, a stream start or stop, or a wait on
another thread.** The start held the manager's lock across the stream switch, whose end waited on the live bitrate
controller's lock, held by a client-health report waiting on the manager's lock. Now each manager call takes the
manager's lock for that call only; the stream switch runs on a helper thread with nothing held and is waited for at
most SWITCH_LIMIT_S; the layer's own lock guards its fields only. While a mini game is on, **every route answers
within 2 s**: `status` / `native-stream-status` from a snapshot when a part cannot be read at once, the result from
the mini game's own state, Home / RESUME / END and the board's end **taken at once** onto the mini game's own queue
and **acted on in order** by its actor (RESUME answers with its own start's answer, which the onn needs). A start
still `starting` after START_LIMIT_S is given up by the hub; END always works — if the actor is stuck in a step past
STEP_GRACE_S the end runs without it.

One row per step in the party log (logs/games/party.jsonl), field names and numbers only.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

import h7_live_read as live
import party_session as party

PLAY_LIMIT_S = 900.0        # a match not ended within this is given up (a draw to the board)
UNKNOWN_LIMIT_S = 30.0      # an unknown screen read this long running is given up
POLL_GONE_S = 120.0         # no result call this long while playing: the caller is gone, the hub ends it
END_WAIT_S = 60.0           # no end call this long after a final state: the hub ends it
TICK = 0.5
FINAL = ("ended", "given_up")
# B114
START_LIMIT_S = 30.0        # a mini game still starting after this is given up by the hub (a normal start ~5 s)
SWITCH_LIMIT_S = 15.0       # one stream switch's bound (the real one ~1-4 s)
STEP_GRACE_S = 3.0          # END waits this long for the actor to take it before the end runs without the actor
TAKE_WAIT_S = 1.5           # a taken Home / END / board end answers with its own answer if done within this
RESUME_WAIT_S = 25.0        # a taken RESUME waits its turn this long (the onn's read timeout is 30 s)
READ_WAIT_S = 1.5           # a status read waits this long before the last snapshot answers
EMU_TRY_S = 0.2             # the manager's lock is tried in steps of this, an END checked between
MANAGER_BOUND_S = 10.0      # the end's manager calls: give up the wait after this (the title then ended directly)
# B115
PLANNED_GRACE_S = 3.0       # the planned-switch window stays open this long after the switch's start returns
# the onn's calls taken while a mini game is on (route → kind)
TAKEN = {"native-stream-stop": "home", "native-stream-start": "resume_start", "native-stream-ready": "resume_ready",
         "stop": "end"}

_local = threading.local()


def inside() -> bool:
    """True on the mini game's own threads running a taken call or a bounded read (they take today's path)."""
    return bool(getattr(_local, "inside", False))


class _Abort(Exception):
    """The start's steps stop: an end was asked for (or done) while starting."""


class PlannedSwitch:
    """B115: the recovery told that a capture restart is planned (`recovery._planned_switch`, set only here): while
    the window is open the client's video-stall datagrams (stall / stall end) and its desync are not taken — no
    client_stall, no desync_pause, no stall save, no stall_handover_v2, no key to the board. The window opens just
    before a mini game's switch and closes PLANNED_GRACE_S after the switch's start returns. What still counts: the
    controller's silence (the pads' packets stopping), a stall that outlasts the window, the recovery's own monitor."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._lock = threading.Lock()
        self.seq = 0
        self.windows: dict[int, dict] = {}        # each switch's own window (two may overlap by their grace)

    def open(self, which: str, bound_s: float) -> int:
        with self._lock:
            self.seq += 1
            now = self.clock()
            self.windows[self.seq] = {"which": which, "opened_at": now, "until": now + bound_s,
                                      "counts": {"stall": 0, "end": 0, "desync": 0}}
            for old in [k for k in self.windows if k <= self.seq - 8]:
                del self.windows[old]
            return self.seq

    def close_after(self, seq: int, grace_s: float) -> float | None:
        with self._lock:
            w = self.windows.get(seq)
            if w is None:
                return None
            w["until"] = min(w["until"], self.clock() + grace_s)
            return w["until"]

    def _covering(self, at: float) -> dict | None:
        for k in sorted(self.windows, reverse=True):
            w = self.windows[k]
            if w["opened_at"] <= at <= w["until"]:
                return w
        return None

    def covers(self, at: float | None = None) -> bool:
        with self._lock:
            return self._covering(self.clock() if at is None else at) is not None

    def swallow(self, what: str, at: float | None = None) -> bool:
        """True (and counted) when `what` ("stall" / "end" / "desync") falls in an open window: not taken."""
        with self._lock:
            w = self._covering(self.clock() if at is None else at)
            if w is None:
                return False
            w["counts"][what] = w["counts"].get(what, 0) + 1
            return True

    def report(self, seq: int) -> dict | None:
        with self._lock:
            w = self.windows.get(seq)
            if w is None:
                return None
            return {"window": w["which"], "open_s": round(w["until"] - w["opened_at"], 2),
                    "stalls_not_taken": w["counts"]["stall"], "stall_ends_not_taken": w["counts"]["end"],
                    "desyncs_not_taken": w["counts"]["desync"]}


class PartyMinigames:
    def __init__(self, plugin: Any, environ=os.environ, clock=time.monotonic):
        self.p = plugin
        self.emu = plugin._emulator
        self.environ = environ
        self.clock = clock
        self._salt = os.urandom(8)
        self._lock = threading.Lock()           # the fields below and each mini game's; never held across a call
        self._cond = threading.Condition(self._lock)
        self.mg: dict | None = None            # the current (or last) mini game
        self.play_limit_s, self.unknown_limit_s = PLAY_LIMIT_S, UNKNOWN_LIMIT_S
        self.poll_gone_s, self.end_wait_s, self.tick = POLL_GONE_S, END_WAIT_S, TICK
        self.start_limit_s, self.switch_limit_s, self.step_grace_s = START_LIMIT_S, SWITCH_LIMIT_S, STEP_GRACE_S
        self.stream_needed = True               # B112's bench sets False (no stream, no switch)
        self._reads: dict[str, dict] = {}       # B114: the last good answer of each bounded read, its helper

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
            if self.mg is not None and not self._finished(self.mg):
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
        now = self.clock()
        mg = {"state": "starting", "seats": seats, "entry": entry, "recognised": None, "class": None,
              "scores": None, "why": None, "t0": now, "last_poll": now, "final_at": None,
              "stash": None, "launched": False, "routed": False, "ended_by": None, "closed": False,
              # B114: the actor's step, the taken calls, the end's owner
              "step": None, "step_since": None, "queue": collections.deque(), "end_req": None, "ending": False,
              "title_proc": None, "actor_done": False, "switched_to": None}
        with self._lock:
            self.mg = mg
        self.row({"step": "minigame_start", "seats": seats, "players": entry["players"]})
        threading.Thread(target=self._actor, args=(mg,), daemon=True, name="party-minigame").start()
        threading.Thread(target=self._watch, args=(mg,), daemon=True, name="party-minigame-watch").start()
        return {"ok": True, "state": "starting", "seats": seats}

    @staticmethod
    def _finished(mg: dict) -> bool:
        return bool(mg["closed"] and mg["actor_done"])

    def _bridge(self):
        try:
            return self.p._native_stream._session_io.controller
        except Exception:
            return None

    def _final(self, mg: dict, state: str, **fields) -> None:
        with self._lock:
            if mg["state"] in FINAL or mg["closed"]:
                return
            mg.update(state=state, final_at=self.clock(), **fields)
        self.row({"step": "minigame_" + state, **{k: v for k, v in fields.items() if k in ("class", "scores", "why")}})

    # --- B114: bounded calls ------------------------------------------------------------------------------------------
    def _emu_call(self, mg: dict | None, fn: Callable[[], Any], bound: float | None = None, abort: bool = True):
        """One manager call under the manager's own lock, for that call only. The lock is tried in EMU_TRY_S steps;
        between them an END stops the start (abort); `bound` gives the wait up (TimeoutError)."""
        lock = self.emu.lock
        deadline = None if bound is None else self.clock() + bound
        while not lock.acquire(timeout=EMU_TRY_S):
            if abort and mg is not None and (mg["end_req"] is not None or mg["closed"]):
                raise _Abort()
            if deadline is not None and self.clock() >= deadline:
                raise TimeoutError("the manager's lock was not free within %.0f s" % bound)
        try:
            if abort and mg is not None and (mg["end_req"] is not None or mg["closed"]):
                raise _Abort()
            return fn()
        finally:
            lock.release()

    def _bounded(self, fn: Callable[[], Any], limit: float) -> tuple[bool, Any]:
        """fn on a helper thread with nothing held; (done, result or exception) after at most `limit` seconds."""
        box: dict = {}
        done = threading.Event()

        def run():
            _local.inside = True
            try:
                box["r"] = fn()
            except BaseException as exc:          # noqa: BLE001 - handed back to the caller
                box["e"] = exc
            finally:
                done.set()
        threading.Thread(target=run, daemon=True, name="party-minigame-call").start()
        if not done.wait(limit):
            return False, None
        return True, box.get("e", box.get("r"))

    def _planned(self) -> PlannedSwitch:
        rec = self.p._recovery
        ps = getattr(rec, "_planned_switch", None)
        if ps is None:
            ps = rec._planned_switch = PlannedSwitch()
        return ps

    def _note_bitrate_planned(self) -> None:
        """B115: the bitrate controller told of the new SSRC (its blackout, as for any restart) but not as a recovery
        restart: no escalation count, so no escalation step for a planned switch."""
        try:
            import adaptive_bitrate_live as abl
            abr = getattr(self.p, "_adaptive_bitrate", None)
            if abl.is_live(abr):
                with abr._lock:
                    abr._emit(abr._policy.note_ssrc_change("minigame_switch"), None)
        except Exception:
            pass

    def _switch_stream(self, which: str, pid: int | None = None) -> bool:
        """The onn's stream to the other window (B115: a planned switch for `pid`, the recovery told): the stream's own
        start for that process, with the remembered client, on a helper thread with no lock held (B114), waited for at
        most switch_limit_s. True when switched."""
        if not self.stream_needed or not self.p._recovery_stream_active():
            self.row({"step": "minigame_stream", "window": which, "switched": False, "why": "the stream is not up"})
            return False
        args = getattr(self.p, "_recovery_start_args", None)
        if not isinstance(args, dict) or not args.get("client_ip") or pid is None:
            self.row({"step": "minigame_stream", "window": which, "switched": False,
                      "why": "no remembered client or no process"})
            return False
        ps = self._planned()
        seq = ps.open(which, self.switch_limit_s + PLANNED_GRACE_S)
        t0 = self.clock()
        ns = self.p._native_stream

        def go():
            return ns.start(client_ip=str(args["client_ip"]), port=int(args["port"]), managed_process_id=int(pid))
        try:
            done, res = self._bounded(go, self.switch_limit_s)
        finally:
            until = ps.close_after(seq, PLANNED_GRACE_S)
            threading.Thread(target=self._window_row, args=(ps, seq, until), daemon=True,
                             name="party-minigame-window").start()
        if not done:
            self.row({"step": "minigame_stream", "window": which, "switched": False, "planned": True,
                      "why": f"the switch did not finish within {self.switch_limit_s:.0f} s"})
            raise TimeoutError(f"the stream switch did not finish within {self.switch_limit_s:.0f} s")
        if isinstance(res, BaseException):
            self.row({"step": "minigame_stream", "window": which, "switched": False, "planned": True,
                      "why": str(res)[:160]})
            return False
        self._note_bitrate_planned()
        self.row({"step": "minigame_stream", "window": which, "switched": True, "planned": True,
                  "seconds": round(self.clock() - t0, 3)})
        return True

    def _window_row(self, ps: PlannedSwitch, seq: int, until: float | None) -> None:
        if until is not None:
            time.sleep(max(0.0, until - self.clock()) + 0.05)
        rep = ps.report(seq)
        if rep is not None:
            self.row({"step": "minigame_switch_window", **rep})

    # --- the actor: the start's steps, then every taken call in order -------------------------------------------------
    def _step(self, mg: dict, name: str, fn: Callable[[], Any]):
        with self._cond:
            if mg["end_req"] is not None or mg["closed"] or mg["state"] != "starting":
                raise _Abort()
            mg["step"], mg["step_since"] = name, self.clock()
        try:
            return fn()
        finally:
            with self._cond:
                mg["step"] = None
                self._cond.notify_all()

    def _start_steps(self, mg: dict) -> None:
        emu = self.emu
        mg["stash"] = self._step(mg, "stash", lambda: self._emu_call(mg, emu._party_stash_begin))
        emu._party_mg_stop_hook = lambda: self._end_by_stop(mg)
        game = self.p._find_game_by_id(mg["entry"]["game"])

        def launch():
            emu.launch(game)
            return emu.process
        proc = self._step(mg, "launch", lambda: self._emu_call(mg, launch))
        with self._lock:
            mg["launched"], mg["title_proc"] = True, proc
            late = mg["ending"] or mg["closed"]
        if late:                                     # the end ran while the title launched: it is not left running
            self._kill(proc)
            raise _Abort()
        self.row({"step": "minigame_launch", "pid_owned": True})
        self._step(mg, "pause", lambda: self._emu_call(mg, emu.pause))
        bridge = self._bridge()
        if bridge is not None:
            self._step(mg, "route", lambda: bridge.set_party_route({s - 1: k for k, s in enumerate(mg["seats"])}))
            mg["routed"] = True
        self.row({"step": "minigame_route", "ports": {str(k + 1): s for k, s in enumerate(mg["seats"])},
                  "routed": mg["routed"]})
        if self._step(mg, "switch", lambda: self._switch_stream("minigame", getattr(proc, "pid", None))):
            mg["switched_to"] = "minigame"
        runner = self.p._h7_minigame_runner()
        self._step(mg, "watch", lambda: runner.start("1", "", bench=not self.stream_needed))
        self.row({"step": "minigame_watch", "loaded": True})
        self._step(mg, "resume", lambda: self._emu_call(mg, emu.resume))
        with self._lock:
            if mg["state"] == "starting":
                mg["state"] = "playing"
        self.row({"step": "minigame_playing"})

    def _actor(self, mg: dict) -> None:
        try:
            self._start_steps(mg)
        except _Abort:
            pass
        except Exception as exc:
            self._final(mg, "given_up", why=f"the mini game did not start: {str(exc)[:160]}")
            self._enqueue(mg, "end_hub", None, by="hub: the start failed")   # B114: the title not left up
        self._serve(mg)

    def _serve(self, mg: dict) -> None:
        """Every taken call in the order taken; ends when the mini game is closed and nothing is left."""
        while True:
            with self._cond:
                while not mg["queue"] and not mg["closed"]:
                    self._cond.wait(0.2)
                if not mg["queue"]:
                    mg["actor_done"] = True
                    self._cond.notify_all()
                    return
                item = mg["queue"].popleft()
            self._do(mg, item)

    def _do(self, mg: dict, item: dict) -> None:
        with self._lock:                              # one runner per item: the actor or the END's guard
            if item.get("claimed"):
                return
            item["claimed"] = True
        kind = item["kind"]
        if kind in ("end", "end_board", "end_hub"):
            self._end_once(mg, item["by"])
        _local.inside = True
        try:
            if item["fn"] is not None:
                item["result"] = item["fn"]()
        except BaseException as exc:                  # noqa: BLE001 - the route raises it in its own thread
            item["error"] = exc
        finally:
            _local.inside = False
            item["done"].set()

    # --- taking the onn's calls and the ends --------------------------------------------------------------------------
    def _enqueue(self, mg: dict, kind: str, fn: Callable[[], Any] | None, by: str | None = None) -> dict | None:
        item = {"kind": kind, "fn": fn, "by": by, "done": threading.Event(), "result": None, "error": None}
        with self._cond:
            if mg["actor_done"]:
                return None
            if kind in ("end", "end_board", "end_hub") and mg["end_req"] is None:
                mg["end_req"] = by
            mg["queue"].append(item)
            state = mg["state"]
            self._cond.notify_all()
        self.row({"step": "minigame_taken", "what": kind, "state": state})
        if kind in ("end", "end_board", "end_hub"):
            threading.Thread(target=self._guard_end, args=(mg, item), daemon=True, name="party-minigame-end").start()
        return item

    def _guard_end(self, mg: dict, item: dict) -> None:
        """END always works: if the actor has not taken the end within step_grace_s (stuck in a step), it runs here."""
        end = self.clock() + self.step_grace_s
        with self._cond:
            while not (mg["ending"] or mg["closed"] or item["done"].is_set()) and self.clock() < end:
                self._cond.wait(0.1)
            if mg["ending"] or mg["closed"] or item["done"].is_set():
                return
            stuck = mg["step"]
            since = mg["step_since"]
        self.row({"step": "minigame_stuck", "what": stuck,
                  "seconds": round(self.clock() - since, 1) if since is not None else None})
        self._do(mg, item)

    def take(self, action: str, fn: Callable[[], Any]) -> dict | None:
        """A route the onn sends while a mini game is on (Home / RESUME / END): taken at once onto the mini game's
        queue and acted on in order. None when no mini game is on (the route runs today's path)."""
        kind = TAKEN.get(action)
        with self._lock:
            mg = self.mg
        if kind is None or mg is None or mg["actor_done"]:
            return None
        if kind == "end":
            self._final(mg, "given_up", why="ended from the onn")
        item = self._enqueue(mg, kind, fn, by="onn" if kind == "end" else None)
        if item is None:
            return None
        wait = RESUME_WAIT_S if kind.startswith("resume") else TAKE_WAIT_S
        if not item["done"].wait(wait):
            if kind.startswith("resume"):
                raise RuntimeError(f"the mini game's calls did not reach this one within {wait:.0f} s")
            with self._lock:
                state = mg["state"]
            return {"ok": True, "plugin": "games", "taken": kind, "minigame": state, "pending": True}
        if item["error"] is not None:
            raise item["error"]
        res = item["result"]
        if isinstance(res, dict) and kind in ("home", "end"):
            res = {**res, "taken": kind}
        return res

    def bounded_read(self, action: str, fn: Callable[[], Any]) -> dict | None:
        """`status` / `native-stream-status` while a mini game is on: today's answer if it comes within READ_WAIT_S,
        else the last good one with "snapshot": true (one helper per route at a time). None when no mini game is on."""
        with self._lock:
            mg = self.mg
            if mg is None or self._finished(mg):
                return None
            slot = self._reads.setdefault(action, {"last": None, "busy": None})
            helper = slot["busy"]
            if helper is None:
                helper = slot["busy"] = {"done": threading.Event(), "r": None, "e": None}

                def run(h=helper, s=slot):
                    _local.inside = True
                    try:
                        h["r"] = fn()
                    except BaseException as exc:      # noqa: BLE001
                        h["e"] = exc
                    finally:
                        with self._lock:
                            if h["e"] is None and isinstance(h["r"], dict):
                                s["last"] = h["r"]
                            s["busy"] = None
                        h["done"].set()
                threading.Thread(target=run, daemon=True, name="party-minigame-read").start()
        if helper["done"].wait(READ_WAIT_S):
            if helper["e"] is not None:
                raise helper["e"]
            return helper["r"]
        with self._lock:
            last = slot["last"]
        if last is None:
            return {"ok": True, "plugin": "games", "snapshot": True, "minigame": mg["state"]}
        return {**last, "snapshot": True}

    # --- the watch (from the start) -----------------------------------------------------------------------------------
    def _watch(self, mg: dict) -> None:
        runner = self.p._h7_minigame_runner()
        unknown_since = None
        while True:
            time.sleep(self.tick)
            with self._lock:
                if self.mg is not mg or mg["closed"]:
                    return
                state = mg["state"]
                asked = mg["end_req"] is not None
            now = self.clock()
            stash = mg.get("stash") or {}
            board = stash.get("process")
            if board is not None and board.poll() is not None and not asked:
                self._final(mg, "given_up", why="the board stopped")
                self._enqueue(mg, "end_hub", None, by="hub: the board stopped")
                continue
            if asked:
                continue
            if state in FINAL:
                if now - (mg["final_at"] or now) >= self.end_wait_s:
                    self._enqueue(mg, "end_hub", None, by="hub: no end call")
                continue
            if state == "starting":
                if now - mg["t0"] >= self.start_limit_s:
                    self._final(mg, "given_up", why=f"the mini game did not start within {self.start_limit_s:.0f} s")
                    self._enqueue(mg, "end_hub", None, by="hub: the start was stuck")
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
        """The board's end: taken at once, acted on in order; answered with the end done if it is within TAKE_WAIT_S."""
        with self._lock:
            mg = self.mg
            if mg is None:
                return {"ok": True, "state": "none", "ended": False}
            if mg["closed"] or mg["end_req"] is not None:
                again = mg["closed"]
                ans = {"ok": True, "state": mg["state"], "scores": mg["scores"], "ended": True}
                return {**ans, "again": True} if again else {**ans, "pending": True}
        if mg["state"] not in FINAL:
            self._final(mg, "given_up", why=f"ended before a result ({by})")
        item = self._enqueue(mg, "end_board", None, by=by)
        done = item["done"].wait(TAKE_WAIT_S) if item is not None else True
        with self._lock:
            ans = {"ok": True, "state": mg["state"], "scores": mg["scores"], "ended": True}
        return ans if done else {**ans, "pending": True}

    def _end_once(self, mg: dict, by: str, inline: bool = False) -> bool:
        """The end's steps, once per mini game (whoever comes first: the actor, the guard, the manager's stop)."""
        with self._cond:
            if mg["ending"] or mg["closed"]:
                return False
            mg["ending"] = True
            if mg["end_req"] is None:
                mg["end_req"] = by
        try:
            self._end_steps(mg, by, inline)
        finally:
            with self._cond:
                mg["ended_by"] = by
                mg["closed"] = True
                self._cond.notify_all()
            self.row({"step": "minigame_end", "by": by})
        return True

    def _kill(self, proc: Any) -> None:
        try:
            if proc is not None and proc.poll() is None:
                proc.kill()
        except Exception:
            pass

    def _end_steps(self, mg: dict, by: str, inline: bool) -> None:
        """B115's way back: the route cleared, **the stream switched to the board while the title still runs** (the
        board's own pid: the title's stop cannot take the stream), **then** the title stopped, then the board's
        session back. END from the onn and the manager's stop (the session ends): no switch."""
        emu = self.emu
        if mg["state"] not in FINAL:
            self._final(mg, "given_up", why=f"ended before a result ({by})")
        self._bounded(lambda: self.p._h7_minigame_runner().stop(), 2.0)
        if emu._party_mg_stop_hook is not None:
            emu._party_mg_stop_hook = None
        if mg.get("routed"):
            bridge = self._bridge()
            if bridge is not None:
                bridge.set_party_route(None)
        board = (mg.get("stash") or {}).get("process")
        if by not in ("stop", "onn") and not inline and board is not None and board.poll() is None:
            try:
                self._switch_stream("board", getattr(board, "pid", None))
            except Exception:
                pass
        title = mg.get("title_proc")

        def stop_title():
            if emu._party_stash is not None and emu.process is not None and emu.process is title:
                emu.stop()                       # the title, RetroArch's own stop (the hook already cleared)
        if mg.get("launched"):
            try:
                if inline:
                    stop_title()
                else:
                    self._emu_call(None, stop_title, bound=MANAGER_BOUND_S, abort=False)
            except Exception as exc:
                self.row({"step": "minigame_end", "title_stop_failed": str(exc)[:160]})
            self._kill(title)                    # whatever the manager's stop did, the title is not left running
            self.row({"step": "minigame_title_stopped"})
        try:
            if inline:
                emu._party_stash_end()
            else:
                self._emu_call(None, emu._party_stash_end, bound=MANAGER_BOUND_S, abort=False)
            self.row({"step": "minigame_restore", "board_alive": emu.process is not None
                      and emu.process.poll() is None})
        except Exception as exc:
            self.row({"step": "minigame_restore", "failed": str(exc)[:160]})

    def _end_by_stop(self, mg: dict) -> dict:
        """The manager's stop with a mini game on (another launch, launch_orphaned — its caller holds the manager's
        lock): the mini game ended inline, waiting on nothing (no actor, no stream), then the board's own stop (F10)."""
        self._final(mg, "given_up", why="ended from the onn")
        self._end_once(mg, "stop", inline=True)
        return self.emu.stop()
