from __future__ import annotations

import atexit
import os
import socket
import subprocess
import threading
import time

from pathlib import Path
from typing import Any


class StreamHostError(RuntimeError):
    pass


class StreamManager:
    """
    PrivyHub-owned Sunshine process manager.

    Sunshine remains a transport backend. It does not own game discovery or
    game launch. PrivyHub launches RetroArch and Sunshine exposes only the
    "PrivyHub Game Session" desktop stream.
    """

    WEB_UI_PORT = 47990
    STARTUP_TIMEOUT_SECONDS = 12.0

    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.project_root = project_root.resolve()

        self.runtime_root = (
            self.project_root
            / "runtime"
            / "streaming"
            / "sunshine"
        ).resolve()

        self.executable = (
            self.runtime_root
            / "sunshine.exe"
        ).resolve()

        self.data_root = (
            self.project_root
            / "data"
            / "games"
            / "sunshine"
        ).resolve()

        self.config_path = (
            self.data_root
            / "sunshine.conf"
        ).resolve()

        self.apps_path = (
            self.data_root
            / "apps.json"
        ).resolve()

        self.stdout_log = (
            self.project_root
            / "logs"
            / "games"
            / "sunshine-process.log"
        ).resolve()

        self.lock = threading.RLock()
        self.process: subprocess.Popen[Any] | None = None
        self.log_handle: Any | None = None
        self.started_at: float | None = None

        atexit.register(
            self._shutdown_at_exit
        )

    @staticmethod
    def _close_quietly(
        handle: Any | None,
    ) -> None:
        if handle is None:
            return

        try:
            handle.close()
        except Exception:
            pass

    @staticmethod
    def _port_open(
        host: str,
        port: int,
        timeout: float = 0.20,
    ) -> bool:
        try:
            with socket.create_connection(
                (host, port),
                timeout=timeout,
            ):
                return True
        except OSError:
            return False

    def _refresh_process(self) -> None:
        if self.process is None:
            return

        if self.process.poll() is None:
            return

        self._close_quietly(
            self.log_handle
        )
        self.process = None
        self.log_handle = None
        self.started_at = None

    def _is_managed_running(self) -> bool:
        self._refresh_process()

        return (
            self.process is not None
            and self.process.poll() is None
        )

    def _is_host_listening(self) -> bool:
        return self._port_open(
            "127.0.0.1",
            self.WEB_UI_PORT,
        )

    def _boundary_check(self) -> None:
        for item in (
            self.runtime_root,
            self.executable,
            self.data_root,
            self.config_path,
            self.apps_path,
            self.stdout_log,
        ):
            try:
                item.relative_to(
                    self.project_root
                )
            except ValueError as exc:
                raise StreamHostError(
                    "Sunshine path escaped the PrivyHub project root"
                ) from exc

    def status(self) -> dict[str, Any]:
        with self.lock:
            self._boundary_check()

            installed = (
                self.executable.is_file()
            )

            configured = (
                self.config_path.is_file()
                and self.apps_path.is_file()
            )

            managed = (
                self._is_managed_running()
            )

            listening = (
                self._is_host_listening()
            )

            # If something is already listening on Sunshine's localhost web
            # port after a companion restart, do not spawn a duplicate or
            # claim ownership of that process.
            external = (
                listening
                and not managed
            )

            ready = (
                installed
                and configured
            )

            active = (
                managed
                or external
            )

            elapsed_seconds: int | None = None

            if (
                managed
                and self.started_at is not None
            ):
                elapsed_seconds = max(
                    0,
                    int(
                        time.monotonic()
                        - self.started_at
                    ),
                )

            if not installed:
                message = (
                    "Run scripts/setup_sunshine_portable.ps1 "
                    "from the project root."
                )
            elif not configured:
                message = (
                    "Sunshine runtime exists but PrivyHub configuration "
                    "is incomplete. Re-run setup_sunshine_portable.ps1."
                )
            elif external:
                message = (
                    "A Sunshine host is already listening locally. "
                    "PrivyHub will not start a duplicate or terminate a "
                    "process it did not create."
                )
            elif managed:
                message = (
                    "PrivyHub-managed Sunshine host is running."
                )
            else:
                message = (
                    "Streaming host is ready."
                )

            return {
                "ok": True,
                "kind": "stream_host",
                "title": "Streaming Host",
                "ready": ready,
                "active": active,
                "managed": managed,
                "external": external,
                "sunshine_installed": installed,
                "sunshine_configured": configured,
                "pid": (
                    self.process.pid
                    if managed
                    and self.process is not None
                    else None
                ),
                "elapsed_seconds": elapsed_seconds,
                "web_ui_local": (
                    "https://localhost:47990"
                ),
                "controller_forwarding": False,
                "controller_message": (
                    "Controller forwarding is intentionally disabled "
                    "for the first streaming proof."
                ),
                "message": message,
            }

    def start(self) -> dict[str, Any]:
        with self.lock:
            self._boundary_check()
            state = self.status()

            if state["active"]:
                return state

            if not state["ready"]:
                raise StreamHostError(
                    str(
                        state.get(
                            "message",
                            "Sunshine setup is incomplete",
                        )
                    )
                )

            self.stdout_log.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.data_root.mkdir(
                parents=True,
                exist_ok=True,
            )

            log_handle = self.stdout_log.open(
                "a",
                encoding="utf-8",
                buffering=1,
            )

            log_handle.write("\n")
            log_handle.write("=" * 72 + "\n")
            log_handle.write(
                "Starting PrivyHub Sunshine host\n"
            )
            log_handle.write(
                f"Executable: {self.executable}\n"
            )
            log_handle.write(
                f"Config:     {self.config_path}\n"
            )
            log_handle.write("=" * 72 + "\n")
            log_handle.flush()

            creationflags = 0

            if os.name == "nt":
                creationflags = (
                    subprocess.CREATE_NEW_PROCESS_GROUP
                )

            try:
                process = subprocess.Popen(
                    [
                        str(self.executable),
                        str(self.config_path),
                    ],
                    cwd=str(
                        self.runtime_root
                    ),
                    stdin=subprocess.DEVNULL,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    creationflags=creationflags,
                )
            except Exception:
                log_handle.close()
                raise

            self.process = process
            self.log_handle = log_handle
            self.started_at = time.monotonic()

        deadline = (
            time.monotonic()
            + self.STARTUP_TIMEOUT_SECONDS
        )

        while time.monotonic() < deadline:
            with self.lock:
                self._refresh_process()

                if self.process is None:
                    raise StreamHostError(
                        "Sunshine exited during startup. "
                        "Check logs/games/sunshine-process.log and "
                        "logs/games/sunshine.log."
                    )

            if self._is_host_listening():
                return self.status()

            time.sleep(
                0.25
            )

        self.stop()

        raise StreamHostError(
            "Sunshine did not become ready before the startup timeout. "
            "Check logs/games/sunshine-process.log and "
            "logs/games/sunshine.log."
        )

    def ensure_running(self) -> dict[str, Any]:
        state = self.status()

        if state["active"]:
            return state

        return self.start()

    def _terminate_managed_process_tree(
        self,
        process: subprocess.Popen[Any],
    ) -> None:
        # Stop only the process tree rooted at the exact PID PrivyHub created.
        if process.poll() is not None:
            return

        if os.name == "nt":
            subprocess.run(
                [
                    "taskkill.exe",
                    "/PID",
                    str(process.pid),
                    "/T",
                    "/F",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
                check=False,
            )

            try:
                process.wait(
                    timeout=5
                )
            except subprocess.TimeoutExpired as exc:
                raise StreamHostError(
                    "Windows reported the managed Sunshine process tree "
                    "could not be stopped."
                ) from exc

            return

        process.terminate()

        try:
            process.wait(
                timeout=5
            )
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(
                timeout=5
            )

    def stop(self) -> dict[str, Any]:
        with self.lock:
            self._refresh_process()

            if self.process is None:
                state = self.status()

                if state["external"]:
                    raise StreamHostError(
                        "Sunshine is running, but this companion instance "
                        "did not start it. PrivyHub will not terminate an "
                        "unowned process."
                    )

                return state

            process = self.process

            if process.poll() is None:
                self._terminate_managed_process_tree(
                    process
                )

            self._close_quietly(
                self.log_handle
            )

            self.process = None
            self.log_handle = None
            self.started_at = None

            deadline = (
                time.monotonic()
                + 5.0
            )

            while (
                time.monotonic() < deadline
                and self._is_host_listening()
            ):
                time.sleep(
                    0.20
                )

            if self._is_host_listening():
                raise StreamHostError(
                    "PrivyHub stopped its managed Sunshine process tree, "
                    "but port 47990 is still listening. Another Sunshine "
                    "instance may be running; PrivyHub will not terminate "
                    "an unowned process."
                )

            return self.status()

    def _shutdown_at_exit(self) -> None:
        try:
            if self._is_managed_running():
                self.stop()
        except Exception:
            pass
