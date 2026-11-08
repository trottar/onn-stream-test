"""B59: the N64 system through RetroArch, only with `PRIVYHUB_N64=1` in the companion's environment.

**Absent = today byte for byte:** the plugin and the emulator manager never import this module, `SYSTEMS` has no
`n64`, an `n64` launch is today's refusal (no `n64` profile in `emulators.json`), and no core-options file is written.

With the flag:
- titles are listed read-only in place from the folder `N64_DIR=` names in the gitignored paths file (B49's file;
  `inplace_library`): `.z64` / `.v64` / `.n64`, one entry per stem, `.z64` preferred. **Nothing is written there**;
- the launch is RetroArch's with the N64 core (`PRIVYHUB_N64_CORE`, SNES_CORE's form; default `mupen64plus_next`),
  the system profile injected per launch (never into `status()`), **four ports always** (`--device=1..4:1`, no
  multitap, so hold-to-join fills P1-P4 with no relaunch), and Mupen64Plus-Next's per-core `.opt` merged at launch
  (GLideN64, native resolution, the original frame rate, the C-buttons on the right stick, a memory pak per port);
- save states, the hold's scratch state, the stall resume and the recovery save are RetroArch's, as PS1's (no skip).

The fetch of the core is A's, with the user's go; `presence()` only looks (no network, the core never loaded).
Design: `docs/memory/evidence/b59_2026-11-08/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import copy
import os
import re
from pathlib import Path
from typing import Any, Callable, Mapping

import inplace_library as _inplace

FLAG_ENV = "PRIVYHUB_N64"
CORE_ENV = "PRIVYHUB_N64_CORE"
DIR_KEY = "N64_DIR"
SYSTEM_ID = "n64"
SYSTEM_NAME = "Nintendo 64"
RELATIVE_PREFIX = "n64/"
SUFFIX_RANK = {".z64": 0, ".v64": 1, ".n64": 2}
DEFAULT_CORE = "mupen64plus_next"
CORES_DIR = "runtime/emulators/retroarch/cores-linux"
PORTS = 4
JOYPAD_DEVICE = 1            # RETRO_DEVICE_JOYPAD
PLAN_SOURCE = "n64"

PROFILE: dict[str, Any] = {
    "name": SYSTEM_NAME,
    "license": "GPL-2.0",
    "extensions": sorted(SUFFIX_RANK),
    "controls": {"analog_dpad": "none"},   # the left stick stays the analog stick, never a D-pad
}

# Mupen64Plus-Next's per-core options (recalled key names; tools/n64_core_check.py --keys checks the fetched .so)
OPTIONS_LIBRARY = {"mupen64plus_next_libretro.so": "Mupen64Plus-Next"}
OPTIONS: dict[str, str] = {
    "mupen64plus-rdp-plugin": "gliden64",
    "mupen64plus-rsp-plugin": "hle",
    "mupen64plus-cpucore": "dynamic_recompiler",
    "mupen64plus-EnableNativeResFactor": "1",
    "mupen64plus-43screensize": "320x240",
    "mupen64plus-aspect": "4:3",
    "mupen64plus-Framerate": "Original",
    "mupen64plus-alt-map": "False",
    "mupen64plus-pak1": "memory",
    "mupen64plus-pak2": "memory",
    "mupen64plus-pak3": "memory",
    "mupen64plus-pak4": "memory",
}


class N64Error(Exception):
    pass


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return (env.get(FLAG_ENV) or "").strip() == "1"


# --- the folder and the list (read-only) -------------------------------------------------------------------------

def read_dir(project_root: Path, environ: Mapping[str, str] | None = None) -> Path | None:
    return _inplace.read_dir(project_root, DIR_KEY, environ)


def list_titles(folder: Path | None) -> list[dict[str, Any]]:
    return _inplace.list_titles(folder, SUFFIX_RANK)


def resolve_title(folder: Path | None, relative_path: str) -> Path:
    try:
        return _inplace.resolve(folder, relative_path, RELATIVE_PREFIX, "N64")
    except _inplace.InPlaceError as exc:
        raise N64Error(str(exc)) from exc


def titles_for_plugin(folder: Path | None, stable_id: Callable[[str, str], str],
                      clean_name: Callable[[Path], str]) -> list[dict[str, Any]]:
    """The scan's entries for the `n64` system (the plugin's own id and title rules)."""
    out = []
    for t in list_titles(folder):
        rel = RELATIVE_PREFIX + t["relative"]
        out.append({"id": stable_id(SYSTEM_ID, rel), "title": clean_name(t["path"]), "system": SYSTEM_ID,
                    "system_name": SYSTEM_NAME, "relative_path": rel, "format": t["suffix"].lstrip("."),
                    "size_bytes": t["size_bytes"]})
    return out


# --- the core ----------------------------------------------------------------------------------------------------

def core_name(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    name = (env.get(CORE_ENV) or "").strip() or DEFAULT_CORE
    if not re.fullmatch(r"[a-z0-9_]+", name):
        raise N64Error(f"{CORE_ENV} is not a core name")
    return name


def core_file(environ: Mapping[str, str] | None = None) -> str:
    return f"{core_name(environ)}_libretro.so"


def core_path(cores_dir: Path, environ: Mapping[str, str] | None = None) -> Path:
    name = core_file(environ)
    root = Path(cores_dir).resolve()
    path = (root / name).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise N64Error("N64 core path is invalid") from exc
    if not path.is_file():
        raise N64Error(f"N64 core not installed (fetch needed): {name}")
    return path


def presence(project_root: Path, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """"bundled" when the core is in the cores folder, else "fetch needed". Looks only: no network, no load.
    `appimage_bundles` is B59's reading of the AppImage (no libretro core inside, listed with 7z)."""
    name = core_file(environ)
    folder = Path(project_root) / CORES_DIR
    try:
        present = (folder / name).is_file()
    except OSError:
        present = False
    return {"state": "bundled" if present else "fetch needed", "core": name, "cores_dir": CORES_DIR,
            "appimage_bundles": False}


def keys_in_core(path: Path, keys: Mapping[str, str] | None = None) -> dict[str, list[str]]:
    """The option keys found / missing as byte strings in the core file (read, never loaded)."""
    data = Path(path).read_bytes()
    wanted = list(OPTIONS if keys is None else keys)
    found = [k for k in wanted if k.encode() in data]
    return {"found": found, "missing": [k for k in wanted if k not in found]}


# --- the launch pieces -------------------------------------------------------------------------------------------

def runtime_with_profile(runtime: dict[str, Any]) -> dict[str, Any]:
    """A copy of the runtime with the `n64` profile and core added (the launch's only; `status()` never sees it)."""
    out = dict(runtime)
    config = copy.deepcopy(runtime["config"])
    config.setdefault("systems", {})[SYSTEM_ID] = {**copy.deepcopy(PROFILE), "core": core_file()}
    out["config"] = config
    return out


def plan(source: str = PLAN_SOURCE) -> dict[str, Any]:
    """Four ports on every N64 launch (B46's plan shape): no multitap, so the client never asks for a relaunch."""
    return {
        "players_chosen": PORTS,
        "ports": PORTS,
        "multitap": False,
        "multitap_available": False,
        "ps1_mode": None,
        "device_args": [f"--device={p}:{JOYPAD_DEVICE}" for p in range(1, PORTS + 1)],
        "source": source,
    }


def options_library(core: str) -> str | None:
    return OPTIONS_LIBRARY.get(core)


_OPT_LINE = re.compile(r'^\s*([^=\s]+)\s*=')


def merge_options(text: str, keys: Mapping[str, str]) -> str:
    """Our keys set (`key = "value"`), every other line kept in place; missing keys appended."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    seen: set[str] = set()
    out = []
    for line in lines:
        m = _OPT_LINE.match(line)
        if m and m.group(1) in keys:
            if m.group(1) in seen:
                continue
            seen.add(m.group(1))
            out.append(f'{m.group(1)} = "{keys[m.group(1)]}"')
        else:
            out.append(line)
    out.extend(f'{k} = "{v}"' for k, v in keys.items() if k not in seen)
    return "\n".join(out) + "\n"


def write_options(config_dir: Path, core: str) -> dict[str, Any]:
    """Merge OPTIONS into `<config dir>/<library>/<library>.opt` (temp + rename). Another core: nothing written."""
    library = options_library(core)
    if library is None:
        return {"library": None, "keys": 0, "written": False}
    root = Path(config_dir).resolve()
    target = (root / library / (library + ".opt")).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise N64Error("N64 core-options path escaped the RetroArch config directory") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        text = target.read_text(encoding="utf-8-sig") if target.is_file() else ""
    except (OSError, UnicodeDecodeError) as exc:
        raise N64Error(f"N64 core options unreadable: {exc}") from exc
    temporary = target.with_name(target.name + ".privyhub.tmp")
    temporary.write_text(merge_options(text, OPTIONS), encoding="utf-8")
    temporary.replace(target)
    return {"library": library, "keys": len(OPTIONS), "written": True}


# --- B62: the layout (a core remap written and verified at launch; a per-title value from the metadata) ---------

# RetroArch's remap values for a button bound to an analog half-axis (recalled: 16-23 = left X+ X- Y+ Y-, right X+ X-
# Y+ Y-; the right stick is Mupen64Plus-Next's "C Buttons X / Y", so right X+ = C-right, right Y- = C-up).
RIGHT_X_PLUS, RIGHT_Y_MINUS = "20", "23"
LAYOUTS: dict[str, dict[str, str]] = {
    "face_c": {"btn_a": RIGHT_X_PLUS, "btn_x": RIGHT_Y_MINUS},   # east (o) = C-right, north (triangle) = C-up
    "core": {},                                                   # the core's own layout (o / triangle idle)
}
DEFAULT_LAYOUT = "face_c"
LAYOUT_KEY = "n64_layout"                                          # controller_overrides.json games[<id>]
LABELS = {
    "face_c": "A = \u2a09, B = \u25a1, C-buttons = right stick (also \u25b3 = C-up, \u25cb = C-right), Z = L2",
    "core": "A = \u2a09, B = \u25a1, C-buttons = right stick, Z = L2",
}
INPUT_CFG_LINES = ['auto_remaps_enable = "true"', 'remap_save_on_exit = "false"']
_RMP_LINE = re.compile(r'^\s*(input_player\d+_[a-z0-9_]+)\s*=\s*"([^"]*)"\s*$')


def layout_of(entry: Any) -> tuple[str, str | None]:
    """(the layout, the ignored value or None) from a title's controller-overrides entry."""
    raw = entry.get(LAYOUT_KEY) if isinstance(entry, dict) else None
    if raw is None or str(raw).strip() == "":
        return DEFAULT_LAYOUT, None
    value = str(raw).strip().casefold()
    if value in LAYOUTS:
        return value, None
    return DEFAULT_LAYOUT, str(raw)[:32]


def layout_label(layout: str) -> str:
    return LABELS.get(layout, LABELS[DEFAULT_LAYOUT])


def remap_binds(layout: str) -> dict[str, str]:
    return {f"input_player{p}_{k}": v for p in range(1, PORTS + 1) for k, v in LAYOUTS[layout].items()}


def remap_text(layout: str) -> str:
    lines = [f"# PrivyHub B62: the N64 layout `{layout}` (written at every N64 launch; do not edit)"]
    lines += [f'{k} = "{v}"' for k, v in remap_binds(layout).items()]
    return "\n".join(lines) + "\n"


def parse_remap(text: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in map(_RMP_LINE.match, text.splitlines()) if m}


def remap_path(config_dir: Path, core: str) -> Path | None:
    library = options_library(core)
    if library is None:
        return None
    root = Path(config_dir).resolve()
    target = (root / "remaps" / library / (library + ".rmp")).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise N64Error("N64 remap path escaped the RetroArch config directory") from exc
    return target


def shadowing(target: Path) -> int:
    """Other remap files beside the core's (a game or content-directory remap outranks it in RetroArch)."""
    try:
        return sum(1 for p in target.parent.glob("*.rmp") if p.name != target.name)
    except OSError:
        return 0


def write_remap(config_dir: Path, core: str, layout: str) -> dict[str, Any]:
    """Write the layout's core remap (temp + rename), read it back and compare; a mismatch raises (no launch)."""
    target = remap_path(config_dir, core)
    if target is None:
        return {"library": None, "layout": layout, "binds": 0, "written": False, "verified": False, "shadowed": 0}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".privyhub.tmp")
    temporary.write_text(remap_text(layout), encoding="utf-8")
    temporary.replace(target)
    try:
        back = parse_remap(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise N64Error(f"N64 remap could not be verified: {exc}") from exc
    if back != remap_binds(layout):
        raise N64Error("N64 remap could not be verified")
    return {"library": options_library(core), "layout": layout, "binds": len(back), "written": True,
            "verified": True, "shadowed": shadowing(target)}


def remap_check(config_dir: Path, core: str) -> dict[str, Any]:
    """Read-only (the tool, before any launch): the core remap against the default layout."""
    target = remap_path(config_dir, core)
    if target is None:
        return {"state": "no remap for this core"}
    out: dict[str, Any] = {"folder_exists": target.parent.is_dir(), "shadowed": shadowing(target)}
    probe = target.parent if target.parent.is_dir() else Path(config_dir)
    out["writable"] = os.access(probe, os.W_OK)
    if not target.is_file():
        out["state"] = "absent (the first N64 launch writes it)"
    else:
        try:
            got = parse_remap(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            got = None
        out["state"] = ("matches" if got == remap_binds(DEFAULT_LAYOUT)
                        else "matches core" if got == remap_binds("core") else "differs")
    return out


def remap_line(remap: Mapping[str, Any], ignored: str | None = None) -> str:
    if not remap.get("written"):
        return "N64 remap: none (no remap for this core)"
    line = (f"N64 remap: {remap['layout']} (players 1-{PORTS}, {remap['binds']} binds) verified"
            if remap["binds"] else f"N64 remap: {remap['layout']} (no binds) verified")
    if remap.get("shadowed"):
        line += f" + shadowed {remap['shadowed']}"
    if ignored is not None:
        line += f" (n64_layout ignored: {ignored!r})"
    return line


def log_lines(core: str, ports: int, options: Mapping[str, Any]) -> list[str]:
    name = core[:-len("_libretro.so")] if core.endswith("_libretro.so") else core
    opt = (f"{options['keys']} keys ({options['library']})" if options.get("written") else f"none ({name})")
    return [f"N64 launch: core={name} ports={int(ports)}", f"N64 core options: {opt}"]
