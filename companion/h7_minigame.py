"""B103 (H7): the mini game's two calls — its start, and its result read from the game's own end screen.

Only with PRIVYHUB_H7=1 (`plugins/games.py` imports this module then; absent / 0 = today: neither route exists, no
picture is read, the learner is not imported).

`POST /plugins/games/h7-start[?load=0]` — for the game the hub is running now, with an end-screen spec in the rules
folder (`<game id>.endscreen.json` + its `.npz`, B102's learner) while the stream is up: B101's load step alone (the kept
`<game id>.state` through scratch slot 8, RetroArch's own load line; PS1 / SNES; B101's code, reused) — no clock, no
read of memory — then the watcher begins. `load=0`: no load (any system); the watcher must see the start itself.

The watcher: about once a second, the game's window read in process (Pillow's X11 grab of the window's area — the
settle's cheapest: no frame lost, nothing written; the stream's own capture untouched), B102's reader, B102's `Ended`
(K agreeing reads; an end class only after the start was seen or loaded) → `ended` with the class, and it stops
reading. It sends nothing to the game. The game stopping (the user's END) stops it with one row.

`GET /plugins/games/h7-result` → `{"state": "no_game" | "no_spec" | "idle" | "watching" | "ended", "class",
"seen_start", "since_s", "reads", "last": {"distances", "margin"}}`. One row per change in logs/games/h7_results.jsonl.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import h7_contest as contest
import h7_live_read as live

READ_EVERY = 1.0            # s: one picture a second
LOG_RELATIVE = "logs/games/h7_results.jsonl"
SYSTEMS = ("ps1", "snes")   # the load; the watcher alone (load=0) on any system
XDOTOOL_WAIT = 1.0
_endscreen = None


def endscreen():
    """B102's learner (`tools/h7_endscreen.py`: PIL + numpy, both on the hub), imported at the first start or result —
    not when the companion starts, so a companion whose tools/ lacks it still starts (B99 / B101 run as before)."""
    global _endscreen
    if _endscreen is None:
        tools = str(Path(__file__).resolve().parents[1] / "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        import h7_endscreen
        _endscreen = h7_endscreen
    return _endscreen


class WindowPicture:
    """The game's window, read in process: the manager's process → its largest visible window (xdotool, as the
    stream's capture finds it) → Pillow's X11 grab of that area on the companion's display. Writes nothing."""

    def __init__(self, emulator: Any, environ=os.environ):
        self._emu = emulator
        self._environ = environ
        self._window: tuple[int, tuple[int, int, int, int]] | None = None

    def _find(self, pid: int, display: str) -> tuple[int, tuple[int, int, int, int]]:
        env = dict(os.environ, DISPLAY=display)
        r = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(pid)], capture_output=True,
                           text=True, timeout=XDOTOOL_WAIT, env=env, check=False)
        best = None
        for w in r.stdout.split():
            g = subprocess.run(["xdotool", "getwindowgeometry", "--shell", w], capture_output=True, text=True,
                               timeout=XDOTOOL_WAIT, env=env, check=False)
            kv = dict(line.split("=", 1) for line in g.stdout.splitlines() if "=" in line)
            try:
                geo = (int(kv["X"]), int(kv["Y"]), int(kv["WIDTH"]), int(kv["HEIGHT"]))
            except (KeyError, ValueError):
                continue
            if geo[2] < 64 or geo[3] < 64:
                continue
            if best is None or geo[2] * geo[3] > best[1][2] * best[1][3]:
                best = (int(w), geo)
        if best is None:
            raise RuntimeError("the game's window was not found")
        return best

    def grab(self):
        from PIL import ImageGrab
        display = (self._environ.get("DISPLAY") or "").strip()
        if not display:
            raise RuntimeError("no display")
        proc = getattr(self._emu, "process", None)
        if proc is None:
            raise RuntimeError("no game process")
        try:
            if self._window is None:
                self._window = self._find(int(proc.pid), display)
            x, y, w, h = self._window[1]
            return ImageGrab.grab(bbox=(x, y, x + w, y + h), xdisplay=display)
        except Exception as exc:
            self._window = None                                 # found again at the next picture
            raise RuntimeError(f"the picture was not read: {exc}") from exc


class _Loader(contest.Contest):
    """B101's load step (`_load`, `_core_file`, `_refused`), its rows sent to h7_results."""

    def __init__(self, owner: "MiniGame"):
        super().__init__(owner._emu, None, owner._stream, owner._project_path, owner._environ, owner._clock)
        self._owner = owner

    def _row(self, fields: dict) -> None:
        self._owner._row(fields)


class MiniGame:
    def __init__(self, emulator: Any, native_stream: Any, project_path, environ=os.environ, clock=time.monotonic):
        self._emu = emulator
        self._stream = native_stream
        self._project_path = project_path
        self._environ = environ
        self._clock = clock
        self._lock = threading.Lock()
        self._live = live.LiveRead(emulator, project_path, environ, clock)    # its `_running` only (no read)
        self.picture = WindowPicture(emulator, environ)
        self.read_every = READ_EVERY
        self._watch: dict | None = None
        self._stopped: str | None = None

    # --- the spec ------------------------------------------------------------------------------------------------
    def _spec(self, game: str):
        """(spec, arrays) or raises ValueError with the plain reason."""
        if not live._ID.match(game) or game in (".", ".."):
            raise ValueError("no end-screen spec for this game")
        path = live.rules_folder(self._environ) / f"{game}.endscreen.json"
        if not path.is_file():
            raise ValueError("no end-screen spec for this game")
        try:
            return endscreen().load_spec(path)
        except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
            raise ValueError(f"the end-screen spec for this game cannot be read: {exc}") from exc

    # --- GET -----------------------------------------------------------------------------------------------------
    def result(self) -> dict:
        game, _system, _kind = self._live._running()
        if game is None:
            out = {"ok": True, "state": "no_game"}
            if self._stopped:
                out["stopped"] = self._stopped
            return out
        with self._lock:
            w = self._watch
            if w is not None and w["game"] == game and w["state"] in ("watching", "ended"):
                out = {k: v for k, v in w.items() if k not in ("t0", "token")}
                out["since_s"] = round(self._clock() - w["t0"], 1)
                return {"ok": True, **json.loads(json.dumps(out))}
        try:
            self._spec(game)
        except ValueError as exc:
            return {"ok": True, "state": "no_spec", "game": game, "why": str(exc)}
        return {"ok": True, "state": "idle", "game": game}

    # --- POST ----------------------------------------------------------------------------------------------------
    def _refused(self, why: str):
        self._row({"step": "refused", "why": why})
        raise ValueError(why)

    def start(self, load_text: str = "") -> dict:
        text = str(load_text or "").strip()
        if text not in ("", "0", "1"):
            raise ValueError("load is 0 or 1")
        load = text != "0"
        with self._lock:
            if self._watch is not None and self._watch["state"] == "watching":
                self._refused("a mini game is already being watched")
        try:
            game, system, kind = self._live._running()
        except RuntimeError as exc:
            self._refused(str(exc))
        if game is None:
            self._refused("no game is running")
        try:
            spec, arrays = self._spec(game)
        except ValueError as exc:
            self._refused(str(exc))
        loader = _Loader(self)
        if load:
            if kind in ("pcsx2", "dolphin"):
                self._refused("not supported yet")
            if system == "n64":
                self._refused("not supported yet — a state cannot be loaded into a running N64 game")
            if system not in SYSTEMS:
                self._refused("not supported yet")
            state = live.rules_folder(self._environ) / f"{game}.state"
            if not state.is_file() or state.stat().st_size <= 0:
                self._refused("no state for this game's mini game")
        if not self._stream_up():
            self._refused("the stream is not up")
        line_ms = None
        if load:
            core = loader._core_file(system)
            folder_name = contest.CORE_FOLDERS.get(core[:-len(".so")] if core.endswith(".so") else core)
            if folder_name is None:
                self._refused("not supported yet with this game's core")
            stem = self._emu._active_state_stem()
            folder = self._emu._state_root() / folder_name
            try:
                line_ms = loader._load(game, state, folder, stem)
            except live.Busy:
                raise live.Busy("the mini game's state did not load; the game is as it was") from None
        reader = endscreen().Reader(spec, arrays, clock=self._clock)
        ended = endscreen().Ended(spec)
        if load:
            ended.start_loaded()
        token = object()
        with self._lock:
            if self._watch is not None and self._watch["state"] == "watching":
                self._refused("a mini game is already being watched")
            self._stopped = None
            self._watch = {"state": "watching", "game": game, "class": None, "seen_start": ended.seen_start,
                           "reads": 0, "last": None, "loaded": load, "picture_failures": 0, "t0": self._clock(),
                           "token": token}
        self._row({"step": "watching", "game": game, "loaded": load, "load_line_ms": line_ms,
                   "k": ended.k, "start_class": spec["start_class"], "end_classes": spec["end_classes"]})
        threading.Thread(target=self._run, args=(token, game, reader, ended), daemon=True,
                         name="h7-minigame").start()
        return {"ok": True, "watch": "started", "game": game, "loaded": load, "load_line_ms": line_ms}

    def _stream_up(self) -> bool:
        try:
            return bool((self._stream.status() or {}).get("active"))
        except Exception:
            return False

    # --- the watcher ---------------------------------------------------------------------------------------------
    def _current(self, token) -> dict | None:
        w = self._watch
        return w if (w is not None and w.get("token") is token and w["state"] == "watching") else None

    def _run(self, token, game: str, reader, ended) -> None:
        t0 = self._clock()
        k = 1
        last_class = None
        try:
            while True:
                time.sleep(max(0.0, t0 + k * self.read_every - self._clock()))
                k += 1
                with self._lock:
                    if self._current(token) is None:
                        return
                try:
                    now, _s, _k = self._live._running()
                except RuntimeError:
                    continue                                        # busy: checked again at the next second
                if now != game:
                    with self._lock:
                        if self._current(token) is None:
                            return
                        reads = self._watch["reads"]
                        self._watch = None
                        self._stopped = "the game stopped"
                    self._row({"step": "stopped", "game": game, "why": "the game stopped", "reads": reads})
                    return
                try:
                    img = self.picture.grab()
                except Exception as exc:
                    with self._lock:
                        if self._current(token) is None:
                            return
                        self._watch["picture_failures"] += 1
                    self._row({"step": "picture_failed", "game": game, "why": str(exc)[:200]})
                    continue
                r = reader.read(img)
                seen_before = ended.seen_start
                done = ended.feed(r["class"])
                with self._lock:
                    w = self._current(token)
                    if w is None:
                        return
                    w["reads"] += 1
                    w["class"] = r["class"]
                    w["seen_start"] = ended.seen_start
                    w["last"] = {"distances": r["distances"], "margin": r["margin"]}
                    reads = w["reads"]
                    since = round(self._clock() - w["t0"], 1)
                    if done:
                        w.update(state="ended", **{"class": done}, ended_after_s=since)
                if ended.seen_start and not seen_before:
                    self._row({"step": "start_seen", "game": game, "after_s": since, "reads": reads})
                if r["class"] == endscreen().UNKNOWN and last_class != endscreen().UNKNOWN:
                    self._row({"step": "unknown_screen", "game": game, "after_s": since,
                               "distances": r["distances"], "margin": r["margin"]})
                last_class = r["class"]
                if done:
                    self._row({"step": "ended", "game": game, "class": done, "after_s": since, "reads": reads})
                    return
        except Exception as exc:                                        # anything unexpected: one row, the watch off
            with self._lock:
                if self._current(token) is not None:
                    self._watch = None
            self._row({"step": "error", "game": game, "why": str(exc)[:200]})

    def _row(self, fields: dict) -> None:
        try:
            path = Path(self._project_path(LOG_RELATIVE))
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"time_unix": round(time.time(), 3), **fields}, sort_keys=True) + "\n")
        except OSError:
            pass
