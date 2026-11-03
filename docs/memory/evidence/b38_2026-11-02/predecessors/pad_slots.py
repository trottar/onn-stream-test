"""B34: the client's stable player-slot map, as the host sees it -- so a record can say which pad was which.

No host flag: the client's key is the switch. A client with `debug.privyhub.pad_slots=stable` sends
`pad_slots=<slot:pad:class,...>` on its `native-stream-start` and on every heartbeat (`pad` is 6 hex of a hash of the
device's vendor / product / descriptor; `class` a vendor class; no names). **An old or flag-absent client sends no
key: nothing imports this module and every row is today's.** Design:
`docs/memory/evidence/b34_2026-10-31/design_written_before_code.md` (hashed before this code).

Rows: at each start one recovery-log row `pad_slots` (`when: "start"`); on a heartbeat the heartbeat row gets
`pad_slots` (the list) and `updates_by_player` (the controller bridge's per-slot counters), and a recovery-log row
`pad_slots` (`when: "change"`) when the map differs from the last one written. A malformed value is dropped
(`pad_slots_bad: true` on the row), never written raw.
"""

from __future__ import annotations

import re
from typing import Any

FIELD = "pad_slots"
_ENTRY = re.compile(r"^([0-3]):([0-9a-f]{6}):([a-z0-9]{2,12})$")


def parse(raw: str) -> list[dict[str, Any]] | None:
    """The map as a list of {slot, pad, class}; [] for an empty map; None when malformed."""
    raw = (raw or "").strip()
    if not raw:
        return []
    parts = raw.split(",")
    if len(parts) > 4:
        return None
    out: list[dict[str, Any]] = []
    for p in parts:
        m = _ENTRY.match(p)
        if not m:
            return None
        out.append({"slot": int(m.group(1)), "pad": m.group(2), "class": m.group(3)})
    if len({e["slot"] for e in out}) != len(out):
        return None
    return out


class SlotsLog:
    """One per plugin: the last map written to the recovery log."""

    def __init__(self) -> None:
        self.last: list[dict[str, Any]] | None = None

    def _row(self, recovery: Any, when: str, slots: list[dict[str, Any]] | None, **extra: Any) -> None:
        fields: dict[str, Any] = {"when": when}
        if slots is None:
            fields["pad_slots_bad"] = True
        else:
            fields["slots"] = slots
            fields["count"] = len(slots)
        fields.update(extra)
        recovery._log("pad_slots", **fields)

    def start(self, recovery: Any, raw: str) -> list[dict[str, Any]] | None:
        slots = parse(raw)
        self._row(recovery, "start", slots)
        if slots is not None:
            self.last = slots
        return slots

    def heartbeat(self, recovery: Any, raw: str, values: dict[str, Any], updates_by_player: Any = None) -> None:
        """One heartbeat's key: the row's fields, and a change row when the map moved."""
        slots = parse(raw)
        if slots is None:
            values["pad_slots_bad"] = True
            return
        values[FIELD] = slots
        if isinstance(updates_by_player, (list, tuple)):
            values["updates_by_player"] = [int(x) for x in updates_by_player]
        if slots != self.last:
            self._row(recovery, "change", slots, heartbeat_sequence=values.get("sequence"))
            self.last = slots


def updates_by_player(controller: Any) -> Any:
    """The controller bridge's per-slot update counters (already kept), or None."""
    try:
        return controller.status().get("updates_by_player")
    except Exception:
        return None
