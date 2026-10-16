"""G1-S1: the `none` overlay provider — always absent (the default)."""

from __future__ import annotations

from .provider import PATH_NONE, REASON_ABSENT, OverlayProvider, OverlayState


class NoneProvider(OverlayProvider):
    name = "none"

    def __init__(self, reason: str = REASON_ABSENT) -> None:
        self._reason = reason

    def state(self) -> OverlayState:
        return OverlayState(
            provider=self.name,
            available=False,
            connected=False,
            path=PATH_NONE,
            peer_ready=None,
            mtu=None,
            reason=self._reason,
        )
