from __future__ import annotations

import json
import os

from collections import deque
import re
import socket
import struct
import subprocess
import sys
import threading
import time

from pathlib import Path
from typing import Any


class NativeSessionIOError(RuntimeError):
    pass


class NativeAudioStreamer:
    MAGIC = b"PHA1"
    VERSION = 1
    SAMPLE_RATE = 48_000
    CHANNELS = 2
    SAMPLE_BYTES = 2
    FRAMES_PER_PACKET = 240  # 5 ms at 48 kHz
    PAYLOAD_BYTES = (
        FRAMES_PER_PACKET
        * CHANNELS
        * SAMPLE_BYTES
    )
    HEADER = struct.Struct("<4sBBHII")

    TIMING_PROBE_VERSION = "audio_timing_probe_v0.17"
    AUDIO_BUFFER_ARCHITECTURE = "bounded_reservoir_v0.18"
    DIRECTSHOW_AUDIO_BUFFER_MS = 20

    # Six 5 ms packets = a hard 30 ms host-side ceiling. Start sending once
    # four packets are available so common 10-30 ms DirectShow batches can be
    # smoothed without creating an unbounded latency queue.
    RESERVOIR_CAPACITY_PACKETS = 6
    RESERVOIR_START_PACKETS = 4
    SENDER_INTERVAL_NS = 5_000_000

    # Small scheduler lateness is absorbed by the normal sample clock. If a
    # sender deadline is missed by more than 2 ms, rebase instead of emitting
    # a compressed catch-up sequence.
    SENDER_REBASE_LATE_NS = 2_000_000
    TIMING_BURST_NS = 2_000_000
    TIMING_LONG_GAP_NS = 10_000_000
    TIMING_EVENT_LIMIT = 512

    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.project_root = project_root.resolve()
        self.log_dir = (
            self.project_root
            / "logs"
            / "games"
        )
        self.log_path = (
            self.log_dir
            / "native_audio_alpha.log"
        )
        self.timing_log_dir = (
            self.log_dir
            / "audio_timing"
        )

        self._process: subprocess.Popen[Any] | None = None
        self._thread: threading.Thread | None = None
        self._reader_thread: threading.Thread | None = None
        self._socket: socket.socket | None = None
        self._log_handle = None
        self._running = threading.Event()
        self._lock = threading.RLock()
        self._reservoir_condition = threading.Condition()
        self._reservoir: deque[bytes] = deque()
        self._source_ended = False

        self._device: str | None = None
        self._client_ip: str | None = None
        self._client_port: int | None = None
        self._packets = 0
        self._bytes = 0
        self._send_errors = 0

        self._reservoir_packets_read = 0
        self._reservoir_packets_sent = 0
        self._reservoir_drop_oldest = 0
        self._reservoir_max_depth = 0
        self._reservoir_depth_samples = 0
        self._reservoir_depth_total = 0
        self._reservoir_underflows = 0
        self._reservoir_sender_rebases = 0
        self._reservoir_sender_max_late_ns = 0
        self._reservoir_start_depth = 0

        self._timing_path: Path | None = None
        self._timing_started_ns = 0
        self._timing_last_read_done_ns = 0
        self._timing_last_send_done_ns = 0
        self._timing_read_calls = 0
        self._timing_read_block_total_ns = 0
        self._timing_read_block_max_ns = 0
        self._timing_send_calls = 0
        self._timing_send_call_total_ns = 0
        self._timing_send_call_max_ns = 0
        self._timing_read_interval_count = 0
        self._timing_read_interval_total_ns = 0
        self._timing_read_interval_min_ns = 0
        self._timing_read_interval_max_ns = 0
        self._timing_send_interval_count = 0
        self._timing_send_interval_total_ns = 0
        self._timing_send_interval_min_ns = 0
        self._timing_send_interval_max_ns = 0
        self._timing_read_interval_hist = self._new_timing_histogram()
        self._timing_send_interval_hist = self._new_timing_histogram()
        self._timing_read_block_hist = self._new_timing_histogram()
        self._timing_send_call_hist = self._new_timing_histogram()
        self._timing_read_burst_intervals = 0
        self._timing_send_burst_intervals = 0
        self._timing_read_long_gaps = 0
        self._timing_send_long_gaps = 0
        self._timing_current_read_burst_packets = 1
        self._timing_max_read_burst_packets = 1
        self._timing_current_send_burst_packets = 1
        self._timing_max_send_burst_packets = 1
        self._timing_events: list[dict[str, float | int | str]] = []

    @staticmethod
    def _new_timing_histogram() -> dict[str, int]:
        return {
            "lt_1ms": 0,
            "1_2ms": 0,
            "2_4ms": 0,
            "4_6ms": 0,
            "6_8ms": 0,
            "8_12ms": 0,
            "12_20ms": 0,
            "20_30ms": 0,
            "ge_30ms": 0,
        }

    @staticmethod
    def _observe_histogram(
        histogram: dict[str, int],
        value_ns: int,
    ) -> None:
        if value_ns < 1_000_000:
            key = "lt_1ms"
        elif value_ns < 2_000_000:
            key = "1_2ms"
        elif value_ns < 4_000_000:
            key = "2_4ms"
        elif value_ns < 6_000_000:
            key = "4_6ms"
        elif value_ns < 8_000_000:
            key = "6_8ms"
        elif value_ns < 12_000_000:
            key = "8_12ms"
        elif value_ns < 20_000_000:
            key = "12_20ms"
        elif value_ns < 30_000_000:
            key = "20_30ms"
        else:
            key = "ge_30ms"

        histogram[key] += 1

    @staticmethod
    def _average_ms(
        total_ns: int,
        count: int,
    ) -> float:
        if count <= 0:
            return 0.0

        return round(
            total_ns /
            count /
            1_000_000.0,
            4,
        )

    def _reset_timing_probe(
        self,
    ) -> None:
        stamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )

        self.timing_log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._timing_path = (
            self.timing_log_dir
            / (
                "audio_timing_"
                + stamp
                + ".json"
            )
        )

        self._timing_started_ns = (
            time.perf_counter_ns()
        )
        self._timing_last_read_done_ns = 0
        self._timing_last_send_done_ns = 0
        self._timing_read_calls = 0
        self._timing_read_block_total_ns = 0
        self._timing_read_block_max_ns = 0
        self._timing_send_calls = 0
        self._timing_send_call_total_ns = 0
        self._timing_send_call_max_ns = 0
        self._timing_read_interval_count = 0
        self._timing_read_interval_total_ns = 0
        self._timing_read_interval_min_ns = 0
        self._timing_read_interval_max_ns = 0
        self._timing_send_interval_count = 0
        self._timing_send_interval_total_ns = 0
        self._timing_send_interval_min_ns = 0
        self._timing_send_interval_max_ns = 0
        self._timing_read_interval_hist = (
            self._new_timing_histogram()
        )
        self._timing_send_interval_hist = (
            self._new_timing_histogram()
        )
        self._timing_read_block_hist = (
            self._new_timing_histogram()
        )
        self._timing_send_call_hist = (
            self._new_timing_histogram()
        )
        self._timing_read_burst_intervals = 0
        self._timing_send_burst_intervals = 0
        self._timing_read_long_gaps = 0
        self._timing_send_long_gaps = 0
        self._timing_current_read_burst_packets = 1
        self._timing_max_read_burst_packets = 1
        self._timing_current_send_burst_packets = 1
        self._timing_max_send_burst_packets = 1
        self._timing_events = []

    def _record_timing_event(
        self,
        event_type: str,
        interval_ns: int,
        read_block_ns: int = 0,
        send_call_ns: int = 0,
    ) -> None:
        if (
            len(self._timing_events)
            >= self.TIMING_EVENT_LIMIT
        ):
            return

        elapsed_ms = (
            (
                time.perf_counter_ns()
                - self._timing_started_ns
            )
            /
            1_000_000.0
            if self._timing_started_ns > 0
            else 0.0
        )

        self._timing_events.append(
            {
                "elapsed_ms": round(
                    elapsed_ms,
                    3,
                ),
                "type": event_type,
                "interval_ms": round(
                    interval_ns /
                    1_000_000.0,
                    4,
                ),
                "read_block_ms": round(
                    read_block_ns /
                    1_000_000.0,
                    4,
                ),
                "send_call_ms": round(
                    send_call_ns /
                    1_000_000.0,
                    4,
                ),
            }
        )

    def _observe_read_timing(
        self,
        read_started_ns: int,
        read_done_ns: int,
    ) -> None:
        block_ns = max(
            0,
            read_done_ns -
            read_started_ns,
        )

        self._timing_read_calls += 1
        self._timing_read_block_total_ns += (
            block_ns
        )
        self._timing_read_block_max_ns = max(
            self._timing_read_block_max_ns,
            block_ns,
        )

        self._observe_histogram(
            self._timing_read_block_hist,
            block_ns,
        )

        previous = (
            self._timing_last_read_done_ns
        )

        if previous > 0:
            interval_ns = max(
                0,
                read_done_ns -
                previous,
            )

            self._timing_read_interval_count += 1
            self._timing_read_interval_total_ns += (
                interval_ns
            )

            if (
                self._timing_read_interval_min_ns == 0
                or interval_ns <
                self._timing_read_interval_min_ns
            ):
                self._timing_read_interval_min_ns = (
                    interval_ns
                )

            self._timing_read_interval_max_ns = max(
                self._timing_read_interval_max_ns,
                interval_ns,
            )

            self._observe_histogram(
                self._timing_read_interval_hist,
                interval_ns,
            )

            if (
                interval_ns <
                self.TIMING_BURST_NS
            ):
                self._timing_read_burst_intervals += 1
                self._timing_current_read_burst_packets += 1
                self._timing_max_read_burst_packets = max(
                    self._timing_max_read_burst_packets,
                    self._timing_current_read_burst_packets,
                )

                self._record_timing_event(
                    "read_burst",
                    interval_ns,
                    read_block_ns=block_ns,
                )
            else:
                self._timing_current_read_burst_packets = 1

            if (
                interval_ns >=
                self.TIMING_LONG_GAP_NS
            ):
                self._timing_read_long_gaps += 1

                self._record_timing_event(
                    "read_gap",
                    interval_ns,
                    read_block_ns=block_ns,
                )

        self._timing_last_read_done_ns = (
            read_done_ns
        )

    def _observe_send_timing(
        self,
        send_started_ns: int,
        send_done_ns: int,
    ) -> None:
        call_ns = max(
            0,
            send_done_ns -
            send_started_ns,
        )

        self._timing_send_calls += 1
        self._timing_send_call_total_ns += (
            call_ns
        )
        self._timing_send_call_max_ns = max(
            self._timing_send_call_max_ns,
            call_ns,
        )

        self._observe_histogram(
            self._timing_send_call_hist,
            call_ns,
        )

        previous = (
            self._timing_last_send_done_ns
        )

        if previous > 0:
            interval_ns = max(
                0,
                send_done_ns -
                previous,
            )

            self._timing_send_interval_count += 1
            self._timing_send_interval_total_ns += (
                interval_ns
            )

            if (
                self._timing_send_interval_min_ns == 0
                or interval_ns <
                self._timing_send_interval_min_ns
            ):
                self._timing_send_interval_min_ns = (
                    interval_ns
                )

            self._timing_send_interval_max_ns = max(
                self._timing_send_interval_max_ns,
                interval_ns,
            )

            self._observe_histogram(
                self._timing_send_interval_hist,
                interval_ns,
            )

            if (
                interval_ns <
                self.TIMING_BURST_NS
            ):
                self._timing_send_burst_intervals += 1
                self._timing_current_send_burst_packets += 1
                self._timing_max_send_burst_packets = max(
                    self._timing_max_send_burst_packets,
                    self._timing_current_send_burst_packets,
                )

                self._record_timing_event(
                    "send_burst",
                    interval_ns,
                    send_call_ns=call_ns,
                )
            else:
                self._timing_current_send_burst_packets = 1

            if (
                interval_ns >=
                self.TIMING_LONG_GAP_NS
            ):
                self._timing_send_long_gaps += 1

                self._record_timing_event(
                    "send_gap",
                    interval_ns,
                    send_call_ns=call_ns,
                )

        self._timing_last_send_done_ns = (
            send_done_ns
        )

    def _timing_payload(
        self,
    ) -> dict[str, Any]:
        duration_ms = (
            (
                time.perf_counter_ns()
                - self._timing_started_ns
            )
            /
            1_000_000.0
            if self._timing_started_ns > 0
            else 0.0
        )

        return {
            "schema": (
                "privyhub_native_audio_timing_v1"
            ),
            "profiler_version": (
                self.TIMING_PROBE_VERSION
            ),
            "duration_ms": round(
                duration_ms,
                3,
            ),
            "device": self._device,
            "packet_ms": 5,
            "frames_per_packet": (
                self.FRAMES_PER_PACKET
            ),
            "payload_bytes": (
                self.PAYLOAD_BYTES
            ),
            "directshow_audio_buffer_ms": (
                self.DIRECTSHOW_AUDIO_BUFFER_MS
            ),
            "audio_buffer_architecture": (
                self.AUDIO_BUFFER_ARCHITECTURE
            ),
            "reservoir": {
                "capacity_packets": (
                    self.RESERVOIR_CAPACITY_PACKETS
                ),
                "startup_target_packets": (
                    self.RESERVOIR_START_PACKETS
                ),
                "packets_read": (
                    self._reservoir_packets_read
                ),
                "packets_sent": (
                    self._reservoir_packets_sent
                ),
                "drop_oldest": (
                    self._reservoir_drop_oldest
                ),
                "max_depth": (
                    self._reservoir_max_depth
                ),
                "avg_depth_at_send": round(
                    self._reservoir_depth_total
                    /
                    max(
                        1,
                        self._reservoir_depth_samples,
                    ),
                    4,
                ),
                "underflows": (
                    self._reservoir_underflows
                ),
                "sender_rebases": (
                    self._reservoir_sender_rebases
                ),
                "sender_max_late_ms": round(
                    self._reservoir_sender_max_late_ns
                    /
                    1_000_000.0,
                    4,
                ),
                "startup_depth": (
                    self._reservoir_start_depth
                ),
            },
            "packets_sent": (
                self._packets
            ),
            "payload_bytes_sent": (
                self._bytes
            ),
            "send_errors": (
                self._send_errors
            ),
            "read": {
                "calls": (
                    self._timing_read_calls
                ),
                "block_avg_ms": (
                    self._average_ms(
                        self._timing_read_block_total_ns,
                        self._timing_read_calls,
                    )
                ),
                "block_max_ms": round(
                    self._timing_read_block_max_ns /
                    1_000_000.0,
                    4,
                ),
                "block_histogram": dict(
                    self._timing_read_block_hist
                ),
                "completion_interval_count": (
                    self._timing_read_interval_count
                ),
                "completion_interval_avg_ms": (
                    self._average_ms(
                        self._timing_read_interval_total_ns,
                        self._timing_read_interval_count,
                    )
                ),
                "completion_interval_min_ms": round(
                    self._timing_read_interval_min_ns /
                    1_000_000.0,
                    4,
                ),
                "completion_interval_max_ms": round(
                    self._timing_read_interval_max_ns /
                    1_000_000.0,
                    4,
                ),
                "completion_interval_histogram": dict(
                    self._timing_read_interval_hist
                ),
                "burst_intervals_under_2ms": (
                    self._timing_read_burst_intervals
                ),
                "long_gaps_ge_10ms": (
                    self._timing_read_long_gaps
                ),
                "max_burst_packets": (
                    self._timing_max_read_burst_packets
                ),
            },
            "send": {
                "calls": (
                    self._timing_send_calls
                ),
                "call_avg_ms": (
                    self._average_ms(
                        self._timing_send_call_total_ns,
                        self._timing_send_calls,
                    )
                ),
                "call_max_ms": round(
                    self._timing_send_call_max_ns /
                    1_000_000.0,
                    4,
                ),
                "call_histogram": dict(
                    self._timing_send_call_hist
                ),
                "completion_interval_count": (
                    self._timing_send_interval_count
                ),
                "completion_interval_avg_ms": (
                    self._average_ms(
                        self._timing_send_interval_total_ns,
                        self._timing_send_interval_count,
                    )
                ),
                "completion_interval_min_ms": round(
                    self._timing_send_interval_min_ns /
                    1_000_000.0,
                    4,
                ),
                "completion_interval_max_ms": round(
                    self._timing_send_interval_max_ns /
                    1_000_000.0,
                    4,
                ),
                "completion_interval_histogram": dict(
                    self._timing_send_interval_hist
                ),
                "burst_intervals_under_2ms": (
                    self._timing_send_burst_intervals
                ),
                "long_gaps_ge_10ms": (
                    self._timing_send_long_gaps
                ),
                "max_burst_packets": (
                    self._timing_max_send_burst_packets
                ),
            },
            "events": list(
                self._timing_events
            ),
            "event_limit": (
                self.TIMING_EVENT_LIMIT
            ),
            "path": (
                str(
                    self._timing_path
                )
                if self._timing_path is not None
                else ""
            ),
        }

    def _persist_timing_probe(
        self,
    ) -> None:
        path = (
            self._timing_path
        )

        if (
            path is None
            or self._timing_started_ns <= 0
        ):
            return

        payload = (
            self._timing_payload()
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = path.with_suffix(
            path.suffix +
            ".tmp"
        )

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )

        os.replace(
            temporary,
            path,
        )

    @staticmethod
    def _kill_process(
        process: subprocess.Popen[Any] | None,
    ) -> None:
        if process is None or process.poll() is not None:
            return

        if os.name == "nt":
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
                timeout=3
            )
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass

    @staticmethod
    def _read_exact(
        stream,
        size: int,
    ) -> bytes:
        chunks: list[bytes] = []
        remaining = size

        while remaining > 0:
            chunk = stream.read(
                remaining
            )

            if not chunk:
                break

            chunks.append(
                chunk
            )
            remaining -= len(
                chunk
            )

        return b"".join(
            chunks
        )

    def _find_cable_output(
        self,
        ffmpeg: Path,
    ) -> str | None:
        try:
            result = subprocess.run(
                [
                    str(ffmpeg),
                    "-hide_banner",
                    "-list_devices",
                    "true",
                    "-f",
                    "dshow",
                    "-i",
                    "dummy",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=8,
                check=False,
            )
        except Exception:
            return None

        text = (
            result.stdout
            + "\n"
            + result.stderr
        )

        candidates = re.findall(
            r'"([^"\r\n]*CABLE Output[^"\r\n]*)"',
            text,
            flags=re.IGNORECASE,
        )

        if not candidates:
            return None

        preferred = [
            candidate
            for candidate in candidates
            if "VB-Audio Virtual Cable" in candidate
        ]

        return (
            preferred[0]
            if preferred
            else candidates[0]
        )

    def start(
        self,
        ffmpeg: Path,
        client_ip: str,
        client_port: int,
    ) -> dict[str, Any]:
        with self._lock:
            self.stop()

            device = (
                self._find_cable_output(
                    ffmpeg
                )
            )

            if not device:
                raise NativeSessionIOError(
                    "VB-CABLE recording endpoint was not found. "
                    "Expected a DirectShow audio source containing "
                    "\"CABLE Output\"."
                )

            self.log_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            self._log_handle = open(
                self.log_path,
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
                "dshow",
                "-audio_buffer_size",
                "20",
                "-i",
                f"audio={device}",
                "-vn",
                "-ac",
                str(self.CHANNELS),
                "-ar",
                str(self.SAMPLE_RATE),
                "-c:a",
                "pcm_s16le",
                "-f",
                "s16le",
                "pipe:1",
            ]

            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
                if os.name == "nt"
                else 0
            )

            try:
                self._process = subprocess.Popen(
                    command,
                    cwd=str(
                        self.project_root
                    ),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=self._log_handle,
                    bufsize=0,
                    creationflags=creationflags,
                )
            except Exception as exc:
                self.stop()

                raise NativeSessionIOError(
                    f"Unable to start VB-CABLE audio capture: {exc}"
                ) from exc

            time.sleep(
                0.35
            )

            if (
                self._process is None
                or self._process.poll() is not None
                or self._process.stdout is None
            ):
                self.stop()

                raise NativeSessionIOError(
                    "VB-CABLE audio capture exited during startup. "
                    "See logs/games/native_audio_alpha.log."
                )

            self._device = device
            self._client_ip = client_ip
            self._client_port = client_port
            self._packets = 0
            self._bytes = 0
            self._send_errors = 0

            with self._reservoir_condition:
                self._reservoir.clear()
                self._source_ended = False
                self._reservoir_packets_read = 0
                self._reservoir_packets_sent = 0
                self._reservoir_drop_oldest = 0
                self._reservoir_max_depth = 0
                self._reservoir_depth_samples = 0
                self._reservoir_depth_total = 0
                self._reservoir_underflows = 0
                self._reservoir_sender_rebases = 0
                self._reservoir_sender_max_late_ns = 0
                self._reservoir_start_depth = 0

            self._reset_timing_probe()

            self._socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

            self._running.set()

            self._reader_thread = threading.Thread(
                target=self._reader_loop,
                name="PrivyHub-Native-Audio-Reader",
                daemon=True,
            )

            self._thread = threading.Thread(
                target=self._send_loop,
                name="PrivyHub-Native-Audio-Sender",
                daemon=True,
            )

            # Reader starts first so it can immediately drain FFmpeg's bursty
            # stdout pipe. The sender independently consumes the bounded
            # reservoir at the sample clock.
            self._reader_thread.start()
            self._thread.start()

            return self.status()

    def _reader_loop(
        self,
    ) -> None:
        process = self._process

        if (
            process is None
            or process.stdout is None
        ):
            with self._reservoir_condition:
                self._source_ended = True
                self._reservoir_condition.notify_all()
            return

        try:
            while self._running.is_set():
                read_started_ns = (
                    time.perf_counter_ns()
                )

                payload = self._read_exact(
                    process.stdout,
                    self.PAYLOAD_BYTES,
                )

                read_done_ns = (
                    time.perf_counter_ns()
                )

                self._observe_read_timing(
                    read_started_ns,
                    read_done_ns,
                )

                if len(payload) != self.PAYLOAD_BYTES:
                    break

                with self._reservoir_condition:
                    if (
                        len(self._reservoir)
                        >= self.RESERVOIR_CAPACITY_PACKETS
                    ):
                        self._reservoir.popleft()
                        self._reservoir_drop_oldest += 1

                    self._reservoir.append(
                        payload
                    )

                    self._reservoir_packets_read += 1
                    self._reservoir_max_depth = max(
                        self._reservoir_max_depth,
                        len(self._reservoir),
                    )

                    self._reservoir_condition.notify_all()

        finally:
            with self._reservoir_condition:
                self._source_ended = True
                self._reservoir_condition.notify_all()

    def _send_loop(
        self,
    ) -> None:
        sock = self._socket
        destination = (
            self._client_ip,
            self._client_port,
        )

        if (
            sock is None
            or destination[0] is None
            or destination[1] is None
        ):
            return

        sequence = 0
        sample_timestamp = 0
        next_send_ns = 0
        started = False

        try:
            while self._running.is_set():
                payload: bytes | None = None

                with self._reservoir_condition:
                    while (
                        self._running.is_set()
                        and not self._source_ended
                        and (
                            not self._reservoir
                            or (
                                not started
                                and len(self._reservoir)
                                < self.RESERVOIR_START_PACKETS
                            )
                        )
                    ):
                        self._reservoir_condition.wait(
                            timeout=0.05
                        )

                    if not self._running.is_set():
                        break

                    if (
                        not self._reservoir
                        and self._source_ended
                    ):
                        break

                    if not self._reservoir:
                        self._reservoir_underflows += 1
                        self._reservoir_condition.wait(
                            timeout=0.01
                        )
                        continue

                    if not started:
                        started = True
                        self._reservoir_start_depth = (
                            len(self._reservoir)
                        )
                        next_send_ns = (
                            time.perf_counter_ns()
                        )

                    payload = self._reservoir.popleft()

                    self._reservoir_depth_samples += 1
                    self._reservoir_depth_total += (
                        len(self._reservoir)
                    )

                if payload is None:
                    continue

                now_ns = time.perf_counter_ns()

                if next_send_ns <= 0:
                    next_send_ns = now_ns

                if now_ns < next_send_ns:
                    time.sleep(
                        (
                            next_send_ns
                            - now_ns
                        )
                        /
                        1_000_000_000.0
                    )

                send_started_ns = (
                    time.perf_counter_ns()
                )

                lateness_ns = max(
                    0,
                    send_started_ns
                    - next_send_ns,
                )

                self._reservoir_sender_max_late_ns = max(
                    self._reservoir_sender_max_late_ns,
                    lateness_ns,
                )

                if (
                    lateness_ns
                    > self.SENDER_REBASE_LATE_NS
                ):
                    self._reservoir_sender_rebases += 1
                    next_send_ns = send_started_ns

                packet = (
                    self.HEADER.pack(
                        self.MAGIC,
                        self.VERSION,
                        self.CHANNELS,
                        sequence & 0xFFFF,
                        sample_timestamp & 0xFFFFFFFF,
                        self.FRAMES_PER_PACKET,
                    )
                    + payload
                )

                try:
                    sock.sendto(
                        packet,
                        destination,
                    )
                    self._packets += 1
                    self._bytes += len(
                        payload
                    )
                    self._reservoir_packets_sent += 1
                except OSError:
                    self._send_errors += 1

                send_done_ns = (
                    time.perf_counter_ns()
                )

                self._observe_send_timing(
                    send_started_ns,
                    send_done_ns,
                )

                sequence = (
                    sequence + 1
                ) & 0xFFFF

                sample_timestamp = (
                    sample_timestamp
                    + self.FRAMES_PER_PACKET
                ) & 0xFFFFFFFF

                next_send_ns += (
                    self.SENDER_INTERVAL_NS
                )

                # A source underrun is handled by waiting for real PCM. Once
                # the reservoir refills, rebase the sender clock rather than
                # trying to reproduce the missed wall-clock packets in a burst.
                with self._reservoir_condition:
                    if (
                        not self._reservoir
                        and not self._source_ended
                    ):
                        self._reservoir_underflows += 1

                        while (
                            self._running.is_set()
                            and not self._source_ended
                            and not self._reservoir
                        ):
                            self._reservoir_condition.wait(
                                timeout=0.05
                            )

                        if self._reservoir:
                            next_send_ns = (
                                time.perf_counter_ns()
                            )
                            self._reservoir_sender_rebases += 1

        finally:
            self._running.clear()

            with self._reservoir_condition:
                self._reservoir_condition.notify_all()

    def status(
        self,
    ) -> dict[str, Any]:
        process_active = (
            self._process is not None
            and self._process.poll() is None
        )

        return {
            "active": (
                process_active
                and self._running.is_set()
            ),
            "device": self._device,
            "sample_rate": self.SAMPLE_RATE,
            "channels": self.CHANNELS,
            "format": "pcm_s16le",
            "packet_ms": 5,
            "packets_sent": self._packets,
            "payload_bytes_sent": self._bytes,
            "send_errors": self._send_errors,
            "timing_probe": (
                self.TIMING_PROBE_VERSION
            ),
            "audio_buffer_architecture": (
                self.AUDIO_BUFFER_ARCHITECTURE
            ),
            "directshow_audio_buffer_ms": (
                self.DIRECTSHOW_AUDIO_BUFFER_MS
            ),
            "reservoir_depth": len(
                self._reservoir
            ),
            "reservoir_capacity_packets": (
                self.RESERVOIR_CAPACITY_PACKETS
            ),
            "reservoir_drop_oldest": (
                self._reservoir_drop_oldest
            ),
            "reservoir_underflows": (
                self._reservoir_underflows
            ),
            "reservoir_sender_rebases": (
                self._reservoir_sender_rebases
            ),
            "timing_log": (
                str(
                    self._timing_path
                )
                if self._timing_path is not None
                else ""
            ),
            "timing_read_bursts_under_2ms": (
                self._timing_read_burst_intervals
            ),
            "timing_read_gaps_ge_10ms": (
                self._timing_read_long_gaps
            ),
            "timing_send_bursts_under_2ms": (
                self._timing_send_burst_intervals
            ),
            "timing_send_gaps_ge_10ms": (
                self._timing_send_long_gaps
            ),
            "port": self._client_port,
        }

    def stop(
        self,
    ) -> None:
        self._running.clear()

        with self._reservoir_condition:
            self._reservoir_condition.notify_all()

        sock = self._socket
        self._socket = None

        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

        self._kill_process(
            self._process
        )
        self._process = None

        thread = self._thread
        self._thread = None

        reader_thread = self._reader_thread
        self._reader_thread = None

        if (
            reader_thread is not None
            and reader_thread is not threading.current_thread()
        ):
            reader_thread.join(
                timeout=1
            )

        if (
            thread is not None
            and thread is not threading.current_thread()
        ):
            thread.join(
                timeout=1
            )

        try:
            self._persist_timing_probe()
        except Exception:
            pass

        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass

        self._log_handle = None
        self._client_ip = None
        self._client_port = None

        with self._reservoir_condition:
            self._reservoir.clear()
            self._source_ended = True


class NativeControllerBridge:
    MAGIC = b"PHI1"
    VERSION = 1
    MAX_PLAYERS = 2
    POC_VERSION = "two_player_poc_v0.1"
    PACKET = struct.Struct(
        "<4sBBHIQIhhhhHH"
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
            / "input_python"
        )

        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._gamepads: list[Any] = []
        self._client_ip: str | None = None
        self._port: int | None = None

        self._packets = 0
        self._lost_packets = 0
        self._rejected_packets = 0
        self._bad_packets = 0
        self._updates = 0
        self._updates_by_player = [0, 0]
        self._last_sequence: int | None = None
        self._last_packet_at = [0.0, 0.0]
        self._neutralized = [True, True]

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

    def start(
        self,
        client_ip: str,
        port: int,
    ) -> dict[str, Any]:
        self.stop()

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
                "Unable to create two temporary virtual X360 controllers. "
                "ViGEmBus must already be installed on this Windows host."
            ) from exc

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

        self._socket = sock
        self._gamepads = gamepads
        self._client_ip = client_ip
        self._port = int(port)

        self._packets = 0
        self._lost_packets = 0
        self._rejected_packets = 0
        self._bad_packets = 0
        self._updates = 0
        self._updates_by_player = [0, 0]
        self._last_sequence = None
        self._last_packet_at = [0.0, 0.0]
        self._neutralized = [True, True]

        self._running.set()

        self._thread = threading.Thread(
            target=self._receive_loop,
            name="PrivyHub-Native-Controller",
            daemon=True,
        )
        self._thread.start()

        return self.status()

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
                gamepad.reset()
                gamepad.update()
                self._neutralized[index] = True
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

        gamepad.report.wButtons = (
            int(buttons)
            & 0xFFFF
        )
        gamepad.report.bLeftTrigger = (
            self._clamp_trigger(lt)
        )
        gamepad.report.bRightTrigger = (
            self._clamp_trigger(rt)
        )
        gamepad.report.sThumbLX = (
            self._clamp_axis(lx)
        )
        gamepad.report.sThumbLY = (
            self._clamp_axis(ly)
        )
        gamepad.report.sThumbRX = (
            self._clamp_axis(rx)
        )
        gamepad.report.sThumbRY = (
            self._clamp_axis(ry)
        )

        gamepad.update()

        self._updates += 1
        self._updates_by_player[player] += 1
        self._neutralized[player] = False

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
        return {
            "active": (
                self._running.is_set()
                and self._socket is not None
                and len(
                    self._gamepads
                ) == self.MAX_PLAYERS
            ),
            "sink": "vigem_x360_dual_poc",
            "transport": "udp_full_state",
            "poc_version": self.POC_VERSION,
            "players": self.MAX_PLAYERS,
            "port": self._port,
            "packets_received": self._packets,
            "lost_packets": self._lost_packets,
            "rejected_packets": self._rejected_packets,
            "bad_packets": self._bad_packets,
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

        self._neutralize()
        self._gamepads = []
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

    def start(
        self,
        ffmpeg: Path,
        client_ip: str,
        audio_port: int,
        input_port: int,
    ) -> dict[str, Any]:
        self.stop()

        self._audio_error = None
        self._controller_error = None

        try:
            self.controller.start(
                client_ip=client_ip,
                port=input_port,
            )
        except Exception as exc:
            self._controller_error = str(
                exc
            )

        try:
            self.audio.start(
                ffmpeg=ffmpeg,
                client_ip=client_ip,
                client_port=audio_port,
            )
        except Exception as exc:
            self._audio_error = str(
                exc
            )

        return self.status()

    def status(
        self,
    ) -> dict[str, Any]:
        audio = self.audio.status()
        controller = self.controller.status()

        if self._audio_error:
            audio["error"] = (
                self._audio_error
            )

        if self._controller_error:
            controller["error"] = (
                self._controller_error
            )

        return {
            "audio": audio,
            "controller": controller,
        }

    def stop(
        self,
    ) -> None:
        self.audio.stop()
        self.controller.stop()
