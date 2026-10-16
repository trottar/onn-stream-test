"""G1-S1: the overlay provider boundary (ROADMAP §G1).

Selected by `PRIVYHUB_OVERLAY_PROVIDER=none|tailscale`. **Absent = today**:
`reporter_from_environ` returns None, the companion constructs nothing,
starts no thread, makes no call, and its status document gains no field.
An unknown name selects the `none` provider with reason `unknown-provider`
(fail closed: no overlay).

Importable both as `overlay` (the companion puts `companion/` on sys.path)
and as `companion.overlay` (`python3 -m companion.overlay --state`).
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Mapping

from .none import NoneProvider
from .provider import (
    REASON_UNKNOWN_PROVIDER,
    OverlayProvider,
    OverlayState,
    endpoint_hash,
)
from .tailscale import TailscaleProvider

OVERLAY_PROVIDER_ENV = "PRIVYHUB_OVERLAY_PROVIDER"
PROVIDERS = ("none", "tailscale")

__all__ = [
    "OVERLAY_PROVIDER_ENV",
    "NoneProvider",
    "OverlayProvider",
    "OverlayState",
    "OverlayStatusReporter",
    "TailscaleProvider",
    "endpoint_hash",
    "reporter_from_environ",
    "select_provider",
]


def select_provider(environ: Mapping[str, str]) -> OverlayProvider | None:
    """None when the flag is absent or empty (today); else the provider."""
    raw = environ.get(OVERLAY_PROVIDER_ENV)
    if raw is None or not raw.strip():
        return None
    value = raw.strip().lower()
    if value == "none":
        return NoneProvider()
    if value == "tailscale":
        return TailscaleProvider()
    return NoneProvider(reason=REASON_UNKNOWN_PROVIDER)


class OverlayStatusReporter:
    """The status document's `overlay` object, and one log line per change."""

    def __init__(self, provider: OverlayProvider, log: Callable[[str], None] = print) -> None:
        self._provider = provider
        self._log = log
        self._last_key: tuple[Any, ...] | None = None
        self._lock = threading.Lock()

    def status_field(self) -> dict[str, Any]:
        state = self._provider.state()
        with self._lock:
            key = state.change_key()
            if key != self._last_key:
                self._last_key = key
                public = state.public()
                self._log(
                    "overlay: "
                    + " ".join(f"{k}={public[k]}" for k in (
                        "provider", "available", "connected", "path",
                        "peer_ready", "mtu", "reason", "endpoint",
                    ))
                )
        return state.public()


def reporter_from_environ(
    environ: Mapping[str, str],
    log: Callable[[str], None] = print,
) -> OverlayStatusReporter | None:
    provider = select_provider(environ)
    if provider is None:
        return None
    return OverlayStatusReporter(provider, log=log)
