"""G5-S3: the remote ladder -- the session's routing class reaches the live
ladder, and on a remote path only the ladder (and its actuator) can use the
720p/4000 rung (C5-M3's, screened on transport only).

Behind `PRIVYHUB_REMOTE_LADDER=1`. **Absent = today**: nothing imports this
module; the ladder's context, its rows and the actuator's validated list are
exactly as before. The design is
`docs/memory/evidence/g5_s3_2026-10-17/design_written_before_code.md` (hashed
before this code).

One shared `RemoteLadder` per process (`shared_from_environ`), read by four
guarded hooks:

- the games plugin, at `native-stream-start`: `note_stream_start(client_ip)` --
  the class of the target the gate handed the plugin (G3-S3: the declared
  endpoint whose class matches the request's routing class), under G3's own
  overlay test. `overlay` -> path `remote`; anything else -> `lan`. Only the
  class is kept; the address is never stored or logged;
- the ladder's context builder (`LiveController._ctx`): `apply` -- the
  context's `path_class`, and the policy's ladder `(4000,) + base` on a remote
  path, `base` otherwise;
- the ladder's log (`LiveController._write`): `annotate` -- `path_class` on
  every row; a move to or from 4000 labelled `remote_rung`, its actuation
  result carrying the decision's reason / trigger / rule;
- the actuator (`c3_linux_actuator_probe`): `actuator_levels` -- `(4000,)` on
  a remote path, `()` otherwise; nothing below 4000, ever;
- G5-S2's rules (`wan_adaptation`): `floor_actuates` -- R3.2's `floor_4000`
  goes through the ladder's own `_decide` when the ladder holds 4000.
"""

from __future__ import annotations

import ipaddress
import threading
from typing import Any, Mapping

FLAG_ENV = "PRIVYHUB_REMOTE_LADDER"

PATH_LAN, PATH_REMOTE = "lan", "remote"
EVIDENCE_OVERLAY, EVIDENCE_NOT_OVERLAY = "overlay", "not_overlay"

REMOTE_RUNG_KBPS = 4000                      # C5-M3: 720p/4000, the only lower rung that passed transport
REMOTE_LADDER_KBPS = (4000, 5000, 5500, 6000, 7000)

# G3's overlay address space, built from integers (no literal), as G3-S1's and
# G5-S2's; a test asserts equality with session_identity.OVERLAY_NETWORKS.
OVERLAY_NETWORKS = (
    ipaddress.ip_network((0x64400000, 10)),
    ipaddress.ip_network((0xFD7A115CA1E0 << 80, 48)),
)

DECISION_EVENTS = ("transition", "would_act", "refused", "hold")
RESULT_EVENTS = ("transition_done", "transition_aborted", "actuator_failed")
_MEMO_MAX = 32


def flag_on(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


def routing_evidence_of(target: Any) -> str:
    """G3's overlay test (`RoutingClassifier.classify`'s overlay branch) over one address."""
    try:
        ip = ipaddress.ip_address(str(target).split("%", 1)[0])
    except ValueError:
        return EVIDENCE_NOT_OVERLAY
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    if any(ip.version == n.version and ip in n for n in OVERLAY_NETWORKS):
        return EVIDENCE_OVERLAY
    return EVIDENCE_NOT_OVERLAY


class RemoteLadder:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.routing_evidence: str | None = None    # None until the first stream start
        self.path_class = PATH_LAN                  # G5-S2's default
        self.stream_starts = 0
        self._decisions: dict[Any, dict[str, Any]] = {}

    # -- the class (the games plugin) ----------------------------------------
    def set_routing_evidence(self, evidence: str) -> str:
        with self._lock:
            self.routing_evidence = evidence
            self.path_class = PATH_REMOTE if evidence == EVIDENCE_OVERLAY else PATH_LAN
            self.stream_starts += 1
            return self.path_class

    def note_stream_start(self, target: Any) -> str | None:
        """At every `native-stream-start`; never raises."""
        try:
            return self.set_routing_evidence(routing_evidence_of(target))
        except Exception:
            return None

    # -- the ladder ------------------------------------------------------------
    def ladder_for(self, ladder: tuple[int, ...]) -> tuple[int, ...]:
        base = tuple(k for k in ladder if k != REMOTE_RUNG_KBPS)
        return (REMOTE_RUNG_KBPS,) + base if self.path_class == PATH_REMOTE else base

    def apply(self, policy: Any, ctx: dict[str, Any]) -> dict[str, Any]:
        """The context's `path_class`; the policy's ladder by class."""
        ctx["path_class"] = self.path_class
        want = self.ladder_for(tuple(policy.ladder))
        if tuple(policy.ladder) != want:
            policy.ladder = want
        return ctx

    def actuator_levels(self) -> tuple[int, ...]:
        return (REMOTE_RUNG_KBPS,) if self.path_class == PATH_REMOTE else ()

    def floor_actuates(self, suggestion: Any, policy: Any) -> bool:
        """G5-S2's `floor_4000`, through the ladder's own `_decide`, when the ladder holds 4000."""
        return (getattr(suggestion, "kind", None) == "floor_4000"
                and REMOTE_RUNG_KBPS in tuple(policy.ladder)
                and int(policy.level_kbps) > REMOTE_RUNG_KBPS)

    # -- the log ---------------------------------------------------------------
    def annotate(self, row: dict[str, Any]) -> dict[str, Any]:
        try:
            out = dict(row)
            out["path_class"] = self.path_class
            ev = out.get("event")
            if ev in DECISION_EVENTS + RESULT_EVENTS and REMOTE_RUNG_KBPS in (out.get("to_kbps"),
                                                                              out.get("from_kbps")):
                out["remote_rung"] = True
            if ev == "wan_suggestion" and out.get("suggestion") == "floor_4000":
                # G5-S2's row says "recorded only"; with this flag, on a remote path, it is actuatable.
                out["floor_actuatable"] = self.path_class == PATH_REMOTE
            cap = (out.get("measurements") or {}).get("remote_cap") if isinstance(out.get("measurements"), dict) else None
            if isinstance(cap, dict):   # G5-S4: a clamped target, hoisted
                for k, v in cap.items():
                    out.setdefault(k, v)
            seq = out.get("decision_sequence")
            if ev in ("transition", "would_act") and seq is not None:
                m = out.get("measurements") or {}
                self._decisions[seq] = {"reason": out.get("reason"), "trigger": out.get("trigger"),
                                        "wan_rule": m.get("wan_rule") if isinstance(m, dict) else None,
                                        **({"source": cap["source"], "wish_kbps": cap.get("wish_kbps"),
                                            "capped_kbps": cap.get("capped_kbps")} if isinstance(cap, dict) else {})}
                while len(self._decisions) > _MEMO_MAX:
                    del self._decisions[next(iter(self._decisions))]
            elif ev in RESULT_EVENTS and seq is not None and seq in self._decisions:
                out["decision"] = self._decisions.pop(seq)
            return out
        except Exception:
            return row

    def status(self) -> dict[str, Any]:
        return {"flag": f"{FLAG_ENV}=1", "path_class": self.path_class,
                "routing_evidence": self.routing_evidence, "stream_starts": self.stream_starts,
                "remote_ladder_kbps": list(REMOTE_LADDER_KBPS)}


_SHARED: RemoteLadder | None = None
_SHARED_LOCK = threading.Lock()


def shared_from_environ(environ: Mapping[str, str]) -> RemoteLadder | None:
    """The one instance the hooks share; None without the flag."""
    global _SHARED
    if not flag_on(environ):
        return None
    with _SHARED_LOCK:
        if _SHARED is None:
            _SHARED = RemoteLadder()
        return _SHARED
