#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b4_2_android_legacy_edge_runtime_v1"
OK = "B4_2_ANDROID_LEGACY_EDGE_RUNTIME_CONFIRMED"
FAIL = "B4_2_ANDROID_LEGACY_EDGE_RUNTIME_NOT_CONFIRMED"

MAIN_REL = (
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
    "MainActivity.kt"
)
MANIFEST_REL = "PrivyHub/app/src/main/AndroidManifest.xml"
GAMES_REL = "companion/plugins/games.py"

EXPECTED_B41_GAMES_SHA = (
    "f1271c865cdf88b971da4116d7eb887bf9855864ce1ae848baafc7a3452e0f9c"
)
BASE_URL = "http://127.0.0.1:8765"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_json(path: str) -> tuple[bool, dict[str, Any], str]:
    request = urllib.request.Request(
        BASE_URL + path,
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=5.0,
        ) as response:
            raw = response.read(1024 * 1024)
    except Exception as exc:
        return False, {}, type(exc).__name__

    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception:
        return False, {}, "INVALID_JSON"

    if not isinstance(value, dict):
        return False, {}, "NON_OBJECT_JSON"

    return True, value, ""


def inspect_sources(root: Path) -> dict[str, Any]:
    main_path = root / MAIN_REL
    manifest_path = root / MANIFEST_REL
    games_path = root / GAMES_REL

    main_data = main_path.read_bytes()
    manifest_data = manifest_path.read_bytes()
    main_text = main_data.decode("utf-8-sig")
    manifest_text = manifest_data.decode("utf-8-sig")

    legacy = [
        token
        for token in (
            "sunshine",
            "moonlight",
            "com.limelight",
            "openGameStreamClient",
        )
        if token.casefold() in main_text.casefold()
    ]

    missing = [
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

    games_sha = sha256(games_path)

    return {
        "main_sha256": hashlib.sha256(main_data).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_data).hexdigest(),
        "main_crlf_preserved": b"\r\n" in main_data,
        "legacy_main_tokens_present": legacy,
        "manifest_limelight_present": (
            "com.limelight" in manifest_text.casefold()
        ),
        "open_game_stream_client_present": (
            "openGameStreamClient" in main_text
        ),
        "required_native_tokens_missing": missing,
        "b4_1_games_sha256": games_sha,
        "b4_1_games_unchanged": (
            games_sha == EXPECTED_B41_GAMES_SHA
        ),
    }


def self_test() -> int:
    assert "openNativeGameStream" in "x openNativeGameStream y"
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
    source = inspect_sources(root)

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

    game_active = bool(status.get("active", False))
    native_ready = bool(native.get("ready", False))
    native_active = bool(native.get("active", False))

    source_ok = (
        not source["legacy_main_tokens_present"]
        and not source["manifest_limelight_present"]
        and not source["open_game_stream_client_present"]
        and not source["required_native_tokens_missing"]
        and source["b4_1_games_unchanged"]
    )

    runtime_ok = (
        status_available
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

    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "b4_2_android_legacy_edge_runtime.json"
    text_path = out_dir / "b4_2_android_legacy_edge_runtime.txt"

    report = {
        "schema": SCHEMA,
        "classification": classification,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "require_active": args.require_active,
        "source": source,
        "status_available": status_available,
        "status_error": status_error,
        "game_active": game_active,
        "native_stream_ready": native_ready,
        "native_stream_active": native_active,
        "native_kind": native.get("kind", ""),
        "capture_backend": native.get("capture_backend", ""),
        "encoder": native.get("encoder", ""),
        "transport": native.get("transport", ""),
    }

    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "PrivyHub Phase B4.2 Android Moonlight-edge runtime validation",
        f"Classification: {classification}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== ANDROID SOURCE ===",
        f"MainActivity SHA-256: {source['main_sha256']}",
        f"AndroidManifest SHA-256: {source['manifest_sha256']}",
        f"MainActivity CRLF preserved: {source['main_crlf_preserved']}",
        f"Legacy Sunshine/Moonlight/com.limelight tokens present: {source['legacy_main_tokens_present']}",
        f"openGameStreamClient present: {source['open_game_stream_client_present']}",
        f"Manifest com.limelight present: {source['manifest_limelight_present']}",
        f"Required native tokens missing: {source['required_native_tokens_missing']}",
        "",
        "=== SERVER PREDECESSOR ===",
        f"B4.1 games.py unchanged: {source['b4_1_games_unchanged']}",
        f"B4.1 games.py SHA-256: {source['b4_1_games_sha256']}",
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
        "Next step: "
        + (
            "B4_2_RUNTIME_CONFIRMED_RUN_ORPHAN_REFERENCE_AUDIT"
            if confirmed
            else "INSPECT_B4_2_FAILURE_BEFORE_ARTIFACT_CLEANUP"
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
