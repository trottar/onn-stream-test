"""B80: PCSX2's bundled widescreen / no-interlacing / 60-fps patches offered per PS2 title, inside PRIVYHUB_PS2=1.

- The title's serial and CRC come from PCSX2's own per-launch logs (`Disc changed to <file>.`, `  Serial: …`,
  `  CRC: …`), cached on the hub by game id; so a title's patches show after its first PrivyHub launch.
- The patch groups come from the AppImage's `resources/patches.zip` (`<SERIAL>_<CRC>.pnach`), read into memory with
  `7z x -so`; nothing extracted, nothing edited.
- The user's toggles are remembered per title on the hub; at launch the game's settings file (`gamesettings/<CRC>.ini`,
  the name PCSX2 2.8.2's log shows it reading, and `<SERIAL>_<CRC>.ini`) carries `EnableWideScreenPatches` /
  `EnableNoInterlacingPatches` and `[Patches] Enable = 60 FPS`.

`PRIVYHUB_PS2_PATCHES=0` = today. Design: `docs/memory/evidence/b80_2026-11-09/design_written_before_code.md`.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Callable, Mapping

KNOB_ENV = "PRIVYHUB_PS2_PATCHES"
ZIP_MEMBER = "usr/bin/resources/patches.zip"
IDS_FILE = "data/games/ps2/title_ids.json"
TOGGLES_FILE = "data/games/ps2/patch_toggles.json"
MARKER = "; PrivyHub per-launch game settings (B80 / B81)"
# the user's toggle -> PCSX2's group name in the bundle
GROUPS = (("ws", "Widescreen 16:9"), ("ni", "No-Interlacing"), ("60", "60 FPS"))
LABELS = {"ws": "Widescreen", "ni": "No interlacing", "60": "60 fps"}
_DISC_RE = re.compile(r"Disc changed to (.+)\.\s*$")
_SERIAL_RE = re.compile(r"^\[[^\]]*\]\s+Serial:\s*(\S+)\s*$")
_CRC_RE = re.compile(r"^\[[^\]]*\]\s+CRC:\s*([0-9A-Fa-f]{8})\s*$")
_SERIAL_OK = re.compile(r"[A-Z]{4}-[0-9]{5}")

_zip_cache: dict[tuple[str, int], zipfile.ZipFile | None] = {}


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return str(env.get(KNOB_ENV, "")).strip() != "0"


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def ids_from_logs(logs_dir: Path) -> dict[str, tuple[str, str]]:
    """`{file name: (serial, crc)}` from PCSX2's per-launch logs, oldest first, so the latest launch wins."""
    out: dict[str, tuple[str, str]] = {}
    try:
        logs = sorted(p for p in Path(logs_dir).glob("*-pcsx2.log") if p.is_file())
    except OSError:
        return out
    for log in logs:
        try:
            lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        name = serial = None
        for line in lines:
            m = _DISC_RE.search(line)
            if m:
                name, serial = m.group(1).strip(), None
                continue
            if name is None:
                continue
            m = _SERIAL_RE.match(line)
            if m:
                serial = m.group(1).strip()
                continue
            m = _CRC_RE.match(line)
            if m and serial and _SERIAL_OK.fullmatch(serial):
                out[name] = (serial, m.group(1).upper())
                name = serial = None
    return out


def title_ids(project_root: Path, game: Mapping[str, Any], logs_dir: Path) -> tuple[str, str] | None:
    """The title's (serial, crc): the hub's cache by game id, else learned from the logs by the file's name."""
    game_id = str(game.get("id", "")).strip()
    if not game_id:
        return None
    path = Path(project_root) / IDS_FILE
    cache = _read_json(path)
    hit = cache.get(game_id)
    if isinstance(hit, dict) and _SERIAL_OK.fullmatch(str(hit.get("serial", ""))) and re.fullmatch(
            r"[0-9A-F]{8}", str(hit.get("crc", ""))):
        return str(hit["serial"]), str(hit["crc"])
    name = Path(str(game.get("relative_path", ""))).name
    found = ids_from_logs(logs_dir).get(name) if name else None
    if found is None:
        return None
    cache[game_id] = {"serial": found[0], "crc": found[1], "learned_from": "pcsx2_log"}
    _atomic_json(path, cache)
    return found


def _bundle(appimage: Path, run: Callable[..., Any]) -> zipfile.ZipFile | None:
    try:
        key = (str(appimage), Path(appimage).stat().st_mtime_ns)
    except OSError:
        return None
    if key not in _zip_cache:
        z = None
        try:
            r = run(["7z", "x", "-so", str(appimage), ZIP_MEMBER], capture_output=True, timeout=30)
            if getattr(r, "returncode", 1) == 0 and r.stdout:
                z = zipfile.ZipFile(io.BytesIO(r.stdout))
        except Exception:
            z = None
        _zip_cache[key] = z
    return _zip_cache[key]


def bundle_groups(appimage: Path, serial: str, crc: str, run: Callable[..., Any] | None = None) -> set[str]:
    z = _bundle(appimage, run or subprocess.run)
    if z is None:
        return set()
    try:
        text = z.read(f"{serial}_{crc.upper()}.pnach").decode("utf-8", errors="replace")
    except KeyError:
        return set()
    return {g.strip() for g in re.findall(r"^\s*\[([^\]]+)\]", text, re.M)}


def available(groups: set[str]) -> list[str]:
    return [key for key, group in GROUPS if group in groups]


def get_toggles(project_root: Path, game_id: str) -> dict[str, bool] | None:
    rec = _read_json(Path(project_root) / TOGGLES_FILE).get(game_id)
    if not isinstance(rec, dict):
        return None
    return {key: bool(rec.get(key, False)) for key, _g in GROUPS}


def set_toggles(project_root: Path, game_id: str, wanted: Mapping[str, bool], offered: list[str]) -> dict[str, bool]:
    """Store the title's toggles; one not offered for the title is refused."""
    bad = [k for k, v in wanted.items() if v and k not in offered]
    if bad:
        raise ValueError("patch not available for this title: " + ",".join(sorted(bad)))
    path = Path(project_root) / TOGGLES_FILE
    data = _read_json(path)
    rec = {key: bool(wanted.get(key, False)) for key, _g in GROUPS}
    data[game_id] = rec
    _atomic_json(path, data)
    return rec


def game_ini_text(toggles: Mapping[str, bool] | None, extra: Mapping[str, Any] | None = None) -> str:
    """The game's settings file. `extra` (B81): {"cheats": bool, "cheat_groups": [names]}."""
    t = toggles or {}
    lines = [MARKER, "[EmuCore]",
             f"EnableWideScreenPatches = {'true' if t.get('ws') else 'false'}",
             f"EnableNoInterlacingPatches = {'true' if t.get('ni') else 'false'}"]
    if extra is not None:
        lines.append(f"EnableCheats = {'true' if extra.get('cheats') else 'false'}")
    if t.get("60"):
        lines += ["", "[Patches]", "Enable = " + dict(GROUPS)["60"]]
    groups = list((extra or {}).get("cheat_groups") or [])
    if groups:
        lines += ["", "[Cheats]"] + [f"Enable = {g}" for g in groups]
    return "\n".join(lines) + "\n"


def write_game_ini(gamesettings: Path, serial: str, crc: str, text: str) -> list[str]:
    folder = Path(gamesettings)
    folder.mkdir(parents=True, exist_ok=True)
    names = [f"{crc.upper()}.ini", f"{serial}_{crc.upper()}.ini"]
    for name in names:
        tmp = folder / (name + ".privyhub.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(folder / name)
    return names


def wrote_before(gamesettings: Path, serial: str, crc: str) -> bool:
    """B81: the title's game settings file exists and is this writer's (its marker line first)."""
    try:
        first = (Path(gamesettings) / f"{crc.upper()}.ini").read_text(encoding="utf-8").splitlines()[:1]
    except (OSError, UnicodeDecodeError):
        return False
    return first == [MARKER]


def log_line(toggles: Mapping[str, bool]) -> str:
    on = {k: ("on" if toggles.get(k) else "off") for k, _g in GROUPS}
    return f"PS2 patches: ws={on['ws']} ni={on['ni']} 60={on['60']}"
