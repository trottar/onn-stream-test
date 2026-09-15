from __future__ import annotations

import json
import os
import subprocess
import sys
import time

from pathlib import Path
from typing import Any, Callable


SCHEMA = "privyhub_c3_fixed_bitrate_cycle_v1"
MODE = "fixed_bitrate_characterization"
REFERENCE_BITRATE_KBPS = 7000
SUPPORTED_CHARACTERIZATION_BITRATES_KBPS = (6000, 5000, 5500)


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


def _wait_for_capture_metadata(
    *,
    metadata_path: Path,
    capture_process: Any,
    monotonic: Callable[[], float],
    sleep: Callable[[float], None],
    timeout_seconds: float = 5.0,
) -> tuple[int, int]:
    deadline = monotonic() + timeout_seconds

    while monotonic() < deadline:
        if capture_process.poll() is not None:
            raise RuntimeError(
                "replacement_capture_exited_before_first_frame"
            )

        if metadata_path.is_file():
            try:
                candidate = json.loads(
                    metadata_path.read_text(
                        encoding="utf-8"
                    )
                )
                width = int(
                    candidate.get(
                        "source_width",
                        candidate.get("width", 0),
                    )
                )
                height = int(
                    candidate.get(
                        "source_height",
                        candidate.get("height", 0),
                    )
                )
                if width >= 64 and height >= 64:
                    return width, height
            except (
                OSError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ):
                pass

        sleep(0.05)

    raise RuntimeError(
        "replacement_capture_first_frame_timeout"
    )


def _run_c3_fixed_bitrate_cycle(
    manager: Any,
    *,
    target_bitrate_kbps: int,
    popen_factory: Callable[..., Any] = subprocess.Popen,
    perf_counter_ns: Callable[[], int] = time.perf_counter_ns,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Restart video at one approved characterization bitrate."""

    manager._reap_locked()

    target_bitrate_kbps = int(target_bitrate_kbps)
    if (
        target_bitrate_kbps
        not in SUPPORTED_CHARACTERIZATION_BITRATES_KBPS
        or target_bitrate_kbps >= REFERENCE_BITRATE_KBPS
    ):
        raise RuntimeError(
            "unsupported_characterization_bitrate"
        )

    if not manager._running_locked():
        raise RuntimeError(
            "native_video_stream_not_active"
        )

    if (
        int(manager.BITRATE_KBPS)
        != REFERENCE_BITRATE_KBPS
        or int(manager.MAX_BITRATE_KBPS)
        != REFERENCE_BITRATE_KBPS
    ):
        raise RuntimeError(
            "reference_profile_not_7000"
        )

    if int(
        getattr(
            manager,
            "_active_bitrate_kbps",
            REFERENCE_BITRATE_KBPS,
        )
    ) != REFERENCE_BITRATE_KBPS:
        raise RuntimeError(
            "characterization_requires_reference_start"
        )

    if not manager._fec_relay.running:
        raise RuntimeError(
            "fec_relay_not_running"
        )

    ffmpeg = manager._find_ffmpeg()
    if ffmpeg is None:
        raise RuntimeError(
            "ffmpeg_unavailable"
        )

    if not manager._wgc_ready():
        raise RuntimeError(
            "wgc_runtime_unavailable"
        )

    if manager._log_handle is None:
        raise RuntimeError(
            "native_video_log_not_open"
        )

    if manager._client_port is None:
        raise RuntimeError(
            "native_client_port_unavailable"
        )

    capture_target = _dict(
        getattr(
            manager,
            "_capture_target",
            None,
        )
    )
    hwnd = _int(
        capture_target.get(
            "_hwnd",
            0,
        )
    )
    if hwnd <= 0:
        raise RuntimeError(
            "capture_target_hwnd_unavailable"
        )

    session_before = manager._session_io.status()
    fec_before = manager._fec_relay.status()

    if not _active(
        session_before.get("audio")
    ):
        raise RuntimeError(
            "process_audio_not_active"
        )

    if not _active(
        session_before.get("controller")
    ):
        raise RuntimeError(
            "controller_not_active"
        )

    if not bool(
        fec_before.get(
            "running",
            False,
        )
    ):
        raise RuntimeError(
            "fec_relay_not_running"
        )

    old_ffmpeg = manager._process
    old_capture = manager._capture_process

    if (
        old_ffmpeg is None
        or old_ffmpeg.poll() is not None
        or old_capture is None
        or old_capture.poll() is not None
    ):
        raise RuntimeError(
            "managed_video_process_not_active"
        )

    metadata_path = (
        manager.data_dir
        / "wgc_capture_meta.json"
    )

    creationflags = (
        subprocess.CREATE_NEW_PROCESS_GROUP
        if os.name == "nt"
        else 0
    )

    environment = os.environ.copy()
    runtime = str(
        manager._wgc_runtime_dir()
    )
    existing_pythonpath = (
        environment.get(
            "PYTHONPATH",
            "",
        )
    )
    environment["PYTHONPATH"] = (
        runtime
        + (
            os.pathsep
            + existing_pythonpath
            if existing_pythonpath
            else ""
        )
    )

    bridge_command = [
        sys.executable,
        str(
            manager._wgc_bridge_path()
        ),
        "--hwnd",
        str(hwnd),
        "--meta",
        str(metadata_path),
    ]

    manager._host_telemetry.stop()

    _safe_log(
        manager,
        "C3 fixed-bitrate characterization: "
        f"7000 -> {target_bitrate_kbps} kbps video-only cycle begin",
    )

    cycle_started_ns = perf_counter_ns()
    replacement_capture = None
    replacement_ffmpeg = None
    first_rtp_resume_ms: float | None = None

    try:
        manager._kill_managed_process(
            old_ffmpeg
        )
        manager._kill_managed_process(
            old_capture
        )

        manager._process = None
        manager._capture_process = None

        session_mid = manager._session_io.status()
        fec_mid = manager._fec_relay.status()

        try:
            metadata_path.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        replacement_capture = popen_factory(
            bridge_command,
            cwd=str(
                manager.project_root
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=manager._log_handle,
            bufsize=0,
            env=environment,
            creationflags=creationflags,
        )
        manager._capture_process = (
            replacement_capture
        )

        source_width, source_height = (
            _wait_for_capture_metadata(
                metadata_path=metadata_path,
                capture_process=replacement_capture,
                monotonic=monotonic,
                sleep=sleep,
            )
        )

        updated_target = dict(
            capture_target
        )
        updated_target["width"] = (
            source_width
        )
        updated_target["height"] = (
            source_height
        )
        updated_target["backend"] = (
            "windows_graphics_capture"
        )
        manager._capture_target = (
            updated_target
        )

        capture_stdout = (
            replacement_capture.stdout
        )
        if capture_stdout is None:
            raise RuntimeError(
                "replacement_capture_pipe_missing"
            )

        replacement_ffmpeg = popen_factory(
            manager._build_ffmpeg_command(
                ffmpeg=ffmpeg,
                client_ip="127.0.0.1",
                port=int(
                    manager._client_port
                ),
                source_width=source_width,
                source_height=source_height,
                bitrate_kbps=target_bitrate_kbps,
                max_bitrate_kbps=target_bitrate_kbps,
            ),
            cwd=str(
                manager.project_root
            ),
            stdin=capture_stdout,
            stdout=manager._log_handle,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
        manager._process = (
            replacement_ffmpeg
        )

        try:
            capture_stdout.close()
        except Exception:
            pass

        before_rtp_packets = _counter(
            fec_before,
            "rtp_packets",
        )

        deadline = (
            monotonic() + 2.0
        )
        while monotonic() < deadline:
            if replacement_ffmpeg.poll() is not None:
                raise RuntimeError(
                    "replacement_ffmpeg_exited"
                )
            if replacement_capture.poll() is not None:
                raise RuntimeError(
                    "replacement_capture_exited"
                )

            current_fec = (
                manager._fec_relay.status()
            )
            if (
                _counter(
                    current_fec,
                    "rtp_packets",
                )
                > before_rtp_packets
            ):
                first_rtp_resume_ms = (
                    perf_counter_ns()
                    - cycle_started_ns
                ) / 1_000_000.0
                break

            sleep(0.01)

        if first_rtp_resume_ms is None:
            raise RuntimeError(
                "replacement_rtp_did_not_resume"
            )

        stable_deadline = (
            monotonic() + 0.75
        )
        while monotonic() < stable_deadline:
            if replacement_ffmpeg.poll() is not None:
                raise RuntimeError(
                    "replacement_ffmpeg_unstable"
                )
            if replacement_capture.poll() is not None:
                raise RuntimeError(
                    "replacement_capture_unstable"
                )
            sleep(0.05)

        manager._active_bitrate_kbps = (
            target_bitrate_kbps
        )

        try:
            manager._host_telemetry.start(
                capture_process=(
                    replacement_capture
                ),
                ffmpeg_process=(
                    replacement_ffmpeg
                ),
                metadata_path=metadata_path,
                capture_target=(
                    manager._public_capture_target(
                        updated_target
                    )
                ),
            )
        except Exception:
            pass

        session_after = (
            manager._session_io.status()
        )
        fec_after = (
            manager._fec_relay.status()
        )

        total_verified_ms = (
            perf_counter_ns()
            - cycle_started_ns
        ) / 1_000_000.0

        audio_before = _dict(
            session_before.get("audio")
        )
        audio_mid = _dict(
            session_mid.get("audio")
        )
        audio_after = _dict(
            session_after.get("audio")
        )
        controller_before = _dict(
            session_before.get("controller")
        )
        controller_mid = _dict(
            session_mid.get("controller")
        )
        controller_after = _dict(
            session_after.get("controller")
        )

        payload = {
            "schema": SCHEMA,
            "ok": True,
            "mode": MODE,
            "reference_bitrate_kbps": (
                REFERENCE_BITRATE_KBPS
            ),
            "target_bitrate_kbps": (
                target_bitrate_kbps
            ),
            "profile_id": str(
                manager.PROFILE.id
            ),
            "video": {
                "capture_restarted": True,
                "encoder_restarted": True,
                "source_width": source_width,
                "source_height": source_height,
                "first_rtp_resume_ms": round(
                    float(
                        first_rtp_resume_ms
                    ),
                    3,
                ),
                "host_verified_ms": round(
                    float(
                        total_verified_ms
                    ),
                    3,
                ),
            },
            "fec": {
                "restarted": False,
                "running_before": bool(
                    fec_before.get(
                        "running",
                        False,
                    )
                ),
                "running_mid_cycle": bool(
                    fec_mid.get(
                        "running",
                        False,
                    )
                ),
                "running_after": bool(
                    fec_after.get(
                        "running",
                        False,
                    )
                ),
                "send_errors_delta": max(
                    0,
                    _counter(
                        fec_after,
                        "send_errors",
                    )
                    - _counter(
                        fec_before,
                        "send_errors",
                    ),
                ),
            },
            "audio": {
                "restarted": False,
                "active_before": _active(
                    audio_before
                ),
                "active_mid_cycle": _active(
                    audio_mid
                ),
                "active_after": _active(
                    audio_after
                ),
                "send_errors_delta": max(
                    0,
                    _counter(
                        audio_after,
                        "send_errors",
                    )
                    - _counter(
                        audio_before,
                        "send_errors",
                    ),
                ),
            },
            "controller": {
                "restarted": False,
                "active_before": _active(
                    controller_before
                ),
                "active_mid_cycle": _active(
                    controller_mid
                ),
                "active_after": _active(
                    controller_after
                ),
                "bad_packets_delta": max(
                    0,
                    _counter(
                        controller_after,
                        "bad_packets",
                    )
                    - _counter(
                        controller_before,
                        "bad_packets",
                    ),
                ),
            },
        }

        _safe_log(
            manager,
            "C3 fixed-bitrate characterization: "
            f"{target_bitrate_kbps} kbps active; "
            f"first RTP resume={payload['video']['first_rtp_resume_ms']} ms",
        )

        return payload

    except Exception:
        try:
            manager._host_telemetry.stop()
        except Exception:
            pass

        manager._kill_managed_process(
            replacement_ffmpeg
        )
        manager._kill_managed_process(
            replacement_capture
        )

        manager._process = None
        manager._capture_process = None
        manager._active_bitrate_kbps = (
            REFERENCE_BITRATE_KBPS
        )

        _safe_log(
            manager,
            "C3 fixed-bitrate characterization: "
            f"{target_bitrate_kbps} kbps cycle failed",
        )

        raise

def run_c3_fixed_bitrate_6000_cycle(
    manager: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run the validated 6000 kbps characterization actuator cycle."""
    return _run_c3_fixed_bitrate_cycle(
        manager,
        target_bitrate_kbps=6000,
        **kwargs,
    )


def run_c3_fixed_bitrate_5000_cycle(
    manager: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run the 5000 kbps characterization actuator cycle."""
    return _run_c3_fixed_bitrate_cycle(
        manager,
        target_bitrate_kbps=5000,
        **kwargs,
    )

def run_c3_fixed_bitrate_5500_cycle(
    manager: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run the 5500 kbps characterization actuator cycle."""
    return _run_c3_fixed_bitrate_cycle(
        manager,
        target_bitrate_kbps=5500,
        **kwargs,
    )
