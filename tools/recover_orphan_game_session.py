#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import json
import os
import socket
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

CONTROL_HOST = "127.0.0.1"
CONTROL_PORT = 8765
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
PROCESS_TERMINATE = 0x0001
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

def companion_available() -> bool:
    try:
        with socket.create_connection(
            (CONTROL_HOST, CONTROL_PORT),
            timeout=0.35,
        ):
            return True
    except OSError:
        return False

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
    entry.dwSize = ctypes.sizeof(
        PROCESSENTRY32W
    )

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
        kernel32.CloseHandle(
            snapshot
        )

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
        kernel32.CloseHandle(
            handle
        )

def process_image(pid: int) -> Path:
    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )
    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        int(pid),
    )
    if not handle:
        raise OSError(
            ctypes.get_last_error(),
            "OpenProcess failed",
        )

    try:
        size = wintypes.DWORD(
            32768
        )
        buffer = ctypes.create_unicode_buffer(
            size.value
        )
        if not kernel32.QueryFullProcessImageNameW(
            handle,
            0,
            buffer,
            ctypes.byref(size),
        ):
            raise OSError(
                ctypes.get_last_error(),
                "QueryFullProcessImageNameW failed",
            )
        return Path(
            buffer.value
        ).resolve()
    finally:
        kernel32.CloseHandle(
            handle
        )

def terminate_exact_process(pid: int) -> None:
    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )
    handle = kernel32.OpenProcess(
        PROCESS_TERMINATE | SYNCHRONIZE,
        False,
        int(pid),
    )
    if not handle:
        raise OSError(
            ctypes.get_last_error(),
            "OpenProcess(PROCESS_TERMINATE) failed",
        )

    try:
        if not kernel32.TerminateProcess(
            handle,
            0xA4,
        ):
            raise OSError(
                ctypes.get_last_error(),
                "TerminateProcess failed",
            )

        if (
            kernel32.WaitForSingleObject(
                handle,
                5000,
            )
            == WAIT_TIMEOUT
        ):
            raise RuntimeError(
                "Terminated helper did not exit within 5 seconds"
            )
    finally:
        kernel32.CloseHandle(
            handle
        )

def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(
            encoding="utf-8-sig",
        )
    )
    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            "JSON root is not an object"
        )
    return payload

def same_path(
    left: Path,
    right: Path,
) -> bool:
    return os.path.normcase(
        str(left.resolve())
    ) == os.path.normcase(
        str(right.resolve())
    )

def write_log(
    path: Path,
    lines: list[str],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=".",
    )
    args = parser.parse_args()

    root = Path(
        args.root
    ).resolve()
    log_path = (
        root
        / "logs"
        / "games"
        / "orphan_game_session_recovery.txt"
    )
    status_path = (
        root
        / "data"
        / "games"
        / "native_stream"
        / "process_audio_status.json"
    )
    expected_helper = (
        root
        / "runtime"
        / "streaming"
        / "process_audio"
        / "PrivyHubProcessAudio.exe"
    ).resolve()

    lines = [
        "PrivyHub orphan game-session recovery v3",
        "Purpose: classify and safely dispose of a helper orphaned after its companion owner exited.",
        "Privacy: no network addresses are written.",
    ]
    result = "FAIL"

    try:
        if os.name != "nt":
            raise RuntimeError(
                "Orphan recovery is Windows-only"
            )

        if companion_available():
            raise RuntimeError(
                "Companion is active; use the normal Games stop lifecycle instead"
            )

        helper_pids = process_ids_by_name(
            "PrivyHubProcessAudio.exe"
        )

        if not helper_pids:
            result = "NO_ORPHAN_HELPER"
            lines.extend(
                [
                    "Audio helper processes observed: 0",
                    f"Result: {result}",
                ]
            )
            write_log(
                log_path,
                lines,
            )
            print(
                "\n".join(lines)
            )
            print(
                f"Recovery log: {log_path}"
            )
            return 0

        if len(helper_pids) != 1:
            raise RuntimeError(
                "Expected exactly one orphaned process-audio helper"
            )

        helper_pid = helper_pids[0]
        helper_image = process_image(
            helper_pid
        )

        if not same_path(
            helper_image,
            expected_helper,
        ):
            raise RuntimeError(
                "Running helper image is not the project runtime helper"
            )

        if not status_path.is_file():
            raise RuntimeError(
                "Project helper is active but process_audio_status.json is missing"
            )

        status = read_json(
            status_path
        )
        target = status.get(
            "target",
            {},
        )
        if not isinstance(
            target,
            dict,
        ):
            raise RuntimeError(
                "Audio status has no target object"
            )

        target_pid = int(
            target.get(
                "pid",
                0,
            )
            or 0
        )
        if target_pid <= 0:
            raise RuntimeError(
                "Audio status has no valid target PID"
            )

        target_alive = process_alive(
            target_pid
        )

        lines.extend(
            [
                "Audio helper processes observed: 1",
                "Helper image verified as project runtime: True",
                f"Managed RetroArch target alive: {target_alive}",
            ]
        )

        if target_alive:
            # Fail closed. The live target still owns an audio session whose
            # mixer state may be recoverable by the original owner. A new
            # process cannot reliably send CTRL_BREAK to the old console group.
            raise RuntimeError(
                "Live-target orphan detected. Recovery remains graceful-only; "
                "the installer will not force-terminate a helper while its "
                "RetroArch target is alive."
            )

        # Target is already dead. The old helper can no longer restore a live
        # target session; its captured 'original' state was 0.01 anyway. There
        # is therefore no mixer-preservation benefit to leaving it running.
        # Force termination is permitted only after both checks above:
        # 1) exact project helper image; 2) target PID is no longer alive.
        terminate_exact_process(
            helper_pid
        )

        if process_alive(
            helper_pid
        ):
            raise RuntimeError(
                "Dead-target helper remained alive after exact termination"
            )

        if process_ids_by_name(
            "PrivyHubProcessAudio.exe"
        ):
            raise RuntimeError(
                "Another process-audio helper appeared during orphan cleanup"
            )

        lines.extend(
            [
                "Dead-target helper exact termination: True",
                "Mixer restoration by orphan helper: not possible (target session already dead)",
                "Legacy 1.0 -> 0.01 mixer recovery must occur on the next managed RetroArch audio session.",
            ]
        )
        result = "DEAD_TARGET_ORPHAN_HELPER_TERMINATED"

    except Exception as exc:
        lines.append(
            f"ERROR: {type(exc).__name__}: {exc}"
        )

    lines.append(
        f"Result: {result}"
    )
    write_log(
        log_path,
        lines,
    )

    print(
        "\n".join(lines)
    )
    print(
        f"Recovery log: {log_path}"
    )

    return (
        0
        if result
        in {
            "DEAD_TARGET_ORPHAN_HELPER_TERMINATED",
            "NO_ORPHAN_HELPER",
        }
        else 1
    )

if __name__ == "__main__":
    raise SystemExit(main())
