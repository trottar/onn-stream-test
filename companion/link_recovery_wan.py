"""B23: `PRIVYHUB_LINK_RECOVERY_WAN=1` -- the stack's hold H and stall threshold per path class, from WAN-R1's numbers.

WAN-R1 (`docs/memory/evidence/WAN_R1_OFFSITE_GAP_DISTRIBUTION_2026-10-24.md` §3): on the overlay's direct path, 113 min
of off-site play held 0 non-drop uplink silences >= 250 ms and 0 output gaps >= 400 ms. Any H >= 250 and any stall
>= 200 keep <= 1 false fire / 10 min. The relayed path had 0.5 min (not answerable). So, per session at the stream's
start:
- `lan` (the client's address is not the overlay's): the values as wired (H 950 with B6, the stall 400 with B9);
- `remote-direct` (an overlay address, the overlay provider's path `direct`): **H 450, stall 200**. H is WAN-R1's 250
  clamped to 450 so B9 / B12's silence save stays at 400 (`rewind_cores.parse_state_at`: min(400, H - 50)), 50 ms
  before the hold, as benched;
- `remote-relayed` / `remote-unknown` (relayed, no-peer, none, the provider absent or not yet read): as wired.
The path class: G5-S3's `remote_ladder.routing_evidence_of` (G3's overlay address test; only the class is kept) and
the overlay provider's `state().path`, read on a daemon thread (it spawns `tailscale status`), never in the request.
Applied to B2's detector (`hold_s`, B6's `Tuning.hold_ms`) and B7's `StallSignal.threshold_ms`, whichever is wired.
Addendum 1 (`design_addendum_1.md`, after the first replay: G4-S1 run 2 went direct -> no-peer inside one session, 18
false holds at 450): the path is re-read every 10 s during a remote session, and on `remote-direct` the first hold
whose silence ends in < 3 s reverts the session to the wired values (not re-applied in that session).
**Absent = today**: nothing imports this module. Design: `docs/memory/evidence/b23_2026-10-24/design_written_before_code.md`
(hashed before this code).
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_LINK_RECOVERY_WAN"

SET_LAN, SET_DIRECT, SET_RELAYED, SET_UNKNOWN = "lan", "remote-direct", "remote-relayed", "remote-unknown"
DIRECT_HOLD_MS = 450        # WAN-R1 direct: 250 (the grid's floor), clamped: the silence save at 400 stays 50 ms before
DIRECT_STALL_MS = 200       # WAN-R1 direct: 200 (output gaps >= 200 at 0-0.1 / min)
REREAD_S = 10.0             # addendum 1: the path re-read during a remote session (the provider caches 10 s)
REAL_DROP_MS = 3000.0       # WAN-R1's rule: a silence >= 3 s is a real drop
WHY_GUARD = ("a non-drop silence >= 450 ms on the direct path: not WAN-R1's direct; as wired for the rest of the "
             "session")
WHY = {
    SET_LAN: "the LAN's, unchanged",
    SET_DIRECT: ("WAN-R1 direct (113 min: H >= 250 / stall >= 200 for <= 1 false fire / 10 min); H clamped to 450 so "
                 "the silence save stays at 400, 50 ms before the hold"),
    SET_RELAYED: "WAN-R1: relayed not answerable (0.5 min); as wired",
    SET_UNKNOWN: "no WAN-R1 class for this path (no-peer is the flapping regime) or the path not known; as wired",
}


def enabled(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


def _default_is_overlay(client_ip: Any) -> bool:
    import remote_ladder
    return remote_ladder.routing_evidence_of(client_ip) == remote_ladder.EVIDENCE_OVERLAY


def _default_overlay_path() -> str:
    """The overlay provider's path (`direct` / `relayed` / `no-peer` / `none`); `unread` without a provider."""
    import overlay
    provider = overlay.select_provider(os.environ)
    if provider is None:
        return "unread"
    return str(provider.state().path)


class WanThresholds:
    def __init__(self, recovery: Any, detector: Any, stall: Any,
                 is_overlay: Callable[[Any], bool] = _default_is_overlay,
                 overlay_path: Callable[[], str] = _default_overlay_path,
                 config_row: Callable[[], dict[str, Any]] | None = None,
                 threaded: bool = True, sleep: Callable[[float], None] = time.sleep) -> None:
        self.recovery = recovery
        self.detector = detector
        self.stall = stall
        self.lan_hold_ms = round(detector.hold_s * 1000.0) if detector is not None else None
        self.lan_stall_ms = int(stall.threshold_ms) if stall is not None else None
        self._is_overlay = is_overlay
        self._overlay_path = overlay_path
        self._config_row = config_row
        self._threaded = threaded
        self._sleep = sleep
        self._lock = threading.Lock()
        self._session = 0
        self._guard_session = 0                         # addendum 1: the session the guard reverted
        self.guard_trips = 0
        # addendum 1: B2's detector's own events, the original emit first and unchanged
        if detector is not None:
            orig = detector._emit

            def emit(ev: tuple) -> None:
                orig(ev)
                try:
                    self._on_detector_event(ev)
                except Exception:
                    pass

            detector._emit = emit
        self.in_force: dict[str, Any] = {"set": SET_LAN, "path_class": "lan", "path": "none", "why": "no session yet"}

    def values(self, which: str) -> tuple[int | None, int | None]:
        if which == SET_DIRECT:
            return (DIRECT_HOLD_MS if self.detector is not None else None,
                    DIRECT_STALL_MS if self.stall is not None else None)
        return self.lan_hold_ms, self.lan_stall_ms

    def sets(self) -> dict[str, Any]:
        return {s: {"hold_ms": self.values(s)[0], "stall_ms": self.values(s)[1], "why": WHY[s]}
                for s in (SET_LAN, SET_DIRECT, SET_RELAYED, SET_UNKNOWN)}

    def config(self) -> dict[str, Any]:
        return {"flag": f"{FLAG_ENV}=1", "lan_hold_ms": self.lan_hold_ms, "lan_stall_ms": self.lan_stall_ms,
                "sets": self.sets()}

    def _apply(self, which: str, path_class: str, path: str, session: int, why: str | None = None) -> None:
        with self._lock:
            if session != self._session:
                return                                  # a late answer for an older session
            if which == SET_DIRECT and self._guard_session == session:
                return                                  # addendum 1: the guard reverted this session
            if why is None and self.in_force.get("set") == which and self.in_force.get("path") == path \
                    and self.in_force.get("session") == session:
                return                                  # a re-read with nothing new: no row
            hold, stall = self.values(which)
            if self.detector is not None and hold is not None:
                self.detector.hold_s = hold / 1000.0
                tuning = getattr(self.detector, "tuning", None)
                if tuning is not None:
                    tuning.hold_ms = hold
            if self.stall is not None and stall is not None:
                self.stall.threshold_ms = int(stall)
            self.in_force = {"set": which, "path_class": path_class, "path": path, "hold_ms": hold,
                             "stall_ms": stall, "why": why or WHY[which], "session": session}
            row: dict[str, Any] = dict(self._config_row()) if self._config_row is not None else {}
            row["at"] = "session"
            row["wan"] = {k: v for k, v in self.in_force.items() if k != "session"}
        self.recovery._log("link_recovery_config", **row)

    def note_stream_start(self, client_ip: Any) -> str:
        """At every `native-stream-start`; never raises. Returns the set applied now."""
        try:
            with self._lock:
                self._session += 1
                session = self._session
            if not self._is_overlay(client_ip):
                self._apply(SET_LAN, "lan", "none", session)
                return SET_LAN
            self._apply(SET_UNKNOWN, "remote", "pending", session)
            if self._threaded:
                threading.Thread(target=self._read_path, args=(session,), name="PrivyHub-Wan-Path",
                                 daemon=True).start()
            else:
                self._read_path(session)
            return SET_UNKNOWN
        except Exception:
            return SET_UNKNOWN

    def _read_path(self, session: int) -> None:
        """The path now, then (threaded) every REREAD_S while this session is current (addendum 1)."""
        while True:
            self.reread_once(session)
            if not self._threaded:
                return
            self._sleep(REREAD_S)
            with self._lock:
                if session != self._session:
                    return

    def reread_once(self, session: int) -> None:
        try:
            path = self._overlay_path()
        except Exception:
            path = "unread"
        which = SET_DIRECT if path == "direct" else SET_RELAYED if path == "relayed" else SET_UNKNOWN
        try:
            self._apply(which, "remote", path, session)
        except Exception:
            pass

    def _on_detector_event(self, ev: tuple) -> None:
        """Addendum 1: on `remote-direct`, a hold released within 3 s reverts the session to the wired values."""
        if not ev or ev[0] != "release" or float(ev[1]) >= REAL_DROP_MS:
            return
        with self._lock:
            if self.in_force.get("set") != SET_DIRECT:
                return
            session = self._session
            self._guard_session = session
            self.guard_trips += 1
            path = str(self.in_force.get("path"))
        if self._threaded:   # off the controller's receive loop
            threading.Thread(target=self._apply, args=(SET_UNKNOWN, "remote", path, session, WHY_GUARD),
                             name="PrivyHub-Wan-Guard", daemon=True).start()
        else:
            self._apply(SET_UNKNOWN, "remote", path, session, WHY_GUARD)


def wire(recovery: Any, controller: Any, environ: Mapping[str, str],
         config_row: Callable[[], dict[str, Any]] | None = None) -> WanThresholds | None:
    """The plugin's one call, after every threshold's own wire (B2 / B6 / B7 / B8 / B12)."""
    detector = getattr(controller, "_input_hold", None)
    stall = getattr(recovery, "_client_stall", None)
    if detector is None and stall is None:
        recovery._log("link_recovery_wan_config", ignored=True, reason="ignored: neither the hold nor the stall signal is wired")
        return None
    w = WanThresholds(recovery, detector, stall, config_row=config_row)
    recovery._log("link_recovery_wan_config", ignored=False, **w.config())
    return w
