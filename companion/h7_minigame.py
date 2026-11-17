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

B105 (the same flag): a start while a watch is on **replaces** it (the load again, a new watch, one row `replaced`;
the other refusals stay, and a refused or failed start leaves the running watch as it was); **`recognised`** in the
result — after a start with the load, `true` once a read names the start class, `false` when RECOGNISE_S pass without
one (the picture in front of the hub is not this game's start: nobody may be sent into a match), `null` until then
(with load=0: `true` once seen, else `null`); settled once, one row; **`POST /plugins/games/h7-stop`** ends the watch,
the game untouched, one row; **`h7-start?keep=1`** saves every picture the watcher reads (JPEG) with an `index.csv`
(seconds, utc, file, class, screen, margin, distances, keep_ms) under `runtime/h7_frames/<game id>_<UTC stamp>/`
(git-ignored); **`last`** carries the read's class and distances, the thresholds they are held against and the spec's
version; an old-measure spec is `no_spec` with B104's plain line.

B127 (the same flag): **under a cheat setup** (the session's `cheat_session.profile_id` set — the onn's Extras launch,
or a party mini game launched with its setup) the begin is the setup's own **`<game id>.<the profile_id's first 12
characters>.state`** when the rules folder holds it, else `<game id>.state` as today; it is loaded through scratch slot
8 of **the setup's own `states/<core>/`** (`_state_root()` is the setup's while its session runs — where RetroArch
reads). The answer and the `watching` row carry `"begin": "setup" | "normal"` only under a setup; without one, today.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
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
SYSTEMS = ("ps1", "snes", "n64")   # the load (B123: N64, only into a paused core); the watcher alone on any system
N64_NOT_PAUSED = "the N64 game is not paused: its state is loaded only into a paused core; nothing was sent"
XDOTOOL_WAIT = 1.0
BENCH_STREAM_UP = "a client's stream is up: not on the bench"   # B112
BENCH_LOOPBACK = "the bench is for loopback callers only"          # B112
LOOPBACK = ("127.0.0.1", "::1", "localhost")
RECOGNISE_S = 8.0           # B105: s after a start with the load within which a read must name the start class
KEEP_RELATIVE = "runtime/h7_frames"   # B105: keep=1's pictures (git-ignored: runtime/)
JPEG_QUALITY = 90
SETUP_PREFIX = 12           # B127: a setup's begin is <game id>.<the profile_id's first 12 characters>.state
_PROFILE_ID = re.compile(r"^[0-9A-F]{64}$")
_endscreen = None


def setup_begin_name(game: str, profile_id: str) -> str:
    """B127: the rules folder's name for a cheat setup's begin, beside the normal `<game id>.state`."""
    return f"{game}.{str(profile_id).strip().upper()[:SETUP_PREFIX]}.state"


def session_profile_id(emulator: Any) -> str | None:
    """B127: the running session's cheat setup (`profile_id`, upper case), or None (no setup, or a mod session)."""
    sess = getattr(emulator, "_active_cheat_session", None)
    if not isinstance(sess, dict) or sess.get("session_kind", "cheat") != "cheat":
        return None
    pid = str(sess.get("profile_id") or "").strip().upper()
    return pid if _PROFILE_ID.match(pid) else None


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
        self.recognise_s = RECOGNISE_S
        self._watch: dict | None = None
        self._stopped: str | None = None
        self._start_lock = threading.Lock()          # B105: starts one at a time (a replace cannot race a replace)

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
            old = getattr(endscreen(), "OLD_MEASURE", None)
            if old and str(exc) == old:
                raise ValueError(old) from exc                  # B105: B104's plain line ("learn it again")
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
                out = {k: v for k, v in w.items() if k not in ("t0", "token") and not k.startswith("_")}
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

    def start(self, load_text: str = "", keep_text: str = "", bench: bool = False) -> dict:
        text = str(load_text or "").strip()
        if text not in ("", "0", "1"):
            raise ValueError("load is 0 or 1")
        load = text != "0"
        keep_word = str(keep_text or "").strip()
        if keep_word not in ("", "0", "1"):
            raise ValueError("keep is 0 or 1")
        keep = keep_word == "1"
        with self._start_lock:
            return self._start(load, keep, bench)

    def _start(self, load: bool, keep: bool, bench: bool = False) -> dict:
        # B105: a watch already on is replaced after the checks and the load (never refused for being on)
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
        begin = None                                        # B127: "setup" / "normal" only under a cheat setup
        if load:
            if kind in ("pcsx2", "dolphin"):
                self._refused("not supported yet")
            if system not in SYSTEMS:
                self._refused("not supported yet")
            state = live.rules_folder(self._environ) / f"{game}.state"
            setup = session_profile_id(self._emu)
            if setup is not None:
                own = live.rules_folder(self._environ) / setup_begin_name(game, setup)
                if own.is_file() and own.stat().st_size > 0:
                    state, begin = own, "setup"
                else:
                    begin = "normal"
            if not state.is_file() or state.stat().st_size <= 0:
                self._refused("no state for this game's mini game")
        if bench and self._stream_up():                     # B112: the bench only while no client's stream is up
            self._refused(BENCH_STREAM_UP)
        if not bench and not self._stream_up():
            self._refused("the stream is not up")
        line_ms = None
        if load:
            core = loader._core_file(system)
            if system == "n64":                                  # B123: the running session's own core (B59's)
                core = str(getattr(self._emu, "_n64_core", None) or core)
            folder_name = contest.CORE_FOLDERS.get(core[:-len(".so")] if core.endswith(".so") else core)
            if folder_name is None:
                self._refused("not supported yet with this game's core")
            stem = self._emu._active_state_stem()
            folder = self._emu._state_root() / folder_name
            # B123: an N64 state only into a core that answers PAUSED (B61 / B65: a running N64 core hangs RetroArch)
            if system == "n64":
                try:
                    paused = self._emu._retroarch_network_status() == "PAUSED"
                except Exception:
                    paused = False
                if not paused:
                    self._refused(N64_NOT_PAUSED)
            try:
                line_ms = loader._load(game, state, folder, stem)
            except live.Busy:
                raise live.Busy("the mini game's state did not load; the game is as it was") from None
        reader = endscreen().Reader(spec, arrays, clock=self._clock)
        ended = endscreen().Ended(spec)
        if load:
            ended.start_loaded()
        keep_dir = self._keep_folder(game) if keep else None
        token = object()
        with self._lock:
            old = self._watch
            replaced = old is not None and old["state"] == "watching"
            if replaced:
                self._row({"step": "replaced", "game": old["game"], "reads": old["reads"], "class": old["class"],
                           "since_s": round(self._clock() - old["t0"], 1)})
            self._stopped = None
            self._watch = {"state": "watching", "game": game, "class": None, "seen_start": ended.seen_start,
                           "recognised": None, "reads": 0, "last": None, "loaded": load, "picture_failures": 0,
                           "keep": ({"folder": keep_dir.name, "pictures": 0} if keep_dir is not None else None),
                           "t0": self._clock(), "token": token, "_keep_dir": keep_dir}
            row = {"step": "watching", "game": game, "loaded": load, "load_line_ms": line_ms,
                   "k": ended.k, "start_class": spec["start_class"], "end_classes": spec["end_classes"],
                   "spec_version": spec.get("version"), "recognise_s": self.recognise_s, "bench": bench,
                   "keep": keep_dir.name if keep_dir is not None else None}
            if begin is not None:
                row["begin"] = begin                                 # B127: only under a cheat setup
            self._row(row)
        threading.Thread(target=self._run, args=(token, game, reader, ended, spec), daemon=True,
                         name="h7-minigame").start()
        answer = {"ok": True, "watch": "started", "game": game, "loaded": load, "load_line_ms": line_ms,
                  "replaced": replaced, "keep": keep_dir.name if keep_dir is not None else None}
        if begin is not None:
            answer["begin"] = begin
        return answer

    def bench_release(self, client_ip: str) -> dict:
        """B112: the running game's pause released with no stream (loopback, no client's stream up)."""
        if str(client_ip or "") not in LOOPBACK:
            self._refused(BENCH_LOOPBACK)
        if self._stream_up():
            self._refused(BENCH_STREAM_UP)
        game, _system, _kind = self._live._running()
        if game is None:
            self._refused("no game is running")
        status = self._emu.resume()
        self._row({"step": "bench_release", "game": game, "paused": bool(status.get("paused"))})
        return {"ok": True, "released": not bool(status.get("paused")), "game": game}

    def stop(self) -> dict:
        """B105: `POST h7-stop` — the watch ends; nothing is sent to the game."""
        with self._lock:
            w = self._watch
            if w is None:
                return {"ok": True, "watch": "none"}
            self._watch = None
            self._stopped = None
            self._row({"step": "stopped_by_call", "game": w["game"], "reads": w["reads"], "state": w["state"]})
            return {"ok": True, "watch": "stopped", "game": w["game"], "reads": w["reads"]}

    def _keep_folder(self, game: str) -> Path | None:
        """runtime/h7_frames/<game id>_<UTC stamp>/ with its index.csv header (None + one row when it cannot be made)."""
        try:
            base = Path(self._project_path(KEEP_RELATIVE))
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            d = base / f"{game}_{stamp}"
            n = 1
            while d.exists():
                n += 1
                d = base / f"{game}_{stamp}_{n}"
            d.mkdir(parents=True)
            with (d / "index.csv").open("w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(["seconds", "utc", "file", "class", "screen", "margin", "distances", "keep_ms"])
            return d
        except OSError as exc:
            self._row({"step": "keep_failed", "game": game, "why": str(exc)[:200]})
            return None

    def _stream_up(self) -> bool:
        try:
            return bool((self._stream.status() or {}).get("active"))
        except Exception:
            return False

    # --- the watcher ---------------------------------------------------------------------------------------------
    def _mine(self, token) -> dict | None:
        """B105: the watch this token started, watching or just ended (its last picture is still kept)."""
        w = self._watch
        return w if (w is not None and w.get("token") is token) else None

    def _current(self, token) -> dict | None:
        w = self._watch
        return w if (w is not None and w.get("token") is token and w["state"] == "watching") else None

    def _settle(self, w: dict, value: bool, since: float, r: dict | None) -> None:
        """B105: `recognised` settles once (under the lock), one row."""
        w["recognised"] = value
        self._row({"step": "recognised", "game": w["game"], "value": value, "after_s": since, "reads": w["reads"],
                   "class": (r or {}).get("class"), "distances": (r or {}).get("distances")})

    def _keep(self, token, keep_dir: Path, img, since: float, r: dict) -> None:
        """B105: the picture as it was read, and its index row (keeping stops at the first failure, one row)."""
        t0 = time.perf_counter()
        try:
            with self._lock:
                w = self._mine(token)
                if w is None or w.get("_keep_dir") is None:
                    return
                n = w["keep"]["pictures"] + 1
            name = f"f{n:06d}.jpg"
            pic = img if getattr(img, "mode", "RGB") in ("L", "RGB") else img.convert("RGB")
            buf = io.BytesIO()
            pic.save(buf, "JPEG", quality=JPEG_QUALITY)
            (keep_dir / name).write_bytes(buf.getvalue())
            ms = round((time.perf_counter() - t0) * 1000.0, 2)
            now = time.time()
            utc = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now)) + f".{int(now * 1000) % 1000:03d}Z"
            with (keep_dir / "index.csv").open("a", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow([f"{since:.2f}", utc, name, r["class"], r["distances"].get("screen"),
                                         r.get("margin"), json.dumps(r["distances"], sort_keys=True), ms])
            with self._lock:
                w = self._mine(token)
                if w is not None and w.get("keep"):
                    w["keep"]["pictures"] = n
        except OSError as exc:
            with self._lock:
                w = self._mine(token)
                if w is None:
                    return
                w["_keep_dir"] = None
                self._row({"step": "keep_failed", "game": w["game"], "why": str(exc)[:200]})

    def _run(self, token, game: str, reader, ended, spec: dict) -> None:
        t0 = self._clock()
        k = 1
        last_class = None
        start_class = spec["start_class"]
        thresholds = endscreen().thresholds(spec) if hasattr(endscreen(), "thresholds") else None
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
                        w = self._current(token)
                        if w is None:
                            return
                        w["picture_failures"] += 1
                        self._row({"step": "picture_failed", "game": game, "why": str(exc)[:200]})
                        since = round(self._clock() - w["t0"], 1)
                        if w["recognised"] is None and w["loaded"] and since >= self.recognise_s:
                            self._settle(w, False, since, None)
                    continue
                r = reader.read(img)
                seen_before = ended.seen_start
                done = ended.feed(r["class"], r.get("places"))         # B123: version 3 ends on the whole row
                with self._lock:
                    w = self._current(token)
                    if w is None:
                        return
                    w["reads"] += 1
                    w["class"] = r["class"]
                    w["seen_start"] = ended.seen_start
                    w["last"] = {"class": r["class"], "distances": r["distances"], "margin": r["margin"],
                                 "thresholds": thresholds, "spec_version": spec.get("version")}
                    reads = w["reads"]
                    since = round(self._clock() - w["t0"], 1)
                    keep_dir = w.get("_keep_dir")
                    if w["recognised"] is None:
                        if r["class"] == start_class:
                            self._settle(w, True, since, r)
                        elif w["loaded"] and since >= self.recognise_s:
                            self._settle(w, False, since, r)
                    if done:
                        w.update(state="ended", **{"class": done}, ended_after_s=since)
                        if getattr(ended, "places", None):              # B123: a version-3 spec's row of places
                            w["places"] = list(ended.places)
                    if ended.seen_start and not seen_before:
                        self._row({"step": "start_seen", "game": game, "after_s": since, "reads": reads})
                    if r["class"] == endscreen().UNKNOWN and last_class != endscreen().UNKNOWN:
                        self._row({"step": "unknown_screen", "game": game, "after_s": since,
                                   "distances": r["distances"], "margin": r["margin"]})
                    if done:
                        self._row({"step": "ended", "game": game, "class": done, "after_s": since, "reads": reads,
                                   **({"places": list(ended.places)} if getattr(ended, "places", None) else {})})
                last_class = r["class"]
                if keep_dir is not None:
                    self._keep(token, keep_dir, img, since, r)
                if done:
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
