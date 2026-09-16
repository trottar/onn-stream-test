#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import hashlib
import ipaddress
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


NETWORK_TARGET_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d+$")
MDNS_TARGET_RE = re.compile(r"^adb-.*\._adb-tls-connect\._tcp$")
REPRESENTATIVE_ONN_EPHEMERAL_RANGE = (32768, 60999)
DEBUG_ENDPOINTS = False
DEBUG_WATCH_PORT: int | None = None


def debug_endpoint(message: str) -> None:
    if DEBUG_ENDPOINTS:
        print(f"[endpoint-debug] {message}", flush=True)


def parse_debug_watch_port(argv: list[str]) -> int | None:
    value: str | None = None
    for index, arg in enumerate(argv):
        if arg.startswith("--debug-watch-port="):
            value = arg.split("=", 1)[1]
            break
        if arg == "--debug-watch-port":
            if index + 1 >= len(argv):
                raise ValueError("--debug-watch-port requires a TCP port")
            value = argv[index + 1]
            break
    if value is None:
        return None
    try:
        port = int(value, 10)
    except ValueError as exc:
        raise ValueError("--debug-watch-port must be an integer TCP port") from exc
    if not 1 <= port <= 65535:
        raise ValueError("--debug-watch-port must be between 1 and 65535")
    return port


@dataclass(frozen=True)
class Resolution:
    target: str
    source: str


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
        decoded = decode_sdk_dir_value(value)
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
        candidates.append((os.environ["ANDROID_SDK_ROOT"], "ANDROID_SDK_ROOT"))
    if os.environ.get("ANDROID_HOME"):
        candidates.append((os.environ["ANDROID_HOME"], "ANDROID_HOME"))

    local_sdk = resolve_local_sdk(android_project)
    if local_sdk:
        candidates.append((local_sdk, "local.properties"))

    seen: set[str] = set()
    adb_name = "adb.exe" if os.name == "nt" else "adb"

    for base, source in candidates:
        normalized = os.path.normcase(
            os.path.normpath(
                os.path.expandvars(os.path.expanduser(base))
            )
        )
        if normalized in seen:
            continue
        seen.add(normalized)

        candidate = Path(normalized) / "platform-tools" / adb_name
        if candidate.is_file():
            return candidate, source

    raise RuntimeError(
        "ADB could not be found through PATH, ANDROID_SDK_ROOT, "
        "ANDROID_HOME, or PrivyHub/local.properties"
    )


def private_cache_path() -> tuple[Path, str]:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return (
                Path(base) / "PrivyHub" / "adb" / "last_wireless_target.txt",
                "windows-localappdata",
            )
        return (
            Path.home() / "AppData" / "Local" / "PrivyHub" / "adb" / "last_wireless_target.txt",
            "windows-home-fallback",
        )

    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return (
            Path(xdg_state) / "privyhub" / "adb" / "last_wireless_target.txt",
            "linux-xdg-state",
        )

    return (
        Path.home() / ".local" / "state" / "privyhub" / "adb" / "last_wireless_target.txt",
        "linux-user-state",
    )


def private_host_cache_path() -> Path:
    target_path, _scope = private_cache_path()
    return target_path.with_name("last_wireless_host.txt")


def private_port_range_cache_path() -> Path:
    target_path, _scope = private_cache_path()
    return target_path.with_name("last_wireless_port_range.txt")


def normalize_ipv4(value: str | None) -> str | None:
    if not value:
        return None
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        return None
    if address.version != 4 or address.is_unspecified or address.is_multicast:
        return None
    return str(address)


def host_from_target(target: str | None) -> str | None:
    if not target or not NETWORK_TARGET_RE.fullmatch(target):
        return None
    host, _sep, _port = target.rpartition(":")
    return normalize_ipv4(host)


def read_cached_host(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return None
    return normalize_ipv4(value)


def save_cached_host(path: Path, host: str) -> bool:
    normalized = normalize_ipv4(host)
    if normalized is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(normalized, encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return True
    except OSError:
        return False


def parse_port_range(text: str) -> tuple[int, int] | None:
    parts = text.strip().split()
    if len(parts) != 2:
        return None
    try:
        start, end = (int(parts[0]), int(parts[1]))
    except ValueError:
        return None
    if not (1 <= start <= end <= 65535):
        return None
    return start, end


def read_cached_port_range(path: Path) -> tuple[int, int] | None:
    try:
        value = path.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    return parse_port_range(value)


def save_cached_port_range(path: Path, port_range: tuple[int, int]) -> bool:
    start, end = port_range
    if not (1 <= start <= end <= 65535):
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{start} {end}\n", encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return True
    except OSError:
        return False


def query_device_port_range(adb: Path, target: str) -> tuple[int, int] | None:
    if not is_valid_target(target):
        return None
    rc, text = run(
        [
            str(adb),
            "-s",
            target,
            "shell",
            "cat",
            "/proc/sys/net/ipv4/ip_local_port_range",
        ],
        timeout=5.0,
    )
    if rc != 0:
        return None
    return parse_port_range(text)


def resolve_private_port_range(path: Path) -> tuple[tuple[int, int], str]:
    cached = read_cached_port_range(path)
    if cached is not None:
        return cached, "private-port-range-cache"
    return REPRESENTATIVE_ONN_EPHEMERAL_RANGE, "representative-onn-runtime-evidence"


def resolve_private_host(cached_target: str | None, host_cache_path: Path) -> tuple[str | None, str]:
    from_target = host_from_target(cached_target)
    if from_target is not None:
        return from_target, "cached-endpoint"

    cached_host = read_cached_host(host_cache_path)
    if cached_host is not None:
        return cached_host, "private-host-cache"

    env_host = normalize_ipv4(os.environ.get("PRIVYHUB_ONN_HOST"))
    if env_host is not None:
        return env_host, "private-environment"

    return None, "unavailable"


def is_valid_target(value: str) -> bool:
    return bool(MDNS_TARGET_RE.fullmatch(value) or NETWORK_TARGET_RE.fullmatch(value))


def read_cached_target(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return None
    return value if is_valid_target(value) else None


def save_cached_target(path: Path, target: str) -> bool:
    if not is_valid_target(target):
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(target, encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return True
    except OSError:
        return False


def parse_server_status(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        stripped = raw.strip()
        key, sep, value = stripped.partition(":")
        if not sep:
            continue
        normalized = key.strip().casefold()
        if normalized in {"version", "mdns_enabled", "mdns_backend"}:
            result[normalized] = value.strip()
    return result


def mdns_counts(text: str) -> dict[str, int]:
    lowered = text.casefold()
    return {
        "tls_connect": lowered.count("_adb-tls-connect._tcp"),
        "tls_pairing": lowered.count("_adb-tls-pairing._tcp"),
        "legacy_adb": lowered.count("_adb._tcp"),
    }


def parse_device_rows(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.casefold().startswith("list of devices"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        rows.append((parts[0], parts[1]))
    return rows


def device_counts(text: str) -> dict[str, int]:
    counts = {"device": 0, "offline": 0, "unauthorized": 0, "other": 0}
    for _target, status in parse_device_rows(text):
        if status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
    return counts


def get_online_devices(adb: Path) -> list[str]:
    rc, text = run([str(adb), "devices"])
    if rc != 0:
        return []
    return [target for target, status in parse_device_rows(text) if status == "device"]


def get_physical_onn_candidates(online_devices: Iterable[str]) -> list[str]:
    result: list[str] = []
    for target in online_devices:
        if target == "emulator-5554":
            continue
        if is_valid_target(target):
            result.append(target)
    return result


def resolve_online_onn(adb: Path) -> str | None:
    candidates = get_physical_onn_candidates(get_online_devices(adb))
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        mdns = [target for target in candidates if MDNS_TARGET_RE.fullmatch(target)]
        if len(mdns) == 1:
            return mdns[0]
    return None


def parse_mdns_connect_targets(text: str) -> list[str]:
    targets: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        instance = parts[0].strip()
        service_index = next(
            (i for i, item in enumerate(parts) if item == "_adb-tls-connect._tcp"),
            -1,
        )
        if service_index < 0:
            continue
        target = f"{instance}._adb-tls-connect._tcp"
        if is_valid_target(target) and target not in targets:
            targets.append(target)
    return targets


def get_mdns_connect_targets(adb: Path) -> list[str]:
    rc, text = run([str(adb), "mdns", "services"])
    if rc != 0:
        return []
    return parse_mdns_connect_targets(text)


def test_adb_target_online(adb: Path, target: str) -> bool:
    if not is_valid_target(target):
        return False
    rc, text = run([str(adb), "-s", target, "get-state"], timeout=5.0)
    return rc == 0 and text.strip().splitlines()[-1:] == ["device"]


def try_adb_connect_target(adb: Path, target: str) -> bool:
    if not is_valid_target(target):
        return False
    debug_endpoint(f"adb connect attempt: {target}")
    rc, _text = run([str(adb), "connect", target], timeout=8.0)
    debug_endpoint(f"adb connect rc={rc}: {target}")
    if rc != 0:
        return False
    time.sleep(0.75)
    online = test_adb_target_online(adb, target)
    debug_endpoint(f"adb get-state {'PASS' if online else 'FAIL'}: {target}")
    return online


def resolve_with_recovery(
    adb: Path,
    cached: str | None,
    private_host: str | None,
    port_range: tuple[int, int],
) -> tuple[Resolution | None, list[str]]:
    trace: list[str] = []

    if cached:
        debug_endpoint(f"cached target: {cached}")
        trace.append("cached-target-present")
        if test_adb_target_online(adb, cached) or try_adb_connect_target(adb, cached):
            trace.append("cached-target-recovered")
            return Resolution(cached, "cached"), trace
        trace.append("cached-target-not-online")
    else:
        trace.append("cached-target-absent")

    if private_host is not None:
        debug_endpoint(f"private host: {private_host}; scan range: {port_range[0]}-{port_range[1]}")
        trace.append("private-host-present")
        refreshed, open_count, overflow = try_refresh_endpoint_on_host(adb, private_host, port_range)
        trace.append(f"private-host-open-port-count:{open_count}")
        trace.append(f"private-host-open-port-overflow:{overflow}")
        if refreshed is not None:
            trace.append("private-host-port-refresh-recovered")
            return Resolution(refreshed, "port-refresh"), trace
    else:
        trace.append("private-host-absent")

    online = resolve_online_onn(adb)
    if online:
        trace.append("online-target-found")
        return Resolution(online, "online"), trace
    trace.append("online-target-absent")

    for attempt in range(1, 4):
        mdns_targets = get_mdns_connect_targets(adb)
        trace.append(f"mdns-attempt-{attempt}-targets:{len(mdns_targets)}")
        for target in mdns_targets:
            if try_adb_connect_target(adb, target):
                trace.append(f"mdns-attempt-{attempt}-recovered")
                return Resolution(target, "mdns"), trace

        online = resolve_online_onn(adb)
        if online:
            trace.append(f"online-after-mdns-attempt-{attempt}")
            return Resolution(online, "online"), trace

        if attempt < 3:
            time.sleep(2.0)

    run([str(adb), "reconnect", "offline"], timeout=8.0)
    trace.append("reconnect-offline-issued")
    time.sleep(1.0)

    online = resolve_online_onn(adb)
    if online:
        trace.append("reconnect-recovered")
        return Resolution(online, "reconnect"), trace

    run([str(adb), "kill-server"], timeout=8.0)
    trace.append("adb-server-killed")
    time.sleep(0.75)
    run([str(adb), "start-server"], timeout=8.0)
    trace.append("adb-server-started")
    time.sleep(2.0)

    if cached and try_adb_connect_target(adb, cached):
        trace.append("cached-after-server-restart-recovered")
        return Resolution(cached, "cached-after-server-restart"), trace

    if private_host is not None:
        debug_endpoint(f"private host after server restart: {private_host}; scan range: {port_range[0]}-{port_range[1]}")
        refreshed, open_count, overflow = try_refresh_endpoint_on_host(adb, private_host, port_range)
        trace.append(f"private-host-after-server-restart-open-port-count:{open_count}")
        trace.append(f"private-host-after-server-restart-open-port-overflow:{overflow}")
        if refreshed is not None:
            trace.append("private-host-after-server-restart-port-refresh-recovered")
            return Resolution(refreshed, "port-refresh-after-server-restart"), trace

    for attempt in range(1, 4):
        online = resolve_online_onn(adb)
        if online:
            trace.append(f"online-after-server-restart-attempt-{attempt}")
            return Resolution(online, "online-after-server-restart"), trace

        mdns_targets = get_mdns_connect_targets(adb)
        trace.append(
            f"mdns-after-server-restart-attempt-{attempt}-targets:{len(mdns_targets)}"
        )
        for target in mdns_targets:
            if try_adb_connect_target(adb, target):
                trace.append(f"mdns-after-server-restart-attempt-{attempt}-recovered")
                return Resolution(target, "mdns-after-server-restart"), trace

        if attempt < 3:
            time.sleep(2.0)

    trace.append("automatic-recovery-exhausted")
    return None, trace


def _tcp_port_open(host: str, port: int, timeout: float) -> int | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return port if sock.connect_ex((host, port)) == 0 else None
    except OSError:
        return None
    finally:
        sock.close()


def find_open_tcp_ports(
    host: str,
    start_port: int,
    end_port: int,
    workers: int = 256,
    timeout: float = 0.06,
    max_open_ports: int = 64,
) -> tuple[list[int], bool]:
    normalized = normalize_ipv4(host)
    if normalized is None:
        return [], False
    if not (1 <= start_port <= end_port <= 65535):
        raise ValueError("invalid TCP port scan range")

    open_ports: list[int] = []
    overflow = False
    batch_size = max(workers * 8, 512)
    watch_in_range = (
        DEBUG_WATCH_PORT is not None
        and start_port <= DEBUG_WATCH_PORT <= end_port
    )
    watch_completed = False

    if DEBUG_WATCH_PORT is not None:
        if watch_in_range:
            debug_endpoint(
                f"WATCH port {DEBUG_WATCH_PORT} is inside scan range "
                f"{start_port}-{end_port}"
            )
        else:
            debug_endpoint(
                f"WATCH port {DEBUG_WATCH_PORT} is OUTSIDE scan range "
                f"{start_port}-{end_port}"
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for batch_start in range(start_port, end_port + 1, batch_size):
            batch_end = min(end_port, batch_start + batch_size - 1)
            futures = {
                executor.submit(_tcp_port_open, normalized, port, timeout): port
                for port in range(batch_start, batch_end + 1)
            }
            if (
                watch_in_range
                and batch_start <= DEBUG_WATCH_PORT <= batch_end
            ):
                debug_endpoint(
                    f"WATCH port scheduled: {normalized}:{DEBUG_WATCH_PORT} "
                    f"in batch {batch_start}-{batch_end}"
                )
            for future in concurrent.futures.as_completed(futures):
                submitted_port = futures[future]
                port = future.result()
                if submitted_port == DEBUG_WATCH_PORT:
                    watch_completed = True
                    debug_endpoint(
                        f"WATCH port result: {normalized}:{submitted_port} "
                        + ("OPEN" if port is not None else "CLOSED/UNREACHABLE")
                    )
                if port is not None:
                    open_ports.append(port)
                    if len(open_ports) > max_open_ports:
                        overflow = True
                        break
            if overflow:
                for future in futures:
                    future.cancel()
                break

    if watch_in_range and not watch_completed:
        debug_endpoint(
            f"WATCH port {normalized}:{DEBUG_WATCH_PORT} was NOT COMPLETED "
            "before scan termination"
        )

    return sorted(set(open_ports)), overflow


def try_refresh_endpoint_on_host(
    adb: Path,
    host: str,
    port_range: tuple[int, int],
) -> tuple[str | None, int, bool]:
    start_port, end_port = port_range
    open_ports, overflow = find_open_tcp_ports(
        host,
        start_port=start_port,
        end_port=end_port,
    )
    if overflow:
        return None, len(open_ports), True

    for port in open_ports:
        target = f"{host}:{port}"
        debug_endpoint(f"open TCP candidate: {target}")
        if try_adb_connect_target(adb, target):
            return target, len(open_ports), False

    return None, len(open_ports), False


def safe_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        return "unset"
    if value in {"0", "1", "adb-tls-connect", "adb,adb-tls-connect"}:
        return value
    return "<custom>"


def script_summary(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lowered = text.casefold()
    return [
        f"build script has D-053 recovery marker: {'PRIVYHUB_ADB_WIRELESS_RECOVERY_01' in text}",
        f"build script has fail-soft recovery wrapper: {'Invoke-AdbRecoveryCommand' in text}",
        f"build script uses private cached target: {'last_wireless_target.txt' in text}",
        f"build script has mDNS recovery: {'Get-MdnsConnectTargets' in text}",
        f"build script has reconnect-offline recovery: {'reconnect' in lowered and 'offline' in lowered}",
        f"build script has ADB server restart recovery: {'kill-server' in text and 'start-server' in text}",
        f"build script has Wireless-debugging toggle fallback: {'toggle Wireless debugging Off, then On' in text}",
    ]


def snapshot(adb: Path) -> tuple[dict[str, int], dict[str, int], int, int]:
    rc_mdns, mdns_text = run([str(adb), "mdns", "services"])
    rc_devices, devices_text = run([str(adb), "devices"])
    mdns = (
        mdns_counts(mdns_text)
        if rc_mdns == 0
        else {"tls_connect": 0, "tls_pairing": 0, "legacy_adb": 0}
    )
    devices = (
        device_counts(devices_text)
        if rc_devices == 0
        else {"device": 0, "offline": 0, "unauthorized": 0, "other": 0}
    )
    return devices, mdns, rc_devices, rc_mdns


def classification_for(resolution: Resolution | None) -> str:
    if resolution is None:
        return "ADB_RECOVERY_EXHAUSTED_REPAIR_PAIRING_REQUIRED"
    mapping = {
        "cached": "ADB_TARGET_RECOVERED_CACHED",
        "online": "ADB_TARGET_ALREADY_ONLINE",
        "mdns": "ADB_TARGET_RECOVERED_MDNS",
        "reconnect": "ADB_TARGET_RECOVERED_RECONNECT",
        "cached-after-server-restart": "ADB_TARGET_RECOVERED_CACHED_AFTER_SERVER_RESTART",
        "online-after-server-restart": "ADB_TARGET_RECOVERED_ONLINE_AFTER_SERVER_RESTART",
        "mdns-after-server-restart": "ADB_TARGET_RECOVERED_MDNS_AFTER_SERVER_RESTART",
        "port-refresh": "ADB_TARGET_RECOVERED_EPHEMERAL_PORT_REFRESH",
        "port-refresh-after-server-restart": "ADB_TARGET_RECOVERED_EPHEMERAL_PORT_REFRESH_AFTER_SERVER_RESTART",
    }
    return mapping.get(resolution.source, "ADB_TARGET_RECOVERED")


def prompt_repair_and_retry() -> bool:
    if not sys.stdin.isatty():
        return False

    print(
        "Automatic wireless ADB recovery failed. "
        "If the existing pairing is stale, re-pair this Linux host on the onn now."
    )
    print(
        "Complete any pairing locally; do not copy network addresses or pairing "
        "details into the diagnostic log or chat."
    )
    try:
        input(
            "After re-pairing, press Enter to retry recovery once "
            "(Ctrl+C to stop): "
        )
    except EOFError:
        return False
    return True


def main() -> int:
    global DEBUG_ENDPOINTS, DEBUG_WATCH_PORT
    try:
        DEBUG_WATCH_PORT = parse_debug_watch_port(sys.argv[1:])
    except ValueError as exc:
        print(f"DEBUG_ARGUMENT_ERROR: {exc}")
        return 2
    DEBUG_ENDPOINTS = (
        "--debug-endpoints" in sys.argv
        or DEBUG_WATCH_PORT is not None
    )
    if DEBUG_ENDPOINTS:
        print("[endpoint-debug] ENABLED: literal network endpoints will be printed to this terminal only.", flush=True)
    if DEBUG_WATCH_PORT is not None:
        debug_endpoint(f"WATCH port configured: {DEBUG_WATCH_PORT}")

    root = Path(__file__).resolve().parents[1]
    output = root / "logs" / "android" / "adb_wireless_recovery_probe.txt"
    output.parent.mkdir(parents=True, exist_ok=True)

    build = root / "tools" / "build_install_onn.ps1"
    if not build.is_file():
        raise RuntimeError("tools/build_install_onn.ps1 is missing")

    try:
        adb, source = find_adb(root)
    except Exception as exc:
        lines = [
            "PrivyHub persistent wireless ADB recovery probe v5",
            "Classification: ADB_BINARY_DISCOVERY_FAILED",
            "Production files modified by probe: NONE",
            "ADB pairing changed by probe: NONE",
            "Network addresses/endpoints in shareable log: NONE",
            "Device serials/instance names in shareable log: NONE",
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
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("ADB_BINARY_DISCOVERY_FAILED")
        print("Log:", output)
        return 1

    cache_path, cache_scope = private_cache_path()
    host_cache_path = private_host_cache_path()
    port_range_cache_path = private_port_range_cache_path()
    cached = read_cached_target(cache_path)
    private_host, private_host_source = resolve_private_host(cached, host_cache_path)
    port_range, port_range_source = resolve_private_port_range(port_range_cache_path)
    if DEBUG_ENDPOINTS:
        debug_endpoint(f"cache path: {cache_path}")
        debug_endpoint(f"cached target value: {cached if cached is not None else '<none>'}")
        debug_endpoint(f"resolved private host: {private_host if private_host is not None else '<none>'} (source={private_host_source})")
        debug_endpoint(f"resolved scan range: {port_range[0]}-{port_range[1]} (source={port_range_source})")

    before_devices, before_mdns, before_devices_rc, before_mdns_rc = snapshot(adb)

    rc_version, version_text = run([str(adb), "version"])
    version_line = version_text.splitlines()[0].strip() if version_text else "<no output>"
    rc_status, status_text = run([str(adb), "server-status"])
    status = parse_server_status(status_text) if rc_status == 0 else {}
    rc_check, _check_text = run([str(adb), "mdns", "check"])

    resolution, trace = resolve_with_recovery(
        adb,
        cached,
        private_host,
        port_range,
    )
    repair_prompt_used = False
    if resolution is None and prompt_repair_and_retry():
        repair_prompt_used = True
        cached = read_cached_target(cache_path)
        private_host, private_host_source = resolve_private_host(cached, host_cache_path)
        port_range, port_range_source = resolve_private_port_range(port_range_cache_path)
        retry_resolution, retry_trace = resolve_with_recovery(
            adb,
            cached,
            private_host,
            port_range,
        )
        trace.append("repair-prompt-completed")
        trace.extend(f"repair-retry:{item}" for item in retry_trace)
        resolution = retry_resolution

    cache_updated = False
    host_cache_updated = False
    port_range_cache_updated = False
    if resolution is not None:
        cache_updated = save_cached_target(cache_path, resolution.target)
        resolved_host = host_from_target(resolution.target)
        if resolved_host is not None:
            host_cache_updated = save_cached_host(host_cache_path, resolved_host)
        measured_port_range = query_device_port_range(adb, resolution.target)
        if measured_port_range is not None:
            port_range = measured_port_range
            port_range_source = "live-device"
            port_range_cache_updated = save_cached_port_range(
                port_range_cache_path,
                measured_port_range,
            )

    after_devices, after_mdns, after_devices_rc, after_mdns_rc = snapshot(adb)
    classification = classification_for(resolution)

    lines = [
        "PrivyHub persistent wireless ADB recovery probe v5",
        f"Classification: {classification}",
        "Production files modified by probe: NONE",
        "ADB pairing changed by probe: NONE",
        "Network addresses/endpoints in shareable log: NONE",
        "Device serials/instance names in shareable log: NONE",
        "Private ADB target cache may contain a network-bearing target: YES",
        "",
        "=== BUILD TOOL ===",
        f"build_install_onn.ps1 sha256: {hashlib.sha256(build.read_bytes()).hexdigest()}",
        *script_summary(build),
        "",
        "=== ADB DISCOVERY ===",
        f"ADB discovery source: {source}",
        f"local.properties exists: {(root / 'PrivyHub/local.properties').is_file()}",
        f"private cache scope: {cache_scope}",
        f"private cache present before recovery: {cached is not None}",
        f"private cache updated after valid recovery: {cache_updated}",
        f"private host available for ephemeral-port refresh: {private_host is not None}",
        f"private host source: {private_host_source}",
        f"private host cache updated after valid network recovery: {host_cache_updated}",
        f"private port range source: {port_range_source}",
        f"private port range cache updated after valid recovery: {port_range_cache_updated}",
        "ephemeral-port refresh scope: single privately identified host only",
        "ephemeral-port scan range: device-specific cached/measured range only",
        "ephemeral-port values written to shareable log: NONE",
        "",
        "=== ADB CAPABILITY ===",
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
        "",
        "=== BEFORE RECOVERY ===",
        f"adb mdns services rc: {before_mdns_rc}",
        f"mDNS TLS-connect services discovered: {before_mdns['tls_connect']}",
        f"mDNS TLS-pairing services discovered: {before_mdns['tls_pairing']}",
        f"mDNS legacy ADB services discovered: {before_mdns['legacy_adb']}",
        f"adb devices rc: {before_devices_rc}",
        f"online device transports: {before_devices['device']}",
        f"offline device transports: {before_devices['offline']}",
        f"unauthorized device transports: {before_devices['unauthorized']}",
        f"other device transports: {before_devices['other']}",
        "",
        "=== BOUNDED D-053 RECOVERY ===",
        f"automatic recovery result: {resolution.source if resolution else 'not-recovered'}",
        f"repair/re-pair prompt used: {repair_prompt_used}",
        *[f"step: {item}" for item in trace],
        "",
        "=== AFTER RECOVERY ===",
        f"adb mdns services rc: {after_mdns_rc}",
        f"mDNS TLS-connect services discovered: {after_mdns['tls_connect']}",
        f"mDNS TLS-pairing services discovered: {after_mdns['tls_pairing']}",
        f"mDNS legacy ADB services discovered: {after_mdns['legacy_adb']}",
        f"adb devices rc: {after_devices_rc}",
        f"online device transports: {after_devices['device']}",
        f"offline device transports: {after_devices['offline']}",
        f"unauthorized device transports: {after_devices['unauthorized']}",
        f"other device transports: {after_devices['other']}",
        "",
        "=== NEXT ACTION ===",
        (
            "none; ADB target recovered"
            if resolution
            else "automatic recovery exhausted; repair/re-pair this Linux host on the onn, then rerun this probe"
        ),
    ]

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(classification)
    print("Log:", output)
    return 0 if resolution is not None else 2


def self_test() -> None:
    import tempfile

    assert decode_sdk_dir_value(
        r"C\:\\Users\\Example\\AppData\\Local\\Android\\Sdk"
    ) == r"C:\Users\Example\AppData\Local\Android\Sdk"

    assert is_valid_target("adb-example._adb-tls-connect._tcp")
    assert is_valid_target("192.0.2.1:5555")
    assert not is_valid_target("not-a-target")

    rows = parse_device_rows("List of devices attached\nserial\tdevice\nother\toffline\n")
    assert rows == [("serial", "device"), ("other", "offline")]
    counts = device_counts("List of devices attached\nserial\tdevice\nother\toffline\n")
    assert counts["device"] == 1
    assert counts["offline"] == 1

    mdns_text = "adb-example\t_adb-tls-connect._tcp\t192.0.2.1:5555\n"
    assert parse_mdns_connect_targets(mdns_text) == [
        "adb-example._adb-tls-connect._tcp"
    ]
    assert mdns_counts(mdns_text)["tls_connect"] == 1

    assert classification_for(Resolution("adb-example._adb-tls-connect._tcp", "cached")) == (
        "ADB_TARGET_RECOVERED_CACHED"
    )
    assert classification_for(None) == "ADB_RECOVERY_EXHAUSTED_REPAIR_PAIRING_REQUIRED"

    with tempfile.TemporaryDirectory(prefix="privyhub_adb_probe_v5_") as td:
        root = Path(td)
        android = root / "PrivyHub"
        android.mkdir()
        sdk = root / "AndroidSdk"
        platform = sdk / "platform-tools"
        platform.mkdir(parents=True)
        fake_adb = platform / ("adb.exe" if os.name == "nt" else "adb")
        fake_adb.write_bytes(b"fake")

        encoded_sdk = str(sdk).replace("\\", "\\\\").replace(":", "\\:")
        (android / "local.properties").write_text(
            "sdk.dir=" + encoded_sdk + "\n",
            encoding="utf-8",
        )
        resolved = resolve_local_sdk(android)
        assert resolved == str(sdk)

        cache = root / "state" / "last_wireless_target.txt"
        assert save_cached_target(cache, "adb-example._adb-tls-connect._tcp")
        assert read_cached_target(cache) == "adb-example._adb-tls-connect._tcp"
        cache.write_text("bad-target", encoding="utf-8")
        assert read_cached_target(cache) is None

        host_cache = root / "state" / "last_wireless_host.txt"
        assert save_cached_host(host_cache, "192.0.2.44")
        assert read_cached_host(host_cache) == "192.0.2.44"

        port_range_cache = root / "state" / "last_wireless_port_range.txt"
        assert save_cached_port_range(port_range_cache, (32768, 60999))
        assert read_cached_port_range(port_range_cache) == (32768, 60999)

    assert host_from_target("192.0.2.44:37123") == "192.0.2.44"
    assert host_from_target("adb-example._adb-tls-connect._tcp") is None
    assert normalize_ipv4("224.0.0.251") is None
    assert parse_port_range("32768\t60999") == (32768, 60999)
    assert parse_port_range("bad") is None
    assert resolve_private_port_range(Path("/definitely/missing"))[0] == REPRESENTATIVE_ONN_EPHEMERAL_RANGE
    assert parse_debug_watch_port(["--debug-watch-port", "45678"]) == 45678
    assert parse_debug_watch_port(["--debug-watch-port=45679"]) == 45679
    assert parse_debug_watch_port([]) is None
    try:
        parse_debug_watch_port(["--debug-watch-port", "70000"])
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range debug watch port was accepted")

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    test_port = listener.getsockname()[1]
    open_ports, overflow = find_open_tcp_ports(
        "127.0.0.1",
        start_port=test_port,
        end_port=test_port,
        workers=1,
        timeout=0.2,
        max_open_ports=4,
    )
    listener.close()
    assert not overflow
    assert open_ports == [test_port]

    print("SELF-TEST PASSED")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        raise SystemExit(0)
    raise SystemExit(main())
