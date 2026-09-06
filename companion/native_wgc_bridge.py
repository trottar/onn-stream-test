from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time

from pathlib import Path


TARGET_FPS = 60.0
FRAME_PERIOD_NS = int(1_000_000_000 / TARGET_FPS)
SOURCE_TICK_TO_MS = 1.0 / 10_000.0


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
    size_mismatch_drops = 0
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
        nonlocal size_mismatch_drops
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

            if (
                width != source_width
                or height != source_height
            ):
                size_mismatch_drops += 1
                report_mismatch += 1

                if (
                    size_mismatch_drops <= 3
                    or size_mismatch_drops % 120 == 0
                ):
                    print(
                        "WGC size-change frame dropped: "
                        f"{width}x{height}; "
                        f"stream envelope remains "
                        f"{source_width}x{source_height}",
                        file=sys.stderr,
                        flush=True,
                    )

                return

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

            payload = frame.frame_buffer.tobytes(
                order="C"
            )

            copy_ms = (
                time.perf_counter()
                - started
            ) * 1000.0

            if len(payload) != expected_bytes:
                size_mismatch_drops += 1
                report_mismatch += 1
                return

            callbacks += 1
            report_callbacks += 1
            callback_bytes += len(
                payload
            )

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
                    f"size_drop={report_mismatch} "
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

        writer.join(
            timeout=1.0
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
