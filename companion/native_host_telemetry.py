from __future__ import annotations

import ctypes
import json
import os
import threading
import time

from datetime import datetime
from pathlib import Path
from typing import Any

from ctypes import wintypes


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010

SAMPLE_INTERVAL_SECONDS = 2.0
PERSIST_EVERY_SAMPLES = 5
MAX_SAMPLES = 1800


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def _atomic_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
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
        ),
        encoding="utf-8",
    )

    os.replace(
        temporary,
        path,
    )


def _filetime_to_int(
    value: wintypes.FILETIME,
) -> int:
    return (
        int(value.dwHighDateTime) << 32
    ) | int(value.dwLowDateTime)


class _WindowsProcessSampler:
    def __init__(self) -> None:
        self.cpu_count = max(
            1,
            os.cpu_count() or 1,
        )

        self._previous: dict[
            int,
            tuple[int, int]
        ] = {}

        self._kernel32 = ctypes.WinDLL(
            "kernel32",
            use_last_error=True,
        )

        self._psapi = ctypes.WinDLL(
            "psapi",
            use_last_error=True,
        )

        self._kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        self._kernel32.OpenProcess.restype = (
            wintypes.HANDLE
        )

        self._kernel32.CloseHandle.argtypes = [
            wintypes.HANDLE,
        ]
        self._kernel32.CloseHandle.restype = (
            wintypes.BOOL
        )

        self._kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(
                wintypes.FILETIME
            ),
            ctypes.POINTER(
                wintypes.FILETIME
            ),
            ctypes.POINTER(
                wintypes.FILETIME
            ),
            ctypes.POINTER(
                wintypes.FILETIME
            ),
        ]
        self._kernel32.GetProcessTimes.restype = (
            wintypes.BOOL
        )

        self._psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(
                PROCESS_MEMORY_COUNTERS_EX
            ),
            wintypes.DWORD,
        ]
        self._psapi.GetProcessMemoryInfo.restype = (
            wintypes.BOOL
        )

    def sample(
        self,
        pid: int,
    ) -> dict[str, Any]:
        if pid <= 0:
            return {
                "ok": False,
                "pid": int(pid),
                "error": "invalid_pid",
            }

        access = (
            PROCESS_QUERY_INFORMATION
            | PROCESS_QUERY_LIMITED_INFORMATION
            | PROCESS_VM_READ
        )

        handle = self._kernel32.OpenProcess(
            access,
            False,
            int(pid),
        )

        if not handle:
            handle = self._kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                int(pid),
            )

        if not handle:
            return {
                "ok": False,
                "pid": int(pid),
                "error": (
                    "open_process_failed"
                ),
            }

        try:
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()

            cpu_100ns: int | None = None

            if self._kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                cpu_100ns = (
                    _filetime_to_int(kernel)
                    + _filetime_to_int(user)
                )

            counters = (
                PROCESS_MEMORY_COUNTERS_EX()
            )
            counters.cb = ctypes.sizeof(
                counters
            )

            memory_ok = bool(
                self._psapi.GetProcessMemoryInfo(
                    handle,
                    ctypes.byref(counters),
                    counters.cb,
                )
            )

            now_ns = time.perf_counter_ns()

            cpu_one_core_percent = None
            cpu_total_host_percent = None

            if cpu_100ns is not None:
                previous = self._previous.get(
                    int(pid)
                )

                if previous is not None:
                    previous_cpu, previous_ns = (
                        previous
                    )

                    delta_cpu_seconds = max(
                        0.0,
                        (
                            cpu_100ns
                            - previous_cpu
                        )
                        / 10_000_000.0,
                    )

                    delta_wall_seconds = max(
                        0.000001,
                        (
                            now_ns
                            - previous_ns
                        )
                        / 1_000_000_000.0,
                    )

                    cpu_one_core_percent = (
                        delta_cpu_seconds
                        / delta_wall_seconds
                        * 100.0
                    )

                    cpu_total_host_percent = (
                        cpu_one_core_percent
                        / self.cpu_count
                    )

                self._previous[
                    int(pid)
                ] = (
                    cpu_100ns,
                    now_ns,
                )

            payload: dict[str, Any] = {
                "ok": (
                    cpu_100ns is not None
                    or memory_ok
                ),
                "pid": int(pid),
                "cpu_one_core_percent": (
                    round(
                        cpu_one_core_percent,
                        3,
                    )
                    if (
                        cpu_one_core_percent
                        is not None
                    )
                    else None
                ),
                "cpu_total_host_percent": (
                    round(
                        cpu_total_host_percent,
                        3,
                    )
                    if (
                        cpu_total_host_percent
                        is not None
                    )
                    else None
                ),
            }

            if memory_ok:
                payload[
                    "working_set_mib"
                ] = round(
                    int(
                        counters.WorkingSetSize
                    )
                    / 1048576.0,
                    3,
                )

                payload[
                    "peak_working_set_mib"
                ] = round(
                    int(
                        counters.PeakWorkingSetSize
                    )
                    / 1048576.0,
                    3,
                )

                payload[
                    "private_mib"
                ] = round(
                    int(
                        counters.PrivateUsage
                    )
                    / 1048576.0,
                    3,
                )

            return payload

        finally:
            self._kernel32.CloseHandle(
                handle
            )


class NativeHostTelemetryProfiler:
    VERSION = "0.15"

    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.project_root = (
            project_root.resolve()
        )

        self.log_dir = (
            self.project_root
            / "logs"
            / "games"
            / "host_telemetry"
        )

        self._lock = threading.RLock()
        self._stop_event = (
            threading.Event()
        )

        self._thread: Thread | None = None
        self._path: Path | None = None
        self._started_at = 0.0
        self._capture_pid = 0
        self._ffmpeg_pid = 0
        self._metadata_path: Path | None = (
            None
        )
        self._capture_target: (
            dict[str, Any] | None
        ) = None
        self._samples: list[
            dict[str, Any]
        ] = []
        self._error = ""

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "version": self.VERSION,
                "active": (
                    self._thread is not None
                    and self._thread.is_alive()
                ),
                "sample_interval_seconds": (
                    SAMPLE_INTERVAL_SECONDS
                ),
                "samples": len(
                    self._samples
                ),
                "path": (
                    str(self._path)
                    if self._path is not None
                    else ""
                ),
                "error": self._error,
            }

    def start(
        self,
        capture_process: Any,
        ffmpeg_process: Any,
        metadata_path: Path,
        capture_target: (
            dict[str, Any] | None
        ),
    ) -> None:
        self.stop()

        try:
            capture_pid = int(
                capture_process.pid
            )
            ffmpeg_pid = int(
                ffmpeg_process.pid
            )
        except Exception as exc:
            with self._lock:
                self._error = (
                    "Unable to resolve managed "
                    f"process IDs: {exc}"
                )
            return

        stamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        with self._lock:
            self._stop_event = (
                threading.Event()
            )
            self._started_at = (
                time.monotonic()
            )
            self._capture_pid = capture_pid
            self._ffmpeg_pid = ffmpeg_pid
            self._metadata_path = (
                Path(metadata_path)
            )
            self._capture_target = (
                dict(capture_target)
                if capture_target is not None
                else None
            )
            self._samples = []
            self._error = ""
            self._path = (
                self.log_dir
                / (
                    "native_host_"
                    + stamp
                    + "_"
                    + str(capture_pid)
                    + "_"
                    + str(ffmpeg_pid)
                    + ".json"
                )
            )

            self._thread = threading.Thread(
                target=self._run,
                name=(
                    "PrivyHub-Host-Telemetry"
                ),
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            thread = self._thread

            if thread is None:
                return

            self._stop_event.set()

        try:
            thread.join(
                timeout=1.5
            )
        except Exception:
            pass

        try:
            self._sample_once(
                final=True
            )
        except Exception:
            pass

        try:
            self._persist(
                final=True
            )
        except Exception:
            pass

        with self._lock:
            self._thread = None

    def _run(self) -> None:
        try:
            sampler = (
                _WindowsProcessSampler()
            )

            sample_number = 0

            while not self._stop_event.wait(
                SAMPLE_INTERVAL_SECONDS
            ):
                self._sample_once(
                    sampler=sampler
                )

                sample_number += 1

                if (
                    sample_number
                    % PERSIST_EVERY_SAMPLES
                    == 0
                ):
                    self._persist(
                        final=False
                    )

        except Exception as exc:
            with self._lock:
                self._error = str(exc)

            try:
                self._persist(
                    final=False
                )
            except Exception:
                pass

    def _sample_once(
        self,
        sampler: (
            _WindowsProcessSampler | None
        ) = None,
        final: bool = False,
    ) -> None:
        if os.name != "nt":
            return

        if sampler is None:
            sampler = (
                _WindowsProcessSampler()
            )

        with self._lock:
            capture_pid = (
                self._capture_pid
            )
            ffmpeg_pid = (
                self._ffmpeg_pid
            )
            metadata_path = (
                self._metadata_path
            )
            started_at = (
                self._started_at
            )

        sample: dict[str, Any] = {
            "elapsed_ms": int(
                max(
                    0.0,
                    (
                        time.monotonic()
                        - started_at
                    )
                    * 1000.0,
                )
            ),
            "final": bool(final),
            "capture_process": (
                sampler.sample(
                    capture_pid
                )
            ),
            "ffmpeg_process": (
                sampler.sample(
                    ffmpeg_pid
                )
            ),
        }

        if (
            metadata_path is not None
            and metadata_path.is_file()
        ):
            try:
                metadata = json.loads(
                    metadata_path.read_text(
                        encoding="utf-8"
                    )
                )

                sample[
                    "wgc"
                ] = {
                    "callbacks": int(
                        metadata.get(
                            "callbacks",
                            0,
                        )
                    ),
                    "emitted_frames": int(
                        metadata.get(
                            "emitted_frames",
                            0,
                        )
                    ),
                    "duplicated_emits": int(
                        metadata.get(
                            "duplicated_emits",
                            0,
                        )
                    ),
                    "overwritten_frames": int(
                        metadata.get(
                            "overwritten_frames",
                            0,
                        )
                    ),
                    "size_mismatch_frames": int(
                        metadata.get(
                            "size_mismatch_frames",
                            0,
                        )
                    ),
                    "normalized_size_frames": int(
                        metadata.get(
                            "normalized_size_frames",
                            0,
                        )
                    ),
                    "normalization_direct_crop_frames": int(
                        metadata.get(
                            "normalization_direct_crop_frames",
                            0,
                        )
                    ),
                    "normalization_failures": int(
                        metadata.get(
                            "normalization_failures",
                            0,
                        )
                    ),
                    "copy_time_total_ms": float(
                        metadata.get(
                            "copy_time_total_ms",
                            0.0,
                        )
                    ),
                    "copy_time_avg_ms": float(
                        metadata.get(
                            "copy_time_avg_ms",
                            0.0,
                        )
                    ),
                    "copy_time_max_ms": float(
                        metadata.get(
                            "copy_time_max_ms",
                            0.0,
                        )
                    ),
                    "write_time_total_ms": float(
                        metadata.get(
                            "write_time_total_ms",
                            0.0,
                        )
                    ),
                    "write_time_avg_ms": float(
                        metadata.get(
                            "write_time_avg_ms",
                            0.0,
                        )
                    ),
                    "write_time_max_ms": float(
                        metadata.get(
                            "write_time_max_ms",
                            0.0,
                        )
                    ),
                    "frame_bytes": int(
                        metadata.get(
                            "frame_bytes",
                            0,
                        )
                    ),
                    "raw_bytes_emitted": int(
                        metadata.get(
                            "raw_bytes_emitted",
                            0,
                        )
                    ),
                }

            except Exception as exc:
                sample[
                    "wgc_error"
                ] = str(exc)

        with self._lock:
            self._samples.append(
                sample
            )

            if (
                len(self._samples)
                > MAX_SAMPLES
            ):
                del self._samples[
                    :len(self._samples)
                    - MAX_SAMPLES
                ]

    @staticmethod
    def _aggregate_process(
        samples: list[
            dict[str, Any]
        ],
        key: str,
    ) -> dict[str, Any]:
        cpu_one: list[float] = []
        cpu_host: list[float] = []
        working: list[float] = []
        private: list[float] = []

        for sample in samples:
            process = sample.get(
                key
            )

            if not isinstance(
                process,
                dict,
            ):
                continue

            one = process.get(
                "cpu_one_core_percent"
            )
            host = process.get(
                "cpu_total_host_percent"
            )
            ws = process.get(
                "working_set_mib"
            )
            private_value = (
                process.get(
                    "private_mib"
                )
            )

            if isinstance(
                one,
                (int, float),
            ):
                cpu_one.append(
                    float(one)
                )

            if isinstance(
                host,
                (int, float),
            ):
                cpu_host.append(
                    float(host)
                )

            if isinstance(
                ws,
                (int, float),
            ):
                working.append(
                    float(ws)
                )

            if isinstance(
                private_value,
                (int, float),
            ):
                private.append(
                    float(
                        private_value
                    )
                )

        def stats(
            values: list[float],
        ) -> dict[str, float]:
            if not values:
                return {
                    "avg": 0.0,
                    "max": 0.0,
                }

            return {
                "avg": round(
                    sum(values)
                    / len(values),
                    3,
                ),
                "max": round(
                    max(values),
                    3,
                ),
            }

        return {
            "cpu_one_core_percent": stats(
                cpu_one
            ),
            "cpu_total_host_percent": stats(
                cpu_host
            ),
            "working_set_mib": stats(
                working
            ),
            "private_mib": stats(
                private
            ),
        }

    def _payload(
        self,
        final: bool,
    ) -> dict[str, Any]:
        with self._lock:
            samples = list(
                self._samples
            )
            path = self._path
            capture_target = (
                dict(
                    self._capture_target
                )
                if self._capture_target
                is not None
                else None
            )
            error = self._error

        latest_wgc = None

        for sample in reversed(
            samples
        ):
            if isinstance(
                sample.get("wgc"),
                dict,
            ):
                latest_wgc = (
                    sample["wgc"]
                )
                break

        duration_ms = (
            int(
                samples[-1][
                    "elapsed_ms"
                ]
            )
            if samples
            else 0
        )

        return {
            "schema": (
                "privyhub_native_host_telemetry_v1"
            ),
            "profiler_version": (
                self.VERSION
            ),
            "final": bool(final),
            "sample_interval_seconds": (
                SAMPLE_INTERVAL_SECONDS
            ),
            "logical_cpu_count": max(
                1,
                os.cpu_count() or 1,
            ),
            "duration_ms": duration_ms,
            "capture_target": (
                capture_target
            ),
            "processes": {
                "capture": {
                    "pid": (
                        self._capture_pid
                    ),
                    **self._aggregate_process(
                        samples,
                        "capture_process",
                    ),
                },
                "ffmpeg": {
                    "pid": (
                        self._ffmpeg_pid
                    ),
                    **self._aggregate_process(
                        samples,
                        "ffmpeg_process",
                    ),
                },
            },
            "latest_wgc": latest_wgc,
            "sample_count": len(
                samples
            ),
            "samples": samples,
            "error": error,
            "path": (
                str(path)
                if path is not None
                else ""
            ),
        }

    def _persist(
        self,
        final: bool,
    ) -> None:
        with self._lock:
            path = self._path

        if path is None:
            return

        _atomic_json(
            path,
            self._payload(
                final=final
            ),
        )
