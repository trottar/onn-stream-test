"""G5-S2: the WAN adaptation rules (docs/WAN_ADAPTATION_RULES.md R1-R5) as a
guarded input to the live ladder.

Behind `PRIVYHUB_WAN_ADAPTATION=1`. **Absent = today**: `adaptive_bitrate_live`
never imports this module and its `LiveController.observe` calls
`policy.feed(s, ctx)` exactly as before. The design is
`docs/memory/evidence/g5_s2_2026-10-16/design_written_before_code.md` (hashed
before this code).

The ladder stays the decider. Per decision tick (one client report) the rules
give **at most one suggestion**, applied only as an additional constraint:

- `no_step_up` / `hold` -- an increase the ladder would take this tick is
  refused (`wan_no_step_up`); nothing else changes;
- `step_down` -- a one-rung decrease the ladder did not take, through the
  ladder's own `_decide` and so every existing gate (hold-downs, blackout,
  guards, rate limit, oscillation); its rows are labelled `wan_rules`;
- `floor_4000` -- recorded only: the remote floor 720p/4000 (C5-M3) is below
  the actuator's validated ladder (5000-7000), so it is never actuated here.

R4 (FEC) is "FEC switch: not implemented; the fixed 8+1 stays" (C4-M1): no
suggestion is ever about FEC. Every non-`none` suggestion is one
`decisions.jsonl` row with `source: wan_rules`.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Any, Mapping

import adaptive_bitrate as ab
import wan_telemetry as wt

FLAG_ENV = "PRIVYHUB_WAN_ADAPTATION"
SOURCE = "wan_rules"

# ---- constants (each from an existing record or the ladder's code) ------------
WINDOW_REPORTS = wt.WINDOW_REPORTS               # 5: the ladder's evidence window
BLACKOUT_REPORTS = ab.BLACKOUT_REPORTS           # 3: R1.1
INCREASE_WINDOW_REPORTS = 90                     # adaptive_bitrate_live.INCREASE_WINDOW_REPORTS: R1.2
R2_CONSECUTIVE_WINDOWS = 2                       # R2 (the task): 2 consecutive windows
R5_CLEAN_WINDOWS_LAN = INCREASE_WINDOW_REPORTS // WINDOW_REPORTS   # 18: the ladder's hysteresis, in windows
R5_CLEAN_WINDOWS_REMOTE = 2 * R5_CLEAN_WINDOWS_LAN                 # 36: doubled on a remote path
LAN_FLOOR_KBPS = 5000                            # the ladder's floor (LADDER_KBPS[0])
REMOTE_FLOOR_KBPS = 4000                         # C5-M3: 720p/4000, the only lower rung that passed
R3_FLOOR_PERSIST_REPORTS = 60                    # ROUTINE's down hold-down (HOLDDOWN_REPORTS): the persistence
R4_NOTE = "FEC switch: not implemented; the fixed 8+1 stays (C4-M1)"
RELAYED_NOTE = "not classified; no relayed-path cap exists (R1.3)"

HISTORY = R5_CLEAN_WINDOWS_REMOTE * WINDOW_REPORTS   # enough reports for the longest rule

# The overlay's address space, built from integers (no literal), as G3-S1's.
OVERLAY_NETWORKS = (
    ipaddress.ip_network((0x64400000, 10)),
    ipaddress.ip_network((0xFD7A115CA1E0 << 80, 48)),
)

PATH_LAN, PATH_REMOTE = "lan", "remote"


def flag_on(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


def is_overlay_address(value: Any) -> bool:
    try:
        ip = ipaddress.ip_address(str(value))
    except ValueError:
        return False
    return any(ip.version == n.version and ip in n for n in OVERLAY_NETWORKS)


def path_class(ctx: Mapping[str, Any]) -> str:
    """remote / lan. The ladder's context carries no client address today; a
    caller may supply `path_class` ("remote" / "overlay") or `target_address`."""
    pc = str(ctx.get("path_class") or "").lower()
    if pc in (PATH_REMOTE, "overlay"):
        return PATH_REMOTE
    if is_overlay_address(ctx.get("target_address")):
        return PATH_REMOTE
    return PATH_LAN


@dataclass
class Suggestion:
    kind: str                    # none | hold | no_step_up | step_down | floor_4000
    rule: str | None = None
    primary: str | None = None
    classes: tuple[str, ...] = ()
    target_kbps: int | None = None
    detail: str | None = None

    @property
    def blocks_increase(self) -> bool:
        return self.kind in ("hold", "no_step_up", "step_down", "floor_4000")


class WanRules:
    """Pure: no clock, no I/O. One `tick` per evaluated client report."""

    def __init__(self) -> None:
        self.reports: list[wt.Report] = []
        self.since_event: int | None = None       # evaluated reports since the last path event
        self.capacity_at_floor = 0                # consecutive reports with a capacity window at 5000 (R3)
        self._last_recovery_playing: bool | None = None
        self._last_overlay_path: Any = None

    # -- inputs ------------------------------------------------------------
    def note_path_event(self) -> None:
        self.since_event = 0

    def observe_context(self, ctx: Mapping[str, Any]) -> bool:
        """Recovery pause / resume and overlay path changes from the context. True = an event."""
        event = False
        playing = (ctx.get("guards") or {}).get("recovery_playing")
        if isinstance(playing, bool):
            if self._last_recovery_playing is not None and playing != self._last_recovery_playing:
                event = True
            self._last_recovery_playing = playing
        ov = ctx.get("overlay_path")
        if ov is not None:
            if self._last_overlay_path is not None and ov != self._last_overlay_path:
                event = True
            self._last_overlay_path = ov
        if event:
            self.note_path_event()
        return event

    def add_report(self, r: wt.Report) -> None:
        self.reports.append(r)
        if len(self.reports) > HISTORY:
            del self.reports[: len(self.reports) - HISTORY]
        if self.since_event is not None:
            self.since_event += 1

    # -- the windows ---------------------------------------------------------
    def _window(self, back: int) -> list[wt.Report] | None:
        """The `back`-th non-overlapping 5-report window counted from the newest (0 = current)."""
        end = len(self.reports) - back * WINDOW_REPORTS
        start = end - WINDOW_REPORTS
        if start < 0:
            return None
        return self.reports[start:end]

    def _classify(self, back: int) -> dict[str, Any] | None:
        w = self._window(back)
        return wt.classify_window(w, []) if w is not None else None

    def clean_windows(self, limit: int) -> int:
        """Consecutive `clean` windows (G5-S1's class: a lossy window is not clean), newest first."""
        n = 0
        for back in range(limit):
            c = self._classify(back)
            if c is None or c["classes"] != ["clean"]:
                break
            n += 1
        return n

    # -- the suggestion --------------------------------------------------------
    def tick(self, level_kbps: int, path: str, top_kbps: int = 7000) -> Suggestion:
        """Only constraining suggestions: a step down above the floor, a block below the top."""
        cur = self._classify(0)
        if cur is None:   # under one window of history: no K clean windows yet (R5)
            if level_kbps >= top_kbps:
                return Suggestion("none")
            return Suggestion("no_step_up", "R5.1", None, (), detail="under one window of history")
        classes = tuple(cur["classes"])
        primary = cur["primary"]
        prev = self._classify(1)

        def s(kind: str, rule: str, **kw: Any) -> Suggestion:
            return Suggestion(kind, rule, primary, classes, **kw)

        # R2: latency-limited or starved on 2 consecutive windows -> one rung down.
        latency = ("latency-limited", "starved")
        if prev is not None and any(c in classes for c in latency) and any(c in prev["classes"] for c in latency):
            if level_kbps > LAN_FLOOR_KBPS:
                return s("step_down", "R2.1", detail="latency-limited / starved on 2 consecutive windows")
        # R3: capacity-limited -> the next rung down; the floor by path.
        if "capacity-limited" in classes:
            if level_kbps > LAN_FLOOR_KBPS:
                self.capacity_at_floor = 0
                return s("step_down", "R3.1", detail="capacity-limited")
            self.capacity_at_floor += 1
            if path == PATH_REMOTE and self.capacity_at_floor >= R3_FLOOR_PERSIST_REPORTS:
                return s("floor_4000", "R3.2", target_kbps=REMOTE_FLOOR_KBPS,
                         detail="capacity-limited persisted at 5000 for the hold-down on a remote path; "
                                "recorded only (the actuator's validated ladder ends at 5000)")
        else:
            self.capacity_at_floor = 0
        if level_kbps >= top_kbps:
            return Suggestion("none", None, primary, classes)    # no increase to block
        # R1: a path event -> hold for the blackout, then no step up until the window refills.
        if self.since_event is not None:
            if self.since_event <= BLACKOUT_REPORTS:
                return s("hold", "R1.1", detail="blackout after a path event")
            if self.since_event < INCREASE_WINDOW_REPORTS:
                return s("no_step_up", "R1.2", detail="the increase window refills after a path event")
        # R5: an increase only after K consecutive clean windows (doubled on a remote path).
        k = R5_CLEAN_WINDOWS_REMOTE if path == PATH_REMOTE else R5_CLEAN_WINDOWS_LAN
        if self.clean_windows(k) < k:
            return s("no_step_up", "R5.1", detail=f"fewer than {k} consecutive clean windows")
        return Suggestion("none", None, primary, classes)


class WanAdaptation:
    """The hook's object: feeds the rules and the ladder's policy for one report."""

    def __init__(self) -> None:
        self.rules = WanRules()
        self.counts: dict[str, int] = {}
        self._last_blackout = 0

    @staticmethod
    def _report(s: Mapping[str, Any], telemetry: Mapping[str, Any] | None) -> wt.Report | None:
        if telemetry is not None:
            return wt.report_from_telemetry({**telemetry, "fresh": bool(s.get("available") and s.get("fresh"))})
        return None

    def feed(self, policy: Any, s: dict[str, Any], ctx: dict[str, Any] | None,
             telemetry: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """The ladder's `feed` with the rules' one suggestion applied as a constraint."""
        ctx = ctx or {}
        el = s.get("elapsed_ms")
        if (self.rules.reports and (policy.last_elapsed_ms is None or
                                    (isinstance(el, (int, float)) and el < policy.last_elapsed_ms))):
            self.rules = WanRules()               # a new stream session: the rules start empty
            self._last_blackout = 0
        rules = self.rules
        # a blackout re-armed since the last tick = an SSRC change or a transition (path event)
        if policy.blackout_remaining > self._last_blackout:
            rules.note_path_event()
        rules.observe_context(ctx)
        path = path_class(ctx)

        evaluated_before = policy.reports
        r = self._report(s, telemetry)
        suggestion = Suggestion("none")
        will_evaluate = (r is not None and s.get("available") and s.get("fresh")
                         and isinstance(s.get("elapsed_ms"), (int, float))
                         and s.get("elapsed_ms") != policy.last_elapsed_ms)
        if will_evaluate:
            rules.add_report(r)
            suggestion = rules.tick(int(policy.level_kbps), path, top_kbps=max(policy.ladder))

        blocked: list[dict[str, Any]] = []
        if suggestion.blocks_increase:
            original = policy._decide

            def decide(kind: str, m: dict[str, Any], elapsed: int, c: dict[str, Any], *, injected: bool = False):
                if kind == "INCREASE" and not injected:
                    blocked.append({"class": kind, "trigger": m.get("trigger")})
                    return policy._refuse(kind, "wan_no_step_up", None, dict(m, wan_rule=suggestion.rule),
                                          injected=False, state=ab.HOLD_DOWN)
                return original(kind, m, elapsed, c, injected=injected)

            policy._decide = decide
            try:
                events = policy.feed(s, ctx)
            finally:
                del policy._decide
        else:
            events = policy.feed(s, ctx)

        decided = [e for e in events if e.get("event") in ("transition", "would_act", "refused", "hold")]
        if (suggestion.kind == "step_down" and not decided and policy.last_disposition == "evaluated"
                and policy.pending is None and policy.reports > evaluated_before
                and policy.reason != "routine_deferred_escalating"):
            m = {"trigger": "capacity_mild", "wan_rule": suggestion.rule, "wan_class": suggestion.primary}
            forced = policy._decide("ROUTINE", m, int(s["elapsed_ms"]), ctx)
            for e in forced:
                if e.get("event") in ("transition", "would_act"):
                    e["reason"] = SOURCE
                    e["trigger"] = SOURCE
                    policy.reason = SOURCE
                    if policy.last_action is not None:
                        policy.last_action["reason"] = SOURCE
                elif e.get("event") == "refused":
                    e["trigger"] = SOURCE
            events = events + forced
            decided = forced

        self._last_blackout = policy.blackout_remaining
        if suggestion.kind != "none":
            self.counts[suggestion.rule or suggestion.kind] = self.counts.get(suggestion.rule or suggestion.kind, 0) + 1
            if blocked:
                result = "blocked_increase"
            elif decided:
                d = decided[-1]
                result = d["event"] if d["event"] != "refused" else f"refused:{d.get('reason')}"
            else:
                result = "none"
            events = events + [{
                "event": "wan_suggestion", "source": SOURCE, "suggestion": suggestion.kind,
                "rule": suggestion.rule, "wan_class": suggestion.primary, "wan_classes": list(suggestion.classes),
                "path": path, "target_kbps": suggestion.target_kbps, "detail": suggestion.detail,
                "ladder_result": result, "level_kbps": policy.level_kbps, "fec": R4_NOTE,
            }]
        return events


def from_environ(environ: Mapping[str, str]) -> WanAdaptation | None:
    return WanAdaptation() if flag_on(environ) else None
