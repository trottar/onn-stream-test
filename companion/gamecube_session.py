"""B69: the GameCube launch kind (`dolphin`), only with `PRIVYHUB_GAMECUBE=1` in the companion's environment.

**Absent = today byte for byte:** the plugin and the emulator manager never import this module, `SYSTEMS` has no
`gamecube`, a `gamecube` launch is today's refusal (no emulator profile), and nothing under `data/games/gamecube/` is
touched.

With the flag (H2-P1's findings, `docs/memory/evidence/H2_P1_GAMECUBE_PROBE_2026-11-09.md`):
- titles are listed read-only in place from the folder `GAMECUBE_DIR=` names in the gitignored paths file
  (`inplace_library`): `.rvz` > `.gcm` > `.iso` > `.ciso`, one per stem; the small `.bin` never (its suffix), nothing
  under 1 MiB (its size). **Nothing is ever written to the drive**;
- Dolphin (the single AppImage in `runtime/emulators/dolphin/`) is launched as `-b -u data/games/gamecube/user -e
  <title>`, its five config files written whole per launch (H2-P1's keys, the FPS overlay off, the hotkeys fixed, the
  four virtual pads in `GCPadNew.ini` by their evdev names, the GameCube layout);
- pause / resume: the F10 hotkey with the window focused (`xdotool`), confirmed by the `CPU thread`'s clock standing /
  growing within 0.5 s, else SIGSTOP / SIGCONT (the method kept). States: Shift+F<n> / F<n>, the file's stable check,
  B52's picture check on a load. Exit: SIGTERM (SIGKILL after 5 s); the AppImage's helper waited for at the next launch;
- four native ports always (no multitap, no relaunch).

Design: `docs/memory/evidence/b69_2026-11-09/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import hashlib
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import inplace_library as _inplace

FLAG_ENV = "PRIVYHUB_GAMECUBE"
DIR_KEY = "GAMECUBE_DIR"
SYSTEM_ID = "gamecube"
SYSTEM_NAME = "GameCube"
RELATIVE_PREFIX = "gamecube/"
SUFFIX_RANK = {".rvz": 0, ".gcm": 1, ".iso": 2, ".ciso": 3}
MIN_TITLE_BYTES = 1 << 20          # a disc image is far larger; the drive's small .bin (and any stub) is not a title
APPIMAGE_DIR = "runtime/emulators/dolphin"
DATA_DIR = "data/games/gamecube"
USER_DIR = DATA_DIR + "/user"
LOGS_DIR = DATA_DIR + "/logs"
PLAN_SOURCE = "gamecube"
PORTS = 4
LAUNCH_KIND = "dolphin"

# the waits (H2-P1: the window by 4 s, the title by ~15 s on a first boot, the sink-input by 12.6 s)
WINDOW_WAIT_S = 30.0
BOOT_WAIT_S = 90.0
AUDIO_WAIT_S = 45.0
# the hotkey and the clock (H2-P1: keydown / 0.12 s / keyup; the CPU thread 13-36 ticks a second running)
KEY_HOLD_S = 0.12
POLL_S = 0.05
STAND_WINDOW_S = 0.5
CONFIRM_S = 1.5
GROW_TICKS = 2
# the exit (H2-P1: SIGTERM 0.31-0.47 s; the AppImage's FUSE helper gone a few seconds later)
TERM_WAIT_S = 5.0
KILL_WAIT_S = 2.0
HELPER_WAIT_S = 10.0
# the states (H2-P1: the file stable <= 0.21 s; a load's picture by 0.2 s)
SAVE_BOUND_S = 1.0
RECOVERY_BOUND_S = 5.0
STABLE_S = 0.25
LOAD_SETTLE_S = 0.5
RELEASE_SHARE_S = 0.45
VERIFY_RUNNING_S = 2.0
PICTURE_BOUND_S = 5.0
PICTURE_STEP_S = 0.2
PICTURE_DISTINCT = 3
PICTURE_BLACK_MEAN = 20
GRAB_W, GRAB_H = 64, 36

USER_SLOTS = (1, 2, 3)
RECOVERY_SLOT = 8
SCRATCH_SLOT = 9
HOTKEY_SLOTS = (1, 2, 3, RECOVERY_SLOT, SCRATCH_SLOT)
PAUSE_KEY = "F10"
CPU_THREAD = "CPU thread"
LIVE_BEHAVIOURS = ("state_save_slot9", "hold_return_load", "stall_resume_load", "recovery_save")
OFF_BEHAVIOURS = ("rewind", "relaunch")
NO_RELAUNCH = "GameCube has four ports; no relaunch"
NO_REWIND = "gamecube: no rewind in Dolphin"
PROC_ROOT = Path("/proc")          # the clock and the helper are read here (a test points it at a fake tree)

HOTKEY_DEVICE = "XInput2/0/Virtual core pointer"
PAD_DEVICE = "evdev/0/PrivyHub Virtual Gamepad P{n}"
# The GameCube layout on the companion's uinput pad (Dolphin's evdev names: libevdev's code name without BTN_; the
# absolute axes numbered in code order X Y Z RX RY RZ HAT0X HAT0Y = 0-7; `-+` = the whole travel)
PAD_LAYOUT = (
    ("Buttons/A", "SOUTH"), ("Buttons/B", "WEST"), ("Buttons/X", "EAST"), ("Buttons/Y", "NORTH"),
    ("Buttons/Z", "TR"), ("Buttons/Start", "START"),
    ("Main Stick/Up", "Axis 1-"), ("Main Stick/Down", "Axis 1+"),
    ("Main Stick/Left", "Axis 0-"), ("Main Stick/Right", "Axis 0+"),
    ("C-Stick/Up", "Axis 4-"), ("C-Stick/Down", "Axis 4+"), ("C-Stick/Left", "Axis 3-"), ("C-Stick/Right", "Axis 3+"),
    ("Triggers/L", "Axis 2-+"), ("Triggers/R", "Axis 5-+"),
    ("Triggers/L-Analog", "Axis 2-+"), ("Triggers/R-Analog", "Axis 5-+"),
    ("D-Pad/Up", "Axis 7-"), ("D-Pad/Down", "Axis 7+"), ("D-Pad/Left", "Axis 6-"), ("D-Pad/Right", "Axis 6+"),
)
# Dolphin 2609b's log types (the names its own Logger.ini lists); these on, every other off
LOG_TYPES = (
    "AUDIO", "BOOT", "COMMON", "CORE", "VIDEO", "ActionReplay", "AI", "AMMB", "AMMB_NET", "CI", "CONSOLE", "CP", "DIO",
    "DSP", "DSPHLE", "DSPLLE", "DSPMails", "DVD", "EXI", "FileMon", "FRAMEDUMP", "GDB_STUB", "GP", "HLE", "Host GPU",
    "HSP", "IOS", "IOS_DI", "IOS_ES", "IOS_FS", "IOS_NET", "IOS_SD", "IOS_SSL", "IOS_STM", "IOS_USB", "IOS_WC24",
    "IOS_WFS", "IOS_WIIMOTE", "JIT", "MASTER", "MemCard Manager", "MI", "NETPLAY", "OSREPORT", "OSREPORT_HLE", "PE",
    "PI", "PowerPC", "RetroAchievements", "SI", "SI_AMBB", "SI_CARD", "SI_JVS", "SP1", "SYMBOLS", "VI", "WII_IPC",
    "Wiimote",
)
LOG_ON = ("BOOT", "CORE", "VIDEO", "AUDIO", "COMMON", "CI")


class GCError(Exception):
    pass


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return (env.get(FLAG_ENV) or "").strip() == "1"


def active(emulator: Any) -> bool:
    """A GameCube session is running on this emulator manager."""
    return getattr(emulator, "_launch_kind", None) == LAUNCH_KIND


# --- the folder and the list (read-only) ---------------------------------------------------------------------------

def read_dir(project_root: Path, environ: Mapping[str, str] | None = None) -> Path | None:
    return _inplace.read_dir(project_root, DIR_KEY, environ)


def list_titles(folder: Path | None) -> list[dict[str, Any]]:
    """`.rvz` > `.gcm` > `.iso` > `.ciso`, one per stem; anything under 1 MiB skipped by its size (never opened)."""
    return [t for t in _inplace.list_titles(folder, SUFFIX_RANK) if int(t["size_bytes"]) >= MIN_TITLE_BYTES]


def resolve_title(folder: Path | None, relative_path: str) -> Path:
    try:
        return _inplace.resolve(folder, relative_path, RELATIVE_PREFIX, "GameCube")
    except _inplace.InPlaceError as exc:
        raise GCError(str(exc)) from exc


def titles_for_plugin(folder: Path | None, stable_id: Callable[[str, str], str],
                      clean_name: Callable[[Path], str]) -> list[dict[str, Any]]:
    out = []
    for t in list_titles(folder):
        rel = RELATIVE_PREFIX + t["relative"]
        out.append({"id": stable_id(SYSTEM_ID, rel), "title": clean_name(t["path"]), "system": SYSTEM_ID,
                    "system_name": SYSTEM_NAME, "relative_path": rel, "format": t["suffix"].lstrip("."),
                    "size_bytes": t["size_bytes"]})
    return out


def find_appimage(project_root: Path) -> Path:
    found = sorted(p for p in (Path(project_root) / APPIMAGE_DIR).glob("*.AppImage") if p.is_file())
    if len(found) != 1:
        raise GCError(f"Dolphin: expected one AppImage in {APPIMAGE_DIR}/, found {len(found)}")
    return found[0]


def plan(source: str = PLAN_SOURCE) -> dict[str, Any]:
    """Four native ports on every GameCube launch (B46's plan shape): no multitap, so the client never relaunches."""
    return {"players_chosen": PORTS, "ports": PORTS, "multitap": False, "multitap_available": False,
            "ps1_mode": None, "device_args": [], "source": source}


# --- the config, written whole per launch --------------------------------------------------------------------------

def ini_text(sections: Iterable[tuple[str, Iterable[tuple[str, str]]]]) -> str:
    lines: list[str] = []
    for name, keys in sections:
        lines.append(f"[{name}]")
        lines.extend(f"{k} = {v}" for k, v in keys)
    return "\n".join(lines) + "\n"


def _q(name: str) -> str:
    return f"`{name}`"


def dolphin_ini() -> str:
    return ini_text([
        ("General", [("UseDiscordPresence", "False")]),
        ("Interface", [("ConfirmStop", "False"), ("UsePanicHandlers", "False"), ("OnScreenDisplayMessages", "False"),
                       ("PauseOnFocusLost", "False")]),
        ("Display", [("RenderToMain", "True"), ("Fullscreen", "True")]),
        ("Core", [("CPUThread", "True"), ("SkipIPL", "True"), ("GFXBackend", "Vulkan")]
         + [(f"SIDevice{i}", "6") for i in range(PORTS)]
         + [("SlotA", "8"), ("SlotB", "255"), ("EnableCheats", "False")]),
        ("DSP", [("Backend", "Cubeb"), ("DSPThread", "True")]),
        ("Input", [("BackgroundInput", "True")]),
        ("Analytics", [("PermissionAsked", "True"), ("Enabled", "False")]),
        ("AutoUpdate", [("UpdateTrack", "")]),
    ])


def gfx_ini() -> str:
    return ini_text([
        ("Hardware", [("Adapter", "0")]),
        ("Settings", [("InternalResolution", "1"), ("ShaderCompilationMode", "2"),
                      ("WaitForShadersBeforeStarting", "True"), ("ShowFPS", "False"), ("LogRenderTimeToFile", "True")]),
    ])


def hotkeys_ini() -> str:
    keys = [("Device", HOTKEY_DEVICE), ("General/Toggle Pause", _q(PAUSE_KEY))]
    keys += [(f"Load State/Load State Slot {n}", _q(f"F{n}")) for n in HOTKEY_SLOTS]
    keys += [(f"Save State/Save State Slot {n}", f"@(Shift+{_q(f'F{n}')})") for n in HOTKEY_SLOTS]
    return ini_text([("Hotkeys", keys)])


def gcpad_ini() -> str:
    sections = []
    for n in range(1, PORTS + 1):
        sections.append((f"GCPad{n}", [("Device", PAD_DEVICE.format(n=n))]
                         + [(k, _q(v)) for k, v in PAD_LAYOUT]))
    return ini_text(sections)


def logger_ini() -> str:
    return ini_text([
        ("Options", [("Verbosity", "4"), ("WriteToFile", "True"), ("WriteToConsole", "False"),
                     ("WriteToWindow", "False")]),
        ("Logs", [(t, "True" if t in LOG_ON else "False") for t in LOG_TYPES]),
    ])


def config_files() -> dict[str, str]:
    return {"Dolphin.ini": dolphin_ini(), "GFX.ini": gfx_ini(), "Hotkeys.ini": hotkeys_ini(),
            "GCPadNew.ini": gcpad_ini(), "Logger.ini": logger_ini()}


def write_config(user_dir: Path) -> list[str]:
    """Each file written whole (a temp name, then renamed over Dolphin's own). Returns the names written."""
    folder = Path(user_dir) / "Config"
    folder.mkdir(parents=True, exist_ok=True)
    names = []
    for name, text in config_files().items():
        tmp = folder / (name + ".privyhub.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(folder / name)
        names.append(name)
    return names


def command(appimage: Path, user_dir: Path, content: Path) -> list[str]:
    return [str(appimage), "-b", "-u", str(Path(user_dir).resolve()), "-e", str(content)]


# --- Dolphin's log per launch --------------------------------------------------------------------------------------

LAUNCH_FILE_RE = re.compile(r"^(\d{8}T\d{6}Z)-(dolphin\.log|render_times\.txt|vblank_times\.txt)$")
LOG_RETAIN_DAYS = 30
COUNTERS = ("render_times.txt", "vblank_times.txt")


def stamp_of(t: float) -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(t))


def log_for_launch(project_root: Path, launched_at: float) -> Path:
    return (Path(project_root) / LOGS_DIR / f"{stamp_of(launched_at)}-dolphin.log").resolve()


def link_log(user_dir: Path, target: Path) -> str:
    """`user/Logs/dolphin.log` -> the per-launch file (made empty). A regular file left there by an earlier launch
    (Dolphin replaced the link and the exit was missed) is kept first, named by its own mtime."""
    logs = Path(user_dir) / "Logs"
    logs.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch(exist_ok=True)
    link = logs / "dolphin.log"
    kept = "none"
    if link.is_symlink():
        link.unlink()
    elif link.exists():
        old = target.parent / f"{stamp_of(link.stat().st_mtime)}-dolphin.log"
        with open(old, "ab") as out:
            out.write(link.read_bytes())
        link.unlink()
        kept = old.name
    os.symlink(target, link)
    return kept


def collect_after_exit(user_dir: Path, target: Path) -> dict[str, Any]:
    """After the exit: a file Dolphin put in place of the link appended to the per-launch log; the render / vblank
    counters moved beside it under the launch's stamp."""
    logs = Path(user_dir) / "Logs"
    link = logs / "dolphin.log"
    out: dict[str, Any] = {"appended": False, "moved": []}
    if link.exists() and not link.is_symlink():
        with open(target, "ab") as fh:
            fh.write(link.read_bytes())
        link.unlink()
        os.symlink(target, link)
        out["appended"] = True
    stamp = target.name[: -len("-dolphin.log")]
    for name in COUNTERS:
        p = logs / name
        if p.is_file() and not p.is_symlink():
            os.replace(p, target.parent / f"{stamp}-{name}")
            out["moved"].append(name)
    return out


def prune_logs(folder: Path, now: float, days: int = LOG_RETAIN_DAYS) -> list[str]:
    """B53's rule: this folder's per-launch files whose name is older than `days` removed (others untouched)."""
    removed = []
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return removed
    for name in names:
        m = LAUNCH_FILE_RE.match(name)
        if not m:
            continue
        try:
            t = time.mktime(time.strptime(m.group(1), "%Y%m%dT%H%M%SZ")) - time.timezone
        except ValueError:
            continue
        if now - t > days * 86400:
            try:
                (Path(folder) / name).unlink()
                removed.append(name)
            except OSError:
                pass
    return removed


PAD_LINE = re.compile(r"(Added|Removed) device: evdev/(\d+)/PrivyHub Virtual Gamepad P([1-4])\b")


def pads_seen(log_path: Path | None) -> dict[str, str]:
    """`P<n>` -> `evdev/<index>` for each virtual pad Dolphin's log added (and did not remove since)."""
    seen: dict[str, str] = {}
    if log_path is None:
        return seen
    try:
        text = Path(log_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return seen
    for m in PAD_LINE.finditer(text):
        key = f"P{m.group(3)}"
        if m.group(1) == "Added":
            seen[key] = f"evdev/{m.group(2)}"
        else:
            seen.pop(key, None)
    return seen


def pads_line(seen: Mapping[str, str]) -> str:
    if not seen:
        return "none yet"
    parts = " ".join(f"{k}={seen[k]}" for k in sorted(seen))
    return parts + ("" if all(v == "evdev/0" for v in seen.values()) else " MISMATCH (the ini names evdev/0)")


# --- the process: the window, the clock, the keys -------------------------------------------------------------------

def _run(cmd: list[str], timeout: float = 2.0) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def find_window(pid: int, run: Callable[..., Any] = _run) -> str | None:
    """The PID's visible window, by the same `xdotool` search the capture uses."""
    try:
        r = run(["xdotool", "search", "--onlyvisible", "--pid", str(int(pid))])
    except Exception:
        return None
    ids = [x.strip() for x in (getattr(r, "stdout", "") or "").splitlines() if x.strip().isdigit()]
    return ids[0] if ids else None


def has_sink_input(pid: int, run: Callable[..., Any] = _run) -> bool:
    try:
        r = run(["pactl", "list", "sink-inputs"])
    except Exception:
        return False
    return f'application.process.id = "{int(pid)}"' in (getattr(r, "stdout", "") or "")


def grab_window(window: str) -> bytes | None:
    """B52: one frame of an X11 window, 64x36 gray (ffmpeg x11grab, the display of the companion's environment)."""
    display = os.environ.get("DISPLAY", "")
    if not display:
        return None
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "x11grab", "-window_id", str(window), "-i", display,
                        "-frames:v", "1", "-vf", f"scale={GRAB_W}:{GRAB_H},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True, timeout=5, check=False)
    return r.stdout if r.returncode == 0 and len(r.stdout) == GRAB_W * GRAB_H else None


def state_files(folder: Path) -> dict[str, tuple[int, int, int]]:
    """Dolphin's state files (`<id>.s01` ... `.s10`): name -> (mtime ns, size, inode); the hub's folder only."""
    out: dict[str, tuple[int, int, int]] = {}
    try:
        for p in Path(folder).glob("*.s[0-9][0-9]"):
            st = p.stat()
            out[p.name] = (st.st_mtime_ns, st.st_size, st.st_ino)
    except OSError:
        pass
    return out


def slot_suffix(slot: int) -> str:
    return f".s{int(slot):02d}"


def session_members(sid: int, proc_root: Path | None = None) -> list[int]:
    """The processes still in the session `sid` whose argv[0] is an AppImage (the runtime's FUSE helper)."""
    proc_root = PROC_ROOT if proc_root is None else Path(proc_root)
    out = []
    try:
        names = os.listdir(proc_root)
    except OSError:
        return out
    for name in names:
        if not name.isdigit():
            continue
        try:
            stat = (Path(proc_root) / name / "stat").read_text()
            fields = stat.rsplit(")", 1)[1].split()
            if int(fields[3]) != int(sid):
                continue
            argv0 = (Path(proc_root) / name / "cmdline").read_bytes().split(b"\0")[0].decode("utf-8", "replace")
        except (OSError, IndexError, ValueError):
            continue
        if argv0.endswith(".AppImage"):
            out.append(int(name))
    return sorted(out)


def wait_helpers(sid: int, bound: float = HELPER_WAIT_S, *, proc_root: Path | None = None,
                 kill: Callable[[int, int], None] | None = None, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic) -> str:
    """Before a launch: the previous launch's helper gone within `bound`, else SIGKILLed (the bound)."""
    kill = os.kill if kill is None else kill
    t0 = clock()
    left = session_members(sid, proc_root)
    if not left:
        return "none"
    while left and clock() - t0 < bound:
        sleep(0.25)
        left = session_members(sid, proc_root)
    if not left:
        return f"gone {clock() - t0:.1f}s"
    for p in left:
        try:
            kill(p, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return f"killed {len(left)} after {bound:.0f}s"


class Session:
    """One Dolphin process: the pause method kept, so a SIGSTOP pause is undone by SIGCONT (never by the hotkey)."""

    def __init__(self, pid: int, log: Callable[[str], None], *, run: Callable[..., Any] = _run,
                 kill: Callable[[int, int], None] = os.kill, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, proc_root: Path | None = None,
                 grab: Callable[[str], bytes | None] | None = None, log_path: Path | None = None,
                 user_dir: Path | None = None) -> None:
        self.pid = int(pid)
        self.log = log
        self.run = run
        self.kill = kill
        self.sleep = sleep
        self.clock = clock
        self.proc_root = PROC_ROOT if proc_root is None else Path(proc_root)
        self.grab = grab or grab_window
        self.log_path = log_path
        self.user_dir = user_dir
        self.paused_by: str | None = None
        self._pads_logged: str | None = None

    # -- the window and the clock --------------------------------------------------------------------------------
    def window(self) -> str | None:
        return find_window(self.pid, self.run)

    def wait_window(self, bound: float = WINDOW_WAIT_S, alive: Callable[[], bool] = lambda: True) -> str | None:
        end = self.clock() + bound
        while self.clock() < end and alive():
            w = self.window()
            if w:
                return w
            self.sleep(0.25)
        return None

    def cpu_tid(self) -> int | None:
        task = self.proc_root / str(self.pid) / "task"
        try:
            tids = sorted(os.listdir(task))
        except OSError:
            return None
        for t in tids:
            try:
                if (task / t / "comm").read_text().strip() == CPU_THREAD:
                    return int(t)
            except (OSError, ValueError):
                continue
        return None

    def ticks(self, tid: int | None) -> int | None:
        if tid is None:
            return None
        try:
            f = (self.proc_root / str(self.pid) / "task" / str(tid) / "stat").read_text().rsplit(")", 1)[1].split()
            return int(f[11]) + int(f[12])
        except (OSError, IndexError, ValueError):
            return None

    def wait_boot(self, bound: float = BOOT_WAIT_S, alive: Callable[[], bool] = lambda: True) -> float | None:
        """The shader pre-compile window: seconds until the `CPU thread` exists and its clock grows, else None."""
        t0 = self.clock()
        first: dict[int, int] = {}
        while self.clock() - t0 < bound and alive():
            tid = self.cpu_tid()
            v = self.ticks(tid)
            if tid is not None and v is not None:
                if tid not in first:
                    first[tid] = v
                elif v - first[tid] >= GROW_TICKS:
                    return self.clock() - t0
            self.sleep(0.25)
        return None

    def wait_audio(self, bound: float = AUDIO_WAIT_S, alive: Callable[[], bool] = lambda: True) -> float | None:
        t0 = self.clock()
        while self.clock() - t0 < bound and alive():
            if has_sink_input(self.pid, self.run):
                return self.clock() - t0
            self.sleep(0.1)
        return None

    def key(self, *keys: str) -> bool:
        """H2-P1's injection: activate + focus the PID's window (sync), keydown, 0.12 s, keyup in reverse."""
        w = self.window()
        if not w:
            return False
        try:
            self.run(["xdotool", "windowactivate", "--sync", w])
            self.run(["xdotool", "windowfocus", "--sync", w])
            self.run(["xdotool", "keydown", *keys])
            self.sleep(KEY_HOLD_S)
            self.run(["xdotool", "keyup", *reversed(keys)])
        except Exception:
            return False
        return True

    def watch(self, tid: int | None, stand: bool, bound: float = CONFIRM_S) -> bool | None:
        """`stand`: True once the clock stood for a 0.5-s window starting within `bound`; else True once it grew by
        >= GROW_TICKS within a 0.5-s window. False at the end; None when the clock cannot be read."""
        t0 = self.clock()
        hist: list[tuple[float, int]] = []
        while True:
            now = self.clock()
            v = self.ticks(tid)
            if v is None:
                return None
            hist.append((now, v))
            if stand:
                old = [(t, a) for t, a in hist if now - t >= STAND_WINDOW_S - 1e-9]
                if old and old[-1][0] - t0 <= bound + 1e-9 and old[-1][1] == v:
                    return True
            else:
                recent = [a for t, a in hist if now - t <= STAND_WINDOW_S + 1e-9]
                if v - min(recent) >= GROW_TICKS:
                    return True
            if now - t0 >= bound + STAND_WINDOW_S:
                return False
            self.sleep(POLL_S)

    def note_pads(self, force: bool = False) -> str:
        line = pads_line(pads_seen(self.log_path))
        if force or line != self._pads_logged:
            self._pads_logged = line
            self.log(f"GC pads: {line}")
        return line

    # -- pause / resume ------------------------------------------------------------------------------------------
    def pause(self) -> str:
        if self.paused_by is not None:
            return self.paused_by
        tid = self.cpu_tid()
        if tid is None or self.ticks(tid) is None or not self.window():
            self.kill(self.pid, signal.SIGSTOP)                 # a silent clock: no key at all
            self.paused_by = "sigstop"
        elif self.key(PAUSE_KEY) and self.watch(tid, stand=True):
            self.paused_by = "hotkey"
        else:
            self.kill(self.pid, signal.SIGSTOP)                 # an unconfirmed key: no second key
            self.paused_by = "sigstop"
        self.log(f"GC pause: {self.paused_by}")
        try:
            self.note_pads()
        except Exception:
            pass
        return self.paused_by

    def resume(self) -> str:
        how = self.paused_by
        if how is None:
            return "running"
        tid = self.cpu_tid()
        if how == "sigstop":
            self.kill(self.pid, signal.SIGCONT)
            done = "sigcont"
            if self.watch(tid, stand=False) is False:
                # the clock still stands: a late key had paused Dolphin as well
                if self.key(PAUSE_KEY) and self.watch(tid, stand=False):
                    done = "sigcont+hotkey"
                else:
                    raise GCError("Dolphin did not resume after SIGCONT")
        else:
            got = self.watch(tid, stand=False) if self.key(PAUSE_KEY) else None
            if got is False:                                    # still standing: one more key
                got = self.watch(tid, stand=False) if self.key(PAUSE_KEY) else None
            if not got:
                raise GCError("Dolphin did not resume after its pause hotkey")
            done = "hotkey"
        self.paused_by = None
        self.log(f"GC resume: {done}")
        return done

    def ensure_hotkey_pause(self) -> None:
        """A SIGSTOP-paused Dolphin cannot read a key: SIGCONT, then its own pause hotkey confirmed by the clock."""
        if self.paused_by != "sigstop":
            return
        self.kill(self.pid, signal.SIGCONT)
        self.paused_by = None
        tid = self.cpu_tid()
        if tid is not None and self.ticks(tid) is not None and self.key(PAUSE_KEY) and self.watch(tid, stand=True):
            self.paused_by = "hotkey"
            self.log("GC pause: hotkey (for a state key)")
            return
        self.kill(self.pid, signal.SIGSTOP)
        self.paused_by = "sigstop"
        raise GCError("Dolphin could not be paused by its hotkey, so the state key cannot be sent")

    # -- states ----------------------------------------------------------------------------------------------------
    def state_dir(self) -> Path:
        if self.user_dir is None:
            raise GCError("the GameCube user folder is unknown")
        return Path(self.user_dir) / "StateSaves"

    def press_save(self, slot: int) -> bool:
        return self.key("Shift_L", f"F{int(slot)}")

    def press_load(self, slot: int) -> bool:
        return self.key(f"F{int(slot)}")

    def wait_state_file(self, folder: Path, slot: int, before: Mapping[str, tuple[int, int, int]],
                        bound: float = SAVE_BOUND_S) -> tuple[Path, float] | None:
        """The slot's file new or changed since `before`, non-empty, its size and mtime standing for 0.25 s;
        (path, seconds from the key) or None at the bound."""
        suffix = slot_suffix(slot)
        t0 = self.clock()
        seen: dict[str, tuple[tuple[int, int], float]] = {}
        while True:
            now = self.clock()
            for name, (mtime, size, ino) in state_files(folder).items():
                if not name.endswith(suffix) or before.get(name) == (mtime, size, ino) or size <= 0:
                    continue
                sig = (mtime, size)
                prev = seen.get(name)
                if prev is None or prev[0] != sig:
                    seen[name] = (sig, now)
                elif now - prev[1] >= STABLE_S - 1e-9:
                    return Path(folder) / name, now - t0
            if now - t0 >= bound:
                return None
            self.sleep(POLL_S)

    def picture(self) -> tuple[str, float] | None:
        """B52: (hash, mean) of one frame of the PID's window, or None."""
        w = self.window()
        if not w:
            return None
        try:
            data = self.grab(w)
        except Exception:
            data = None
        if not data:
            return None
        return hashlib.sha256(data).hexdigest()[:16], sum(data) / len(data)

    def check_picture(self, pre: str | None, bound: float = PICTURE_BOUND_S) -> tuple[str, float]:
        """B52 after the resume: `ok` (3 distinct frames, not the pre-load one, one not black, the clock growing)
        or `static`; with the seconds it took."""
        t0 = self.clock()
        tid = self.cpu_tid()
        start = self.ticks(tid)
        seen: dict[str, float] = {}
        while True:
            v = self.ticks(tid)
            running = start is not None and v is not None and v - start >= GROW_TICKS
            p = self.picture()
            if p is not None and p[0] != pre:
                seen[p[0]] = p[1]
            if running and len(seen) >= PICTURE_DISTINCT and any(m > PICTURE_BLACK_MEAN for m in seen.values()):
                return "ok", self.clock() - t0
            if self.clock() - t0 >= bound:
                return "static", self.clock() - t0
            self.sleep(PICTURE_STEP_S)

    def booted(self) -> bool:
        return self.ticks(self.cpu_tid()) is not None

    # -- the exit --------------------------------------------------------------------------------------------------
    def stop(self, process: Any) -> str:
        """SIGCONT if stopped, SIGTERM, <= 5 s, else SIGKILL (<= 2 s); the helper count logged."""
        t0 = self.clock()
        try:
            if self.paused_by == "sigstop":
                self.kill(self.pid, signal.SIGCONT)
            self.kill(self.pid, signal.SIGTERM)
        except ProcessLookupError:
            self.log("GC exit: gone")
            return "gone"
        try:
            process.wait(timeout=TERM_WAIT_S)
            how = f"sigterm {self.clock() - t0:.1f}s"
        except subprocess.TimeoutExpired:
            try:
                self.kill(self.pid, signal.SIGKILL)
                process.wait(timeout=KILL_WAIT_S)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
            how = "sigkill"
        self.paused_by = None
        self.log(f"GC exit: {how} helper={len(session_members(self.pid, self.proc_root))}")
        return how


def iter_off_behaviours() -> Iterable[str]:
    return iter(OFF_BEHAVIOURS)
