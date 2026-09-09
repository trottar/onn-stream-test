from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time

from pathlib import Path
from typing import Any, Callable


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
        self._hotkey_sender: Callable[[str], dict[str, Any]] | None = None
        self._paused = False

        # PrivyHub A4: best-effort Windows host coexistence state.
        # RetroArch stays rendered/non-iconic for WGC, but is pushed behind
        # normal host applications without being activated.
        self._host_window_policy: dict[str, Any] | None = None

        # PrivyHub A2/A3 patch 03: RetroArch's documented Network Control
        # Interface is session-scoped and uses a per-launch ephemeral port.
        # Companion commands are sent only to IPv4 loopback.
        self._network_cmd_port: int | None = None

        # PrivyHub A7.3: optional per-launch deterministic cheat profile.
        # A non-null session always uses isolated save/state storage, and any
        # requested enabled indexes are applied and verified before launch returns.
        self._active_cheat_session: dict[str, Any] | None = None

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

        cheat_runtime_cleanup = (
            isinstance(self._active_cheat_session, dict)
            and self._active_cheat_session.get("session_kind", "cheat") == "cheat"
        )

        self._close_quietly(self.process.stdin)
        self._close_quietly(self.log_handle)
        self.process = None
        self.log_handle = None
        self.active_game = None
        self.started_at = None
        self._paused = False
        self._host_window_policy = None
        self._network_cmd_port = None
        self._active_cheat_session = None

        if cheat_runtime_cleanup:
            self._cleanup_cheat_runtime()

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
                "paused": bool(active and self._paused),
                "host_window_policy": (
                    dict(self._host_window_policy)
                    if active and self._host_window_policy is not None
                    else None
                ),
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
                "save_state_slots": list(self.SAVE_STATE_SLOTS),
                "save_state_slot_details": (
                    self._save_state_slot_details()
                    if active
                    else []
                ),
                "cheat_session": (
                    {
                        "profile_schema": self.CHEAT_PROFILE_SCHEMA,
                        "profile_id": self._active_cheat_session.get("profile_id"),
                        "source_index": self._active_cheat_session.get("source_index"),
                        "source_filename": self._active_cheat_session.get("source_filename"),
                        "enabled_cheat_indexes": list(
                            self._active_cheat_session.get("enabled_cheat_indexes", [])
                        ),
                        "enabled_cheats": list(
                            self._active_cheat_session.get("enabled_cheats", [])
                        ),
                        "activation_verified": bool(
                            self._active_cheat_session.get("activation_verified")
                        ),
                    }
                    if (
                        active
                        and isinstance(self._active_cheat_session, dict)
                        and self._active_cheat_session.get("session_kind", "cheat") == "cheat"
                    )
                    else None
                ),
                "mod_session": (
                    {
                        "profile_schema": self.MOD_PROFILE_SCHEMA,
                        "profile_id": self._active_cheat_session.get("profile_id"),
                        "mod_index": self._active_cheat_session.get("mod_index"),
                        "filename": self._active_cheat_session.get("mod_filename"),
                        "format": self._active_cheat_session.get("mod_format"),
                        "sha256": self._active_cheat_session.get("mod_sha256"),
                    }
                    if (
                        active
                        and isinstance(self._active_cheat_session, dict)
                        and self._active_cheat_session.get("session_kind") == "mod"
                    )
                    else None
                ),
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

    def _controller_overrides_path(
        self,
    ) -> Path:
        path = self._project_path(
            "data/games/retroarch/controller_overrides.json"
        )
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        return path

    def _load_controller_overrides(
        self,
    ) -> dict[str, Any]:
        path = self._controller_overrides_path()

        if not path.is_file():
            return {
                "version": 1,
                "games": {},
            }

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise EmulatorError(
                f"Unable to read controller overrides: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise EmulatorError(
                "Controller overrides root must be an object"
            )

        games = payload.get(
            "games",
            {},
        )

        if not isinstance(games, dict):
            raise EmulatorError(
                "Controller overrides games entry must be an object"
            )

        return {
            "version": 1,
            "games": games,
        }

    def _write_controller_overrides(
        self,
        payload: dict[str, Any],
    ) -> None:
        path = self._controller_overrides_path()
        temporary = path.with_name(
            path.name + ".tmp"
        )

        try:
            temporary.write_text(
                json.dumps(
                    payload,
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )
            temporary.replace(path)
        except OSError as exc:
            try:
                temporary.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

            raise EmulatorError(
                f"Unable to write controller overrides: {exc}"
            ) from exc

    def _controller_profile_catalog(
        self,
        game: dict[str, Any],
    ) -> tuple[str, str, dict[str, dict[str, Any]]]:
        system_id = str(
            game.get(
                "system",
                "",
            )
        ).strip()

        config = self._load_config()
        systems = config.get(
            "systems",
            {},
        )
        system_config = systems.get(
            system_id
        )

        if not isinstance(
            system_config,
            dict,
        ):
            raise EmulatorError(
                f"No emulator profile configured for system: {system_id}"
            )

        controls = system_config.get(
            "controls",
            {},
        )

        if controls is None:
            controls = {}

        if not isinstance(
            controls,
            dict,
        ):
            raise EmulatorError(
                f"Invalid controls profile for system: {system_id}"
            )

        raw_profiles = controls.get(
            "controller_profiles",
            {},
        )

        if raw_profiles is None:
            raw_profiles = {}

        if not isinstance(
            raw_profiles,
            dict,
        ):
            raise EmulatorError(
                f"Invalid controller profile map for system: {system_id}"
            )

        profiles: dict[str, dict[str, Any]] = {}

        for profile_id, raw_profile in raw_profiles.items():
            normalized_id = str(
                profile_id
            ).strip().casefold()

            if (
                not normalized_id
                or not isinstance(
                    raw_profile,
                    dict,
                )
            ):
                raise EmulatorError(
                    f"Invalid controller profile for system: {system_id}"
                )

            label = str(
                raw_profile.get(
                    "label",
                    normalized_id,
                )
            ).strip()

            device = raw_profile.get(
                "libretro_device"
            )

            if (
                not isinstance(device, int)
                or isinstance(device, bool)
                or device < 0
                or device > 65535
            ):
                raise EmulatorError(
                    "Invalid libretro controller device for "
                    f"{system_id}/{normalized_id}"
                )

            profiles[normalized_id] = {
                "label": (
                    label
                    if label
                    else normalized_id
                ),
                "libretro_device": device,
            }

        default_profile = str(
            controls.get(
                "controller_default",
                "",
            )
        ).strip().casefold()

        if profiles and default_profile not in profiles:
            raise EmulatorError(
                "Controller default is missing from the profile map for "
                f"{system_id}: {default_profile or '<blank>'}"
            )

        return (
            system_id,
            default_profile,
            profiles,
        )

    def controller_profile(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        with self.lock:
            (
                system_id,
                default_profile,
                profiles,
            ) = self._controller_profile_catalog(
                game
            )

            if not profiles:
                return {
                    "system": system_id,
                    "profile": "core_default",
                    "default_profile": "core_default",
                    "label": "Core default",
                    "source": "core_default",
                    "libretro_device": None,
                    "selectable": False,
                    "options": [],
                }

            game_id = str(
                game.get(
                    "id",
                    "",
                )
            ).strip()

            if not game_id:
                raise EmulatorError(
                    "Game record is missing its stable id"
                )

            overrides = self._load_controller_overrides()
            games = overrides["games"]
            raw_override = games.get(
                game_id
            )

            override_profile = ""

            if isinstance(
                raw_override,
                dict,
            ):
                override_profile = str(
                    raw_override.get(
                        "controller_profile",
                        "",
                    )
                ).strip().casefold()

            if override_profile in profiles:
                selected = override_profile
                source = "game_override"
            else:
                selected = default_profile
                source = "system_default"

            selected_profile = profiles[
                selected
            ]

            options = [
                {
                    "id": profile_id,
                    "label": str(
                        profile["label"]
                    ),
                }
                for profile_id, profile in profiles.items()
            ]

            return {
                "system": system_id,
                "profile": selected,
                "default_profile": default_profile,
                "label": str(
                    selected_profile["label"]
                ),
                "source": source,
                "libretro_device": int(
                    selected_profile[
                        "libretro_device"
                    ]
                ),
                "selectable": len(
                    profiles
                ) > 1,
                "options": options,
            }

    def set_controller_profile(
        self,
        game: dict[str, Any],
        profile: str,
    ) -> dict[str, Any]:
        with self.lock:
            (
                _system_id,
                default_profile,
                profiles,
            ) = self._controller_profile_catalog(
                game
            )

            requested = str(
                profile
            ).strip().casefold()

            if not profiles:
                raise EmulatorError(
                    "This emulator system does not expose selectable "
                    "controller profiles"
                )

            if requested not in profiles:
                raise EmulatorError(
                    "Unsupported controller profile: "
                    f"{requested or '<blank>'}"
                )

            game_id = str(
                game.get(
                    "id",
                    "",
                )
            ).strip()

            if not game_id:
                raise EmulatorError(
                    "Game record is missing its stable id"
                )

            payload = self._load_controller_overrides()
            games = payload["games"]

            if requested == default_profile:
                games.pop(
                    game_id,
                    None,
                )
            else:
                games[game_id] = {
                    "controller_profile": requested,
                }

            self._write_controller_overrides(
                payload
            )

            return self.controller_profile(
                game
            )

    def _prepare_input_override(
        self,
        game: dict[str, Any],
        runtime: dict[str, Any],
    ) -> tuple[Path, dict[str, Any]]:
        """Build the active RetroArch input/controller profile.

        The native controller transport always carries both digital D-pad
        bits and true analog axes. The append-config only controls analog-to-
        digital mirroring. PS1 emulated controller selection is applied on
        the RetroArch command line at launch time because modern RetroArch
        does not honor input_libretro_device_pN from ordinary config files.
        """
        system_id = str(
            game.get("system", "")
        ).strip()

        systems = runtime["config"].get(
            "systems",
            {},
        )
        system_config = systems.get(
            system_id
        )

        if not isinstance(
            system_config,
            dict,
        ):
            raise EmulatorError(
                f"No emulator profile configured for system: {system_id}"
            )

        controls = system_config.get(
            "controls",
            {},
        )

        if controls is None:
            controls = {}

        if not isinstance(
            controls,
            dict,
        ):
            raise EmulatorError(
                f"Invalid controls profile for system: {system_id}"
            )

        analog_dpad = str(
            controls.get(
                "analog_dpad",
                "none",
            )
        ).strip().casefold()

        analog_dpad_values = {
            "none": 0,
            "left": 1,
            "right": 2,
        }

        if analog_dpad not in analog_dpad_values:
            raise EmulatorError(
                "Unsupported analog_dpad mode for "
                f"{system_id}: {analog_dpad}. "
                "Expected none, left, or right."
            )

        retroarch_value = analog_dpad_values[
            analog_dpad
        ]

        controller = self.controller_profile(
            game
        )

        config_directory = self._project_path(
            "data/games/retroarch/config"
        )
        config_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        config_path = (
            config_directory
            / "privyhub-input.cfg"
        ).resolve()

        try:
            config_path.relative_to(
                config_directory.resolve()
            )
        except ValueError as exc:
            raise EmulatorError(
                "Generated RetroArch input config escaped its data directory"
            ) from exc

        command_port = self._allocate_network_command_port()

        lines = [
            "# PrivyHub Phase A controller profile",
            "# Generated for the active emulator system; do not edit.",
            (
                "input_player1_analog_dpad_mode = "
                f'"{retroarch_value}"'
            ),
            (
                "input_player2_analog_dpad_mode = "
                f'"{retroarch_value}"'
            ),
            # PrivyHub A2/A3 patch 03: use RetroArch's documented runtime
            # command interface instead of unproven controller meta binds.
            'network_cmd_enable = "true"',
            f'network_cmd_port = "{command_port}"',
        ]

        libretro_device = controller.get(
            "libretro_device"
        )

        config_text = (
            "\n".join(lines)
            + "\n"
        )

        try:
            config_path.write_text(
                config_text,
                encoding="utf-8",
            )
        except OSError as exc:
            raise EmulatorError(
                f"Unable to write RetroArch input override: {exc}"
            ) from exc

        self._network_cmd_port = command_port

        return (
            config_path,
            {
                "analog_dpad": analog_dpad,
                "retroarch_analog_dpad_mode": retroarch_value,
                "controller_profile": controller["profile"],
                "controller_label": controller["label"],
                "controller_source": controller["source"],
                "libretro_device": libretro_device,
                "network_cmd_port": command_port,
            },
        )


    # PRIVYHUB_A7_PATCH_11_A7_4_SOFTPATCH_MODS_ADB_FIX
    # PRIVYHUB_A7_PATCH_12_DETERMINISTIC_IPS_DERIVED_CONTENT
    IPS_MAX_PATCH_BYTES = 16 * 1024 * 1024
    IPS_MAX_OUTPUT_BYTES = 64 * 1024 * 1024

    @staticmethod
    def _ips_u24(data: bytes) -> int:
        if len(data) != 3:
            raise EmulatorError("Invalid IPS 24-bit value")
        return (data[0] << 16) | (data[1] << 8) | data[2]

    def _apply_ips_patch_bytes(
        self,
        base_bytes: bytes,
        patch_bytes: bytes,
    ) -> bytes:
        if len(patch_bytes) > self.IPS_MAX_PATCH_BYTES:
            raise EmulatorError("IPS patch exceeds PrivyHub safety limit")
        if not patch_bytes.startswith(b"PATCH"):
            raise EmulatorError("IPS patch is missing PATCH header")

        output = bytearray(base_bytes)
        cursor = 5
        records = 0

        while True:
            if cursor + 3 > len(patch_bytes):
                raise EmulatorError("IPS patch ended before EOF marker")

            if patch_bytes[cursor:cursor + 3] == b"EOF":
                cursor += 3
                break

            if cursor + 5 > len(patch_bytes):
                raise EmulatorError("IPS record header is truncated")

            offset = self._ips_u24(patch_bytes[cursor:cursor + 3])
            size = int.from_bytes(patch_bytes[cursor + 3:cursor + 5], "big")
            cursor += 5

            if size == 0:
                if cursor + 3 > len(patch_bytes):
                    raise EmulatorError("IPS RLE record is truncated")
                run_size = int.from_bytes(patch_bytes[cursor:cursor + 2], "big")
                value = patch_bytes[cursor + 2]
                cursor += 3
                if run_size <= 0:
                    raise EmulatorError("IPS RLE record has zero length")
                end = offset + run_size
                if end > self.IPS_MAX_OUTPUT_BYTES:
                    raise EmulatorError("IPS output exceeds PrivyHub safety limit")
                if end > len(output):
                    output.extend(b"\x00" * (end - len(output)))
                output[offset:end] = bytes((value,)) * run_size
            else:
                if cursor + size > len(patch_bytes):
                    raise EmulatorError("IPS data record is truncated")
                end = offset + size
                if end > self.IPS_MAX_OUTPUT_BYTES:
                    raise EmulatorError("IPS output exceeds PrivyHub safety limit")
                if end > len(output):
                    output.extend(b"\x00" * (end - len(output)))
                output[offset:end] = patch_bytes[cursor:cursor + size]
                cursor += size

            records += 1

        remaining = len(patch_bytes) - cursor
        if remaining == 3:
            truncate_size = self._ips_u24(patch_bytes[cursor:cursor + 3])
            if truncate_size > self.IPS_MAX_OUTPUT_BYTES:
                raise EmulatorError("IPS truncate size exceeds PrivyHub safety limit")
            if truncate_size < len(output):
                del output[truncate_size:]
            elif truncate_size > len(output):
                output.extend(b"\x00" * (truncate_size - len(output)))
            cursor += 3
        elif remaining != 0:
            raise EmulatorError("IPS patch has unexpected trailing bytes")

        if records == 0:
            raise EmulatorError("IPS patch contains no records")
        if len(output) > self.IPS_MAX_OUTPUT_BYTES:
            raise EmulatorError("IPS output exceeds PrivyHub safety limit")
        if bytes(output) == base_bytes:
            raise EmulatorError("IPS patch produced unchanged content")
        return bytes(output)

    def _prepare_ips_derived_content(
        self,
        content_path: Path,
        patch_path: Path,
        mod_session: dict[str, Any],
    ) -> Path:
        profile_relative = str(mod_session.get("profile_root", "")).strip()
        expected_patch_sha = str(mod_session.get("mod_sha256", "")).strip().upper()
        if not profile_relative or not expected_patch_sha:
            raise EmulatorError("IPS mod profile is incomplete")

        profile_root = self._project_path(profile_relative)
        content_root = (profile_root / "content").resolve()
        content_root.relative_to(profile_root.resolve())
        derived_path = (content_root / content_path.name).resolve()
        derived_path.relative_to(content_root)
        metadata_path = (content_root / "privyhub_derived_content.json").resolve()
        metadata_path.relative_to(content_root)

        try:
            base_bytes = content_path.read_bytes()
            patch_bytes = patch_path.read_bytes()
        except OSError as exc:
            raise EmulatorError(f"Unable to read IPS source content: {exc}") from exc

        if len(base_bytes) > self.IPS_MAX_OUTPUT_BYTES:
            raise EmulatorError("Base content exceeds PrivyHub IPS safety limit")
        patch_sha = hashlib.sha256(patch_bytes).hexdigest().upper()
        if patch_sha != expected_patch_sha:
            raise EmulatorError("Selected IPS mod changed before derivation")
        base_sha = hashlib.sha256(base_bytes).hexdigest().upper()
        derived_bytes = self._apply_ips_patch_bytes(base_bytes, patch_bytes)
        derived_sha = hashlib.sha256(derived_bytes).hexdigest().upper()

        metadata = {
            "schema": 1,
            "method": "privyhub_ips",
            "base_relative_path": str(content_path.relative_to(self.project_root)).replace("\\", "/"),
            "base_sha256": base_sha,
            "patch_relative_path": str(patch_path.relative_to(self.project_root)).replace("\\", "/"),
            "patch_sha256": patch_sha,
            "derived_filename": content_path.name,
            "derived_sha256": derived_sha,
            "derived_size_bytes": len(derived_bytes),
        }

        content_root.mkdir(parents=True, exist_ok=True)
        reusable = False
        if derived_path.is_file() and metadata_path.is_file():
            try:
                existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                reusable = (
                    existing_metadata == metadata
                    and self._sha256_file(derived_path) == derived_sha
                    and derived_path.stat().st_size == len(derived_bytes)
                )
            except (OSError, json.JSONDecodeError):
                reusable = False

        if not reusable:
            data_tmp = derived_path.with_name(derived_path.name + ".tmp")
            metadata_tmp = metadata_path.with_name(metadata_path.name + ".tmp")
            try:
                data_tmp.write_bytes(derived_bytes)
                if self._sha256_file(data_tmp) != derived_sha:
                    raise EmulatorError("Generated IPS content failed SHA-256 verification")
                metadata_tmp.write_text(
                    json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                data_tmp.replace(derived_path)
                metadata_tmp.replace(metadata_path)
            except Exception:
                try:
                    data_tmp.unlink(missing_ok=True)
                except OSError:
                    pass
                try:
                    metadata_tmp.unlink(missing_ok=True)
                except OSError:
                    pass
                raise

        if self._sha256_file(derived_path) != derived_sha:
            raise EmulatorError("Installed IPS derived content failed SHA-256 verification")

        mod_session["patch_application"] = "privyhub_ips"
        mod_session["base_content_sha256"] = base_sha
        mod_session["derived_content_sha256"] = derived_sha
        mod_session["derived_content_relative_path"] = str(
            derived_path.relative_to(self.project_root)
        ).replace("\\", "/")
        return derived_path

    # A7.4 softpatch mods. These use RetroArch's frontend patch arguments and
    # deliberately reuse the proven A7.3 isolated profile storage plumbing.
    MOD_USER_CONTENT_ROOT = "data/games/user_content"
    MOD_PROFILE_ROOT = "data/games/retroarch/mod_profiles"
    MOD_PROFILE_SCHEMA = 1
    MOD_FORMAT_FLAGS = {
        ".ips": "--ips",
        ".bps": "--bps",
        ".ups": "--ups",
        ".xdelta": "--xdelta",
    }
    # Current PrivyHub cores with documented RetroArch softpatch support.
    # Beetle PSX HW explicitly reports Softpatching = unsupported.
    MOD_SUPPORTED_SYSTEMS = {"nes", "snes", "genesis"}

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest().upper()

    def _mod_catalog_unlocked(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        game_id = str(game.get("id", "")).strip()
        system = str(game.get("system", "")).strip().casefold()
        relative_path = str(game.get("relative_path", "")).strip().replace("\\", "/")
        if not game_id or not system or not relative_path:
            raise EmulatorError("Game record is incomplete")

        managed_root = self._project_path(
            f"{self.MOD_USER_CONTENT_ROOT}/{game_id}/mods"
        )
        managed_relative = str(
            managed_root.relative_to(self.project_root)
        ).replace("\\", "/")

        if system not in self.MOD_SUPPORTED_SYSTEMS:
            return {
                "game_id": game_id,
                "system": system,
                "status": "unsupported",
                "supported": False,
                "reason": "core_softpatching_unsupported",
                "managed_directory": managed_relative,
                "mods": [],
            }

        mods: list[dict[str, Any]] = []
        if managed_root.is_dir():
            candidates = sorted(
                (
                    path
                    for path in managed_root.rglob("*")
                    if path.is_file()
                    and path.suffix.casefold() in self.MOD_FORMAT_FLAGS
                    and not path.name.startswith(".")
                ),
                key=lambda path: str(path).casefold(),
            )
            for path in candidates:
                resolved = path.resolve()
                try:
                    resolved.relative_to(managed_root.resolve())
                    project_relative = str(
                        resolved.relative_to(self.project_root)
                    ).replace("\\", "/")
                    stat = resolved.stat()
                    digest = self._sha256_file(resolved)
                except (OSError, ValueError) as exc:
                    raise EmulatorError(
                        f"Unable to validate managed mod file: {exc}"
                    ) from exc
                suffix = resolved.suffix.casefold()
                mods.append(
                    {
                        "mod_index": len(mods),
                        "filename": resolved.name,
                        "relative_path": project_relative,
                        "format": suffix.lstrip("."),
                        "cli_flag": self.MOD_FORMAT_FLAGS[suffix],
                        "sha256": digest,
                        "size_bytes": int(stat.st_size),
                    }
                )

        return {
            "game_id": game_id,
            "system": system,
            "status": "available" if mods else "empty",
            "supported": True,
            "reason": None,
            "managed_directory": managed_relative,
            "mods": mods,
        }

    def mod_catalog(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        with self.lock:
            return self._mod_catalog_unlocked(game)

    def _prepare_mod_profile_storage(
        self,
        game: dict[str, Any],
        mod_record: dict[str, Any],
    ) -> dict[str, Any]:
        identity = {
            "schema": self.MOD_PROFILE_SCHEMA,
            "game_id": str(game.get("id", "")).strip(),
            "system": str(game.get("system", "")).strip(),
            "relative_path": str(
                game.get("relative_path", "")
            ).strip().replace("\\", "/"),
            "mod_relative_path": str(mod_record.get("relative_path", "")).strip(),
            "mod_sha256": str(mod_record.get("sha256", "")).strip().upper(),
        }
        if any(not str(identity[key]).strip() for key in (
            "game_id", "system", "relative_path", "mod_relative_path", "mod_sha256"
        )):
            raise EmulatorError("Mod profile identity is incomplete")

        canonical = json.dumps(
            identity,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        profile_id = hashlib.sha256(canonical).hexdigest().upper()

        profile_root = self._project_path(self.MOD_PROFILE_ROOT)
        game_root = (profile_root / identity["game_id"]).resolve()
        game_root.relative_to(profile_root.resolve())
        root = (game_root / profile_id).resolve()
        root.relative_to(game_root)
        saves = (root / "saves").resolve()
        states = (root / "states").resolve()
        slot_index = (root / "privyhub_state_slots.json").resolve()
        profile_path = (root / "profile.json").resolve()
        for candidate in (saves, states, slot_index, profile_path):
            candidate.relative_to(root)

        metadata = {
            "schema": self.MOD_PROFILE_SCHEMA,
            "profile_id": profile_id,
            "identity": identity,
            "mod": {
                "filename": str(mod_record.get("filename", "")),
                "format": str(mod_record.get("format", "")),
                "cli_flag": str(mod_record.get("cli_flag", "")),
                "sha256": str(mod_record.get("sha256", "")).upper(),
                "relative_path": str(mod_record.get("relative_path", "")),
            },
        }

        root.mkdir(parents=True, exist_ok=True)
        saves.mkdir(parents=True, exist_ok=True)
        states.mkdir(parents=True, exist_ok=True)
        if profile_path.is_file():
            try:
                existing = json.loads(profile_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise EmulatorError(
                    f"Unable to read mod profile metadata: {exc}"
                ) from exc
            if existing != metadata:
                raise EmulatorError(
                    "Mod profile metadata does not match its deterministic identity"
                )
        else:
            temporary = profile_path.with_name(profile_path.name + ".tmp")
            try:
                temporary.write_text(
                    json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                temporary.replace(profile_path)
            except OSError as exc:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
                raise EmulatorError(
                    f"Unable to write mod profile metadata: {exc}"
                ) from exc

        return {
            "profile_id": profile_id,
            "profile_path": str(profile_path.relative_to(self.project_root)).replace("\\", "/"),
            "profile_root": str(root.relative_to(self.project_root)).replace("\\", "/"),
            "savefile_directory": str(saves.relative_to(self.project_root)).replace("\\", "/"),
            "savestate_directory": str(states.relative_to(self.project_root)).replace("\\", "/"),
            "state_slot_index": str(slot_index.relative_to(self.project_root)).replace("\\", "/"),
        }

    def _prepare_mod_runtime(
        self,
        game: dict[str, Any],
        mod_index: int,
    ) -> tuple[str, Path, dict[str, Any]]:
        catalog = self._mod_catalog_unlocked(game)
        if not bool(catalog.get("supported")):
            raise EmulatorError(
                "Softpatch mods are not supported by the configured core for this system"
            )
        mods = catalog.get("mods", [])
        try:
            selected_index = int(mod_index)
        except (TypeError, ValueError) as exc:
            raise EmulatorError("Mod index must be an integer") from exc
        if (
            not isinstance(mods, list)
            or selected_index < 0
            or selected_index >= len(mods)
        ):
            raise EmulatorError("Mod index is out of range")
        record = mods[selected_index]
        if not isinstance(record, dict):
            raise EmulatorError("Selected mod record is invalid")

        patch_path = self._project_path(
            str(record.get("relative_path", "")),
            must_exist=True,
        )
        managed_root = self._project_path(
            f"{self.MOD_USER_CONTENT_ROOT}/{str(game.get('id', '')).strip()}/mods"
        )
        try:
            patch_path.resolve().relative_to(managed_root.resolve())
        except ValueError as exc:
            raise EmulatorError("Selected mod escaped managed user content") from exc
        if self._sha256_file(patch_path) != str(record.get("sha256", "")).upper():
            raise EmulatorError("Selected mod changed after catalog validation")

        profile = self._prepare_mod_profile_storage(game, record)
        session = {
            "session_kind": "mod",
            "game_id": str(game.get("id", "")).strip(),
            "mod_index": selected_index,
            "mod_filename": str(record.get("filename", "")),
            "mod_format": str(record.get("format", "")),
            "mod_relative_path": str(record.get("relative_path", "")),
            "mod_sha256": str(record.get("sha256", "")).upper(),
            **profile,
        }
        return str(record.get("cli_flag", "")), patch_path, session

    def mod_profiles(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        with self.lock:
            catalog = self._mod_catalog_unlocked(game)
            game_id = str(game.get("id", "")).strip()
            system = str(game.get("system", "")).strip()
            relative_path = str(game.get("relative_path", "")).strip().replace("\\", "/")
            result: dict[str, Any] = {
                "game_id": game_id,
                "system": system,
                "status": catalog.get("status", "unavailable"),
                "supported": bool(catalog.get("supported")),
                "reason": catalog.get("reason"),
                "profile_schema": self.MOD_PROFILE_SCHEMA,
                "profiles": [],
                "invalid_profiles": [],
            }
            if not result["supported"]:
                return result

            mods = catalog.get("mods", [])
            if not isinstance(mods, list):
                raise EmulatorError("Validated mod catalog is unavailable")
            by_identity = {
                (
                    str(item.get("relative_path", "")),
                    str(item.get("sha256", "")).upper(),
                ): item
                for item in mods
                if isinstance(item, dict)
            }

            root = self._project_path(self.MOD_PROFILE_ROOT)
            game_root = (root / game_id).resolve()
            game_root.relative_to(root.resolve())
            if not game_root.is_dir():
                return result

            for profile_root in sorted(path for path in game_root.iterdir() if path.is_dir()):
                profile_path = (profile_root / "profile.json").resolve()
                if not profile_path.is_file():
                    result["invalid_profiles"].append(
                        {"profile_id": profile_root.name, "reason": "missing_profile_metadata"}
                    )
                    continue
                try:
                    metadata = json.loads(profile_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    result["invalid_profiles"].append(
                        {"profile_id": profile_root.name, "reason": "invalid_profile_metadata"}
                    )
                    continue
                identity = metadata.get("identity") if isinstance(metadata, dict) else None
                if not isinstance(identity, dict) or metadata.get("schema") != self.MOD_PROFILE_SCHEMA:
                    result["invalid_profiles"].append(
                        {"profile_id": profile_root.name, "reason": "invalid_profile_identity"}
                    )
                    continue
                expected_base = {
                    "schema": self.MOD_PROFILE_SCHEMA,
                    "game_id": game_id,
                    "system": system,
                    "relative_path": relative_path,
                    "mod_relative_path": str(identity.get("mod_relative_path", "")),
                    "mod_sha256": str(identity.get("mod_sha256", "")).upper(),
                }
                if identity != expected_base:
                    result["invalid_profiles"].append(
                        {"profile_id": profile_root.name, "reason": "profile_identity_mismatch"}
                    )
                    continue
                record = by_identity.get(
                    (expected_base["mod_relative_path"], expected_base["mod_sha256"])
                )
                if not isinstance(record, dict):
                    result["invalid_profiles"].append(
                        {"profile_id": profile_root.name, "reason": "mod_source_unavailable"}
                    )
                    continue
                canonical = json.dumps(
                    expected_base,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                expected_id = hashlib.sha256(canonical).hexdigest().upper()
                if (
                    profile_root.name.upper() != expected_id
                    or str(metadata.get("profile_id", "")).upper() != expected_id
                ):
                    result["invalid_profiles"].append(
                        {"profile_id": profile_root.name, "reason": "profile_hash_mismatch"}
                    )
                    continue
                slots = self._cheat_profile_slot_summaries(
                    game,
                    expected_id,
                    profile_root,
                )
                saves_root = (profile_root / "saves").resolve()
                persistent = False
                if saves_root.is_dir():
                    try:
                        persistent = any(
                            path.is_file() and path.stat().st_size > 0
                            for path in saves_root.rglob("*")
                        )
                    except OSError:
                        persistent = False
                result["profiles"].append(
                    {
                        "profile_id": expected_id,
                        "mod_index": int(record.get("mod_index", -1)),
                        "filename": str(record.get("filename", "")),
                        "format": str(record.get("format", "")),
                        "relative_path": str(record.get("relative_path", "")),
                        "sha256": str(record.get("sha256", "")).upper(),
                        "persistent_save_present": persistent,
                        "state_slots": slots,
                        "occupied_slots": [
                            item["slot"] for item in slots if item.get("exists")
                        ],
                    }
                )
            result["profiles"].sort(key=lambda item: (str(item.get("filename", "")).casefold(), item["profile_id"]))
            return result

    # PrivyHub A7.3: generic cheat catalog/staging backend. Cheat sessions
    # use deterministic, profile-isolated save/state namespaces and fixed
    # enabled-index profiles verified through RetroArch NCI before use.
    CHEAT_MANIFEST_RELATIVE = "data/games/cheats.json"
    CHEAT_RUNTIME_ROOT = "data/games/retroarch/cheat_runtime"
    CHEAT_PROFILE_ROOT = "data/games/retroarch/cheat_profiles"
    CHEAT_PROFILE_SCHEMA = 2
    CHEAT_MAX_CODES_PER_FILE = 4096
    CHEAT_CORE_LIBRARY_NAMES = {
        "nes": "FCEUmm",
        "snes": "bsnes",
        "genesis": "BlastEm",
        "ps1": "Beetle PSX HW",
    }

    # PrivyHub A7.3: NCI cheat hotkeys are one-frame virtual input pulses.
    # Patch 03f runtime-validated a quiet interval on both sides of CHEAT_TOGGLE.
    CHEAT_TOGGLE_SETTLE_SECONDS = 0.25

    _CHEAT_COUNT_RE = re.compile(
        r'^\s*cheats\s*=\s*["\']?([0-9]+)["\']?\s*$',
        re.IGNORECASE,
    )
    _CHEAT_KEY_RE = re.compile(
        r'^\s*cheat([0-9]+)_([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$',
    )

    @staticmethod
    def _cheat_scalar_text(value: str) -> str:
        text = str(value).strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
            text = text[1:-1]
        return text

    def _cleanup_cheat_runtime(self) -> str | None:
        root = self._project_path(self.CHEAT_RUNTIME_ROOT)
        if not root.exists():
            return None
        try:
            shutil.rmtree(root)
            return None
        except OSError as exc:
            return str(exc)

    def _read_cheat_source(
        self,
        relative_path: str,
        expected_sha256: str,
    ) -> dict[str, Any]:
        source = self._project_path(
            relative_path,
            must_exist=True,
        )
        try:
            raw = source.read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise EmulatorError(
                f"Unable to read cached cheat file: {exc}"
            ) from exc

        digest = hashlib.sha256(raw).hexdigest().upper()
        wanted_digest = str(expected_sha256).strip().upper()
        if not wanted_digest or digest != wanted_digest:
            raise EmulatorError(
                "Cached cheat file SHA-256 does not match its A7.2 manifest"
            )

        declared_count: int | None = None
        fields: dict[int, dict[str, str]] = {}

        for line in text.splitlines():
            count_match = self._CHEAT_COUNT_RE.match(line)
            if count_match is not None:
                declared_count = int(count_match.group(1))
                continue

            key_match = self._CHEAT_KEY_RE.match(line)
            if key_match is None:
                continue

            index = int(key_match.group(1))
            key = key_match.group(2).casefold()
            value = key_match.group(3)
            fields.setdefault(index, {})[key] = value

        if (
            declared_count is None
            or declared_count < 1
            or declared_count > self.CHEAT_MAX_CODES_PER_FILE
        ):
            raise EmulatorError(
                "Cached cheat file has an invalid declared cheat count"
            )

        if any(index >= declared_count for index in fields):
            raise EmulatorError(
                "Cached cheat file references an index beyond its declared count"
            )

        entries: list[dict[str, Any]] = []
        for index in range(declared_count):
            item = fields.get(index, {})
            description = self._cheat_scalar_text(
                item.get("desc", "")
            ).strip()
            code = self._cheat_scalar_text(
                item.get("code", "")
            ).strip()
            enabled = self._cheat_scalar_text(
                item.get("enable", "false")
            ).strip().casefold()

            if not description or not code:
                raise EmulatorError(
                    "Cached cheat file is missing a cheat description or payload"
                )

            if enabled in {"true", "yes", "1"}:
                raise EmulatorError(
                    "PrivyHub refuses a cached cheat source containing pre-enabled cheats"
                )

            entries.append(
                {
                    "index": index,
                    "description": description,
                    "enabled": False,
                }
            )

        return {
            "path": source,
            "raw": raw,
            "sha256": digest,
            "cheat_count": declared_count,
            "entries": entries,
        }

    def _cheat_catalog_unlocked(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        game_id = str(game.get("id", "")).strip()
        relative_path = str(
            game.get("relative_path", "")
        ).strip().replace("\\", "/")
        system_id = str(game.get("system", "")).strip()

        if not game_id or not relative_path or not system_id:
            raise EmulatorError("Game record is incomplete")

        manifest = self._project_path(
            self.CHEAT_MANIFEST_RELATIVE,
            must_exist=True,
        )
        try:
            payload = json.loads(
                manifest.read_text(encoding="utf-8-sig")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise EmulatorError(
                f"Unable to read cheat manifest: {exc}"
            ) from exc

        games = payload.get("games") if isinstance(payload, dict) else None
        if not isinstance(games, dict):
            raise EmulatorError("Cheat manifest games entry is invalid")

        record = games.get(game_id)
        if not isinstance(record, dict):
            return {
                "game_id": game_id,
                "system": system_id,
                "status": "no_manifest_record",
                "activation_available": False,
                "activation_locked_reason": (
                    "isolated_cheat_profile_launch_required"
                ),
                "sources": [],
            }

        if str(record.get("id", "")).strip() != game_id:
            raise EmulatorError("Cheat manifest game identity mismatch")
        if str(record.get("system", "")).strip() != system_id:
            raise EmulatorError("Cheat manifest system identity mismatch")
        if str(record.get("relative_path", "")).strip().replace("\\", "/") != relative_path:
            raise EmulatorError("Cheat manifest content identity mismatch")

        status = str(record.get("status", "")).strip()
        raw_files = record.get("files", [])
        if status != "cached" or not isinstance(raw_files, list):
            return {
                "game_id": game_id,
                "system": system_id,
                "status": status or "unavailable",
                "activation_available": False,
                "activation_locked_reason": (
                    "isolated_cheat_profile_launch_required"
                ),
                "sources": [],
            }

        sources: list[dict[str, Any]] = []
        for source_index, file_record in enumerate(raw_files):
            if not isinstance(file_record, dict):
                raise EmulatorError("Cheat manifest source record is invalid")

            local_path = str(file_record.get("local_path", "")).strip()
            local_sha256 = str(file_record.get("local_sha256", "")).strip()
            if not local_path or not local_sha256:
                raise EmulatorError("Cheat manifest source record is incomplete")

            parsed = self._read_cheat_source(
                local_path,
                local_sha256,
            )
            manifest_count = int(file_record.get("cheat_count", 0) or 0)
            if manifest_count != int(parsed["cheat_count"]):
                raise EmulatorError(
                    "Cheat source count does not match its A7.2 manifest"
                )

            sources.append(
                {
                    "source_index": source_index,
                    "provider": str(record.get("provider", "libretro")),
                    "filename": str(file_record.get("local_filename", "")).strip(),
                    "local_path": local_path.replace("\\", "/"),
                    "sha256": parsed["sha256"],
                    "cheat_count": parsed["cheat_count"],
                    "entries": parsed["entries"],
                }
            )

        return {
            "game_id": game_id,
            "system": system_id,
            "status": "cached",
            "activation_available": False,
            "activation_locked_reason": (
                "isolated_cheat_profile_launch_required"
            ),
            "sources": sources,
        }

    def cheat_catalog(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        with self.lock:
            return self._cheat_catalog_unlocked(game)

    def _cheat_profile_slot_summaries(
        self,
        game: dict[str, Any],
        profile_id: str,
        profile_root: Path,
    ) -> list[dict[str, Any]]:
        summaries = [
            {
                "slot": slot,
                "exists": False,
                "invalid": False,
                "overwrite_requires_confirmation": False,
            }
            for slot in self.SAVE_STATE_SLOTS
        ]

        index_path = (profile_root / "privyhub_state_slots.json").resolve()
        index_path.relative_to(profile_root.resolve())
        if not index_path.is_file():
            return summaries

        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            for item in summaries:
                item["invalid"] = True
                item["invalid_reason"] = "invalid_slot_index"
                item["overwrite_requires_confirmation"] = True
            return summaries

        games = payload.get("games") if isinstance(payload, dict) else None
        if not isinstance(games, dict):
            for item in summaries:
                item["invalid"] = True
                item["invalid_reason"] = "invalid_slot_index"
                item["overwrite_requires_confirmation"] = True
            return summaries

        relative_path = str(game.get("relative_path", "")).strip().replace("\\", "/")
        system = str(game.get("system", "")).strip()
        game_key = system.casefold() + "::" + relative_path.casefold()
        entry = games.get(game_key)
        if not isinstance(entry, dict):
            return summaries

        if str(entry.get("cheat_profile_id", "")).strip().upper() != profile_id.upper():
            for item in summaries:
                item["invalid"] = True
                item["invalid_reason"] = "profile_identity_mismatch"
                item["overwrite_requires_confirmation"] = True
            return summaries

        slots = entry.get("slots")
        if not isinstance(slots, dict):
            return summaries

        states_root = (profile_root / "states").resolve()
        for item in summaries:
            record = slots.get(str(item["slot"]))
            if not isinstance(record, dict):
                continue
            relative = str(record.get("state_file", "")).strip()
            if not relative:
                item["invalid"] = True
                item["invalid_reason"] = "missing_state_file"
                item["overwrite_requires_confirmation"] = True
                continue
            try:
                path = self._project_path(relative, must_exist=True)
                path.relative_to(states_root)
                stat = path.stat()
            except (EmulatorError, OSError, ValueError):
                item["invalid"] = True
                item["invalid_reason"] = "profile_state_path_mismatch"
                item["overwrite_requires_confirmation"] = True
                continue
            if stat.st_size <= 0:
                item["invalid"] = True
                item["invalid_reason"] = "zero_byte_state"
                item["overwrite_requires_confirmation"] = True
                continue
            item.update(
                {
                    "exists": True,
                    "size_bytes": int(stat.st_size),
                    "modified_unix_ms": int(stat.st_mtime * 1000),
                    "state_file": str(path.relative_to(self.project_root)).replace("\\", "/"),
                    "overwrite_requires_confirmation": True,
                }
            )
        return summaries

    def cheat_profiles(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        with self.lock:
            catalog = self._cheat_catalog_unlocked(game)
            game_id = str(game.get("id", "")).strip()
            system = str(game.get("system", "")).strip()
            relative_path = str(game.get("relative_path", "")).strip().replace("\\", "/")
            if not game_id or not system or not relative_path:
                raise EmulatorError("Game record is incomplete")

            result: dict[str, Any] = {
                "game_id": game_id,
                "system": system,
                "status": catalog.get("status", "unavailable"),
                "profile_schema": self.CHEAT_PROFILE_SCHEMA,
                "profiles": [],
                "legacy_profiles_ignored": 0,
                "invalid_profiles": [],
            }
            if catalog.get("status") != "cached":
                return result

            sources = catalog.get("sources", [])
            if not isinstance(sources, list):
                raise EmulatorError("Validated cheat sources are unavailable")

            profile_root = self._project_path(self.CHEAT_PROFILE_ROOT)
            game_root = (profile_root / game_id).resolve()
            game_root.relative_to(profile_root.resolve())
            if not game_root.is_dir():
                return result

            for root in sorted(path for path in game_root.iterdir() if path.is_dir()):
                profile_path = (root / "profile.json").resolve()
                try:
                    profile_path.relative_to(root.resolve())
                except ValueError:
                    continue
                if not profile_path.is_file():
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "missing_profile_metadata"}
                    )
                    continue
                try:
                    metadata = json.loads(profile_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "invalid_profile_metadata"}
                    )
                    continue
                if not isinstance(metadata, dict):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "invalid_profile_metadata"}
                    )
                    continue
                schema = metadata.get("schema")
                if schema != self.CHEAT_PROFILE_SCHEMA:
                    result["legacy_profiles_ignored"] += 1
                    continue
                identity = metadata.get("identity")
                if not isinstance(identity, dict):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "invalid_profile_identity"}
                    )
                    continue
                try:
                    source_index = int(identity.get("source_index"))
                except (TypeError, ValueError):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "invalid_source_index"}
                    )
                    continue
                if source_index < 0 or source_index >= len(sources):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "source_index_out_of_range"}
                    )
                    continue
                source = sources[source_index]
                raw_indexes = identity.get("enabled_cheat_indexes")
                if not isinstance(raw_indexes, list) or any(isinstance(v, bool) for v in raw_indexes):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "invalid_enabled_indexes"}
                    )
                    continue
                try:
                    enabled_indexes = [int(value) for value in raw_indexes]
                except (TypeError, ValueError):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "invalid_enabled_indexes"}
                    )
                    continue
                if enabled_indexes != sorted(set(enabled_indexes)):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "invalid_enabled_indexes"}
                    )
                    continue

                entries = source.get("entries", [])
                entry_by_index = {
                    int(item["index"]): item
                    for item in entries
                    if isinstance(item, dict) and isinstance(item.get("index"), int)
                }
                if any(index not in entry_by_index for index in enabled_indexes):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "enabled_index_out_of_range"}
                    )
                    continue

                expected_identity = {
                    "schema": self.CHEAT_PROFILE_SCHEMA,
                    "game_id": game_id,
                    "system": system,
                    "relative_path": relative_path,
                    "source_index": source_index,
                    "source_sha256": str(source.get("sha256", "")).upper(),
                    "enabled_cheat_indexes": enabled_indexes,
                }
                if identity != expected_identity:
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "profile_identity_mismatch"}
                    )
                    continue
                canonical = json.dumps(
                    expected_identity,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                expected_profile_id = hashlib.sha256(canonical).hexdigest().upper()
                if (
                    root.name.upper() != expected_profile_id
                    or str(metadata.get("profile_id", "")).strip().upper() != expected_profile_id
                ):
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "profile_hash_mismatch"}
                    )
                    continue

                expected_enabled = [
                    {
                        "index": index,
                        "description": str(entry_by_index[index].get("description", "")),
                    }
                    for index in enabled_indexes
                ]
                if metadata.get("enabled_cheats") != expected_enabled:
                    result["invalid_profiles"].append(
                        {"profile_id": root.name, "reason": "enabled_cheat_metadata_mismatch"}
                    )
                    continue

                slots = self._cheat_profile_slot_summaries(
                    game,
                    expected_profile_id,
                    root,
                )
                saves_root = (root / "saves").resolve()
                saves_root.relative_to(root.resolve())
                persistent_save_present = False
                if saves_root.is_dir():
                    try:
                        persistent_save_present = any(
                            path.is_file() and path.stat().st_size > 0
                            for path in saves_root.rglob("*")
                        )
                    except OSError:
                        persistent_save_present = False

                result["profiles"].append(
                    {
                        "profile_id": expected_profile_id,
                        "source_index": source_index,
                        "source_filename": str(source.get("filename", "")),
                        "source_sha256": str(source.get("sha256", "")).upper(),
                        "enabled_cheat_indexes": enabled_indexes,
                        "enabled_cheats": expected_enabled,
                        "persistent_save_present": persistent_save_present,
                        "state_slots": slots,
                        "occupied_slots": [
                            item["slot"] for item in slots if item.get("exists")
                        ],
                    }
                )

            result["profiles"].sort(key=lambda item: item["profile_id"])
            return result

    def _prepare_cheat_profile_storage(
        self,
        game: dict[str, Any],
        source_record: dict[str, Any],
        enabled_indexes: list[int] | tuple[int, ...] | None,
    ) -> dict[str, Any]:
        raw_indexes = [] if enabled_indexes is None else list(enabled_indexes)
        normalized: list[int] = []
        for value in raw_indexes:
            if isinstance(value, bool):
                raise EmulatorError("Cheat indexes must be integers")
            try:
                index = int(value)
            except (TypeError, ValueError) as exc:
                raise EmulatorError("Cheat indexes must be integers") from exc
            normalized.append(index)

        if len(set(normalized)) != len(normalized):
            raise EmulatorError("Cheat profile contains duplicate indexes")

        normalized.sort()
        entries = source_record.get("entries", [])
        if not isinstance(entries, list):
            raise EmulatorError("Validated cheat source entries are unavailable")

        entry_by_index = {
            int(item.get("index")): item
            for item in entries
            if isinstance(item, dict) and isinstance(item.get("index"), int)
        }
        for index in normalized:
            if index not in entry_by_index:
                raise EmulatorError("Cheat profile index is out of range")

        identity = {
            "schema": self.CHEAT_PROFILE_SCHEMA,
            "game_id": str(game.get("id", "")).strip(),
            "system": str(game.get("system", "")).strip(),
            "relative_path": str(
                game.get("relative_path", "")
            ).strip().replace("\\", "/"),
            "source_index": int(source_record["source_index"]),
            "source_sha256": str(source_record["sha256"]).upper(),
            "enabled_cheat_indexes": normalized,
        }
        if not identity["game_id"] or not identity["system"] or not identity["relative_path"]:
            raise EmulatorError("Game record is incomplete")

        canonical = json.dumps(
            identity,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        profile_id = hashlib.sha256(canonical).hexdigest().upper()

        profile_root = self._project_path(self.CHEAT_PROFILE_ROOT)
        game_root = (profile_root / identity["game_id"]).resolve()
        game_root.relative_to(profile_root.resolve())
        root = (game_root / profile_id).resolve()
        root.relative_to(game_root)

        savefile_directory = (root / "saves").resolve()
        savestate_directory = (root / "states").resolve()
        state_slot_index = (root / "privyhub_state_slots.json").resolve()
        profile_path = (root / "profile.json").resolve()
        for candidate in (
            savefile_directory,
            savestate_directory,
            state_slot_index,
            profile_path,
        ):
            candidate.relative_to(root)

        enabled = [
            {
                "index": index,
                "description": str(entry_by_index[index].get("description", "")),
            }
            for index in normalized
        ]
        metadata = {
            "schema": self.CHEAT_PROFILE_SCHEMA,
            "profile_id": profile_id,
            "identity": identity,
            "source_filename": str(source_record.get("filename", "")),
            "enabled_cheats": enabled,
        }

        root.mkdir(parents=True, exist_ok=True)
        savefile_directory.mkdir(parents=True, exist_ok=True)
        savestate_directory.mkdir(parents=True, exist_ok=True)

        if profile_path.is_file():
            try:
                existing = json.loads(profile_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise EmulatorError(
                    f"Unable to read cheat profile metadata: {exc}"
                ) from exc
            if existing != metadata:
                raise EmulatorError(
                    "Cheat profile metadata does not match its deterministic identity"
                )
        else:
            temporary = profile_path.with_name(profile_path.name + ".tmp")
            try:
                temporary.write_text(
                    json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                temporary.replace(profile_path)
            except OSError as exc:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
                raise EmulatorError(
                    f"Unable to write cheat profile metadata: {exc}"
                ) from exc

        return {
            "profile_id": profile_id,
            "profile_path": str(
                profile_path.relative_to(self.project_root)
            ).replace("\\", "/"),
            "profile_root": str(root.relative_to(self.project_root)).replace(
                "\\", "/"
            ),
            "savefile_directory": str(
                savefile_directory.relative_to(self.project_root)
            ).replace("\\", "/"),
            "savestate_directory": str(
                savestate_directory.relative_to(self.project_root)
            ).replace("\\", "/"),
            "state_slot_index": str(
                state_slot_index.relative_to(self.project_root)
            ).replace("\\", "/"),
            "enabled_cheat_indexes": normalized,
            "enabled_cheats": enabled,
        }

    def _prepare_cheat_runtime(
        self,
        game: dict[str, Any],
        content_path: Path,
        source_index: int,
        enabled_indexes: list[int] | tuple[int, ...] | None = None,
    ) -> tuple[Path, dict[str, Any]]:
        catalog = self._cheat_catalog_unlocked(game)
        if catalog.get("status") != "cached":
            raise EmulatorError("No cached cheats are available for this game")

        try:
            selected_index = int(source_index)
        except (TypeError, ValueError) as exc:
            raise EmulatorError("Cheat source index must be an integer") from exc

        sources = catalog.get("sources", [])
        if (
            not isinstance(sources, list)
            or selected_index < 0
            or selected_index >= len(sources)
        ):
            raise EmulatorError("Cheat source index is out of range")

        system_id = str(game.get("system", "")).strip()
        core_library_name = self.CHEAT_CORE_LIBRARY_NAMES.get(system_id)
        if not core_library_name:
            raise EmulatorError(
                f"No validated RetroArch cheat library name for system: {system_id}"
            )

        cleanup_error = self._cleanup_cheat_runtime()
        if cleanup_error:
            raise EmulatorError(
                "Unable to clean prior cheat runtime staging: " + cleanup_error
            )

        source_record = sources[selected_index]
        parsed = self._read_cheat_source(
            str(source_record["local_path"]),
            str(source_record["sha256"]),
        )

        root = self._project_path(self.CHEAT_RUNTIME_ROOT)
        target_dir = (root / core_library_name).resolve()
        target_dir.relative_to(self.project_root)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = (target_dir / f"{content_path.stem}.cht").resolve()
        target.relative_to(root.resolve())
        temporary = target.with_name(target.name + ".tmp")

        try:
            temporary.write_bytes(parsed["raw"])
            temporary.replace(target)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            self._cleanup_cheat_runtime()
            raise EmulatorError(
                f"Unable to stage cheat source: {exc}"
            ) from exc

        staged_sha = hashlib.sha256(target.read_bytes()).hexdigest().upper()
        if staged_sha != str(source_record["sha256"]).upper():
            self._cleanup_cheat_runtime()
            raise EmulatorError("Staged cheat source failed SHA-256 verification")

        try:
            profile = self._prepare_cheat_profile_storage(
                game,
                source_record,
                enabled_indexes,
            )
        except Exception:
            self._cleanup_cheat_runtime()
            raise

        session = {
            "session_kind": "cheat",
            "game_id": str(game.get("id", "")).strip(),
            "source_index": selected_index,
            "source_filename": source_record["filename"],
            "source_sha256": staged_sha,
            "cheat_count": source_record["cheat_count"],
            "entries": source_record["entries"],
            "staged_file": str(
                target.relative_to(self.project_root)
            ).replace("\\", "/"),
            **profile,
            "activation_available": False,
            "activation_locked_reason": (
                "isolated_cheat_profile_launch_required"
            ),
        }
        return root, session

    def active_cheats(self) -> dict[str, Any]:
        with self.lock:
            self._refresh_process()
            if self.process is None or self.process.poll() is not None:
                raise EmulatorError("No PrivyHub game session is running")

            if (
                self._active_cheat_session is None
                or self._active_cheat_session.get("session_kind", "cheat") != "cheat"
            ):
                return {
                    "active": False,
                    "activation_available": False,
                    "activation_locked_reason": "cheat_source_not_staged",
                }

            return {
                "active": True,
                **dict(self._active_cheat_session),
            }

    def _wait_for_cheat_state_line(
        self,
        offset: int,
        *,
        index: int,
        description: str,
        timeout: float = 1.0,
    ) -> tuple[str, bool] | None:
        marker = f"Cheat #{int(index)}: {str(description).strip()}: "
        wanted = marker.casefold()
        deadline = time.monotonic() + max(0.25, float(timeout))
        while time.monotonic() < deadline:
            for line in reversed(self._retroarch_session_log_since(offset)):
                folded = line.casefold().strip()
                if wanted not in folded:
                    continue
                if folded.endswith(": on"):
                    return line, True
                if folded.endswith(": off"):
                    return line, False
            time.sleep(0.05)
        return None

    def _select_cheat_index_state(
        self,
        session: dict[str, Any],
        target_index: int,
    ) -> tuple[str, bool]:
        entries = session.get("entries", [])
        if not isinstance(entries, list) or not entries:
            raise EmulatorError("Active cheat source entries are unavailable")
        by_index = {
            int(item["index"]): item
            for item in entries
            if isinstance(item, dict) and isinstance(item.get("index"), int)
        }
        target = by_index.get(int(target_index))
        if not isinstance(target, dict):
            raise EmulatorError("Cheat index is not present in the active source")
        description = str(target.get("description", "")).strip()
        if not description:
            raise EmulatorError("Active cheat entry has no description")

        # NCI cheat-index actions are one-frame virtual input pulses. Send the
        # next pulse only after RetroArch has logged the result of the previous
        # one. This makes selection deterministic without assuming the current
        # frontend cheat index.
        for _ in range(len(by_index) + 1):
            offset = self._retroarch_session_log_position()
            self._retroarch_network_request(
                "CHEAT_INDEX_PLUS",
                expect_response=False,
                retries=1,
            )
            deadline = time.monotonic() + 1.0
            observed_index: int | None = None
            observed_state = False
            observed_line = ""
            while time.monotonic() < deadline and observed_index is None:
                for line in reversed(self._retroarch_session_log_since(offset)):
                    folded = line.casefold().strip()
                    for item_index, item in by_index.items():
                        description_text = str(item.get("description", "")).strip()
                        marker = (
                            f"Cheat #{item_index}: {description_text}: "
                        ).casefold()
                        if marker not in folded:
                            continue
                        if folded.endswith(": on"):
                            observed_state = True
                        elif folded.endswith(": off"):
                            observed_state = False
                        else:
                            continue
                        observed_index = item_index
                        observed_line = line
                        break
                    if observed_index is not None:
                        break
                if observed_index is None:
                    time.sleep(0.05)
            if observed_index is None:
                raise EmulatorError(
                    "RetroArch did not report cheat-index navigation state"
                )
            if observed_index == int(target_index):
                return observed_line, observed_state

        raise EmulatorError("Unable to select requested cheat index")

    def _validate_active_cheat_profile_identity(
        self,
        session: dict[str, Any],
    ) -> None:
        profile_path = self._project_path(
            str(session.get("profile_path", "")),
            must_exist=True,
        )
        try:
            metadata = json.loads(profile_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EmulatorError(
                f"Unable to read active cheat profile metadata: {exc}"
            ) from exc
        if not isinstance(metadata, dict):
            raise EmulatorError("Active cheat profile metadata is invalid")
        identity = metadata.get("identity")
        if not isinstance(identity, dict):
            raise EmulatorError("Active cheat profile identity is invalid")
        checks = {
            "schema": self.CHEAT_PROFILE_SCHEMA,
            "game_id": str(session.get("game_id", "")).strip(),
            "source_index": int(session.get("source_index", -1)),
            "source_sha256": str(session.get("source_sha256", "")).upper(),
            "enabled_cheat_indexes": list(session.get("enabled_cheat_indexes", [])),
        }
        for key, expected in checks.items():
            if identity.get(key) != expected:
                raise EmulatorError(
                    "Active cheat profile metadata does not match the running session"
                )
        if str(metadata.get("profile_id", "")).upper() != str(
            session.get("profile_id", "")
        ).upper():
            raise EmulatorError("Active cheat profile ID mismatch")

    def _apply_active_cheat_profile(self) -> dict[str, Any]:
        session = self._active_cheat_session
        if not isinstance(session, dict):
            raise EmulatorError("No isolated cheat profile is active")
        self._validate_active_cheat_profile_identity(session)
        desired = list(session.get("enabled_cheat_indexes", []))
        if not desired:
            session["activation_available"] = True
            session["activation_locked_reason"] = None
            session["activation_verified"] = True
            session["active_enabled_cheat_indexes"] = []
            return dict(session)

        initial_state = self._retroarch_network_status()
        if initial_state != "PLAYING":
            raise EmulatorError(
                "Cheat profile activation requires RetroArch to begin in PLAYING state"
            )

        self.pause()
        toggled_indexes: list[int] = []
        verification_lines: list[str] = []
        try:
            for index in desired:
                selected_line, selected_on = self._select_cheat_index_state(
                    session,
                    int(index),
                )
                verification_lines.append(selected_line)
                if selected_on:
                    raise EmulatorError(
                        "Requested cheat was unexpectedly enabled before profile activation"
                    )

                # Keep a full quiet window on both sides of CHEAT_TOGGLE. Patch
                # 03f runtime-validated this as necessary for NCI hotkey pulses.
                time.sleep(self.CHEAT_TOGGLE_SETTLE_SECONDS)
                self._retroarch_network_request(
                    "CHEAT_TOGGLE",
                    expect_response=False,
                    retries=1,
                )
                toggled_indexes.append(int(index))
                time.sleep(self.CHEAT_TOGGLE_SETTLE_SECONDS)

                verified_line, verified_on = self._select_cheat_index_state(
                    session,
                    int(index),
                )
                verification_lines.append(verified_line)
                if not verified_on:
                    raise EmulatorError(
                        "RetroArch did not verify the requested cheat as enabled"
                    )

            session["activation_available"] = True
            session["activation_locked_reason"] = None
            session["activation_verified"] = True
            session["active_enabled_cheat_indexes"] = list(desired)
            session["activation_verification_lines"] = list(verification_lines)
            self.resume()
            return dict(session)

        except Exception as exc:
            # Once any toggle pulse has been sent, do not resume or flush a
            # potentially uncertain session. The isolated namespace protects
            # normal saves, and the frontend is terminated without SAVE_FILES.
            session["activation_available"] = False
            session["activation_verified"] = False
            session["activation_error"] = str(exc)
            process = self.process
            if process is not None and process.poll() is None:
                self._force_stop_process(process)
            self._refresh_process()
            raise EmulatorError(
                "Cheat profile activation failed closed: " + str(exc)
            ) from exc

    def set_cheat_enabled(
        self,
        index: int,
        enabled: bool,
    ) -> dict[str, Any]:
        # Cheat profiles are immutable for the lifetime of a session. The UI
        # will create/launch a different deterministic profile instead of
        # mutating the cheat set underneath existing save metadata.
        del index, enabled
        raise EmulatorError(
            "Active cheat sets are fixed by profile; launch a different "
            "isolated cheat profile to change enabled cheats"
        )

    # PrivyHub A2/A3 patch 08: full per-session base config
    def _prepare_retroarch_session_config(
        self,
        retroarch_config: Path,
        input_override: Path,
        *,
        cheat_database_path: Path | None = None,
        cheat_session: dict[str, Any] | None = None,
        mod_session: dict[str, Any] | None = None,
    ) -> Path:
        # Create the exact base config RetroArch will read at startup.
        # Session-critical controller and Network Command Interface settings
        # are copied into the base config instead of relying on --appendconfig.
        config_directory = self._project_path(
            "data/games/retroarch/config"
        )
        config_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        session_config = (
            config_directory
            / "privyhub-session.cfg"
        ).resolve()

        try:
            session_config.relative_to(
                config_directory.resolve()
            )
        except ValueError as exc:
            raise EmulatorError(
                "Generated RetroArch session config escaped its data directory"
            ) from exc

        try:
            base_text = retroarch_config.read_text(
                encoding="utf-8-sig",
            )
            override_text = input_override.read_text(
                encoding="utf-8-sig",
            )
        except OSError as exc:
            raise EmulatorError(
                f"Unable to read RetroArch session config inputs: {exc}"
            ) from exc

        required_settings = (
            'network_cmd_enable = "true"',
            "network_cmd_port = ",
        )
        for setting in required_settings:
            if setting not in override_text:
                raise EmulatorError(
                    "Generated RetroArch input override is missing "
                    f"required session setting: {setting}"
                )

        cheat_override = ""
        if cheat_database_path is not None:
            cheat_database_path.resolve().relative_to(self.project_root)
            cheat_path = str(cheat_database_path.resolve()).replace("\\", "/")
            cheat_override = (
                "\n\n# PrivyHub A7.3 session-only cheat database\n"
                + f'cheat_database_path = "{cheat_path}"\n'
            )

        cheat_storage_override = ""
        expected_storage_settings: dict[str, str] = {}
        if cheat_session is not None and mod_session is not None:
            raise EmulatorError("A session cannot combine cheat and mod profiles")
        isolated_session = cheat_session if cheat_session is not None else mod_session
        if isolated_session is not None:
            savefile_directory = self._project_path(
                str(isolated_session.get("savefile_directory", "")),
                directory=True,
            )
            savestate_directory = self._project_path(
                str(isolated_session.get("savestate_directory", "")),
                directory=True,
            )
            savefile_directory.mkdir(parents=True, exist_ok=True)
            savestate_directory.mkdir(parents=True, exist_ok=True)
            savefile_path = str(savefile_directory).replace("\\", "/")
            savestate_path = str(savestate_directory).replace("\\", "/")

            # PrivyHub A7.3 patch 06b: RetroArch did not honor duplicate
            # savefile_directory/savestate_directory assignments appended to
            # the generated session config. Replace the persistent settings
            # in-place so a cheat-profile session contains exactly one
            # effective assignment for each isolated storage path.
            expected_storage_settings = {
                "savefile_directory": savefile_path,
                "savestate_directory": savestate_path,
            }
            for key, value in expected_storage_settings.items():
                pattern = re.compile(
                    rf"(?m)^\s*{re.escape(key)}\s*=.*$"
                )
                matches = pattern.findall(base_text)
                if len(matches) != 1:
                    raise EmulatorError(
                        "Persistent RetroArch config must contain exactly one "
                        f"{key} assignment for isolated-profile storage"
                    )
                base_text = pattern.sub(
                    f'{key} = "{value}"',
                    base_text,
                    count=1,
                )

            cheat_storage_override = (
                "\n\n# PrivyHub A7.3 cheat-profile storage isolation\n"
                + "# Persistent save/state directory settings were replaced in-place.\n"
            )

        session_text = (
            base_text.rstrip()
            + "\n\n"
            + "# PrivyHub session-only overrides\n"
            + "# Generated from persistent retroarch.cfg + active profile.\n"
            + override_text.rstrip()
            + cheat_override
            + cheat_storage_override
            + "\n\n"
            + "# PrivyHub A4 host coexistence\n"
            + "# Only explicit PrivyHub navigation controls emulator pause.\n"
            + 'pause_nonactive = "false"\n'
        )

        if expected_storage_settings:
            session_lines = session_text.splitlines()
            for key, value in expected_storage_settings.items():
                assignment_pattern = re.compile(
                    rf"^\s*{re.escape(key)}\s*=.*$"
                )
                assignments = [
                    line.strip()
                    for line in session_lines
                    if assignment_pattern.match(line)
                ]
                expected = f'{key} = "{value}"'
                if assignments != [expected]:
                    raise EmulatorError(
                        "Generated cheat-profile session config has an "
                        f"ambiguous {key} assignment"
                    )

        temporary = session_config.with_name(
            session_config.name + ".tmp"
        )

        try:
            temporary.write_text(
                session_text,
                encoding="utf-8",
            )
            temporary.replace(
                session_config
            )
        except OSError as exc:
            try:
                temporary.unlink(
                    missing_ok=True
                )
            except OSError:
                pass
            raise EmulatorError(
                f"Unable to write RetroArch session config: {exc}"
            ) from exc

        return session_config

    # PrivyHub A4 host coexistence
    @staticmethod
    def _windows_foreground_window() -> int:
        if os.name != "nt":
            return 0

        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL(
                "user32",
                use_last_error=True,
            )
            user32.GetForegroundWindow.argtypes = []
            user32.GetForegroundWindow.restype = wintypes.HWND

            hwnd = user32.GetForegroundWindow()
            return int(hwnd or 0)

        except Exception:
            return 0

    @staticmethod
    def _apply_windows_host_coexistence(
        process: subprocess.Popen[Any],
        previous_foreground_hwnd: int,
        *,
        timeout_seconds: float = 2.5,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "mode": "background_nonintrusive",
            "supported": os.name == "nt",
            "applied": False,
            "window_found": False,
            "sent_to_bottom": False,
            "foreground_restore_attempted": False,
            "foreground_restored": False,
            "retroarch_iconic": False,
            "error": None,
        }

        if os.name != "nt":
            result["error"] = "not_windows"
            return result

        if process.poll() is not None:
            result["error"] = "process_exited"
            return result

        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL(
                "user32",
                use_last_error=True,
            )

            callback_type = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HWND,
                wintypes.LPARAM,
            )

            user32.EnumWindows.argtypes = [
                callback_type,
                wintypes.LPARAM,
            ]
            user32.EnumWindows.restype = wintypes.BOOL
            user32.IsWindow.argtypes = [
                wintypes.HWND,
            ]
            user32.IsWindow.restype = wintypes.BOOL
            user32.IsWindowVisible.argtypes = [
                wintypes.HWND,
            ]
            user32.IsWindowVisible.restype = wintypes.BOOL
            user32.IsIconic.argtypes = [
                wintypes.HWND,
            ]
            user32.IsIconic.restype = wintypes.BOOL
            user32.GetWindowThreadProcessId.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(wintypes.DWORD),
            ]
            user32.GetWindowThreadProcessId.restype = wintypes.DWORD
            user32.GetClientRect.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(wintypes.RECT),
            ]
            user32.GetClientRect.restype = wintypes.BOOL
            user32.ShowWindowAsync.argtypes = [
                wintypes.HWND,
                ctypes.c_int,
            ]
            user32.ShowWindowAsync.restype = wintypes.BOOL
            user32.SetWindowPos.argtypes = [
                wintypes.HWND,
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                wintypes.UINT,
            ]
            user32.SetWindowPos.restype = wintypes.BOOL
            user32.SetForegroundWindow.argtypes = [
                wintypes.HWND,
            ]
            user32.SetForegroundWindow.restype = wintypes.BOOL
            user32.GetForegroundWindow.argtypes = []
            user32.GetForegroundWindow.restype = wintypes.HWND

            SW_SHOWNOACTIVATE = 4
            HWND_BOTTOM = 1
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            SWP_ASYNCWINDOWPOS = 0x4000

            target_pid = int(process.pid)
            deadline = (
                time.monotonic()
                + max(
                    0.1,
                    float(timeout_seconds),
                )
            )
            target_hwnd = 0

            while (
                target_hwnd <= 0
                and time.monotonic() < deadline
                and process.poll() is None
            ):
                matches: list[
                    tuple[int, int]
                ] = []

                @callback_type
                def visit_window(
                    hwnd: int,
                    _lparam: int,
                ) -> bool:
                    try:
                        pid = wintypes.DWORD()
                        user32.GetWindowThreadProcessId(
                            hwnd,
                            ctypes.byref(pid),
                        )

                        if int(pid.value) != target_pid:
                            return True

                        if not user32.IsWindowVisible(
                            hwnd
                        ):
                            return True

                        if user32.IsIconic(
                            hwnd
                        ):
                            return True

                        rect = wintypes.RECT()

                        if not user32.GetClientRect(
                            hwnd,
                            ctypes.byref(rect),
                        ):
                            return True

                        width = max(
                            0,
                            int(
                                rect.right
                                - rect.left
                            ),
                        )
                        height = max(
                            0,
                            int(
                                rect.bottom
                                - rect.top
                            ),
                        )

                        if (
                            width < 64
                            or height < 64
                        ):
                            return True

                        matches.append(
                            (
                                int(hwnd),
                                width * height,
                            )
                        )
                    except Exception:
                        return True

                    return True

                user32.EnumWindows(
                    visit_window,
                    0,
                )

                if matches:
                    target_hwnd = max(
                        matches,
                        key=lambda item: item[1],
                    )[0]
                    break

                time.sleep(
                    0.05
                )

            if target_hwnd <= 0:
                result["error"] = "retroarch_window_not_found"
                return result

            result["window_found"] = True
            result["retroarch_iconic"] = bool(
                user32.IsIconic(
                    target_hwnd
                )
            )

            # Keep the window rendered and non-iconic for WGC, but do not
            # activate it. Probe A4-02 established that fully occluded,
            # non-iconic capture continues at the normal fresh-frame rate.
            user32.ShowWindowAsync(
                target_hwnd,
                SW_SHOWNOACTIVATE,
            )

            sent_to_bottom = bool(
                user32.SetWindowPos(
                    target_hwnd,
                    HWND_BOTTOM,
                    0,
                    0,
                    0,
                    0,
                    (
                        SWP_NOMOVE
                        | SWP_NOSIZE
                        | SWP_NOACTIVATE
                        | SWP_ASYNCWINDOWPOS
                    ),
                )
            )
            result["sent_to_bottom"] = sent_to_bottom

            previous = int(
                previous_foreground_hwnd
                or 0
            )

            if (
                previous > 0
                and previous != target_hwnd
                and user32.IsWindow(
                    previous
                )
            ):
                result[
                    "foreground_restore_attempted"
                ] = True

                user32.SetForegroundWindow(
                    previous
                )

                time.sleep(
                    0.03
                )

                foreground = int(
                    user32.GetForegroundWindow()
                    or 0
                )

                result[
                    "foreground_restored"
                ] = (
                    foreground
                    == previous
                )

            result["applied"] = bool(
                sent_to_bottom
            )
            return result

        except Exception as exc:
            result["error"] = (
                f"{type(exc).__name__}: {exc}"
            )
            return result


    def launch(
        self,
        game: dict[str, Any],
        *,
        entry_slot: int | None = None,
        cheat_source_index: int | None = None,
        cheat_enabled_indexes: list[int] | tuple[int, ...] | None = None,
        mod_index: int | None = None,
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

            if cheat_source_index is None and cheat_enabled_indexes is not None:
                raise EmulatorError(
                    "Cheat indexes require an explicit cheat source index"
                )

            cheat_database_path: Path | None = None
            cheat_session: dict[str, Any] | None = None
            mod_session: dict[str, Any] | None = None
            mod_cli_flag: str | None = None
            mod_path: Path | None = None
            if cheat_source_index is not None and mod_index is not None:
                raise EmulatorError("Cheat and mod profiles cannot be combined in one session")
            if cheat_source_index is not None:
                cheat_database_path, cheat_session = self._prepare_cheat_runtime(
                    game,
                    content_path,
                    cheat_source_index,
                    cheat_enabled_indexes,
                )
            elif mod_index is not None:
                mod_cli_flag, mod_path, mod_session = self._prepare_mod_runtime(
                    game,
                    mod_index,
                )
                if str(mod_session.get("mod_format", "")).casefold() == "ips":
                    content_path = self._prepare_ips_derived_content(
                        content_path,
                        mod_path,
                        mod_session,
                    )
                    mod_cli_flag = None
                    mod_path = None

            input_override, input_profile = (
                self._prepare_input_override(
                    game,
                    runtime,
                )
            )

            session_config = (
                self._prepare_retroarch_session_config(
                    retroarch_config,
                    input_override,
                    cheat_database_path=cheat_database_path,
                    cheat_session=cheat_session,
                    mod_session=mod_session,
                )
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

            # PrivyHub Phase A PS1 controller CLI device
            command = [
                str(executable),
                "--config",
                str(session_config),
            ]

            libretro_device = input_profile.get(
                "libretro_device"
            )

            if isinstance(
                libretro_device,
                int,
            ):
                command.extend(
                    [
                        f"--device=1:{libretro_device}",
                        f"--device=2:{libretro_device}",
                    ]
                )

            if entry_slot is not None:
                try:
                    launch_entry_slot = int(entry_slot)
                except (TypeError, ValueError) as exc:
                    raise EmulatorError(
                        "RetroArch entry-state slot must be an integer"
                    ) from exc

                if not 0 <= launch_entry_slot <= 999:
                    raise EmulatorError(
                        "RetroArch entry-state slot must be between 0 and 999"
                    )

                command.append(
                    f"--entryslot={launch_entry_slot}"
                )

            if mod_session is not None and mod_cli_flag is not None:
                if mod_path is None:
                    raise EmulatorError("Validated mod launch arguments are incomplete")
                command.extend([mod_cli_flag, str(mod_path)])

            command.extend(
                [
                    "--verbose",
                    "-L",
                    str(core_path),
                    str(content_path),
                ]
            )

            creationflags = 0
            previous_foreground_hwnd = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
                previous_foreground_hwnd = (
                    self._windows_foreground_window()
                )

            log_handle.write("PrivyHub game session\n")
            log_handle.write(f"Game ID: {game.get('id')}\n")
            log_handle.write(f"Title: {game.get('title')}\n")
            log_handle.write(f"System: {game.get('system')}\n")
            log_handle.write(f"Core: {core_path.name}\n")
            if mod_session is not None:
                log_handle.write(
                    "Mod: "
                    + str(mod_session.get("mod_filename", ""))
                    + " ["
                    + str(mod_session.get("mod_sha256", ""))
                    + "]\n"
                )
                if mod_session.get("patch_application") == "privyhub_ips":
                    log_handle.write(
                        "IPS derived content: "
                        + str(mod_session.get("derived_content_relative_path", ""))
                        + " ["
                        + str(mod_session.get("derived_content_sha256", ""))
                        + "]\n"
                    )
            log_handle.write(
                f"Analog D-pad: {input_profile['analog_dpad']}\n"
            )
            log_handle.write(
                "Controller: "
                f"{input_profile['controller_label']} "
                f"({input_profile['controller_source']})\n"
            )
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
                if cheat_session is not None:
                    self._cleanup_cheat_runtime()
                raise

            self.process = process
            self.log_handle = log_handle
            self.active_game = dict(game)
            self.started_at = time.monotonic()
            self._paused = False
            isolated_session = cheat_session if cheat_session is not None else mod_session
            self._active_cheat_session = (
                dict(isolated_session)
                if isolated_session is not None
                else None
            )

            self._reset_retroarch_command_log()

            self._reset_save_state_probe(
                game=game,
                command=command,
                retroarch_config=session_config,
                input_override=input_override,
                session_log=log_path,
                process=process,
            )

            # Catch immediate startup failures without adding meaningful delay.
            time.sleep(0.15)
            if process.poll() is not None:
                exit_code = process.returncode
                self._refresh_process()
                if cheat_session is not None:
                    self._cleanup_cheat_runtime()
                raise EmulatorError(
                    f"RetroArch exited during startup (code {exit_code}). "
                    f"See {log_path.relative_to(self.project_root)}"
                )

            try:
                command_state = self._wait_for_retroarch_command_ready()
            except EmulatorError:
                self._force_stop_process(
                    process
                )
                self._refresh_process()
                if cheat_session is not None:
                    self._cleanup_cheat_runtime()
                raise

            if cheat_session is not None:
                try:
                    self._apply_active_cheat_profile()
                except Exception:
                    if self.process is not None and self.process.poll() is None:
                        self._force_stop_process(self.process)
                    self._refresh_process()
                    self._cleanup_cheat_runtime()
                    raise

            host_window_policy = (
                self._apply_windows_host_coexistence(
                    process,
                    previous_foreground_hwnd,
                )
            )

            self._host_window_policy = (
                host_window_policy
            )

            log_handle.write(
                "Host coexistence: "
                + json.dumps(
                    host_window_policy,
                    sort_keys=True,
                )
                + "\n"
            )
            log_handle.flush()

            self.record_save_state_probe_event(
                "host_window_policy",
                **host_window_policy,
            )

            payload = self.status()
            payload["retroarch_command_state"] = command_state
            payload["host_window_policy"] = (
                host_window_policy
            )
            payload["action"] = "launch"
            payload["input_profile"] = input_profile
            payload["cheat_session"] = (
                dict(self._active_cheat_session)
                if isinstance(self._active_cheat_session, dict)
                and self._active_cheat_session.get("session_kind", "cheat") == "cheat"
                else None
            )
            payload["mod_session"] = (
                dict(self._active_cheat_session)
                if isinstance(self._active_cheat_session, dict)
                and self._active_cheat_session.get("session_kind") == "mod"
                else None
            )
            payload["log"] = log_path.relative_to(
                self.project_root
            ).as_posix()
            return payload

    # PrivyHub Phase A2 saves and states
    SAVE_STATE_SLOTS = (1, 2, 3)

    def _normalize_save_state_slot(
        self,
        slot: int,
    ) -> int:
        try:
            normalized = int(slot)
        except (TypeError, ValueError) as exc:
            raise EmulatorError(
                "Save-state slot must be 1, 2, or 3"
            ) from exc

        if normalized not in self.SAVE_STATE_SLOTS:
            raise EmulatorError(
                "Save-state slot must be 1, 2, or 3"
            )

        return normalized

    # PrivyHub A2/A3 patch 03: verified RetroArch loopback control.
    # RetroArch NCI reports PAUSED/PLAYING through GET_STATUS, allowing the
    # manager to verify lifecycle transitions instead of setting a local flag
    # after an unverified controller chord.
    RETROARCH_COMMAND_HOST = "127.0.0.1"
    RETROARCH_COMMAND_TIMEOUT = 0.45
    RETROARCH_COMMAND_RETRIES = 3
    RETROARCH_COMMAND_LOG_RELATIVE = (
        "logs/games/retroarch_control_probe.txt"
    )

    @staticmethod
    def _allocate_network_command_port() -> int:
        try:
            with socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            ) as probe:
                probe.bind(("127.0.0.1", 0))
                port = int(
                    probe.getsockname()[1]
                )
        except OSError as exc:
            raise EmulatorError(
                f"Unable to allocate RetroArch command port: {exc}"
            ) from exc

        if not (1024 <= port <= 65535):
            raise EmulatorError(
                "RetroArch command port allocation returned an invalid port"
            )

        return port

    def _retroarch_command_log_path(self) -> Path:
        return self._project_path(
            self.RETROARCH_COMMAND_LOG_RELATIVE
        )

    def _reset_retroarch_command_log(self) -> None:
        try:
            path = self._retroarch_command_log_path()
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            path.write_text(
                "",
                encoding="utf-8",
            )
        except Exception:
            pass

    def _record_retroarch_command(
        self,
        event: str,
        **fields: Any,
    ) -> None:
        try:
            path = self._retroarch_command_log_path()
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            record: dict[str, Any] = {
                "time_unix": time.time(),
                "event": event,
            }
            record.update(fields)
            with path.open(
                "a",
                encoding="utf-8",
                buffering=1,
            ) as handle:
                handle.write(
                    json.dumps(
                        record,
                        sort_keys=True,
                        default=str,
                    )
                    + "\n"
                )
        except Exception:
            pass

        # Mirror the low-level NCI exchange into the per-launch unified trace.
        self.record_save_state_probe_event(
            "retroarch_command",
            command_event=event,
            **fields,
        )

    def _retroarch_network_request(
        self,
        command: str,
        *,
        expect_response: bool,
        timeout: float | None = None,
        retries: int | None = None,
    ) -> str | None:
        self._refresh_process()

        process = self.process
        if process is None or process.poll() is not None:
            raise EmulatorError(
                "No PrivyHub game session is running"
            )

        port = self._network_cmd_port
        if port is None:
            raise EmulatorError(
                "RetroArch network command interface is unavailable"
            )

        normalized = str(command).strip()
        if not normalized:
            raise EmulatorError(
                "RetroArch network command is blank"
            )

        wait = (
            self.RETROARCH_COMMAND_TIMEOUT
            if timeout is None
            else max(0.05, float(timeout))
        )
        attempts = (
            self.RETROARCH_COMMAND_RETRIES
            if retries is None
            else max(1, int(retries))
        )
        payload = normalized.encode(
            "utf-8"
        )
        last_error = ""

        for attempt in range(1, attempts + 1):
            try:
                with socket.socket(
                    socket.AF_INET,
                    socket.SOCK_DGRAM,
                ) as client:
                    client.bind((
                        self.RETROARCH_COMMAND_HOST,
                        0,
                    ))
                    client.settimeout(wait)
                    client.sendto(
                        payload,
                        (
                            self.RETROARCH_COMMAND_HOST,
                            int(port),
                        ),
                    )

                    if not expect_response:
                        self._record_retroarch_command(
                            "command_sent",
                            command=normalized,
                            attempt=attempt,
                            port=int(port),
                        )
                        return None

                    while True:
                        response, source = client.recvfrom(4096)
                        if (
                            source[0]
                            != self.RETROARCH_COMMAND_HOST
                            or int(source[1])
                            != int(port)
                        ):
                            continue

                        text = response.decode(
                            "utf-8",
                            errors="replace",
                        ).strip()
                        self._record_retroarch_command(
                            "command_response",
                            command=normalized,
                            response=text,
                            attempt=attempt,
                            port=int(port),
                        )
                        return text

            except (OSError, socket.timeout) as exc:
                last_error = str(exc)
                self._record_retroarch_command(
                    "command_retry",
                    command=normalized,
                    attempt=attempt,
                    error=last_error,
                    port=int(port),
                )

        raise EmulatorError(
            "RetroArch network command did not respond: "
            f"{normalized}"
            + (
                f" ({last_error})"
                if last_error
                else ""
            )
        )

    def _retroarch_network_status(self) -> str:
        response = self._retroarch_network_request(
                "GET_STATUS",
                expect_response=True,
            )

        if not response:
            raise EmulatorError(
                "RetroArch GET_STATUS returned no response"
            )

        upper = response.upper()
        if upper.startswith("GET_STATUS PAUSED"):
            return "PAUSED"
        if upper.startswith("GET_STATUS PLAYING"):
            return "PLAYING"
        if upper.startswith("GET_STATUS CONTENTLESS"):
            return "CONTENTLESS"

        raise EmulatorError(
            f"Unexpected RetroArch GET_STATUS response: {response}"
        )

    def _wait_for_retroarch_state(
        self,
        wanted: str,
        *,
        timeout: float = 1.5,
    ) -> str:
        target = str(wanted).strip().upper()
        deadline = time.monotonic() + max(
            0.25,
            float(timeout),
        )
        last_state = ""
        last_error = ""

        while time.monotonic() < deadline:
            try:
                last_state = self._retroarch_network_status()
                if last_state == target:
                    return last_state
            except EmulatorError as exc:
                last_error = str(exc)

            time.sleep(0.05)

        raise EmulatorError(
            f"RetroArch did not reach {target}"
            + (
                f"; last state was {last_state}"
                if last_state
                else ""
            )
            + (
                f"; {last_error}"
                if last_error
                else ""
            )
        )

    def _wait_for_retroarch_command_ready(
        self,
        *,
        timeout: float = 2.5,
    ) -> str:
        deadline = time.monotonic() + max(
            0.5,
            float(timeout),
        )
        last_error = ""

        while time.monotonic() < deadline:
            try:
                return self._retroarch_network_status()
            except EmulatorError as exc:
                last_error = str(exc)
                time.sleep(0.05)

        raise EmulatorError(
            "RetroArch network control interface did not become ready"
            + (
                f": {last_error}"
                if last_error
                else ""
            )
        )

    # PrivyHub Phase A2 controller-hotkey state bridge
    HOTKEY_STATE_VERSION = "controller_hotkey_slot0_copy_v0.1"

    def set_hotkey_sender(
        self,
        sender: Callable[[str], dict[str, Any]],
    ) -> None:
        self._hotkey_sender = sender

    def _send_retroarch_hotkey(
        self,
        action: str,
    ) -> dict[str, Any]:
        self._refresh_process()

        process = self.process
        if process is None or process.poll() is not None:
            raise EmulatorError(
                "No PrivyHub game session is running"
            )

        sender = self._hotkey_sender
        if sender is None:
            raise EmulatorError(
                "Native controller hotkey bridge is unavailable"
            )

        self.record_save_state_probe_event(
            "retroarch_hotkey_attempt",
            action=action,
            pid=process.pid,
        )

        try:
            result = sender(action)
        except Exception as exc:
            self.record_save_state_probe_event(
                "retroarch_hotkey_result",
                action=action,
                ok=False,
                error=str(exc),
            )
            raise EmulatorError(
                f"RetroArch controller hotkey failed: {exc}"
            ) from exc

        self.record_save_state_probe_event(
            "retroarch_hotkey_result",
            action=action,
            ok=True,
            result=result,
        )
        return result

    def _active_state_stem(self) -> str:
        game = self.active_game
        if not isinstance(game, dict):
            raise EmulatorError(
                "No PrivyHub game session is running"
            )

        relative_path = str(
            game.get("relative_path", "")
        ).strip()
        if not relative_path:
            raise EmulatorError(
                "Active game record has no content path"
            )

        stem = Path(relative_path).stem
        if not stem:
            raise EmulatorError(
                "Unable to determine active save-state name"
            )
        return stem

    def _state_root(self) -> Path:
        cheat_session = self._active_cheat_session
        if isinstance(cheat_session, dict):
            relative = str(
                cheat_session.get("savestate_directory", "")
            ).strip()
            if not relative:
                raise EmulatorError(
                    "Active isolated profile has no savestate directory"
                )
            root = self._project_path(relative)
        else:
            root = self._project_path(
                "data/games/retroarch/states"
            )
        root.mkdir(
            parents=True,
            exist_ok=True,
        )
        return root

    def _find_state_files(
        self,
        filename: str,
    ) -> list[Path]:
        root = self._state_root()
        wanted = filename.casefold()
        matches: list[Path] = []
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.name.casefold() == wanted
            ):
                matches.append(path)
        return matches

    # PrivyHub A2/A3 patch 07: per-game slot identity
    def _active_game_state_identity(
        self,
    ) -> dict[str, str]:
        game = self.active_game
        if not isinstance(game, dict):
            raise EmulatorError(
                "No PrivyHub game session is running"
            )

        relative_path = str(
            game.get("relative_path", "")
        ).strip().replace("\\", "/")
        if not relative_path:
            raise EmulatorError(
                "Active game record has no content path"
            )

        system = str(
            game.get("system", "")
        ).strip()

        title = str(
            game.get("title", "")
        ).strip()
        if not title:
            title = Path(relative_path).stem

        key = (
            system.casefold()
            + "::"
            + relative_path.casefold()
        )

        identity = {
            "game_key": key,
            "game_title": title,
            "game_system": system,
            "game_relative_path": relative_path,
        }
        cheat_session = self._active_cheat_session
        if isinstance(cheat_session, dict):
            profile_id = str(cheat_session.get("profile_id", "")).strip()
            if not profile_id:
                raise EmulatorError(
                    "Active isolated profile has no deterministic profile id"
                )
            identity["cheat_profile_id"] = profile_id
        return identity

    def _state_slot_index_path(
        self,
    ) -> Path:
        cheat_session = self._active_cheat_session
        if isinstance(cheat_session, dict):
            relative = str(
                cheat_session.get("state_slot_index", "")
            ).strip()
            if not relative:
                raise EmulatorError(
                    "Active isolated profile has no state-slot index"
                )
            path = self._project_path(relative)
        else:
            path = self._project_path(
                "data/games/retroarch/privyhub_state_slots.json"
            )
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        return path

    def _read_state_slot_index(
        self,
    ) -> dict[str, Any]:
        path = self._state_slot_index_path()
        if not path.is_file():
            return {
                "schema": 1,
                "games": {},
            }

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {
                "schema": 1,
                "games": {},
            }

        if not isinstance(payload, dict):
            return {
                "schema": 1,
                "games": {},
            }

        games = payload.get(
            "games",
            {},
        )
        if not isinstance(games, dict):
            games = {}

        return {
            "schema": 1,
            "games": games,
        }

    def _write_state_slot_index(
        self,
        payload: dict[str, Any],
    ) -> None:
        path = self._state_slot_index_path()
        temporary = path.with_name(
            path.name + ".tmp"
        )

        try:
            temporary.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    sort_keys=True,
                ) + "\n",
                encoding="utf-8",
            )
            temporary.replace(
                path
            )
        except OSError as exc:
            try:
                temporary.unlink(
                    missing_ok=True
                )
            except OSError:
                pass
            raise EmulatorError(
                f"Unable to write save-state slot index: {exc}"
            ) from exc

    def _record_state_slot_index(
        self,
        slot: int,
        path: Path,
    ) -> None:
        identity = (
            self._active_game_state_identity()
        )
        payload = (
            self._read_state_slot_index()
        )
        games = payload["games"]

        entry = games.get(
            identity["game_key"]
        )
        if not isinstance(
            entry,
            dict,
        ):
            entry = {}

        slots = entry.get(
            "slots",
            {},
        )
        if not isinstance(
            slots,
            dict,
        ):
            slots = {}

        try:
            stat = path.stat()
            if stat.st_size <= 0:
                raise EmulatorError(
                    "Refusing to index an empty 0-byte savestate"
                )
            relative = str(
                path.relative_to(
                    self.project_root
                )
            ).replace("\\", "/")
        except (
            OSError,
            ValueError,
        ) as exc:
            raise EmulatorError(
                f"Unable to index save-state slot: {exc}"
            ) from exc

        slots[str(slot)] = {
            "state_file": relative,
            "size_bytes": int(
                stat.st_size
            ),
            "modified_unix_ms": int(
                stat.st_mtime
                * 1000
            ),
        }

        entry.update(
            identity
        )
        entry["slots"] = slots
        games[
            identity["game_key"]
        ] = entry
        payload["games"] = games

        self._write_state_slot_index(
            payload
        )

    def _save_state_slot_detail(
        self,
        slot: int,
    ) -> dict[str, Any]:
        normalized = (
            self._normalize_save_state_slot(
                slot
            )
        )
        identity = (
            self._active_game_state_identity()
        )

        base: dict[str, Any] = {
            "slot": normalized,
            **identity,
        }

        payload = (
            self._read_state_slot_index()
        )
        indexed_game = payload[
            "games"
        ].get(
            identity["game_key"]
        )

        if isinstance(
            indexed_game,
            dict,
        ):
            active_profile_id = identity.get("cheat_profile_id")
            if active_profile_id is not None and str(
                indexed_game.get("cheat_profile_id", "")
            ).strip().upper() != str(active_profile_id).strip().upper():
                return {
                    **base,
                    "exists": False,
                    "invalid": True,
                    "invalid_reason": "profile_identity_mismatch",
                    "ambiguous": False,
                    "overwrite_requires_confirmation": True,
                    "source": "privyhub_game_slot_index",
                }
            slots = indexed_game.get(
                "slots",
                {},
            )
            if isinstance(
                slots,
                dict,
            ):
                indexed_slot = slots.get(
                    str(normalized)
                )
                if isinstance(
                    indexed_slot,
                    dict,
                ):
                    relative = str(
                        indexed_slot.get(
                            "state_file",
                            "",
                        )
                    ).strip()

                    if relative:
                        try:
                            indexed_path = (
                                self._project_path(
                                    relative,
                                    must_exist=True,
                                )
                            )
                            if active_profile_id is not None:
                                try:
                                    indexed_path.relative_to(
                                        self._state_root().resolve()
                                    )
                                except ValueError:
                                    return {
                                        **base,
                                        "exists": False,
                                        "invalid": True,
                                        "invalid_reason": "profile_state_path_mismatch",
                                        "ambiguous": False,
                                        "overwrite_requires_confirmation": True,
                                        "state_file": str(
                                            indexed_path.relative_to(self.project_root)
                                        ).replace("\\", "/"),
                                        "source": "privyhub_game_slot_index",
                                    }
                            stat = (
                                indexed_path.stat()
                            )
                            if stat.st_size <= 0:
                                return {
                                    **base,
                                    "exists": False,
                                    "invalid": True,
                                    "invalid_reason": "zero_byte_state",
                                    "ambiguous": False,
                                    "size_bytes": 0,
                                    "modified_unix_ms": int(
                                        stat.st_mtime
                                        * 1000
                                    ),
                                    "state_file": str(
                                        indexed_path.relative_to(
                                            self.project_root
                                        )
                                    ).replace(
                                        "\\",
                                        "/",
                                    ),
                                    "source": (
                                        "privyhub_game_slot_index"
                                    ),
                                }
                            return {
                                **base,
                                "exists": True,
                                "ambiguous": False,
                                "size_bytes": int(
                                    stat.st_size
                                ),
                                "modified_unix_ms": int(
                                    stat.st_mtime
                                    * 1000
                                ),
                                "state_file": str(
                                    indexed_path.relative_to(
                                        self.project_root
                                    )
                                ).replace(
                                    "\\",
                                    "/",
                                ),
                                "source": (
                                    "privyhub_game_slot_index"
                                ),
                            }
                        except (
                            EmulatorError,
                            OSError,
                            ValueError,
                        ):
                            pass

        stem = (
            self._active_state_stem()
        )
        candidates = (
            self._find_state_files(
                f"{stem}.state{normalized}"
            )
        )

        if not candidates:
            return {
                **base,
                "exists": False,
                "ambiguous": False,
                "source": "legacy_discovery",
            }

        if len(candidates) != 1:
            return {
                **base,
                "exists": True,
                "ambiguous": True,
                "match_count": len(
                    candidates
                ),
                "source": "legacy_discovery",
            }

        path = candidates[0]
        try:
            stat = path.stat()
        except OSError as exc:
            return {
                **base,
                "exists": True,
                "ambiguous": False,
                "error": str(exc),
                "source": "legacy_discovery",
            }

        if stat.st_size <= 0:
            return {
                **base,
                "exists": False,
                "invalid": True,
                "invalid_reason": "zero_byte_state",
                "ambiguous": False,
                "size_bytes": 0,
                "modified_unix_ms": int(
                    stat.st_mtime
                    * 1000
                ),
                "state_file": str(
                    path.relative_to(
                        self.project_root
                    )
                ).replace("\\", "/"),
                "source": "legacy_discovery",
            }

        return {
            **base,
            "exists": True,
            "ambiguous": False,
            "size_bytes": int(
                stat.st_size
            ),
            "modified_unix_ms": int(
                stat.st_mtime
                * 1000
            ),
            "state_file": str(
                path.relative_to(
                    self.project_root
                )
            ).replace("\\", "/"),
            "source": "legacy_discovery",
        }

    def _save_state_slot_details(
        self,
    ) -> list[dict[str, Any]]:
        details = [
            self._save_state_slot_detail(slot)
            for slot in self.SAVE_STATE_SLOTS
        ]
        if isinstance(self._active_cheat_session, dict):
            for item in details:
                item["overwrite_requires_confirmation"] = bool(
                    item.get("exists")
                    or item.get("invalid")
                    or item.get("ambiguous")
                )
        return details

    @staticmethod
    def _copy_state_file(
        source: Path,
        destination: Path,
    ) -> None:
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        destination.write_bytes(
            source.read_bytes()
        )

    # PrivyHub A2/A3 patch 03: verified paused game-session lifecycle.
    def pause(self) -> dict[str, Any]:
        with self.lock:
            self._refresh_process()
            if self.process is None or self.process.poll() is not None:
                raise EmulatorError(
                    "No PrivyHub game session is running"
                )

            observed = self._retroarch_network_status()

            if observed != "PAUSED":
                self._retroarch_network_request(
                    "PAUSE_TOGGLE",
                    expect_response=False,
                )
                observed = self._wait_for_retroarch_state(
                        "PAUSED"
                    )

            self._paused = True
            payload = self.status()
            payload["action"] = "pause"
            payload["paused"] = True
            payload["retroarch_state"] = observed
            self.record_save_state_probe_event(
                "lifecycle",
                action="pause",
                retroarch_state=observed,
                pid=(
                    self.process.pid
                    if self.process is not None
                    else None
                ),
            )
            return payload

    def resume(self) -> dict[str, Any]:
        with self.lock:
            self._refresh_process()
            if self.process is None or self.process.poll() is not None:
                raise EmulatorError(
                    "No PrivyHub game session is running"
                )

            observed = self._retroarch_network_status()

            if observed != "PLAYING":
                self._retroarch_network_request(
                    "PAUSE_TOGGLE",
                    expect_response=False,
                )
                observed = self._wait_for_retroarch_state(
                        "PLAYING"
                    )

            self._paused = False
            payload = self.status()
            payload["action"] = "resume"
            payload["paused"] = False
            payload["retroarch_state"] = observed
            self.record_save_state_probe_event(
                "lifecycle",
                action="resume",
                retroarch_state=observed,
                pid=(
                    self.process.pid
                    if self.process is not None
                    else None
                ),
            )
            return payload

    def save_state(
        self,
        slot: int,
        *,
        replace: bool = False,
    ) -> dict[str, Any]:
        with self.lock:
            normalized = self._normalize_save_state_slot(
                slot
            )
            replacing_existing = False
            if isinstance(self._active_cheat_session, dict):
                existing_detail = self._save_state_slot_detail(normalized)
                replacing_existing = bool(
                    existing_detail.get("exists")
                    or existing_detail.get("invalid")
                    or existing_detail.get("ambiguous")
                )
                if replacing_existing and not bool(replace):
                    raise EmulatorError(
                        f"Profile save Slot {normalized} is already occupied; "
                        "explicit replacement confirmation is required"
                    )
            stem = self._active_state_stem()
            before = self._save_state_probe_snapshot()
            log_offset = (
                self._retroarch_session_log_position()
            )

            self.record_save_state_probe_event(
                "manager_action",
                action="save_state_nightly_direct",
                slot=normalized,
                state_files_before=before,
                game=(
                    dict(self.active_game)
                    if isinstance(
                        self.active_game,
                        dict,
                    )
                    else None
                ),
            )

            command_response = (
                self._retroarch_network_request(
                    "SAVE_STATE_SLOT 0",
                    expect_response=True,
                    timeout=2.0,
                    retries=1,
                )
            )

            if (
                not command_response
                or not command_response.upper().startswith(
                    "SAVE_STATE_SLOT 0"
                )
            ):
                self.record_save_state_probe_event(
                    "save_state_failure",
                    slot=normalized,
                    reason="direct_command_not_acknowledged",
                    retroarch_response=command_response,
                    retroarch_log=(
                        self._retroarch_session_log_since(
                            log_offset
                        )
                    ),
                )
                raise EmulatorError(
                    "RetroArch nightly did not acknowledge "
                    "SAVE_STATE_SLOT 0"
                )

            # The direct action may queue an asynchronous save task. Observe the
            # slot-0 artifact, then wait until it is non-zero and stable before
            # copying it into a PrivyHub slot.
            deadline = time.monotonic() + 5.0
            matching: list[dict[str, Any]] = []
            changes: dict[str, list[dict[str, Any]]] = {
                "created": [],
                "modified": [],
                "removed": [],
            }
            wanted_name = (
                stem + ".state"
            ).casefold()

            while time.monotonic() < deadline:
                time.sleep(0.05)
                after = self._save_state_probe_snapshot()
                changes = self._save_state_probe_diff(
                    before,
                    after,
                )
                matching = [
                    item
                    for item in (
                        changes["created"]
                        + changes["modified"]
                    )
                    if Path(
                        str(item.get("path", ""))
                    ).name.casefold() == wanted_name
                ]
                if matching:
                    break

            if len(matching) != 1:
                self.record_save_state_probe_event(
                    "save_state_failure",
                    slot=normalized,
                    reason="slot0_not_created_or_modified",
                    changes=changes,
                    matching_slot0_changes=matching,
                    retroarch_response=command_response,
                    retroarch_log=(
                        self._retroarch_session_log_since(
                            log_offset
                        )
                    ),
                )
                raise EmulatorError(
                    "RetroArch did not create or update the slot-0 "
                    "savestate after SAVE_STATE_SLOT 0"
                )

            relative = Path(
                str(matching[0]["path"])
            )
            source = (
                self._state_root()
                / relative
            )

            source_diag = (
                self._wait_for_nonzero_stable_state(
                    source,
                    timeout=5.0,
                )
            )
            source_size = int(
                source_diag.get(
                    "size_bytes",
                    0,
                )
                or 0
            )

            if source_size <= 0:
                self.record_save_state_probe_event(
                    "save_state_failure",
                    slot=normalized,
                    reason="zero_byte_slot0",
                    changes=changes,
                    source=source_diag,
                    retroarch_response=command_response,
                    retroarch_log=(
                        self._retroarch_session_log_since(
                            log_offset
                        )
                    ),
                )
                raise EmulatorError(
                    "RetroArch produced an empty 0-byte savestate; "
                    "the save was rejected and was not indexed"
                )

            destination = source.with_name(
                source.name + str(normalized)
            )
            self._copy_state_file(
                source,
                destination,
            )

            source_png = Path(
                str(source) + ".png"
            )
            destination_png = Path(
                str(destination) + ".png"
            )
            if source_png.is_file():
                self._copy_state_file(
                    source_png,
                    destination_png,
                )
            elif replacing_existing and destination_png.exists():
                try:
                    destination_png.unlink()
                except OSError as exc:
                    raise EmulatorError(
                        f"Unable to remove stale replaced savestate preview: {exc}"
                    ) from exc

            destination_diag = (
                self._state_file_diagnostic(
                    destination
                )
            )

            if (
                int(
                    destination_diag.get(
                        "size_bytes",
                        0,
                    )
                    or 0
                )
                <= 0
                or destination_diag.get(
                    "sha256"
                )
                != source_diag.get(
                    "sha256"
                )
            ):
                self.record_save_state_probe_event(
                    "save_state_failure",
                    slot=normalized,
                    reason="slot_copy_verification_failed",
                    source=source_diag,
                    destination=destination_diag,
                    retroarch_response=command_response,
                    retroarch_log=(
                        self._retroarch_session_log_since(
                            log_offset
                        )
                    ),
                )
                raise EmulatorError(
                    "PrivyHub could not verify the copied savestate"
                )

            self.record_save_state_probe_event(
                "save_state_observation",
                slot=normalized,
                changes=changes,
                matching_slot0_changes=matching,
                state_file_observed=True,
                control=(
                    "retroarch_nightly_save_state_slot"
                ),
                source=source_diag,
                destination=destination_diag,
                retroarch_response=command_response,
                retroarch_log=(
                    self._retroarch_session_log_since(
                        log_offset
                    )
                ),
            )

            self._record_state_slot_index(
                normalized,
                destination,
            )

            payload = self.status()
            payload["action"] = "save_state"
            payload["slot"] = normalized
            payload["accepted"] = True
            payload["confirmed"] = True
            payload["replaced_existing"] = bool(replacing_existing)
            payload["overwrite_requires_confirmation"] = False
            payload["control"] = (
                "retroarch_nightly_save_state_slot"
            )
            payload["retroarch_response"] = (
                command_response
            )
            payload["slot_detail"] = (
                self._save_state_slot_detail(
                    normalized
                )
            )
            payload["state_file"] = str(
                destination.relative_to(
                    self.project_root
                )
            ).replace("\\", "/")
            return payload

    # PrivyHub A2/A3 patch 07: nightly live-state load
    def load_state(
        self,
        slot: int,
    ) -> dict[str, Any]:
        with self.lock:
            normalized = (
                self._normalize_save_state_slot(
                    slot
                )
            )

            self._refresh_process()
            if (
                self.process is None
                or self.process.poll()
                is not None
                or self.active_game
                is None
            ):
                raise EmulatorError(
                    "No active game session is available to load"
                )

            if not self._paused:
                raise EmulatorError(
                    "Load State requires the game to be paused"
                )

            detail = (
                self._save_state_slot_detail(
                    normalized
                )
            )

            if detail.get(
                "invalid",
                False,
            ):
                self.record_save_state_probe_event(
                    "load_state_failure",
                    slot=normalized,
                    reason=detail.get(
                        "invalid_reason",
                        "invalid_slot",
                    ),
                    slot_detail=detail,
                )
                raise EmulatorError(
                    f"Slot {normalized} contains an invalid "
                    "0-byte savestate; create a new save"
                )

            if not detail.get(
                "exists",
                False,
            ):
                raise EmulatorError(
                    f"No save state exists in Slot {normalized}"
                )

            if detail.get(
                "ambiguous",
                False,
            ):
                raise EmulatorError(
                    f"Multiple save-state files match Slot {normalized}; "
                    "refusing an ambiguous load"
                )

            relative = str(
                detail.get(
                    "state_file",
                    "",
                )
            ).strip()
            if not relative:
                raise EmulatorError(
                    f"Slot {normalized} has no indexed state file"
                )

            source = (
                self._project_path(
                    relative,
                    must_exist=True,
                )
            )
            source_diag = (
                self._state_file_diagnostic(
                    source
                )
            )

            if (
                int(
                    source_diag.get(
                        "size_bytes",
                        0,
                    )
                    or 0
                )
                <= 0
            ):
                self.record_save_state_probe_event(
                    "load_state_failure",
                    slot=normalized,
                    reason="zero_byte_source",
                    source=source_diag,
                )
                raise EmulatorError(
                    f"Slot {normalized} contains an invalid "
                    "0-byte savestate; create a new save"
                )

            stem = (
                self._active_state_stem()
            )
            scratch = source.with_name(
                f"{stem}.state"
            )

            self._copy_state_file(
                source,
                scratch,
            )
            scratch_diag = (
                self._state_file_diagnostic(
                    scratch
                )
            )

            if (
                scratch_diag.get(
                    "sha256"
                )
                != source_diag.get(
                    "sha256"
                )
                or int(
                    scratch_diag.get(
                        "size_bytes",
                        0,
                    )
                    or 0
                )
                <= 0
            ):
                self.record_save_state_probe_event(
                    "load_state_failure",
                    slot=normalized,
                    reason="slot0_staging_verification_failed",
                    source=source_diag,
                    scratch=scratch_diag,
                )
                raise EmulatorError(
                    "PrivyHub could not verify the staged slot-0 savestate"
                )

            source_png = Path(
                str(source)
                + ".png"
            )
            scratch_png = Path(
                str(scratch)
                + ".png"
            )
            if source_png.is_file():
                self._copy_state_file(
                    source_png,
                    scratch_png,
                )

            log_offset = (
                self._retroarch_session_log_position()
            )

            self.record_save_state_probe_event(
                "manager_action",
                action="load_state_nightly_direct",
                slot=normalized,
                source=source_diag,
                scratch=scratch_diag,
            )

            response = (
                self._retroarch_network_request(
                    "LOAD_STATE_SLOT 0",
                    expect_response=True,
                    timeout=2.0,
                    retries=1,
                )
            )

            if (
                not response
                or not response.upper().startswith(
                    "LOAD_STATE_SLOT 0"
                )
            ):
                self.record_save_state_probe_event(
                    "load_state_failure",
                    slot=normalized,
                    reason="direct_command_not_acknowledged",
                    source=source_diag,
                    scratch=scratch_diag,
                    retroarch_response=response,
                    retroarch_log=(
                        self._retroarch_session_log_since(
                            log_offset
                        )
                    ),
                )
                raise EmulatorError(
                    "RetroArch nightly did not acknowledge "
                    "LOAD_STATE_SLOT 0"
                )

            time.sleep(
                0.30
            )

            state_log = (
                self._retroarch_session_log_since(
                    log_offset
                )
            )
            failed_lines = [
                line
                for line in state_log
                if "failed to load state"
                in line.casefold()
            ]

            if failed_lines:
                self.record_save_state_probe_event(
                    "load_state_failure",
                    slot=normalized,
                    reason="retroarch_rejected_state",
                    source=source_diag,
                    scratch=scratch_diag,
                    retroarch_response=response,
                    retroarch_log=state_log,
                )
                raise EmulatorError(
                    "RetroArch reported Failed to load state"
                )

            observed = (
                self._retroarch_network_status()
            )

            if observed != "PAUSED":
                self._paused = False
                pause_result = self.pause()
                observed = str(
                    pause_result.get(
                        "retroarch_state",
                        "",
                    )
                ).upper()

            if observed != "PAUSED":
                raise EmulatorError(
                    "RetroArch did not return to PAUSED after "
                    "the load-state action"
                )

            self._paused = True

            success_lines = [
                line
                for line in state_log
                if (
                    "[State]" in line
                    and "loaded"
                    in line.casefold()
                    and "failed"
                    not in line.casefold()
                )
            ]

            self.record_save_state_probe_event(
                "load_state_observation",
                slot=normalized,
                source=source_diag,
                scratch=scratch_diag,
                process_alive=True,
                control=(
                    "retroarch_nightly_load_state_slot"
                ),
                response=response,
                retroarch_state=observed,
                retroarch_log=state_log,
                retroarch_success_lines=success_lines,
            )

            payload = self.status()
            payload["action"] = (
                "load_state"
            )
            payload["slot"] = (
                normalized
            )
            payload["accepted"] = True
            payload["confirmed"] = bool(
                success_lines
            )
            payload["verification"] = (
                "retroarch_log"
                if success_lines
                else "visual_required"
            )
            payload["paused"] = True
            payload["control"] = (
                "retroarch_nightly_load_state_slot"
            )
            payload["retroarch_response"] = (
                response
            )
            payload["slot_detail"] = (
                self._save_state_slot_detail(
                    normalized
                )
            )
            payload["state_file"] = (
                relative
            )
            return payload


    @staticmethod
    def _request_graceful_frontend_close(
        process: subprocess.Popen[Any],
    ) -> str:
        if process.poll() is not None:
            return "already_exited"

        if os.name != "nt":
            process.terminate()
            return "sigterm"

        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL(
                "user32",
                use_last_error=True,
            )
            WM_CLOSE = 0x0010
            target_pid = int(process.pid)
            posted = 0

            callback_type = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HWND,
                wintypes.LPARAM,
            )

            user32.EnumWindows.argtypes = [
                callback_type,
                wintypes.LPARAM,
            ]
            user32.EnumWindows.restype = wintypes.BOOL
            user32.GetWindowThreadProcessId.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(wintypes.DWORD),
            ]
            user32.GetWindowThreadProcessId.restype = wintypes.DWORD
            user32.PostMessageW.argtypes = [
                wintypes.HWND,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPARAM,
            ]
            user32.PostMessageW.restype = wintypes.BOOL

            @callback_type
            def visit_window(
                hwnd: int,
                _lparam: int,
            ) -> bool:
                nonlocal posted
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(
                    hwnd,
                    ctypes.byref(pid),
                )
                if int(pid.value) == target_pid:
                    if user32.PostMessageW(
                        hwnd,
                        WM_CLOSE,
                        0,
                        0,
                    ):
                        posted += 1
                return True

            user32.EnumWindows(
                visit_window,
                0,
            )

            if posted <= 0:
                raise EmulatorError(
                    "No RetroArch window accepted WM_CLOSE"
                )

            return f"wm_close:{posted}"

        except EmulatorError:
            raise
        except Exception as exc:
            raise EmulatorError(
                f"Unable to request graceful RetroArch window close: {exc}"
            ) from exc

    @staticmethod
    def _force_stop_process(
        process: subprocess.Popen[Any],
    ) -> None:
        if process.poll() is not None:
            return

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
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

    # PrivyHub A2/A3 patch 10: self-diagnosing savestate control
    # One fresh per-launch trace now covers lifecycle, NCI, file evidence,
    # RetroArch state-loader output, and save/load verification.
    SAVE_STATE_PROBE_VERSION = "a2_a3_game_session_trace_v0.2"
    SAVE_STATE_PROBE_RELATIVE = "logs/games/save_state_probe.txt"

    def _save_state_probe_path(self) -> Path:
        return self._project_path(
            self.SAVE_STATE_PROBE_RELATIVE
        )

    def _save_state_probe_config_lines(
        self,
        path: Path,
    ) -> list[str]:
        if not path.is_file():
            return ["<missing>"]

        patterns = (
            "stdin_cmd_enable",
            "network_cmd_enable",
            "network_cmd_port",
            "input_joypad_driver",
            "input_enable_hotkey",
            "input_save_state",
            "input_load_state",
            "savefile_directory",
            "savestate_directory",
            "sort_savestates",
            "cheat_database_path",
        )
        try:
            return [
                line.strip()
                for line in path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).splitlines()
                if any(
                    pattern in line.casefold()
                    for pattern in patterns
                )
            ]
        except OSError as exc:
            return [f"<read error: {exc}>"]

    def _save_state_probe_snapshot(self) -> list[dict[str, Any]]:
        root = self._state_root()
        if not root.is_dir():
            return []

        rows: list[dict[str, Any]] = []
        try:
            for path in sorted(root.rglob("*")):
                if not path.is_file():
                    continue
                try:
                    stat = path.stat()
                except OSError:
                    continue
                rows.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "size": int(stat.st_size),
                        "mtime_ns": int(stat.st_mtime_ns),
                    }
                )
        except OSError:
            return rows
        return rows

    @staticmethod
    def _save_state_probe_diff(
        before: list[dict[str, Any]],
        after: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        before_map = {
            str(item.get("path")): item
            for item in before
        }
        after_map = {
            str(item.get("path")): item
            for item in after
        }
        created = [
            after_map[path]
            for path in sorted(after_map.keys() - before_map.keys())
        ]
        removed = [
            before_map[path]
            for path in sorted(before_map.keys() - after_map.keys())
        ]
        modified = [
            after_map[path]
            for path in sorted(after_map.keys() & before_map.keys())
            if (
                after_map[path].get("size") != before_map[path].get("size")
                or after_map[path].get("mtime_ns") != before_map[path].get("mtime_ns")
            )
        ]
        return {
            "created": created,
            "modified": modified,
            "removed": removed,
        }

    def _state_file_diagnostic(
        self,
        path: Path,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": str(path),
            "exists": path.is_file(),
        }

        if not path.is_file():
            return result

        try:
            stat = path.stat()
            result["size_bytes"] = int(
                stat.st_size
            )
            result["mtime_ns"] = int(
                stat.st_mtime_ns
            )
            if stat.st_size > 0:
                digest = hashlib.sha256()
                with path.open("rb") as handle:
                    while True:
                        chunk = handle.read(
                            1024 * 1024
                        )
                        if not chunk:
                            break
                        digest.update(
                            chunk
                        )
                result["sha256"] = (
                    digest.hexdigest().upper()
                )
            else:
                result["sha256"] = None
        except OSError as exc:
            result["error"] = str(exc)

        try:
            result["project_relative"] = str(
                path.resolve().relative_to(
                    self.project_root
                )
            ).replace("\\", "/")
        except (
            OSError,
            ValueError,
        ):
            pass

        return result

    def _wait_for_nonzero_stable_state(
        self,
        path: Path,
        *,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + max(
            0.25,
            float(timeout),
        )
        previous: tuple[int, int] | None = None
        stable_hits = 0
        last = self._state_file_diagnostic(
            path
        )

        while time.monotonic() < deadline:
            last = self._state_file_diagnostic(
                path
            )
            size = int(
                last.get(
                    "size_bytes",
                    0,
                )
                or 0
            )
            mtime_ns = int(
                last.get(
                    "mtime_ns",
                    0,
                )
                or 0
            )

            if size > 0:
                current = (
                    size,
                    mtime_ns,
                )
                if current == previous:
                    stable_hits += 1
                else:
                    stable_hits = 0
                    previous = current

                if stable_hits >= 2:
                    return last
            else:
                previous = None
                stable_hits = 0

            time.sleep(
                0.05
            )

        return last

    def _retroarch_session_log_position(
        self,
    ) -> int:
        try:
            if self.log_handle is None:
                return 0
            self.log_handle.flush()
            name = getattr(
                self.log_handle,
                "name",
                "",
            )
            if not name:
                return 0
            return int(
                Path(name).stat().st_size
            )
        except (
            OSError,
            ValueError,
        ):
            return 0

    def _retroarch_session_log_since(
        self,
        offset: int,
    ) -> list[str]:
        try:
            if self.log_handle is None:
                return []
            self.log_handle.flush()
            name = getattr(
                self.log_handle,
                "name",
                "",
            )
            if not name:
                return []

            path = Path(
                str(name)
            )
            with path.open(
                "rb"
            ) as handle:
                handle.seek(
                    max(
                        0,
                        int(offset),
                    )
                )
                text = handle.read(
                    256 * 1024
                ).decode(
                    "utf-8",
                    errors="replace",
                )

            interesting = (
                "[State]",
                "[Command]",
                "[Cheats]",
                "savestate",
                "serialize",
                "unserialize",
                "ERROR",
                "WARN",
            )
            lines = [
                line.strip()
                for line in text.splitlines()
                if any(
                    token.casefold()
                    in line.casefold()
                    for token in interesting
                )
            ]
            return lines[-160:]
        except (
            OSError,
            ValueError,
        ):
            return []

    def record_save_state_probe_event(
        self,
        event: str,
        **fields: Any,
    ) -> None:
        try:
            path = self._save_state_probe_path()
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            record: dict[str, Any] = {
                "probe": self.SAVE_STATE_PROBE_VERSION,
                "time_unix": time.time(),
                "event": event,
            }
            record.update(fields)
            with path.open(
                "a",
                encoding="utf-8",
                buffering=1,
            ) as handle:
                handle.write(
                    json.dumps(
                        record,
                        sort_keys=True,
                        default=str,
                    )
                    + "\n"
                )
        except Exception:
            # The diagnostic path must never destabilize game control.
            pass

    def _reset_save_state_probe(
        self,
        *,
        game: dict[str, Any],
        command: list[str],
        retroarch_config: Path,
        input_override: Path,
        session_log: Path,
        process: subprocess.Popen[Any],
    ) -> None:
        path = self._save_state_probe_path()
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text("", encoding="utf-8")
        self.record_save_state_probe_event(
            "launch",
            game_id=game.get("id"),
            title=game.get("title"),
            system=game.get("system"),
            pid=process.pid,
            command=command,
            base_config=str(retroarch_config),
            append_config=str(input_override),
            session_log=str(session_log),
            base_config_lines=self._save_state_probe_config_lines(
                retroarch_config
            ),
            append_config_lines=self._save_state_probe_config_lines(
                input_override
            ),
            state_files=self._save_state_probe_snapshot(),
        )


    def stop(self) -> dict[str, Any]:
        with self.lock:
            self._refresh_process()

            if self.process is None:
                payload = self.status()
                payload["action"] = "stop"
                payload["stopped"] = False
                payload["graceful"] = True
                payload["save_flush_confirmed"] = True
                return payload

            process = self.process
            active_cheat_session = (
                dict(self._active_cheat_session)
                if isinstance(self._active_cheat_session, dict)
                else None
            )
            cheat_runtime_cleanup = (
                active_cheat_session is not None
                and active_cheat_session.get("session_kind", "cheat") == "cheat"
            )
            save_flush_response = ""
            close_method = ""
            close_requested = False
            network_quit_fallback = False
            forced = False

            try:
                response = self._retroarch_network_request(
                    "SAVE_FILES",
                    expect_response=True,
                    timeout=0.75,
                    retries=3,
                )
                save_flush_response = (
                    response or ""
                ).strip()
            except EmulatorError as exc:
                save_flush_response = (
                    "ERROR: " + str(exc)
                )

            try:
                close_method = self._request_graceful_frontend_close(
                    process
                )
                close_requested = True
                self._record_retroarch_command(
                    "frontend_close_requested",
                    method=close_method,
                    pid=process.pid,
                    save_flush_response=save_flush_response,
                )
            except EmulatorError as exc:
                close_method = "ERROR: " + str(exc)
                self._record_retroarch_command(
                    "frontend_close_failed",
                    error=str(exc),
                    pid=process.pid,
                    save_flush_response=save_flush_response,
                )

            if close_requested:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass

            if process.poll() is None:
                # RetroArch's simple network QUIT command is only a one-frame
                # virtual input pulse, so it is a fallback rather than the
                # primary shutdown path.
                for _ in range(3):
                    try:
                        self._retroarch_network_request(
                            "QUIT",
                            expect_response=False,
                            retries=1,
                        )
                        network_quit_fallback = True
                    except EmulatorError:
                        break
                    try:
                        process.wait(timeout=0.75)
                        break
                    except subprocess.TimeoutExpired:
                        continue

            if process.poll() is None:
                forced = True
                self._force_stop_process(
                    process
                )

            self._record_retroarch_command(
                "frontend_close_result",
                pid=process.pid,
                method=close_method,
                close_requested=close_requested,
                network_quit_fallback=network_quit_fallback,
                forced=forced,
                returncode=process.poll(),
                save_flush_response=save_flush_response,
            )
            self.record_save_state_probe_event(
                "lifecycle",
                action="stop",
                pid=process.pid,
                graceful=(not forced),
                close_method=close_method,
                network_quit_fallback=network_quit_fallback,
                save_flush_response=save_flush_response,
                state_files=self._save_state_probe_snapshot(),
            )

            self._close_quietly(
                process.stdin
            )
            self._close_quietly(
                self.log_handle
            )
            self.process = None
            self.log_handle = None
            self.active_game = None
            self.started_at = None
            self._paused = False
            self._network_cmd_port = None
            self._active_cheat_session = None

            if cheat_runtime_cleanup:
                cleanup_error = self._cleanup_cheat_runtime()
                if cleanup_error:
                    self.record_save_state_probe_event(
                        "a7_3_cheat_runtime_cleanup_error",
                        error=cleanup_error,
                    )

            payload = self.status()
            payload["action"] = "stop"
            payload["stopped"] = True
            payload["graceful"] = not forced
            payload["frontend_close_requested"] = close_requested
            payload["frontend_close_method"] = close_method
            payload["network_quit_fallback"] = network_quit_fallback
            payload["save_flush_requested"] = True
            payload["save_flush_confirmed"] = (
                save_flush_response.upper() == "OK"
            )
            payload["save_flush_response"] = save_flush_response
            payload["control"] = "retroarch_network_direct_slot"
            return payload
