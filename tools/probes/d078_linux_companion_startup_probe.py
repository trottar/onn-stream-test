#!/usr/bin/env python3
from __future__ import annotations

import importlib
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPANION = ROOT / "companion"
LOG_PATH = ROOT / "logs" / "games" / "d078_linux_companion_startup_probe.txt"
PASS_TOKEN = "D078_LINUX_MEDIA_SERVER_STARTUP_READY"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http_ready(port: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if int(response.status) == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(0.1)
    return False


def main() -> int:
    if os.name == "nt":
        print("D078 probe is Linux-only")
        return 2

    sys.path.insert(0, str(COMPANION))
    service = importlib.import_module("privyhub_service")

    source_path = COMPANION / "privyhub_service.py"
    source_text = source_path.read_text(encoding="utf-8")
    required_tokens = (
        "# PRIVYHUB_D078_LINUX_MEDIA_SERVER_STARTUP_V1",
        "RANGE_SERVER = COMPANION_DIR / \"range_server.py\"",
        "def _launch_python_media_server(",
        "sys.executable",
        "self._launch_python_media_server(",
    )
    missing = [token for token in required_tokens if token not in source_text]
    if missing:
        raise RuntimeError(f"D-078 source markers missing: {missing}")

    if not service.RANGE_SERVER.is_file():
        raise RuntimeError(f"Range server missing: {service.RANGE_SERVER}")

    original_port = service.DEFAULT_MEDIA_PORT
    port = _free_port()
    service.DEFAULT_MEDIA_PORT = port
    controller = service.PrivyHubController()

    server_pid = None
    running = False
    ready = False
    stopped = False
    log_path = None

    try:
        controller.start_server()
        if controller.server is None:
            raise RuntimeError("start_server() did not create a managed process")

        server_pid = controller.server.process.pid
        log_path = controller.server.log_path
        running = controller.server.process.poll() is None
        ready = _http_ready(port)

        if not running:
            raise RuntimeError("Linux media server process exited during startup")
        if not ready:
            raise RuntimeError("Linux media server did not become HTTP-ready")
    finally:
        try:
            controller.stop_server()
            stopped = controller.server is None
        finally:
            service.DEFAULT_MEDIA_PORT = original_port

    lines = [
        "PrivyHub D-078 Linux companion startup probe",
        f"platform={sys.platform}",
        f"python_executable={sys.executable}",
        f"range_server={service.RANGE_SERVER.relative_to(ROOT)}",
        f"media_port={port}",
        f"server_pid={server_pid}",
        f"server_running={running}",
        f"http_ready={ready}",
        f"server_stopped={stopped}",
        f"server_log={log_path.relative_to(ROOT) if log_path else None}",
        "powershell_required=False",
        PASS_TOKEN,
    ]

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
