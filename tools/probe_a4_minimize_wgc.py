#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import time

from ctypes import wintypes
from pathlib import Path
from typing import Any


class ProbeError(RuntimeError):
    pass


SW_MINIMIZE = 6
SW_RESTORE = 9
META_RELATIVE = Path(
    "data/games/native_stream/wgc_capture_meta.json"
)
OUTPUT_JSON_RELATIVE = Path(
    "logs/games/a4_host_coexistence_minimize_probe.json"
)
OUTPUT_TEXT_RELATIVE = Path(
    "logs/games/a4_host_coexistence_minimize_probe.txt"
)


def _same_windows_path(
    first: str,
    second: Path,
) -> bool:
    return os.path.normcase(
        os.path.abspath(first)
    ) == os.path.normcase(
        os.path.abspath(str(second))
    )


def _configured_retroarch(
    root: Path,
) -> Path:
    config = (
        root
        / "companion"
        / "games"
        / "config"
        / "emulators.json"
    )

    try:
        payload = json.loads(
            config.read_text(
                encoding="utf-8-sig"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise ProbeError(
            f"Unable to read emulators.json: {exc}"
        ) from exc

    retroarch = (
        payload.get("retroarch")
        if isinstance(payload, dict)
        else None
    )

    if not isinstance(
        retroarch,
        dict,
    ):
        raise ProbeError(
            "RetroArch profile is missing from emulators.json"
        )

    executable_rel = retroarch.get(
        "executable"
    )

    if (
        not isinstance(
            executable_rel,
            str,
        )
        or not executable_rel.strip()
    ):
        raise ProbeError(
            "RetroArch executable is not configured"
        )

    candidate = (
        root
        / executable_rel
    ).resolve()

    try:
        candidate.relative_to(
            root
        )
    except ValueError as exc:
        raise ProbeError(
            "Configured RetroArch executable escaped the project root"
        ) from exc

    if not candidate.is_file():
        raise ProbeError(
            "Configured RetroArch executable does not exist"
        )

    return candidate


def _window_api():
    if os.name != "nt":
        raise ProbeError(
            "A4 minimize probe requires the Windows host"
        )

    user32 = ctypes.WinDLL(
        "user32",
        use_last_error=True,
    )
    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )

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

    user32.GetClientRect.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(
            wintypes.RECT
        ),
    ]
    user32.GetClientRect.restype = wintypes.BOOL

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

    user32.ShowWindowAsync.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
    ]
    user32.ShowWindowAsync.restype = wintypes.BOOL

    kernel32.OpenProcess.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    kernel32.OpenProcess.restype = wintypes.HANDLE

    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(
            wintypes.DWORD
        ),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

    kernel32.CloseHandle.argtypes = [
        wintypes.HANDLE,
    ]
    kernel32.CloseHandle.restype = wintypes.BOOL

    return (
        user32,
        kernel32,
        callback_type,
    )


def _find_window(
    executable: Path,
    preferred_hwnd: int,
) -> dict[str, Any]:
    (
        user32,
        kernel32,
        callback_type,
    ) = _window_api()

    PROCESS_QUERY_LIMITED_INFORMATION = (
        0x1000
    )

    matches: list[
        dict[str, Any]
    ] = []

    @callback_type
    def visit(
        hwnd: int,
        _lparam: int,
    ) -> bool:
        try:
            if not user32.IsWindowVisible(
                hwnd
            ):
                return True

            pid = wintypes.DWORD()

            user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(
                    pid
                ),
            )

            if pid.value <= 0:
                return True

            process = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                pid.value,
            )

            if not process:
                return True

            try:
                path_buffer = (
                    ctypes.create_unicode_buffer(
                        32768
                    )
                )
                path_length = wintypes.DWORD(
                    len(
                        path_buffer
                    )
                )

                if not kernel32.QueryFullProcessImageNameW(
                    process,
                    0,
                    path_buffer,
                    ctypes.byref(
                        path_length
                    ),
                ):
                    return True

                process_path = (
                    path_buffer.value
                )

            finally:
                kernel32.CloseHandle(
                    process
                )

            if not _same_windows_path(
                process_path,
                executable,
            ):
                return True

            rect = wintypes.RECT()

            if not user32.GetClientRect(
                hwnd,
                ctypes.byref(
                    rect
                ),
            ):
                return True

            width = max(
                0,
                int(
                    rect.right
                    - rect.left
                ),
            )
            height = max(
                0,
                int(
                    rect.bottom
                    - rect.top
                ),
            )

            if (
                width < 64
                or height < 64
            ):
                return True

            length = (
                user32.GetWindowTextLengthW(
                    hwnd
                )
            )
            title = ""

            if length > 0:
                buffer = (
                    ctypes.create_unicode_buffer(
                        length + 1
                    )
                )
                if (
                    user32.GetWindowTextW(
                        hwnd,
                        buffer,
                        len(buffer),
                    )
                    > 0
                ):
                    title = (
                        buffer.value
                    )

            matches.append(
                {
                    "hwnd": int(hwnd),
                    "pid": int(pid.value),
                    "title": title,
                    "width": width,
                    "height": height,
                    "iconic": bool(
                        user32.IsIconic(
                            hwnd
                        )
                    ),
                    "area": (
                        width * height
                    ),
                }
            )

        except Exception:
            return True

        return True

    if not user32.EnumWindows(
        visit,
        0,
    ):
        raise ProbeError(
            "EnumWindows failed"
        )

    if not matches:
        raise ProbeError(
            "No visible project-managed RetroArch window was found"
        )

    for match in matches:
        if (
            preferred_hwnd > 0
            and int(
                match["hwnd"]
            )
            == preferred_hwnd
        ):
            return match

    return max(
        matches,
        key=lambda item: int(
            item["area"]
        ),
    )


def _read_meta(
    path: Path,
    *,
    require_fresh: bool,
) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise ProbeError(
            f"Unable to read active WGC metadata: {exc}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise ProbeError(
            "WGC metadata root is invalid"
        )

    if payload.get(
        "backend"
    ) != "windows_graphics_capture":
        raise ProbeError(
            "Active stream is not reporting Windows Graphics Capture"
        )

    updated_ms = int(
        payload.get(
            "updated_unix_ms",
            0,
        )
        or 0
    )

    if require_fresh:
        age_ms = (
            int(
                time.time()
                * 1000.0
            )
            - updated_ms
        )

        if (
            updated_ms <= 0
            or age_ms > 12_000
        ):
            raise ProbeError(
                "WGC metadata is stale. Open the game fullscreen on the onn before running the probe."
            )

    return payload


def _counter(
    payload: dict[str, Any],
    name: str,
) -> int:
    try:
        return int(
            payload.get(
                name,
                0,
            )
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


def _diagnostic_counter(
    payload: dict[str, Any],
    name: str,
) -> int:
    diagnostics = payload.get(
        "diagnostics"
    )
    if not isinstance(
        diagnostics,
        dict,
    ):
        return 0

    try:
        return int(
            diagnostics.get(
                name,
                0,
            )
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


def _window_flag(
    payload: dict[str, Any],
    name: str,
) -> bool:
    window = payload.get(
        "window"
    )
    if not isinstance(
        window,
        dict,
    ):
        return False

    return bool(
        window.get(
            name,
            False,
        )
    )


def _summary(
    start: dict[str, Any],
    end: dict[str, Any],
) -> dict[str, Any]:
    return {
        "callbacks_delta": (
            _counter(
                end,
                "callbacks",
            )
            - _counter(
                start,
                "callbacks",
            )
        ),
        "emitted_delta": (
            _counter(
                end,
                "emitted_frames",
            )
            - _counter(
                start,
                "emitted_frames",
            )
        ),
        "duplicates_delta": (
            _counter(
                end,
                "duplicated_emits",
            )
            - _counter(
                start,
                "duplicated_emits",
            )
        ),
        "near_black_delta": (
            _diagnostic_counter(
                end,
                "near_black_samples",
            )
            - _diagnostic_counter(
                start,
                "near_black_samples",
            )
        ),
        "black_streak": (
            _diagnostic_counter(
                end,
                "current_near_black_streak_samples",
            )
        ),
        "captured_exists": (
            _window_flag(
                end,
                "captured_exists",
            )
        ),
        "captured_visible": (
            _window_flag(
                end,
                "captured_visible",
            )
        ),
        "captured_iconic": (
            _window_flag(
                end,
                "captured_iconic",
            )
        ),
        "updated_unix_ms": (
            _counter(
                end,
                "updated_unix_ms",
            )
        ),
    }


def _wait_stage(
    meta_path: Path,
    seconds: float,
) -> dict[str, Any]:
    deadline = (
        time.monotonic()
        + seconds
    )
    latest: (
        dict[str, Any]
        | None
    ) = None

    while (
        time.monotonic()
        < deadline
    ):
        try:
            latest = _read_meta(
                meta_path,
                require_fresh=False,
            )
        except ProbeError:
            pass

        time.sleep(
            0.25
        )

    if latest is None:
        raise ProbeError(
            "WGC metadata disappeared during the probe"
        )

    return latest


def _classify(
    baseline: dict[str, Any],
    minimized: dict[str, Any],
    restored: dict[str, Any],
) -> tuple[str, str]:
    baseline_callbacks = int(
        baseline[
            "callbacks_delta"
        ]
    )
    minimized_callbacks = int(
        minimized[
            "callbacks_delta"
        ]
    )
    minimized_emitted = int(
        minimized[
            "emitted_delta"
        ]
    )
    minimized_duplicates = int(
        minimized[
            "duplicates_delta"
        ]
    )

    restored_callbacks = int(
        restored[
            "callbacks_delta"
        ]
    )

    if baseline_callbacks < 10:
        return (
            "INCONCLUSIVE_BASELINE",
            "The active visible-window baseline did not deliver enough WGC callbacks to judge minimization.",
        )

    if not bool(
        minimized[
            "captured_exists"
        ]
    ):
        return (
            "MINIMIZE_BREAKS_CAPTURE_TARGET",
            "The captured HWND became invalid while minimized.",
        )

    if (
        int(
            minimized[
                "near_black_delta"
            ]
        )
        > 0
        or int(
            minimized[
                "black_streak"
            ]
        )
        > 0
    ):
        return (
            "MINIMIZE_BLACK_CAPTURE",
            "WGC continued enough to sample content, but minimized-window content became near-black.",
        )

    healthy_threshold = max(
        10,
        int(
            baseline_callbacks
            * 0.25
        ),
    )

    if (
        minimized_callbacks
        >= healthy_threshold
    ):
        return (
            "MINIMIZE_CAPTURE_CONTINUES",
            "WGC continued receiving fresh frame callbacks while RetroArch was minimized.",
        )

    if (
        minimized_callbacks <= 3
        and minimized_emitted >= 10
        and minimized_duplicates >= 5
    ):
        if restored_callbacks >= 10:
            return (
                "MINIMIZE_FREEZES_CAPTURE_RECOVERS",
                "Minimization stopped fresh WGC callbacks; the bridge kept emitting the stale last frame, then fresh capture recovered after restore.",
            )

        return (
            "MINIMIZE_FREEZES_CAPTURE_NO_RECOVERY",
            "Minimization stopped fresh WGC callbacks and capture did not clearly recover after restore.",
        )

    return (
        "INCONCLUSIVE_MINIMIZE",
        "Minimized capture changed materially but did not match the clear continue/freeze/black classifications.",
    )


def _write_results(
    root: Path,
    payload: dict[str, Any],
) -> None:
    json_path = (
        root
        / OUTPUT_JSON_RELATIVE
    )
    text_path = (
        root
        / OUTPUT_TEXT_RELATIVE
    )

    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path.write_text(
        json.dumps(
            payload,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "PrivyHub A4 host coexistence minimize probe",
        "",
        f"Verdict: {payload['verdict']}",
        payload[
            "interpretation"
        ],
        "",
        "Baseline visible:",
        json.dumps(
            payload[
                "baseline"
            ],
            indent=2,
        ),
        "",
        "Minimized:",
        json.dumps(
            payload[
                "minimized"
            ],
            indent=2,
        ),
        "",
        "Restored:",
        json.dumps(
            payload[
                "restored"
            ],
            indent=2,
        ),
        "",
        "Note: no network addresses are collected by this probe.",
        "",
    ]

    text_path.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe whether an already-active PrivyHub WGC game stream survives RetroArch minimization."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
    )
    parser.add_argument(
        "--stage-seconds",
        type=float,
        default=6.25,
    )
    args = parser.parse_args()

    root = Path(
        args.root
    ).resolve()

    if args.stage_seconds < 5.5:
        raise ProbeError(
            "stage-seconds must be at least 5.5 because WGC diagnostics update every 5 seconds"
        )

    executable = (
        _configured_retroarch(
            root
        )
    )
    meta_path = (
        root
        / META_RELATIVE
    )

    initial = _read_meta(
        meta_path,
        require_fresh=True,
    )

    preferred_hwnd = _counter(
        initial,
        "hwnd",
    )

    window = _find_window(
        executable,
        preferred_hwnd,
    )

    if bool(
        window[
            "iconic"
        ]
    ):
        raise ProbeError(
            "RetroArch is already minimized. Restore it and open the game fullscreen on the onn first."
        )

    hwnd = int(
        window[
            "hwnd"
        ]
    )

    if (
        preferred_hwnd > 0
        and hwnd != preferred_hwnd
    ):
        raise ProbeError(
            "The active WGC capture HWND does not match the selected RetroArch window."
        )

    (
        user32,
        _kernel32,
        _callback_type,
    ) = _window_api()

    print(
        "A4 minimize probe"
    )
    print(
        "Keep the game fullscreen on the onn during this test."
    )
    print(
        "Stage 1/3: visible baseline..."
    )

    baseline_start = _read_meta(
        meta_path,
        require_fresh=True,
    )

    baseline_end = _wait_stage(
        meta_path,
        args.stage_seconds,
    )

    baseline = _summary(
        baseline_start,
        baseline_end,
    )

    minimized_start = baseline_end

    restored_from_finally = False

    try:
        print(
            "Stage 2/3: minimizing RetroArch..."
        )

        user32.ShowWindowAsync(
            hwnd,
            SW_MINIMIZE,
        )

        time.sleep(
            0.75
        )

        minimized_end = _wait_stage(
            meta_path,
            args.stage_seconds,
        )

        minimized = _summary(
            minimized_start,
            minimized_end,
        )

        print(
            "Stage 3/3: restoring RetroArch..."
        )

        user32.ShowWindowAsync(
            hwnd,
            SW_RESTORE,
        )

        time.sleep(
            0.75
        )

        restored_start = (
            minimized_end
        )

        restored_end = _wait_stage(
            meta_path,
            args.stage_seconds,
        )

        restored = _summary(
            restored_start,
            restored_end,
        )

    finally:
        try:
            user32.ShowWindowAsync(
                hwnd,
                SW_RESTORE,
            )
            restored_from_finally = True
        except Exception:
            pass

    verdict, interpretation = (
        _classify(
            baseline,
            minimized,
            restored,
        )
    )

    payload = {
        "schema": (
            "privyhub_a4_host_coexistence_minimize_probe_v1"
        ),
        "verdict": verdict,
        "interpretation": (
            interpretation
        ),
        "retroarch_window": {
            "pid": int(
                window[
                    "pid"
                ]
            ),
            "title": str(
                window[
                    "title"
                ]
            ),
            "width": int(
                window[
                    "width"
                ]
            ),
            "height": int(
                window[
                    "height"
                ]
            ),
        },
        "baseline": baseline,
        "minimized": minimized,
        "restored": restored,
        "restore_attempted": (
            restored_from_finally
        ),
        "privacy": (
            "No network addresses are recorded."
        ),
    }

    _write_results(
        root,
        payload,
    )

    print()
    print(
        f"Verdict: {verdict}"
    )
    print(
        interpretation
    )
    print()
    print(
        "Saved: "
        + str(
            OUTPUT_TEXT_RELATIVE
        )
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )
    except ProbeError as exc:
        print(
            f"ERROR: {exc}"
        )
        raise SystemExit(1)
