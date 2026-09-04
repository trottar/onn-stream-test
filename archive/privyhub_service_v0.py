#!/usr/bin/env python3
"""
PrivyHub local control service.

Prototype API:
    GET  /status
    POST /start/camera
    POST /start/browser
    POST /stop

The service keeps the existing PrivyHub HTTP/range server running and
starts exactly one live source at a time.

Windows-only prototype. Uses only the Python standard library.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(r"L:\Projects\onn-stream-test")
LOG_DIR = PROJECT_ROOT / "logs"

SERVER_SCRIPT = PROJECT_ROOT / "start_server.ps1"
CAMERA_SCRIPT = PROJECT_ROOT / "start_camera.ps1"
BROWSER_SCRIPT = PROJECT_ROOT / "start_browser.ps1"

CONTROL_HOST = "0.0.0.0"
CONTROL_PORT = 8765

POWERSHELL = "powershell.exe"


@dataclass
class ManagedProcess:
    name: str
    process: subprocess.Popen
    log_handle: object
    log_path: Path


class PrivyHubController:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.server: Optional[ManagedProcess] = None
        self.source: Optional[ManagedProcess] = None

        LOG_DIR.mkdir(parents=True, exist_ok=True)

        for required in (SERVER_SCRIPT, CAMERA_SCRIPT, BROWSER_SCRIPT):
            if not required.exists():
                raise FileNotFoundError(f"Required script not found: {required}")

    @staticmethod
    def _running(item: Optional[ManagedProcess]) -> bool:
        return item is not None and item.process.poll() is None

    def _cleanup_finished_process(self, item: Optional[ManagedProcess]) -> None:
        if item is not None and item.process.poll() is not None:
            try:
                item.log_handle.close()
            except Exception:
                pass

    def _launch(self, name: str, script: Path) -> ManagedProcess:
        log_path = LOG_DIR / f"{name}.log"
        log_handle = open(log_path, "a", encoding="utf-8", buffering=1)

        log_handle.write("\n")
        log_handle.write("=" * 72 + "\n")
        log_handle.write(f"Starting PrivyHub process: {name}\n")
        log_handle.write(f"Script: {script}\n")
        log_handle.write("=" * 72 + "\n")
        log_handle.flush()

        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            process = subprocess.Popen(
                [
                    POWERSHELL,
                    "-NoLogo",
                    "-NoProfile",
                    "-File",
                    str(script),
                ],
                cwd=str(PROJECT_ROOT),
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
            )
        except Exception:
            log_handle.close()
            raise

        return ManagedProcess(
            name=name,
            process=process,
            log_handle=log_handle,
            log_path=log_path,
        )

    @staticmethod
    def _kill_process_tree(item: ManagedProcess) -> None:
        if item.process.poll() is not None:
            return

        if os.name == "nt":
            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(item.process.pid),
                    "/T",
                    "/F",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            item.process.terminate()

        try:
            item.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                item.process.kill()
            except Exception:
                pass

    def start_server(self) -> dict:
        with self.lock:
            if self._running(self.server):
                return self.status()

            self._cleanup_finished_process(self.server)
            self.server = self._launch("server", SERVER_SCRIPT)

            return self.status()

    def stop_server(self) -> None:
        with self.lock:
            if self.server is not None:
                self._kill_process_tree(self.server)

                try:
                    self.server.log_handle.close()
                except Exception:
                    pass

                self.server = None

    def start_source(self, source_name: str) -> dict:
        if source_name not in {"camera", "browser"}:
            raise ValueError(f"Unsupported source: {source_name}")

        with self.lock:
            self.start_server()
            self.stop_source()

            script = CAMERA_SCRIPT if source_name == "camera" else BROWSER_SCRIPT
            self.source = self._launch(source_name, script)

            return self.status()

    def stop_source(self) -> dict:
        with self.lock:
            if self.source is not None:
                self._kill_process_tree(self.source)

                try:
                    self.source.log_handle.close()
                except Exception:
                    pass

                self.source = None

            return self.status()

    def shutdown(self) -> None:
        with self.lock:
            self.stop_source()
            self.stop_server()

    def status(self) -> dict:
        with self.lock:
            if self.server is not None and not self._running(self.server):
                self._cleanup_finished_process(self.server)
                self.server = None

            if self.source is not None and not self._running(self.source):
                self._cleanup_finished_process(self.source)
                self.source = None

            return {
                "service": "PrivyHub",
                "control_port": CONTROL_PORT,
                "server": {
                    "running": self._running(self.server),
                    "pid": self.server.process.pid if self._running(self.server) else None,
                    "log": str(self.server.log_path) if self.server else None,
                },
                "source": {
                    "name": self.source.name if self._running(self.source) else None,
                    "running": self._running(self.source),
                    "pid": self.source.process.pid if self._running(self.source) else None,
                    "log": str(self.source.log_path) if self.source else None,
                },
                "media": {
                    "vod_path": "/test_1080p_4m.mp4",
                    "live_path": "/live/stream.m3u8",
                    "media_port": 8000,
                },
            }


CONTROLLER = PrivyHubController()


class PrivyHubRequestHandler(BaseHTTPRequestHandler):
    server_version = "PrivyHubControl/0.1"

    def log_message(self, format: str, *args) -> None:
        print(
            f"{self.client_address[0]} - "
            f"{self.log_date_time_string()} - "
            f"{format % args}"
        )

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/status":
            self._send_json(200, CONTROLLER.status())
            return

        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        try:
            if self.path == "/start/camera":
                status = CONTROLLER.start_source("camera")
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "action": "start",
                        "source": "camera",
                        "status": status,
                    },
                )
                return

            if self.path == "/start/browser":
                status = CONTROLLER.start_source("browser")
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "action": "start",
                        "source": "browser",
                        "status": status,
                    },
                )
                return

            if self.path == "/stop":
                status = CONTROLLER.stop_source()
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "action": "stop",
                        "status": status,
                    },
                )
                return

            self._send_json(404, {"ok": False, "error": "Not found"})

        except Exception as exc:
            self._send_json(
                500,
                {
                    "ok": False,
                    "error": str(exc),
                },
            )


def main() -> None:
    print("PrivyHub control service")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Control API: http://127.0.0.1:{CONTROL_PORT}")
    print("")
    print("Endpoints:")
    print("  GET  /status")
    print("  POST /start/camera")
    print("  POST /start/browser")
    print("  POST /stop")
    print("")
    print(f"Logs: {LOG_DIR}")
    print("")
    print("Starting the existing PrivyHub range server...")

    CONTROLLER.start_server()

    httpd = ThreadingHTTPServer(
        (CONTROL_HOST, CONTROL_PORT),
        PrivyHubRequestHandler,
    )

    print(f"Listening on {CONTROL_HOST}:{CONTROL_PORT}")
    print("Stop the control service with Ctrl+C.")
    print("")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PrivyHub control service...")
    finally:
        httpd.server_close()
        CONTROLLER.shutdown()
        print("PrivyHub control service stopped.")


if __name__ == "__main__":
    main()
