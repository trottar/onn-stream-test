"""B59: a system listed in place from a folder the gitignored paths file names (B49's PS2 listing, generalised).

The paths file is PS2's: the file `PRIVYHUB_PS2_PATHS` names, else `runtime/h3_p1_paths.txt` (gitignored). A system
reads one key from it (`N64_DIR=` for N64; `GAMECUBE_DIR=` later) and nothing else. Folders are only read: no `mkdir`,
no write, hidden names skipped. Imported only by a flag-gated system module (`n64_session`); absent = never imported.
PS2's own listing (`ps2_session`) is not moved onto this module (B49-B57's tested path untouched).

Design: `docs/memory/evidence/b59_2026-11-08/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

PATHS_ENV = "PRIVYHUB_PS2_PATHS"
DEFAULT_PATHS = "runtime/h3_p1_paths.txt"


class InPlaceError(Exception):
    pass


def read_dir(project_root: Path, key: str, environ: Mapping[str, str] | None = None) -> Path | None:
    """The folder `key=` names in the paths file; None for a missing file, key or value. Only that key is read."""
    env = os.environ if environ is None else environ
    named = (env.get(PATHS_ENV) or "").strip()
    path = Path(named) if named else Path(project_root) / DEFAULT_PATHS
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    for line in lines:
        k, sep, value = line.partition("=")
        if sep and k.strip() == key and value.strip():
            return Path(value.strip())
    return None


def list_titles(folder: Path | None, rank: Mapping[str, int]) -> list[dict[str, Any]]:
    """The titles under `folder`, read-only: one per (folder, stem case-folded), the lowest `rank` suffix kept;
    other suffixes and hidden names skipped. [] when the folder is not configured or not there."""
    if folder is None:
        return []
    root = Path(folder)
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
            r = rank.get(p.suffix.casefold())
            if r is None:
                continue
            key = (str(p.parent), p.stem.casefold())
            if key not in best or r < best[key][0]:
                best[key] = (r, p)
    out = []
    for _, p in sorted(best.values(), key=lambda v: str(v[1]).casefold()):
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        out.append({"path": p, "relative": p.relative_to(root).as_posix(), "suffix": p.suffix.casefold(),
                    "size_bytes": size})
    return out


def resolve(folder: Path | None, relative_path: str, prefix: str, what: str) -> Path:
    """`<prefix><inside folder>` -> the file; a missing folder, a wrong prefix, an escape or a missing file refuses."""
    if folder is None:
        raise InPlaceError(f"{what} folder is not configured")
    rel = str(relative_path or "")
    if not rel.startswith(prefix):
        raise InPlaceError(f"not a {what} title path")
    root = Path(folder).resolve()
    target = (root / rel[len(prefix):]).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise InPlaceError(f"{what} title path escapes its folder") from exc
    if not target.is_file():
        raise InPlaceError(f"{what} title not found")
    return target
