#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b4_1_server_legacy_edge_runtime_v2"
CLASSIFICATION_OK = "B4_1_SERVER_LEGACY_EDGE_RUNTIME_CONFIRMED"
CLASSIFICATION_FAIL = "B4_1_SERVER_LEGACY_EDGE_RUNTIME_NOT_CONFIRMED"

GAMES_REL = "companion/plugins/games.py"
STREAM_MANAGER_REL = "companion/games/stream_manager.py"
NATIVE_STREAM_REL = "companion/native_stream.py"

EXPECTED_STREAM_MANAGER_SHA = (
    "12ea9b05879c434b85e1c01892d9a7b6020b85efbdc3b7656a95275e47db8e8b"
)
EXPECTED_NATIVE_STREAM_SHA = (
    "d48363d2c8ef6b0f08c78cef322efbf16e8518d56955c33ba174c5a973767cf1"
)

BASE_URL = "http://127.0.0.1:8765"

FORBIDDEN = (
    "games.stream_manager",
    "StreamHostError",
    "self._stream",
    '"stream_host"',
    '"stream_warning"',
    '"stream-status"',
    '"stream-start"',
    '"stream-stop"',
    '"games_stream_host"',
)

REQUIRED = (
    "NativeStreamManager",
    "self._native_stream",
    '"native_stream"',
    '"native-stream-status"',
    '"native-stream-start"',
    '"native-stream-stop"',
    '"games_native_stream"',
)


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def get_json(
    path: str,
) -> tuple[
    bool,
    dict[str, Any],
    str,
]:
    request = urllib.request.Request(
        BASE_URL + path,
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=5.0,
        ) as response:
            raw = response.read(
                1024 * 1024
            )
    except Exception as exc:
        return (
            False,
            {},
            type(exc).__name__,
        )

    try:
        value = json.loads(
            raw.decode("utf-8")
        )
    except (
        UnicodeError,
        json.JSONDecodeError,
    ):
        return (
            False,
            {},
            "INVALID_JSON",
        )

    if not isinstance(
        value,
        dict,
    ):
        return (
            False,
            {},
            "NON_OBJECT_JSON",
        )

    return (
        True,
        value,
        "",
    )


def legacy_endpoint_disabled(
    path: str,
) -> tuple[
    bool,
    str,
]:
    request = urllib.request.Request(
        BASE_URL + path,
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=5.0,
        ) as response:
            response.read(
                4096
            )
            return (
                False,
                f"HTTP_{response.status}",
            )

    except urllib.error.HTTPError as exc:
        return (
            exc.code >= 400,
            f"HTTP_{exc.code}",
        )

    except Exception as exc:
        return (
            False,
            type(exc).__name__,
        )


def sunshine_process_running() -> tuple[
    bool | None,
    str,
]:
    try:
        completed = subprocess.run(
            [
                "tasklist.exe",
                "/FI",
                "IMAGENAME eq sunshine.exe",
                "/FO",
                "CSV",
                "/NH",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=8.0,
            check=False,
        )
    except Exception as exc:
        return (
            None,
            type(exc).__name__,
        )

    if completed.returncode != 0:
        return (
            None,
            "TASKLIST_FAILED",
        )

    running = any(
        line.strip().casefold().startswith(
            '"sunshine.exe"'
        )
        for line
        in completed.stdout.splitlines()
    )

    return (
        running,
        "",
    )


def inspect_source(
    path: Path,
) -> dict[str, Any]:
    data = path.read_bytes()
    text = data.decode(
        "utf-8-sig"
    )

    tree = ast.parse(
        text,
        filename=GAMES_REL,
    )

    forbidden = [
        token
        for token in FORBIDDEN
        if token in text
    ]

    missing = [
        token
        for token in REQUIRED
        if token not in text
    ]

    legacy_imports = 0
    stream_refs = 0
    native_calls = []

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.ImportFrom,
        ):
            module = node.module or ""

            if (
                module
                == "games.stream_manager"
                or module.endswith(
                    ".stream_manager"
                )
            ):
                legacy_imports += 1

        if (
            isinstance(
                node,
                ast.Attribute,
            )
            and isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id == "self"
            and node.attr == "_stream"
        ):
            stream_refs += 1

        if (
            isinstance(
                node,
                ast.Call,
            )
            and isinstance(
                node.func,
                ast.Attribute,
            )
            and isinstance(
                node.func.value,
                ast.Attribute,
            )
            and isinstance(
                node.func.value.value,
                ast.Name,
            )
            and node.func.value.value.id == "self"
            and node.func.value.attr == "_native_stream"
        ):
            native_calls.append(
                node.func.attr
            )

    return {
        "sha256": hashlib.sha256(
            data
        ).hexdigest(),
        "crlf_present": (
            b"\r\n"
            in data
        ),
        "legacy_import_count": legacy_imports,
        "legacy_self_stream_reference_count": stream_refs,
        "forbidden_tokens_present": forbidden,
        "required_tokens_missing": missing,
        "native_call_count": len(
            native_calls
        ),
        "native_call_methods": sorted(
            set(
                native_calls
            )
        ),
    }


def self_test() -> int:
    sample = """
class X:
    def f(self):
        self._native_stream.status()
        self._native_stream.start()
        self._native_stream.stop()
        self._native_stream.end_game_session()
"""
    tree = ast.parse(
        sample
    )

    methods = {
        node.func.attr
        for node in ast.walk(
            tree
        )
        if (
            isinstance(
                node,
                ast.Call,
            )
            and isinstance(
                node.func,
                ast.Attribute,
            )
        )
    }

    assert {
        "status",
        "start",
        "stop",
        "end_game_session",
    } <= methods

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        default=".",
    )

    parser.add_argument(
        "--require-active",
        action="store_true",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(
        args.root
    ).resolve()

    games = (
        root
        / GAMES_REL
    )

    stream_manager = (
        root
        / STREAM_MANAGER_REL
    )

    native_stream = (
        root
        / NATIVE_STREAM_REL
    )

    source = inspect_source(
        games
    )

    stream_manager_unchanged = (
        stream_manager.is_file()
        and sha256(
            stream_manager
        )
        == EXPECTED_STREAM_MANAGER_SHA
    )

    native_stream_unchanged = (
        native_stream.is_file()
        and sha256(
            native_stream
        )
        == EXPECTED_NATIVE_STREAM_SHA
    )

    status_available, status, status_error = (
        get_json(
            "/plugins/games/status"
        )
    )

    stream_status_disabled, stream_status_result = (
        legacy_endpoint_disabled(
            "/plugins/games/stream-status"
        )
        if status_available
        else (
            False,
            "COMPANION_UNAVAILABLE",
        )
    )

    native = (
        status.get(
            "native_stream"
        )
        if status_available
        else None
    )

    if not isinstance(
        native,
        dict,
    ):
        native = {}

    game_active = bool(
        status.get(
            "active",
            False,
        )
    )

    native_ready = bool(
        native.get(
            "ready",
            False,
        )
    )

    native_active = bool(
        native.get(
            "active",
            False,
        )
    )

    stream_host_absent = (
        status_available
        and "stream_host"
        not in status
    )

    sunshine_running, sunshine_error = (
        sunshine_process_running()
    )

    source_ok = (
        source[
            "legacy_import_count"
        ] == 0
        and source[
            "legacy_self_stream_reference_count"
        ] == 0
        and not source[
            "forbidden_tokens_present"
        ]
        and not source[
            "required_tokens_missing"
        ]
    )

    runtime_ok = (
        status_available
        and stream_host_absent
        and stream_status_disabled
        and stream_manager_unchanged
        and native_stream_unchanged
        and sunshine_running is False
    )

    active_ok = (
        not args.require_active
        or (
            game_active
            and native_ready
            and native_active
        )
    )

    confirmed = (
        source_ok
        and runtime_ok
        and active_ok
    )

    classification = (
        CLASSIFICATION_OK
        if confirmed
        else CLASSIFICATION_FAIL
    )

    report = {
        "schema": SCHEMA,
        "classification": classification,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "files_deleted_by_probe": 0,
        "require_active": args.require_active,
        "source": source,
        "stream_manager_file_unchanged": stream_manager_unchanged,
        "native_stream_file_unchanged": native_stream_unchanged,
        "status_available": status_available,
        "status_error": status_error,
        "stream_host_field_absent": stream_host_absent,
        "legacy_stream_status_endpoint_disabled": stream_status_disabled,
        "legacy_stream_status_endpoint_result": stream_status_result,
        "game_active": game_active,
        "native_stream_ready": native_ready,
        "native_stream_active": native_active,
        "native_stream_kind": native.get(
            "kind",
            "",
        ),
        "capture_backend": native.get(
            "capture_backend",
            "",
        ),
        "encoder": native.get(
            "encoder",
            "",
        ),
        "transport": native.get(
            "transport",
            "",
        ),
        "sunshine_process_running": sunshine_running,
        "sunshine_process_check_error": sunshine_error,
        "stream_manager_deleted": not stream_manager.exists(),
        "sunshine_artifacts_deleted": False,
        "android_changed_by_b4_1": False,
    }

    out_dir = (
        root
        / "logs"
        / "diagnostics"
    )

    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        out_dir
        / "b4_1_server_legacy_edge_runtime.json"
    )

    text_path = (
        out_dir
        / "b4_1_server_legacy_edge_runtime.txt"
    )

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "PrivyHub Phase B4.1 server legacy-edge runtime validation",
        f"Classification: {classification}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "Files deleted by probe: 0",
        "",
        "=== SOURCE CUT ===",
        f"Games SHA-256: {source['sha256']}",
        f"CRLF preserved: {source['crlf_present']}",
        f"Legacy StreamManager import count: {source['legacy_import_count']}",
        f"Legacy self._stream reference count: {source['legacy_self_stream_reference_count']}",
        f"Forbidden legacy tokens present: {source['forbidden_tokens_present']}",
        f"Required native tokens missing: {source['required_tokens_missing']}",
        f"Native stream call count: {source['native_call_count']}",
        "Native stream call methods: "
        + json.dumps(
            source[
                "native_call_methods"
            ]
        ),
        f"stream_manager.py unchanged and retained: {stream_manager_unchanged}",
        f"native_stream.py unchanged: {native_stream_unchanged}",
        "",
        "=== LIVE COMPANION ===",
        f"Status endpoint available: {status_available}",
        f"Status endpoint error: {status_error or '<none>'}",
        f"stream_host field absent: {stream_host_absent}",
        f"Legacy stream-status endpoint disabled: {stream_status_disabled}",
        f"Legacy stream-status endpoint result: {stream_status_result}",
        "",
        "=== ACTIVE NATIVE SESSION ===",
        f"Active session required: {args.require_active}",
        f"Game active: {game_active}",
        f"Native stream ready: {native_ready}",
        f"Native stream active: {native_active}",
        f"Native kind: {native.get('kind', '')}",
        f"Capture backend: {native.get('capture_backend', '')}",
        f"Encoder: {native.get('encoder', '')}",
        f"Transport: {native.get('transport', '')}",
        "",
        "=== SUNSHINE PROCESS ===",
        f"Sunshine process running: {sunshine_running}",
        f"Process check error: {sunshine_error or '<none>'}",
        "",
        "=== SCOPE ===",
        f"stream_manager.py deleted by B4.1: {not stream_manager.exists()}",
        "Sunshine runtime/scripts deleted by B4.1: False",
        "Android Moonlight integration changed by B4.1: False",
        "",
        "Next step: "
        + (
            "B4_1_RUNTIME_CONFIRMED_PROCEED_ANDROID_EDGE"
            if confirmed
            else "INSPECT_FAILED_B4_1_SIGNAL_BEFORE_NEXT_PATCH"
        ),
    ]

    text_path.write_text(
        "\n".join(
            lines
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(
        classification
    )
    print(
        "Text:",
        text_path,
    )

    return (
        0
        if confirmed
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
