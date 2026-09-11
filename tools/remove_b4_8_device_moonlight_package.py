#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCHEMA = "privyhub_b4_8_device_moonlight_removal_v1"
OK = "B4_8_DEVICE_MOONLIGHT_REMOVAL_CONFIRMED"
NOT_INSTALLED = "B4_8_DEVICE_MOONLIGHT_ALREADY_ABSENT"
FAIL = "B4_8_DEVICE_MOONLIGHT_REMOVAL_NOT_CONFIRMED"

MOONLIGHT_PACKAGE = "com.limelight"
PRIVYHUB_PACKAGE = "com.safeiot.privyhub"

MDNS_RE = re.compile(r"^adb-.*\._adb-tls-connect\._tcp$")
NETWORK_SERIAL_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d+$")


def decode_local_properties_sdk(path: Path) -> str | None:
    if not path.is_file():
        return None

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None

    for line in text.splitlines():
        match = re.match(
            r"^\s*sdk\.dir\s*=(.*)$",
            line,
        )
        if not match:
            continue

        value = match.group(1).strip()
        value = value.replace(r"\:", ":")
        value = value.replace(r"\\", "\\")
        return value or None

    return None


def find_adb(root: Path) -> tuple[str | None, str]:
    for command in ("adb.exe", "adb"):
        found = shutil.which(command)
        if found:
            return found, "PATH"

    candidates: list[tuple[str, Path]] = []

    for env_name in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        value = os.environ.get(env_name)
        if value:
            candidates.append((env_name, Path(value)))

    local_sdk = decode_local_properties_sdk(
        root / "PrivyHub" / "local.properties"
    )
    if local_sdk:
        candidates.append(("local.properties", Path(local_sdk)))

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(
            (
                "LOCALAPPDATA_ANDROID_SDK",
                Path(local_app_data) / "Android" / "Sdk",
            )
        )

    seen: set[str] = set()

    for source, sdk_root in candidates:
        key = str(sdk_root).casefold()
        if key in seen:
            continue
        seen.add(key)

        adb = sdk_root / "platform-tools" / "adb.exe"
        if adb.is_file():
            return str(adb), source

    return None, "NOT_FOUND"


def run(
    args: list[str],
    *,
    timeout: float = 12.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def online_devices(adb: str) -> list[str]:
    result = run([adb, "devices"])
    if result.returncode != 0:
        return []

    devices: list[str] = []
    for line in result.stdout.splitlines()[1:]:
        line = line.strip()
        if "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        if state.strip() == "device":
            devices.append(serial.strip())

    return devices


def physical_candidates(devices: list[str]) -> list[str]:
    result: list[str] = []

    for value in devices:
        if value == "emulator-5554":
            continue

        if (
            MDNS_RE.fullmatch(value)
            or NETWORK_SERIAL_RE.fullmatch(value)
        ):
            result.append(value)

    return result


def target_online(adb: str, target: str) -> bool:
    if not target:
        return False

    result = run(
        [
            adb,
            "-s",
            target,
            "get-state",
        ]
    )

    return (
        result.returncode == 0
        and result.stdout.strip() == "device"
    )


def try_connect(adb: str, target: str) -> bool:
    if not target:
        return False

    run([adb, "connect", target])
    time.sleep(0.75)
    return target_online(adb, target)


def private_cache_path() -> Path | None:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None

    return (
        Path(local_app_data)
        / "PrivyHub"
        / "adb"
        / "last_wireless_target.txt"
    )


def read_cached_target() -> str | None:
    path = private_cache_path()
    if path is None or not path.is_file():
        return None

    try:
        value = path.read_text(
            encoding="utf-8-sig",
            errors="replace",
        ).strip()
    except OSError:
        return None

    if (
        MDNS_RE.fullmatch(value)
        or NETWORK_SERIAL_RE.fullmatch(value)
    ):
        return value

    return None


def mdns_targets(adb: str) -> list[str]:
    result = run(
        [
            adb,
            "mdns",
            "services",
        ]
    )
    if result.returncode != 0:
        return []

    targets: list[str] = []

    for line in result.stdout.splitlines():
        parts = line.strip().split("\t")
        if len(parts) < 2:
            continue

        instance = parts[0].strip()
        service = parts[1].strip()

        if (
            instance
            and service == "_adb-tls-connect._tcp"
        ):
            targets.append(f"{instance}.{service}")

    return list(dict.fromkeys(targets))


def resolve_online(adb: str) -> tuple[str | None, str]:
    candidates = physical_candidates(
        online_devices(adb)
    )

    if len(candidates) == 1:
        return candidates[0], "online"

    mdns = [
        item
        for item in candidates
        if MDNS_RE.fullmatch(item)
    ]
    if len(mdns) == 1:
        return mdns[0], "online-mdns"

    return None, ""


def resolve_with_recovery(
    adb: str,
) -> tuple[str | None, str, bool]:
    connection_attempted = False
    cached = read_cached_target()

    if cached:
        if target_online(adb, cached):
            return cached, "cached-online", connection_attempted

        connection_attempted = True
        if try_connect(adb, cached):
            return cached, "cached-recovery", connection_attempted

    online, source = resolve_online(adb)
    if online:
        return online, source, connection_attempted

    for _attempt in range(3):
        for target in mdns_targets(adb):
            connection_attempted = True
            if try_connect(adb, target):
                return target, "mdns-recovery", connection_attempted

        online, source = resolve_online(adb)
        if online:
            return online, source, connection_attempted

        time.sleep(1.0)

    run([adb, "reconnect", "offline"])
    time.sleep(0.75)

    online, source = resolve_online(adb)
    if online:
        return online, "reconnect", connection_attempted

    run([adb, "kill-server"])
    time.sleep(0.5)
    run([adb, "start-server"])
    time.sleep(1.0)

    if cached:
        connection_attempted = True
        if try_connect(adb, cached):
            return (
                cached,
                "cached-after-server-restart",
                connection_attempted,
            )

    for _attempt in range(3):
        online, source = resolve_online(adb)
        if online:
            return (
                online,
                "online-after-server-restart",
                connection_attempted,
            )

        for target in mdns_targets(adb):
            connection_attempted = True
            if try_connect(adb, target):
                return (
                    target,
                    "mdns-after-server-restart",
                    connection_attempted,
                )

        time.sleep(1.0)

    return None, "", connection_attempted


def package_present(
    adb: str,
    target: str,
    package: str,
) -> tuple[bool, str]:
    result = run(
        [
            adb,
            "-s",
            target,
            "shell",
            "pm",
            "path",
            package,
        ]
    )

    if result.returncode != 0:
        return False, "PACKAGE_QUERY_FAILED"

    return "package:" in result.stdout, ""


def uninstall_package(
    adb: str,
    target: str,
    package: str,
) -> tuple[bool, str]:
    result = run(
        [
            adb,
            "-s",
            target,
            "uninstall",
            package,
        ],
        timeout=30.0,
    )

    output = result.stdout.strip()
    success = (
        result.returncode == 0
        and "success" in output.casefold()
    )

    if success:
        return True, ""

    return False, "ADB_UNINSTALL_FAILED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        assert MDNS_RE.fullmatch(
            "adb-fixture._adb-tls-connect._tcp"
        )
        assert NETWORK_SERIAL_RE.fullmatch(
            ".".join(("192", "0", "2", "10")) + ":5555"
        )
        return 0

    root = Path(args.root).resolve()

    adb, adb_source = find_adb(root)

    target = None
    recovery_source = ""
    connection_attempted = False
    privyhub_before = False
    privyhub_after = False
    moonlight_before = False
    moonlight_after = False
    uninstall_attempted = False
    uninstall_command_success = False
    error = ""

    if adb:
        (
            target,
            recovery_source,
            connection_attempted,
        ) = resolve_with_recovery(adb)

    if not adb:
        error = "ADB_NOT_FOUND"
    elif not target:
        error = "PHYSICAL_TARGET_NOT_RESOLVED"
    else:
        privyhub_before, query_error = package_present(
            adb,
            target,
            PRIVYHUB_PACKAGE,
        )

        if query_error:
            error = query_error
        elif not privyhub_before:
            error = "PRIVYHUB_PACKAGE_NOT_PRESENT"
        else:
            moonlight_before, query_error = package_present(
                adb,
                target,
                MOONLIGHT_PACKAGE,
            )

            if query_error:
                error = query_error
            elif moonlight_before:
                uninstall_attempted = True
                (
                    uninstall_command_success,
                    uninstall_error,
                ) = uninstall_package(
                    adb,
                    target,
                    MOONLIGHT_PACKAGE,
                )

                if uninstall_error:
                    error = uninstall_error

            if not error or uninstall_attempted:
                # Always verify final package states after an uninstall attempt,
                # even if adb returned a failure string.
                privyhub_after, privyhub_error = package_present(
                    adb,
                    target,
                    PRIVYHUB_PACKAGE,
                )
                moonlight_after, moonlight_error = package_present(
                    adb,
                    target,
                    MOONLIGHT_PACKAGE,
                )

                if privyhub_error:
                    error = privyhub_error
                elif moonlight_error:
                    error = moonlight_error

    if (
        adb
        and target
        and privyhub_before
        and not error
        and not moonlight_before
        and privyhub_after
        and not moonlight_after
    ):
        classification = NOT_INSTALLED
    elif (
        adb
        and target
        and privyhub_before
        and privyhub_after
        and moonlight_before
        and uninstall_attempted
        and uninstall_command_success
        and not moonlight_after
        and not error
    ):
        classification = OK
    else:
        classification = FAIL

    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    text_path = (
        out_dir
        / "b4_8_device_moonlight_removal.txt"
    )

    lines = [
        "PrivyHub B4.8 device Moonlight package removal",
        f"Classification: {classification}",
        f"Schema: {SCHEMA}",
        "Project production files modified by action: NONE",
        "Network addresses collected/logged: NONE",
        "Device identifiers logged: NONE",
        "",
        "=== PRIVATE ADB RESOLUTION ===",
        f"ADB available: {adb is not None}",
        f"ADB discovery source: {adb_source}",
        f"Physical target resolved: {target is not None}",
        f"Recovery source: {recovery_source or '<none>'}",
        f"ADB connection attempted: {connection_attempted}",
        "",
        "=== PACKAGE STATE ===",
        f"PrivyHub present before removal: {privyhub_before}",
        f"Moonlight/com.limelight present before removal: {moonlight_before}",
        f"Moonlight uninstall attempted: {uninstall_attempted}",
        f"ADB uninstall command success: {uninstall_command_success}",
        f"PrivyHub present after removal: {privyhub_after}",
        f"Moonlight/com.limelight present after removal: {moonlight_after}",
        f"Error: {error or '<none>'}",
        "",
        "Next step: "
        + (
            "B4_8_DEVICE_MOONLIGHT_REMOVAL_CONFIRMED_BEGIN_B5_NATIVE_ONLY_REGRESSION"
            if classification in (OK, NOT_INSTALLED)
            else "INSPECT_B4_8_DEVICE_PACKAGE_REMOVAL_FAILURE_BEFORE_B5"
        ),
    ]

    text_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(classification)
    print("Text:", text_path)

    return 0 if classification in (OK, NOT_INSTALLED) else 1


if __name__ == "__main__":
    raise SystemExit(main())
