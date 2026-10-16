"""G1-S1: the `tailscale` overlay provider (ROADMAP §G1's first candidate).

Reads `tailscale status --json` (and `tailscale netcheck --format=json` while
the backend is Running) **only if the binary is installed**. It never
installs Tailscale, never runs `tailscale up` / `down` / `set`, and never
changes the host. With no binary the state is "unavailable", reason
`binary-absent`.

Results are cached for `CACHE_S` so a status poll does not spawn a process
every time. The overlay address stays opaque inside `OverlayState.endpoint`;
the diagnostics keep only booleans and enum values, never raw output.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from .provider import (
    PATH_DIRECT,
    PATH_NO_PEER,
    PATH_NONE,
    PATH_RELAYED,
    REASON_BINARY_ABSENT,
    REASON_ERROR,
    REASON_NEEDS_LOGIN,
    REASON_RUNNING,
    REASON_STARTING,
    REASON_STOPPED,
    OverlayProvider,
    OverlayState,
)

Runner = Callable[[list[str]], tuple[int, str]]

BACKEND_REASON = {
    "Running": REASON_RUNNING,
    "Stopped": REASON_STOPPED,
    "NeedsLogin": REASON_NEEDS_LOGIN,
    "NeedsMachineAuth": REASON_NEEDS_LOGIN,
    "Starting": REASON_STARTING,
    "NoState": REASON_STARTING,
}

# Read-only subcommands; nothing else is ever run.
STATUS_ARGV = ["status", "--json"]
NETCHECK_ARGV = ["netcheck", "--format=json"]


def _run(argv: list[str]) -> tuple[int, str]:
    try:
        cp = subprocess.run(argv, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return cp.returncode, cp.stdout


def _interface_mtu(name: str = "tailscale0") -> int | None:
    try:
        return int((Path("/sys/class/net") / name / "mtu").read_text().strip())
    except (OSError, ValueError):
        return None


class TailscaleProvider(OverlayProvider):
    name = "tailscale"
    CACHE_S = 10.0

    def __init__(
        self,
        which: Callable[[str], str | None] = shutil.which,
        runner: Runner = _run,
        mtu_reader: Callable[[], int | None] = _interface_mtu,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._which = which
        self._runner = runner
        self._mtu_reader = mtu_reader
        self._clock = clock
        self._cached: OverlayState | None = None
        self._cached_at = 0.0

    def state(self) -> OverlayState:
        now = self._clock()
        if self._cached is not None and now - self._cached_at < self.CACHE_S:
            return self._cached
        try:
            state = self._read()
        except Exception:  # the contract: state() never raises
            state = self._unavailable(REASON_ERROR, {"read": "exception"})
        self._cached, self._cached_at = state, now
        return state

    def _unavailable(self, reason: str, diagnostics: dict[str, Any] | None = None) -> OverlayState:
        return OverlayState(
            provider=self.name, available=False, connected=False, path=PATH_NONE,
            peer_ready=None, mtu=None, reason=reason, diagnostics=diagnostics or {},
        )

    def _read(self) -> OverlayState:
        binary = self._which("tailscale")
        if not binary:
            return self._unavailable(REASON_BINARY_ABSENT)

        rc, out = self._runner([binary, *STATUS_ARGV])
        try:
            status = json.loads(out) if out.strip() else None
        except ValueError:
            status = None
        if not isinstance(status, dict):
            # e.g. tailscaled not running: the CLI exits non-zero with text.
            return self._unavailable(REASON_ERROR, {"status_rc": rc, "status_json": False})

        backend = str(status.get("BackendState") or "")
        reason = BACKEND_REASON.get(backend, REASON_ERROR)
        diagnostics: dict[str, Any] = {"status_rc": rc, "backend_state": backend or None}

        connected = reason == REASON_RUNNING
        endpoint = None
        path, peer_ready, mtu = PATH_NONE, None, None
        if connected:
            ips = ((status.get("Self") or {}).get("TailscaleIPs") or [])
            endpoint = str(ips[0]) if ips else None
            peers = [p for p in (status.get("Peer") or {}).values() if isinstance(p, dict)]
            online = [p for p in peers if p.get("Online")]
            peer_ready = bool(online)
            if any(p.get("CurAddr") for p in online):
                path = PATH_DIRECT
            elif any(p.get("Relay") for p in online):
                path = PATH_RELAYED
            else:
                path = PATH_NO_PEER
            diagnostics["peers_online"] = len(online)
            diagnostics["peers_direct"] = sum(1 for p in online if p.get("CurAddr"))
            mtu = self._mtu_reader()

            nrc, nout = self._runner([binary, *NETCHECK_ARGV])
            try:
                netcheck = json.loads(nout) if nout.strip() else {}
            except ValueError:
                netcheck = {}
            if isinstance(netcheck, dict):
                diagnostics["netcheck_rc"] = nrc
                diagnostics["netcheck_udp"] = netcheck.get("UDP")
                diagnostics["netcheck_mapping_varies"] = netcheck.get("MappingVariesByDestIP")

        return OverlayState(
            provider=self.name,
            available=True,
            connected=connected,
            path=path,
            peer_ready=peer_ready,
            mtu=mtu,
            reason=reason,
            endpoint=endpoint,
            diagnostics=diagnostics,
        )
