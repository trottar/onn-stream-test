"""G5-S4: the remote rung cap -- a data saver the user sets, for remote sessions.

`PRIVYHUB_REMOTE_RUNG_CAP=<kbps>`. **Absent (or empty) = today**: nothing imports
this module; the ladder has no cap and writes no row about one. The design is
`docs/memory/evidence/g5_s4_2026-10-17/design_written_before_code.md` (hashed
before this code).

- **Valid** only at a rung of G5-S3's remote list (4000 / 5000 / 5500 / 6000 /
  7000). Anything else is logged once (a `remote_cap_config` row) and ignored.
- **Depends on G5-S3** (`PRIVYHUB_REMOTE_LADDER=1`): without it the cap does
  nothing and says so once.
- **Effect, on a remote path only** (`path_class` from G5-S3's shared
  `RemoteLadder`):
  - the clamp in the ladder's target selection (`LivePolicy._decide`): a
    decrease aimed above the cap goes to the cap; an increase aimed above it is
    refused `remote_cap`;
  - the move to the cap (`LiveController.observe`, after the feed): with the
    stream above the cap, one ROUTINE decision (trigger `remote_cap`) through
    every gate of the ladder, aimed at the cap.

  Below the cap every step is the ladder's own; the cap never lowers the floor
  (every valid cap is >= 4000). On the LAN: nothing.
- **Recorded:** every clamp's row carries `source: remote_cap`, `wish_kbps` (the
  ladder's target), `capped_kbps`, `cap_kbps`.
"""

from __future__ import annotations

from typing import Any, Mapping

import remote_ladder as rl

FLAG_ENV = "PRIVYHUB_REMOTE_RUNG_CAP"
SOURCE = TRIGGER = "remote_cap"
VALID_KBPS = rl.REMOTE_LADDER_KBPS          # 4000 / 5000 / 5500 / 6000 / 7000
DECISION_EVENTS = ("transition", "would_act", "refused", "hold")


def parse(raw: Any) -> tuple[int | None, str | None, Any]:
    """(cap, refusal reason, the value as it may be recorded)."""
    text = str(raw or "").strip()
    if not text.isdigit():
        return None, "not_a_remote_rung", "non-numeric"
    value = int(text)
    if value not in VALID_KBPS:
        return None, "not_a_remote_rung", value
    return value, None, value


class RemoteCap:
    def __init__(self, raw: Any, ladder: Any) -> None:
        self.ladder = ladder
        self.cap_kbps, reason, self.value = parse(raw)
        if reason is None and ladder is None:
            reason = "remote_ladder_flag_absent"
        self.reason = reason
        self.active = reason is None
        self.clamps = 0              # every target the cap changed or blocked
        self.moves = 0               # transitions to the cap it initiated

    # -- the log -------------------------------------------------------------
    def config_row(self) -> dict[str, Any]:
        row = {"event": "remote_cap_config", "source": SOURCE, "active": self.active, "value": self.value,
               "cap_kbps": self.cap_kbps if self.active else None, "valid_kbps": list(VALID_KBPS)}
        if self.reason:
            row["reason"] = self.reason
            row["note"] = ("ignored; the ladder behaves as without the cap" if self.reason == "not_a_remote_rung"
                           else "the cap needs PRIVYHUB_REMOTE_LADDER=1 (G5-S3); it does nothing")
        return row

    def status(self) -> dict[str, Any]:
        return {"flag": FLAG_ENV, "active": self.active, "cap_kbps": self.cap_kbps, "reason": self.reason,
                "applies_now": self.applies(), "clamps": self.clamps, "moves": self.moves}

    # -- the effect ------------------------------------------------------------
    def applies(self) -> bool:
        return bool(self.active and self.ladder is not None and self.ladder.path_class == rl.PATH_REMOTE)

    def clamp(self, policy: Any, direction: str, target: int | None,
              m: dict[str, Any]) -> tuple[int | None, dict[str, Any], dict[str, Any] | None]:
        """In `_decide`, after the target is chosen: (target, measurements, blocked).

        `blocked` is not None for an increase the cap refuses (the caller refuses it)."""
        if target is None or not self.applies():
            return target, m, None
        cap = int(self.cap_kbps)
        level = int(policy.level_kbps)
        if direction == "up":
            if target <= cap:
                return target, m, None
            self.clamps += 1
            info = {"source": SOURCE, "wish_kbps": int(target), "capped_kbps": level, "cap_kbps": cap}
            return target, dict(m, remote_cap=info), info
        if m.get("trigger") == TRIGGER:
            new = cap                                  # the move to the cap is aimed at the cap
        elif target > cap:
            new = cap                                  # a decrease aimed above the cap goes to the cap
        else:
            return target, m, None                     # at or below the cap: the ladder's own step
        if new != target:
            self.clamps += 1
        info = {"source": SOURCE, "wish_kbps": int(target if m.get("trigger") != TRIGGER else level),
                "capped_kbps": new, "cap_kbps": cap}
        return new, dict(m, remote_cap=info), None

    def after_feed(self, policy: Any, s: Mapping[str, Any], ctx: dict[str, Any],
                   events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """The move to the cap: one ROUTINE decision through every gate, when the stream is above it."""
        if not self.applies() or int(policy.level_kbps) <= int(self.cap_kbps):
            return events
        if (any(e.get("event") in DECISION_EVENTS for e in events) or policy.last_disposition != "evaluated"
                or policy.pending is not None or policy.reason == "routine_deferred_escalating"):
            return events
        m = {"trigger": TRIGGER, "cap_kbps": int(self.cap_kbps)}
        forced = policy._decide("ROUTINE", m, int(s["elapsed_ms"]), ctx)
        for e in forced:
            if e.get("event") in ("transition", "would_act"):
                e["reason"] = SOURCE
                policy.reason = SOURCE
                if policy.last_action is not None:
                    policy.last_action["reason"] = SOURCE
                self.moves += 1
        return events + forced


def from_environ(environ: Mapping[str, str], ladder: Any) -> RemoteCap | None:
    raw = environ.get(FLAG_ENV)
    if raw is None or str(raw).strip() == "":
        return None
    return RemoteCap(raw, ladder)
