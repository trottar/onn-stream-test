"""B81: the user's own cheat files, dropped into folders on the hub (nothing is ever downloaded for these).

- PS1 / SNES: `.cht` files (RetroArch's format) in `data/games/retroarch/cheats/<system>/<the game's file name without
  its ending>/` are offered in the Cheats list after the database's, and launched the same way.
- PS2: `.pnach` files in `data/games/ps2/cheats/<serial>/` (or the folder `PS2_CHEATS_DIR=` names in the paths file,
  then `<serial>/`) are offered by file name; the ticked ones are put together into PCSX2's
  `cheats/<SERIAL>_<CRC>.pnach` for that launch (PCSX2's own loading).

`PRIVYHUB_CHEAT_DROPINS=0` = today. Design: `docs/memory/evidence/b81_2026-11-09/design_written_before_code.md`.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping

KNOB_ENV = "PRIVYHUB_CHEAT_DROPINS"
RETRO_ROOT = "data/games/retroarch/cheats"
RETRO_SYSTEMS = ("ps1", "snes")
PS2_ROOT = "data/games/ps2/cheats"
PS2_DIR_KEY = "PS2_CHEATS_DIR"
PNACH_SOURCE_NAME = "Your PS2 cheat files"
PNACH_PROVIDER = "user_pnach"
USER_PROVIDER = "user"
_SERIAL_OK = re.compile(r"[A-Z]{4}-[0-9]{5}")


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return str(env.get(KNOB_ENV, "")).strip() != "0"


def _files(folder: Path, suffix: str) -> list[Path]:
    try:
        if not folder.is_dir():
            return []
        return sorted((p for p in folder.iterdir()
                       if p.is_file() and not p.name.startswith(".") and p.suffix.casefold() == suffix),
                      key=lambda p: p.name.casefold())
    except OSError:
        return []


def retro_dir(project_root: Path, system: str, stem: str) -> Path | None:
    if system not in RETRO_SYSTEMS or not stem or stem in (".", "..") or "/" in stem or "\\" in stem:
        return None
    return Path(project_root) / RETRO_ROOT / system / stem


def user_cht_files(project_root: Path, game: Mapping[str, Any]) -> list[Path]:
    system = str(game.get("system", "")).strip().casefold()
    stem = Path(str(game.get("relative_path", ""))).stem
    folder = retro_dir(project_root, system, stem)
    return _files(folder, ".cht") if folder is not None else []


def ps2_dir(project_root: Path, serial: str, environ: Mapping[str, str] | None = None) -> Path | None:
    if not _SERIAL_OK.fullmatch(serial or ""):
        return None
    import inplace_library
    named = inplace_library.read_dir(Path(project_root), PS2_DIR_KEY, environ)
    base = named if named is not None else Path(project_root) / PS2_ROOT
    return base / serial


def pnach_files(project_root: Path, serial: str, environ: Mapping[str, str] | None = None) -> list[Path]:
    folder = ps2_dir(project_root, serial, environ)
    return _files(folder, ".pnach") if folder is not None else []


def pnach_groups(text: str) -> list[str]:
    out: list[str] = []
    for g in re.findall(r"^\s*\[([^\]\r\n]+)\]\s*$", text or "", re.M):
        g = g.strip()
        if g and g not in out:
            out.append(g)
    return out


def stage_pnach(cheats_dir: Path, serial: str, crc: str, files: list[Path]) -> tuple[Path, list[str]]:
    """The ticked files' text, in order, as PCSX2's `<SERIAL>_<CRC>.pnach`; returns it and the files' groups."""
    if not _SERIAL_OK.fullmatch(serial or "") or not re.fullmatch(r"[0-9A-Fa-f]{8}", crc or ""):
        raise ValueError("the title's serial / CRC are not known")
    parts: list[str] = []
    groups: list[str] = []
    for n, f in enumerate(files, start=1):
        text = f.read_text(encoding="utf-8", errors="replace")
        parts.append(f"// PrivyHub: your cheat file {n} of {len(files)}\n" + text.rstrip("\n") + "\n")
        for g in pnach_groups(text):
            if g not in groups:
                groups.append(g)
    folder = Path(cheats_dir)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{serial}_{crc.upper()}.pnach"
    tmp = target.with_name(target.name + ".privyhub.tmp")
    tmp.write_text("\n".join(parts), encoding="utf-8")
    tmp.replace(target)
    return target, groups


def ensure_folders(project_root: Path, ps2: bool) -> list[str]:
    """The empty drop-in folders, created when missing (nothing is written inside them). Returns those created."""
    made = []
    wanted = [Path(RETRO_ROOT) / s for s in RETRO_SYSTEMS] + ([Path(PS2_ROOT)] if ps2 else [])
    for rel in wanted:
        p = Path(project_root) / rel
        if not p.is_dir():
            try:
                p.mkdir(parents=True, exist_ok=True)
                made.append(rel.as_posix())
            except OSError:
                pass
    return made
