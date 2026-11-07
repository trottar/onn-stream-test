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

B38: such a client also turns on the controller bridge's changed-only counter (`enable_changes`); its heartbeat row's
`updates_by_player` is then the per-slot count of reports whose state changed (a press, a stick or trigger move), and
`packets_by_player` today's per-packet count -- the sender sends all four players every tick (CTRL-L1), so only the
changes say which pad was used. Design: `docs/memory/evidence/b38_2026-11-02/design_written_before_code.md`.

B41: a client with `debug.privyhub.player_prompt=1` also sends `pad_claims=<slot:p|s,...>` (p = claimed at the prompt,
s = kept from the stable map); each slot entry of the rows then carries `claimed_by` (`prompt` / `stable`). No key
(`claims=None`) = the rows above byte for byte; a malformed value adds nothing. Design:
`docs/memory/evidence/b41_2026-11-06/design_written_before_code.md`.
B46: a client whose chooser picked also sends `players_chosen=<1|2|4>`; the rows then carry `players_chosen` and each
entry a `label` (`P1`-`P4`), and a changed pick is a change row. No key = B41's rows byte for byte. Design:
`docs/memory/evidence/b46_2026-11-07/design_written_before_code.md`.
"""

from __future__ import annotations

import re
from typing import Any

FIELD = "pad_slots"
_ENTRY = re.compile(r"^([0-3]):([0-9a-f]{6}):([a-z0-9]{2,12})$")
_CLAIM = re.compile(r"^([0-3]):([ps])$")


def parse_claims(raw: str) -> dict[int, str] | None:
    """B41: {slot: "prompt" | "stable"}; {} for an empty value; None when malformed."""
    raw = (raw or "").strip()
    if not raw:
        return {}
    out: dict[int, str] = {}
    for p in raw.split(",")[:5]:
        m = _CLAIM.match(p)
        if not m:
            return None
        out[int(m.group(1))] = "prompt" if m.group(2) == "p" else "stable"
    return out


def with_claims(slots: list[dict[str, Any]] | None, claims: str | None) -> list[dict[str, Any]] | None:
    """B41: the entries with `claimed_by` from the client's claims; unchanged with no key or a malformed one."""
    if slots is None or claims is None:
        return slots
    parsed = parse_claims(claims)
    if parsed is None:
        return slots
    return [({**e, "claimed_by": parsed[e["slot"]]} if e["slot"] in parsed else e) for e in slots]


def with_chosen(slots: list[dict[str, Any]] | None, players_chosen: int | None) -> list[dict[str, Any]] | None:
    """B46: each entry's `label` (`P1`-`P4`) once the chooser picked; unchanged without the key."""
    if slots is None or players_chosen is None:
        return slots
    return [{**e, "label": "P%d" % (int(e["slot"]) + 1)} for e in slots]


def parse_chosen(raw: str | None) -> int | None:
    """B46: the client's `players_chosen` (1 / 2 / 4); None when absent or malformed."""
    try:
        n = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return n if n in (1, 2, 4) else None


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
        self.last_chosen: int | None = None

    def _row(self, recovery: Any, when: str, slots: list[dict[str, Any]] | None, **extra: Any) -> None:
        fields: dict[str, Any] = {"when": when}
        if slots is None:
            fields["pad_slots_bad"] = True
        else:
            fields["slots"] = slots
            fields["count"] = len(slots)
        fields.update(extra)
        recovery._log("pad_slots", **fields)

    def start(self, recovery: Any, raw: str, claims: str | None = None,
              players_chosen: int | None = None) -> list[dict[str, Any]] | None:
        slots = with_chosen(with_claims(parse(raw), claims), players_chosen)
        # B46: the chooser's pick, only when the client sent one
        self._row(recovery, "start", slots, **({"players_chosen": players_chosen} if players_chosen is not None else {}))
        if slots is not None:
            self.last = slots
        self.last_chosen = players_chosen
        return slots

    def heartbeat(self, recovery: Any, raw: str, values: dict[str, Any], updates_by_player: Any = None,
                  claims: str | None = None, players_chosen: int | None = None) -> None:
        """One heartbeat's key: the row's fields, and a change row when the map moved."""
        slots = with_chosen(with_claims(parse(raw), claims), players_chosen)
        if slots is None:
            values["pad_slots_bad"] = True
            return
        values[FIELD] = slots
        # B46: the chooser's pick (only a client that picked sends it)
        extra: dict[str, Any] = {}
        if players_chosen is not None:
            values["players_chosen"] = players_chosen
            extra["players_chosen"] = players_chosen
        if isinstance(updates_by_player, dict):
            # B38: changes as updates_by_player, today's per-packet counts beside them
            if isinstance(updates_by_player.get("changes"), (list, tuple)):
                values["updates_by_player"] = [int(x) for x in updates_by_player["changes"]]
            if isinstance(updates_by_player.get("packets"), (list, tuple)):
                values["packets_by_player"] = [int(x) for x in updates_by_player["packets"]]
        elif isinstance(updates_by_player, (list, tuple)):
            values["updates_by_player"] = [int(x) for x in updates_by_player]
        if slots != self.last or players_chosen != self.last_chosen:
            self._row(recovery, "change", slots, heartbeat_sequence=values.get("sequence"), **extra)
            self.last = slots
            self.last_chosen = players_chosen


def enable_changes(controller: Any) -> bool:
    """B38: turn on the bridge's changed-only counter (idempotent); False when there is no bridge to turn it on in."""
    try:
        if getattr(controller, "_changes_by_player", None) is None:
            controller._changes_by_player = [0 for _ in range(int(controller.MAX_PLAYERS))]
        return True
    except Exception:
        return False


def updates_by_player(controller: Any) -> Any:
    """B38: {"changes": the changed-only counts, "packets": the per-packet counts}; B34's list when the counter is off."""
    try:
        enable_changes(controller)
        status = controller.status()
        if "changes_by_player" in status:
            return {"changes": status.get("changes_by_player"), "packets": status.get("updates_by_player")}
        return status.get("updates_by_player")
    except Exception:
        return None
