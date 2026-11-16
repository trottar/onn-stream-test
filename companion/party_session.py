"""B108: the board game (PrivyParty, a Godot project) as a launch the hub can stream, pause and end like a game.

Only with PRIVYHUB_PARTY=1 (`games/emulator_manager.py` and `plugins/games.py` import this module then; absent / 0 =
today: nothing imported, no system, entry, route, field or log).

The board is one game entry in its own system ("PrivyParty"); the onn launches it as any game (no client change).
Its paths come from a small config file off the repo (`PRIVYHUB_PARTY_CONFIG`, else
`$XDG_CONFIG_HOME/privyhub/party.json`): `{"godot", "project", "pictures", "renderer"}` — absent or incomplete → a
plain refusal; the renderer `gl_compatibility` (default) or `mobile`. The executable is started directly (no shell),
so its pid owns its window and its sound stream, which the stream's capture and audio find by pid as for PCSX2 /
Dolphin. `--fullscreen` (Godot's own switch) covers the panel; the window is also found by its title class and its pid
checked. Home → the board's `pause` action (Esc once; its pause is a toggle, so the state is kept here, and nothing is
sent before the board's first release); RESUME → Esc once if paused by key; SAVE / LOAD / the recovery's states →
refused plainly, nothing sent; END → the `quit` action (F10 by XTEST), the exit awaited QUIT_WAIT_S, its code in a
row; no exit → SIGTERM (a row), then SIGKILL. One row per step in logs/games/party.jsonl (field names, never paths).
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

SYSTEM_ID = "party"
SYSTEM_NAME = "PrivyParty"
TITLE = "PrivyParty"
RELATIVE_PATH = "party/privyparty"
LAUNCH_KIND = "godot"
WINDOW_CLASS = "PrivyParty"          # Godot's window: class "Godot_Engine", "PrivyParty" (PP-H1)
RENDERERS = {"gl_compatibility": "opengl3", "mobile": "vulkan"}
DEFAULT_RENDERER = "gl_compatibility"
FIELDS = ("godot", "project", "pictures")
WINDOW_WAIT_S = 15.0
AUDIO_WAIT_S = 15.0
QUIT_WAIT_S = 8.0                    # END: F10, then this long for the exit before SIGTERM
KILL_WAIT_S = 5.0
LOG_RELATIVE = "logs/games/party.jsonl"
PAUSE_KEY = "Escape"                 # the board's `pause` action (Esc, P, a pad's Start)
QUIT_KEY = "F10"                     # the board's `quit` action
DEVICES = Path("/proc/bus/input/devices")
PAD_NAME = re.compile(r"PrivyHub Virtual Gamepad P(\d)")

NO_STATES = "Saving and loading are not offered for the board game; nothing was sent."
NO_EXTRAS = "Cheats and mods are not offered for the board game."
NO_CONFIG = "The board game is not set up on this hub (no config file)"
BAD_RENDERER = "The board game's renderer must be gl_compatibility or mobile"

# SDL's mapping of the companion's uinput pad (0x1209 / 0x5048), as PCSX2 gets it (ps2_session.SDL_MAPPING)
SDL_MAPPING = (
    "03000000091200004850000001000000,PrivyHub Virtual Gamepad,"
    "a:b0,b:b1,y:b2,x:b3,leftshoulder:b4,rightshoulder:b5,back:b6,start:b7,leftstick:b8,rightstick:b9,"
    "leftx:a0,lefty:a1,lefttrigger:a2,rightx:a3,righty:a4,righttrigger:a5,"
    "dpup:h0.1,dpright:h0.2,dpdown:h0.4,dpleft:h0.8,platform:Linux,"
)

_POPEN = subprocess.Popen            # the board's own starter (taken at import)


class PartyError(RuntimeError):
    """A plain refusal the onn can show."""


# --- the config -------------------------------------------------------------------------------------------------------
def config_path(environ=os.environ) -> Path:
    named = (environ.get("PRIVYHUB_PARTY_CONFIG") or "").strip()
    if named:
        return Path(named)
    base = (environ.get("XDG_CONFIG_HOME") or "").strip() or str(Path(environ.get("HOME") or "~").expanduser() / ".config")
    return Path(base) / "privyhub" / "party.json"


def read_config(environ=os.environ) -> dict[str, str]:
    """{"godot", "project", "pictures", "renderer"} or PartyError with the plain line."""
    path = config_path(environ)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PartyError(NO_CONFIG) from None
    except (OSError, ValueError):
        raise PartyError("The board game's config file cannot be read") from None
    if not isinstance(data, dict):
        raise PartyError("The board game's config file cannot be read")
    for field in FIELDS:
        if not str(data.get(field) or "").strip():
            raise PartyError(f"The board game's config is incomplete: {field}")
    renderer = str(data.get("renderer") or "").strip() or DEFAULT_RENDERER
    if renderer not in RENDERERS:
        raise PartyError(BAD_RENDERER)
    cfg = {f: str(data[f]).strip() for f in FIELDS}
    cfg["renderer"] = renderer
    if not Path(cfg["godot"]).is_file():
        raise PartyError("The board game's godot was not found")
    if not (Path(cfg["project"]) / "project.godot").is_file():
        raise PartyError("The board game's project was not found")
    if not Path(cfg["pictures"]).is_dir():
        raise PartyError("The board game's pictures was not found")
    return cfg


def command(cfg: dict[str, str]) -> list[str]:
    return [cfg["godot"], "--path", cfg["project"], "--rendering-method", cfg["renderer"],
            "--rendering-driver", RENDERERS[cfg["renderer"]], "--fullscreen", "--", "--content=" + cfg["pictures"]]


def launch_env(environ=os.environ) -> dict[str, str]:
    env = dict(environ)
    have = env.get("SDL_GAMECONTROLLERCONFIG", "")
    env["SDL_GAMECONTROLLERCONFIG"] = (have + "\n" if have else "") + SDL_MAPPING
    return env


def titles_for_plugin(stable_id: Callable[[str, str], str]) -> list[dict[str, Any]]:
    return [{"id": stable_id(SYSTEM_ID, RELATIVE_PATH), "title": TITLE, "system": SYSTEM_ID,
             "system_name": SYSTEM_NAME, "relative_path": RELATIVE_PATH, "format": "godot", "size_bytes": 0}]


def active(emulator: Any) -> bool:
    return getattr(emulator, "_launch_kind", None) == LAUNCH_KIND and getattr(emulator, "_party", None) is not None


# --- the rows ---------------------------------------------------------------------------------------------------------
def row(project_path: Callable[[str], Any], fields: dict[str, Any]) -> None:
    try:
        path = Path(project_path(LOG_RELATIVE))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"time_unix": round(time.time(), 3), **fields}, sort_keys=True) + "\n")
    except OSError:
        pass


# --- the running board ------------------------------------------------------------------------------------------------
def _run(cmd: list[str], timeout: float = 3.0) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def pads_in_order(devices: Path = DEVICES) -> list[dict[str, Any]]:
    """The virtual pads as the system lists them: [{"player", "event"}] in event order (the order SDL finds them)."""
    try:
        text = devices.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    found = []
    for block in text.split("\n\n"):
        m = PAD_NAME.search(block)
        e = re.search(r"Handlers=.*?\bevent(\d+)", block)
        if m and e:
            found.append({"player": int(m.group(1)), "event": int(e.group(1))})
    return sorted(found, key=lambda d: d["event"])


class Session:
    """The board's process: its window, its sound stream, pause / resume by its own keys, the quit."""

    def __init__(self, pid: int, log_row: Callable[[dict], None], run: Callable[..., Any] | None = None,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep,
                 kill: Callable[[int, int], None] = os.kill, devices: Path = DEVICES):
        self.pid = int(pid)
        self.row = log_row
        self.run = run or _run
        self.clock, self.sleep, self.kill = clock, sleep, kill
        self.devices = devices
        self.window_id: str | None = None
        self.released = False          # the board's first native-stream-ready seen
        self.paused_by_key = False

    # -- the window and the sound --------------------------------------------------------------------------------
    def find_window(self) -> str | None:
        """The board's window by its title class, its pid the launched one (the capture finds it by that pid)."""
        try:
            r = self.run(["xdotool", "search", "--onlyvisible", "--class", WINDOW_CLASS])
        except Exception:
            return None
        for w in [x.strip() for x in (getattr(r, "stdout", "") or "").splitlines() if x.strip().isdigit()]:
            try:
                p = self.run(["xdotool", "getwindowpid", w])
            except Exception:
                continue
            if (getattr(p, "stdout", "") or "").strip() == str(self.pid):
                return w
        return None

    def wait_window(self, alive: Callable[[], bool], bound: float = WINDOW_WAIT_S) -> float | None:
        t0 = self.clock()
        while self.clock() - t0 < bound and alive():
            w = self.find_window()
            if w:
                self.window_id = w
                return self.clock() - t0
            self.sleep(0.25)
        return None

    def wait_audio(self, alive: Callable[[], bool], bound: float = AUDIO_WAIT_S) -> float | None:
        t0 = self.clock()
        while self.clock() - t0 < bound and alive():
            try:
                r = self.run(["pactl", "list", "sink-inputs"])
                if f'application.process.id = "{self.pid}"' in (getattr(r, "stdout", "") or ""):
                    return self.clock() - t0
            except Exception:
                pass
            self.sleep(0.25)
        return None

    # -- keys --------------------------------------------------------------------------------------------------------
    def key(self, name: str) -> None:
        """One key by XTEST to the board's window (activated first: the window the keyboard goes to)."""
        if not self.window_id:
            self.window_id = self.find_window()
        if not self.window_id:
            raise PartyError("the board's window was not found")
        r = self.run(["xdotool", "windowactivate", "--sync", self.window_id, "key", "--clearmodifiers", name])
        if getattr(r, "returncode", 1) != 0:
            raise PartyError(f"the key {name} was not sent")

    def pause(self) -> str:
        if not self.released:
            self.row({"step": "pause", "key": None, "why": "not released yet (the lobby): nothing sent"})
            return "held"
        if self.paused_by_key:
            self.row({"step": "pause", "key": None, "why": "already paused"})
            return "already"
        self.key(PAUSE_KEY)
        self.paused_by_key = True
        self.row({"step": "pause", "key": PAUSE_KEY})
        return "key"

    def resume(self) -> str:
        first = not self.released
        self.released = True
        if not self.paused_by_key:
            self.row({"step": "resume", "key": None, "why": "first release" if first else "not paused by key"})
            return "released"
        self.key(PAUSE_KEY)
        self.paused_by_key = False
        self.row({"step": "resume", "key": PAUSE_KEY})
        return "key"

    # -- the exit ----------------------------------------------------------------------------------------------------
    def stop(self, process: Any) -> str:
        t0 = self.clock()
        if process.poll() is not None:
            self.row({"step": "exited", "code": process.returncode, "seconds": 0.0, "why": "already gone"})
            return "gone"
        try:
            self.key(QUIT_KEY)
            self.row({"step": "quit", "key": QUIT_KEY})
        except Exception as exc:
            self.row({"step": "quit", "key": QUIT_KEY, "failed": str(exc)[:120]})
        try:
            code = process.wait(timeout=QUIT_WAIT_S)
            self.row({"step": "exited", "code": code, "seconds": round(self.clock() - t0, 2)})
            return f"quit {code}"
        except subprocess.TimeoutExpired:
            pass
        try:
            self.kill(self.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        self.row({"step": "sigterm", "after_s": QUIT_WAIT_S, "why": f"no exit {QUIT_WAIT_S:.0f} s after F10"})
        try:
            code = process.wait(timeout=KILL_WAIT_S)
            self.row({"step": "exited", "code": code, "seconds": round(self.clock() - t0, 2), "by": "sigterm"})
            return f"sigterm {code}"
        except subprocess.TimeoutExpired:
            try:
                self.kill(self.pid, signal.SIGKILL)
                process.wait(timeout=KILL_WAIT_S)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            self.row({"step": "sigkill", "after_s": QUIT_WAIT_S + KILL_WAIT_S})
            return "sigkill"


def start(cfg: dict[str, str], log_handle: Any, environ=os.environ) -> Any:
    return _POPEN(command(cfg), cwd=cfg["project"], stdin=subprocess.DEVNULL, stdout=log_handle,
                  stderr=subprocess.STDOUT, env=launch_env(environ), start_new_session=True)
