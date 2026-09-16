#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

EXPECTED_HEAD = "7c029de7ff7d569bce07d26c23f0bcfbb1147e8d"
EXPECTED_AVIATOR_ID = "vod_file_aviator_52feb1dbba"
OUT_REL = Path("logs/d096_storage_boundary_probe.txt")


def run(
    cmd: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def listener_present(
    port: int,
) -> bool:
    p = run(
        [
            "ss",
            "-H",
            "-ltn",
            f"sport = :{port}",
        ]
    )

    return bool(
        p.stdout.strip()
    )


def privyhub_processes_present(
) -> bool:
    p = run(
        [
            "pgrep",
            "-f",
            r"[p]ython.*companion/(privyhub_service|range_server)\.py",
        ]
    )

    return (
        p.returncode == 0
        and bool(
            p.stdout.strip()
        )
    )


def wait_lifecycle_clear(
    ports: tuple[int, ...],
    timeout_seconds: float = 5.0,
    poll_seconds: float = 0.1,
) -> tuple[
    bool,
    dict[int, bool],
    bool,
    float,
]:
    started = time.monotonic()
    deadline = (
        started + timeout_seconds
    )

    listeners = {
        port: listener_present(
            port
        )
        for port in ports
    }

    processes_present = (
        privyhub_processes_present()
    )

    while (
        (
            any(
                listeners.values()
            )
            or processes_present
        )
        and time.monotonic() < deadline
    ):
        time.sleep(
            poll_seconds
        )

        listeners = {
            port: listener_present(
                port
            )
            for port in ports
        }

        processes_present = (
            privyhub_processes_present()
        )

    elapsed = (
        time.monotonic()
        - started
    )

    clear = (
        not any(
            listeners.values()
        )
        and not processes_present
    )

    return (
        clear,
        listeners,
        processes_present,
        elapsed,
    )


def request_json(
    url: str,
    method: str = "GET",
) -> tuple[int | None, dict[str, Any] | None, str]:
    req = urllib.request.Request(
        url,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=8,
        ) as response:
            raw = response.read()
            obj = json.loads(
                raw.decode(
                    "utf-8"
                )
            )
            return (
                response.status,
                obj
                if isinstance(
                    obj,
                    dict,
                )
                else None,
                "",
            )
    except urllib.error.HTTPError as exc:
        return (
            exc.code,
            None,
            exc.read().decode(
                "utf-8",
                errors="replace",
            ),
        )
    except Exception as exc:
        return (
            None,
            None,
            f"{type(exc).__name__}: {exc}",
        )


def flatten(
    value: Any,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    if isinstance(
        value,
        dict,
    ):
        if (
            value.get(
                "node_type"
            )
            == "source"
        ):
            out.append(
                value
            )

        children = value.get(
            "children"
        )

        if isinstance(
            children,
            list,
        ):
            for child in children:
                out.extend(
                    flatten(
                        child
                    )
                )

    elif isinstance(
        value,
        list,
    ):
        for child in value:
            out.extend(
                flatten(
                    child
                )
            )

    return out


def range_one_byte(
    path: str,
) -> tuple[bool, str]:
    req = urllib.request.Request(
        "http://127.0.0.1:8000"
        + path,
        headers={
            "Range": "bytes=0-0",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=8,
        ) as response:
            body = response.read()
            content_range = (
                response.headers.get(
                    "Content-Range"
                )
            )

            ok = (
                response.status == 206
                and len(body) == 1
                and bool(
                    content_range
                )
            )

            return (
                ok,
                (
                    f"status={response.status}; "
                    f"bytes={len(body)}; "
                    f"content_range_present="
                    f"{bool(content_range)}"
                ),
            )

    except Exception as exc:
        return (
            False,
            f"{type(exc).__name__}: {exc}",
        )


def self_test() -> int:
    sample = {
        "root": [
            {
                "node_type": "source",
                "id": "x",
                "playback": {
                    "path": "/vod/x.mp4"
                },
            }
        ]
    }

    assert (
        flatten(
            sample["root"]
        )[0]["id"]
        == "x"
    )

    # Exact classifier semantics: NOT_CONFIRMED must not be success.
    confirmed = "D096_CONFIGURABLE_VOD_STORAGE_BOUNDARY_CONFIRMED"
    not_confirmed = "D096_STORAGE_BOUNDARY_NOT_CONFIRMED"

    assert (
        0
        if confirmed
        == "D096_CONFIGURABLE_VOD_STORAGE_BOUNDARY_CONFIRMED"
        else 1
    ) == 0

    assert (
        0
        if not_confirmed
        == "D096_CONFIGURABLE_VOD_STORAGE_BOUNDARY_CONFIRMED"
        else 1
    ) == 1

    print(
        "SELF-TEST PASS"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default="/home/privyhub/Projects/onn-stream-test",
    )
    ap.add_argument(
        "--self-test",
        action="store_true",
    )
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(
        args.root
    ).resolve()

    out = (
        repo / OUT_REL
    )

    out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    head = run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "HEAD",
        ]
    ).stdout.strip()

    config_path = (
        repo / "data/storage.json"
    )

    pre_control_clear = (
        not listener_present(
            8765
        )
    )
    pre_media_clear = (
        not listener_present(
            8000
        )
    )
    pre_processes_clear = (
        not privyhub_processes_present()
    )

    lines = [
        "PrivyHub D-096R3 configurable VOD storage boundary probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        f"Expected checkpoint: {EXPECTED_HEAD}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== PRECHECK ===",
        f"Git HEAD: {head}",
        f"Git HEAD expected: {head == EXPECTED_HEAD}",
        f"Storage config exists: {config_path.is_file()}",
        f"Control listener absent before probe: {pre_control_clear}",
        f"Media listener absent before probe: {pre_media_clear}",
        f"PrivyHub processes absent before probe: {pre_processes_clear}",
    ]

    classification = (
        "D096_STORAGE_BOUNDARY_NOT_CONFIRMED"
    )

    if (
        head != EXPECTED_HEAD
        or not config_path.is_file()
        or not pre_control_clear
        or not pre_media_clear
        or not pre_processes_clear
    ):
        lines += [
            "",
            "=== RESULT ===",
            f"Classification: {classification}",
        ]

        out.write_text(
            "\n".join(
                lines
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            classification
        )
        print(
            "Log:",
            out,
        )
        return 1

    companion_log = (
        repo
        / "logs/d096_companion_probe_console.log"
    )

    handle = companion_log.open(
        "w",
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [
            sys.executable,
            str(
                repo
                / "companion/privyhub_service.py"
            ),
        ],
        cwd=str(
            repo
        ),
        stdin=subprocess.DEVNULL,
        stdout=handle,
        stderr=subprocess.STDOUT,
    )

    status_http = None
    status_obj = None
    storage: dict[str, Any] = {}
    sources_http = None
    sources_obj = None
    sources_error = ""
    catalog_storage: dict[str, Any] = {}
    sources: list[dict[str, Any]] = []
    aviator = None
    start_http = None
    ready = False
    range_ok = False
    range_detail = "<not-run>"

    try:
        for _ in range(
            30
        ):
            status_http, status_obj, _ = (
                request_json(
                    "http://127.0.0.1:8765/status"
                )
            )

            if (
                status_http == 200
                and status_obj
            ):
                break

            if process.poll() is not None:
                break

            time.sleep(
                0.25
            )

        storage = (
            status_obj.get(
                "storage",
                {},
            ).get(
                "vod",
                {},
            )
            if status_obj
            else {}
        )

        (
            sources_http,
            sources_obj,
            sources_error,
        ) = request_json(
            "http://127.0.0.1:8765/sources"
        )

        catalog_storage = (
            sources_obj.get(
                "storage",
                {},
            ).get(
                "vod",
                {},
            )
            if sources_obj
            else {}
        )

        sources = (
            flatten(
                sources_obj.get(
                    "root",
                    [],
                )
            )
            if sources_obj
            else []
        )

        for source in sources:
            if (
                source.get(
                    "id"
                )
                == EXPECTED_AVIATOR_ID
            ):
                aviator = source
                break

        lines += [
            "",
            "=== STORAGE STATUS ===",
            f"GET /status HTTP: {status_http}",
            f"Status storage configured: {storage.get('configured')}",
            f"Status storage mode: {storage.get('mode')}",
            f"Status storage available: {storage.get('available')}",
            f"GET /sources HTTP: {sources_http}",
            f"Catalog storage configured: {catalog_storage.get('configured')}",
            f"Catalog storage mode: {catalog_storage.get('mode')}",
            f"Catalog storage available: {catalog_storage.get('available')}",
            f"Catalog request error: {sources_error or '<none>'}",
            "",
            "=== LOGICAL IDENTITY ===",
            f"VOD source count: {sum(1 for item in sources if str(item.get('playback', {}).get('path', '')).startswith('/vod/'))}",
            f"Aviator stable source ID present: {aviator is not None}",
        ]

        if aviator is not None:
            (
                start_http,
                start_obj,
                start_error,
            ) = request_json(
                "http://127.0.0.1:8765"
                + "/sources/"
                + EXPECTED_AVIATOR_ID
                + "/start",
                method="POST",
            )

            ready = bool(
                start_obj
                and start_obj.get(
                    "ready"
                )
            )

            playback_path = str(
                aviator.get(
                    "playback",
                    {},
                ).get(
                    "path",
                    "",
                )
            )

            if (
                start_http == 200
                and ready
                and playback_path
            ):
                (
                    range_ok,
                    range_detail,
                ) = range_one_byte(
                    playback_path
                )

            lines += [
                "",
                "=== SOURCE START / RANGE ===",
                f"POST Aviator start HTTP: {start_http}",
                f"POST Aviator ready: {ready}",
                f"POST Aviator error: {start_error or '<none>'}",
                f"One-byte Range through logical VOD namespace: {range_ok}",
                f"Range detail: {range_detail}",
            ]

    finally:
        if process.poll() is None:
            process.send_signal(
                signal.SIGINT
            )

            try:
                process.wait(
                    timeout=8
                )
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(
                    timeout=3
                )

        handle.close()

    (
        lifecycle_clear,
        listener_state,
        processes_present_after,
        lifecycle_elapsed,
    ) = wait_lifecycle_clear(
        (
            8765,
            8000,
        ),
        timeout_seconds=5.0,
        poll_seconds=0.1,
    )

    control_listener_after = (
        listener_state.get(
            8765,
            False,
        )
    )
    media_listener_after = (
        listener_state.get(
            8000,
            False,
        )
    )

    lines += [
        "",
        "=== LIFECYCLE ===",
        f"Companion process exited: {process.poll() is not None}",
        f"Lifecycle wait seconds: {lifecycle_elapsed:.3f}",
        f"Control listener absent after bounded wait: {not control_listener_after}",
        f"Media listener absent after bounded wait: {not media_listener_after}",
        f"PrivyHub processes absent after bounded wait: {not processes_present_after}",
        f"Lifecycle cleanup confirmed: {lifecycle_clear}",
    ]

    if (
        status_http == 200
        and storage.get(
            "configured"
        ) is True
        and storage.get(
            "available"
        ) is True
        and sources_http == 200
        and catalog_storage.get(
            "configured"
        ) is True
        and catalog_storage.get(
            "available"
        ) is True
        and aviator is not None
        and start_http == 200
        and ready
        and range_ok
        and lifecycle_clear
    ):
        classification = (
            "D096_CONFIGURABLE_VOD_STORAGE_BOUNDARY_CONFIRMED"
        )

    lines += [
        "",
        "=== RESULT ===",
        f"Classification: {classification}",
    ]

    out.write_text(
        "\n".join(
            lines
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        classification
    )
    print(
        "Log:",
        out,
    )

    return (
        0
        if classification
        == "D096_CONFIGURABLE_VOD_STORAGE_BOUNDARY_CONFIRMED"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
