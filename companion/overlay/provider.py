"""G1-S1: the overlay provider contract (ROADMAP §G1).

A provider reports the secure overlay's state; it never configures the
overlay, never installs anything, and never decides authorization (overlay
membership is transport, not PrivyHub authority — ROADMAP §G3).

The reachable endpoint is opaque: it stays inside `OverlayState` and is
never logged or exported. `public()` replaces it with "present"/"absent"
and a short hash, and drops the provider's own diagnostics.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

# Path values.
PATH_DIRECT = "direct"
PATH_RELAYED = "relayed"
PATH_NO_PEER = "no-peer"
PATH_NONE = "none"

# Reason values: why the state is what it is.
REASON_ABSENT = "absent"                 # no overlay provider (the default)
REASON_UNKNOWN_PROVIDER = "unknown-provider"
REASON_BINARY_ABSENT = "binary-absent"
REASON_STOPPED = "stopped"
REASON_NEEDS_LOGIN = "needs-login"
REASON_STARTING = "starting"
REASON_RUNNING = "running"
REASON_ERROR = "error"


@dataclass(frozen=True)
class OverlayState:
    provider: str
    available: bool                 # the provider can be read on this host
    connected: bool                 # the overlay is up on this host
    path: str                       # direct | relayed | no-peer | none
    peer_ready: bool | None         # at least one peer online (None: unknown)
    mtu: int | None                 # the overlay interface's MTU, if known
    reason: str
    endpoint: str | None = field(default=None, repr=False)      # opaque; never exported
    diagnostics: dict[str, Any] = field(default_factory=dict, repr=False)  # provider-internal

    def public(self) -> dict[str, Any]:
        """The status-document form: no endpoint value, no diagnostics."""
        return {
            "provider": self.provider,
            "available": self.available,
            "connected": self.connected,
            "path": self.path,
            "peer_ready": self.peer_ready,
            "mtu": self.mtu,
            "reason": self.reason,
            "endpoint": "present" if self.endpoint else "absent",
            "endpoint_hash": endpoint_hash(self.endpoint),
        }

    def change_key(self) -> tuple[Any, ...]:
        """What counts as a state change for the one-line log."""
        return (self.available, self.connected, self.path, self.peer_ready, self.reason,
                endpoint_hash(self.endpoint))


def endpoint_hash(endpoint: str | None) -> str | None:
    if not endpoint:
        return None
    return hashlib.sha256(endpoint.encode("utf-8")).hexdigest()[:8]


class OverlayProvider:
    """The contract. Subclasses implement `state()`; it must not raise."""

    name = "abstract"

    def state(self) -> OverlayState:  # pragma: no cover - contract
        raise NotImplementedError
