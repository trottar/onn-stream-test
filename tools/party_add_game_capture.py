#!/usr/bin/env python3
"""B157: the add-a-game tool's picture source on the hub — a kept state loaded paused in a headless RetroArch, then
run forward with no pads, a picture every `every` seconds (H7-V1's capture, B95's Session: the hub's AppImage, its
persistent config as the base, temp saves / states / system folders, the null joypad driver, the game file read in
place; the screenshot folder in the temp folder). Nothing is written beside the game file or in the user's folders.

B167 — it starts as H7-V1's did and as the hub launches the title:
- **the hub's display** (`DISPLAY`, `XAUTHORITY` from the caller, else from the user manager the companion runs under):
  without one RetroArch cannot open its video driver and exits at startup (the first use's "exited during startup");
- **the hub's own core** for the system (`emulators.json`'s Linux core; the N64 session's) and its states folder;
- **the hub's own core options** (the core's `.opt` and the title's own, read only from the user's RetroArch config,
  copied into the temp config, `game_specific_options` on: the picture drawn as the hub draws it);
- **every failure a reason** (`CaptureError(reason, words)`: busy, display, content not found, core missing, config,
  exited, not playing, state refused — fixed words, no name), and RetroArch's own log copied to `log_to` (the title's
  add_game folder, off the repo) whatever the end.

`capture(state, binding, out_dir, seconds, every, log_to=None) -> [(seconds, file name)]`: frames as JPEG (quality 90,
at most 640 px wide) in `out_dir`. The tests replace this module (PARTY_ADD_GAME_CAPTURE) with made-up pictures, or
the AppImage with a made-up one (PRIVYHUB_ADD_GAME_RA_APP, PRIVYHUB_ADD_GAME_RA_CORES, PRIVYHUB_ADD_GAME_RA_CONFIG,
PRIVYHUB_ADD_GAME_RA_BASE).
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import h7_minigame_proof as proof  # noqa: E402  (B95's tool, imported, not edited)

START_BOUND_S = 30.0
# the core's file -> RetroArch's folder name for it (its states and its core options)
CORE_FOLDER = {"bsnes_libretro.so": "bsnes", "snes9x_libretro.so": "Snes9x",
               "mednafen_psx_hw_libretro.so": "Beetle PSX HW", "mupen64plus_next_libretro.so": "Mupen64Plus-Next"}
N64_CORE = "mupen64plus_next_libretro.so"            # companion/n64_session.py's DEFAULT_CORE
WORDS = {                                            # fixed, name-free words per reason
    "busy": "a game or a client's stream is up on the hub: nothing started",
    "display": "RetroArch could not open a window: no display was given to it (the hub's display is needed)",
    "content not found": "the game file was not found",
    "core missing": "the hub's core for this system is not in the cores folder",
    "config": "RetroArch could not read its config",
    "exited": "RetroArch stopped during startup; its log names no known reason",
    "not playing": "RetroArch did not start playing in time",
    "state refused": "RetroArch did not load the kept state",
}
LOG_REASONS = (                                       # RetroArch's own log line -> the reason (first match wins)
    ("Cannot open video driver", "display"),
    ("Failed to load content", "content not found"),
    ("Could not read content", "content not found"),
    ("Failed to open libretro core", "core missing"),
    ("Failed to load config", "config"),
    ("Could not read config", "config"),
)


class CaptureError(RuntimeError):
    def __init__(self, reason: str):
        self.reason, self.words = reason, WORDS[reason]
        super().__init__(f"{reason}: {self.words}")


def _app() -> Path:
    v = os.environ.get("PRIVYHUB_ADD_GAME_RA_APP", "").strip()
    return Path(v) if v else proof.APP


def _cores() -> Path:
    v = os.environ.get("PRIVYHUB_ADD_GAME_RA_CORES", "").strip()
    return Path(v) if v else proof.CORES


def hub_core(system: str) -> str:
    """The core the hub launches the system with: emulators.json's Linux core (ps1, snes), the N64 session's."""
    if system == "n64":
        return N64_CORE
    cfg = json.loads((proof.REPO / "companion/games/config/emulators.json").read_text())
    core = ((cfg.get("platforms") or {}).get("linux") or {}).get("cores", {}).get(system)
    if not core:
        raise CaptureError("core missing")
    return str(core)


def hub_display(environ=os.environ, systemctl: str | None = None) -> dict:
    """DISPLAY / XAUTHORITY from the caller's environment, else from the user manager's (the companion's)."""
    systemctl = systemctl or os.environ.get("PRIVYHUB_ADD_GAME_SYSTEMCTL", "systemctl")
    out = {k: environ[k] for k in ("DISPLAY", "XAUTHORITY") if environ.get(k)}
    if "DISPLAY" not in out:
        try:
            r = subprocess.run(systemctl.split() + ["--user", "show-environment"], capture_output=True, text=True,
                               timeout=10)
            for ln in r.stdout.splitlines():
                k, _, v = ln.partition("=")
                if k in ("DISPLAY", "XAUTHORITY") and v and k not in out:
                    out[k] = v
        except (OSError, subprocess.SubprocessError):
            pass
    if "DISPLAY" not in out:
        raise CaptureError("display")
    return out


def _base_config() -> Path:
    v = os.environ.get("PRIVYHUB_ADD_GAME_RA_BASE", "").strip()
    return Path(v) if v else proof.REPO / "data/games/retroarch/retroarch.cfg"


def _user_config() -> Path:
    v = os.environ.get("PRIVYHUB_ADD_GAME_RA_CONFIG", "").strip()
    if v:
        return Path(v)
    base = os.environ.get("XDG_CONFIG_HOME", "").strip() or str(Path.home() / ".config")
    return Path(base) / "retroarch" / "config"


def hub_busy() -> bool:
    """A game running or a client's stream up on the hub (its status routes on loopback); a hub that does not answer
    has nothing running to protect."""
    import urllib.request
    base = os.environ.get("PRIVYHUB_ADD_GAME_HUB", "http://127.0.0.1:8765").rstrip("/") + "/plugins/games/"
    for action in ("status", "native-stream-status"):
        try:
            with urllib.request.urlopen(base + action, timeout=5) as r:
                if json.loads(r.read().decode() or "{}").get("active"):
                    return True
        except Exception:
            continue
    return False


def reason_of_log(text: str) -> str:
    for line, reason in LOG_REASONS:
        if line in text:
            return reason
    return "exited"


class _Session(proof.Session):
    """B95's Session started as the hub starts the title (B167): its display, its core, its core options; with the
    screenshot folder added (H7-V1's CaptureSession, without the memory reads)."""

    def __init__(self, content: Path, system: str, work: Path, display: dict):
        self.core = hub_core(system)
        self.library = CORE_FOLDER.get(self.core, Path(self.core).stem)
        self.work = work
        for d in ("saves", "states", "system", "xdg", "cheats", "shots"):
            (work / d).mkdir(parents=True, exist_ok=True)
        if not (_cores() / self.core).is_file():
            raise CaptureError("core missing")
        self.content = Path(content).resolve()
        if not self.content.is_file():
            raise CaptureError("content not found")
        optdir = work / "xdg" / "retroarch" / "config" / self.library
        optdir.mkdir(parents=True, exist_ok=True)
        self.opts = []
        for name in (f"{self.library}.opt", f"{self.content.stem}.opt"):   # read only, copied
            src = _user_config() / self.library / name
            if src.is_file():
                shutil.copyfile(src, optdir / name)
                self.opts.append("core" if name == f"{self.library}.opt" else "title")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        self.port = s.getsockname()[1]
        s.close()
        try:                                                     # the hub's persistent config, the base
            base = _base_config().read_text()
        except OSError:
            raise CaptureError("config") from None
        over = {"savefile_directory": work / "saves", "savestate_directory": work / "states",
                "system_directory": work / "system", "cheat_database_path": work / "cheats",
                "network_cmd_enable": "true", "network_cmd_port": self.port, "input_joypad_driver": "null",
                "history_list_enable": "false", "config_save_on_exit": "false", "savestate_auto_save": "false",
                "savestate_auto_load": "false", "savestate_thumbnail_enable": "false",
                "joypad_autoconfig_dir": work / "system", "pause_nonactive": "false",
                "screenshot_directory": work / "shots", "screenshots_in_content_dir": "false",
                "auto_screenshot_filename": "true", "notification_show_screenshot": "false",
                "video_font_enable": "false", "game_specific_options": "true"}
        lines = [ln for ln in base.splitlines() if ln.split("=")[0].strip() not in over]
        (work / "session.cfg").write_text("\n".join(lines + [f'{k} = "{v}"' for k, v in over.items()]) + "\n")
        self.logf = work / "retroarch.log"
        self.log = self.logf.open("w")
        env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY")}
        env.update(display)
        env["XDG_CONFIG_HOME"] = str(work / "xdg")
        app = _app()
        self.proc = subprocess.Popen(
            [str(app), "--config", str(work / "session.cfg"), "--verbose", "-L", str(_cores() / self.core),
             str(self.content)], cwd=str(app.parent), stdin=subprocess.DEVNULL, stdout=self.log,
            stderr=subprocess.STDOUT, env=env, start_new_session=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))

    def resume(self) -> None:
        if "PAUSED" in (self.ask("GET_STATUS", 0.3) or ""):
            self.send("PAUSE_TOGGLE")
            end = time.monotonic() + 3
            while time.monotonic() < end and "PLAYING" not in (self.ask("GET_STATUS", 0.2) or ""):
                time.sleep(0.02)


SHOT_READ_S = 1.5                                    # a screenshot still being written: read again until this


def _read_shot(path: Path):
    """RetroArch's screenshot once it is whole (H7-V1 read again after 0.1 s; at the hub's 4x render scale a PNG takes
    longer to write): its size the same twice 20 ms apart and the picture loads; None if it never does (the frame
    skipped)."""
    end = time.monotonic() + SHOT_READ_S
    last = -1
    while time.monotonic() < end:
        try:
            size = path.stat().st_size
            if size > 0 and size == last:
                with Image.open(path) as im:
                    im.load()
                    return im.convert("RGB")
            last = size
        except (OSError, SyntaxError, ValueError):       # PIL: a partial PNG is OSError or SyntaxError
            last = -1
        time.sleep(0.02)
    return None


def _as_reason(exc: Exception, log_text: str) -> CaptureError:
    """B95's errors (and an unknown one) as a reason; RetroArch's own log decides an exit's."""
    if isinstance(exc, CaptureError):
        return exc
    msg = str(exc)
    if "exited during startup" in msg:
        return CaptureError(reason_of_log(log_text))
    if "did not reach PLAYING" in msg:
        return CaptureError("not playing")
    if "state" in msg and ("load" in msg or "0 bytes" in msg):
        return CaptureError("state refused")
    return CaptureError(reason_of_log(log_text))


def capture(state: Path, binding: dict, out_dir: Path, seconds: float, every: float,
            log_to: Path | None = None) -> list[tuple[float, str]]:
    work = Path(tempfile.mkdtemp(prefix="add_game_capture_"))
    rows: list[tuple[float, str]] = []
    s = None
    try:
        temp_state = work / "copy.state"
        shutil.copyfile(state, temp_state)                      # the kept copy is only read
        try:
            if hub_busy():                                       # never beside a user's game or stream
                raise CaptureError("busy")
            display = hub_display()
            s = _Session(Path(binding["content"]), binding["system"], work, display)
            s.wait_playing(START_BOUND_S)
            s.pause()
            s.load_state(temp_state)
        except Exception as exc:
            if s is None and not isinstance(exc, CaptureError):
                raise                                            # not RetroArch's: the tool names it, keeps its trace
            raise _as_reason(exc, s.text() if s is not None else "") from None
        try:
            shots = work / "shots"
            s.resume()
            t0 = time.monotonic()
            k = 0
            while True:
                target = t0 + k * every
                if target > time.monotonic():
                    time.sleep(target - time.monotonic())
                t = time.monotonic() - t0
                if t > seconds:
                    break
                before = set(shots.iterdir())
                s.send("SCREENSHOT")
                new, end = None, time.monotonic() + 0.45
                while time.monotonic() < end:
                    fresh = [p for p in set(shots.iterdir()) - before if p.suffix == ".png"]
                    if fresh:
                        time.sleep(0.03)
                        new = fresh[0]
                        break
                    time.sleep(0.01)
                im = _read_shot(new) if new is not None else None
                if im is not None:
                    if im.width > 640:
                        im = im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS)
                    name = f"f{k:04d}.jpg"
                    im.save(out_dir / name, quality=90)
                    rows.append((round(k * every, 2), name))
                k += 1
        finally:
            s.close()
    finally:
        if log_to is not None and (work / "retroarch.log").is_file():   # off the repo, whatever the end
            Path(log_to).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / "retroarch.log", log_to)
        if s is not None and s.proc.poll() is None:
            s.close()
        shutil.rmtree(work, ignore_errors=True)
    return rows
