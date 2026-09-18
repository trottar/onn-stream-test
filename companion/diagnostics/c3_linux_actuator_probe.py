from __future__ import annotations

import subprocess
import time

from pathlib import Path
from typing import Any, Callable


# The Linux cycle deliberately emits the same probe schema as the Windows
# implementation so the existing loopback-only action and the existing
# tools/probe_c3_actuator_continuity.py runner work unchanged. C3.L0 recorded
# that reusing the validated evidence path matters more than a Linux-specific
# result shape.
SCHEMA = "privyhub_c3_actuator_cycle_probe_v1"
MODE = "encoder_only_restart_same_bitrate"
REFERENCE_BITRATE_KBPS = 7000

CAPTURE_BACKEND = "x11grab_window"
ENCODER_BACKEND = "h264_vaapi"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _active(section: Any) -> bool:
    return bool(_dict(section).get("active", False))


def _counter(section: Any, key: str) -> int:
    return _int(_dict(section).get(key, 0))


def _safe_log(manager: Any, message: str) -> None:
    handle = getattr(manager, "_log_handle", None)

    if handle is None:
        return

    try:
        handle.write(message.rstrip("\n") + "\n")
        handle.flush()
    except Exception:
        pass


def run_c3_linux_actuator_continuity_cycle(
    manager: Any,
    *,
    popen_factory: Callable[..., Any] = subprocess.Popen,
    perf_counter_ns: Callable[[], int] = time.perf_counter_ns,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Replace only the Linux encoder process at the unchanged reference bitrate.

    On Linux the video path is a single FFmpeg process: x11grab is an input
    format rather than a separate capture bridge. There is therefore no capture
    process to replace and no raw-video pipe to re-handshake.

    The FEC relay, process audio, the persistent controller and the managed
    RetroArch process are intentionally left running. `_stop_locked()` must not
    be called: it stops the FEC relay and session I/O.

    This is a diagnostic. It changes no bitrate, encodes no acceptance
    threshold, and implements no adaptation policy.
    """

    manager._reap_locked()

    if not manager._linux_host():
        raise RuntimeError("not_linux_host")

    if not manager._running_locked():
        raise RuntimeError("native_video_stream_not_active")

    if (
        int(manager.BITRATE_KBPS) != REFERENCE_BITRATE_KBPS
        or int(manager.MAX_BITRATE_KBPS) != REFERENCE_BITRATE_KBPS
    ):
        raise RuntimeError("reference_bitrate_not_7000")

    if (
        int(
            getattr(
                manager,
                "_active_bitrate_kbps",
                REFERENCE_BITRATE_KBPS,
            )
        )
        != REFERENCE_BITRATE_KBPS
    ):
        raise RuntimeError("active_bitrate_not_reference")

    if not manager._fec_relay.running:
        raise RuntimeError("fec_relay_not_running")

    ffmpeg = manager._find_ffmpeg()

    if ffmpeg is None:
        raise RuntimeError("ffmpeg_unavailable")

    if manager._linux_display() is None:
        raise RuntimeError("x11_display_unavailable")

    if manager._linux_xdotool() is None:
        raise RuntimeError("x11_window_tool_unavailable")

    if manager._linux_vaapi_device() is None:
        raise RuntimeError("vaapi_render_node_unavailable")

    if manager._log_handle is None:
        raise RuntimeError("native_video_log_not_open")

    if manager._client_port is None:
        raise RuntimeError("native_client_port_unavailable")

    capture_target = _dict(
        getattr(
            manager,
            "_capture_target",
            None,
        )
    )

    window_id = _int(
        capture_target.get(
            "_window_id",
            0,
        )
    )

    if window_id <= 0:
        raise RuntimeError("capture_target_window_id_unavailable")

    # Reuse the stored window identity rather than re-running discovery. The
    # narrow hypothesis is about encoder replacement cost; re-resolving the
    # window could change what is captured and confound the measurement.
    managed_pid = _int(
        capture_target.get(
            "pid",
            0,
        )
    )

    if managed_pid <= 0 or not Path(f"/proc/{managed_pid}").is_dir():
        raise RuntimeError("managed_game_process_not_active")

    session_before = manager._session_io.status()
    fec_before = manager._fec_relay.status()

    if not _active(session_before.get("audio")):
        raise RuntimeError("process_audio_not_active")

    if not _active(session_before.get("controller")):
        raise RuntimeError("controller_not_active")

    if not bool(fec_before.get("running", False)):
        raise RuntimeError("fec_relay_not_running")

    old_ffmpeg = manager._process

    if old_ffmpeg is None or old_ffmpeg.poll() is not None:
        raise RuntimeError("managed_encoder_process_not_active")

    if manager._capture_process is not None:
        raise RuntimeError("unexpected_linux_capture_process")

    # Host resource telemetry is never started on the Linux path (recorded in
    # docs/KNOWN_ISSUES.md by C3.L0), so there is nothing to stop or restart
    # here. Do not add it inside a diagnostic.

    pre_kill_rtp_packets = _counter(fec_before, "rtp_packets")

    _safe_log(
        manager,
        "C3.L1 Linux actuator continuity probe: "
        "same-bitrate encoder-only cycle begin",
    )

    cycle_started_ns = perf_counter_ns()
    replacement_ffmpeg = None
    first_rtp_resume_ms: float | None = None
    ffmpeg_spawn_ms: float | None = None

    try:
        # Clear the handle before killing so that any concurrent status() call
        # cannot observe an exited process and trigger _reap_locked ->
        # _stop_locked, which would tear down FEC and session I/O. The manager
        # lock is already held by the caller; this is belt-and-braces against
        # the reaper specifically.
        manager._process = None

        manager._kill_managed_process(old_ffmpeg)

        session_mid = manager._session_io.status()
        fec_mid = manager._fec_relay.status()

        # C3.L1R1: take the RTP baseline AFTER the old encoder is dead and
        # reaped, not from the pre-kill snapshot. Packets the old encoder sent
        # between the precondition read and the kill are already counted; using
        # the stale figure made the first poll succeed immediately and reported
        # encoder spawn time as if it were video resume time.
        #
        # A few packets may still be queued in the relay socket when the
        # baseline is taken. That residue is reported rather than papered over,
        # so a reader can challenge this measurement with raw numbers. The
        # spawn is deliberately NOT delayed to drain the queue: that would
        # lengthen the very interruption this probe measures.
        before_rtp_packets = _counter(fec_mid, "rtp_packets")
        rtp_baseline_residual_packets = max(
            0,
            before_rtp_packets - pre_kill_rtp_packets,
        )

        encoder_down_ms = (
            perf_counter_ns() - cycle_started_ns
        ) / 1_000_000.0

        replacement_ffmpeg = popen_factory(
            manager._build_linux_ffmpeg_command(
                ffmpeg=ffmpeg,
                capture_target=capture_target,
            ),
            cwd=str(manager.project_root),
            stdin=subprocess.DEVNULL,
            stdout=manager._log_handle,
            stderr=subprocess.STDOUT,
        )

        manager._process = replacement_ffmpeg

        ffmpeg_spawn_ms = (
            perf_counter_ns() - cycle_started_ns
        ) / 1_000_000.0

        rtp_deadline = monotonic() + 2.0

        while monotonic() < rtp_deadline:
            if replacement_ffmpeg.poll() is not None:
                raise RuntimeError("replacement_ffmpeg_exited")

            if (
                _counter(
                    manager._fec_relay.status(),
                    "rtp_packets",
                )
                > before_rtp_packets
            ):
                first_rtp_resume_ms = (
                    perf_counter_ns() - cycle_started_ns
                ) / 1_000_000.0
                break

            sleep(0.01)

        if first_rtp_resume_ms is None:
            raise RuntimeError("replacement_rtp_did_not_resume")

        stable_deadline = monotonic() + 0.75

        while monotonic() < stable_deadline:
            if replacement_ffmpeg.poll() is not None:
                raise RuntimeError("replacement_ffmpeg_unstable")

            sleep(0.05)

        session_after = manager._session_io.status()
        fec_after = manager._fec_relay.status()

        total_verified_ms = (
            perf_counter_ns() - cycle_started_ns
        ) / 1_000_000.0

        audio_before = _dict(session_before.get("audio"))
        audio_mid = _dict(session_mid.get("audio"))
        audio_after = _dict(session_after.get("audio"))

        controller_before = _dict(session_before.get("controller"))
        controller_mid = _dict(session_mid.get("controller"))
        controller_after = _dict(session_after.get("controller"))

        payload = {
            "schema": SCHEMA,
            "ok": True,
            "mode": MODE,
            "platform": "linux",
            "capture_backend": CAPTURE_BACKEND,
            "encoder_backend": ENCODER_BACKEND,
            "target_bitrate_kbps": REFERENCE_BITRATE_KBPS,
            "profile_id": str(manager.PROFILE.id),
            "video": {
                # Linux x11grab is an FFmpeg input format, so there is no
                # separate capture process and none is restarted.
                "capture_restarted": False,
                "capture_process_present": False,
                "encoder_restarted": True,
                "source_width": _int(
                    capture_target.get("width", 0)
                ),
                "source_height": _int(
                    capture_target.get("height", 0)
                ),
                "ffmpeg_spawn_ms": round(
                    float(ffmpeg_spawn_ms or 0.0),
                    3,
                ),
                "encoder_down_ms": round(
                    float(encoder_down_ms),
                    3,
                ),
                "first_rtp_resume_ms": round(
                    float(first_rtp_resume_ms),
                    3,
                ),
                # first_rtp_resume_ms minus ffmpeg_spawn_ms. A value at or
                # near zero means the baseline was satisfied by residue rather
                # than by new video; treat the measurement as untrustworthy and
                # read rtp_baseline_residual_packets.
                "rtp_silence_after_spawn_ms": round(
                    float(first_rtp_resume_ms)
                    - float(ffmpeg_spawn_ms or 0.0),
                    3,
                ),
                "rtp_baseline_residual_packets": int(
                    rtp_baseline_residual_packets
                ),
                "host_verified_ms": round(
                    total_verified_ms,
                    3,
                ),
            },
            "fec": {
                "restarted": False,
                "running_before": bool(
                    fec_before.get("running", False)
                ),
                "running_mid_cycle": bool(
                    fec_mid.get("running", False)
                ),
                "running_after": bool(
                    fec_after.get("running", False)
                ),
                "rtp_packets_delta": max(
                    0,
                    _counter(fec_after, "rtp_packets")
                    - before_rtp_packets,
                ),
                "send_errors_delta": max(
                    0,
                    _counter(fec_after, "send_errors")
                    - _counter(fec_before, "send_errors"),
                ),
            },
            "audio": {
                "restarted": False,
                "active_before": _active(audio_before),
                "active_mid_cycle": _active(audio_mid),
                "active_after": _active(audio_after),
                "packets_sent_delta": max(
                    0,
                    _counter(audio_after, "packets_sent")
                    - _counter(audio_before, "packets_sent"),
                ),
                "send_errors_delta": max(
                    0,
                    _counter(audio_after, "send_errors")
                    - _counter(audio_before, "send_errors"),
                ),
            },
            "controller": {
                "restarted": False,
                "active_before": _active(controller_before),
                "active_mid_cycle": _active(controller_mid),
                "active_after": _active(controller_after),
                "packets_received_delta": max(
                    0,
                    _counter(controller_after, "packets_received")
                    - _counter(controller_before, "packets_received"),
                ),
                "bad_packets_delta": max(
                    0,
                    _counter(controller_after, "bad_packets")
                    - _counter(controller_before, "bad_packets"),
                ),
            },
        }

        _safe_log(
            manager,
            "C3.L1 Linux actuator continuity probe: "
            "same-bitrate encoder-only cycle complete; "
            f"first RTP resume={payload['video']['first_rtp_resume_ms']} ms",
        )

        return payload

    except Exception:
        # Preserve game/controller/audio/FEC ownership. Remove only a partial
        # replacement encoder so normal Back/End can still exit cleanly.
        manager._kill_managed_process(replacement_ffmpeg)
        manager._process = None

        _safe_log(
            manager,
            "C3.L1 Linux actuator continuity probe: "
            "encoder-only cycle failed",
        )

        raise
