#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b4_4_code_orphan_cleanup_runtime_v1"
OK = "B4_4_CODE_ORPHAN_CLEANUP_RUNTIME_CONFIRMED"
FAIL = "B4_4_CODE_ORPHAN_CLEANUP_RUNTIME_NOT_CONFIRMED"

MAIN_REL = (
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
    "MainActivity.kt"
)
MANIFEST_REL = "PrivyHub/app/src/main/AndroidManifest.xml"
GAMES_REL = "companion/plugins/games.py"
STREAM_MANAGER_REL = "companion/games/stream_manager.py"

EXPECTED_MANIFEST_SHA = (
    "ab1140c3230582f9dbbbf3c179d8fa08363971d9289e08442487f3849c7ac8a2"
)
EXPECTED_GAMES_SHA = (
    "f1271c865cdf88b971da4116d7eb887bf9855864ce1ae848baafc7a3452e0f9c"
)

BASE_URL = "http://127.0.0.1:8765"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_json(
    path: str,
) -> tuple[bool, dict[str, Any], str]:
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
        return False, {}, type(exc).__name__

    try:
        value = json.loads(
            raw.decode("utf-8")
        )
    except Exception:
        return False, {}, "INVALID_JSON"

    if not isinstance(value, dict):
        return False, {}, "NON_OBJECT_JSON"

    return True, value, ""


def sunshine_running() -> tuple[bool | None, str]:
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
        return None, type(exc).__name__

    if completed.returncode != 0:
        return None, "TASKLIST_FAILED"

    running = any(
        line.strip().casefold().startswith(
            '"sunshine.exe"'
        )
        for line in completed.stdout.splitlines()
    )

    return running, ""


def self_test() -> int:
    assert "NativeStreamManager".endswith("StreamManager")
    assert "NativeStreamManager" != "StreamManager"
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--require-active", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()

    main_path = root / MAIN_REL
    manifest_path = root / MANIFEST_REL
    games_path = root / GAMES_REL
    manager_path = root / STREAM_MANAGER_REL

    main_data = main_path.read_bytes()
    main_text = main_data.decode("utf-8-sig")

    helper_tokens = [
        token
        for token in (
            "buildStreamHostMessage",
            "setGameStreamHost",
            "/plugins/games/stream-start",
            "/plugins/games/stream-stop",
        )
        if token in main_text
    ]

    required_missing = [
        token
        for token in (
            "openNativeGameStream",
            "native_stream_host",
            "buildNativeStreamMessage",
            "completeGameLaunchHandoff",
            '"native_stream"',
        )
        if token not in main_text
    ]

    manifest_unchanged = (
        manifest_path.is_file()
        and sha256(manifest_path)
        == EXPECTED_MANIFEST_SHA
    )
    games_unchanged = (
        games_path.is_file()
        and sha256(games_path)
        == EXPECTED_GAMES_SHA
    )
    manager_deleted = (
        not manager_path.exists()
    )

    status_available, status, status_error = get_json(
        "/plugins/games/status"
    )

    native = (
        status.get("native_stream")
        if status_available
        else None
    )
    if not isinstance(native, dict):
        native = {}

    game_active = bool(
        status.get("active", False)
    )
    native_ready = bool(
        native.get("ready", False)
    )
    native_active = bool(
        native.get("active", False)
    )

    sunshine, sunshine_error = sunshine_running()

    source_ok = (
        not helper_tokens
        and not required_missing
        and manifest_unchanged
        and games_unchanged
        and manager_deleted
    )

    runtime_ok = (
        status_available
        and sunshine is False
        and (
            not args.require_active
            or (
                game_active
                and native_ready
                and native_active
            )
        )
    )

    confirmed = source_ok and runtime_ok
    classification = OK if confirmed else FAIL

    report = {
        "schema": SCHEMA,
        "classification": classification,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "require_active": args.require_active,
        "main_activity_sha256": hashlib.sha256(
            main_data
        ).hexdigest(),
        "main_activity_crlf_preserved": (
            b"\r\n" in main_data
        ),
        "orphan_helper_tokens_present": helper_tokens,
        "required_native_tokens_missing": required_missing,
        "android_manifest_unchanged": manifest_unchanged,
        "b4_1_games_unchanged": games_unchanged,
        "stream_manager_deleted": manager_deleted,
        "status_available": status_available,
        "status_error": status_error,
        "game_active": game_active,
        "native_stream_ready": native_ready,
        "native_stream_active": native_active,
        "native_kind": native.get("kind", ""),
        "capture_backend": native.get("capture_backend", ""),
        "encoder": native.get("encoder", ""),
        "transport": native.get("transport", ""),
        "sunshine_process_running": sunshine,
        "sunshine_process_check_error": sunshine_error,
    }

    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        out_dir
        / "b4_4_code_orphan_cleanup_runtime.json"
    )
    text_path = (
        out_dir
        / "b4_4_code_orphan_cleanup_runtime.txt"
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
        "PrivyHub B4.4 code-orphan cleanup runtime validation",
        f"Classification: {classification}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== SOURCE CLEANUP ===",
        f"MainActivity SHA-256: {report['main_activity_sha256']}",
        f"MainActivity CRLF preserved: {report['main_activity_crlf_preserved']}",
        f"Orphan helper tokens present: {helper_tokens}",
        f"Required native tokens missing: {required_missing}",
        f"AndroidManifest unchanged: {manifest_unchanged}",
        f"B4.1 games.py unchanged: {games_unchanged}",
        f"stream_manager.py deleted: {manager_deleted}",
        "",
        "=== ACTIVE NATIVE SESSION ===",
        f"Active session required: {args.require_active}",
        f"Companion status available: {status_available}",
        f"Status error: {status_error or '<none>'}",
        f"Game active: {game_active}",
        f"Native stream ready: {native_ready}",
        f"Native stream active: {native_active}",
        f"Native kind: {native.get('kind', '')}",
        f"Capture backend: {native.get('capture_backend', '')}",
        f"Encoder: {native.get('encoder', '')}",
        f"Transport: {native.get('transport', '')}",
        "",
        "=== LEGACY PROCESS ===",
        f"Sunshine process running: {sunshine}",
        f"Process check error: {sunshine_error or '<none>'}",
        "",
        "Next step: "
        + (
            "B4_4_RUNTIME_CONFIRMED_HASH_PHYSICAL_LEGACY_ARTIFACTS"
            if confirmed
            else "INSPECT_B4_4_FAILURE_BEFORE_PHYSICAL_CLEANUP"
        ),
    ]

    text_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(classification)
    print("Text:", text_path)
    return 0 if confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
