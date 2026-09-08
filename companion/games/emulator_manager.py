from __future__ import annotations

import json
import os
import subprocess
import threading
import time

from pathlib import Path
from typing import Any


class EmulatorError(RuntimeError):
    pass


class EmulatorManager:
    """PrivyHub-owned emulator process manager.

    The API never accepts an executable path, core path, or arbitrary content
    path from the client. Callers provide a trusted game record produced by the
    Games library scanner; all executable/core/content paths are resolved from
    project-local configuration and then boundary-checked.
    """

    def __init__(
        self,
        project_root: Path,
        config_path: Path | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.config_path = (
            config_path
            if config_path is not None
            else (
                self.project_root
                / "companion"
                / "games"
                / "config"
                / "emulators.json"
            )
        ).resolve()

        self.lock = threading.RLock()
        self.process: subprocess.Popen[Any] | None = None
        self.log_handle: Any | None = None
        self.active_game: dict[str, Any] | None = None
        self.started_at: float | None = None

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise EmulatorError(
                f"Emulator config not found: {self.config_path}"
            )

        try:
            data = json.loads(
                self.config_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise EmulatorError(
                f"Unable to read emulator config: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise EmulatorError("Emulator config root must be an object")

        return data

    def _project_path(
        self,
        relative: str,
        *,
        must_exist: bool = False,
        directory: bool = False,
    ) -> Path:
        candidate = (self.project_root / relative).resolve()

        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise EmulatorError(
                f"Configured path escapes project root: {relative}"
            ) from exc

        if must_exist and not candidate.exists():
            raise EmulatorError(
                f"Required path not found: {relative}"
            )

        if must_exist and directory and not candidate.is_dir():
            raise EmulatorError(
                f"Required directory not found: {relative}"
            )

        if must_exist and not directory and not candidate.is_file():
            raise EmulatorError(
                f"Required file not found: {relative}"
            )

        return candidate

    @staticmethod
    def _close_quietly(handle: Any | None) -> None:
        if handle is None:
            return
        try:
            handle.close()
        except Exception:
            pass

    def _refresh_process(self) -> None:
        if self.process is None:
            return

        if self.process.poll() is None:
            return

        self._close_quietly(self.log_handle)
        self.process = None
        self.log_handle = None
        self.active_game = None
        self.started_at = None

    def _runtime_details(self) -> dict[str, Any]:
        config = self._load_config()
        retroarch = config.get("retroarch")
        systems = config.get("systems")

        if not isinstance(retroarch, dict):
            raise EmulatorError("Missing retroarch config")

        if not isinstance(systems, dict):
            raise EmulatorError("Missing systems config")

        executable_rel = retroarch.get("executable")
        config_rel = retroarch.get("config")
        cores_rel = retroarch.get("cores_directory")

        if not all(
            isinstance(item, str) and item.strip()
            for item in (executable_rel, config_rel, cores_rel)
        ):
            raise EmulatorError("RetroArch paths are incomplete")

        executable = self._project_path(str(executable_rel))
        retroarch_config = self._project_path(str(config_rel))
        cores_directory = self._project_path(str(cores_rel))

        core_status: dict[str, dict[str, Any]] = {}

        for system_id, system_config in systems.items():
            if not isinstance(system_config, dict):
                continue

            core_file = system_config.get("core")
            if not isinstance(core_file, str) or not core_file:
                continue

            core_path = (cores_directory / core_file).resolve()
            try:
                core_path.relative_to(cores_directory.resolve())
            except ValueError as exc:
                raise EmulatorError(
                    f"Core path escapes core directory: {core_file}"
                ) from exc

            core_status[str(system_id)] = {
                "name": str(system_config.get("name", system_id)),
                "core": core_file,
                "installed": core_path.is_file(),
            }

        return {
            "config": config,
            "executable": executable,
            "retroarch_config": retroarch_config,
            "cores_directory": cores_directory,
            "core_status": core_status,
        }

    def status(self) -> dict[str, Any]:
        with self.lock:
            self._refresh_process()

            try:
                runtime = self._runtime_details()
                runtime_error = None
            except EmulatorError as exc:
                runtime = None
                runtime_error = str(exc)

            installed = False
            configured = False
            core_status: dict[str, Any] = {}

            if runtime is not None:
                installed = runtime["executable"].is_file()
                configured = runtime["retroarch_config"].is_file()
                core_status = runtime["core_status"]

            active = (
                self.process is not None
                and self.process.poll() is None
            )

            elapsed_seconds: int | None = None
            if active and self.started_at is not None:
                elapsed_seconds = max(
                    0,
                    int(time.monotonic() - self.started_at),
                )

            missing_cores = [
                system_id
                for system_id, item in core_status.items()
                if not bool(item.get("installed"))
            ]

            ready = (
                runtime_error is None
                and installed
                and configured
                and not missing_cores
            )

            return {
                "ok": True,
                "kind": "game_session",
                "title": "Game Session",
                "active": active,
                "ready": ready,
                "retroarch_installed": installed,
                "retroarch_configured": configured,
                "missing_cores": missing_cores,
                "cores": core_status,
                "runtime_error": runtime_error,
                "game": (
                    {
                        "id": self.active_game.get("id"),
                        "title": self.active_game.get("title"),
                        "system": self.active_game.get("system"),
                        "system_name": self.active_game.get("system_name"),
                    }
                    if active and self.active_game is not None
                    else None
                ),
                "pid": (
                    self.process.pid
                    if active and self.process is not None
                    else None
                ),
                "elapsed_seconds": elapsed_seconds,
                "message": (
                    "A PrivyHub-managed game is running on the companion."
                    if active
                    else (
                        "Emulator runtime is ready."
                        if ready
                        else (
                            "Run scripts/setup_retroarch_portable.ps1 "
                            "from the project root."
                        )
                    )
                ),
            }

    def _resolve_game(
        self,
        game: dict[str, Any],
        runtime: dict[str, Any],
    ) -> tuple[Path, Path]:
        system_id = str(game.get("system", "")).strip()
        relative_path = str(game.get("relative_path", "")).strip()

        if not system_id or not relative_path:
            raise EmulatorError("Game record is incomplete")

        systems = runtime["config"].get("systems", {})
        system_config = systems.get(system_id)

        if not isinstance(system_config, dict):
            raise EmulatorError(
                f"No emulator profile configured for system: {system_id}"
            )

        allowed_extensions = {
            str(item).casefold()
            for item in system_config.get("extensions", [])
            if isinstance(item, str)
        }

        content_path = self._project_path(
            relative_path,
            must_exist=True,
        )

        games_root = self._project_path(
            "games",
            must_exist=True,
            directory=True,
        )

        try:
            content_path.relative_to(games_root)
        except ValueError as exc:
            raise EmulatorError(
                "Game content escaped the trusted games library"
            ) from exc

        if (
            allowed_extensions
            and content_path.suffix.casefold() not in allowed_extensions
        ):
            raise EmulatorError(
                f"Unsupported {system_id} content format: "
                f"{content_path.suffix}"
            )

        core_file = system_config.get("core")
        if not isinstance(core_file, str) or not core_file:
            raise EmulatorError(
                f"No core configured for system: {system_id}"
            )

        core_path = (
            runtime["cores_directory"] / core_file
        ).resolve()

        try:
            core_path.relative_to(
                runtime["cores_directory"].resolve()
            )
        except ValueError as exc:
            raise EmulatorError("Configured core path is invalid") from exc

        if not core_path.is_file():
            raise EmulatorError(
                f"Core is not installed: {core_file}. "
                "Run scripts/setup_retroarch_portable.ps1."
            )

        return content_path, core_path

    def launch(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        with self.lock:
            self._refresh_process()

            if self.process is not None:
                raise EmulatorError(
                    "A PrivyHub game session is already running"
                )

            runtime = self._runtime_details()
            executable = runtime["executable"]
            retroarch_config = runtime["retroarch_config"]

            if not executable.is_file():
                raise EmulatorError(
                    "RetroArch is not installed. Run "
                    "scripts/setup_retroarch_portable.ps1."
                )

            if not retroarch_config.is_file():
                raise EmulatorError(
                    "PrivyHub RetroArch config is missing. Run "
                    "scripts/setup_retroarch_portable.ps1."
                )

            content_path, core_path = self._resolve_game(
                game,
                runtime,
            )

            logs_dir = self._project_path("logs/games")
            logs_dir.mkdir(parents=True, exist_ok=True)

            timestamp = time.strftime("%Y%m%d-%H%M%S")
            safe_game_id = str(game.get("id", "game"))[:80]
            log_path = logs_dir / f"{timestamp}-{safe_game_id}.log"
            log_handle = log_path.open(
                "a",
                encoding="utf-8",
                buffering=1,
            )

            command = [
                str(executable),
                "--config",
                str(retroarch_config),
                "--verbose",
                "-L",
                str(core_path),
                str(content_path),
            ]

            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            log_handle.write("PrivyHub game session\n")
            log_handle.write(f"Game ID: {game.get('id')}\n")
            log_handle.write(f"Title: {game.get('title')}\n")
            log_handle.write(f"System: {game.get('system')}\n")
            log_handle.write(f"Core: {core_path.name}\n")
            log_handle.write("Command uses project-local paths only.\n\n")
            log_handle.flush()

            try:
                process = subprocess.Popen(
                    command,
                    cwd=str(executable.parent),
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
            self.active_game = dict(game)
            self.started_at = time.monotonic()

            # Catch immediate startup failures without adding meaningful delay.
            time.sleep(0.15)
            if process.poll() is not None:
                exit_code = process.returncode
                self._refresh_process()
                raise EmulatorError(
                    f"RetroArch exited during startup (code {exit_code}). "
                    f"See {log_path.relative_to(self.project_root)}"
                )

            payload = self.status()
            payload["action"] = "launch"
            payload["log"] = log_path.relative_to(
                self.project_root
            ).as_posix()
            return payload

    def stop(self) -> dict[str, Any]:
        with self.lock:
            self._refresh_process()

            if self.process is None:
                payload = self.status()
                payload["action"] = "stop"
                payload["stopped"] = False
                return payload

            process = self.process

            if os.name == "nt":
                subprocess.run(
                    [
                        "taskkill",
                        "/PID",
                        str(process.pid),
                        "/T",
                        "/F",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                process.terminate()

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass

            self._close_quietly(self.log_handle)
            self.process = None
            self.log_handle = None
            self.active_game = None
            self.started_at = None

            payload = self.status()
            payload["action"] = "stop"
            payload["stopped"] = True
            return payload
