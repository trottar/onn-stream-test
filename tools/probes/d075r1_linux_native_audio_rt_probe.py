#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import resource
import socket
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANION = PROJECT_ROOT / "companion"
if str(COMPANION) not in sys.path:
    sys.path.insert(0, str(COMPANION))

from games.emulator_manager import EmulatorManager  # noqa: E402
from native_stream import NativeStreamManager  # noqa: E402

HEADER = struct.Struct("<4sBBHII")
EXPECTED_AUDIO_BYTES = 16 + 960
RT_PRIORITY = 1


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=check,
    )


def pactl_json(*args: str) -> list[dict]:
    payload = json.loads(run(["pactl", "-f", "json", *args]).stdout)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected PulseAudio JSON shape")
    return [item for item in payload if isinstance(item, dict)]


def owned_audio_inputs(pid: int) -> list[dict]:
    result = []
    for item in pactl_json("list", "sink-inputs"):
        props = item.get("properties") or {}
        if str(props.get("application.process.id", "")).strip() == str(pid):
            result.append(item)
    return result


def ensure_temporary_rtprio_limit() -> tuple[tuple[int, int], tuple[int, int]]:
    before = resource.getrlimit(resource.RLIMIT_RTPRIO)
    process_id = os.getpid()
    result = run(
        [
            "sudo",
            "-n",
            "prlimit",
            "--pid",
            str(process_id),
            f"--rtprio={RT_PRIORITY}:{RT_PRIORITY}",
        ],
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            "Unable to grant the probe process temporary RLIMIT_RTPRIO=1. "
            "Run `sudo -v` immediately before this probe."
            + (f" Detail: {detail[:300]}" if detail else "")
        )
    after = resource.getrlimit(resource.RLIMIT_RTPRIO)
    if after[0] < RT_PRIORITY or after[1] < RT_PRIORITY:
        raise RuntimeError(
            f"Temporary RT priority limit did not take effect: {after!r}"
        )
    return before, after


def main() -> int:
    root = PROJECT_ROOT
    print("=== PRIVYHUB D-075R1 LINUX NATIVE AUDIO RT RUNTIME ===")
    print("head=", run(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip())

    before_limit, after_limit = ensure_temporary_rtprio_limit()
    print("rtprio_limit_before=", before_limit)
    print("rtprio_limit_after=", after_limit)

    data = json.loads(
        (root / "companion/games/config/emulators.json").read_text(
            encoding="utf-8"
        )
    )
    data["retroarch"]["executable"] = (
        "runtime/emulators/retroarch-nightly-20260907-linux/"
        "RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
    )
    data["retroarch"]["cores_directory"] = (
        "runtime/emulators/retroarch/cores-linux"
    )
    for system in data["systems"].values():
        if system["core"].endswith(".dll"):
            system["core"] = system["core"][:-4] + ".so"

    probe_config = Path("/tmp/privyhub_emulators_linux_d075r1_probe.json")
    probe_config.write_text(json.dumps(data, indent=2), encoding="utf-8")

    game = {
        "id": "game_snes_84cbb2d09db83cb9",
        "title": "Donkey Kong Country",
        "system": "snes",
        "system_name": "SNES",
        "relative_path": "games/snes/Donkey Kong Country (USA).sfc",
    }

    manager = EmulatorManager(root, config_path=probe_config)
    stream = NativeStreamManager(root)

    audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        audio_socket.bind(("127.0.0.1", NativeStreamManager.AUDIO_PORT))
    except OSError as exc:
        raise RuntimeError(
            "Audio UDP port is unavailable. Stop the PrivyHub companion before the probe."
        ) from exc
    audio_socket.settimeout(0.1)

    video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    video_socket.bind(("127.0.0.1", 0))
    video_socket.settimeout(0.1)
    video_port = video_socket.getsockname()[1]

    audio = {
        "packets": 0,
        "bad": 0,
        "gaps": 0,
        "nonzero": 0,
        "last_sequence": None,
    }
    video_packets = 0
    running = True

    def audio_receive() -> None:
        while running:
            try:
                packet, _ = audio_socket.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                return

            if len(packet) != EXPECTED_AUDIO_BYTES:
                audio["bad"] += 1
                continue

            magic, version, channels, sequence, _timestamp, frames = HEADER.unpack(
                packet[:16]
            )
            if (
                magic != b"PHA1"
                or version != 1
                or channels != 2
                or frames != 240
            ):
                audio["bad"] += 1
                continue

            previous = audio["last_sequence"]
            if previous is not None:
                expected = (int(previous) + 1) & 0xFFFF
                if sequence != expected:
                    audio["gaps"] += (sequence - expected) & 0xFFFF

            audio["last_sequence"] = sequence
            audio["packets"] += 1
            if any(packet[16:]):
                audio["nonzero"] += 1

    def video_receive() -> None:
        nonlocal video_packets
        while running:
            try:
                video_socket.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                return
            video_packets += 1

    audio_thread = threading.Thread(target=audio_receive, daemon=True)
    video_thread = threading.Thread(target=video_receive, daemon=True)
    audio_thread.start()
    video_thread.start()

    stream_started = False
    game_started = False
    dedicated_sink = ""
    original_sink = None
    runtime_validated = False

    try:
        manager.launch(game)
        game_started = True
        status = manager.status()
        pid = int(status["pid"])
        print("game_active=", status["active"])
        print("managed_pid_present=", pid > 0)

        deadline = time.monotonic() + 5.0
        owned = []
        while time.monotonic() < deadline:
            owned = owned_audio_inputs(pid)
            if len(owned) == 1:
                break
            time.sleep(0.05)

        print("prestream_managed_sink_input_count=", len(owned))
        if len(owned) != 1:
            raise RuntimeError(
                "Managed RetroArch PID did not have exactly one PulseAudio sink-input"
            )
        original_sink = owned[0].get("sink")

        paused = manager.pause()
        print("game_paused_before_stream=", paused.get("paused"))

        started = stream.start(
            client_ip="127.0.0.1",
            port=video_port,
            managed_process_id=pid,
        )
        stream_started = True

        audio_status = started["audio"]
        helper = audio_status["helper_status"]
        scheduler = helper.get("scheduler") or {}
        dedicated_sink = (helper.get("route") or {}).get("dedicated_sink", "")

        print("paused_audio_active=", audio_status["active"])
        print("audio_capture_backend=", audio_status["capture_backend"])
        print("audio_scheduler_ready=", scheduler.get("ready"))
        print("audio_scheduler_policy=", scheduler.get("policy"))
        print("audio_scheduler_priority=", scheduler.get("priority"))
        print("audio_scheduler_native_tid_present=", bool(scheduler.get("native_tid")))
        print("audio_scheduler_error=", scheduler.get("error", ""))

        before_resume_packets = audio["packets"]
        before_resume_nonzero = audio["nonzero"]
        before_resume_underflows = int((helper.get("send") or {}).get("underflows", 0))

        resumed = manager.resume()
        print("game_paused_after_resume=", resumed.get("paused"))

        time.sleep(5.0)

        final_status = stream.status()
        final_audio = final_status["audio"]
        final_helper = final_audio["helper_status"]
        final_send = final_helper["send"]
        intervals = final_send["intervals"]
        final_scheduler = final_helper.get("scheduler") or {}

        print("audio_active_after_5s=", final_audio["active"])
        print("audio_packets_sent=", final_audio["packets_sent"])
        print("audio_send_errors=", final_audio["send_errors"])
        print("audio_sender_underflows=", final_send["underflows"])
        print(
            "post_resume_underflow_delta=",
            int(final_send["underflows"]) - before_resume_underflows,
        )
        print("audio_reader_bytes=", final_helper["capture"]["reader_bytes"])

        print("receiver_audio_packets=", audio["packets"])
        print("receiver_bad_packets=", audio["bad"])
        print("receiver_sequence_gaps=", audio["gaps"])
        print("receiver_nonzero_packets=", audio["nonzero"])
        print("post_resume_packet_delta=", audio["packets"] - before_resume_packets)
        print(
            "post_resume_nonzero_delta=",
            audio["nonzero"] - before_resume_nonzero,
        )

        print("send_interval_count=", intervals["count"])
        print("send_interval_avg_ms=", intervals["avg_ms"])
        print("send_interval_p95_ms=", intervals["p95_ms"])
        print("send_interval_max_ms=", intervals["max_ms"])
        print("send_interval_under_2ms=", intervals["under_2ms"])
        print("send_interval_ge_8ms=", intervals["ge_8ms"])

        sender_cadence_ok = bool(
            intervals["count"] >= 900
            and float(intervals["p95_ms"]) <= 6.5
            and int(intervals["under_2ms"]) <= 5
            and int(intervals["ge_8ms"]) <= 5
        )
        scheduler_ok = bool(
            final_scheduler.get("ready")
            and final_scheduler.get("policy") == "SCHED_RR"
            and int(final_scheduler.get("priority") or 0) == RT_PRIORITY
        )
        wire_ok = bool(
            audio["packets"] >= 900
            and audio["bad"] == 0
            and audio["gaps"] == 0
            and audio["nonzero"] > 0
            and int(final_audio["send_errors"]) == 0
        )

        stopped = stream.end_game_session()
        stream_started = False
        print("stream_active_after_stop=", stopped["active"])

        time.sleep(0.2)
        restored = owned_audio_inputs(pid)
        print("poststop_managed_sink_input_count=", len(restored))
        route_restored = bool(
            len(restored) == 1
            and restored[0].get("sink") == original_sink
        )
        print("audio_route_restored=", route_restored)

        remaining_sinks = {item.get("name") for item in pactl_json("list", "sinks")}
        dedicated_removed = dedicated_sink not in remaining_sinks
        print("dedicated_sink_present_after_stop=", not dedicated_removed)

        runtime_validated = bool(
            audio_status["active"]
            and final_audio["active"]
            and scheduler_ok
            and sender_cadence_ok
            and wire_ok
            and route_restored
            and dedicated_removed
        )
        print("d075r1_runtime_validated=", runtime_validated)
    finally:
        if stream_started:
            try:
                stream.end_game_session()
            except Exception as exc:
                print("stream_cleanup_error=", type(exc).__name__)
        if game_started:
            try:
                stopped_game = manager.stop()
                print("game_stop_graceful=", stopped_game.get("graceful"))
            except Exception as exc:
                print("game_stop_error=", type(exc).__name__)

        running = False
        try:
            audio_socket.close()
        except Exception:
            pass
        try:
            video_socket.close()
        except Exception:
            pass
        audio_thread.join(timeout=1)
        video_thread.join(timeout=1)
        print("video_packets_received=", video_packets)

    return 0 if runtime_validated else 2


if __name__ == "__main__":
    raise SystemExit(main())
