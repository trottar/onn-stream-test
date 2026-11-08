"""B56: what an import tells the games list -- a "NEW" tag for 7 days, a hidden `.iso`, "(OpenBIOS)" on PlayStation.

Only with `PRIVYHUB_IMPORT=1` does the plugin import this module (absent = the list byte for byte). The marks are
`data/import/marks.json`, written by `tools/import_usb.py apply` (`new`: game id -> the import's unix ms; `hide`: game id
-> why), beside `data/games/metadata.json`, which the metadata update rebuilds from scratch (so the marks are not kept
there). The onn shows each node's host-given name, so no client change is needed. Design:
`docs/memory/evidence/b56_2026-11-08/design_written_before_code.md` (hashed before this code). Never raises.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FLAG_ENV = "PRIVYHUB_IMPORT"
MARKS_REL = Path("data") / "import" / "marks.json"
JOURNAL_REL = Path("data") / "import" / "journal.json"      # B58
BIOS_REL = Path("data") / "games" / "retroarch" / "system"
BIOS_FILES = ("scph5500.bin", "scph5501.bin", "scph5502.bin")
BIOS_SIZE = 524_288
NEW_DAYS = 7
NEW_TAG = " · NEW"
OPENBIOS_LABEL = " (OpenBIOS)"


def read(project_root: Path) -> dict[str, Any]:
    try:
        m = json.loads((Path(project_root) / MARKS_REL).read_text(encoding="utf-8"))
        if isinstance(m, dict):
            return {"new": dict(m.get("new") or {}), "hide": dict(m.get("hide") or {})}
    except (OSError, ValueError):
        pass
    return {"new": {}, "hide": {}}


def pending(project_root: Path) -> dict[str, str]:
    """B58: the ids of titles an import is copying, or left half-placed by an interrupted apply (the tool's journal,
    `data/import/journal.json`): left out of the list until the next apply finishes or cleans them. Never raises."""
    try:
        j = json.loads((Path(project_root) / JOURNAL_REL).read_text(encoding="utf-8"))
        entries = j.get("entries") if isinstance(j, dict) else None
        if not isinstance(entries, dict):
            return {}
        return {str(i): "import in progress" for e in entries.values() if isinstance(e, dict)
                for i in (e.get("list_ids") or []) if isinstance(i, str)}
    except (OSError, ValueError, AttributeError, TypeError):
        return {}


def is_new(marks: dict[str, Any], game_id: str, now_ms: int) -> bool:
    try:
        at = int(marks["new"][game_id])
    except (KeyError, TypeError, ValueError):
        return False
    return 0 <= now_ms - at < NEW_DAYS * 86_400_000


def ps1_bios_present(project_root: Path) -> bool:
    d = Path(project_root) / BIOS_REL
    for name in BIOS_FILES:
        try:
            if (d / name).stat().st_size == BIOS_SIZE:
                return True
        except OSError:
            continue
    return False
