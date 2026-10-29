"""B28: `PRIVYHUB_REMOTE=1` -- one host line for the four WAN lines, each acting only on a remote-class session.

It means exactly `PRIVYHUB_REMOTE_LADDER=1`, `PRIVYHUB_START_RUNG=floor`, `PRIVYHUB_REMOTE_RUNG_CAP=7000`,
`PRIVYHUB_WAN_TELEMETRY=1` (G4-S4's four), **but per session**:
- the class at each `native-stream-start`, before the start: B23's (`link_recovery_wan`): G3's overlay address test,
  then the overlay provider's path on a daemon thread -> `lan` / `remote-direct` / `remote-relayed` / `remote-unknown`;
- **remote (any of the three):** the umbrella's own objects go into today's module globals (`adaptive_bitrate_live`'s
  `REMOTE_LADDER` / `REMOTE_CAP` / `START_RUNG`, the actuator probe's `REMOTE_LADDER`, `native_stream`'s `START_RUNG`,
  the service's `WAN_TELEMETRY`): the four exactly as G4-S4 ran them. `remote-unknown` counts as remote for the start
  rung: the rung is chosen at the spawn, before the path can be read; the overlay address alone says the onn is not on
  the hub's LAN, and the floor is the safe start (the ladder climbs from it, ~3 min a rung in G4-S4);
- **lan:** those globals back to None -- today's code path, byte for byte (the policy's ladder put back to its base if
  a remote session left 4000 in it; the telemetry's open remote session written now).
The umbrella sets no environment line, so nothing builds at import and today's hooks are untouched. An explicit
individual line wins (present, any value): its module keeps its own object for every class; the umbrella leaves it.
One `remote_config` row per session (the class, each line in force or not, why). **Absent = today**: nothing imports
this module. Design: `docs/memory/evidence/b28_2026-10-28/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import importlib
import sys
import threading
from typing import Any, Callable, Mapping

import link_recovery_wan as lrw
import remote_cap as rc
import remote_ladder as rl
import start_rung as sr

FLAG_ENV = "PRIVYHUB_REMOTE"
LADDER, START, CAP, TELEMETRY = ("PRIVYHUB_REMOTE_LADDER", "PRIVYHUB_START_RUNG", "PRIVYHUB_REMOTE_RUNG_CAP",
                                 "PRIVYHUB_WAN_TELEMETRY")
LINES = {LADDER: "1", START: "floor", CAP: "7000", TELEMETRY: "1"}     # G4-S4's four
CLASS_LAN = lrw.SET_LAN
REMOTE_CLASSES = (lrw.SET_DIRECT, lrw.SET_RELAYED, lrw.SET_UNKNOWN)
PROBE_MODULE = "diagnostics.c3_linux_actuator_probe"
SERVICE_ATTRS = ("CONTROLLER", "STREAM_TELEMETRY_STORE", "PROJECT_ROOT", "WAN_TELEMETRY")
WHY = {
    CLASS_LAN: "not an overlay address: the LAN, today's behaviour (the four not in force)",
    lrw.SET_DIRECT: "an overlay address, the provider's path direct: the four as G4-S4",
    lrw.SET_RELAYED: "an overlay address, the provider's path relayed: the four as G4-S4",
    lrw.SET_UNKNOWN: ("an overlay address, the path not known (no-peer / none / unread): the four as G4-S4; the start "
                      "rung's floor is the safe start on an unknown path"),
}


def enabled(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


def find_service() -> Any:
    """The companion's service module (run as `__main__`), once it is fully loaded; None otherwise."""
    for name in ("__main__", "privyhub_service"):
        m = sys.modules.get(name)
        if m is not None and all(hasattr(m, a) for a in SERVICE_ATTRS):
            return m
    return None


class RemoteUmbrella:
    def __init__(self, recovery: Any, environ: Mapping[str, str], controller: Any = None,
                 live: Any = None, native: Any = None, service: Callable[[], Any] = find_service,
                 probe: Callable[[], Any] | None = None,
                 is_overlay: Callable[[Any], bool] = lrw._default_is_overlay,
                 overlay_path: Callable[[], str] = lrw._default_overlay_path, threaded: bool = True) -> None:
        self.recovery = recovery
        self.controller = controller
        self.live = live if live is not None else importlib.import_module("adaptive_bitrate_live")
        self.native = native if native is not None else importlib.import_module("native_stream")
        self._service = service
        self._probe = probe if probe is not None else (lambda: importlib.import_module(PROBE_MODULE))
        self._is_overlay = is_overlay
        self._overlay_path = overlay_path
        self._threaded = threaded
        self._lock = threading.Lock()
        self.explicit = {k: str(environ[k]) for k in LINES if k in environ}
        self.implied = [k for k in LINES if k not in environ]
        self.ladder = rl.RemoteLadder() if LADDER in self.implied else None
        cap_ladder = self.ladder if LADDER in self.implied else getattr(self.live, "REMOTE_LADDER", None)
        self.cap = rc.RemoteCap(LINES[CAP], cap_ladder) if CAP in self.implied else None
        self.start = sr.StartRung(LINES[START]) if START in self.implied else None
        self.telemetry: Any = None
        self.telemetry_note = "not built yet (the first remote session builds it)"
        self._cap_row_written = False
        self._status_wrapped = False
        self.session = 0
        self.cls: str | None = None
        self.rows = 0

    # -- the record -------------------------------------------------------------------------------------------------
    def config(self) -> dict[str, Any]:
        return {"flag": f"{FLAG_ENV}=1",
                "lines": {k: (f"explicit {self.explicit[k][:32]}" if k in self.explicit else f"implied {LINES[k]}")
                          for k in LINES},
                "cap": self.cap.config_row() if self.cap is not None else None,
                "acts_on": list(REMOTE_CLASSES), "lan": "today's, byte for byte"}

    def _in_force(self, remote: bool) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k in LINES:
            if k in self.explicit:
                mod_obj = {LADDER: getattr(self.live, "REMOTE_LADDER", None), START: getattr(self.native, "START_RUNG", None),
                           CAP: getattr(self.live, "REMOTE_CAP", None),
                           TELEMETRY: getattr(self._svc(), "WAN_TELEMETRY", None)}[k]
                out[k] = {"in_force": mod_obj is not None, "how": f"explicit {self.explicit[k][:32]}"}
            elif k == TELEMETRY:
                out[k] = {"in_force": remote and self.telemetry is not None, "how": f"implied {LINES[k]}",
                          **({} if not remote or self.telemetry is not None else {"note": self.telemetry_note})}
            else:
                out[k] = {"in_force": remote, "how": f"implied {LINES[k]}"}
        return out

    def _row(self, cls: str, session: int) -> None:
        row = {"class": cls, "session": session, "lines": self._in_force(cls != CLASS_LAN), "why": WHY[cls]}
        with self._lock:
            self.rows += 1
        try:
            self.recovery._log("remote_config", **row)
        except Exception:
            pass

    def _svc(self) -> Any:
        try:
            return self._service()
        except Exception:
            return None

    # -- the session --------------------------------------------------------------------------------------------------
    def note_stream_start(self, client_ip: Any) -> str:
        """At every `native-stream-start`, before the start; never raises. Returns the class applied now."""
        try:
            with self._lock:
                self.session += 1
                session = self.session
            if not self._is_overlay(client_ip):
                self._to_lan()
                self.cls = CLASS_LAN
                self._row(CLASS_LAN, session)
                return CLASS_LAN
            self._to_remote()
            self.cls = lrw.SET_UNKNOWN
            if self._threaded:
                threading.Thread(target=self._read_path, args=(session,), name="PrivyHub-Remote-Path",
                                 daemon=True).start()
            else:
                self._read_path(session)
            return lrw.SET_UNKNOWN
        except Exception:
            return lrw.SET_UNKNOWN

    def _read_path(self, session: int) -> None:
        try:
            path = self._overlay_path()
        except Exception:
            path = "unread"
        cls = lrw.SET_DIRECT if path == "direct" else lrw.SET_RELAYED if path == "relayed" else lrw.SET_UNKNOWN
        with self._lock:
            if session == self.session:
                self.cls = cls
        self._row(cls, session)

    def _to_remote(self) -> None:
        live, native = self.live, self.native
        if self.ladder is not None:
            live.REMOTE_LADDER = self.ladder
            try:
                self._probe().REMOTE_LADDER = self.ladder
            except Exception:
                pass
        if self.cap is not None:
            live.REMOTE_CAP = self.cap
            if not self._cap_row_written and self.controller is not None and hasattr(self.controller, "_write"):
                try:
                    self.controller._write(self.cap.config_row())   # once, as at the controller's start under G4-S4
                    self._cap_row_written = True
                except Exception:
                    pass
        if self.start is not None:
            live.START_RUNG = self.start
            native.START_RUNG = self.start
        if TELEMETRY in self.implied:
            svc = self._svc()
            if svc is None:
                self.telemetry_note = "unavailable: the service module is not loaded"
            else:
                if self.telemetry is None:
                    try:
                        import wan_telemetry
                        ov = getattr(svc, "OVERLAY_STATUS", None)
                        self.telemetry = wan_telemetry.WanTelemetry(
                            svc.PROJECT_ROOT, overlay_state=(ov.status_field if ov is not None else None))
                    except Exception as exc:
                        self.telemetry_note = f"unavailable: {type(exc).__name__}"
                if self.telemetry is not None:
                    svc.WAN_TELEMETRY = self.telemetry
                    self._wrap_status(svc)

    def _to_lan(self) -> None:
        live, native = self.live, self.native
        if self.ladder is not None:
            if live.REMOTE_LADDER is self.ladder:
                live.REMOTE_LADDER = None
            probe = sys.modules.get(PROBE_MODULE)
            if probe is not None and getattr(probe, "REMOTE_LADDER", None) is self.ladder:
                probe.REMOTE_LADDER = None
            policy = getattr(self.controller, "_policy", None)
            if policy is not None and rl.REMOTE_RUNG_KBPS in tuple(getattr(policy, "ladder", ())):
                policy.ladder = tuple(k for k in policy.ladder if k != rl.REMOTE_RUNG_KBPS)
        if self.cap is not None and live.REMOTE_CAP is self.cap:
            live.REMOTE_CAP = None
        if self.start is not None:
            if live.START_RUNG is self.start:
                live.START_RUNG = None
            if native.START_RUNG is self.start:
                native.START_RUNG = None
            with self.start._lock:
                self.start.pending = None
        if self.telemetry is not None:
            svc = self._svc()
            if svc is not None and svc.WAN_TELEMETRY is self.telemetry:
                svc.WAN_TELEMETRY = None
            t = self.telemetry
            try:
                with t._lock:
                    t._close_session_locked(t._overlay())
            except Exception:
                pass

    def _wrap_status(self, svc: Any) -> None:
        """`/status`'s `wan`, as the service's own wrapper does when the line is set at import (once)."""
        if self._status_wrapped:
            return
        self._status_wrapped = True
        orig = svc.CONTROLLER.status

        def status_with_wan() -> dict[str, Any]:
            payload = orig()
            t = getattr(svc, "WAN_TELEMETRY", None)
            if t is not None:
                wan = t.status_field()
                if wan is not None:
                    payload["wan"] = wan
            return payload

        svc.CONTROLLER.status = status_with_wan


def wire(recovery: Any, environ: Mapping[str, str], controller: Any = None, **kw: Any) -> RemoteUmbrella | None:
    """The plugin's one call (after the live controller exists): the umbrella and its config row."""
    if not enabled(environ):
        return None
    u = RemoteUmbrella(recovery, environ, controller=controller, **kw)
    try:
        recovery._log("remote_umbrella_config", **u.config())
    except Exception:
        pass
    return u
