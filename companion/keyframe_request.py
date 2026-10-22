"""B10: the client's keyframe request under loss -- the host's side.

`PRIVYHUB_LOSS_GUARD=1`. **Absent = today**: nothing imports this module, and a `PHK1` datagram is a bad packet (it
fails the 36-byte size check) exactly as any unknown datagram is today. Design:
`docs/memory/evidence/b10_2026-10-22/design_written_before_code.md` (hashed before this code).

The client (`debug.privyhub.loss_guard=1`) holds non-IDR frames after a dropped access unit until the next IDR and
sends one 24-byte `PHK1` request per episode on the controller socket. Here the receive loop only parses and queues;
one worker counts every request and acts on at most one per 500 ms through an encoder-control seam,
`control.force_idr() -> {"forced": bool, ...}`.

**Settled from the code (design §0.3):** the running encoder (an `ffmpeg h264_vaapi` process, `-g 15`) has no
runtime keyframe command; the only path to a fresh IDR is the actuator's encoder restart, whose 287-318-ms output gap
is longer than the <= 250-ms wait for the next natural IDR. So today's control, `NoRuntimeIdr`, forces nothing and
says why; a forced IDR (a control that can) is logged `keyframe_forced`. The heartbeat's loss-guard fields are
recorded with this flag (games/native_stream_heartbeat.py).
"""

from __future__ import annotations

import queue
import struct
import threading
import time
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_LOSS_GUARD"
MAGIC = b"PHK1"
PACKET = struct.Struct("<4sBBHIqI")         # 24 bytes, B7's layout
KIND_REQUEST = 1
MIN_INTERVAL_S = 0.5        # at most one request acted on per 500 ms
SUMMARY_S = 60.0
NO_RUNTIME_IDR = ("no runtime IDR path: the ffmpeg encoder's GOP (15 frames) is fixed at launch; the only path is "
                  "an encoder restart, whose 287-318-ms output gap exceeds the <= 250-ms wait for the next IDR")


def parse(raw: Any) -> tuple[bool, str | None]:
    if raw is None or str(raw).strip() == "":
        return False, None
    v = str(raw).strip()
    if v == "1":
        return True, None
    return False, f"ignored: {v[:32]!r} is not 1"


def decode(data: bytes) -> tuple[int, int, int] | None:
    """(seq, the client's delivered access units, drops) or None."""
    if len(data) != PACKET.size or data[:4] != MAGIC:
        return None
    _m, kind, _flags, _r, seq, delivered, drops = PACKET.unpack(data)
    if kind != KIND_REQUEST:
        return None
    return seq, delivered, drops


class NoRuntimeIdr:
    """Today's encoder control: it cannot force an IDR without a restart, and a restart costs more than it saves."""

    def force_idr(self) -> dict[str, Any]:
        return {"forced": False, "reason": NO_RUNTIME_IDR}


class KeyframeRequests:
    def __init__(self, recovery: Any, control: Any = None, clock: Callable[[], float] = time.monotonic,
                 threaded: bool = True):
        self.recovery = recovery
        self.control = control if control is not None else NoRuntimeIdr()
        self._clock = clock
        self._q: "queue.SimpleQueue[tuple]" = queue.SimpleQueue()
        self.received = 0
        self.acted = 0
        self.rate_limited = 0
        self.forced = 0
        self.unforced = 0
        self._last_acted: float | None = None
        self._last_summary = clock()
        self._summarized = (0, 0, 0, 0, 0)
        self._reason: str | None = None
        if threaded:
            threading.Thread(target=self._run, name="PrivyHub-Keyframe-Request", daemon=True).start()

    # --- the receive loop (never blocks) -------------------------------------------------------------------------

    def on_datagram(self, data: bytes, now: float) -> bool:
        ev = decode(data)
        if ev is None:
            return False
        self._q.put((ev, now))
        return True

    # --- the worker -----------------------------------------------------------------------------------------------

    def _run(self) -> None:
        while True:
            try:
                item = self._q.get(timeout=1.0)
            except queue.Empty:
                item = None
            try:
                if item is not None:
                    self.handle(*item)
                self.maybe_summary(self._clock())
            except Exception:
                pass                                   # the request must never take the worker down

    def handle(self, ev: tuple[int, int, int], rx: float) -> None:
        seq, delivered, drops = ev
        self.received += 1
        if self._last_acted is not None and rx - self._last_acted < MIN_INTERVAL_S:
            self.rate_limited += 1
            return
        self._last_acted = rx
        self.acted += 1
        try:
            result = self.control.force_idr() or {}
        except Exception as exc:
            result = {"forced": False, "reason": f"{type(exc).__name__}: {exc}"}
        if result.get("forced"):
            self.forced += 1
            self.recovery._log("keyframe_forced", client_seq=seq, client_delivered_aus=delivered, client_drops=drops,
                               request_to_forced_ms=round((self._clock() - rx) * 1000.0, 1),
                               via=result.get("via"))
        else:
            self.unforced += 1
            self._reason = str(result.get("reason") or "")[:240] or None

    def counts(self) -> tuple[int, int, int, int, int]:
        return self.received, self.acted, self.rate_limited, self.forced, self.unforced

    def maybe_summary(self, now: float) -> None:
        if now - self._last_summary < SUMMARY_S:
            return
        self._last_summary = now
        c = self.counts()
        if c == self._summarized:
            return
        self._summarized = c
        self.recovery._log("keyframe_requests", received=c[0], acted=c[1], rate_limited=c[2], forced=c[3],
                           unforced=c[4], min_interval_ms=int(MIN_INTERVAL_S * 1000), reason=self._reason)


def wire(recovery: Any, controller: Any, environ: Mapping[str, str], control: Any = None) -> KeyframeRequests | None:
    """The plugin's one call: parse, one config row, the requests on the bridge."""
    on, why = parse(environ.get(FLAG_ENV))
    if not on:
        if why:
            recovery._log("loss_guard_config", ignored=True, reason=why)
        return None
    k = KeyframeRequests(recovery, control)
    controller.set_keyframe_request(k)
    recovery._log("loss_guard_config", ignored=False, min_interval_ms=int(MIN_INTERVAL_S * 1000),
                  control=type(k.control).__name__, reason=(NO_RUNTIME_IDR if isinstance(k.control, NoRuntimeIdr)
                                                            else None))
    return k
