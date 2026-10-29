"""G8-S2: the start rung -- the rung a stream starts at, instead of 7000.

`PRIVYHUB_START_RUNG=<floor|cap|kbps>`. **Absent (or empty) = today**: nothing
imports this module; every stream starts at the profile's 7000 with the same
argv. The design is
`docs/memory/evidence/g8_s2_2026-10-17/design_written_before_code.md` (hashed
before this code).

- The active list, per start, from that start's client target: G5-S3's remote
  list (4000-7000) when `PRIVYHUB_REMOTE_LADDER=1` is in force and the target is
  overlay-class (G3's overlay test, as G5-S3 classifies it); else the ladder's
  validated list (5000-7000).
- `floor` -> the active list's lowest rung; `cap` -> G5-S4's cap where it applies
  (active, remote), else `floor`; `<kbps>` -> that rung if in the active list,
  else `floor` (logged once); anything else -> ignored, today's 7000 (logged once).
- The climb is the ladder's own increase rule; nothing in the ladder changes.
- Recorded on the session's first `sample` row after each start (`start_rung`:
  the rung, its source, the request, the active list, the path class).
"""

from __future__ import annotations

import os
import sys
import threading
from typing import Any, Mapping

FLAG_ENV = "PRIVYHUB_START_RUNG"
REFERENCE_KBPS = 7000
LAN_LIST = (5000, 5500, 6000, 7000)               # the ladder's validated list (adaptive_bitrate.LADDER_KBPS)
REMOTE_LIST = (4000, 5000, 5500, 6000, 7000)      # G5-S3's remote list (remote_ladder.REMOTE_LADDER_KBPS)


def parse(raw: Any) -> tuple[str, Any]:
    """(kind, value): floor | cap | kbps | invalid."""
    text = str(raw or "").strip().lower()
    if text in ("floor", "cap"):
        return text, text
    if text.isdigit():
        return "kbps", int(text)
    return "invalid", "invalid"


class StartRung:
    def __init__(self, raw: Any, log: Any = print) -> None:
        self.kind, self.value = parse(raw)
        self._log = log
        self._logged: set[str] = set()
        self._lock = threading.Lock()
        self.pending: dict[str, Any] | None = None
        self.last: dict[str, Any] | None = None
        self.starts = 0

    def _once(self, key: str, text: str) -> None:
        if key not in self._logged:
            self._logged.add(key)
            try:
                self._log(f"PrivyHub start rung ({FLAG_ENV}): {text}")
            except Exception:
                pass

    # -- the class and the lists (read from G5-S3 / G5-S4's shared objects, never guessed) --
    @staticmethod
    def _ladder_module() -> Any:
        return sys.modules.get("adaptive_bitrate_live")

    def _remote(self, target: Any) -> bool:
        live = self._ladder_module()
        if live is None or getattr(live, "REMOTE_LADDER", None) is None:
            return False
        import remote_ladder   # G5-S3's flag is on, so G5-S3's module is already loaded
        return remote_ladder.routing_evidence_of(target) == remote_ladder.EVIDENCE_OVERLAY

    def _cap(self, remote: bool) -> int | None:
        cap = getattr(self._ladder_module(), "REMOTE_CAP", None)
        if remote and cap is not None and getattr(cap, "active", False):
            return int(cap.cap_kbps)
        return None

    # -- the choice -------------------------------------------------------------
    def choose(self, target: Any) -> dict[str, Any]:
        """At a stream start: the rung, its source, the active list. Never raises."""
        try:
            remote = self._remote(target)
        except Exception:
            remote = False
        active = REMOTE_LIST if remote else LAN_LIST
        if self.kind == "floor":
            kbps, source = active[0], "floor"
        elif self.kind == "cap":
            cap = self._cap(remote)
            kbps, source = (cap, "cap") if cap else (active[0], "cap→floor")
            if not cap:
                self._once("cap", "no G5-S4 cap applies to this start; the floor is used")
        elif self.kind == "kbps" and self.value in active:
            kbps, source = int(self.value), "value"
        elif self.kind == "kbps":
            kbps, source = active[0], "value→floor"
            self._once(f"value:{self.value}:{remote}", f"{self.value} is not a rung of the active list "
                                                      f"{list(active)}; the floor is used")
        else:
            kbps, source = REFERENCE_KBPS, "invalid→today"
            self._once("invalid", "not floor, cap or a rung; ignored (the stream starts at 7000 as today)")
        rec = {"kbps": int(kbps), "source": source, "requested": self.value, "active_list": list(active),
               "path_class": "remote" if remote else "lan"}
        with self._lock:
            self.last = rec
            self.pending = dict(rec)
            self.starts += 1
        return rec

    def encoder_kwargs(self, target: Any) -> dict[str, Any]:
        """The first-target argv's kwargs: none for 7000 (today's call), the rung's own otherwise."""
        rec = self.choose(target)
        if rec["kbps"] == REFERENCE_KBPS:
            return {}
        return {"bitrate_kbps": rec["kbps"], "max_bitrate_kbps": rec["kbps"]}

    # -- the record ---------------------------------------------------------------
    def annotate(self, row: dict[str, Any]) -> dict[str, Any]:
        """The session's first `sample` row after a start carries `start_rung`; every other row as today."""
        try:
            if row.get("event") != "sample":
                return row
            with self._lock:
                rec, self.pending = self.pending, None
            if rec is None:
                return row
            out = dict(row)
            out["start_rung"] = rec
            return out
        except Exception:
            return row


_SHARED: StartRung | None = None
_SHARED_LOCK = threading.Lock()


def shared_from_environ(environ: Mapping[str, str]) -> StartRung | None:
    """The one instance the two hooks share; None when the flag is absent or empty."""
    global _SHARED
    raw = environ.get(FLAG_ENV)
    if raw is None or str(raw).strip() == "":
        return None
    with _SHARED_LOCK:
        if _SHARED is None:
            _SHARED = StartRung(raw)
        return _SHARED


def from_environ_fresh(environ: Mapping[str, str] = os.environ, log: Any = print) -> StartRung | None:
    """A new instance (tests and harnesses)."""
    raw = environ.get(FLAG_ENV)
    if raw is None or str(raw).strip() == "":
        return None
    return StartRung(raw, log=log)
