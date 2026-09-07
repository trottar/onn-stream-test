from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import threading
import time

from pathlib import Path
from ctypes import wintypes


TARGET_FPS = 60.0
FRAME_PERIOD_NS = int(1_000_000_000 / TARGET_FPS)
SOURCE_TICK_TO_MS = 1.0 / 10_000.0

# Passive capture-compatibility diagnostics. These values do not
# alter WGC, FFmpeg, FEC, decoder, audio, or controller behavior.
DIAGNOSTIC_INTERVAL_SECONDS = 5.0
BLACK_SAMPLE_EVERY_CALLBACKS = 300
BLACK_SAMPLE_PIXEL_BUDGET = 2048
NEAR_BLACK_MEAN_RGB = 4.0
NEAR_BLACK_NONBLACK_FRACTION = 0.01


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _install_runtime_path() -> Path:
    runtime = (
        _project_root()
        / "runtime"
        / "streaming"
        / "wgc_python"
    )

    sys.path.insert(
        0,
        str(runtime),
    )

    return runtime


def _atomic_json(
    path: Path,
    payload: dict[str, object],
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


def _write_all(
    descriptor: int,
    data: bytes,
) -> None:
    view = memoryview(data)

    while view:
        written = os.write(
            descriptor,
            view,
        )

        if written <= 0:
            raise BrokenPipeError(
                "Raw video pipe closed"
            )

        view = view[written:]


def _sample_bgra_content(
    payload: bytes,
    width: int,
    height: int,
) -> dict[str, object]:
    pixel_count = max(
        1,
        width * height,
    )

    step = max(
        1,
        pixel_count // BLACK_SAMPLE_PIXEL_BUDGET,
    )

    view = memoryview(
        payload
    )

    total_rgb = 0
    sampled = 0
    nonblack = 0
    minimum_rgb = 255
    maximum_rgb = 0

    pixel_index = 0

    while (
        pixel_index < pixel_count
        and sampled < BLACK_SAMPLE_PIXEL_BUDGET
    ):
        offset = (
            pixel_index *
            4
        )

        if (
            offset + 2 >=
            len(view)
        ):
            break

        blue = int(
            view[offset]
        )
        green = int(
            view[
                offset +
                1
            ]
        )
        red = int(
            view[
                offset +
                2
            ]
        )

        sample_rgb = (
            blue +
            green +
            red
        ) // 3

        total_rgb += (
            blue +
            green +
            red
        )

        minimum_rgb = min(
            minimum_rgb,
            sample_rgb,
        )

        maximum_rgb = max(
            maximum_rgb,
            sample_rgb,
        )

        if (
            max(
                blue,
                green,
                red,
            ) >
            12
        ):
            nonblack += 1

        sampled += 1
        pixel_index += step

    if sampled <= 0:
        return {
            "sampled_pixels": 0,
            "mean_rgb": 0.0,
            "nonblack_fraction": 0.0,
            "min_rgb": 0,
            "max_rgb": 0,
            "near_black": True,
        }

    mean_rgb = (
        total_rgb /
        (
            sampled *
            3.0
        )
    )

    nonblack_fraction = (
        nonblack /
        sampled
    )

    near_black = (
        mean_rgb <=
        NEAR_BLACK_MEAN_RGB
        and
        nonblack_fraction <=
        NEAR_BLACK_NONBLACK_FRACTION
    )

    return {
        "sampled_pixels": sampled,
        "mean_rgb": round(
            mean_rgb,
            3,
        ),
        "nonblack_fraction": round(
            nonblack_fraction,
            6,
        ),
        "min_rgb": minimum_rgb,
        "max_rgb": maximum_rgb,
        "near_black": near_black,
    }


def _normalize_bgra_to_envelope(
    frame_buffer,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
    cv2,
    np,
) -> tuple[bytes, str]:
    if (
        source_width <= 0
        or source_height <= 0
        or target_width <= 0
        or target_height <= 0
    ):
        raise ValueError(
            "Invalid WGC normalization dimensions"
        )

    width_delta = (
        abs(
            source_width -
            target_width
        )
        /
        max(
            1,
            target_width,
        )
    )

    height_delta = (
        abs(
            source_height -
            target_height
        )
        /
        max(
            1,
            target_height,
        )
    )

    if max(
        width_delta,
        height_delta,
    ) <= 0.15:
        # Fast case: the resized WGC surface is at least as large as the
        # original raw-video envelope in both dimensions. Center-crop directly
        # from the WGC ndarray and pack once into the immutable latest-frame
        # bytes object. This removes the former full-frame zero canvas and
        # extra ndarray copy. The 941x763 -> 881x763 compatibility case uses
        # this path.
        if (
            source_width >= target_width
            and source_height >= target_height
        ):
            source_x = (
                source_width -
                target_width
            ) // 2

            source_y = (
                source_height -
                target_height
            ) // 2

            return (
                frame_buffer[
                    source_y:
                        source_y +
                        target_height,
                    source_x:
                        source_x +
                        target_width,
                    :,
                ].tobytes(
                    order="C"
                ),
                "direct_crop",
            )

        # Padding is required when one or both source dimensions are smaller
        # than the fixed raw-video envelope. Keep the proven compatibility
        # behavior for that less common case.
        canvas = np.zeros(
            (
                target_height,
                target_width,
                4,
            ),
            dtype=np.uint8,
        )

        canvas[
            :,
            :,
            3
        ] = 255

        copy_width = min(
            source_width,
            target_width,
        )
        copy_height = min(
            source_height,
            target_height,
        )

        source_x = max(
            0,
            (
                source_width -
                copy_width
            ) //
            2,
        )
        source_y = max(
            0,
            (
                source_height -
                copy_height
            ) //
            2,
        )

        target_x = max(
            0,
            (
                target_width -
                copy_width
            ) //
            2,
        )
        target_y = max(
            0,
            (
                target_height -
                copy_height
            ) //
            2,
        )

        canvas[
            target_y:
                target_y +
                copy_height,
            target_x:
                target_x +
                copy_width,
            :,
        ] = frame_buffer[
            source_y:
                source_y +
                copy_height,
            source_x:
                source_x +
                copy_width,
            :,
        ]

        return (
            canvas.tobytes(
                order="C"
            ),
            "center_crop_pad",
        )

    scale = min(
        target_width /
            source_width,
        target_height /
            source_height,
    )

    resized_width = max(
        1,
        min(
            target_width,
            int(
                round(
                    source_width *
                    scale
                )
            ),
        ),
    )

    resized_height = max(
        1,
        min(
            target_height,
            int(
                round(
                    source_height *
                    scale
                )
            ),
        ),
    )

    interpolation = (
        cv2.INTER_AREA
        if scale < 1.0
        else cv2.INTER_LINEAR
    )

    resized = cv2.resize(
        frame_buffer,
        (
            resized_width,
            resized_height,
        ),
        interpolation=interpolation,
    )

    canvas = np.zeros(
        (
            target_height,
            target_width,
            4,
        ),
        dtype=np.uint8,
    )

    canvas[
        :,
        :,
        3
    ] = 255

    target_x = (
        target_width -
        resized_width
    ) // 2

    target_y = (
        target_height -
        resized_height
    ) // 2

    canvas[
        target_y:
            target_y +
            resized_height,
        target_x:
            target_x +
            resized_width,
        :,
    ] = resized

    return (
        canvas.tobytes(
            order="C"
        ),
        "aspect_fit",
    )


def _window_probe(
    hwnd: int,
    owner_pid_hint: int = 0,
) -> dict[str, object]:
    if os.name != "nt":
        return {
            "probe_ok": False,
            "error": "not_windows",
        }

    user32 = ctypes.WinDLL(
        "user32",
        use_last_error=True,
    )

    user32.IsWindow.argtypes = [
        wintypes.HWND,
    ]
    user32.IsWindow.restype = wintypes.BOOL

    user32.IsWindowVisible.argtypes = [
        wintypes.HWND,
    ]
    user32.IsWindowVisible.restype = wintypes.BOOL

    user32.IsIconic.argtypes = [
        wintypes.HWND,
    ]
    user32.IsIconic.restype = wintypes.BOOL

    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(
            wintypes.DWORD
        ),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    user32.GetWindowTextLengthW.argtypes = [
        wintypes.HWND,
    ]
    user32.GetWindowTextLengthW.restype = ctypes.c_int

    user32.GetWindowTextW.argtypes = [
        wintypes.HWND,
        wintypes.LPWSTR,
        ctypes.c_int,
    ]
    user32.GetWindowTextW.restype = ctypes.c_int

    user32.GetClientRect.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(
            wintypes.RECT
        ),
    ]
    user32.GetClientRect.restype = wintypes.BOOL

    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.LPARAM,
    )

    user32.EnumWindows.argtypes = [
        callback_type,
        wintypes.LPARAM,
    ]
    user32.EnumWindows.restype = wintypes.BOOL

    def title_for(
        target_hwnd: int,
    ) -> str:
        length = user32.GetWindowTextLengthW(
            target_hwnd
        )

        if length <= 0:
            return ""

        buffer = ctypes.create_unicode_buffer(
            length + 1
        )

        if (
            user32.GetWindowTextW(
                target_hwnd,
                buffer,
                len(buffer),
            )
            <= 0
        ):
            return ""

        return buffer.value

    def client_size(
        target_hwnd: int,
    ) -> tuple[int, int]:
        rect = wintypes.RECT()

        if not user32.GetClientRect(
            target_hwnd,
            ctypes.byref(
                rect
            ),
        ):
            return (
                0,
                0,
            )

        return (
            max(
                0,
                int(
                    rect.right -
                    rect.left
                ),
            ),
            max(
                0,
                int(
                    rect.bottom -
                    rect.top
                ),
            ),
        )

    captured_exists = bool(
        user32.IsWindow(
            hwnd
        )
    )

    pid = int(
        owner_pid_hint
    )

    if captured_exists:
        process_id = wintypes.DWORD()

        user32.GetWindowThreadProcessId(
            hwnd,
            ctypes.byref(
                process_id
            ),
        )

        if process_id.value > 0:
            pid = int(
                process_id.value
            )

    captured_width = 0
    captured_height = 0

    if captured_exists:
        (
            captured_width,
            captured_height,
        ) = client_size(
            hwnd
        )

    matches: list[
        dict[str, object]
    ] = []

    if pid > 0:
        @callback_type
        def visit(
            candidate_hwnd: int,
            _lparam: int,
        ) -> bool:
            try:
                candidate_pid = (
                    wintypes.DWORD()
                )

                user32.GetWindowThreadProcessId(
                    candidate_hwnd,
                    ctypes.byref(
                        candidate_pid
                    ),
                )

                if (
                    int(
                        candidate_pid.value
                    ) !=
                    pid
                ):
                    return True

                if not user32.IsWindowVisible(
                    candidate_hwnd
                ):
                    return True

                (
                    width,
                    height,
                ) = client_size(
                    candidate_hwnd
                )

                if (
                    width < 64
                    or height < 64
                ):
                    return True

                matches.append(
                    {
                        "hwnd": int(
                            candidate_hwnd
                        ),
                        "title": title_for(
                            candidate_hwnd
                        ),
                        "width": width,
                        "height": height,
                        "area": (
                            width *
                            height
                        ),
                    }
                )
            except Exception:
                return True

            return True

        try:
            user32.EnumWindows(
                visit,
                0,
            )
        except Exception:
            pass

    largest = (
        max(
            matches,
            key=lambda item: int(
                item["area"]
            ),
        )
        if matches
        else None
    )

    return {
        "probe_ok": True,
        "captured_hwnd": int(
            hwnd
        ),
        "owner_pid": pid,
        "captured_exists": (
            captured_exists
        ),
        "captured_visible": (
            bool(
                user32.IsWindowVisible(
                    hwnd
                )
            )
            if captured_exists
            else False
        ),
        "captured_iconic": (
            bool(
                user32.IsIconic(
                    hwnd
                )
            )
            if captured_exists
            else False
        ),
        "captured_title": (
            title_for(
                hwnd
            )
            if captured_exists
            else ""
        ),
        "captured_client_width": (
            captured_width
        ),
        "captured_client_height": (
            captured_height
        ),
        "visible_owner_windows": len(
            matches
        ),
        "largest_visible_hwnd": (
            int(
                largest["hwnd"]
            )
            if largest is not None
            else 0
        ),
        "largest_visible_title": (
            str(
                largest["title"]
            )
            if largest is not None
            else ""
        ),
        "largest_visible_width": (
            int(
                largest["width"]
            )
            if largest is not None
            else 0
        ),
        "largest_visible_height": (
            int(
                largest["height"]
            )
            if largest is not None
            else 0
        ),
        "largest_matches_capture": (
            (
                int(
                    largest["hwnd"]
                ) ==
                int(
                    hwnd
                )
            )
            if largest is not None
            else False
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "PrivyHub Windows Graphics Capture "
            "latest-frame low-latency bridge"
        )
    )

    parser.add_argument(
        "--hwnd",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--meta",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    runtime = _install_runtime_path()

    if not runtime.is_dir():
        print(
            "PrivyHub WGC runtime is missing: "
            f"{runtime}",
            file=sys.stderr,
            flush=True,
        )
        return 2

    try:
        from windows_capture import (
            Frame,
            InternalCaptureControl,
            WindowsCapture,
        )

        import cv2
        import numpy as np
    except Exception as exc:
        print(
            "Unable to import the project-local "
            f"Windows Graphics Capture runtime: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 3

    if args.hwnd <= 0:
        print(
            "Invalid RetroArch HWND",
            file=sys.stderr,
            flush=True,
        )
        return 4

    stdout_fd = sys.stdout.fileno()

    if os.name == "nt":
        import msvcrt

        msvcrt.setmode(
            stdout_fd,
            os.O_BINARY,
        )

    slot_lock = threading.Condition()
    stop_event = threading.Event()

    source_width = 0
    source_height = 0
    expected_bytes = 0

    latest_frame: bytes | None = None
    latest_generation = 0
    last_written_generation = 0

    previous_source_timespan = 0

    callbacks = 0
    callback_bytes = 0
    overwritten_frames = 0
    size_mismatch_frames = 0
    size_mismatch_drops = 0
    normalized_size_frames = 0
    normalization_direct_crop_frames = 0
    normalization_crop_pad_frames = 0
    normalization_scaled_frames = 0
    normalization_failures = 0
    emitted_frames = 0
    duplicated_emits = 0
    late_ticks = 0

    copy_time_total_ms = 0.0
    copy_time_max_ms = 0.0
    write_time_total_ms = 0.0
    write_time_max_ms = 0.0

    report_started = time.perf_counter()
    report_callbacks = 0
    report_emitted = 0
    report_overwritten = 0
    report_mismatch = 0
    report_duplicates = 0
    report_late_ticks = 0
    report_source_delta_samples = 0
    report_source_delta_total_ms = 0.0
    report_source_delta_min_ms = 1_000_000.0
    report_source_delta_max_ms = 0.0
    report_copy_ms = 0.0
    report_write_ms = 0.0

    diagnostic_archive_path = (
        _project_root()
        / "logs"
        / "games"
        / "capture_diagnostics"
        / (
            "wgc_"
            + time.strftime(
                "%Y%m%d_%H%M%S"
            )
            + "_"
            + str(
                int(
                    args.hwnd
                )
            )
            + ".json"
        )
    )

    diagnostics: dict[str, object] = {
        "version": (
            "PrivyHub WGC Capture Hotpath Optimization v0.14"
        ),
        "dynamic_size_fix": True,
        "capture_hotpath_optimized": True,
        "normalization_policy": (
            "small_direct_crop_or_pad_large_aspect_fit"
        ),
        "started_unix_ms": int(
            time.time() *
            1000.0
        ),
        "latest_callback_width": 0,
        "latest_callback_height": 0,
        "first_mismatch_width": 0,
        "first_mismatch_height": 0,
        "last_mismatch_width": 0,
        "last_mismatch_height": 0,
        "content_samples": 0,
        "near_black_samples": 0,
        "current_near_black_streak_samples": 0,
        "max_near_black_streak_samples": 0,
        "last_sample_mean_rgb": 0.0,
        "last_sample_nonblack_fraction": 0.0,
        "last_sample_min_rgb": 0,
        "last_sample_max_rgb": 0,
        "owner_pid": 0,
        "window_probe_count": 0,
        "captured_invalid_observations": 0,
        "alternative_hwnd_observations": 0,
        "largest_hwnd_changes": 0,
        "last_largest_hwnd": 0,
    }

    meta_lock = threading.Lock()

    def writer_loop() -> None:
        nonlocal last_written_generation
        nonlocal emitted_frames
        nonlocal duplicated_emits
        nonlocal late_ticks
        nonlocal write_time_total_ms
        nonlocal write_time_max_ms
        nonlocal report_emitted
        nonlocal report_duplicates
        nonlocal report_late_ticks
        nonlocal report_write_ms

        next_tick_ns = 0

        while not stop_event.is_set():
            with slot_lock:
                while (
                    not stop_event.is_set()
                    and latest_frame is None
                ):
                    slot_lock.wait(timeout=0.050)

                if stop_event.is_set():
                    return

                if next_tick_ns == 0:
                    next_tick_ns = time.perf_counter_ns()

            now_ns = time.perf_counter_ns()
            remaining_ns = next_tick_ns - now_ns

            if remaining_ns > 0:
                if remaining_ns > 400_000:
                    time.sleep(
                        (remaining_ns - 250_000)
                        / 1_000_000_000.0
                    )

                while (
                    not stop_event.is_set()
                    and time.perf_counter_ns() < next_tick_ns
                ):
                    time.sleep(0)

            if stop_event.is_set():
                return

            now_ns = time.perf_counter_ns()
            lateness_ns = now_ns - next_tick_ns

            if lateness_ns > FRAME_PERIOD_NS:
                missed = max(
                    1,
                    lateness_ns // FRAME_PERIOD_NS,
                )

                late_ticks += int(missed)
                report_late_ticks += int(missed)

                # Never catch up by bursting stale frames.
                next_tick_ns = now_ns

            with slot_lock:
                payload = latest_frame
                generation = latest_generation

            if payload is None:
                next_tick_ns += FRAME_PERIOD_NS
                continue

            is_duplicate = (
                generation == last_written_generation
            )

            started = time.perf_counter()

            try:
                _write_all(
                    stdout_fd,
                    payload,
                )
            except (
                BrokenPipeError,
                OSError,
            ):
                stop_event.set()
                return

            write_ms = (
                time.perf_counter()
                - started
            ) * 1000.0

            write_time_total_ms += write_ms
            write_time_max_ms = max(
                write_time_max_ms,
                write_ms,
            )
            report_write_ms += write_ms

            emitted_frames += 1
            report_emitted += 1

            if is_duplicate:
                duplicated_emits += 1
                report_duplicates += 1
            else:
                last_written_generation = generation

            next_tick_ns += FRAME_PERIOD_NS

    writer = threading.Thread(
        target=writer_loop,
        name="PrivyHub-WGC-Writer",
        daemon=True,
    )
    writer.start()

    def write_diagnostic_snapshot() -> None:
        owner_pid_hint = int(
            diagnostics.get(
                "owner_pid",
                0,
            )
        )

        probe = _window_probe(
            int(
                args.hwnd
            ),
            owner_pid_hint,
        )

        if bool(
            probe.get(
                "probe_ok",
                False,
            )
        ):
            diagnostics[
                "window_probe_count"
            ] = int(
                diagnostics[
                    "window_probe_count"
                ]
            ) + 1

            owner_pid = int(
                probe.get(
                    "owner_pid",
                    0,
                )
            )

            if owner_pid > 0:
                diagnostics[
                    "owner_pid"
                ] = owner_pid

            if not bool(
                probe.get(
                    "captured_exists",
                    False,
                )
            ):
                diagnostics[
                    "captured_invalid_observations"
                ] = int(
                    diagnostics[
                        "captured_invalid_observations"
                    ]
                ) + 1

            largest_hwnd = int(
                probe.get(
                    "largest_visible_hwnd",
                    0,
                )
            )

            if (
                largest_hwnd > 0
                and largest_hwnd !=
                int(
                    args.hwnd
                )
            ):
                diagnostics[
                    "alternative_hwnd_observations"
                ] = int(
                    diagnostics[
                        "alternative_hwnd_observations"
                    ]
                ) + 1

            previous_largest = int(
                diagnostics.get(
                    "last_largest_hwnd",
                    0,
                )
            )

            if (
                previous_largest > 0
                and largest_hwnd > 0
                and largest_hwnd !=
                previous_largest
            ):
                diagnostics[
                    "largest_hwnd_changes"
                ] = int(
                    diagnostics[
                        "largest_hwnd_changes"
                    ]
                ) + 1

            if largest_hwnd > 0:
                diagnostics[
                    "last_largest_hwnd"
                ] = largest_hwnd

        if source_width <= 0:
            return probe

        payload = {
            "ok": True,
            "backend": (
                "windows_graphics_capture"
            ),
            "bridge": (
                "latest_frame_60hz_cadence_lock"
            ),
            "diagnostic_version": (
                "capture_hotpath_v0.14"
            ),
            "pixel_format": "bgra",
            "width": source_width,
            "height": source_height,
            "source_width": source_width,
            "source_height": source_height,
            "hwnd": int(
                args.hwnd
            ),
            "target_fps": TARGET_FPS,
            "callbacks": callbacks,
            "callback_bytes": callback_bytes,
            "emitted_frames": emitted_frames,
            "duplicated_emits": duplicated_emits,
            "overwritten_frames": overwritten_frames,
            "size_mismatch_frames": size_mismatch_frames,
            "size_mismatch_drops": size_mismatch_drops,
            "normalized_size_frames": normalized_size_frames,
            "normalization_direct_crop_frames": (
                normalization_direct_crop_frames
            ),
            "normalization_crop_pad_frames": (
                normalization_crop_pad_frames
            ),
            "normalization_scaled_frames": (
                normalization_scaled_frames
            ),
            "normalization_failures": normalization_failures,
            "late_ticks": late_ticks,
            "frame_bytes": expected_bytes,
            "raw_bytes_emitted": (
                emitted_frames *
                expected_bytes
            ),
            "copy_time_total_ms": round(
                copy_time_total_ms,
                3,
            ),
            "copy_time_avg_ms": round(
                copy_time_total_ms /
                max(
                    1,
                    callbacks,
                ),
                4,
            ),
            "copy_time_max_ms": round(
                copy_time_max_ms,
                3,
            ),
            "write_time_total_ms": round(
                write_time_total_ms,
                3,
            ),
            "write_time_avg_ms": round(
                write_time_total_ms /
                max(
                    1,
                    emitted_frames,
                ),
                4,
            ),
            "write_time_max_ms": round(
                write_time_max_ms,
                3,
            ),
            "diagnostics": dict(
                diagnostics
            ),
            "window": probe,
            "archive_path": str(
                diagnostic_archive_path
            ),
            "updated_unix_ms": int(
                time.time() *
                1000.0
            ),
        }

        with meta_lock:
            _atomic_json(
                args.meta,
                payload,
            )

            _atomic_json(
                diagnostic_archive_path,
                payload,
            )

        return probe

    def diagnostic_loop() -> None:
        last_warning_state = None

        while not stop_event.wait(
            DIAGNOSTIC_INTERVAL_SECONDS
        ):
            try:
                probe = write_diagnostic_snapshot()

                if (
                    source_width <= 0
                    or probe is None
                ):
                    continue

                warning_state = (
                    bool(
                        probe.get(
                            "captured_exists",
                            False,
                        )
                    ),
                    int(
                        probe.get(
                            "largest_visible_hwnd",
                            0,
                        )
                    ),
                    int(
                        diagnostics.get(
                            "current_near_black_streak_samples",
                            0,
                        )
                    ),
                    size_mismatch_frames,
                )

                if (
                    warning_state !=
                    last_warning_state
                    and (
                        not warning_state[0]
                        or (
                            warning_state[1] > 0
                            and warning_state[1] !=
                            int(
                                args.hwnd
                            )
                        )
                        or warning_state[2] >= 3
                        or warning_state[3] > 0
                    )
                ):
                    print(
                        "WGC diagnostic event: "
                        f"captured_exists={warning_state[0]} "
                        f"largest_hwnd={warning_state[1]} "
                        f"captured_hwnd={args.hwnd} "
                        f"black_streak_samples={warning_state[2]} "
                        f"size_mismatch_frames={warning_state[3]} "
                        f"normalized={normalized_size_frames} "
                        f"normalization_failures={normalization_failures}",
                        file=sys.stderr,
                        flush=True,
                    )

                    last_warning_state = (
                        warning_state
                    )

            except Exception as exc:
                print(
                    "WGC diagnostic snapshot error: "
                    f"{exc}",
                    file=sys.stderr,
                    flush=True,
                )

    diagnostic = threading.Thread(
        target=diagnostic_loop,
        name="PrivyHub-WGC-Diagnostic",
        daemon=True,
    )
    diagnostic.start()

    print(
        "PrivyHub WGC Capture Hotpath Optimization v0.14 active; "
        "stable-size semantics unchanged",
        file=sys.stderr,
        flush=True,
    )

    capture = WindowsCapture(
        cursor_capture=False,
        draw_border=None,
        secondary_window=None,
        minimum_update_interval=None,
        dirty_region=None,
        monitor_index=None,
        window_name=None,
        window_hwnd=args.hwnd,
    )

    @capture.event
    def on_frame_arrived(
        frame: Frame,
        capture_control: InternalCaptureControl,
    ) -> None:
        nonlocal source_width
        nonlocal source_height
        nonlocal expected_bytes
        nonlocal latest_frame
        nonlocal latest_generation
        nonlocal previous_source_timespan
        nonlocal callbacks
        nonlocal callback_bytes
        nonlocal overwritten_frames
        nonlocal size_mismatch_frames
        nonlocal size_mismatch_drops
        nonlocal normalized_size_frames
        nonlocal normalization_direct_crop_frames
        nonlocal normalization_crop_pad_frames
        nonlocal normalization_scaled_frames
        nonlocal normalization_failures
        nonlocal copy_time_total_ms
        nonlocal copy_time_max_ms
        nonlocal report_started
        nonlocal report_callbacks
        nonlocal report_emitted
        nonlocal report_overwritten
        nonlocal report_mismatch
        nonlocal report_duplicates
        nonlocal report_late_ticks
        nonlocal report_source_delta_samples
        nonlocal report_source_delta_total_ms
        nonlocal report_source_delta_min_ms
        nonlocal report_source_delta_max_ms
        nonlocal report_copy_ms
        nonlocal report_write_ms

        try:
            width = int(
                frame.width
            )
            height = int(
                frame.height
            )

            if (
                width <= 0
                or height <= 0
            ):
                return

            diagnostics[
                "latest_callback_width"
            ] = width
            diagnostics[
                "latest_callback_height"
            ] = height

            if source_width == 0:
                source_width = width
                source_height = height
                expected_bytes = (
                    width
                    * height
                    * 4
                )

                _atomic_json(
                    args.meta,
                    {
                        "ok": True,
                        "backend": (
                            "windows_graphics_capture"
                        ),
                        "bridge": (
                            "latest_frame_60hz_cadence_lock"
                        ),
                        "pixel_format": "bgra",
                        "width": width,
                        "height": height,
                        "source_width": width,
                        "source_height": height,
                        "hwnd": int(args.hwnd),
                        "target_fps": TARGET_FPS,
                    },
                )

                print(
                    "WGC first source frame: "
                    f"{width}x{height} BGRA "
                    f"({expected_bytes} bytes/frame) "
                    f"hwnd={args.hwnd}",
                    file=sys.stderr,
                    flush=True,
                )

                print(
                    "WGC queue: latest-frame-only; "
                    "capture callback never waits for FFmpeg",
                    file=sys.stderr,
                    flush=True,
                )

                print(
                    "WGC cadence v0.7.2: fixed 60 Hz encoder feed; "
                    "reuse latest complete frame when no newer WGC "
                    "frame is available",
                    file=sys.stderr,
                    flush=True,
                )

            needs_size_normalization = (
                width != source_width
                or height != source_height
            )

            if needs_size_normalization:
                size_mismatch_frames += 1
                report_mismatch += 1

                if int(
                    diagnostics[
                        "first_mismatch_width"
                    ]
                ) <= 0:
                    diagnostics[
                        "first_mismatch_width"
                    ] = width
                    diagnostics[
                        "first_mismatch_height"
                    ] = height

                diagnostics[
                    "last_mismatch_width"
                ] = width
                diagnostics[
                    "last_mismatch_height"
                ] = height

                if (
                    size_mismatch_frames <= 3
                    or size_mismatch_frames % 600 == 0
                ):
                    print(
                        "WGC size-change frame will be normalized: "
                        f"{width}x{height} -> "
                        f"{source_width}x{source_height}",
                        file=sys.stderr,
                        flush=True,
                    )

            source_timespan = int(
                getattr(
                    frame,
                    "timespan",
                    0,
                )
            )

            if (
                source_timespan > 0
                and previous_source_timespan > 0
                and source_timespan > previous_source_timespan
            ):
                delta_ms = (
                    source_timespan
                    - previous_source_timespan
                ) * SOURCE_TICK_TO_MS

                if 0.0 < delta_ms < 250.0:
                    report_source_delta_samples += 1
                    report_source_delta_total_ms += delta_ms
                    report_source_delta_min_ms = min(
                        report_source_delta_min_ms,
                        delta_ms,
                    )
                    report_source_delta_max_ms = max(
                        report_source_delta_max_ms,
                        delta_ms,
                    )

            if source_timespan > 0:
                previous_source_timespan = source_timespan

            started = time.perf_counter()

            if needs_size_normalization:
                try:
                    (
                        payload,
                        normalization_strategy,
                    ) = _normalize_bgra_to_envelope(
                        frame.frame_buffer,
                        width,
                        height,
                        source_width,
                        source_height,
                        cv2,
                        np,
                    )

                    normalized_size_frames += 1

                    if (
                        normalization_strategy ==
                        "direct_crop"
                    ):
                        normalization_direct_crop_frames += 1
                    elif (
                        normalization_strategy ==
                        "center_crop_pad"
                    ):
                        normalization_crop_pad_frames += 1
                    else:
                        normalization_scaled_frames += 1

                except Exception as exc:
                    normalization_failures += 1
                    size_mismatch_drops += 1

                    if (
                        normalization_failures <= 3
                        or normalization_failures % 120 == 0
                    ):
                        print(
                            "WGC dynamic-size normalization failed: "
                            f"{exc}",
                            file=sys.stderr,
                            flush=True,
                        )

                    return
            else:
                payload = frame.frame_buffer.tobytes(
                    order="C"
                )

            copy_ms = (
                time.perf_counter()
                - started
            ) * 1000.0

            if len(payload) != expected_bytes:
                size_mismatch_drops += 1
                normalization_failures += 1
                return

            callbacks += 1
            report_callbacks += 1
            callback_bytes += len(
                payload
            )

            if (
                callbacks %
                BLACK_SAMPLE_EVERY_CALLBACKS
                == 0
            ):
                sample = _sample_bgra_content(
                    payload,
                    source_width,
                    source_height,
                )

                diagnostics[
                    "content_samples"
                ] = int(
                    diagnostics[
                        "content_samples"
                    ]
                ) + 1

                diagnostics[
                    "last_sample_mean_rgb"
                ] = sample[
                    "mean_rgb"
                ]
                diagnostics[
                    "last_sample_nonblack_fraction"
                ] = sample[
                    "nonblack_fraction"
                ]
                diagnostics[
                    "last_sample_min_rgb"
                ] = sample[
                    "min_rgb"
                ]
                diagnostics[
                    "last_sample_max_rgb"
                ] = sample[
                    "max_rgb"
                ]

                if bool(
                    sample[
                        "near_black"
                    ]
                ):
                    diagnostics[
                        "near_black_samples"
                    ] = int(
                        diagnostics[
                            "near_black_samples"
                        ]
                    ) + 1

                    streak = int(
                        diagnostics[
                            "current_near_black_streak_samples"
                        ]
                    ) + 1

                    diagnostics[
                        "current_near_black_streak_samples"
                    ] = streak

                    diagnostics[
                        "max_near_black_streak_samples"
                    ] = max(
                        int(
                            diagnostics[
                                "max_near_black_streak_samples"
                            ]
                        ),
                        streak,
                    )
                else:
                    diagnostics[
                        "current_near_black_streak_samples"
                    ] = 0

            copy_time_total_ms += copy_ms
            copy_time_max_ms = max(
                copy_time_max_ms,
                copy_ms,
            )
            report_copy_ms += copy_ms

            with slot_lock:
                if (
                    latest_generation !=
                    last_written_generation
                ):
                    overwritten_frames += 1
                    report_overwritten += 1

                latest_frame = payload
                latest_generation += 1
                slot_lock.notify()

            now = time.perf_counter()
            elapsed = (
                now - report_started
            )

            if elapsed >= 5.0:
                callback_fps = (
                    report_callbacks /
                    elapsed
                )

                emit_fps = (
                    report_emitted /
                    elapsed
                )

                avg_copy = (
                    report_copy_ms /
                    max(
                        1,
                        report_callbacks,
                    )
                )

                avg_write = (
                    report_write_ms /
                    max(
                        1,
                        report_emitted,
                    )
                )

                avg_source_delta = (
                    report_source_delta_total_ms
                    / max(
                        1,
                        report_source_delta_samples,
                    )
                )

                source_min = (
                    report_source_delta_min_ms
                    if report_source_delta_samples > 0
                    else 0.0
                )

                source_max = (
                    report_source_delta_max_ms
                    if report_source_delta_samples > 0
                    else 0.0
                )

                print(
                    "WGC perf: "
                    f"callback={callback_fps:.1f}fps "
                    f"emit={emit_fps:.1f}fps "
                    f"duplicate={report_duplicates} "
                    f"overwritten={report_overwritten} "
                    f"late_ticks={report_late_ticks} "
                    f"source_dt={avg_source_delta:.2f}ms "
                    f"[{source_min:.2f},{source_max:.2f}] "
                    f"size_change={report_mismatch} "
                    f"normalized={normalized_size_frames} "
                    f"norm_fail={normalization_failures} "
                    f"copy_avg={avg_copy:.2f}ms "
                    f"copy_max={copy_time_max_ms:.2f}ms "
                    f"pipe_avg={avg_write:.2f}ms "
                    f"pipe_max={write_time_max_ms:.2f}ms",
                    file=sys.stderr,
                    flush=True,
                )

                report_started = now
                report_callbacks = 0
                report_emitted = 0
                report_overwritten = 0
                report_mismatch = 0
                report_duplicates = 0
                report_late_ticks = 0
                report_source_delta_samples = 0
                report_source_delta_total_ms = 0.0
                report_source_delta_min_ms = 1_000_000.0
                report_source_delta_max_ms = 0.0
                report_copy_ms = 0.0
                report_write_ms = 0.0

        except Exception as exc:
            print(
                f"WGC frame error: {exc}",
                file=sys.stderr,
                flush=True,
            )
            stop_event.set()
            capture_control.stop()

    @capture.event
    def on_closed() -> None:
        print(
            "WGC capture item closed",
            file=sys.stderr,
            flush=True,
        )
        stop_event.set()

    try:
        capture.start()
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(
            f"WGC capture failed: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 5
    finally:
        stop_event.set()

        with slot_lock:
            slot_lock.notify_all()

        try:
            write_diagnostic_snapshot()
        except Exception:
            pass

        writer.join(
            timeout=1.0
        )

        diagnostic.join(
            timeout=1.0
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
