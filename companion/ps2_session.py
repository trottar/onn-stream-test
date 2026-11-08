"""B49: the PS2 launch kind (`pcsx2`), only with `PRIVYHUB_PS2=1` in the companion's environment.

**Absent = today byte for byte:** the plugin never imports this module, `SYSTEMS` has no `ps2`, a `ps2` launch is
today's refusal (no emulator profile), and nothing under `data/games/ps2/` is touched.

With the flag:
- the folders come from the paths file `PRIVYHUB_PS2_PATHS` names, else `runtime/h3_p1_paths.txt` (gitignored;
  `BIOS_DIR=` / `GAMES_DIR=` lines, nothing else read). They are never written into code, a record or a fixture;
- titles are listed read-only from `GAMES_DIR` (`.chd` / `.iso` / `.cue`; a `.bin` only through its `.cue`; one entry
  per stem, `.chd` preferred). **Nothing is ever written to the drive**;
- PCSX2 (the single AppImage in `runtime/emulators/pcsx2/`) is launched with `-datapath data/games/ps2/config -nogui
  -fullscreen -- <title>`, its ini merged per launch. A writable BIOS copy on the hub is made once, so the NVRAM write
  lands on the hub. The four virtual pads are mapped for SDL (`SDL_GAMECONTROLLERCONFIG`, the DualShock 2 layout), and
  the multitap comes from `players_chosen` (B46's rule: at launch only);
- pause / resume: PCSX2's `TogglePause` hotkey sent with `xdotool` and confirmed by PINE's status, else
  SIGSTOP / SIGCONT. Exit: SIGTERM, then SIGKILL after 5 s;
- RetroArch's save-state behaviours are off for the session (`ps2_mode`).

Design: `docs/memory/evidence/b49_2026-11-08/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

FLAG_ENV = "PRIVYHUB_PS2"
PATHS_ENV = "PRIVYHUB_PS2_PATHS"
DEFAULT_PATHS = "runtime/h3_p1_paths.txt"
APPIMAGE_DIR = "runtime/emulators/pcsx2"
DATA_DIR = "data/games/ps2"
SYSTEM_ID = "ps2"
SYSTEM_NAME = "PlayStation 2"
RELATIVE_PREFIX = "ps2/"
SUFFIX_RANK = {".chd": 0, ".iso": 1, ".cue": 2}
BIOS_IMAGE_BYTES = 4 * 1024 * 1024
WINDOW_WAIT_S = 30.0
CONFIRM_S = 1.5
TERM_WAIT_S = 5.0
KILL_WAIT_S = 2.0
PINE_SLOT = 28011
PINE_STATUS_OPCODE = 0x0F
# B51: PINE's state messages on PCSX2 2.8.2, read from its binary's dispatch table (evidence/b51_2026-11-08/
# pine_opcodes.txt): request [u32 size = 6][u8 opcode][u8 slot]; reply [u32 5][u8 0x00 OK | 0xFF fail]. The OK means
# queued (the save is zipped on a thread afterwards), so a save is confirmed by its file, a load by PCSX2's log.
MSG_SAVE_STATE = 0x09
MSG_LOAD_STATE = 0x0A
MSG_STATUS = PINE_STATUS_OPCODE
PINE_OK, PINE_FAIL = 0x00, 0xFF
SAVE_BOUND_S = 10.0            # no write time measurable by B (PCSX2 not run); ~1 s expected; HOME-5 logs the real one
LOAD_CONFIRM_S = 3.0
STATE_POLL_S = 0.25
# B52: the load runs the game from the state: after the game's ELF (PCSX2's own `ELF Loading:` line), then a picture
# check on the PID's window (3 distinct frames, not the pre-load picture, not black, PINE running, no `TLB Miss`)
ELF_LINE = "ELF Loading:"
ELF_WAIT_S = 30.0
PICTURE_BOUND_S = 5.0
PICTURE_STEP_S = 0.2
PICTURE_DISTINCT = 3
PICTURE_BLACK_MEAN = 20
TLB_MISS = "TLB Miss"
GRAB_W, GRAB_H = 64, 36
PINE_RUNNING, PINE_PAUSED = 0, 1

# The save-state behaviours a PS2 session turns off (B49 S3), in the rows' words
OFF_BEHAVIOURS = ("hold_rewind", "state_save_slot9", "stall_resume_load", "recovery_save")
SKIP_REASON = "ps2_mode: no save states"

# SDL's mapping of the companion's uinput pad (0x1209 / 0x5048, version 1, USB): buttons in key-code order b0-b9
# (SOUTH EAST NORTH WEST TL TR SELECT START THUMBL THUMBR), axes X Y Z RX RY RZ = a0-a5, the hat h0
SDL_MAPPING = (
    "03000000091200004850000001000000,PrivyHub Virtual Gamepad,"
    "a:b0,b:b1,y:b2,x:b3,leftshoulder:b4,rightshoulder:b5,back:b6,start:b7,leftstick:b8,rightstick:b9,"
    "leftx:a0,lefty:a1,lefttrigger:a2,rightx:a3,righty:a4,righttrigger:a5,"
    "dpup:h0.1,dpright:h0.2,dpdown:h0.4,dpleft:h0.8,platform:Linux,"
)

# The DualShock 2 layout from the SDL game-controller names (PCSX2's `SDL-<k>/<name>` bindings)
DS2_BINDINGS = (
    ("Up", "DPadUp"), ("Right", "DPadRight"), ("Down", "DPadDown"), ("Left", "DPadLeft"),
    # B50: PCSX2 2.8.2 is built on SDL3: the face buttons are FaceNorth / FaceEast / FaceSouth / FaceWest (its log
    # rejected `SDL-k/A` / `B` / `X` / `Y`); every other name below was accepted
    ("Triangle", "FaceNorth"), ("Circle", "FaceEast"), ("Cross", "FaceSouth"), ("Square", "FaceWest"),
    ("Select", "Back"), ("Start", "Start"),
    ("L1", "LeftShoulder"), ("L2", "+LeftTrigger"), ("R1", "RightShoulder"), ("R2", "+RightTrigger"),
    ("L3", "LeftStick"), ("R3", "RightStick"),
    ("LUp", "-LeftY"), ("LRight", "+LeftX"), ("LDown", "+LeftY"), ("LLeft", "-LeftX"),
    ("RUp", "-RightY"), ("RRight", "+RightX"), ("RDown", "+RightY"), ("RLeft", "-RightX"),
)
# B50: the SDL names PCSX2 2.8.2 accepts (its binary; its log of H3-P2), for the bindings above
SDL_BUTTONS = frozenset(("FaceSouth", "FaceEast", "FaceWest", "FaceNorth", "Back", "Guide", "Start", "LeftStick",
                         "RightStick", "LeftShoulder", "RightShoulder", "DPadUp", "DPadDown", "DPadLeft", "DPadRight"))
SDL_AXES = frozenset(s + a for s in "+-" for a in ("LeftX", "LeftY", "RightX", "RightY", "LeftTrigger", "RightTrigger"))
# B50: the two slots' cards on the hub, formatted by the companion when absent or all 0xFF (ps2_memcard)
MEMCARDS = ("Mcd001.ps2", "Mcd002.ps2")
PINE_LATE_S = 1.0

# PCSX2's pad numbering: 1A = Pad1, 2A = Pad2, 1B-1D = Pad3-Pad5, 2B-2D = Pad6-Pad8
MULTITAP_PORT1_PADS = (1, 3, 4, 5)
PLAIN_PADS = (1, 2)


class PS2Error(Exception):
    pass


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return (env.get(FLAG_ENV) or "").strip() == "1"


def active(emulator: Any) -> bool:
    """A PS2 session is running on this emulator manager (the save-state behaviours check this)."""
    return getattr(emulator, "_launch_kind", None) == "pcsx2"


# --- the folders ------------------------------------------------------------------------------------------------

def read_paths(project_root: Path, environ: Mapping[str, str] | None = None) -> dict[str, Path | None]:
    """BIOS_DIR / GAMES_DIR from the paths file; a missing file or key is None. Nothing else in the file is read."""
    env = os.environ if environ is None else environ
    named = (env.get(PATHS_ENV) or "").strip()
    path = Path(named) if named else Path(project_root) / DEFAULT_PATHS
    out: dict[str, Path | None] = {"bios_dir": None, "games_dir": None}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return out
    for line in lines:
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key, value = key.strip(), value.strip()
        if key == "BIOS_DIR" and value:
            out["bios_dir"] = Path(value)
        elif key == "GAMES_DIR" and value:
            out["games_dir"] = Path(value)
    return out


def find_appimage(project_root: Path) -> Path:
    found = sorted(p for p in (Path(project_root) / APPIMAGE_DIR).glob("*.AppImage") if p.is_file())
    if len(found) != 1:
        raise PS2Error(f"PCSX2: expected one AppImage in {APPIMAGE_DIR}/, found {len(found)}")
    return found[0]


# --- the list (read-only) ------------------------------------------------------------------------------------------

_CUE_FILE = re.compile(r'^\s*FILE\s+(?:"([^"]+)"|(\S+))', re.IGNORECASE)


def cue_complete(cue: Path) -> bool:
    """Every FILE a .cue names exists beside it (at least one)."""
    try:
        text = cue.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    names = [m.group(1) or m.group(2) for m in map(_CUE_FILE.match, text.splitlines()) if m]
    return bool(names) and all((cue.parent / n).is_file() for n in names)


def list_titles(games_dir: Path | None) -> list[dict[str, Any]]:
    """The titles under `games_dir`, read-only: one per (folder, stem), `.chd` > `.iso` > `.cue`; a `.bin` never
    listed itself; a `.cue` with a missing file skipped; hidden names skipped. [] when the folder is not there."""
    if games_dir is None:
        return []
    root = Path(games_dir)
    try:
        if not root.is_dir():
            return []
    except OSError:
        return []
    best: dict[tuple[str, str], tuple[int, Path]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name.startswith("."):
                continue
            p = Path(dirpath) / name
            rank = SUFFIX_RANK.get(p.suffix.casefold())
            if rank is None:
                continue
            if p.suffix.casefold() == ".cue" and not cue_complete(p):
                continue
            key = (str(p.parent), p.stem.casefold())
            if key not in best or rank < best[key][0]:
                best[key] = (rank, p)
    out = []
    for _, p in sorted(best.values(), key=lambda v: str(v[1]).casefold()):
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        out.append({"path": p, "relative": p.relative_to(root).as_posix(), "suffix": p.suffix.casefold(),
                    "size_bytes": size})
    return out


def resolve_title(games_dir: Path | None, relative_path: str) -> Path:
    """`ps2/<inside GAMES_DIR>` → the file; anything escaping the folder or missing refuses."""
    if games_dir is None:
        raise PS2Error("PS2 folders are not configured")
    rel = str(relative_path or "")
    if not rel.startswith(RELATIVE_PREFIX):
        raise PS2Error("not a PS2 title path")
    root = Path(games_dir).resolve()
    target = (root / rel[len(RELATIVE_PREFIX):]).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PS2Error("PS2 title path escapes the games folder") from exc
    if not target.is_file():
        raise PS2Error("PS2 title not found")
    return target


# --- the hub side: the BIOS copy, the ini -------------------------------------------------------------------------

def bios_copy_once(bios_dir: Path | None, hub_bios: Path) -> int:
    """Copy every regular file of the drive's BIOS folder to the hub once (the hub copy empty); never overwrite.
    Returns the number copied (0 when the hub copy already holds files)."""
    hub_bios.mkdir(parents=True, exist_ok=True)
    if any(p.is_file() for p in hub_bios.iterdir()):
        return 0
    if bios_dir is None or not Path(bios_dir).is_dir():
        raise PS2Error("PS2 folders are not configured")
    n = 0
    for p in sorted(Path(bios_dir).iterdir()):
        if p.is_file() and not p.name.startswith("."):
            dest = hub_bios / p.name
            if not dest.exists():
                shutil.copy2(p, dest)
                n += 1
    if n == 0:
        raise PS2Error("the PS2 BIOS folder holds no file")
    return n


def choose_bios(hub_bios: Path, existing: str | None) -> str:
    files = sorted(p for p in hub_bios.iterdir() if p.is_file())
    if existing and any(p.name == existing for p in files):
        return existing
    sized = [p for p in files if p.stat().st_size == BIOS_IMAGE_BYTES]
    if len(sized) == 1:
        return sized[0].name
    bins = [p for p in files if p.suffix.casefold() == ".bin"]
    if len(bins) == 1:
        return bins[0].name
    raise PS2Error("PS2 BIOS image not identifiable in the hub copy")


def ini_get(text: str, section: str, key: str) -> str | None:
    cur = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1]
            continue
        if cur == section and "=" in s:
            k, _, v = s.partition("=")
            if k.strip() == key:
                return v.strip()
    return None


def ini_merge(text: str, settings: Mapping[str, Mapping[str, str]]) -> str:
    """Set each section's keys in PCSX2's `key = value` ini, keeping every other line; missing ones appended."""
    lines = text.splitlines()
    out: list[str] = []
    done: dict[str, set[str]] = {s: set() for s in settings}
    cur: str | None = None

    def flush(section: str | None) -> None:
        if section in settings:
            missing = [k for k in settings[section] if k not in done[section]]
            while out and out[-1].strip() == "":
                out.pop()
            out.extend(f"{k} = {settings[section][k]}" for k in missing)
            done[section].update(missing)
            out.append("")

    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            flush(cur)
            cur = s[1:-1]
            out.append(line)
            continue
        if cur in settings and "=" in s:
            k = s.partition("=")[0].strip()
            if k in settings[cur]:
                out.append(f"{k} = {settings[cur][k]}")
                done[cur].add(k)
                continue
        out.append(line)
    flush(cur)
    for section in settings:
        if section not in {l.strip()[1:-1] for l in out if l.strip().startswith("[")}:
            out.append(f"[{section}]")
            out.extend(f"{k} = {v}" for k, v in settings[section].items())
            out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def pad_sections(players: int, multitap: bool) -> dict[str, dict[str, str]]:
    """[Pad] and [Pad1]-[Pad8]: the virtual pads P1-P4 (SDL-0..3, creation order) on the ports the pick needs."""
    n = max(1, min(4 if multitap else 2, int(players)))
    pads = MULTITAP_PORT1_PADS if multitap else PLAIN_PADS
    out: dict[str, dict[str, str]] = {"Pad": {"MultitapPort1": "true" if multitap else "false",
                                              "MultitapPort2": "false"}}
    used = {pads[i]: i for i in range(n)}
    for pad in range(1, 9):
        if pad in used:
            k = used[pad]
            sec = {"Type": "DualShock2"}
            sec.update({name: f"SDL-{k}/{sdl}" for name, sdl in DS2_BINDINGS})
        else:
            sec = {"Type": "None"}
        out[f"Pad{pad}"] = sec
    return out


def pick_adapter(existing: str | None, run: Callable[[list[str]], str] | None) -> str | None:
    """The existing adapter when it names AMD / RADV, else the first such `vulkaninfo --summary` device, else None."""
    if existing and re.search(r"AMD|RADV", existing):
        return existing
    if run is None:
        return None
    try:
        text = run(["vulkaninfo", "--summary"])
    except Exception:
        return None
    for m in re.finditer(r"deviceName\s*=\s*(.+)", text or ""):
        name = m.group(1).strip()
        if re.search(r"AMD|RADV", name):
            return name
    return None


def settings_for(project_root: Path, bios_name: str, adapter: str | None, players: int,
                 multitap: bool) -> dict[str, dict[str, str]]:
    data = (Path(project_root) / DATA_DIR).resolve()
    # B50: vsync on with mailbox allowed: a tear-free present (MAILBOX where the driver offers it, else FIFO)
    gs = {"Renderer": "14", "upscale_multiplier": "1", "VsyncEnable": "true", "DisableMailboxPresentation": "false"}
    for k in ("OsdShowSpeed", "OsdShowFPS", "OsdShowVPS", "OsdShowCPU", "OsdShowGPU", "OsdShowResolution"):
        gs[k] = "false"
    if adapter:
        gs["Adapter"] = adapter
    s: dict[str, dict[str, str]] = {
        "UI": {"StartFullscreen": "true", "SetupWizardIncomplete": "false", "ConfirmShutdown": "false",
               "HideMouseCursor": "true", "PauseOnFocusLoss": "false", "StartPaused": "false"},
        "Folders": {"Bios": str(data / "bios"), "MemoryCards": str(data / "memcards"),
                    "Savestates": str(data / "sstates")},
        "Filenames": {"BIOS": bios_name},
        "EmuCore": {"EnableDiscordPresence": "false", "EnablePINE": "true", "PINESlot": str(PINE_SLOT),
                    "SaveStateOnShutdown": "false", "EnableFastBoot": "true"},
        "EmuCore/GS": gs,
        "AutoUpdater": {"CheckAtStartup": "false"},
        "InputSources": {"SDL": "true", "Keyboard": "true", "Mouse": "false"},
        # B52: MTVU off -- PCSX2: "MTVU speedhack is enabled, saved states may not be stable" (HOME-5's black load)
        "EmuCore/Speedhacks": {"vuThread": "false"},
        "Hotkeys": {"TogglePause": "Keyboard/Space"},
        # B50: both slots on the hub's formatted cards
        "MemoryCards": {"Slot1_Enable": "true", "Slot1_Filename": MEMCARDS[0], "Slot2_Enable": "true",
                        "Slot2_Filename": MEMCARDS[1]},
    }
    s.update(pad_sections(players, multitap))
    return s


def pcsx2_log_path(project_root: Path) -> Path:
    """B51: PCSX2's own log under its data path (read for the load's confirmation; never copied into a record)."""
    return Path(project_root) / DATA_DIR / "config" / "PCSX2" / "logs" / "emulog.txt"


def ini_path(project_root: Path) -> Path:
    return Path(project_root) / DATA_DIR / "config" / "PCSX2" / "inis" / "PCSX2.ini"


def command(appimage: Path, project_root: Path, content: Path, logfile: Path | None = None) -> list[str]:
    datapath = (Path(project_root) / DATA_DIR / "config").resolve()
    # B53: PCSX2's own log per launch (2.8.2: "-logfile <path>: Writes the application log to path instead of emulog.txt")
    log = ["-logfile", str(logfile)] if logfile is not None else []
    return [str(appimage), "-datapath", str(datapath), "-nogui", "-fullscreen", *log, "--", str(content)]


# B53: PCSX2's log per launch, named by the UTC launch time only, kept 30 days under data/games/ps2/logs/
PCSX2_LOG_RE = re.compile(r"^(\d{8}T\d{6}Z)-pcsx2\.log$")
LOG_RETAIN_DAYS = 30


def pcsx2_log_for_launch(project_root: Path, launched_at: float) -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(launched_at))
    return (Path(project_root) / DATA_DIR / "logs" / f"{stamp}-pcsx2.log").resolve()


def prune_pcsx2_logs(folder: Path, now: float, days: int = LOG_RETAIN_DAYS) -> list[str]:
    """B53: remove this folder's per-launch PCSX2 logs whose name is older than `days` (others untouched)."""
    removed = []
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return removed
    for name in names:
        m = PCSX2_LOG_RE.match(name)
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


def launch_env(base: Mapping[str, str]) -> dict[str, str]:
    env = dict(base)
    env["SDL_GAMECONTROLLERCONFIG"] = SDL_MAPPING
    return env


# --- the running session: the window, PINE, pause / resume / exit ------------------------------------------------

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


AUDIO_WAIT_S = 45.0


def has_sink_input(pid: int, run: Callable[..., Any] = _run) -> bool:
    """H3-P2 (A, 2026-11-08): does the PID own a PulseAudio sink-input yet (`application.process.id`)? The session's
    audio is found by exactly this match, so the paused handoff must not freeze PCSX2 before its stream exists."""
    try:
        r = run(["pactl", "list", "sink-inputs"])
    except Exception:
        return False
    return f'application.process.id = "{int(pid)}"' in (getattr(r, "stdout", "") or "")


def wait_sink_input(pid: int, bound: float = AUDIO_WAIT_S, alive: Callable[[], bool] = lambda: True,
                    run: Callable[..., Any] = _run, sleep: Callable[[float], None] = time.sleep,
                    clock: Callable[[], float] = time.monotonic) -> float | None:
    """Seconds until the PID's sink-input appeared, or None at the bound / if the process ended."""
    t0 = clock()
    end = t0 + bound
    while clock() < end and alive():
        if has_sink_input(pid, run):
            return clock() - t0
        sleep(0.1)      # B50: 0.1 s (A's 0.25); the sink-input came 0.1-0.3 s after the window in H3-P2
    return None


def ensure_memcards(project_root: Path) -> dict[str, str]:
    """B50: the hub's two cards formatted when absent or all 0xFF (never a card holding data)."""
    import ps2_memcard
    return ps2_memcard.ensure_cards(Path(project_root) / DATA_DIR / "memcards", list(MEMCARDS))


def grab_window(window: str) -> bytes | None:
    """B52: one frame of an X11 window, 64x36 gray (ffmpeg x11grab, the display of the companion's environment)."""
    display = os.environ.get("DISPLAY", "")
    if not display:
        return None
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "x11grab", "-window_id", str(window), "-i", display,
                        "-frames:v", "1", "-vf", f"scale={GRAB_W}:{GRAB_H},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True, timeout=5, check=False)
    return r.stdout if r.returncode == 0 and len(r.stdout) == GRAB_W * GRAB_H else None


def pine_socket_path(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    base = env.get("XDG_RUNTIME_DIR") or "/tmp"
    return Path(base) / ("pcsx2.sock" if PINE_SLOT == 28011 else f"pcsx2.sock.{PINE_SLOT}")


def pine_call(path: Path, opcode: int, payload: bytes = b"", timeout: float = 2.0) -> int | None:
    """B51: one PINE message with no reply body (the state messages): the result byte, or None with no answer."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(str(path))
            s.sendall(struct.pack("<IB", 5 + len(payload), opcode) + payload)
            data = b""
            while len(data) < 5:
                chunk = s.recv(5 - len(data))
                if not chunk:
                    break
                data += chunk
    except OSError:
        return None
    if len(data) < 5:
        return None
    return data[4]


def state_files(folder: Path) -> dict[str, tuple[int, int, int]]:
    """B51: PCSX2's state files (name -> mtime ns, size, inode: PCSX2 keeps the old one as .p2s.backup and writes a new
    file); never the drive (the hub's sstates folder only)."""
    out: dict[str, tuple[int, int, int]] = {}
    try:
        for p in Path(folder).glob("*.p2s"):
            st = p.stat()
            out[p.name] = (st.st_mtime_ns, st.st_size, st.st_ino)
    except OSError:
        pass
    return out


def _complete_zip(p: Path) -> bool:
    import zipfile
    try:
        return zipfile.is_zipfile(p)
    except OSError:
        return False


def pine_status(path: Path, timeout: float = 0.5) -> int | None:
    """PINE MsgStatus: 0 running, 1 paused, 2 shutdown; None when the socket does not answer."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(str(path))
            s.sendall(struct.pack("<IB", 5, PINE_STATUS_OPCODE))
            data = b""
            while len(data) < 9:
                chunk = s.recv(9 - len(data))
                if not chunk:
                    break
                data += chunk
    except OSError:
        return None
    if len(data) < 9:
        return None
    size, result, status = struct.unpack("<IBI", data[:9])
    return int(status) if result == 0 and size >= 9 else None


class Session:
    """One PCSX2 process: the pause method kept, so a SIGSTOP pause is undone by SIGCONT (never by the hotkey)."""

    def __init__(self, pid: int, log: Callable[[str], None], *, run: Callable[..., Any] = _run,
                 status: Callable[[], int | None] | None = None, kill: Callable[[int, int], None] = os.kill,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
                 pine_path: Path | None = None, grab: Callable[[str], bytes | None] | None = None,
                 log_path: Path | None = None) -> None:
        self.pid = int(pid)
        self.log = log
        self.run = run
        # B51: one PINE socket for the status and the state messages (a test points both at its double)
        self.pine_path = pine_path or pine_socket_path()
        # B52: one window frame (64x36 gray bytes) and PCSX2's own log for this launch (B53 points it per launch)
        self.grab = grab or grab_window
        self.log_path = log_path
        self.status = status or (lambda: pine_status(self.pine_path))
        self.kill = kill
        self.sleep = sleep
        self.clock = clock
        self.paused_by: str | None = None

    def wait_window(self, bound: float = WINDOW_WAIT_S, alive: Callable[[], bool] = lambda: True) -> str | None:
        end = self.clock() + bound
        while self.clock() < end and alive():
            w = find_window(self.pid, self.run)
            if w:
                return w
            self.sleep(0.25)
        return None

    def wait_audio(self, bound: float = AUDIO_WAIT_S, alive: Callable[[], bool] = lambda: True) -> float | None:
        """B50: A's H3-P2 wait (the PID's sink-input, the earliest proof of PCSX2's audio stream), on this session's
        own run / sleep / clock, so the tests fake it."""
        return wait_sink_input(self.pid, bound, alive, self.run, self.sleep, self.clock)

    def _hotkey(self) -> bool:
        w = find_window(self.pid, self.run)
        if not w:
            return False
        try:
            self.run(["xdotool", "windowfocus", "--sync", w])
            self.run(["xdotool", "key", "--clearmodifiers", "space"])
        except Exception:
            return False
        return True

    def _await(self, want: int) -> bool:
        end = self.clock() + CONFIRM_S
        while True:
            if self.status() == want:
                return True
            if self.clock() >= end:
                return False
            self.sleep(0.1)

    def pause(self) -> str:
        if self.paused_by is not None:
            return self.paused_by
        st = self.status()
        # B50: PINE answers ~0.1 s after the audio stream (after the VM's init): a late first answer is waited for
        if st is None and not getattr(self, "_pine_seen", False):
            end = self.clock() + PINE_LATE_S
            while st is None and self.clock() < end:
                self.sleep(0.1)
                st = self.status()
        if st is not None:
            self._pine_seen = True
        if st == PINE_PAUSED:
            self.paused_by = "hotkey"
        elif st == PINE_RUNNING and self._hotkey() and self._await(PINE_PAUSED):
            self.paused_by = "hotkey"
        else:
            self.kill(self.pid, signal.SIGSTOP)
            self.paused_by = "sigstop"
        self.log(f"PS2 pause: {self.paused_by}")
        return self.paused_by

    def resume(self) -> str:
        how = self.paused_by
        if how is None:
            return "running"
        if how == "sigstop":
            self.kill(self.pid, signal.SIGCONT)
            done = "sigcont"
        else:
            ok = self._hotkey() and self._await(PINE_RUNNING)
            if not ok and self.status() == PINE_PAUSED:
                ok = self._hotkey() and self._await(PINE_RUNNING)
            if not ok:
                raise PS2Error("PCSX2 did not resume after its pause hotkey")
            done = "hotkey"
        self.paused_by = None
        self.log(f"PS2 resume: {done}")
        return done

    def ensure_pine_pause(self) -> None:
        """B51: a SIGSTOP-paused PCSX2 cannot answer PINE: SIGCONT, then its own pause hotkey confirmed by PINE."""
        if self.paused_by != "sigstop":
            return
        self.kill(self.pid, signal.SIGCONT)
        self.paused_by = None
        end = self.clock() + PINE_LATE_S
        st = self.status()
        while st is None and self.clock() < end:
            self.sleep(0.1)
            st = self.status()
        if st == PINE_PAUSED or (st == PINE_RUNNING and self._hotkey() and self._await(PINE_PAUSED)):
            self.paused_by = "hotkey"
            self.log("PS2 pause: hotkey (for a state message)")
            return
        self.kill(self.pid, signal.SIGSTOP)
        self.paused_by = "sigstop"
        raise PS2Error("PCSX2 did not answer PINE, so the state message cannot be sent")

    def state_message(self, opcode: int, slot: int) -> int | None:
        """B51: MsgSaveState / MsgLoadState with the slot byte; the result byte or None."""
        return pine_call(self.pine_path, opcode, bytes((int(slot) & 0xFF,)))

    def wait_state_file(self, folder: Path, slot: int, before: dict[str, tuple[int, int, int]],
                        bound: float = SAVE_BOUND_S) -> tuple[Path, float] | None:
        """B51: the slot's .p2s that is new or changed since `before`, its size steady over two polls and a whole zip;
        (path, seconds) or None at the bound."""
        suffix = f".{int(slot):02d}.p2s"
        t0 = self.clock()
        last: dict[str, int] = {}
        while True:
            now = state_files(folder)
            for name, (mtime, size, ino) in now.items():
                if not name.endswith(suffix) or before.get(name) == (mtime, size, ino) or size <= 0:
                    continue
                if last.get(name) == size and _complete_zip(Path(folder) / name):
                    return Path(folder) / name, self.clock() - t0
                last[name] = size
            if self.clock() - t0 >= bound:
                return None
            self.sleep(STATE_POLL_S)

    def _log_text(self, offset: int = 0) -> str:
        if self.log_path is None:
            return ""
        try:
            with open(self.log_path, "rb") as fh:
                fh.seek(offset)
                return fh.read().decode("utf-8", "replace")
        except OSError:
            return ""

    def log_size(self) -> int:
        try:
            return Path(self.log_path).stat().st_size if self.log_path is not None else 0
        except OSError:
            return 0

    def elf_started(self) -> bool:
        """B52: this launch's game has booted (PCSX2's `ELF Loading:` line in its log)."""
        return ELF_LINE in self._log_text()

    def wait_elf(self, bound: float = ELF_WAIT_S) -> bool:
        t0 = self.clock()
        while not self.elf_started():
            if self.clock() - t0 >= bound:
                return False
            self.sleep(STATE_POLL_S)
        return True

    def picture(self) -> tuple[str, float] | None:
        """B52: (hash, mean) of one frame of the PID's window, or None."""
        w = find_window(self.pid, self.run)
        if not w:
            return None
        try:
            data = self.grab(w)
        except Exception:
            data = None
        if not data:
            return None
        import hashlib
        return hashlib.sha256(data).hexdigest()[:16], sum(data) / len(data)

    def check_picture(self, pre: str | None, log_offset: int, bound: float = PICTURE_BOUND_S) -> tuple[str, float]:
        """B52: after the resume -- `ok` (the game runs: 3 distinct frames, not the pre-load one, not all black, PINE
        running, no TLB Miss), `fault` (a TLB Miss since the load) or `static`; with the seconds it took."""
        t0 = self.clock()
        seen: dict[str, float] = {}
        running = False
        while True:
            if TLB_MISS in self._log_text(log_offset):
                return "fault", self.clock() - t0
            if self.status() == PINE_RUNNING:
                running = True
            p = self.picture()
            if p is not None and p[0] != pre:
                seen[p[0]] = p[1]
            if (running and len(seen) >= PICTURE_DISTINCT
                    and any(mean > PICTURE_BLACK_MEAN for mean in seen.values())):
                return "ok", self.clock() - t0
            if self.clock() - t0 >= bound:
                return "static", self.clock() - t0
            self.sleep(PICTURE_STEP_S)

    def wait_log_line(self, path: Path, offset: int, text: str, bound: float = LOAD_CONFIRM_S) -> bool:
        """B51: PCSX2's own log line (e.g. `Loaded state from slot N.`) written after `offset`, within the bound."""
        t0 = self.clock()
        while True:
            try:
                with open(path, "rb") as fh:
                    fh.seek(offset)
                    if text.encode() in fh.read():
                        return True
            except OSError:
                pass
            if self.clock() - t0 >= bound:
                return False
            self.sleep(STATE_POLL_S)

    def stop(self, process: Any) -> str:
        """SIGCONT if stopped, SIGTERM, ≤ 5 s, else SIGKILL (≤ 2 s). Returns how it ended."""
        t0 = self.clock()
        try:
            if self.paused_by == "sigstop":
                self.kill(self.pid, signal.SIGCONT)
            self.kill(self.pid, signal.SIGTERM)
        except ProcessLookupError:
            self.log("PS2 exit: gone")
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
        self.log(f"PS2 exit: {how}")
        return how


def default_runner(cmd: list[str]) -> str:
    return _run(cmd, timeout=10.0).stdout


def titles_for_plugin(games_dir: Path | None, stable_id: Callable[[str, str], str],
                      clean_name: Callable[[Path], str]) -> list[dict[str, Any]]:
    """The scan's entries for the `ps2` system (the plugin's own id and title rules)."""
    out = []
    for t in list_titles(games_dir):
        rel = RELATIVE_PREFIX + t["relative"]
        out.append({"id": stable_id(SYSTEM_ID, rel), "title": clean_name(t["path"]), "system": SYSTEM_ID,
                    "system_name": SYSTEM_NAME, "relative_path": rel, "format": t["suffix"].lstrip("."),
                    "size_bytes": t["size_bytes"]})
    return out


def iter_off_behaviours() -> Iterable[str]:
    return iter(OFF_BEHAVIOURS)
