"""LAN-R1: one rung down on sustained FEC-unrecoverable groups, on any path.

`PRIVYHUB_LAN_LOSS_RULE=1`. **Absent (or anything but `1`) = today**: the ladder
does not import this module and `LiveController.observe` runs as before. The
design is `docs/memory/evidence/lan_r1_2026-10-21/design_written_before_code.md`
(hashed before this code).

- **The signal:** the client's FEC-unrecoverable groups since its previous
  report (`telemetry.fec.unrecoverable_groups_delta`, host-computed from the
  client-health counters; missing = 0), on reports the ladder evaluated.
- **The rule:** when each of the newest K = 2 non-overlapping 5-report windows
  (20 s) holds >= T = 4, ask the ladder for one rung down, through its own
  `_decide("ROUTINE", ...)` with the one-rung target of `capacity_mild`. Every
  gate holds (hold-downs, blackout, 60-s session age, guards, rate limit,
  oscillation guard). Labelled `lan_loss`. Never below 5000.
- **T and K from the data** (LAN-R1 §2): 0 false triggers in every clean window
  on file and in last night's clean minutes; Sunday's first ask 05:03:05Z, before
  the 05:06 burst. An edge cell, chosen in sample; the live test decides.
- **Re-climb:** the ladder's existing increase rule, unchanged.
- **Recorded:** one `lan_loss_rule` event per ask (the window sums, T, K, the
  level, the ladder's answer).
"""

from __future__ import annotations

from typing import Any, Mapping

FLAG_ENV = "PRIVYHUB_LAN_LOSS_RULE"
SOURCE = TRIGGER = "lan_loss"
T_UNREC = 4                 # unrecoverable groups per 5-report window, on each of ...
K_WINDOWS = 2               # ... the newest K non-overlapping windows
WINDOW_REPORTS = 5          # adaptive_bitrate.WINDOW_REPORTS: 10 s at the 2-s cadence
FLOOR_KBPS = 5000           # the LAN list's floor (LADDER_KBPS[0])
DECISION_EVENTS = ("transition", "would_act", "refused", "hold")


def flag_on(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


def unrec_of(telemetry: Mapping[str, Any] | None) -> int:
    v = ((telemetry or {}).get("fec") or {}).get("unrecoverable_groups_delta")
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 else 0


class LanLossRule:
    """Pure: no clock, no I/O. Called once per client report, after the ladder's feed."""

    def __init__(self) -> None:
        self.values: list[int] = []
        self._last_elapsed: Any = None
        self._last_blackout = 0
        self.asks = 0

    def clear(self) -> None:
        self.values = []

    def windows(self) -> list[int] | None:
        """The newest K window sums, newest first; None under K full windows."""
        need = K_WINDOWS * WINDOW_REPORTS
        if len(self.values) < need:
            return None
        v = self.values[-need:]
        return [sum(v[len(v) - WINDOW_REPORTS * (i + 1): len(v) - WINDOW_REPORTS * i]) for i in range(K_WINDOWS)]

    def after_feed(self, policy: Any, s: Mapping[str, Any], ctx: dict[str, Any],
                   telemetry: Mapping[str, Any] | None, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        el = s.get("elapsed_ms")
        if isinstance(el, (int, float)) and isinstance(self._last_elapsed, (int, float)) and el < self._last_elapsed:
            self.clear()                          # a new client session
        if isinstance(el, (int, float)):
            self._last_elapsed = el
        if policy.blackout_remaining > self._last_blackout:
            self.clear()                          # an SSRC change or a transition re-armed the blackout
        self._last_blackout = policy.blackout_remaining
        if policy.last_disposition != "evaluated":
            return events
        self.values.append(unrec_of(telemetry))
        del self.values[: max(0, len(self.values) - K_WINDOWS * WINDOW_REPORTS)]
        ws = self.windows()
        if ws is None or any(w < T_UNREC for w in ws) or int(policy.level_kbps) <= FLOOR_KBPS:
            return events
        if (any(e.get("event") in DECISION_EVENTS for e in events) or policy.pending is not None
                or policy.reason == "routine_deferred_escalating"):
            return events
        self.asks += 1
        self.clear()
        level = int(policy.level_kbps)
        m = {"trigger": "capacity_mild", "lan_loss_windows": ws, "lan_loss_t": T_UNREC, "lan_loss_k": K_WINDOWS}
        forced = policy._decide("ROUTINE", m, int(el), ctx)
        result = "none"
        for e in forced:
            if e.get("event") in ("transition", "would_act"):
                e["reason"] = SOURCE
                e["trigger"] = SOURCE
                policy.reason = SOURCE
                if policy.last_action is not None:
                    policy.last_action["reason"] = SOURCE
                result = e["event"]
            elif e.get("event") == "refused":
                e["trigger"] = SOURCE
                result = f"refused:{e.get('reason')}"
            elif e.get("event") == "hold":
                e["trigger"] = SOURCE
                result = "hold"
        if not forced:   # a refusal already logged in the same (class, reason) run returns no row
            result = f"refused:{policy.reason}"
        self._last_blackout = policy.blackout_remaining
        return events + forced + [{"event": "lan_loss_rule", "source": SOURCE, "unrec_windows": ws, "t": T_UNREC,
                                   "k": K_WINDOWS, "level_kbps": level, "ladder_result": result}]

    def feed(self, policy: Any, s: dict[str, Any], ctx: dict[str, Any] | None,
             telemetry: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """The harness entry: the ladder's own feed, then the rule."""
        ctx = ctx or {}
        return self.after_feed(policy, s, ctx, telemetry, policy.feed(s, ctx))


def from_environ(environ: Mapping[str, str]) -> LanLossRule | None:
    # LAN-R2: PRIVYHUB_LAN_LOSS_RULE=bidir -- the rule renamed to its purpose (unrec AND the uplink's own silences)
    if (environ.get(FLAG_ENV) or "").strip() == BIDIR_VALUE:
        return LanBidirRule()
    return LanLossRule() if flag_on(environ) else None


# --- LAN-R2: step down when the link is bidirectionally bad -----------------------------------------------------
# `PRIVYHUB_LAN_LOSS_RULE=bidir` (`1` = LAN-R1 above, unchanged). Design:
# docs/memory/evidence/lan_r2_2026-10-22/design_written_before_code.md (hashed before this code). On the data on
# file no host signal tells Sunday's pre-burst loss from 1 % random loss (rule_search*.md); what separates is the
# bidirectional burst: LAN-R1's windows (each >= 4 unrecoverable groups) AND, in each window, >= 2 uplink silences
# >= 400 ms (the host's own controller stream). 0 asks in BENCH-R1 cells 1-4, the clean windows and last night;
# Sunday 05:06:13Z (every burst minute). An edge cell, in sample; the live test decides.

import threading
import time
from collections import deque

BIDIR_VALUE = "bidir"
SOURCE_BIDIR = "lan_bidir"
UPLINK_MIN_MS = 400          # an uplink silence this long ...
UPLINK_PER_WINDOW = 2        # ... at least this many times in each window


class UplinkSilences:
    """The controller receive loop's silences >= 250 ms, (start, end) on the monotonic clock; bounded."""

    def __init__(self, maxlen: int = 512) -> None:
        self._ring: deque[tuple[float, float]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def note(self, start: float, end: float) -> None:
        with self._lock:
            self._ring.append((float(start), float(end)))

    def ended_between(self, a: float, b: float, min_ms: float) -> int:
        """Silences >= min_ms that ENDED in (a, b] (a silence is known only at its end)."""
        with self._lock:
            return sum(1 for s, e in self._ring if a < e <= b and (e - s) * 1000.0 >= min_ms)


UPLINK = UplinkSilences()


class LanBidirRule(LanLossRule):
    """LAN-R1's rule with a second term in each window; its asks labelled lan_bidir."""

    def __init__(self, uplink: UplinkSilences | None = None, clock=time.monotonic) -> None:
        super().__init__()
        self.uplink = uplink if uplink is not None else UPLINK
        self.clock = clock
        self.up_values: list[int] = []
        self._pending_up = 0
        self._last_eval_t: float | None = None
        self.last_up_windows: list[int] | None = None

    def clear(self) -> None:
        super().clear()
        self.up_values = []

    def windows(self) -> list[int] | None:
        """Called once per evaluated report, after the unrec value was appended: append the uplink count in step."""
        self.up_values.append(self._pending_up)
        del self.up_values[: max(0, len(self.up_values) - K_WINDOWS * WINDOW_REPORTS)]
        ws = super().windows()
        if ws is None or len(self.up_values) < K_WINDOWS * WINDOW_REPORTS:
            return None
        u = self.up_values
        up = [sum(u[len(u) - WINDOW_REPORTS * (i + 1): len(u) - WINDOW_REPORTS * i]) for i in range(K_WINDOWS)]
        self.last_up_windows = up
        return ws if all(n >= UPLINK_PER_WINDOW for n in up) else [0] * K_WINDOWS

    def after_feed(self, policy: Any, s: Mapping[str, Any], ctx: dict[str, Any],
                   telemetry: Mapping[str, Any] | None, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if policy.last_disposition == "evaluated":
            now = self.clock()
            a = self._last_eval_t if self._last_eval_t is not None else now - 2.0
            self._pending_up = self.uplink.ended_between(a, now, UPLINK_MIN_MS)
            self._last_eval_t = now
        asks = self.asks
        out = super().after_feed(policy, s, ctx, telemetry, events)
        if self.asks > asks:                                  # relabel this ask to its purpose
            for e in out[len(events):]:
                if e.get("reason") == SOURCE:
                    e["reason"] = SOURCE_BIDIR
                if e.get("trigger") == SOURCE:
                    e["trigger"] = SOURCE_BIDIR
                if e.get("event") == "lan_loss_rule":
                    e["source"] = SOURCE_BIDIR
                    e["uplink_windows"] = self.last_up_windows
                    e["uplink_min_ms"] = UPLINK_MIN_MS
                    e["uplink_per_window"] = UPLINK_PER_WINDOW
            if policy.reason == SOURCE:
                policy.reason = SOURCE_BIDIR
            if policy.last_action is not None and policy.last_action.get("reason") == SOURCE:
                policy.last_action["reason"] = SOURCE_BIDIR
        return out
