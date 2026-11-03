"""B32: `PRIVYHUB_STEP_IN_PLACE=1` -- a ladder step changes the bitrate on the same stream: no SSRC change, one IDR.

Settled (`docs/memory/evidence/b32_2026-10-31/host/design_written_before_code.md`, hashed before this code):
ffmpeg 7.1's `h264_vaapi` takes its rate control at init only (no runtime `-b:v`; `zmq` / `sendcmd` reach filters,
not encoders; the argv runs `-nostdin`), so a new encoder process is unavoidable. A new SSRC is not: the RTP muxer
takes `-ssrc`, and the relay keeps the stream's identity.

- **`RtpSplice`**, installed on the relay *instance* (its `_handle_rtp` wrapped; `native_fec_relay.py` not edited),
  idle = pass-through byte for byte. Armed with the new encoder's SSRC, it buffers the new encoder's packets while the
  old encoder's still pass; at the old encoder's next frame end (the RTP marker) -- or after `SPLICE_BOUND_S` -- it
  forwards the buffered packets rewritten onto the old stream (its SSRC, the sequence +1, the timestamp + one frame)
  and from then on drops the old encoder's packets and rewrites the new one's. The new encoder's first frame is its
  IDR: the onn gets one IDR and no SSRC change, no sequence gap. Any other SSRC (a full or recovery restart) drops the
  mapping: pass-through, today's SSRC change.
- **`run_in_place_transition`** (under the stream lock, from `NativeStreamManager.adaptive_level_transition`): the
  new encoder spawned at the target before the old one is killed, the splice awaited (<= 2 s), the old killed, today's
  0.75 s stability window. No splice in 2 s: the new one killed, today's restart (`in_place: false`).

Absent = today: nothing imports this module.
"""

from __future__ import annotations

import random
import subprocess
import threading
import time
from typing import Any, Callable

FLAG_ENV = "PRIVYHUB_STEP_IN_PLACE"
MODE = "validated_ladder_in_place"
SPLICE_BOUND_S = 0.120          # the longest the new encoder's first frame waits for the old one's frame end
SPLICE_WAIT_S = 2.0             # today's wait for the replacement's first RTP
STABLE_S = 0.75                 # today's stability window
RTP_CLOCK_HZ = 90000


def enabled(environ: Any) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


class RtpSplice:
    def __init__(self, fps: int = 60, clock: Callable[[], float] = time.monotonic) -> None:
        self.frame_ticks = max(1, RTP_CLOCK_HZ // max(1, int(fps)))
        self._clock = clock
        self._lock = threading.Lock()
        self._splice_event = threading.Event()
        # the stream now being forwarded: its input SSRC and the rewrite onto the output identity
        self.in_ssrc: int | None = None
        self.out_ssrc: int | None = None
        self.seq_off = 0
        self.ts_off = 0
        self.last_out_seq: int | None = None
        self.last_out_ts: int | None = None
        self.last_marker = True
        self.last_forward_at: float | None = None
        # a pending splice
        self.pending: int | None = None
        self.buffer: list[bytes] = []
        self.first_pending_at: float | None = None
        self.retired: set[int] = set()
        # counters
        self.splices = 0
        self.rewritten = 0
        self.dropped_old = 0
        self.identity_resets = 0
        self.last_splice: dict[str, Any] | None = None

    # -- the transition's side ----------------------------------------------------------------------------------------
    def arm(self, new_ssrc: int) -> None:
        with self._lock:
            self.pending = int(new_ssrc) & 0xFFFFFFFF
            self.buffer = []
            self.first_pending_at = None
            self._splice_event.clear()

    def disarm(self) -> None:
        with self._lock:
            if self.pending is not None:
                self.retired.add(self.pending)   # the failed encoder's late packets never reach the onn
            self.pending = None
            self.buffer = []
            self.first_pending_at = None

    def wait(self, timeout: float) -> bool:
        return self._splice_event.wait(timeout)

    def spliced(self) -> bool:
        return self._splice_event.is_set()

    def current_input_ssrc(self) -> int | None:
        with self._lock:
            return self.in_ssrc

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {"splices": self.splices, "rewritten": self.rewritten, "dropped_old": self.dropped_old,
                    "identity_resets": self.identity_resets, "armed": self.pending is not None,
                    "mapped": bool(self.in_ssrc is not None and self.out_ssrc != self.in_ssrc),
                    "last_splice": dict(self.last_splice) if self.last_splice else None}

    # -- the relay's side (its receive thread) ------------------------------------------------------------------------
    def process(self, packet: bytes) -> list[bytes]:
        if len(packet) < 12 or (packet[0] >> 6) != 2:
            return [packet]
        ssrc = int.from_bytes(packet[8:12], "big")
        marker = bool(packet[1] & 0x80)
        with self._lock:
            now = self._clock()
            if self.pending is not None and ssrc == self.pending:
                if self.in_ssrc is None:                     # nothing forwarded yet: it simply is the stream
                    self.pending = None
                    self._adopt_locked(ssrc)
                    self._splice_event.set()
                    return [self._forward_locked(packet, marker, now)]
                if self.first_pending_at is None:
                    self.first_pending_at = now
                self.buffer.append(packet)
                if self.last_marker or now - self.first_pending_at >= SPLICE_BOUND_S:
                    return self._splice_locked(now)
                return []
            if ssrc == self.in_ssrc:
                out = [self._forward_locked(packet, marker, now)]
                if self.pending is not None and self.buffer and marker:
                    out += self._splice_locked(now)
                return out
            if ssrc in self.retired:
                self.dropped_old += 1
                return []
            # an SSRC this splice never saw: a full or recovery restart -- today's pass-through, today's SSRC change
            if self.in_ssrc is not None:
                self.identity_resets += 1
            self._adopt_locked(ssrc)
            return [self._forward_locked(packet, marker, now)]

    def _adopt_locked(self, ssrc: int) -> None:
        self.in_ssrc = self.out_ssrc = ssrc
        self.seq_off = self.ts_off = 0
        self.retired = set()

    def _forward_locked(self, packet: bytes, marker: bool, now: float) -> bytes:
        seq = int.from_bytes(packet[2:4], "big")
        ts = int.from_bytes(packet[4:8], "big")
        if self.seq_off or self.ts_off or self.out_ssrc != self.in_ssrc:
            seq = (seq + self.seq_off) & 0xFFFF
            ts = (ts + self.ts_off) & 0xFFFFFFFF
            b = bytearray(packet)
            b[2:4] = seq.to_bytes(2, "big")
            b[4:8] = ts.to_bytes(4, "big")
            b[8:12] = int(self.out_ssrc or 0).to_bytes(4, "big")
            packet = bytes(b)
            self.rewritten += 1
        self.last_out_seq, self.last_out_ts = seq, ts
        self.last_marker = marker
        self.last_forward_at = now
        return packet

    def _splice_locked(self, now: float) -> list[bytes]:
        first = self.buffer[0]
        first_seq = int.from_bytes(first[2:4], "big")
        first_ts = int.from_bytes(first[4:8], "big")
        old = self.in_ssrc
        gap_ms = None if self.last_forward_at is None else round((now - self.last_forward_at) * 1000.0, 1)
        waited_ms = None if self.first_pending_at is None else round((now - self.first_pending_at) * 1000.0, 1)
        at_frame_end = bool(self.last_marker)
        next_seq = ((self.last_out_seq if self.last_out_seq is not None else first_seq - 1) + 1) & 0xFFFF
        next_ts = ((self.last_out_ts if self.last_out_ts is not None else first_ts - self.frame_ticks)
                   + self.frame_ticks) & 0xFFFFFFFF
        self.in_ssrc = self.pending
        self.seq_off = (next_seq - first_seq) & 0xFFFF
        self.ts_off = (next_ts - first_ts) & 0xFFFFFFFF
        if old is not None:
            self.retired.add(old)
        self.pending = None
        self.first_pending_at = None
        buffered, self.buffer = self.buffer, []
        out = [self._forward_locked(p, bool(p[1] & 0x80), now) for p in buffered]
        self.splices += 1
        self.last_splice = {"gap_ms": gap_ms, "new_waited_ms": waited_ms, "at_old_frame_end": at_frame_end,
                            "buffered_packets": len(buffered)}
        self._splice_event.set()
        return out


def install(relay: Any, fps: int = 60) -> RtpSplice:
    """The relay instance's splice (installed once per relay object; idle it forwards every packet unchanged)."""
    splice = getattr(relay, "_b32_splice", None)
    if isinstance(splice, RtpSplice):
        return splice
    splice = RtpSplice(fps=fps)
    orig = type(relay)._handle_rtp.__get__(relay)

    def handle_rtp_spliced(packet: bytes) -> None:
        for p in splice.process(packet):
            orig(p)

    relay._handle_rtp = handle_rtp_spliced
    relay._b32_splice = splice
    return splice


def _with_ssrc(command: list[str], ssrc: int) -> list[str]:
    """The encoder argv with `-ssrc` before its `-f rtp` output (an output option of the RTP muxer)."""
    out = list(command)
    at = max(i for i in range(len(out) - 1) if out[i] == "-f" and out[i + 1] == "rtp")
    out[at:at] = ["-ssrc", str(int(ssrc))]
    return out


def _fresh_ssrc(avoid: set[int], rng: Callable[[], int]) -> int:
    while True:
        v = rng() & 0xFFFFFFFF
        if v and v not in avoid:
            return v


def run_in_place_transition(manager: Any, target_bitrate_kbps: int, *,
                            popen_factory: Callable[..., Any] = subprocess.Popen,
                            probe: Any = None,
                            rng: Callable[[], int] = lambda: random.getrandbits(32),
                            monotonic: Callable[[], float] = time.monotonic,
                            perf_counter_ns: Callable[[], int] = time.perf_counter_ns,
                            sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Under the stream lock. A precondition today's path would refuse -> today's path (its own error)."""
    if probe is None:
        from diagnostics import c3_linux_actuator_probe as probe
    target = int(target_bitrate_kbps)
    today = manager.diagnostic_c3_validated_bitrate_transition

    def fallback(why: str) -> dict[str, Any]:
        result = today(target)
        if isinstance(result, dict) and isinstance(result.get("video"), dict):
            result["video"]["in_place"] = False
            result["video"]["in_place_fallback"] = why
        return result

    validated = tuple(probe.LINUX_VALIDATED_ADAPTIVE_BITRATES_KBPS)
    if getattr(probe, "REMOTE_LADDER", None) is not None:   # G5-S3's + 4000, on a remote path only (as today)
        validated = validated + tuple(probe.REMOTE_LADDER.actuator_levels())
    manager._reap_locked()
    current = int(getattr(manager, "_active_bitrate_kbps", probe.REFERENCE_BITRATE_KBPS))
    relay = getattr(manager, "_fec_relay", None)
    old = getattr(manager, "_process", None)
    if (target not in validated or current not in validated or target == current
            or not manager._linux_host() or not manager._running_locked()
            or int(manager.BITRATE_KBPS) != probe.REFERENCE_BITRATE_KBPS
            or int(manager.MAX_BITRATE_KBPS) != probe.REFERENCE_BITRATE_KBPS
            or relay is None or not relay.running or old is None or old.poll() is not None
            or getattr(manager, "_log_handle", None) is None):
        return today(target)                                    # today's refusal or today's restart, unchanged
    ffmpeg = manager._find_ffmpeg()
    capture_target = dict(getattr(manager, "_capture_target", None) or {})
    if ffmpeg is None or int(capture_target.get("_window_id", 0) or 0) <= 0:
        return today(target)

    splice = install(relay, fps=int(getattr(manager, "FPS", 60) or 60))
    avoid = {x for x in (splice.current_input_ssrc(), splice.out_ssrc) if x is not None}
    new_ssrc = _fresh_ssrc(avoid, rng)
    command = _with_ssrc(manager._build_linux_ffmpeg_command(
        ffmpeg=ffmpeg, capture_target=capture_target, bitrate_kbps=target, max_bitrate_kbps=target), new_ssrc)
    _log(manager, f"B32 in-place step: {current} -> {target} kbps, a new encoder on the same stream begin")
    started_ns = perf_counter_ns()
    splice.arm(new_ssrc)
    try:
        new = popen_factory(command, cwd=str(manager.project_root), stdin=subprocess.DEVNULL,
                            stdout=manager._log_handle, stderr=subprocess.STDOUT)
    except Exception:
        splice.disarm()
        raise
    spawn_ms = (perf_counter_ns() - started_ns) / 1e6
    deadline = monotonic() + SPLICE_WAIT_S
    why = None
    while not splice.spliced():
        if new.poll() is not None:
            why = "replacement_ffmpeg_exited"
            break
        if monotonic() >= deadline:
            why = "replacement_rtp_did_not_splice"
            break
        sleep(0.01)
    if why is not None:
        splice.disarm()
        manager._kill_managed_process(new)
        _log(manager, f"B32 in-place step: {why}; today's restart")
        return fallback(why)
    resume_ms = (perf_counter_ns() - started_ns) / 1e6
    overlap_ms = resume_ms
    try:
        manager._process = new
        manager._kill_managed_process(old)
        stable = monotonic() + STABLE_S
        while monotonic() < stable:
            if new.poll() is not None:
                raise RuntimeError("replacement_ffmpeg_unstable")
            sleep(0.05)
        manager._active_bitrate_kbps = target
    except Exception:
        manager._kill_managed_process(new)
        manager._process = None
        manager._active_bitrate_kbps = current
        _log(manager, f"B32 in-place step: {current} -> {target} kbps failed")
        raise
    st = splice.status()
    last = st.get("last_splice") or {}
    payload = {
        "schema": probe.BIDIRECTIONAL_SCHEMA, "ok": True, "mode": MODE, "platform": "linux",
        "capture_backend": probe.CAPTURE_BACKEND, "encoder_backend": probe.ENCODER_BACKEND,
        "reference_bitrate_kbps": probe.REFERENCE_BITRATE_KBPS, "from_bitrate_kbps": current,
        "target_bitrate_kbps": target, "profile_id": str(getattr(getattr(manager, "PROFILE", None), "id", "")),
        "video": {"capture_restarted": False, "encoder_restarted": True, "in_place": True, "ssrc_unchanged": True,
                  "idr_frames": 1, "ffmpeg_spawn_ms": round(spawn_ms, 3), "first_rtp_resume_ms": round(resume_ms, 3),
                  "rtp_silence_after_spawn_ms": 0.0, "splice_gap_ms": last.get("gap_ms"),
                  "splice_at_old_frame_end": last.get("at_old_frame_end"), "overlap_ms": round(overlap_ms, 3),
                  "host_verified_ms": round((perf_counter_ns() - started_ns) / 1e6, 3)},
        "fec": {"restarted": False, "running_after": bool(relay.running)},
        "splice": {k: st[k] for k in ("splices", "rewritten", "dropped_old", "identity_resets")},
    }
    _log(manager, f"B32 in-place step: {target} kbps active on the same stream; splice gap "
                  f"{payload['video']['splice_gap_ms']} ms")
    return payload


def _log(manager: Any, message: str) -> None:
    """Into the encoder's log, as the actuator probe's `_safe_log` writes."""
    handle = getattr(manager, "_log_handle", None)
    if handle is None:
        return
    try:
        handle.write(message.rstrip("\n") + "\n")
        handle.flush()
    except Exception:
        pass
