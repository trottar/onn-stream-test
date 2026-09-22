from __future__ import annotations

import ipaddress
import json
import os

from collections import deque
import re
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time

from pathlib import Path
from typing import Any, Callable


class NativeSessionIOError(RuntimeError):
    pass


class NativeAudioStreamer:
    TIMING_PROBE_VERSION = "process_loopback_pair_pacer_v0.22"
    AUDIO_BUFFER_ARCHITECTURE = "windows_process_loopback_pair_pacer_v0.22"

    # PrivyHub D-075 Linux native audio backend
    LINUX_TIMING_PROBE_VERSION = "pulse_monitor_thread_rt_pacer_v0.2"
    LINUX_AUDIO_BUFFER_ARCHITECTURE = "pulse_monitor_accumulator_thread_rt_pacer_v0.2"
    LINUX_SENDER_RT_PRIORITY = 1
    LINUX_SAMPLE_RATE = 48_000
    LINUX_CHANNELS = 2
    LINUX_FRAMES_PER_PACKET = 240
    LINUX_PACKET_MS = 5
    LINUX_PAYLOAD_BYTES = 960
    LINUX_PACKET_NS = 5_000_000
    LINUX_HEADER = struct.Struct("<4sBBHII")
    LINUX_SILENCE_PAYLOAD = bytes(LINUX_PAYLOAD_BYTES)

    _ADDRESS_CANDIDATE_RE = re.compile(
        r"(?<!\d)(?:\d{1,5}\.){3}\d{1,5}(?!\d)"
    )
    _MAC_RE = re.compile(
        r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
    )
    _WINDOWS_ABSOLUTE_PATH_RE = re.compile(
        r"(?i)(?<![A-Za-z0-9_])[A-Z]:[\\/][^\r\n\t\"<>|]*"
    )

    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.project_root = project_root.resolve()
        self.runtime_dir = (
            self.project_root
            / "runtime"
            / "streaming"
            / "process_audio"
        )
        self.helper_path = (
            self.runtime_dir
            / "PrivyHubProcessAudio.exe"
        )
        self.log_dir = (
            self.project_root
            / "logs"
            / "games"
        )
        self.timing_log_dir = (
            self.log_dir
            / "audio_timing"
        )
        self.helper_log_path = (
            self.log_dir
            / "native_process_audio.log"
        )
        self.status_path = (
            self.project_root
            / "data"
            / "games"
            / "native_stream"
            / "process_audio_status.json"
        )

        self._process: subprocess.Popen[Any] | None = None
        self._log_handle = None
        self._lock = threading.RLock()

        self._target_pid: int | None = None
        self._client_ip: str | None = None
        self._client_port: int | None = None
        self._timing_path: Path | None = None
        self._last_status: dict[str, Any] = {}

        self._linux_pactl: str | None = None
        self._linux_sink_module: str | None = None
        self._linux_sink_name: str | None = None
        self._linux_sink_index: int | None = None
        self._linux_monitor_source: str | None = None
        self._linux_sink_input_index: int | None = None
        self._linux_original_sink: int | str | None = None
        self._linux_reader_thread: threading.Thread | None = None
        self._linux_sender_thread: threading.Thread | None = None
        self._linux_stop_event = threading.Event()
        self._linux_buffer_condition = threading.Condition()
        self._linux_buffer = bytearray()
        self._linux_ready = False
        self._linux_packets_sent = 0
        self._linux_send_errors = 0
        self._linux_sender_underflows = 0
        self._linux_reader_bytes = 0
        self._linux_max_buffer_bytes = 0
        self._linux_restore_errors = 0
        self._linux_send_intervals_ns: deque[int] = deque(maxlen=4096)
        self._linux_last_send_ns = 0
        self._linux_sender_native_id: int | None = None
        self._linux_sender_scheduler_ready = False
        self._linux_sender_scheduler_policy = ""
        self._linux_sender_scheduler_priority = 0
        self._linux_sender_scheduler_error = ""
        self._linux_log_path = self.log_dir / "native_pulseaudio.log"

    @staticmethod
    def _kill_process(
        process: subprocess.Popen[Any] | None,
    ) -> None:
        if (
            process is None
            or process.poll() is not None
        ):
            return

        if os.name == "nt":
            try:
                import signal

                process.send_signal(
                    signal.CTRL_BREAK_EVENT
                )
                process.wait(
                    timeout=2.0
                )
                return
            except Exception:
                subprocess.run(
                    [
                        "taskkill",
                        "/PID",
                        str(process.pid),
                        "/T",
                        "/F",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
        else:
            try:
                process.terminate()
            except Exception:
                return

        try:
            process.wait(
                timeout=2
            )
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass

    def _read_status(
        self,
    ) -> dict[str, Any]:
        if not self.status_path.is_file():
            return {}

        try:
            payload = json.loads(
                self.status_path.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(
                payload,
                dict,
            ):
                self._last_status = (
                    payload
                )
                return payload
        except Exception:
            pass

        return dict(
            self._last_status
        )

    # PrivyHub D-075 Linux native audio backend
    def _linux_run_pactl(
        self,
        *args: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        pactl = self._linux_pactl or shutil.which("pactl")

        if not pactl:
            raise NativeSessionIOError(
                "Linux native audio requires pactl."
            )

        result = subprocess.run(
            [pactl, *args],
            cwd=str(self.project_root),
            text=True,
            capture_output=True,
            check=False,
            timeout=3.0,
        )

        if check and result.returncode != 0:
            detail = result.stderr.strip()
            raise NativeSessionIOError(
                "PulseAudio command failed"
                + (f": {detail[:300]}" if detail else ".")
            )

        return result

    def _linux_pactl_json(
        self,
        *args: str,
    ) -> list[dict[str, Any]]:
        result = self._linux_run_pactl(
            "-f",
            "json",
            *args,
        )

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise NativeSessionIOError(
                "PulseAudio returned invalid JSON."
            ) from exc

        if not isinstance(payload, list):
            raise NativeSessionIOError(
                "PulseAudio JSON response had an unexpected shape."
            )

        return [
            item
            for item in payload
            if isinstance(item, dict)
        ]

    @staticmethod
    def _linux_process_id_from_sink_input(
        item: dict[str, Any],
    ) -> str:
        properties = item.get("properties")

        if not isinstance(properties, dict):
            return ""

        return str(
            properties.get(
                "application.process.id",
                "",
            )
        ).strip()

    def _linux_find_owned_sink_inputs(
        self,
        process_id: int,
    ) -> list[dict[str, Any]]:
        return [
            item
            for item in self._linux_pactl_json(
                "list",
                "sink-inputs",
            )
            if self._linux_process_id_from_sink_input(item)
            == str(process_id)
        ]

    def _linux_wait_until(
        self,
        deadline_ns: int,
    ) -> bool:
        while not self._linux_stop_event.is_set():
            remaining_ns = (
                deadline_ns
                - time.perf_counter_ns()
            )

            if remaining_ns <= 0:
                return True

            if remaining_ns > 1_500_000:
                self._linux_stop_event.wait(0.001)
            elif remaining_ns > 250_000:
                time.sleep(0)
            else:
                # Baseline 34 validated a final <=0.25 ms spin as the
                # smallest reliable way to avoid Linux scheduler catch-up
                # bursts at the existing 5 ms PHA1 cadence.
                pass

        return False

    def _linux_reader_loop(self) -> None:
        process = self._process
        stream = (
            process.stdout
            if process is not None
            else None
        )

        if stream is None:
            return

        try:
            descriptor = stream.fileno()

            while not self._linux_stop_event.is_set():
                chunk = os.read(
                    descriptor,
                    16 * 1024,
                )

                if not chunk:
                    break

                with self._linux_buffer_condition:
                    self._linux_buffer.extend(chunk)
                    self._linux_reader_bytes += len(chunk)
                    self._linux_max_buffer_bytes = max(
                        self._linux_max_buffer_bytes,
                        len(self._linux_buffer),
                    )
                    self._linux_buffer_condition.notify_all()
        except (OSError, ValueError):
            pass

    # PrivyHub D-075R1 sender-thread realtime scheduler
    def _linux_prepare_sender_scheduler(self) -> bool:
        self._linux_sender_native_id = threading.get_native_id()
        self._linux_sender_scheduler_ready = False
        self._linux_sender_scheduler_policy = ""
        self._linux_sender_scheduler_priority = 0
        self._linux_sender_scheduler_error = ""

        try:
            if not all(
                hasattr(os, name)
                for name in (
                    "SCHED_RR",
                    "sched_setscheduler",
                    "sched_getscheduler",
                    "sched_getparam",
                    "sched_param",
                )
            ):
                raise RuntimeError(
                    "required Linux scheduler APIs are unavailable"
                )

            # Linux scheduling policy is per-thread. pid=0 means the calling
            # thread, so this does not promote the companion's main thread.
            os.sched_setscheduler(
                0,
                os.SCHED_RR,
                os.sched_param(
                    self.LINUX_SENDER_RT_PRIORITY
                ),
            )
            policy = os.sched_getscheduler(0)
            priority = int(
                os.sched_getparam(0).sched_priority
            )

            if (
                policy != os.SCHED_RR
                or priority != self.LINUX_SENDER_RT_PRIORITY
            ):
                raise RuntimeError(
                    "sender thread did not retain SCHED_RR priority 1"
                )

            self._linux_sender_scheduler_policy = "SCHED_RR"
            self._linux_sender_scheduler_priority = priority
            self._linux_sender_scheduler_ready = True
            return True
        except Exception as exc:
            self._linux_sender_scheduler_error = (
                type(exc).__name__
                + ": "
                + str(exc)[:240]
            )
            return False

    def _linux_sender_loop(self) -> None:
        client_ip = self._client_ip
        client_port = self._client_port

        if client_ip is None or client_port is None:
            return

        if not self._linux_prepare_sender_scheduler():
            return

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:
            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_SNDBUF,
                64 * 1024,
            )
            sock.setblocking(False)

            sequence = 0
            sample_timestamp = 0
            deadline_ns = time.perf_counter_ns()

            while not self._linux_stop_event.is_set():
                deadline_ns += self.LINUX_PACKET_NS

                if not self._linux_wait_until(deadline_ns):
                    break

                with self._linux_buffer_condition:
                    if len(self._linux_buffer) >= self.LINUX_PAYLOAD_BYTES:
                        payload = bytes(
                            self._linux_buffer[
                                : self.LINUX_PAYLOAD_BYTES
                            ]
                        )
                        del self._linux_buffer[
                            : self.LINUX_PAYLOAD_BYTES
                        ]
                    else:
                        payload = self.LINUX_SILENCE_PAYLOAD
                        self._linux_sender_underflows += 1

                datagram = self.LINUX_HEADER.pack(
                    b"PHA1",
                    1,
                    self.LINUX_CHANNELS,
                    sequence,
                    sample_timestamp,
                    self.LINUX_FRAMES_PER_PACKET,
                ) + payload

                try:
                    sock.sendto(
                        datagram,
                        (
                            client_ip,
                            int(client_port),
                        ),
                    )
                    now_ns = time.perf_counter_ns()

                    if self._linux_last_send_ns > 0:
                        self._linux_send_intervals_ns.append(
                            now_ns
                            - self._linux_last_send_ns
                        )

                    self._linux_last_send_ns = now_ns
                    self._linux_packets_sent += 1
                except (BlockingIOError, OSError):
                    self._linux_send_errors += 1

                sequence = (
                    sequence + 1
                ) & 0xFFFF
                sample_timestamp = (
                    sample_timestamp
                    + self.LINUX_FRAMES_PER_PACKET
                ) & 0xFFFFFFFF
        finally:
            try:
                sock.close()
            except OSError:
                pass

    def _linux_interval_metrics(self) -> dict[str, Any]:
        values = list(
            self._linux_send_intervals_ns
        )

        if not values:
            return {
                "count": 0,
                "avg_ms": 0.0,
                "p95_ms": 0.0,
                "max_ms": 0.0,
                "under_2ms": 0,
                "ge_8ms": 0,
            }

        ordered = sorted(values)
        p95_index = min(
            len(ordered) - 1,
            int(
                (len(ordered) - 1)
                * 0.95
            ),
        )

        return {
            "count": len(values),
            "avg_ms": round(
                sum(values)
                / len(values)
                / 1_000_000.0,
                4,
            ),
            "p95_ms": round(
                ordered[p95_index]
                / 1_000_000.0,
                4,
            ),
            "max_ms": round(
                max(values)
                / 1_000_000.0,
                4,
            ),
            "under_2ms": sum(
                value < 2_000_000
                for value in values
            ),
            "ge_8ms": sum(
                value >= 8_000_000
                for value in values
            ),
        }

    def _linux_status_locked(self) -> dict[str, Any]:
        process_active = (
            self._process is not None
            and self._process.poll() is None
        )
        reader_active = (
            self._linux_reader_thread is not None
            and self._linux_reader_thread.is_alive()
        )
        sender_active = (
            self._linux_sender_thread is not None
            and self._linux_sender_thread.is_alive()
        )

        with self._linux_buffer_condition:
            buffered_bytes = len(
                self._linux_buffer
            )

        active = bool(
            self._linux_ready
            and process_active
            and reader_active
            and sender_active
            and self._linux_sender_scheduler_ready
            and self._linux_sink_module
            and self._linux_sink_input_index is not None
        )

        helper_status = {
            "schema": "privyhub_linux_pulseaudio_v1",
            "ready": active,
            "backend": "pulseaudio_managed_sink_monitor",
            "route": {
                "managed_sink_input": self._linux_sink_input_index,
                "dedicated_sink": self._linux_sink_name or "",
                "dedicated_sink_index": self._linux_sink_index,
            },
            "capture": {
                "reader_bytes": self._linux_reader_bytes,
                "buffered_bytes": buffered_bytes,
                "max_buffer_bytes": self._linux_max_buffer_bytes,
            },
            "scheduler": {
                "native_tid": self._linux_sender_native_id,
                "ready": self._linux_sender_scheduler_ready,
                "policy": self._linux_sender_scheduler_policy,
                "priority": self._linux_sender_scheduler_priority,
                "required_policy": "SCHED_RR",
                "required_priority": self.LINUX_SENDER_RT_PRIORITY,
                "error": self._linux_sender_scheduler_error,
            },
            "send": {
                "packets": self._linux_packets_sent,
                "errors": self._linux_send_errors,
                "underflows": self._linux_sender_underflows,
                "intervals": self._linux_interval_metrics(),
            },
            "restore_errors": self._linux_restore_errors,
        }

        return {
            "active": active,
            "device": "managed_process_audio",
            "sample_rate": self.LINUX_SAMPLE_RATE,
            "channels": self.LINUX_CHANNELS,
            "format": "pcm_s16le",
            "packet_ms": self.LINUX_PACKET_MS,
            "port": self._client_port,
            "target_pid": self._target_pid,
            "include_process_tree": False,
            "capture_backend": "pulseaudio_managed_sink_monitor",
            "helper": "FFmpeg PulseAudio monitor + thread-local SCHED_RR/1 PHA1 pacer",
            "timing_probe": self.LINUX_TIMING_PROBE_VERSION,
            "audio_buffer_architecture": self.LINUX_AUDIO_BUFFER_ARCHITECTURE,
            "packets_sent": self._linux_packets_sent,
            "send_errors": self._linux_send_errors,
            "timing_log": self._public_timing_log(),
            "helper_status": helper_status,
        }

    def _write_linux_timing_snapshot(self) -> None:
        path = self._timing_path

        if path is None:
            return

        payload = {
            "schema": "privyhub_linux_pulseaudio_timing_v1",
            "probe_version": self.LINUX_TIMING_PROBE_VERSION,
            "final": True,
            "target_pid": self._target_pid,
            "format": {
                "sample_rate": self.LINUX_SAMPLE_RATE,
                "channels": self.LINUX_CHANNELS,
                "network_sample_format": "pcm_s16le",
                "frames_per_packet": self.LINUX_FRAMES_PER_PACKET,
                "packet_ms": self.LINUX_PACKET_MS,
                "payload_bytes": self.LINUX_PAYLOAD_BYTES,
            },
            "capture_backend": "pulseaudio_managed_sink_monitor",
            "scheduler": {
                "native_tid": self._linux_sender_native_id,
                "ready": self._linux_sender_scheduler_ready,
                "policy": self._linux_sender_scheduler_policy,
                "priority": self._linux_sender_scheduler_priority,
                "required_policy": "SCHED_RR",
                "required_priority": self.LINUX_SENDER_RT_PRIORITY,
                "error": self._linux_sender_scheduler_error,
            },
            "packets_sent": self._linux_packets_sent,
            "send_errors": self._linux_send_errors,
            "sender_underflows": self._linux_sender_underflows,
            "reader_bytes": self._linux_reader_bytes,
            "max_buffer_bytes": self._linux_max_buffer_bytes,
            "send_intervals": self._linux_interval_metrics(),
            "restore_errors": self._linux_restore_errors,
        }

        try:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            temporary = path.with_suffix(
                path.suffix + ".tmp"
            )
            temporary.write_text(
                json.dumps(
                    payload,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            temporary.replace(path)
        except OSError:
            pass

    def _stop_linux_locked(self) -> None:
        had_session = bool(
            self._process is not None
            or self._linux_sink_module
            or self._linux_sink_input_index is not None
            or self._target_pid is not None
        )

        self._linux_ready = False
        self._linux_stop_event.set()

        with self._linux_buffer_condition:
            self._linux_buffer_condition.notify_all()

        sender = self._linux_sender_thread
        self._linux_sender_thread = None

        if (
            sender is not None
            and sender is not threading.current_thread()
        ):
            sender.join(timeout=1.0)

        process = self._process
        self._process = None
        self._kill_process(process)

        if process is not None and process.stdout is not None:
            try:
                process.stdout.close()
            except Exception:
                pass

        reader = self._linux_reader_thread
        self._linux_reader_thread = None

        if (
            reader is not None
            and reader is not threading.current_thread()
        ):
            reader.join(timeout=1.0)

        if (
            self._linux_sink_input_index is not None
            and self._linux_original_sink is not None
            and self._linux_pactl
        ):
            result = self._linux_run_pactl(
                "move-sink-input",
                str(self._linux_sink_input_index),
                str(self._linux_original_sink),
                check=False,
            )

            if result.returncode != 0:
                self._linux_restore_errors += 1

        if (
            self._linux_sink_module
            and self._linux_pactl
        ):
            result = self._linux_run_pactl(
                "unload-module",
                str(self._linux_sink_module),
                check=False,
            )

            if result.returncode != 0:
                self._linux_restore_errors += 1

        if had_session:
            self._write_linux_timing_snapshot()

        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass

        self._log_handle = None
        self._linux_pactl = None
        self._linux_sink_module = None
        self._linux_sink_index = None
        self._linux_monitor_source = None
        self._linux_sink_input_index = None
        self._linux_original_sink = None
        self._client_ip = None
        self._client_port = None
        self._target_pid = None
        self._linux_sender_native_id = None
        self._linux_sender_scheduler_ready = False
        self._linux_sender_scheduler_policy = ""
        self._linux_sender_scheduler_priority = 0
        self._linux_sender_scheduler_error = ""

        with self._linux_buffer_condition:
            self._linux_buffer.clear()

    def _start_linux_locked(
        self,
        ffmpeg: Path,
        client_ip: str,
        client_port: int,
        process_id: int,
    ) -> dict[str, Any]:
        if not sys.platform.startswith("linux"):
            raise NativeSessionIOError(
                "Linux native audio backend requested on a non-Linux host."
            )

        pactl = shutil.which("pactl")

        if not pactl:
            raise NativeSessionIOError(
                "Linux native audio requires pactl."
            )

        ffmpeg = Path(ffmpeg).resolve()

        if not ffmpeg.is_file():
            raise NativeSessionIOError(
                "Linux native audio requires a valid FFmpeg executable."
            )

        process_id = int(process_id)

        if (
            process_id <= 0
            or not Path(
                f"/proc/{process_id}"
            ).is_dir()
        ):
            raise NativeSessionIOError(
                "Managed RetroArch process ID is invalid or inactive."
            )

        self._linux_pactl = pactl
        self._target_pid = process_id
        self._client_ip = client_ip
        self._client_port = int(client_port)
        self._linux_stop_event.clear()
        self._linux_ready = False
        self._linux_packets_sent = 0
        self._linux_send_errors = 0
        self._linux_sender_underflows = 0
        self._linux_reader_bytes = 0
        self._linux_max_buffer_bytes = 0
        self._linux_restore_errors = 0
        self._linux_send_intervals_ns.clear()
        self._linux_last_send_ns = 0
        self._linux_sender_native_id = None
        self._linux_sender_scheduler_ready = False
        self._linux_sender_scheduler_policy = ""
        self._linux_sender_scheduler_priority = 0
        self._linux_sender_scheduler_error = ""

        with self._linux_buffer_condition:
            self._linux_buffer.clear()

        self.log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.timing_log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        stamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )
        self._timing_path = (
            self.timing_log_dir
            / f"audio_pulseaudio_{stamp}.json"
        )
        self._linux_sink_name = (
            "privyhub_native_audio_"
            + str(os.getpid())
            + "_"
            + str(process_id)
            + "_"
            + format(
                time.monotonic_ns()
                & 0x0FFFFFFF,
                "x",
            )
        )

        try:
            loaded = self._linux_run_pactl(
                "load-module",
                "module-null-sink",
                f"sink_name={self._linux_sink_name}",
                "rate=48000",
                "channels=2",
            )
            module_id = loaded.stdout.strip()

            if not module_id:
                raise NativeSessionIOError(
                    "PulseAudio did not return a module ID for the dedicated sink."
                )

            self._linux_sink_module = module_id

            sinks = self._linux_pactl_json(
                "list",
                "sinks",
            )
            matches = [
                item
                for item in sinks
                if item.get("name")
                == self._linux_sink_name
            ]

            if len(matches) != 1:
                raise NativeSessionIOError(
                    "Dedicated PulseAudio sink was not uniquely created."
                )

            sink = matches[0]
            self._linux_sink_index = int(
                sink.get("index")
            )
            self._linux_monitor_source = str(
                sink.get("monitor_source_name")
                or (
                    self._linux_sink_name
                    + ".monitor"
                )
            )

            deadline = time.monotonic() + 5.0
            owned: list[dict[str, Any]] = []

            while time.monotonic() < deadline:
                owned = self._linux_find_owned_sink_inputs(
                    process_id
                )

                if len(owned) == 1:
                    break

                if len(owned) > 1:
                    raise NativeSessionIOError(
                        "Managed RetroArch PID owns multiple PulseAudio sink-inputs; refusing ambiguous routing."
                    )

                time.sleep(0.05)

            if len(owned) != 1:
                raise NativeSessionIOError(
                    "Managed RetroArch PID did not resolve to exactly one PulseAudio sink-input."
                )

            target = owned[0]
            self._linux_sink_input_index = int(
                target.get("index")
            )
            self._linux_original_sink = target.get(
                "sink"
            )

            if self._linux_original_sink is None:
                raise NativeSessionIOError(
                    "Managed PulseAudio sink-input did not report its original sink."
                )

            self._linux_run_pactl(
                "move-sink-input",
                str(self._linux_sink_input_index),
                self._linux_sink_name,
            )

            moved = [
                item
                for item in self._linux_pactl_json(
                    "list",
                    "sink-inputs",
                )
                if int(
                    item.get(
                        "index",
                        -1,
                    )
                )
                == self._linux_sink_input_index
            ]

            if (
                len(moved) != 1
                or int(
                    moved[0].get(
                        "sink",
                        -1,
                    )
                )
                != self._linux_sink_index
            ):
                raise NativeSessionIOError(
                    "Managed PulseAudio stream did not remain on the dedicated sink."
                )

            self._log_handle = open(
                self._linux_log_path,
                "ab",
                buffering=0,
            )

            command = [
                str(ffmpeg),
                "-hide_banner",
                "-loglevel",
                "warning",
                "-nostdin",
                "-f",
                "pulse",
                "-i",
                self._linux_monitor_source,
                "-ac",
                str(self.LINUX_CHANNELS),
                "-ar",
                str(self.LINUX_SAMPLE_RATE),
                "-c:a",
                "pcm_s16le",
                "-f",
                "s16le",
                "pipe:1",
            ]

            self._process = subprocess.Popen(
                command,
                cwd=str(self.project_root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=self._log_handle,
                bufsize=0,
            )

            self._linux_reader_thread = threading.Thread(
                target=self._linux_reader_loop,
                daemon=True,
                name="PrivyHub-Linux-Audio-Reader",
            )
            self._linux_sender_thread = threading.Thread(
                target=self._linux_sender_loop,
                daemon=True,
                name="PrivyHub-Linux-Audio-PHA1",
            )
            self._linux_reader_thread.start()
            self._linux_sender_thread.start()

            startup_deadline = time.monotonic() + 1.0

            while time.monotonic() < startup_deadline:
                if (
                    self._process is None
                    or self._process.poll() is not None
                ):
                    raise NativeSessionIOError(
                        "Linux PulseAudio FFmpeg capture exited during startup."
                    )

                if (
                    self._linux_reader_thread is None
                    or not self._linux_reader_thread.is_alive()
                    or self._linux_sender_thread is None
                    or not self._linux_sender_thread.is_alive()
                ):
                    if self._linux_sender_scheduler_error:
                        raise NativeSessionIOError(
                            "Linux native-audio sender requires thread-local "
                            "SCHED_RR priority 1. Grant only the PrivyHub "
                            "service/process RLIMIT_RTPRIO=1. Scheduler error: "
                            + self._linux_sender_scheduler_error
                        )
                    raise NativeSessionIOError(
                        "Linux native-audio worker exited during startup."
                    )

                if self._linux_packets_sent >= 20:
                    self._linux_ready = True
                    return self._linux_status_locked()

                time.sleep(0.01)

            raise NativeSessionIOError(
                "Linux native-audio sender did not establish the 5 ms PHA1 cadence within one second."
            )
        except NativeSessionIOError:
            self._stop_linux_locked()
            raise
        except Exception as exc:
            self._stop_linux_locked()
            raise NativeSessionIOError(
                "Unable to start Linux native audio: "
                + type(exc).__name__
            ) from exc

    def start(
        self,
        ffmpeg: Path,
        client_ip: str,
        client_port: int,
        process_id: int,
    ) -> dict[str, Any]:
        with self._lock:
            self.stop()

            if sys.platform.startswith("linux"):
                return self._start_linux_locked(
                    ffmpeg=ffmpeg,
                    client_ip=client_ip,
                    client_port=client_port,
                    process_id=process_id,
                )

            if os.name != "nt":
                raise NativeSessionIOError(
                    "Native audio is not implemented for this host platform."
                )

            del ffmpeg

            if not self.helper_path.is_file():
                raise NativeSessionIOError(
                    "PrivyHub process-loopback audio helper is missing. "
                    "Re-apply the v0.21.1 audio probe patch."
                )

            process_id = int(
                process_id
            )

            if process_id <= 0:
                raise NativeSessionIOError(
                    "Managed RetroArch process ID is invalid."
                )

            self.timing_log_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
            self.status_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            stamp = time.strftime(
                "%Y%m%d_%H%M%S"
            )
            self._timing_path = (
                self.timing_log_dir
                / (
                    "audio_process_loopback_"
                    + stamp
                    + ".json"
                )
            )

            try:
                self.status_path.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

            self._log_handle = open(
                self.helper_log_path,
                "ab",
                buffering=0,
            )

            command = [
                str(
                    self.helper_path
                ),
                "--pid",
                str(
                    process_id
                ),
                "--client-ip",
                client_ip,
                "--port",
                str(
                    int(
                        client_port
                    )
                ),
                "--log",
                str(
                    self._timing_path
                ),
                "--status",
                str(
                    self.status_path
                ),
            ]

            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
                if os.name == "nt"
                else 0
            )

            try:
                self._process = (
                    subprocess.Popen(
                        command,
                        cwd=str(
                            self.project_root
                        ),
                        stdin=subprocess.DEVNULL,
                        stdout=self._log_handle,
                        stderr=self._log_handle,
                        creationflags=creationflags,
                    )
                )
            except Exception as exc:
                self.stop()

                raise NativeSessionIOError(
                    "Unable to start native Windows process-loopback "
                    f"audio helper: {exc}"
                ) from exc

            self._target_pid = (
                process_id
            )
            self._client_ip = (
                client_ip
            )
            self._client_port = int(
                client_port
            )
            self._last_status = {}

            deadline = (
                time.monotonic()
                + 5.0
            )

            while time.monotonic() < deadline:
                process = (
                    self._process
                )

                if (
                    process is None
                    or process.poll()
                    is not None
                ):
                    status = (
                        self._read_status()
                    )
                    detail = str(
                        status.get(
                            "error",
                            "",
                        )
                    ).strip()

                    self.stop()

                    raise NativeSessionIOError(
                        "Windows process-loopback audio helper exited "
                        "during startup."
                        + (
                            " "
                            + detail
                            if detail
                            else ""
                        )
                    )

                status = (
                    self._read_status()
                )

                if bool(
                    status.get(
                        "ready",
                        False,
                    )
                ):
                    return self.status()

                time.sleep(
                    0.05
                )

            self.stop()

            raise NativeSessionIOError(
                "Windows process-loopback audio helper did not become "
                "ready within 5 seconds."
            )

    @classmethod
    def _redact_network_text(
        cls,
        value: str,
    ) -> str:
        def replace_address(
            match: re.Match[str],
        ) -> str:
            candidate = match.group(0)

            try:
                ipaddress.ip_address(candidate)
            except ValueError:
                return candidate

            return "<redacted-address>"

        value = cls._ADDRESS_CANDIDATE_RE.sub(
            replace_address,
            value,
        )

        return cls._MAC_RE.sub(
            "<redacted-address>",
            value,
        )

    def _public_timing_log(
        self,
    ) -> str:
        if self._timing_path is None:
            return ""

        try:
            return (
                self._timing_path.resolve()
                .relative_to(self.project_root)
                .as_posix()
            )
        except (OSError, ValueError):
            return self._timing_path.name

    def _sanitize_public_helper_status(
        self,
        value: Any,
        *,
        key: str = "",
        depth: int = 0,
    ) -> Any:
        if depth > 12:
            return None

        normalized_key = key.strip().lower()

        if (
            normalized_key == "ip"
            or normalized_key.endswith("_ip")
            or normalized_key == "address"
            or normalized_key.endswith("_address")
        ):
            if value in (None, ""):
                return value
            return "<redacted-address>"

        if (
            normalized_key == "path"
            or normalized_key.endswith("_path")
            or normalized_key in {"log_path", "timing_log", "status_path"}
        ):
            if value in (None, ""):
                return value
            return "<redacted-path>"

        if value is None:
            return None
        if isinstance(value, (bool, int, float)):
            return value

        if isinstance(value, str):
            public = self._redact_network_text(value)
            root_text = str(self.project_root)
            if root_text:
                public = public.replace(root_text, "<project-root>")
                public = public.replace(root_text.replace("\\", "/"), "<project-root>")
            return self._WINDOWS_ABSOLUTE_PATH_RE.sub("<redacted-path>", public)

        if isinstance(value, list):
            return [
                self._sanitize_public_helper_status(item, depth=depth + 1)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                str(item_key): self._sanitize_public_helper_status(
                    item_value, key=str(item_key), depth=depth + 1
                )
                for item_key, item_value in value.items()
            }

        return str(type(value).__name__)

    def status(
        self,
    ) -> dict[str, Any]:
        if sys.platform.startswith("linux"):
            with self._lock:
                return self._linux_status_locked()

        process_active = (
            self._process is not None
            and self._process.poll()
            is None
        )

        helper = (
            self._read_status()
        )

        return {
            "active": (
                process_active
                and bool(
                    helper.get(
                        "ready",
                        False,
                    )
                )
            ),
            "device": (
                "managed_process_audio"
            ),
            "sample_rate": 48_000,
            "channels": 2,
            "format": "pcm_s16le",
            "packet_ms": 5,
            "port": self._client_port,
            "target_pid": (
                self._target_pid
            ),
            "include_process_tree": True,
            "capture_backend": (
                "windows_wasapi_process_loopback"
            ),
            "helper": (
                "NAudio.Wasapi 3.0.1"
            ),
            "timing_probe": (
                self.TIMING_PROBE_VERSION
            ),
            "audio_buffer_architecture": (
                self.AUDIO_BUFFER_ARCHITECTURE
            ),
            "packets_sent": int(
                helper.get(
                    "send",
                    {},
                ).get(
                    "packets",
                    0,
                )
                if isinstance(
                    helper.get(
                        "send",
                        {},
                    ),
                    dict,
                )
                else 0
            ),
            "send_errors": int(
                helper.get(
                    "send",
                    {},
                ).get(
                    "errors",
                    0,
                )
                if isinstance(
                    helper.get(
                        "send",
                        {},
                    ),
                    dict,
                )
                else 0
            ),
            "timing_log": (
                self._public_timing_log()
            ),
            "helper_status": (
                self._sanitize_public_helper_status(
                    helper
                )
            ),
        }

    def stop(
        self,
    ) -> None:
        if sys.platform.startswith("linux"):
            with self._lock:
                self._stop_linux_locked()
            return

        process = (
            self._process
        )
        self._process = None

        self._kill_process(
            process
        )

        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass

        self._log_handle = None
        self._client_ip = None
        self._client_port = None
        self._target_pid = None

class NativeControllerBridge:
    MAGIC = b"PHI1"
    VERSION = 1
    MAX_PLAYERS = 4
    POC_VERSION = "four_player_poc_v0.1"
    PACKET = struct.Struct(
        "<4sBBHIQIhhhhHH"
    )

    LINUX_VENDOR_ID = 0x1209
    LINUX_PRODUCT_ID = 0x5048
    LINUX_VERSION_ID = 1
    LINUX_GAMEPAD_NAME = "PrivyHub Virtual Gamepad P{player}"

    XUSB_DPAD_UP = 0x0001
    XUSB_DPAD_DOWN = 0x0002
    XUSB_DPAD_LEFT = 0x0004
    XUSB_DPAD_RIGHT = 0x0008
    XUSB_START = 0x0010
    XUSB_BACK = 0x0020
    XUSB_LEFT_THUMB = 0x0040
    XUSB_RIGHT_THUMB = 0x0080
    XUSB_LEFT_SHOULDER = 0x0100
    XUSB_RIGHT_SHOULDER = 0x0200
    XUSB_A = 0x1000
    XUSB_B = 0x2000
    XUSB_X = 0x4000
    XUSB_Y = 0x8000

    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.project_root = project_root.resolve()
        self.runtime_dir = (
            self.project_root
            / "runtime"
            / "streaming"
            / "input_python"
        )

        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._gamepads: list[Any] = []
        self._client_ip: str | None = None
        self._port: int | None = None
        self._controller_backend = self._selected_backend()
        self._evdev: Any | None = None

        self._packets = 0
        self._lost_packets = 0
        self._rejected_packets = 0
        self._bad_packets = 0
        self._updates = 0
        self._updates_by_player = [
            0 for _ in range(self.MAX_PLAYERS)
        ]
        self._last_sequence: int | None = None
        self._last_packet_at = [
            0.0 for _ in range(self.MAX_PLAYERS)
        ]
        self._neutralized = [
            True for _ in range(self.MAX_PLAYERS)
        ]
        self._forced_buttons = [
            0 for _ in range(self.MAX_PLAYERS)
        ]
        self._last_reports = [
            self._empty_report()
            for _ in range(self.MAX_PLAYERS)
        ]
        self._meta_lock = threading.RLock()

        # D-BASE-R3: the host's own evidence that the client is gone. The
        # receive loop already wakes every 50 ms and already measures
        # per-player silence in order to neutralize inputs; this rides on
        # that and reports the first crossing of the recovery threshold.
        self._last_any_packet_at = 0.0
        self._silence_callback: Callable[[float], None] | None = None
        self._silence_threshold_s = 1.0
        self._silence_reported = False

    @staticmethod
    def _selected_backend() -> str:
        if os.name == "nt":
            return "windows_vigem"
        if sys.platform.startswith("linux"):
            return "linux_uinput"
        raise NativeSessionIOError(
            f"Unsupported controller host platform: {os.name}"
        )

    @staticmethod
    def _empty_report() -> dict[str, int]:
        return {
            "buttons": 0,
            "lx": 0,
            "ly": 0,
            "rx": 0,
            "ry": 0,
            "lt": 0,
            "rt": 0,
        }

    def _load_vgamepad(
        self,
    ):
        if not self.runtime_dir.is_dir():
            raise NativeSessionIOError(
                "Project-local vgamepad runtime is missing."
            )

        runtime = str(
            self.runtime_dir
        )

        if runtime not in sys.path:
            sys.path.insert(
                0,
                runtime,
            )

        try:
            import vgamepad as vg
        except Exception as exc:
            raise NativeSessionIOError(
                f"Unable to import project-local vgamepad: {exc}"
            ) from exc

        return vg

    @staticmethod
    def _load_evdev():
        try:
            import evdev
        except Exception as exc:
            raise NativeSessionIOError(
                "Linux controller backend requires python3-evdev. "
                f"Import failed: {exc}"
            ) from exc

        return evdev

    @staticmethod
    def _clamp_axis(
        value: int,
    ) -> int:
        return max(
            -32768,
            min(
                32767,
                int(value),
            ),
        )

    @classmethod
    def _invert_axis(
        cls,
        value: int,
    ) -> int:
        return cls._clamp_axis(
            -cls._clamp_axis(value)
        )

    @staticmethod
    def _clamp_trigger(
        value: int,
    ) -> int:
        return max(
            0,
            min(
                255,
                int(value),
            ),
        )

    def _linux_capabilities(
        self,
        evdev: Any,
    ) -> dict[int, list[Any]]:
        ecodes = evdev.ecodes
        stick = evdev.AbsInfo(
            value=0,
            min=-32768,
            max=32767,
            fuzz=0,
            flat=128,
            resolution=0,
        )
        trigger = evdev.AbsInfo(
            value=0,
            min=0,
            max=255,
            fuzz=0,
            flat=0,
            resolution=0,
        )
        hat = evdev.AbsInfo(
            value=0,
            min=-1,
            max=1,
            fuzz=0,
            flat=0,
            resolution=0,
        )
        return {
            ecodes.EV_KEY: [
                ecodes.BTN_SOUTH,
                ecodes.BTN_EAST,
                ecodes.BTN_NORTH,
                ecodes.BTN_WEST,
                ecodes.BTN_TL,
                ecodes.BTN_TR,
                ecodes.BTN_SELECT,
                ecodes.BTN_START,
                ecodes.BTN_THUMBL,
                ecodes.BTN_THUMBR,
            ],
            ecodes.EV_ABS: [
                (ecodes.ABS_X, stick),
                (ecodes.ABS_Y, stick),
                (ecodes.ABS_Z, trigger),
                (ecodes.ABS_RX, stick),
                (ecodes.ABS_RY, stick),
                (ecodes.ABS_RZ, trigger),
                (ecodes.ABS_HAT0X, hat),
                (ecodes.ABS_HAT0Y, hat),
            ],
        }

    def _create_gamepads(
        self,
    ) -> list[Any]:
        if self._controller_backend == "windows_vigem":
            vg = self._load_vgamepad()
            gamepads: list[Any] = []
            try:
                for _ in range(
                    self.MAX_PLAYERS
                ):
                    gamepads.append(
                        vg.VX360Gamepad()
                    )
            except Exception as exc:
                for gamepad in gamepads:
                    try:
                        gamepad.reset()
                        gamepad.update()
                    except Exception:
                        pass
                raise NativeSessionIOError(
                    "Unable to create four temporary virtual X360 controllers. "
                    "ViGEmBus must already be installed on this Windows host."
                ) from exc
            return gamepads

        evdev = self._load_evdev()
        self._evdev = evdev
        capabilities = self._linux_capabilities(evdev)
        gamepads = []

        try:
            for player in range(
                1,
                self.MAX_PLAYERS + 1,
            ):
                gamepads.append(
                    evdev.UInput(
                        capabilities,
                        name=self.LINUX_GAMEPAD_NAME.format(
                            player=player
                        ),
                        vendor=self.LINUX_VENDOR_ID,
                        product=self.LINUX_PRODUCT_ID,
                        version=self.LINUX_VERSION_ID,
                        bustype=evdev.ecodes.BUS_USB,
                    )
                )
        except Exception as exc:
            for gamepad in reversed(gamepads):
                try:
                    gamepad.close()
                except Exception:
                    pass
            self._evdev = None
            raise NativeSessionIOError(
                "Unable to create four Linux uinput controllers. "
                "The companion user must have write access to /dev/uinput. "
                f"uinput error: {exc}"
            ) from exc

        return gamepads

    def _dispose_gamepads(
        self,
        gamepads: list[Any],
    ) -> None:
        if self._controller_backend == "windows_vigem":
            for gamepad in gamepads:
                try:
                    gamepad.reset()
                    gamepad.update()
                except Exception:
                    pass
            return

        for gamepad in reversed(gamepads):
            try:
                gamepad.close()
            except Exception:
                pass
        self._evdev = None

    # PrivyHub Phase A3 persistent game-session controller
    # D-BASE-R3 accessors. The callback fires once per silence episode, from
    # the receive loop, and is re-armed by the next packet.
    def set_client_silence_callback(
        self,
        callback: "Callable[[float], None] | None",
        threshold_ms: float,
    ) -> None:
        self._silence_callback = callback
        self._silence_threshold_s = max(
            0.05,
            float(threshold_ms) / 1000.0,
        )

    def last_client_packet_age_ms(self) -> float | None:
        last = self._last_any_packet_at

        if last <= 0.0:
            return None

        return max(
            0.0,
            (time.monotonic() - last) * 1000.0,
        )

    def ensure_started(
        self,
        client_ip: str,
        port: int,
    ) -> dict[str, Any]:
        active = bool(
            self._running.is_set()
            and self._socket is not None
            and len(self._gamepads) == self.MAX_PLAYERS
        )
        if active and self._client_ip == client_ip and self._port == int(port):
            return self.status()
        result = self.start(client_ip=client_ip, port=port)
        time.sleep(0.35)
        return result

    def start(
        self,
        client_ip: str,
        port: int,
    ) -> dict[str, Any]:
        self.stop()

        gamepads = self._create_gamepads()
        sock: socket.socket | None = None

        try:
            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF,
                256 * 1024,
            )

            sock.bind(
                (
                    "0.0.0.0",
                    int(port),
                )
            )

            sock.settimeout(
                0.05
            )
        except Exception:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
            self._dispose_gamepads(gamepads)
            raise

        self._socket = sock
        self._gamepads = gamepads
        self._client_ip = client_ip
        self._port = int(port)

        self._packets = 0
        self._lost_packets = 0
        self._rejected_packets = 0
        self._bad_packets = 0
        self._updates = 0
        self._updates_by_player = [
            0 for _ in range(self.MAX_PLAYERS)
        ]
        self._last_sequence = None
        self._last_packet_at = [
            0.0 for _ in range(self.MAX_PLAYERS)
        ]
        self._neutralized = [
            True for _ in range(self.MAX_PLAYERS)
        ]
        self._last_reports = [
            self._empty_report()
            for _ in range(self.MAX_PLAYERS)
        ]
        self._last_any_packet_at = 0.0
        self._silence_reported = False

        with self._meta_lock:
            self._forced_buttons = [
                0 for _ in range(self.MAX_PLAYERS)
            ]

        self._running.set()

        self._thread = threading.Thread(
            target=self._receive_loop,
            name="PrivyHub-Native-Controller",
            daemon=True,
        )
        self._thread.start()

        return self.status()

    def _write_linux_report_locked(
        self,
        player: int,
        report: dict[str, int],
        *,
        forced_buttons: int,
    ) -> None:
        if self._evdev is None:
            raise NativeSessionIOError(
                "Linux uinput backend is unavailable"
            )

        ecodes = self._evdev.ecodes
        gamepad = self._gamepads[player]
        buttons = (
            int(report["buttons"])
            | int(forced_buttons)
        ) & 0xFFFF

        button_map = (
            (self.XUSB_A, ecodes.BTN_SOUTH),
            (self.XUSB_B, ecodes.BTN_EAST),
            (self.XUSB_X, ecodes.BTN_WEST),
            (self.XUSB_Y, ecodes.BTN_NORTH),
            (self.XUSB_LEFT_SHOULDER, ecodes.BTN_TL),
            (self.XUSB_RIGHT_SHOULDER, ecodes.BTN_TR),
            (self.XUSB_BACK, ecodes.BTN_SELECT),
            (self.XUSB_START, ecodes.BTN_START),
            (self.XUSB_LEFT_THUMB, ecodes.BTN_THUMBL),
            (self.XUSB_RIGHT_THUMB, ecodes.BTN_THUMBR),
        )

        for mask, code in button_map:
            gamepad.write(
                ecodes.EV_KEY,
                code,
                1 if buttons & mask else 0,
            )

        hat_x = (
            -1
            if buttons & self.XUSB_DPAD_LEFT
            else 1
            if buttons & self.XUSB_DPAD_RIGHT
            else 0
        )
        hat_y = (
            -1
            if buttons & self.XUSB_DPAD_UP
            else 1
            if buttons & self.XUSB_DPAD_DOWN
            else 0
        )

        gamepad.write(
            ecodes.EV_ABS,
            ecodes.ABS_X,
            self._clamp_axis(report["lx"]),
        )
        gamepad.write(
            ecodes.EV_ABS,
            ecodes.ABS_Y,
            self._invert_axis(report["ly"]),
        )
        gamepad.write(
            ecodes.EV_ABS,
            ecodes.ABS_RX,
            self._clamp_axis(report["rx"]),
        )
        gamepad.write(
            ecodes.EV_ABS,
            ecodes.ABS_RY,
            self._invert_axis(report["ry"]),
        )
        gamepad.write(
            ecodes.EV_ABS,
            ecodes.ABS_Z,
            self._clamp_trigger(report["lt"]),
        )
        gamepad.write(
            ecodes.EV_ABS,
            ecodes.ABS_RZ,
            self._clamp_trigger(report["rt"]),
        )
        gamepad.write(
            ecodes.EV_ABS,
            ecodes.ABS_HAT0X,
            hat_x,
        )
        gamepad.write(
            ecodes.EV_ABS,
            ecodes.ABS_HAT0Y,
            hat_y,
        )
        gamepad.syn()

    def _neutralize(
        self,
        player: int | None = None,
    ) -> None:
        players = (
            range(
                self.MAX_PLAYERS
            )
            if player is None
            else (player,)
        )

        for index in players:
            if not (
                0 <= index < len(
                    self._gamepads
                )
            ):
                continue

            gamepad = self._gamepads[index]

            try:
                # Timeout neutralization must not erase a companion-injected
                # RetroArch meta hotkey mid-pulse.
                with self._meta_lock:
                    forced_buttons = self._forced_buttons[index]
                    self._last_reports[index] = self._empty_report()

                    if self._controller_backend == "windows_vigem":
                        gamepad.reset()
                        gamepad.report.wButtons = (
                            int(forced_buttons)
                            & 0xFFFF
                        )
                        gamepad.update()
                    else:
                        self._write_linux_report_locked(
                            index,
                            self._last_reports[index],
                            forced_buttons=forced_buttons,
                        )

                    self._neutralized[index] = (
                        forced_buttons == 0
                    )
            except Exception:
                pass

    def _apply_report(
        self,
        player: int,
        buttons: int,
        lx: int,
        ly: int,
        rx: int,
        ry: int,
        lt: int,
        rt: int,
    ) -> None:
        if not (
            0 <= player < len(
                self._gamepads
            )
        ):
            return

        gamepad = self._gamepads[player]

        # Serialize real reports with the forced meta-button overlay so
        # receiver traffic cannot erase a hotkey.
        with self._meta_lock:
            forced_buttons = self._forced_buttons[player]
            report = {
                "buttons": int(buttons) & 0xFFFF,
                "lx": self._clamp_axis(lx),
                "ly": self._clamp_axis(ly),
                "rx": self._clamp_axis(rx),
                "ry": self._clamp_axis(ry),
                "lt": self._clamp_trigger(lt),
                "rt": self._clamp_trigger(rt),
            }
            self._last_reports[player] = report

            if self._controller_backend == "windows_vigem":
                gamepad.report.wButtons = (
                    report["buttons"]
                    | forced_buttons
                ) & 0xFFFF
                gamepad.report.bLeftTrigger = report["lt"]
                gamepad.report.bRightTrigger = report["rt"]
                gamepad.report.sThumbLX = report["lx"]
                gamepad.report.sThumbLY = report["ly"]
                gamepad.report.sThumbRX = report["rx"]
                gamepad.report.sThumbRY = report["ry"]
                gamepad.update()
            else:
                self._write_linux_report_locked(
                    player,
                    report,
                    forced_buttons=forced_buttons,
                )

            self._updates += 1
            self._updates_by_player[player] += 1
            self._neutralized[player] = False

    # RetroArch meta-hotkey edges. RetroArch treats input_enable_hotkey as a
    # modifier, so establish Back/View before the action button and release it
    # last. The canonical XUSB masks remain unchanged on both host backends.
    RETROARCH_HOTKEY_ENABLE = XUSB_BACK
    RETROARCH_META_ACTION_BUTTONS = {
        "save": XUSB_RIGHT_SHOULDER,
        "load": XUSB_LEFT_SHOULDER,
        "pause": XUSB_RIGHT_THUMB,
        "quit": XUSB_START,
    }

    def _write_forced_overlay_locked(
        self,
        player: int,
    ) -> None:
        gamepad = self._gamepads[player]
        forced_buttons = self._forced_buttons[player]

        if self._controller_backend == "windows_vigem":
            gamepad.report.wButtons = (
                int(gamepad.report.wButtons)
                | int(forced_buttons)
            ) & 0xFFFF
            gamepad.update()
            return

        self._write_linux_report_locked(
            player,
            self._last_reports[player],
            forced_buttons=forced_buttons,
        )

    def _clear_forced_bit_locked(
        self,
        player: int,
        mask: int,
    ) -> None:
        gamepad = self._gamepads[player]
        self._forced_buttons[player] &= ~mask

        if self._controller_backend == "windows_vigem":
            gamepad.report.wButtons = (
                int(gamepad.report.wButtons)
                & ~mask
            ) & 0xFFFF
            gamepad.update()
            return

        self._write_linux_report_locked(
            player,
            self._last_reports[player],
            forced_buttons=self._forced_buttons[player],
        )

    def pulse_retroarch_hotkey(
        self,
        action: str,
        *,
        player: int = 0,
        hold_seconds: float = 0.18,
        modifier_settle_seconds: float = 0.08,
        release_gap_seconds: float = 0.06,
    ) -> dict[str, Any]:
        normalized_action = (
            str(action).strip().casefold()
        )
        action_mask = (
            self.RETROARCH_META_ACTION_BUTTONS.get(
                normalized_action
            )
        )
        if action_mask is None:
            raise NativeSessionIOError(
                f"Unknown RetroArch hotkey action: {action}"
            )

        if not self._running.is_set():
            raise NativeSessionIOError(
                "Native controller bridge is not running"
            )
        if not (0 <= player < len(self._gamepads)):
            raise NativeSessionIOError(
                "Requested virtual controller is unavailable"
            )

        modifier_mask = int(
            self.RETROARCH_HOTKEY_ENABLE
        )
        action_mask = int(action_mask)
        hold = max(
            0.08,
            min(0.50, float(hold_seconds)),
        )
        settle = max(
            0.04,
            min(0.20, float(modifier_settle_seconds)),
        )
        release_gap = max(
            0.03,
            min(0.20, float(release_gap_seconds)),
        )

        # 1. Establish Back/View alone.
        with self._meta_lock:
            self._forced_buttons[player] |= modifier_mask
            self._write_forced_overlay_locked(player)

        time.sleep(settle)

        # 2. Press the action while the modifier is already held.
        with self._meta_lock:
            self._forced_buttons[player] |= action_mask
            self._write_forced_overlay_locked(player)

        time.sleep(hold)

        # 3. Release the action first, preserving Back/View.
        with self._meta_lock:
            self._clear_forced_bit_locked(
                player,
                action_mask,
            )

        time.sleep(release_gap)

        # 4. Release Back/View last so RetroArch sees a complete chord.
        with self._meta_lock:
            self._clear_forced_bit_locked(
                player,
                modifier_mask,
            )

        return {
            "action": normalized_action,
            "player": player + 1,
            "modifier_mask": modifier_mask,
            "action_mask": action_mask,
            "mask": modifier_mask | action_mask,
            "modifier_settle_ms": int(settle * 1000),
            "hold_ms": int(hold * 1000),
            "release_gap_ms": int(release_gap * 1000),
            "edge_sequence": [
                "modifier_down",
                "action_down",
                "action_up",
                "modifier_up",
            ],
        }

    def _receive_loop(
        self,
    ) -> None:
        sock = self._socket

        if sock is None:
            return

        while self._running.is_set():
            try:
                data, source = sock.recvfrom(
                    256
                )
            except socket.timeout:
                now = time.monotonic()

                for player in range(
                    self.MAX_PLAYERS
                ):
                    if (
                        not self._neutralized[player]
                        and self._last_packet_at[player] > 0.0
                        and now - self._last_packet_at[player] > 0.25
                    ):
                        self._neutralize(
                            player
                        )

                # D-BASE-R3: the client sends ~430 packets/s even with no
                # input, so this silence means the client or the link is
                # gone. Reported once per episode; the callback must not
                # block this loop for long.
                callback = self._silence_callback

                if (
                    callback is not None
                    and not self._silence_reported
                    and self._last_any_packet_at > 0.0
                    and now - self._last_any_packet_at
                    > self._silence_threshold_s
                ):
                    self._silence_reported = True

                    try:
                        callback(
                            (
                                now - self._last_any_packet_at
                            )
                            * 1000.0
                        )
                    except Exception:
                        pass

                continue
            except OSError:
                break

            if source[0] != self._client_ip:
                self._rejected_packets += 1
                continue

            if len(data) != self.PACKET.size:
                self._bad_packets += 1
                continue

            try:
                (
                    magic,
                    version,
                    player,
                    _flags,
                    sequence,
                    _client_time_us,
                    buttons,
                    lx,
                    ly,
                    rx,
                    ry,
                    lt,
                    rt,
                ) = self.PACKET.unpack(
                    data
                )
            except struct.error:
                self._bad_packets += 1
                continue

            if (
                magic != self.MAGIC
                or version != self.VERSION
                or player < 0
                or player >= self.MAX_PLAYERS
            ):
                self._bad_packets += 1
                continue

            if self._last_sequence is not None:
                expected = (
                    self._last_sequence + 1
                ) & 0xFFFFFFFF

                if sequence != expected:
                    missing = (
                        sequence - expected
                    ) & 0xFFFFFFFF

                    if missing < 0x80000000:
                        self._lost_packets += missing

            self._last_sequence = sequence
            self._packets += 1
            self._last_packet_at[player] = (
                time.monotonic()
            )
            self._last_any_packet_at = (
                self._last_packet_at[player]
            )
            self._silence_reported = False

            try:
                self._apply_report(
                    player=player,
                    buttons=buttons,
                    lx=lx,
                    ly=ly,
                    rx=rx,
                    ry=ry,
                    lt=lt,
                    rt=rt,
                )
            except Exception:
                self._bad_packets += 1

        self._neutralize()

    def status(
        self,
    ) -> dict[str, Any]:
        sink = (
            "vigem_x360_quad_poc"
            if self._controller_backend == "windows_vigem"
            else "uinput_quad"
        )
        return {
            "active": (
                self._running.is_set()
                and self._socket is not None
                and len(
                    self._gamepads
                ) == self.MAX_PLAYERS
            ),
            "sink": sink,
            "backend": self._controller_backend,
            "transport": "udp_full_state",
            "poc_version": self.POC_VERSION,
            "players": self.MAX_PLAYERS,
            "port": self._port,
            "packets_received": self._packets,
            "lost_packets": self._lost_packets,
            "rejected_packets": self._rejected_packets,
            "bad_packets": self._bad_packets,
            "updates": self._updates,
            "updates_by_player": list(
                self._updates_by_player
            ),
            # Compatibility aliases consumed by existing diagnostics. These
            # remain populated on Linux even though the sink is not ViGEm.
            "vigem_updates": self._updates,
            "vigem_updates_by_player": list(
                self._updates_by_player
            ),
        }

    def stop(
        self,
    ) -> None:
        self._running.clear()

        sock = self._socket
        self._socket = None

        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

        thread = self._thread
        self._thread = None

        if (
            thread is not None
            and thread is not threading.current_thread()
        ):
            thread.join(
                timeout=1
            )

        with self._meta_lock:
            self._forced_buttons = [
                0 for _ in range(self.MAX_PLAYERS)
            ]

        self._neutralize()
        gamepads = self._gamepads
        self._gamepads = []
        self._dispose_gamepads(gamepads)
        self._last_reports = [
            self._empty_report()
            for _ in range(self.MAX_PLAYERS)
        ]
        self._client_ip = None
        self._port = None

class NativeSessionIO:
    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.audio = NativeAudioStreamer(
            project_root
        )
        self.controller = NativeControllerBridge(
            project_root
        )

        self._audio_error: str | None = None
        self._controller_error: str | None = None

    # PrivyHub Phase A3 persistent game-session controller
    def ensure_controller(
        self,
        client_ip: str,
        input_port: int,
    ) -> dict[str, Any]:
        self._controller_error = None
        try:
            return self.controller.ensure_started(client_ip=client_ip, port=input_port)
        except Exception as exc:
            self._controller_error = str(exc)
            raise

    def start(
        self,
        ffmpeg: Path,
        client_ip: str,
        audio_port: int,
        input_port: int,
        process_id: int,
    ) -> dict[str, Any]:
        self.audio.stop()
        self._audio_error = None
        try:
            self.ensure_controller(client_ip=client_ip, input_port=input_port)
        except Exception:
            pass
        try:
            self.audio.start(
                ffmpeg=ffmpeg,
                client_ip=client_ip,
                client_port=audio_port,
                process_id=process_id,
            )
        except Exception as exc:
            self._audio_error = str(exc)
        return self.status()

    def status(self) -> dict[str, Any]:
        audio = self.audio.status()
        controller = self.controller.status()
        if self._audio_error:
            audio["error"] = self._audio_error
        if self._controller_error:
            controller["error"] = self._controller_error
        return {"audio": audio, "controller": controller}

    def stop_stream(self) -> None:
        self.audio.stop()
        self._audio_error = None

    def stop(self) -> None:
        self.audio.stop()
        self.controller.stop()
        self._audio_error = None
        self._controller_error = None
