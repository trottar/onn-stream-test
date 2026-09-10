#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path


def run(args: list[str], timeout: float = 8.0) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return proc.returncode, (proc.stdout + "\n" + proc.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, "<timeout>"
    except OSError as exc:
        return 127, f"<os-error:{type(exc).__name__}>"


def decode_sdk_dir_value(value: str) -> str:
    # Android local.properties escapes the Windows drive colon and path
    # separators, e.g. C\:\\Users\\...  Match build_install_onn.ps1's
    # decoding without regex.
    return value.strip().replace(r"\:", ":").replace("\\\\", "\\")


def resolve_local_sdk(android_project: Path) -> str | None:
    path = android_project / "local.properties"
    if not path.is_file():
        return None

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()
    except OSError:
        return None

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        key, sep, value = stripped.partition("=")
        if not sep:
            continue

        if key.strip().casefold() != "sdk.dir":
            continue

        decoded = decode_sdk_dir_value(
            value
        )
        return decoded or None

    return None


def find_adb(root: Path) -> tuple[Path, str]:
    for name in ("adb.exe", "adb"):
        found = shutil.which(name)
        if found:
            return Path(found), "PATH"

    android_project = root / "PrivyHub"
    candidates: list[tuple[str, str]] = []

    if os.environ.get("ANDROID_SDK_ROOT"):
        candidates.append(
            (
                os.environ["ANDROID_SDK_ROOT"],
                "ANDROID_SDK_ROOT",
            )
        )

    if os.environ.get("ANDROID_HOME"):
        candidates.append(
            (
                os.environ["ANDROID_HOME"],
                "ANDROID_HOME",
            )
        )

    local_sdk = resolve_local_sdk(
        android_project
    )
    if local_sdk:
        candidates.append(
            (
                local_sdk,
                "local.properties",
            )
        )

    seen: set[str] = set()

    for base, source in candidates:
        normalized = os.path.normcase(
            os.path.normpath(
                os.path.expandvars(
                    os.path.expanduser(
                        base
                    )
                )
            )
        )
        if normalized in seen:
            continue
        seen.add(normalized)

        candidate = (
            Path(normalized)
            / "platform-tools"
            / "adb.exe"
        )

        if candidate.is_file():
            return candidate, source

    raise RuntimeError(
        "ADB could not be found through PATH, ANDROID_SDK_ROOT, "
        "ANDROID_HOME, or PrivyHub/local.properties"
    )


def parse_server_status(text: str) -> dict[str, str]:
    result: dict[str, str] = {}

    for raw in text.splitlines():
        stripped = raw.strip()
        key, sep, value = stripped.partition(":")
        if not sep:
            continue

        normalized = key.strip().casefold()
        if normalized in {
            "version",
            "mdns_enabled",
            "mdns_backend",
        }:
            result[
                normalized
            ] = value.strip()

    return result


def mdns_counts(text: str) -> dict[str, int]:
    lowered = text.casefold()

    return {
        "tls_connect": lowered.count(
            "_adb-tls-connect._tcp"
        ),
        "tls_pairing": lowered.count(
            "_adb-tls-pairing._tcp"
        ),
        "legacy_adb": lowered.count(
            "_adb._tcp"
        ),
    }


def device_counts(text: str) -> dict[str, int]:
    counts = {
        "device": 0,
        "offline": 0,
        "unauthorized": 0,
        "other": 0,
    }

    lines = text.splitlines()
    if lines and lines[0].strip().casefold().startswith(
        "list of devices"
    ):
        lines = lines[1:]

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if "\t" in line:
            status = line.rsplit(
                "\t",
                1,
            )[1].strip()
        else:
            parts = line.split()
            status = (
                parts[-1]
                if len(parts) >= 2
                else "other"
            )

        if status in counts:
            counts[
                status
            ] += 1
        else:
            counts[
                "other"
            ] += 1

    return counts


def safe_env(name: str) -> str:
    value = os.environ.get(
        name
    )

    if value is None:
        return "unset"

    if value in {
        "0",
        "1",
        "adb-tls-connect",
        "adb,adb-tls-connect",
    }:
        return value

    return "<custom>"


def script_summary(path: Path) -> list[str]:
    text = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    return [
        (
            "build script performs adb devices query: "
            + str(
                "$DeviceLines = & $Adb devices"
                in text
            )
        ),
        (
            "build script has immediate no-online-device failure: "
            + str(
                "No online ADB devices found."
                in text
            )
        ),
        (
            "build script invokes adb mdns services: "
            + str(
                "mdns services"
                in text.casefold()
            )
        ),
        (
            "build script invokes adb reconnect: "
            + str(
                "adb reconnect"
                in text.casefold()
                or "& $Adb reconnect"
                in text
            )
        ),
    ]


def main() -> int:
    root = Path(
        __file__
    ).resolve().parents[1]

    output = (
        root
        / "logs"
        / "android"
        / "adb_wireless_recovery_probe.txt"
    )
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    build = (
        root
        / "tools"
        / "build_install_onn.ps1"
    )

    if not build.is_file():
        raise RuntimeError(
            "tools/build_install_onn.ps1 is missing"
        )

    try:
        adb, source = find_adb(
            root
        )
    except Exception as exc:
        lines = [
            "PrivyHub persistent wireless ADB recovery audit v2",
            "Classification: ADB_BINARY_DISCOVERY_FAILED",
            "Production files modified by probe: NONE",
            "ADB pairing changed by probe: NONE",
            "Network addresses collected/logged: NONE",
            "Device serials/instance names logged: NONE",
            "",
            "=== ADB DISCOVERY ===",
            f"error type: {type(exc).__name__}",
            f"error: {exc}",
            f"local.properties exists: {(root / 'PrivyHub/local.properties').is_file()}",
            f"ANDROID_SDK_ROOT set: {bool(os.environ.get('ANDROID_SDK_ROOT'))}",
            f"ANDROID_HOME set: {bool(os.environ.get('ANDROID_HOME'))}",
            "",
            "=== BUILD TOOL ===",
            f"build_install_onn.ps1 sha256: {hashlib.sha256(build.read_bytes()).hexdigest()}",
            *script_summary(build),
        ]
        output.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
        print(
            "ADB_BINARY_DISCOVERY_FAILED"
        )
        print(
            "Log:",
            output,
        )
        return 1

    rc_version, version_text = run(
        [
            str(adb),
            "version",
        ]
    )
    version_line = (
        version_text.splitlines()[0].strip()
        if version_text
        else "<no output>"
    )

    rc_status, status_text = run(
        [
            str(adb),
            "server-status",
        ]
    )
    status = (
        parse_server_status(
            status_text
        )
        if rc_status == 0
        else {}
    )

    rc_check, _check_text = run(
        [
            str(adb),
            "mdns",
            "check",
        ]
    )

    rc_mdns, mdns_text = run(
        [
            str(adb),
            "mdns",
            "services",
        ]
    )

    mdns = (
        mdns_counts(
            mdns_text
        )
        if rc_mdns == 0
        else {
            "tls_connect": 0,
            "tls_pairing": 0,
            "legacy_adb": 0,
        }
    )

    rc_devices, devices_text = run(
        [
            str(adb),
            "devices",
        ]
    )

    devices = (
        device_counts(
            devices_text
        )
        if rc_devices == 0
        else {
            "device": 0,
            "offline": 0,
            "unauthorized": 0,
            "other": 0,
        }
    )

    if devices["device"] > 0:
        classification = (
            "ADB_TARGET_ALREADY_ONLINE"
        )
    elif status.get(
        "mdns_enabled",
        "",
    ).casefold() in {
        "false",
        "0",
        "no",
    }:
        classification = (
            "ADB_MDNS_DISABLED_TARGET_NOT_CONNECTED"
        )
    elif mdns[
        "tls_connect"
    ] > 0:
        classification = (
            "ADB_TLS_CONNECT_SERVICE_VISIBLE_TARGET_NOT_CONNECTED"
        )
    elif rc_mdns == 0:
        classification = (
            "ADB_TLS_CONNECT_SERVICE_NOT_DISCOVERED"
        )
    else:
        classification = (
            "ADB_MDNS_DIAGNOSTIC_UNAVAILABLE"
        )

    lines = [
        "PrivyHub persistent wireless ADB recovery audit v2",
        f"Classification: {classification}",
        "Production files modified by probe: NONE",
        "ADB pairing changed by probe: NONE",
        "Network addresses collected/logged: NONE",
        "Device serials/instance names logged: NONE",
        "",
        "=== BUILD TOOL ===",
        f"build_install_onn.ps1 sha256: {hashlib.sha256(build.read_bytes()).hexdigest()}",
        *script_summary(build),
        "",
        "=== ADB DISCOVERY ===",
        f"ADB discovery source: {source}",
        f"local.properties exists: {(root / 'PrivyHub/local.properties').is_file()}",
        "",
        "=== ADB ===",
        f"adb version command rc: {rc_version}",
        f"adb version: {version_line}",
        f"adb server-status supported: {rc_status == 0}",
        f"adb server version: {status.get('version', '<unavailable>')}",
        f"adb mdns_enabled: {status.get('mdns_enabled', '<unavailable>')}",
        f"adb mdns_backend: {status.get('mdns_backend', '<unavailable>')}",
        f"ADB_MDNS env: {safe_env('ADB_MDNS')}",
        f"ADB_MDNS_OPENSCREEN env: {safe_env('ADB_MDNS_OPENSCREEN')}",
        f"ADB_MDNS_AUTO_CONNECT env: {safe_env('ADB_MDNS_AUTO_CONNECT')}",
        f"adb mdns check supported: {rc_check == 0}",
        f"adb mdns services rc: {rc_mdns}",
        f"mDNS TLS-connect services discovered: {mdns['tls_connect']}",
        f"mDNS TLS-pairing services discovered: {mdns['tls_pairing']}",
        f"mDNS legacy ADB services discovered: {mdns['legacy_adb']}",
        f"adb devices rc: {rc_devices}",
        f"online device transports: {devices['device']}",
        f"offline device transports: {devices['offline']}",
        f"unauthorized device transports: {devices['unauthorized']}",
        f"other device transports: {devices['other']}",
    ]

    output.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(
        classification
    )
    print(
        "Log:",
        output,
    )
    return 0


def self_test() -> None:
    import tempfile

    assert decode_sdk_dir_value(
        r"C\:\\Users\\Example\\AppData\\Local\\Android\\Sdk"
    ) == r"C:\Users\Example\AppData\Local\Android\Sdk"

    with tempfile.TemporaryDirectory(
        prefix="privyhub_adb_probe_v2_"
    ) as td:
        root = Path(
            td
        )
        android = root / "PrivyHub"
        android.mkdir()

        sdk = root / "AndroidSdk"
        platform = sdk / "platform-tools"
        platform.mkdir(
            parents=True
        )
        fake_adb = platform / "adb.exe"
        fake_adb.write_bytes(
            b"fake"
        )

        encoded_sdk = str(
            sdk
        ).replace(
            "\\",
            "\\\\",
        ).replace(
            ":",
            "\\:",
        )

        (
            android
            / "local.properties"
        ).write_text(
            "sdk.dir="
            + encoded_sdk
            + "\n",
            encoding="utf-8",
        )

        resolved = resolve_local_sdk(
            android
        )
        assert resolved == str(
            sdk
        )

    assert device_counts(
        "List of devices attached\nserial\tdevice\n"
    )[
        "device"
    ] == 1

    assert mdns_counts(
        "x _adb-tls-connect._tcp y\n"
    )[
        "tls_connect"
    ] == 1

    print(
        "SELF-TEST PASSED"
    )


if __name__ == "__main__":
    import sys

    if "--self-test" in sys.argv:
        self_test()
        raise SystemExit(
            0
        )

    raise SystemExit(
        main()
    )
