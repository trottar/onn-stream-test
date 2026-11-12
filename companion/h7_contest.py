"""B101 (H7): the timed contest — a kept state loaded into the running game, a fixed time, the leader when it ends.

Only with PRIVYHUB_H7=1 (`plugins/games.py` imports this module then; absent / 0 = today: neither route exists).
`POST /plugins/games/h7-contest?seconds=N` (5 <= N <= 300): for the running RetroArch game (PS1 or SNES) with a rule
(B99's `<rules folder>/<game id>.json`) and a state beside it (`<game id>.state`) while the stream is up: the state is
loaded into the running game through scratch slot 8 (`<stem>.state8` in the core's state folder, removed after;
RetroArch's own load line required), the contest arms when the values first differ from the state's own (the bars
filling; at most ARM_WAIT s), runs N seconds with a read every second (`samples`), and at "time is up" reads once more:
the leader is the winner. The game is never paused, saved, written or cheated; it ends running (the onn cannot resume
a pause it did not ask for — B101's record). `GET /plugins/games/h7-contest` → the running contest or the last outcome.
One row per step in logs/games/h7_contests.jsonl.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
from pathlib import Path
from typing import Any

import h7_live_read as live

MIN_SECONDS, MAX_SECONDS = 5, 300
SCRATCH_SLOT = 8               # never the user's 1-3, the hub's 0, the rewind's 9 or the recovery's .state.recovery
LOCK_WAIT = 2.0                # s: the manager's lock for the load (the hub's own LOAD holds it the same way)
LOAD_LINE_WAIT = 1.5           # s: RetroArch's load line (settled: 32-34 ms)
ARM_WAIT = 20.0                # s: the values must leave the state's own within this
ARM_POLL = 0.25                # s
SAMPLE_EVERY = 1.0             # s
LOG_RELATIVE = "logs/games/h7_contests.jsonl"
CORE_FOLDERS = {"mednafen_psx_hw_libretro": "Beetle PSX HW", "mednafen_psx_libretro": "Beetle PSX",
                "snes9x_libretro": "Snes9x", "bsnes_libretro": "bsnes"}          # RetroArch's per-core state folders
LOADING = re.compile(r'\[State\] Loading state ".*", (\d+) bytes\.')
SYSTEMS = ("ps1", "snes")


class Ended(Exception):
    """The contest ends without an answer (the game stopped, the stream stopped)."""


class Contest:
    def __init__(self, emulator: Any, reader: "live.LiveRead", native_stream: Any, project_path,
                 environ=os.environ, clock=time.monotonic):
        self._emu = emulator
        self._reader = reader
        self._stream = native_stream
        self._project_path = project_path
        self._environ = environ
        self._clock = clock
        self._lock = threading.Lock()
        self._current: dict | None = None        # the running contest's state, or the last outcome

    # --- the routes ----------------------------------------------------------------------------------------------
    def status(self) -> dict:
        with self._lock:
            if self._current is None:
                return {"ok": True, "contest": None}
            out = json.loads(json.dumps(self._current))
        if out.get("state") in ("arming", "running") and out.get("t0") is not None:
            out["elapsed_s"] = round(self._clock() - out["t0"], 1)
        out.pop("t0", None)
        return {"ok": True, "contest": out}

    def start(self, seconds_text: str) -> dict:
        try:
            seconds = int(str(seconds_text).strip())
        except ValueError:
            raise ValueError(f"seconds must be a whole number from {MIN_SECONDS} to {MAX_SECONDS}") from None
        if not MIN_SECONDS <= seconds <= MAX_SECONDS:
            raise ValueError(f"seconds must be a whole number from {MIN_SECONDS} to {MAX_SECONDS}")
        with self._lock:
            if self._current is not None and self._current.get("state") in ("loading", "arming", "running"):
                self._refused("a contest is already running")
            previous, self._current = self._current, {"state": "loading", "seconds": seconds}
        try:
            game, system, rule, state, folder, stem = self._checks()
            loaded = self._load(game, state, folder, stem)
        except Exception:
            with self._lock:
                self._current = previous                    # a refused start leaves the last outcome as it was
            raise
        own = self._reader._read(game, rule)
        with self._lock:
            self._current = {"state": "arming", "seconds": seconds, "game": game, "t0": self._clock(),
                             "load_line_ms": loaded, "state_values": own["values"], "samples": []}
        threading.Thread(target=self._run, args=(game, rule, seconds, own["values"]), daemon=True,
                         name="h7-contest").start()
        return {"ok": True, "contest": "started", "game": game, "seconds": seconds, "load_line_ms": loaded,
                "state_values": own["values"]}

    # --- (1) the checks --------------------------------------------------------------------------------------------
    def _refused(self, why: str):
        self._row({"step": "refused", "why": why})
        raise ValueError(why)

    def _checks(self):
        try:
            game, system, kind = self._reader._running()
        except RuntimeError as exc:
            self._refused(str(exc))
        if game is None:
            self._refused("no game is running")
        if kind in ("pcsx2", "dolphin"):
            self._refused("not supported yet")
        if system == "n64":
            self._refused("not supported yet — a state cannot be loaded into a running N64 game")
        if system not in SYSTEMS:
            self._refused("not supported yet")
        try:
            rule = self._reader._rule(game)
        except ValueError as exc:
            self._refused(str(exc))
        state = live.rules_folder(self._environ) / f"{game}.state"
        if not state.is_file() or state.stat().st_size <= 0:
            self._refused("no state for this game's contest")
        try:
            active = bool((self._stream.status() or {}).get("active"))
        except Exception:
            active = False
        if not active:
            self._refused("the stream is not up")
        core = self._core_file(system)
        folder_name = CORE_FOLDERS.get(core[:-len(".so")] if core.endswith(".so") else core)
        if folder_name is None:
            self._refused("not supported yet with this game's core")
        stem = self._emu._active_state_stem()
        folder = self._emu._state_root() / folder_name
        return game, system, rule, state, folder, stem

    def _core_file(self, system: str) -> str:
        if system == "snes":
            snes = (self._environ.get("PRIVYHUB_SNES_CORE") or "").strip()
            if snes:
                return f"{snes}_libretro.so"
        core = str(self._emu._runtime_details()["core_status"].get(system, {}).get("core", ""))
        return re.sub(r"\.(dll|dylib)$", ".so", core)

    # --- (2) the load ------------------------------------------------------------------------------------------------
    def _load(self, game: str, state: Path, folder: Path, stem: str) -> float:
        emu = self._emu
        scratch = folder / f"{stem}.state{SCRATCH_SLOT}"
        if not emu.lock.acquire(timeout=LOCK_WAIT):
            self._refused("the game is busy (a save or a load); try again")
        try:
            if scratch.exists():
                self._refused("a scratch state is already in the game's state folder; not loaded")
            folder.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copyfile(state, scratch)
                offset = emu._retroarch_session_log_position()
                t0 = self._clock()
                try:
                    answer = emu._retroarch_network_request(f"LOAD_STATE_SLOT {SCRATCH_SLOT}", expect_response=True,
                                                            timeout=2.0, retries=1)
                except RuntimeError:
                    answer = None
                ok, line_ms = False, None
                if answer and answer.upper().startswith(f"LOAD_STATE_SLOT {SCRATCH_SLOT}"):
                    end = self._clock() + LOAD_LINE_WAIT
                    while self._clock() < end:
                        text = "\n".join(emu._retroarch_session_log_since(offset))
                        if "failed to load state" in text.casefold():
                            break
                        m = LOADING.search(text)
                        if m and int(m.group(1)) > 0:
                            ok, line_ms = True, round((self._clock() - t0) * 1000.0, 1)
                            break
                        time.sleep(0.01)
            finally:
                try:
                    scratch.unlink()
                except FileNotFoundError:
                    pass
        finally:
            emu.lock.release()
        if not ok:
            self._row({"step": "error", "game": game, "why": "the state did not load"})
            raise live.Busy("the contest's state did not load; the game is as it was")
        self._row({"step": "loaded", "game": game, "load_line_ms": line_ms})
        return line_ms

    # --- (3)-(5) the run -----------------------------------------------------------------------------------------
    def _still(self, game: str) -> None:
        try:
            now, _system, _kind = self._reader._running()
        except RuntimeError:
            return                                              # busy: checked again at the next step
        if now != game:
            raise Ended("the game stopped")
        try:
            if not bool((self._stream.status() or {}).get("active")):
                raise Ended("the stream stopped")
        except Ended:
            raise
        except Exception:
            pass

    def _sample(self, game: str, rule: dict) -> dict | None:
        try:
            return self._reader._read(game, rule)
        except RuntimeError:
            return None                                         # a read not answered: no sample, not a value

    def _run(self, game: str, rule: dict, seconds: int, own: dict) -> None:
        try:
            t_load = self._clock()
            armed = None
            while self._clock() - t_load < ARM_WAIT:
                self._still(game)
                r = self._sample(game, rule)
                if r is not None and r["values"] != own:
                    armed = r
                    break
                time.sleep(ARM_POLL)
            if armed is None:
                why = f"the fight did not start within {ARM_WAIT:g} s; the game left running"
                self._row({"step": "not_armed", "game": game, "why": why})
                self._finish({"state": "error", "seconds": seconds, "game": game, "error": why})
                return
            t_arm = self._clock()
            armed_after = round(t_arm - t_load, 2)
            names = list(armed["values"])
            base = [armed["values"][n] for n in names]
            self._row({"step": "armed", "game": game, "armed_after_s": armed_after, "values": armed["values"]})
            samples = [[0.0, *base]]
            resets, lowered = 0, False
            with self._lock:
                self._current.update(state="running", t0=t_arm, armed_after_s=armed_after, samples=samples)
            k = 1
            while True:
                next_at = t_arm + k * SAMPLE_EVERY
                if next_at >= t_arm + seconds:
                    break
                time.sleep(max(0.0, next_at - self._clock()))
                self._still(game)
                r = self._sample(game, rule)
                if r is not None:
                    vals = [r["values"][n] for n in names]
                    samples.append([round(self._clock() - t_arm, 1), *vals])
                    if any(v < b for v, b in zip(vals, base)):
                        lowered = True
                    elif lowered and vals == base:
                        resets += 1
                        lowered = False
                k += 1
            time.sleep(max(0.0, t_arm + seconds - self._clock()))
            self._still(game)
            final = self._reader._read(game, rule)
            vals = [final["values"][n] for n in names]
            if lowered and vals == base:
                resets += 1
            samples.append([round(self._clock() - t_arm, 1), *vals])
            answer = {"ok": True, "game": game, "winner": final["winner"], "reason": final["reason"],
                      "values": final["values"], "seconds": seconds, "armed_after_s": armed_after, "samples": samples,
                      "resets_seen": resets, "ended": "running"}
            self._row({"step": "done", **{k2: v for k2, v in answer.items() if k2 != "ok"}})
            self._finish({"state": "done", **answer})
        except Ended as exc:
            self._row({"step": "ended", "game": game, "why": str(exc)})
            self._finish({"state": "ended", "seconds": seconds, "game": game, "why": str(exc)})
        except Exception as exc:                                    # a final read that failed, anything else
            self._row({"step": "error", "game": game, "why": str(exc)})
            self._finish({"state": "error", "seconds": seconds, "game": game, "error": str(exc)})

    def _finish(self, outcome: dict) -> None:
        with self._lock:
            self._current = outcome

    def _row(self, fields: dict) -> None:
        try:
            path = Path(self._project_path(LOG_RELATIVE))
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"time_unix": round(time.time(), 3), **fields}, sort_keys=True) + "\n")
        except OSError:
            pass
