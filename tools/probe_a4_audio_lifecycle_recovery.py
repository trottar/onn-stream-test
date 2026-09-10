#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from ctypes import wintypes
from pathlib import Path
from typing import Any

BASE = "http://127.0.0.1:8765"
EXPECTED_VERSION = (
    "process_loopback_float_crash_safe_recovery_v0.25"
)
SYNCHRONIZE = 0x00100000
WAIT_TIMEOUT = 0x00000102
TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]

def port_open() -> bool:
    try:
        with socket.create_connection(
            ("127.0.0.1", 8765),
            timeout=0.35,
        ):
            return True
    except OSError:
        return False

def request_json(path: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(
            BASE + path,
            timeout=5,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )
    except (
        urllib.error.URLError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise RuntimeError(
            "Companion API request failed"
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(
            "Companion API returned a non-object payload"
        )
    return payload

def process_ids_by_name(name: str) -> list[int]:
    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )
    snapshot = kernel32.CreateToolhelp32Snapshot(
        TH32CS_SNAPPROCESS,
        0,
    )
    if snapshot == wintypes.HANDLE(-1).value:
        raise OSError(
            ctypes.get_last_error(),
            "CreateToolhelp32Snapshot failed",
        )

    result: list[int] = []
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)

    try:
        if not kernel32.Process32FirstW(
            snapshot,
            ctypes.byref(entry),
        ):
            return result

        while True:
            if entry.szExeFile.casefold() == name.casefold():
                result.append(
                    int(entry.th32ProcessID)
                )

            if not kernel32.Process32NextW(
                snapshot,
                ctypes.byref(entry),
            ):
                break
    finally:
        kernel32.CloseHandle(snapshot)

    return result

def process_alive(pid: int) -> bool:
    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )
    handle = kernel32.OpenProcess(
        SYNCHRONIZE,
        False,
        int(pid),
    )
    if not handle:
        return False

    try:
        return (
            kernel32.WaitForSingleObject(
                handle,
                0,
            )
            == WAIT_TIMEOUT
        )
    finally:
        kernel32.CloseHandle(handle)

def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(
            encoding="utf-8-sig",
        )
    )
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"JSON root is not an object: {path}"
        )
    return payload

def wait_for_live_audio_status(
    status_path: Path,
    started: float,
    timeout: float = 8.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error = ""

    while time.monotonic() < deadline:
        try:
            if (
                status_path.is_file()
                and status_path.stat().st_mtime
                >= started - 2.0
            ):
                payload = read_json(status_path)
                if (
                    payload.get("probe_version")
                    == EXPECTED_VERSION
                    and payload.get("ready") is True
                    and payload.get("final") is False
                ):
                    return payload
        except Exception as exc:
            last_error = str(exc)

        time.sleep(0.20)

    detail = (
        f": {last_error}"
        if last_error
        else ""
    )
    raise RuntimeError(
        "Fresh live process_audio_status.json was not observed"
        + detail
    )

def newest_fresh_final(
    directory: Path,
    started: float,
) -> Path | None:
    candidates = [
        path
        for path in directory.glob("*.json")
        if (
            path.is_file()
            and path.stat().st_mtime >= started - 2.0
        )
    ]
    candidates.sort(
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for path in candidates:
        try:
            payload = read_json(path)
        except Exception:
            continue

        if (
            payload.get("probe_version")
            == EXPECTED_VERSION
            and payload.get("final") is True
        ):
            return path

    return None

def validate_original_volumes(
    local_output: dict[str, Any],
) -> list[float]:
    original = local_output.get(
        "original_volumes",
        [],
    )

    if not (
        isinstance(original, list)
        and original
    ):
        raise RuntimeError(
            "Audio status contains no original session volumes"
        )

    normalized: list[float] = []

    for value in original:
        if (
            isinstance(value, bool)
            or not isinstance(
                value,
                (int, float),
            )
        ):
            raise RuntimeError(
                "Audio status contains an invalid original volume"
            )

        normalized.append(
            float(value)
        )

    if not all(
        abs(value - 1.0) <= 0.001
        for value in normalized
    ):
        raise RuntimeError(
            "Pre-suppression RetroArch session volume is not restored to 1.0"
        )

    return normalized

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=".",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    service = (
        root
        / "companion"
        / "privyhub_service.py"
    )
    timing_dir = (
        root
        / "logs"
        / "games"
        / "audio_timing"
    )
    live_status_path = (
        root
        / "data"
        / "games"
        / "native_stream"
        / "process_audio_status.json"
    )
    recovery_marker_path = (
        root
        / "data"
        / "games"
        / "native_stream"
        / "process_audio_suppression_recovery.json"
    )
    log_path = (
        root
        / "logs"
        / "games"
        / "a4_audio_lifecycle_recovery_probe.txt"
    )
    companion_log = (
        root
        / "logs"
        / "games"
        / "a4_audio_lifecycle_probe_companion.log"
    )
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        "PrivyHub A4 audio/lifecycle recovery E2E probe v5",
        (
            "Purpose: validate live TV/PC audio behavior, stable 1.0 "
            "pre-suppression baseline, final mixer restoration, and "
            "companion-owned game/audio cleanup."
        ),
    ]

    result = "FAIL"
    companion: subprocess.Popen[Any] | None = None
    log_handle = None
    started = time.time()
    target_pid = 0

    try:
        if os.name != "nt":
            raise RuntimeError(
                "A4 lifecycle probe is Windows-only"
            )

        if port_open():
            raise RuntimeError(
                "A companion is already running. Stop it normally before running this probe."
            )

        if process_ids_by_name(
            "PrivyHubProcessAudio.exe"
        ):
            raise RuntimeError(
                "A process-audio helper is already running before the probe"
            )

        log_handle = companion_log.open("wb")

        companion = subprocess.Popen(
            [
                sys.executable,
                str(service),
            ],
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=log_handle,
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP
            ),
        )

        deadline = time.monotonic() + 15.0

        while (
            time.monotonic() < deadline
            and not port_open()
        ):
            if companion.poll() is not None:
                raise RuntimeError(
                    "Companion exited during probe startup"
                )

            time.sleep(0.20)

        if not port_open():
            raise RuntimeError(
                "Companion did not become available on localhost"
            )

        print("")
        print("A4 AUDIO/LIFECYCLE RUNTIME TEST")
        print("")
        print(
            "On the onn, launch any game with clearly audible music/effects."
        )
        print(
            "Play for about 20-30 seconds."
        )
        print("Confirm:")
        print(
            "  1. TV game audio is clearly audible."
        )
        print(
            "  2. PC does not duplicate audible game audio."
        )
        print("")

        answer = input(
            "While the game is still running, type y if both audio conditions are true: "
        ).strip().casefold()

        if answer not in {"y", "yes"}:
            raise RuntimeError(
                "TV-audible / PC-silent behavior was not confirmed"
            )

        games_status = request_json(
            "/plugins/games/status"
        )

        if not bool(
            games_status.get(
                "active",
                False,
            )
        ):
            raise RuntimeError(
                "Games plugin did not report an active game"
            )

        target_pid = int(
            games_status.get(
                "pid",
                0,
            )
            or 0
        )

        if target_pid <= 0:
            raise RuntimeError(
                "Games status has no active RetroArch PID"
            )

        helpers = process_ids_by_name(
            "PrivyHubProcessAudio.exe"
        )

        if len(helpers) != 1:
            raise RuntimeError(
                "Expected exactly one active process-audio helper"
            )

        # Correct live-source check:
        # process_audio_status.json is continuously updated while the helper
        # runs. audio_timing/*.json is the final-session history and is only
        # required after shutdown.
        live_payload = wait_for_live_audio_status(
            live_status_path,
            started,
        )

        live_local = live_payload.get(
            "local_output",
            {},
        )

        if not isinstance(
            live_local,
            dict,
        ):
            raise RuntimeError(
                "Live process-audio status has no local_output object"
            )

        original = validate_original_volumes(
            live_local
        )

        live_recovery = live_local.get(
            "recovery",
            {},
        )

        if not isinstance(
            live_recovery,
            dict,
        ):
            live_recovery = {}

        live_callback = live_payload.get(
            "callback",
            {},
        )

        live_peak = (
            live_callback.get(
                "compensated_peak_absolute",
                0.0,
            )
            if isinstance(
                live_callback,
                dict,
            )
            else 0.0
        )

        if (
            not isinstance(
                live_peak,
                (int, float),
            )
            or float(live_peak) <= 0.02
        ):
            raise RuntimeError(
                "Live compensated game-audio level remains unexpectedly quiet"
            )

        marker_present_during_run = (
            recovery_marker_path.is_file()
        )

        lines.extend(
            [
                "TV audio audible: True",
                "PC duplicate audio effectively silent: True",
                f"Live probe version: {live_payload.get('probe_version', '')}",
                f"Live original volumes: {original}",
                (
                    "Live recovery marker found by helper: "
                    + str(
                        bool(
                            live_recovery.get(
                                "marker_found",
                                False,
                            )
                        )
                    )
                ),
                (
                    "Live recovery applied: "
                    + str(
                        bool(
                            live_recovery.get(
                                "applied",
                                False,
                            )
                        )
                    )
                ),
                (
                    "Live recovery ignored reason: "
                    + str(
                        live_recovery.get(
                            "ignored_reason",
                            "",
                        )
                    )
                ),
                (
                    "Crash-safe active recovery marker present: "
                    + str(
                        marker_present_during_run
                    )
                ),
                (
                    "Live compensated peak absolute: "
                    + str(live_peak)
                ),
            ]
        )

        if not marker_present_during_run:
            raise RuntimeError(
                "Crash-safe suppression recovery marker was not present during active attenuation"
            )

        print("")
        print(
            "The probe will now send Ctrl+Break to the companion it started."
        )
        print(
            "The game should close through the normal Games stop lifecycle."
        )
        print("")

        companion.send_signal(
            signal.CTRL_BREAK_EVENT
        )

        try:
            companion.wait(
                timeout=20.0
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "Companion did not exit within 20 seconds"
            ) from exc

        time.sleep(0.75)

        if port_open():
            raise RuntimeError(
                "Companion control port remained open after shutdown"
            )

        if process_ids_by_name(
            "PrivyHubProcessAudio.exe"
        ):
            raise RuntimeError(
                "Process-audio helper remained alive after companion shutdown"
            )

        if process_alive(target_pid):
            raise RuntimeError(
                "RetroArch remained alive after companion shutdown"
            )

        fresh_final = newest_fresh_final(
            timing_dir,
            started,
        )

        if fresh_final is None:
            raise RuntimeError(
                "No fresh final process-audio timing log was written after shutdown"
            )

        final_payload = read_json(
            fresh_final
        )

        final_local = final_payload.get(
            "local_output",
            {},
        )

        if not isinstance(
            final_local,
            dict,
        ):
            raise RuntimeError(
                "Fresh final audio timing log has no local_output object"
            )

        final_original = validate_original_volumes(
            final_local
        )

        final_flag = bool(
            final_payload.get(
                "final",
                False,
            )
        )
        restored = bool(
            final_local.get(
                "restored",
                False,
            )
        )

        if not final_flag:
            raise RuntimeError(
                "Fresh audio timing log did not report final=true"
            )

        if not restored:
            raise RuntimeError(
                "Fresh audio timing log did not report restored=true"
            )

        if recovery_marker_path.exists():
            raise RuntimeError(
                "Crash-safe suppression marker remained after successful restoration"
            )

        lines.extend(
            [
                f"Final timing log: {fresh_final.name}",
                f"Final original volumes: {final_original}",
                "Final audio helper status: True",
                "Audio mixer restored: True",
                "Crash-safe recovery marker cleared after restore: True",
                "Companion exited: True",
                "RetroArch exited with companion: True",
                "Process-audio helper exited with companion: True",
            ]
        )

        result = (
            "A4_AUDIO_LIFECYCLE_RECOVERY_E2E_OBSERVED"
        )

    except Exception as exc:
        lines.append(
            f"ERROR: {type(exc).__name__}: {exc}"
        )

        if (
            companion is not None
            and companion.poll() is None
        ):
            try:
                companion.send_signal(
                    signal.CTRL_BREAK_EVENT
                )
                companion.wait(
                    timeout=15.0
                )
            except Exception:
                # Do not force-kill from the probe.
                pass

    finally:
        if log_handle is not None:
            try:
                log_handle.close()
            except Exception:
                pass

    lines.append(
        f"Result: {result}"
    )

    log_path.write_text(
        "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )

    print("")
    print("\n".join(lines))
    print(f"Probe log: {log_path}")

    return (
        0
        if result
        == "A4_AUDIO_LIFECYCLE_RECOVERY_E2E_OBSERVED"
        else 1
    )

if __name__ == "__main__":
    raise SystemExit(main())
