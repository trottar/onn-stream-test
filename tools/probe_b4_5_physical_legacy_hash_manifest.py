#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b4_5_physical_legacy_hash_manifest_v1"
CLASSIFICATION = "B4_5_PHYSICAL_LEGACY_HASH_MANIFEST_CAPTURED"

EXPLICIT_GROUPS = (
    "runtime/streaming/sunshine",
    "runtime/downloads/sunshine",
    "runtime/downloads/moonlight",
    "data/games/sunshine",
    "scripts/setup_sunshine_portable.ps1",
    "scripts/install_sunshine_firewall.ps1",
    "scripts/remove_sunshine_firewall.ps1",
    "scripts/open_sunshine_web_ui.ps1",
    "scripts/install_moonlight_onn.ps1",
)

DISCOVERY_EXCLUDE_PREFIXES = (
    ".git/",
    "archive/",
    "docs/",
    "logs/",
    "tools/",
)

NON_TARGET_PATTERNS = (
    re.compile(r"^runtime/emulators/.*/moonlight_libretro\.info$", re.I),
    re.compile(r"^runtime/emulators/.*/stellabialek-moonlight-sillyness\.", re.I),
)
LEGACY_NAME = re.compile(r"sunshine|moonlight|limelight", re.I)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def is_non_target(rel: str) -> bool:
    return any(pattern.search(rel) for pattern in NON_TARGET_PATTERNS)


def file_entry(root: Path, path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": stat.st_size,
        "sha256": sha256_file(path),
        "is_symlink": path.is_symlink(),
    }


def group_manifest(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    result: dict[str, Any] = {
        "path": rel,
        "exists": path.exists(),
        "kind": "missing",
        "files": 0,
        "bytes": 0,
        "symlinks": 0,
        "manifest_sha256": None,
        "entries": [],
    }

    if not path.exists():
        return result

    if path.is_symlink():
        result["kind"] = "symlink"
        result["symlinks"] = 1
        return result

    entries: list[dict[str, Any]] = []

    if path.is_file():
        result["kind"] = "file"
        entries.append(file_entry(root, path))
    elif path.is_dir():
        result["kind"] = "directory"
        for item in sorted(
            path.rglob("*"),
            key=lambda value: value.relative_to(root).as_posix().casefold(),
        ):
            if item.is_symlink():
                entries.append({
                    "path": item.relative_to(root).as_posix(),
                    "bytes": 0,
                    "sha256": None,
                    "is_symlink": True,
                })
            elif item.is_file():
                entries.append(file_entry(root, item))
    else:
        result["kind"] = "other"
        return result

    canonical = hashlib.sha256()
    for entry in entries:
        canonical.update(entry["path"].encode("utf-8"))
        canonical.update(b"\0")
        canonical.update(str(entry["bytes"]).encode("ascii"))
        canonical.update(b"\0")
        canonical.update((entry["sha256"] or "<symlink>").encode("ascii"))
        canonical.update(b"\n")

    result["entries"] = entries
    result["files"] = sum(1 for entry in entries if not entry["is_symlink"])
    result["bytes"] = sum(int(entry["bytes"]) for entry in entries if not entry["is_symlink"])
    result["symlinks"] = sum(1 for entry in entries if entry["is_symlink"])
    result["manifest_sha256"] = canonical.hexdigest()
    return result


def discover_named_paths(root: Path) -> tuple[list[str], list[str]]:
    target: set[str] = set()
    non_target: set[str] = set()

    for current_root, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_root)
        rel_root = current.relative_to(root).as_posix() if current != root else ""
        kept_dirs = []

        for dirname in dirs:
            rel = f"{rel_root}/{dirname}" if rel_root else dirname
            if any(
                rel == prefix.rstrip("/") or rel.startswith(prefix)
                for prefix in DISCOVERY_EXCLUDE_PREFIXES
            ):
                continue
            kept_dirs.append(dirname)
            if LEGACY_NAME.search(dirname):
                (non_target if is_non_target(rel) else target).add(rel)

        dirs[:] = kept_dirs

        for filename in files:
            rel = f"{rel_root}/{filename}" if rel_root else filename
            if any(rel.startswith(prefix) for prefix in DISCOVERY_EXCLUDE_PREFIXES):
                continue
            if not LEGACY_NAME.search(filename):
                continue
            (non_target if is_non_target(rel) else target).add(rel)

    compact: list[str] = []
    for rel in sorted(target, key=lambda value: (value.count("/"), value.casefold())):
        if any(rel == parent or rel.startswith(parent.rstrip("/") + "/") for parent in compact):
            continue
        compact.append(rel)

    return sorted(compact, key=str.casefold), sorted(non_target, key=str.casefold)


def powershell_json(script: str) -> tuple[bool, Any, str]:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        return False, None, "POWERSHELL_UNAVAILABLE"

    try:
        completed = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20.0,
            check=False,
        )
    except Exception as exc:
        return False, None, type(exc).__name__

    if completed.returncode != 0:
        return False, None, "POWERSHELL_FAILED"

    text = completed.stdout.strip()
    if not text:
        return True, None, ""

    try:
        return True, json.loads(text), ""
    except json.JSONDecodeError:
        return False, None, "POWERSHELL_INVALID_JSON"


def windows_legacy_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "available": False,
        "error": "",
        "sunshine_process_count": None,
        "sunshine_service_count": None,
        "sunshine_task_count": None,
        "firewall_tcp_rule_count": None,
        "firewall_udp_rule_count": None,
        "firewall_enabled_rule_count": None,
    }

    script = r'''
$processCount = @(
    Get-Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.ProcessName -match '^(?i:sunshine|moonlight|limelight)$'
        }
).Count

$serviceCount = @(
    Get-CimInstance Win32_Service -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '(?i:sunshine|moonlight|limelight)' -or
            $_.DisplayName -match '(?i:sunshine|moonlight|limelight)'
        }
).Count

$taskCount = @(
    Get-ScheduledTask -ErrorAction SilentlyContinue |
        Where-Object {
            $_.TaskName -match '(?i:sunshine|moonlight|limelight)' -or
            $_.TaskPath -match '(?i:sunshine|moonlight|limelight)'
        }
).Count

$tcp = @(
    Get-NetFirewallRule -DisplayName 'PrivyHub Sunshine TCP' -ErrorAction SilentlyContinue
)
$udp = @(
    Get-NetFirewallRule -DisplayName 'PrivyHub Sunshine UDP' -ErrorAction SilentlyContinue
)

$enabledCount = @(
    @($tcp) + @($udp) |
        Where-Object {
            $_.Enabled -eq 'True' -or $_.Enabled -eq $true
        }
).Count

[ordered]@{
    process_count = $processCount
    service_count = $serviceCount
    task_count = $taskCount
    firewall_tcp_rule_count = @($tcp).Count
    firewall_udp_rule_count = @($udp).Count
    firewall_enabled_rule_count = $enabledCount
} | ConvertTo-Json -Compress
'''

    ok, value, error = powershell_json(script)
    if not ok:
        state["error"] = error
        return state
    if not isinstance(value, dict):
        state["error"] = "POWERSHELL_NON_OBJECT"
        return state

    state["available"] = True
    state["sunshine_process_count"] = int(value.get("process_count", 0))
    state["sunshine_service_count"] = int(value.get("service_count", 0))
    state["sunshine_task_count"] = int(value.get("task_count", 0))
    state["firewall_tcp_rule_count"] = int(value.get("firewall_tcp_rule_count", 0))
    state["firewall_udp_rule_count"] = int(value.get("firewall_udp_rule_count", 0))
    state["firewall_enabled_rule_count"] = int(value.get("firewall_enabled_rule_count", 0))
    return state


def adb_moonlight_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "adb_available": False,
        "connected_target_count": 0,
        "ready_target_count": 0,
        "moonlight_installed_target_count": 0,
        "connection_attempted": False,
        "identifiers_logged": False,
        "error": "",
    }

    adb = shutil.which("adb.exe") or shutil.which("adb")
    if not adb:
        state["error"] = "ADB_UNAVAILABLE"
        return state

    state["adb_available"] = True

    try:
        devices = subprocess.run(
            [adb, "devices"],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=12.0,
            check=False,
        )
    except Exception as exc:
        state["error"] = type(exc).__name__
        return state

    if devices.returncode != 0:
        state["error"] = "ADB_DEVICES_FAILED"
        return state

    ready_serials: list[str] = []
    connected = 0

    for line in devices.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices") or "\t" not in line:
            continue
        serial, status = line.split("\t", 1)
        connected += 1
        if status.strip() == "device":
            ready_serials.append(serial)

    installed = 0
    for serial in ready_serials:
        try:
            completed = subprocess.run(
                [adb, "-s", serial, "shell", "pm", "path", "com.limelight"],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=12.0,
                check=False,
            )
        except Exception:
            continue

        if (
            completed.returncode == 0
            and any(line.strip().startswith("package:") for line in completed.stdout.splitlines())
        ):
            installed += 1

    state["connected_target_count"] = connected
    state["ready_target_count"] = len(ready_serials)
    state["moonlight_installed_target_count"] = installed
    return state


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="privyhub_b45_manifest_test_") as temp_name:
        root = Path(temp_name)
        group = root / "runtime/streaming/sunshine"
        group.mkdir(parents=True, exist_ok=True)
        (group / "a.bin").write_bytes(b"a")
        (group / "b.bin").write_bytes(b"bb")

        first = group_manifest(root, "runtime/streaming/sunshine")
        second = group_manifest(root, "runtime/streaming/sunshine")
        assert first["manifest_sha256"] == second["manifest_sha256"]
        assert first["files"] == 2
        assert first["bytes"] == 3

        collision = root / "runtime/emulators/x/moonlight_libretro.info"
        collision.parent.mkdir(parents=True, exist_ok=True)
        collision.write_text("x", encoding="utf-8")

        target, non_target = discover_named_paths(root)
        assert "runtime/streaming/sunshine" in target
        assert "runtime/emulators/x/moonlight_libretro.info" in non_target

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    groups = [group_manifest(root, rel) for rel in EXPLICIT_GROUPS]
    discovered, non_targets = discover_named_paths(root)

    additional = []
    for rel in discovered:
        if any(
            rel == group or rel.startswith(group.rstrip("/") + "/")
            for group in EXPLICIT_GROUPS
        ):
            continue
        additional.append(rel)

    discovered_groups = [group_manifest(root, rel) for rel in additional]
    all_groups = groups + discovered_groups

    windows_state = windows_legacy_state()
    adb_state = adb_moonlight_state()

    total_files = sum(int(group["files"]) for group in all_groups)
    total_bytes = sum(int(group["bytes"]) for group in all_groups)
    symlinks = sum(int(group["symlinks"]) for group in all_groups)

    active_system = False
    cleanup_actions: list[str] = []

    if windows_state["available"]:
        if (
            windows_state["sunshine_process_count"]
            or windows_state["sunshine_service_count"]
            or windows_state["sunshine_task_count"]
        ):
            active_system = True
        if (
            windows_state["firewall_tcp_rule_count"]
            or windows_state["firewall_udp_rule_count"]
        ):
            cleanup_actions.append("REMOVE_SUNSHINE_FIREWALL_RULES")
    else:
        cleanup_actions.append("VERIFY_WINDOWS_LEGACY_STATE")

    if adb_state["moonlight_installed_target_count"] > 0:
        cleanup_actions.append("UNINSTALL_COM_LIMELIGHT_FROM_CONNECTED_TARGETS")

    if symlinks:
        cleanup_actions.append("INSPECT_SYMLINKS_BEFORE_DELETE")

    if active_system:
        disposition = "B4_5_ACTIVE_LEGACY_SYSTEM_STATE_INSPECT_BEFORE_CLEANUP"
    elif cleanup_actions:
        disposition = "B4_5_HASH_MANIFEST_CAPTURED_CLEANUP_ACTIONS_REQUIRED"
    else:
        disposition = "B4_5_HASH_MANIFEST_CAPTURED_READY_FOR_PHYSICAL_CLEANUP"

    report = {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "production_files_modified_by_probe": "NONE",
        "files_deleted_by_probe": 0,
        "network_addresses_collected_or_logged": "NONE",
        "group_count": len(all_groups),
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_symlinks": symlinks,
        "explicit_groups": groups,
        "additional_discovered_groups": discovered_groups,
        "non_target_name_collisions": non_targets,
        "windows_legacy_state": windows_state,
        "adb_moonlight_state": adb_state,
        "cleanup_actions_required": cleanup_actions,
        "disposition": disposition,
    }

    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "b4_5_physical_legacy_hash_manifest.json"
    text_path = out_dir / "b4_5_physical_legacy_hash_manifest.txt"

    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "PrivyHub B4.5 physical legacy artifact hash manifest",
        f"Classification: {CLASSIFICATION}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Files deleted by probe: 0",
        "Network addresses collected/logged: NONE",
        "",
        "=== HASHED TARGET GROUPS ===",
        f"Group count: {len(all_groups)}",
        f"Total files: {total_files}",
        f"Total bytes: {total_bytes}",
        f"Symlinks/reparse-like path count: {symlinks}",
    ]

    for group in all_groups:
        lines.append(
            f"{group['path']}: exists={group['exists']} kind={group['kind']} "
            f"files={group['files']} bytes={group['bytes']} symlinks={group['symlinks']} "
            f"manifest_sha256={group['manifest_sha256'] or '<none>'}"
        )
        if group["kind"] == "file" and group["entries"]:
            lines.append(f"  file_sha256={group['entries'][0]['sha256']}")

    lines += [
        "",
        "=== ADDITIONAL DISCOVERY ===",
        f"Additional target groups discovered: {len(discovered_groups)}",
    ]
    for group in discovered_groups:
        lines.append(f"  {group['path']}")

    lines.append(f"Explicit non-target name collisions preserved: {len(non_targets)}")
    for rel in non_targets[:40]:
        lines.append(f"  NON_TARGET {rel}")
    if len(non_targets) > 40:
        lines.append(
            f"  ... {len(non_targets) - 40} additional non-target collisions retained in JSON."
        )

    lines += [
        "",
        "=== WINDOWS LEGACY SYSTEM STATE ===",
        f"State available: {windows_state['available']}",
        f"State error: {windows_state['error'] or '<none>'}",
        f"Sunshine/Moonlight process count: {windows_state['sunshine_process_count']}",
        f"Sunshine/Moonlight service count: {windows_state['sunshine_service_count']}",
        f"Sunshine/Moonlight scheduled-task count: {windows_state['sunshine_task_count']}",
        f"PrivyHub Sunshine TCP firewall-rule count: {windows_state['firewall_tcp_rule_count']}",
        f"PrivyHub Sunshine UDP firewall-rule count: {windows_state['firewall_udp_rule_count']}",
        f"Enabled PrivyHub Sunshine firewall-rule count: {windows_state['firewall_enabled_rule_count']}",
        "",
        "=== CONNECTED ANDROID STATE ===",
        f"ADB available: {adb_state['adb_available']}",
        f"Connected target count: {adb_state['connected_target_count']}",
        f"Ready target count: {adb_state['ready_target_count']}",
        f"Moonlight/com.limelight installed target count: {adb_state['moonlight_installed_target_count']}",
        f"ADB connection attempted: {adb_state['connection_attempted']}",
        f"Device identifiers logged: {adb_state['identifiers_logged']}",
        f"ADB error: {adb_state['error'] or '<none>'}",
        "",
        "=== CLEANUP ACTIONS ===",
        "Required actions: " + json.dumps(cleanup_actions),
        "",
        "=== DISPOSITION ===",
        disposition,
        "",
        "Full sorted per-file hashes are in:",
        "logs/diagnostics/b4_5_physical_legacy_hash_manifest.json",
        "",
        "No artifact deletion is authorized until this manifest is reviewed.",
    ]

    text_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(CLASSIFICATION)
    print("Disposition:", disposition)
    print("Text:", text_path)
    print("JSON:", json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
