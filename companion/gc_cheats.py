"""B79: GameCube cheats from Dolphin's own bundled codes (no download), inside PRIVYHUB_GAMECUBE=1.

- the title's id from its disc header (read-only): `.rvz` / `.wia` keep the disc's first bytes uncompressed at 0x58,
  `.ciso` at 0x8000, `.iso` / `.gcm` at 0; the GameCube magic C2 33 9F 3D at the disc's 0x1C;
- the code names from Dolphin's `Sys/GameSettings/<ID3>.ini` and `<ID6>.ini`, read from the AppImage with `7z x -so`
  (never extracted, never edited): `[ActionReplay]` `$<name>`, `[Gecko]` `$<name> [<author>]`;
- the ticked codes written per launch to the user dir's `GameSettings/<ID6>.ini` `[ActionReplay_Enabled]` /
  `[Gecko_Enabled]` (Dolphin reads the enabled lists only from the user's files), only when at least one is ticked.

`PRIVYHUB_GC_CHEATS=0` = today. Design: `docs/memory/evidence/b79_2026-11-09/design_written_before_code.md`.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

KNOB_ENV = "PRIVYHUB_GC_CHEATS"
BUNDLED_DIR = "usr/share/dolphin-emu/Sys/GameSettings"
GC_MAGIC = bytes.fromhex("C2339F3D")
HEADER_OFFSETS = {b"RVZ\x01": 0x58, b"WIA\x01": 0x58}
CISO_OFFSET = 0x8000
ID_RE = re.compile(rb"[A-Z0-9]{6}")
SOURCE_NAME = "Dolphin's built-in codes"
PROVIDER = "dolphin_bundled"


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return str(env.get(KNOB_ENV, "")).strip() != "0"


def disc_id(path: Path) -> str | None:
    """The 6-character game id from the disc header, or None (no file, too short, not a GameCube disc)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(CISO_OFFSET + 0x100)
    except OSError:
        return None
    if head[:4] in HEADER_OFFSETS:
        off = HEADER_OFFSETS[head[:4]]
    elif Path(path).suffix.casefold() == ".ciso" or head[:4] == b"CISO":
        off = CISO_OFFSET
    else:
        off = 0
    gid = head[off:off + 6]
    if len(gid) < 6 or not ID_RE.fullmatch(gid) or head[off + 0x1C:off + 0x20] != GC_MAGIC:
        return None
    return gid.decode("ascii")


def read_bundled(appimage: Path, name: str, run: Callable[..., Any] | None = None) -> str | None:
    """One bundled GameSettings file's text from the AppImage (read into memory only), or None."""
    if not re.fullmatch(r"[A-Z0-9]{3,6}\.ini", name):
        return None
    try:
        r = (run or subprocess.run)(["7z", "x", "-so", str(appimage), f"{BUNDLED_DIR}/{name}"], capture_output=True, timeout=10)
    except Exception:
        return None
    if getattr(r, "returncode", 1) != 0 or not r.stdout:
        return None
    return r.stdout.decode("utf-8", errors="replace")


def parse_codes(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    section = None
    for line in (text or "").splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1]
            continue
        if not s.startswith("$"):
            continue
        if section == "ActionReplay":
            name = s[1:].strip()
            kind = "ar"
        elif section == "Gecko":
            name = s[1:].split("[", 1)[0].strip()
            kind = "gecko"
        else:
            continue
        if name:
            out.append((kind, name))
    return out


def codes_for(gid: str, reader: Callable[[str], str | None]) -> list[dict[str, Any]]:
    """The codes Dolphin lists for `gid`: `<ID3>.ini` then `<ID6>.ini`, each (kind, name) once."""
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for name in (gid[:3] + ".ini", gid + ".ini"):
        for kind, code in parse_codes(reader(name) or ""):
            if (kind, code) in seen:
                continue
            seen.add((kind, code))
            out.append({"index": len(out), "description": code, "kind": kind})
    return out


def enabled_text(existing: str, ar: list[str], gecko: list[str]) -> str:
    """The user file: every other section of `existing` kept as it was; the two `_Enabled` sections replaced."""
    replaced = ("ActionReplay_Enabled", "Gecko_Enabled")
    kept: list[str] = []
    section = None
    for line in (existing or "").splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1]
        if section in replaced:
            continue
        kept.append(line)
    while kept and not kept[-1].strip():
        kept.pop()
    out = kept + ([""] if kept else [])
    for title, names in (("ActionReplay_Enabled", ar), ("Gecko_Enabled", gecko)):
        if names:
            out.append(f"[{title}]")
            out.extend(f"${n}" for n in names)
    return "\n".join(out).rstrip("\n") + "\n"


def write_enabled(user_dir: Path, gid: str, ar: list[str], gecko: list[str]) -> Path | None:
    """`GameSettings/<gid>.ini` in the user dir, only with at least one code; None (nothing written) otherwise."""
    if not (ar or gecko):
        return None
    if not ID_RE.fullmatch(gid.encode("ascii", "replace")):
        raise ValueError("not a GameCube game id")
    folder = Path(user_dir) / "GameSettings"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{gid}.ini"
    try:
        existing = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        existing = ""
    tmp = target.with_name(target.name + ".privyhub.tmp")
    tmp.write_text(enabled_text(existing, ar, gecko), encoding="utf-8")
    tmp.replace(target)
    return target
