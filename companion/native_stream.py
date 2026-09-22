from __future__ import annotations

import ctypes
import ipaddress
import json
import os
import sys
import shutil
import subprocess
import threading
import time

from pathlib import Path
from typing import Any

from ctypes import wintypes

from native_session_io import NativeSessionIO
from native_fec_relay import NativeVideoFecRelay

# Encoder knobs read from the environment at command build time.
#
#   PRIVYHUB_ENC_MAX_FRAME_SIZE  bytes, `h264_vaapi -max_frame_size`.
#     **D-BASE-P6a: no longer a diagnostic default-off knob.** The cap is
#     now a PROFILE field (`max_frame_size_bytes`, 90,000 on the reference
#     profile) and this variable OVERRIDES it. Setting it to **0 runs
#     uncapped** -- the argv omits the flag -- which is how the D-BASE-P6
#     baseline arm is re-run for comparison. Unset means "use the profile".
#   PRIVYHUB_ENC_BUFSIZE_K       kbit, overrides `-bufsize` (VBV depth).
#     Still diagnostic and still default off (D-BASE-P6 measured it and it
#     was NOT adopted: 3x the loss of the cap).
ENC_MAX_FRAME_SIZE_ENV = "PRIVYHUB_ENC_MAX_FRAME_SIZE"
ENC_BUFSIZE_K_ENV = "PRIVYHUB_ENC_BUFSIZE_K"
from games import host_resource_sampling
from native_host_telemetry import NativeHostTelemetryProfiler
from native_stream_profiles import NATIVE_GAME_720P60_REFERENCE


class NativeStreamError(RuntimeError):
    pass


class NativeStreamManager:
    """PrivyHub Native A/V/Input Alpha host.

    v0.4 replaces GDI window capture with Windows Graphics Capture while
    deliberately retaining FFmpeg/NVENC and RTP as temporary encoder/transport
    scaffolding.

    The Android client never supplies a process, executable path, window title,
    or HWND. PrivyHub derives the exact RetroArch HWND from its managed runtime.
    """

    ALPHA_VERSION = "0.7"

    PROFILE = NATIVE_GAME_720P60_REFERENCE
    WIDTH = PROFILE.width
    HEIGHT = PROFILE.height
    FPS = PROFILE.fps
    GOP_FRAMES = PROFILE.gop_frames
    BITRATE_KBPS = PROFILE.bitrate_kbps
    MAX_BITRATE_KBPS = PROFILE.max_bitrate_kbps
    BFRAMES = PROFILE.bframes
    PAYLOAD_TYPE = 96
    DEFAULT_PORT = 48100
    FEC_INPUT_PORT = 48110
    FEC_GROUP_SIZE = PROFILE.fec_group_size
    AUDIO_PORT = 48101
    INPUT_PORT = 48102

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.data_dir = self.project_root / "data" / "games" / "native_stream"
        self.log_dir = self.project_root / "logs" / "games"
        self.log_path = self.log_dir / "native_video_alpha.log"

        self._lock = threading.RLock()
        self._process: subprocess.Popen[Any] | None = None
        self._capture_process: subprocess.Popen[Any] | None = None
        self._log_handle = None
        self._client_port: int | None = None
        self._active_bitrate_kbps = self.BITRATE_KBPS
        self._capture_target: dict[str, Any] | None = None
        self._encoder_command: list[str] | None = None
        self._last_capture_target: dict[str, Any] | None = None
        self._session_io = NativeSessionIO(
            self.project_root
        )
        self._fec_relay = NativeVideoFecRelay(
            local_port=self.FEC_INPUT_PORT,
            group_size=self.FEC_GROUP_SIZE,
            # D-BASE-P5: one JSON line per second of streaming, rotated
            # into the same `stream_log_archive/` the heartbeat log uses,
            # so the existing retention family bounds it.
            frame_size_log=(
                self.log_dir / "native_frame_sizes.jsonl"
            ),
        )
        self._host_telemetry = NativeHostTelemetryProfiler(
            self.project_root
        )

    @staticmethod
    def _env_int(name: str) -> int:
        """A positive integer from the environment, or 0 for 'not set'.

        Anything unparseable reads as not set rather than raising: a
        malformed diagnostic knob must not stop a stream from starting.
        """

        try:
            value = int(str(os.environ.get(name, "")).strip() or 0)
        except (TypeError, ValueError):
            return 0

        return value if value > 0 else 0

    def _log_line(self, message: str) -> None:
        """One line into the native video host log, if it is open.

        Used for the few notices that belong with the encoder's own output
        rather than in a status field. Never raises: a log that cannot be
        written must not stop a stream starting.
        """

        handle = self._log_handle

        if handle is None:
            return

        try:
            handle.write(message.rstrip("\n") + "\n")
            handle.flush()
        except Exception:
            pass

    @staticmethod
    def _env_int_or_none(name: str) -> int | None:
        """The same, but **0 is a value, not an absence**.

        `_env_int` cannot express "explicitly zero", and D-BASE-P6a needs
        it to: with the cap in the profile, `PRIVYHUB_ENC_MAX_FRAME_SIZE=0`
        is the documented way to run uncapped for comparison. None means
        the variable is unset or unparseable, i.e. use the profile.
        """

        raw = str(os.environ.get(name, "")).strip()

        if not raw:
            return None

        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None

        return value if value >= 0 else None

    def _effective_max_frame_size(self) -> tuple[int, str]:
        """The cap actually applied, and which source decided it.

        Returns (bytes, source) where 0 bytes means uncapped and source is
        one of "profile", the environment variable's name, or
        "profile (uncapped)".
        """

        override = self._env_int_or_none(ENC_MAX_FRAME_SIZE_ENV)

        if override is not None:
            return override, ENC_MAX_FRAME_SIZE_ENV

        return int(self.PROFILE.max_frame_size_bytes), "profile"

    def encoder_overrides(self) -> dict[str, Any]:
        """Which encoder settings are in force and where each came from.

        **D-BASE-P6a changed what `any_override` means.** The frame cap is
        now a profile default, so the profile being in force is NOT an
        override: `any_override` is false when nothing but the profile and
        the reference bitrate decide the argv. It is true only when an
        environment variable is actually set -- including
        `PRIVYHUB_ENC_MAX_FRAME_SIZE=0`, which overrides the profile to run
        uncapped.
        """

        max_frame_size, mfs_source = self._effective_max_frame_size()
        mfs_override = self._env_int_or_none(ENC_MAX_FRAME_SIZE_ENV)
        bufsize_k = self._env_int(ENC_BUFSIZE_K_ENV)

        return {
            "max_frame_size_bytes": max_frame_size or None,
            "max_frame_size_source": mfs_source,
            "max_frame_size_env": ENC_MAX_FRAME_SIZE_ENV,
            "default_max_frame_size_bytes": int(
                self.PROFILE.max_frame_size_bytes
            ),
            "uncapped": max_frame_size <= 0,
            "bufsize_kbits": bufsize_k or None,
            "bufsize_source": ENC_BUFSIZE_K_ENV,
            "default_bufsize_kbits": self.MAX_BITRATE_KBPS,
            "any_override": bool(
                mfs_override is not None or bufsize_k
            ),
        }

    def fec_frame_size_status(self) -> dict[str, Any]:
        """D-BASE-P5: the relay's frame-size block, including its bounded
        per-second ring. Counting only."""

        return self._fec_relay.frame_size_status()

    def fec_pacing_status(self) -> dict[str, Any]:
        """D-BASE-P3: the relay's pacing block, for the decoder session
        log's host metadata. Diagnostic only; default off."""

        return self._fec_relay.pacing_status()

    def _find_ffmpeg(self) -> Path | None:
        names = (
            self.project_root / "runtime" / "streaming" / "ffmpeg" / "bin" / "ffmpeg.exe",
            self.project_root / "runtime" / "ffmpeg" / "bin" / "ffmpeg.exe",
            self.project_root / "runtime" / "streaming" / "ffmpeg" / "ffmpeg.exe",
        )

        for candidate in names:
            if candidate.is_file():
                return candidate.resolve()

        found = shutil.which("ffmpeg")
        if found:
            return Path(found).resolve()

        return None

    def _wgc_runtime_dir(self) -> Path:
        return (
            self.project_root
            / "runtime"
            / "streaming"
            / "wgc_python"
        )

    def _wgc_bridge_path(self) -> Path:
        return (
            self.project_root
            / "companion"
            / "native_wgc_bridge.py"
        )

    def _wgc_ready(self) -> bool:
        runtime = self._wgc_runtime_dir()

        return (
            self._wgc_bridge_path().is_file()
            and (
                runtime
                / "windows_capture"
            ).is_dir()
        )


    # PrivyHub D-074 Linux native video backend
    @staticmethod
    def _linux_host() -> bool:
        return sys.platform.startswith("linux")

    @staticmethod
    def _linux_display() -> str | None:
        value = os.environ.get("DISPLAY", "").strip()
        return value or None

    @staticmethod
    def _linux_xdotool() -> str | None:
        return shutil.which("xdotool")

    @staticmethod
    def _linux_vaapi_device() -> Path | None:
        render_root = Path("/dev/dri")

        try:
            candidates = sorted(
                render_root.glob("renderD*")
            )
        except OSError:
            return None

        usable = [
            candidate
            for candidate in candidates
            if (
                candidate.exists()
                and os.access(
                    candidate,
                    os.R_OK | os.W_OK,
                )
            )
        ]

        # Fail closed when host GPU selection is ambiguous. Phase D has
        # validated the single-render-node case; a multi-GPU selector is a
        # later capability problem rather than something to guess here.
        if len(usable) != 1:
            return None

        return usable[0].resolve()

    def _running_locked(self) -> bool:
        if (
            self._process is None
            or self._process.poll() is not None
            or not self._fec_relay.running
        ):
            return False

        if os.name == "nt":
            return (
                self._capture_process is not None
                and self._capture_process.poll() is None
            )

        if self._linux_host():
            return self._capture_process is None

        return False

    def _reap_locked(self) -> None:
        ffmpeg_exited = (
            self._process is not None
            and self._process.poll() is not None
        )

        capture_exited = (
            self._capture_process is not None
            and self._capture_process.poll() is not None
        )

        relay_exited = (
            self._process is not None
            and self._process.poll() is None
            and not self._fec_relay.running
        )

        if ffmpeg_exited or capture_exited or relay_exited:
            self._stop_locked()

    # PrivyHub Phase A2 controller-hotkey state bridge
    def retroarch_hotkey(
        self,
        action: str,
    ) -> dict[str, Any]:
        return self._session_io.controller.pulse_retroarch_hotkey(
            action
        )

    # PrivyHub Phase A3 stream pause/resume lifecycle
    def ensure_game_controller(self, client_ip: str) -> dict[str, Any]:
        client_ip = self._validated_ipv4(client_ip)
        try:
            return self._session_io.ensure_controller(client_ip=client_ip, input_port=self.INPUT_PORT)
        except Exception as exc:
            raise NativeStreamError(f"Unable to start persistent game controller: {exc}") from exc

    def end_game_session(self) -> dict[str, Any]:
        with self._lock:
            self._stop_locked()
            self._session_io.stop()
            return self.status()

    def _host_thermal_c(self) -> float | None:
        """Hottest hwmon reading in °C, or None if none is readable.

        Read directly rather than from the sampler's log so `status` is
        answerable whether or not a session — and therefore a sampler — is
        running. Any failure reads as None; this must never raise.
        """

        try:
            sys.path.insert(
                0,
                str(self.project_root / "tools"),
            )
            from host_resource_sampler import (  # noqa: PLC0415
                hottest_c,
                read_hwmon,
            )

            return hottest_c(read_hwmon())
        except Exception:
            return None

    def status(self) -> dict[str, Any]:
        with self._lock:
            self._reap_locked()

            ffmpeg = self._find_ffmpeg()
            wgc_ready = self._wgc_ready()
            active = self._running_locked()

            linux_host = self._linux_host()
            linux_display = (
                self._linux_display()
                if linux_host
                else None
            )
            linux_xdotool = (
                self._linux_xdotool()
                if linux_host
                else None
            )
            linux_vaapi_device = (
                self._linux_vaapi_device()
                if linux_host
                else None
            )

            if os.name == "nt":
                if ffmpeg is None:
                    ready = False
                    message = (
                        "FFmpeg was not found. The project-local "
                        "runtime/streaming/ffmpeg build is required."
                    )
                elif not wgc_ready:
                    ready = False
                    message = (
                        "The project-local Windows Graphics Capture runtime "
                        "is missing. Re-run the v0.4 setup patch."
                    )
                elif active:
                    ready = True
                    message = (
                        f"PrivyHub Native A/V/Input Alpha v{self.ALPHA_VERSION} "
                        "is capturing the managed RetroArch window with "
                        "Windows Graphics Capture using the "
                        f"{self.PROFILE.width}x{self.PROFILE.height} "
                        "reference profile envelope and streaming H.264 RTP/UDP."
                    )
                else:
                    ready = True
                    message = (
                        "Native Performance Alpha v0.6 is ready. Launch a game first, "
                        "then open the native receiver on the onn."
                    )
            elif linux_host:
                if ffmpeg is None:
                    ready = False
                    message = "FFmpeg was not found on the Linux host."
                elif linux_display is None:
                    ready = False
                    message = (
                        "Linux native video requires an active X11 DISPLAY."
                    )
                elif linux_xdotool is None:
                    ready = False
                    message = (
                        "Linux native video requires xdotool for fail-closed "
                        "managed-window discovery."
                    )
                elif linux_vaapi_device is None:
                    ready = False
                    message = (
                        "Linux native video requires exactly one accessible "
                        "DRM render node."
                    )
                elif active:
                    ready = True
                    message = (
                        f"PrivyHub Native Video Alpha v{self.ALPHA_VERSION} "
                        "is capturing the managed RetroArch X11 window and "
                        "streaming VAAPI H.264 through the existing RTP/FEC path."
                    )
                else:
                    ready = True
                    message = (
                        "Linux native video is ready. Audio, controller output, "
                        "and host telemetry remain separate Phase D migration "
                        "surfaces."
                    )
            else:
                ready = False
                message = (
                    "Native streaming is not implemented for this host platform."
                )

            session_io = (
                self._session_io.status()
            )

            return {
                "ok": True,
                "kind": "native_stream_host",
                "alpha_version": self.ALPHA_VERSION,
                "profile_id": self.PROFILE.id,
                "profile": self.PROFILE.to_dict(),
                "title": "Native Streaming Alpha",
                "ready": ready,
                "active": active,
                "managed": active,
                "capture_backend": (
                    "windows_graphics_capture"
                    if os.name == "nt"
                    else (
                        "x11grab_window"
                        if linux_host
                        else "unavailable"
                    )
                ),
                "encoder": (
                    "h264_nvenc"
                    if os.name == "nt"
                    else (
                        "h264_vaapi"
                        if linux_host
                        else "unavailable"
                    )
                ),
                "transport": "rtp_udp_xor_fec",
                # D-BASE-P6: the argv actually used for the running
                # encoder, so an arm can be confirmed before the stream
                # opens rather than inferred. None when nothing is running.
                "encoder_command": list(self._encoder_command or ()) or None,
                "encoder_overrides": self.encoder_overrides(),
                "fec": self._fec_relay.status(),
                # D-BASE-T1: the hottest host sensor, so one `status` call
                # carries both ends' temperatures once the client's arrive
                # in the heartbeat. None when no sensor is readable.
                "host_thermal_c": self._host_thermal_c(),
                "host_resource_sampler": (
                    host_resource_sampling.status()
                ),
                "host_telemetry": self._host_telemetry.status(),
                "fec_enabled": True,
                "fec_group_size": self.FEC_GROUP_SIZE,
                "source_bitrate_kbps": self._active_bitrate_kbps,
                "reference_bitrate_kbps": self.BITRATE_KBPS,
                "width": self.WIDTH,
                "height": self.HEIGHT,
                "fps": self.FPS,
                "gop_frames": self.GOP_FRAMES,
                "bitrate_kbps": self._active_bitrate_kbps,
                "payload_type": self.PAYLOAD_TYPE,
                "video_port": self._client_port,
                "audio_port": self.AUDIO_PORT,
                "input_port": self.INPUT_PORT,
                "audio": session_io["audio"],
                "controller": session_io["controller"],
                "ffmpeg_found": ffmpeg is not None,
                "wgc_runtime_found": wgc_ready,
                "x11_display_found": linux_display is not None,
                "x11_window_tool_found": linux_xdotool is not None,
                "vaapi_render_node_found": linux_vaapi_device is not None,
                "capture_target": self._public_capture_target(
                    self._capture_target
                    or self._last_capture_target
                ),
                "message": message,
            }

    @staticmethod
    def _validated_ipv4(client_ip: str) -> str:
        try:
            address = ipaddress.ip_address(client_ip)
        except ValueError as exc:
            raise NativeStreamError("Invalid client network address") from exc

        if address.version != 4:
            raise NativeStreamError(
                "Native A/V/Input Alpha is IPv4-only for the first benchmark."
            )

        if address.is_unspecified or address.is_multicast:
            raise NativeStreamError("Invalid client network address")

        return str(address)

    @staticmethod
    def _validated_port(port: int) -> int:
        if port < 1024 or port > 65535:
            raise NativeStreamError("Native stream UDP port is out of range")
        return port

    # PrivyHub A2/A3 patch 09: configured RetroArch capture identity
    def _retroarch_executable(self) -> Path:
        config_path = (
            self.project_root
            / "companion"
            / "games"
            / "config"
            / "emulators.json"
        ).resolve()

        try:
            config_path.relative_to(
                self.project_root
            )
        except ValueError as exc:
            raise NativeStreamError(
                "Emulator configuration escaped the project root."
            ) from exc

        try:
            payload = json.loads(
                config_path.read_text(
                    encoding="utf-8-sig"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise NativeStreamError(
                f"Unable to read emulator configuration: {exc}"
            ) from exc

        retroarch = (
            payload.get("retroarch")
            if isinstance(payload, dict)
            else None
        )

        if not isinstance(
            retroarch,
            dict,
        ):
            raise NativeStreamError(
                "Emulator configuration has no RetroArch profile."
            )

        executable_rel = retroarch.get(
            "executable"
        )

        if (
            not isinstance(
                executable_rel,
                str,
            )
            or not executable_rel.strip()
        ):
            raise NativeStreamError(
                "RetroArch executable is not configured."
            )

        candidate = (
            self.project_root
            / executable_rel
        ).resolve()

        try:
            candidate.relative_to(
                self.project_root
            )
        except ValueError as exc:
            raise NativeStreamError(
                "Configured RetroArch executable escaped the project root."
            ) from exc

        return candidate

    @staticmethod
    def _same_windows_path(
        first: str,
        second: Path,
    ) -> bool:
        return os.path.normcase(
            os.path.abspath(first)
        ) == os.path.normcase(
            os.path.abspath(str(second))
        )


    def _find_linux_retroarch_window(
        self,
        managed_process_id: int | None,
    ) -> dict[str, Any] | None:
        if managed_process_id is None:
            return None

        try:
            process_id = int(managed_process_id)
        except (TypeError, ValueError):
            return None

        if process_id <= 0:
            return None

        if not Path(f"/proc/{process_id}").is_dir():
            return None

        xdotool = self._linux_xdotool()
        display = self._linux_display()

        if xdotool is None or display is None:
            return None

        environment = os.environ.copy()
        environment["DISPLAY"] = display

        try:
            search = subprocess.run(
                [
                    xdotool,
                    "search",
                    "--onlyvisible",
                    "--pid",
                    str(process_id),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=1.0,
                env=environment,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None

        if search.returncode not in (0, 1):
            return None

        matches: list[dict[str, Any]] = []

        for raw_window_id in search.stdout.splitlines():
            raw_window_id = raw_window_id.strip()

            if not raw_window_id:
                continue

            try:
                window_id = int(raw_window_id, 10)
            except ValueError:
                continue

            try:
                owner = subprocess.run(
                    [
                        xdotool,
                        "getwindowpid",
                        str(window_id),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=1.0,
                    env=environment,
                )

                if (
                    owner.returncode != 0
                    or int(owner.stdout.strip()) != process_id
                ):
                    continue

                geometry_result = subprocess.run(
                    [
                        xdotool,
                        "getwindowgeometry",
                        "--shell",
                        str(window_id),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=1.0,
                    env=environment,
                )

                if geometry_result.returncode != 0:
                    continue

                geometry: dict[str, str] = {}

                for line in geometry_result.stdout.splitlines():
                    if "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    geometry[key.strip()] = value.strip()

                width = int(geometry.get("WIDTH", "0"))
                height = int(geometry.get("HEIGHT", "0"))

                if width < 64 or height < 64:
                    continue

                title_result = subprocess.run(
                    [
                        xdotool,
                        "getwindowname",
                        str(window_id),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=1.0,
                    env=environment,
                )

                class_result = subprocess.run(
                    [
                        xdotool,
                        "getwindowclassname",
                        str(window_id),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=1.0,
                    env=environment,
                )

                title = (
                    title_result.stdout.strip()
                    if title_result.returncode == 0
                    else ""
                )
                window_class = (
                    class_result.stdout.strip()
                    if class_result.returncode == 0
                    else ""
                )

                matches.append(
                    {
                        "type": "window",
                        "process": "retroarch",
                        "pid": process_id,
                        "title": title,
                        "window_class": window_class,
                        "width": width,
                        "height": height,
                        "_window_id": window_id,
                        "_area": int(width * height),
                    }
                )
            except (
                OSError,
                ValueError,
                subprocess.TimeoutExpired,
            ):
                continue

        if not matches:
            return None

        return max(
            matches,
            key=lambda item: int(item["_area"]),
        )
    def _find_retroarch_window(
        self,
        managed_process_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Return the largest visible top-level window owned by RetroArch.

        Windows preserves the validated executable-path ownership check.
        Linux uses the EmulatorManager-owned PID because an AppImage executable
        resolves through a temporary mount rather than its project path.
        """

        if self._linux_host():
            return self._find_linux_retroarch_window(
                managed_process_id
            )

        if os.name != "nt":
            return None

        expected_exe = self._retroarch_executable()

        if not expected_exe.is_file():
            return None

        user32 = ctypes.WinDLL(
            "user32",
            use_last_error=True,
        )
        kernel32 = ctypes.WinDLL(
            "kernel32",
            use_last_error=True,
        )

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        user32.EnumWindows.argtypes = [
            ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HWND,
                wintypes.LPARAM,
            ),
            wintypes.LPARAM,
        ]
        user32.EnumWindows.restype = wintypes.BOOL

        user32.IsWindowVisible.argtypes = [
            wintypes.HWND,
        ]
        user32.IsWindowVisible.restype = wintypes.BOOL

        user32.IsIconic.argtypes = [
            wintypes.HWND,
        ]
        user32.IsIconic.restype = wintypes.BOOL

        user32.GetWindowTextLengthW.argtypes = [
            wintypes.HWND,
        ]
        user32.GetWindowTextLengthW.restype = ctypes.c_int

        user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        ]
        user32.GetWindowTextW.restype = ctypes.c_int

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

        kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = wintypes.HANDLE

        kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

        kernel32.CloseHandle.argtypes = [
            wintypes.HANDLE,
        ]
        kernel32.CloseHandle.restype = wintypes.BOOL

        matches: list[dict[str, Any]] = []

        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM,
        )

        @callback_type
        def visit_window(
            hwnd: int,
            _lparam: int,
        ) -> bool:
            try:
                if not user32.IsWindowVisible(hwnd):
                    return True

                if user32.IsIconic(hwnd):
                    return True

                title_length = user32.GetWindowTextLengthW(hwnd)

                if title_length <= 0:
                    return True

                title_buffer = ctypes.create_unicode_buffer(
                    title_length + 1
                )

                if (
                    user32.GetWindowTextW(
                        hwnd,
                        title_buffer,
                        len(title_buffer),
                    )
                    <= 0
                ):
                    return True

                process_id = wintypes.DWORD()

                user32.GetWindowThreadProcessId(
                    hwnd,
                    ctypes.byref(process_id),
                )

                if process_id.value <= 0:
                    return True

                process = kernel32.OpenProcess(
                    PROCESS_QUERY_LIMITED_INFORMATION,
                    False,
                    process_id.value,
                )

                if not process:
                    return True

                try:
                    path_buffer = ctypes.create_unicode_buffer(
                        32768
                    )
                    path_length = wintypes.DWORD(
                        len(path_buffer)
                    )

                    if not kernel32.QueryFullProcessImageNameW(
                        process,
                        0,
                        path_buffer,
                        ctypes.byref(path_length),
                    ):
                        return True

                    process_path = path_buffer.value
                finally:
                    kernel32.CloseHandle(process)

                if not self._same_windows_path(
                    process_path,
                    expected_exe,
                ):
                    return True

                client_rect = wintypes.RECT()

                if not user32.GetClientRect(
                    hwnd,
                    ctypes.byref(client_rect),
                ):
                    return True

                width = max(
                    0,
                    client_rect.right - client_rect.left,
                )
                height = max(
                    0,
                    client_rect.bottom - client_rect.top,
                )

                if width < 64 or height < 64:
                    return True

                matches.append(
                    {
                        "type": "window",
                        "process": "retroarch.exe",
                        "pid": int(process_id.value),
                        "title": title_buffer.value,
                        "width": int(width),
                        "height": int(height),
                        "_hwnd": int(hwnd),
                        "_area": int(width * height),
                    }
                )

            except Exception:
                # Window enumeration is best-effort.  One inaccessible helper
                # window must not abort discovery of the actual game window.
                return True

            return True

        if not user32.EnumWindows(
            visit_window,
            0,
        ):
            return None

        if not matches:
            return None

        selected = max(
            matches,
            key=lambda item: int(item["_area"]),
        )

        return selected

    def _select_capture_target(
        self,
        managed_process_id: int | None = None,
    ) -> dict[str, Any]:
        # Fail closed. Native game streaming must never silently broaden from
        # the PrivyHub-owned emulator window to the user's whole desktop.
        deadline = time.monotonic() + 2.0

        while time.monotonic() < deadline:
            window = self._find_retroarch_window(
                managed_process_id
            )

            if window is not None:
                return window

            time.sleep(0.10)

        raise NativeStreamError(
            "No visible window owned by the project-managed RetroArch "
            "session was found. Whole-desktop capture is intentionally "
            "disabled."
        )

    @staticmethod
    def _public_capture_target(
        target: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if target is None:
            return None

        return {
            key: value
            for key, value in target.items()
            if not key.startswith("_")
        }

    def _build_ffmpeg_command(
        self,
        ffmpeg: Path,
        client_ip: str,
        port: int,
        source_width: int,
        source_height: int,
        bitrate_kbps: int | None = None,
        max_bitrate_kbps: int | None = None,
    ) -> list[str]:
        # D-BASE-P6a: the profile's `max_frame_size_bytes` is honoured by
        # the `h264_vaapi` builder only. NVENC has its own rate-control
        # vocabulary and no measurement behind a translation, so this path
        # **ignores the field and says so once** rather than inventing an
        # equivalent. See `decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.
        if int(self.PROFILE.max_frame_size_bytes) > 0:
            self._log_line(
                "h264_nvenc: ignoring profile max_frame_size_bytes="
                f"{int(self.PROFILE.max_frame_size_bytes)} "
                "(honoured by the h264_vaapi path only, D-BASE-P6a)"
            )

        target_bitrate_kbps = (
            self.BITRATE_KBPS
            if bitrate_kbps is None
            else int(bitrate_kbps)
        )
        target_max_bitrate_kbps = (
            self.MAX_BITRATE_KBPS
            if max_bitrate_kbps is None
            else int(max_bitrate_kbps)
        )

        if (
            target_bitrate_kbps <= 0
            or target_max_bitrate_kbps < target_bitrate_kbps
        ):
            raise NativeStreamError(
                "Invalid native-stream encoder bitrate override"
            )

        destination = (
            f"rtp://127.0.0.1:{self.FEC_INPUT_PORT}"
            "?pkt_size=1200"
        )

        video_filter = (
            f"scale={self.WIDTH}:{self.HEIGHT}:"
            "force_original_aspect_ratio=decrease:"
            "flags=fast_bilinear,"
            f"pad={self.WIDTH}:{self.HEIGHT}:"
            "(ow-iw)/2:(oh-ih)/2:black"
        )

        return [
            str(ffmpeg),
            "-hide_banner",
            "-loglevel",
            "info",
            "-nostdin",
            "-f",
            "rawvideo",
            "-pixel_format",
            "bgra",
            "-video_size",
            f"{source_width}x{source_height}",
            "-framerate",
            str(self.FPS),
            "-i",
            "pipe:0",
            "-vf",
            video_filter,
            "-an",
            "-c:v",
            "h264_nvenc",
            "-preset",
            "p1",
            "-tune",
            "ull",
            "-zerolatency",
            "1",
            "-delay",
            "0",
            "-rc-lookahead",
            "0",
            "-rc",
            "cbr",
            "-b:v",
            f"{target_bitrate_kbps}k",
            "-maxrate",
            f"{target_max_bitrate_kbps}k",
            "-bufsize",
            "1000k",
            "-g",
            str(self.GOP_FRAMES),
            "-bf",
            str(self.BFRAMES),
            "-pix_fmt",
            "yuv420p",
            "-payload_type",
            str(self.PAYLOAD_TYPE),
            "-f",
            "rtp",
            destination,
        ]


    def _build_linux_ffmpeg_command(
        self,
        ffmpeg: Path,
        capture_target: dict[str, Any],
        bitrate_kbps: int | None = None,
        max_bitrate_kbps: int | None = None,
    ) -> list[str]:
        target_bitrate_kbps = (
            self.BITRATE_KBPS
            if bitrate_kbps is None
            else int(bitrate_kbps)
        )
        target_max_bitrate_kbps = (
            self.MAX_BITRATE_KBPS
            if max_bitrate_kbps is None
            else int(max_bitrate_kbps)
        )

        if (
            target_bitrate_kbps <= 0
            or target_max_bitrate_kbps < target_bitrate_kbps
        ):
            raise NativeStreamError(
                "Invalid native-stream encoder bitrate override"
            )

        display = self._linux_display()
        vaapi_device = self._linux_vaapi_device()

        try:
            window_id = int(
                capture_target["_window_id"]
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise NativeStreamError(
                "Linux capture target has no valid X11 window ID"
            ) from exc

        if display is None:
            raise NativeStreamError(
                "Linux native video requires an active X11 DISPLAY."
            )

        if vaapi_device is None:
            raise NativeStreamError(
                "Linux native video requires exactly one accessible DRM "
                "render node."
            )

        destination = (
            f"rtp://127.0.0.1:{self.FEC_INPUT_PORT}"
            "?pkt_size=1200"
        )

        video_filter = (
            f"scale={self.WIDTH}:{self.HEIGHT}:"
            "force_original_aspect_ratio=decrease:"
            "flags=fast_bilinear,"
            f"pad={self.WIDTH}:{self.HEIGHT}:"
            "(ow-iw)/2:(oh-ih)/2:black,"
            "format=nv12,hwupload"
        )

        # D-BASE-P6a: the frame cap comes from the PROFILE by default and
        # the environment variable overrides it, including with 0 to run
        # uncapped. `-bufsize` stays a default-off diagnostic knob.
        max_frame_size_bytes, _cap_source = self._effective_max_frame_size()
        bufsize_override_kbits = self._env_int(ENC_BUFSIZE_K_ENV)
        bufsize_kbits = (
            bufsize_override_kbits
            if bufsize_override_kbits > 0
            else target_max_bitrate_kbps
        )

        command = [
            str(ffmpeg),
            "-hide_banner",
            "-loglevel",
            "info",
            "-nostdin",
            "-vaapi_device",
            str(vaapi_device),
            "-f",
            "x11grab",
            "-framerate",
            str(self.FPS),
            "-window_id",
            str(window_id),
            "-i",
            display,
            "-vf",
            video_filter,
            "-an",
            "-c:v",
            "h264_vaapi",
            "-profile:v",
            "high",
            "-b:v",
            f"{target_bitrate_kbps}k",
            "-maxrate",
            f"{target_max_bitrate_kbps}k",
            "-bufsize",
            f"{bufsize_kbits}k",
        ]

        # `h264_vaapi -max_frame_size` caps a single encoded frame in
        # BYTES -- the one knob that acts directly on the tail `D-BASE-P5`
        # found drives the loss and `D-BASE-P6` proved controls it.
        # **Adopted as the profile default by D-BASE-P6a (90,000).** At 0,
        # from the profile or from the override, the argument is absent and
        # the command is byte for byte the pre-P6 one.
        if max_frame_size_bytes > 0:
            command += [
                "-max_frame_size",
                str(max_frame_size_bytes),
            ]

        command += [
            "-g",
            str(self.GOP_FRAMES),
            "-bf",
            str(self.BFRAMES),
            "-payload_type",
            str(self.PAYLOAD_TYPE),
            "-f",
            "rtp",
            destination,
        ]

        return command
    @staticmethod
    def _kill_managed_process(
        process: subprocess.Popen[Any] | None,
    ) -> None:
        if process is None or process.poll() is not None:
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
            try:
                process.terminate()
            except Exception:
                return

        try:
            process.wait(
                timeout=5
            )
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass

    def _tail_log(self, max_chars: int = 3000) -> str:
        try:
            text = self.log_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            return ""

        return text[-max_chars:].strip()

    def _stop_locked(self) -> None:
        # Finalize resource telemetry while the managed processes still exist.
        self._host_telemetry.stop()

        self._session_io.stop_stream()

        ffmpeg = self._process
        capture = self._capture_process

        # Stop the encoder first. That closes its raw-video input reader.
        self._kill_managed_process(
            ffmpeg
        )
        self._kill_managed_process(
            capture
        )

        self._fec_relay.stop()

        self._process = None
        self._capture_process = None
        self._encoder_command = None
        self._client_port = None
        self._active_bitrate_kbps = self.BITRATE_KBPS

        if self._capture_target is not None:
            self._last_capture_target = self._capture_target

        self._capture_target = None

        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass

            self._log_handle = None


    def _start_linux_locked(
        self,
        client_ip: str,
        port: int,
        managed_process_id: int | None,
    ) -> dict[str, Any]:
        if not self._linux_host():
            raise NativeStreamError(
                "Linux native-video backend requested on a non-Linux host."
            )

        try:
            process_id = int(managed_process_id)
        except (TypeError, ValueError) as exc:
            raise NativeStreamError(
                "Linux native video requires the managed RetroArch process ID."
            ) from exc

        if (
            process_id <= 0
            or not Path(f"/proc/{process_id}").is_dir()
        ):
            raise NativeStreamError(
                "The managed RetroArch process is no longer active."
            )

        ffmpeg = self._find_ffmpeg()

        if ffmpeg is None:
            raise NativeStreamError(
                "FFmpeg was not found on the Linux host."
            )

        if self._linux_display() is None:
            raise NativeStreamError(
                "Linux native video requires an active X11 DISPLAY."
            )

        if self._linux_xdotool() is None:
            raise NativeStreamError(
                "Linux native video requires xdotool for fail-closed "
                "managed-window discovery."
            )

        if self._linux_vaapi_device() is None:
            raise NativeStreamError(
                "Linux native video requires exactly one accessible DRM "
                "render node."
            )

        self._stop_locked()

        capture_target = self._select_capture_target(
            managed_process_id=process_id
        )
        capture_target = dict(capture_target)
        capture_target["backend"] = "x11grab_window"

        self._capture_target = capture_target

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._log_handle = open(
            self.log_path,
            "a",
            encoding="utf-8",
            errors="replace",
            buffering=1,
        )

        self._log_handle.write(
            "\n"
            + "=" * 72
            + "\n"
        )
        self._log_handle.write(
            "Starting PrivyHub Linux native-video backend "
            f"v{self.ALPHA_VERSION}\n"
        )
        self._log_handle.write(
            f"Profile: {self.PROFILE.id} "
            f"{self.WIDTH}x{self.HEIGHT}@{self.FPS}, "
            f"{self.BITRATE_KBPS}/{self.MAX_BITRATE_KBPS} kbps "
            f"H.264 VAAPI, GOP={self.GOP_FRAMES}, BF={self.BFRAMES}\n"
        )
        self._log_handle.write(
            "Capture backend: exact X11 window via x11grab\n"
        )
        self._log_handle.write(
            "Capture: managed RetroArch window "
            f"(pid={process_id}, "
            f"window_id={capture_target['_window_id']}, "
            f"discovered={capture_target['width']}x"
            f"{capture_target['height']})\n"
        )
        self._log_handle.write(
            f"Window title: {capture_target.get('title', '')}\n"
        )
        self._log_handle.write(
            f"Video FEC: XOR {self.FEC_GROUP_SIZE}+1; "
            "FFmpeg RTP -> loopback relay -> onn; "
            f"encoder={self.BITRATE_KBPS} kbps\n"
        )
        self._log_handle.write(
            "=" * 72
            + "\n"
        )
        self._log_handle.flush()

        try:
            self._fec_relay.start(
                client_ip=client_ip,
                client_port=port,
            )

            linux_command = self._build_linux_ffmpeg_command(
                ffmpeg=ffmpeg,
                capture_target=capture_target,
            )
            self._encoder_command = list(linux_command)

            self._log_handle.write(
                "encoder argv: "
                + " ".join(linux_command)
                + "\n"
            )
            self._log_handle.flush()

            self._process = subprocess.Popen(
                linux_command,
                cwd=str(self.project_root),
                stdin=subprocess.DEVNULL,
                stdout=self._log_handle,
                stderr=subprocess.STDOUT,
            )
        except Exception as exc:
            self._stop_locked()
            raise NativeStreamError(
                f"Unable to start Linux native video: {exc}"
            ) from exc

        self._client_port = port

        deadline = time.monotonic() + 0.75

        while time.monotonic() < deadline:
            if (
                self._process is None
                or self._process.poll() is not None
                or not self._fec_relay.running
            ):
                log_tail = self._tail_log()
                self._stop_locked()

                detail = (
                    f"\n\nFFmpeg log:\n{log_tail}"
                    if log_tail
                    else ""
                )

                raise NativeStreamError(
                    "Linux native video exited during startup."
                    + detail
                )

            time.sleep(0.05)

        self._session_io.start(
            ffmpeg=ffmpeg,
            client_ip=client_ip,
            audio_port=self.AUDIO_PORT,
            input_port=self.INPUT_PORT,
            process_id=process_id,
        )

        payload = self.status()
        payload["bootstrap"] = "in_band_h264_parameter_sets"
        payload["fec_enabled"] = True
        payload["fec_group_size"] = self.FEC_GROUP_SIZE
        payload["source_bitrate_kbps"] = self.BITRATE_KBPS
        payload["capture_target"] = self._public_capture_target(
            capture_target
        )

        return payload
    def start(
        self,
        client_ip: str,
        port: int = DEFAULT_PORT,
        managed_process_id: int | None = None,
    ) -> dict[str, Any]:
        client_ip = self._validated_ipv4(
            client_ip
        )

        port = self._validated_port(
            int(port)
        )

        # D-BASE-T1 piece 2: the host resource sampler runs for the life of
        # the stream. Idempotent, `nice 10`, its own process, and every
        # failure swallowed — a session must never fail to start because a
        # diagnostic sampler would not.
        try:
            host_resource_sampling.start(
                self.project_root
            )
        except Exception:
            pass

        with self._lock:
            if self._linux_host():
                return self._start_linux_locked(
                    client_ip=client_ip,
                    port=port,
                    managed_process_id=managed_process_id,
                )

            if os.name != "nt":
                raise NativeStreamError(
                    "Native streaming is not implemented for this host platform."
                )

            ffmpeg = self._find_ffmpeg()

            if ffmpeg is None:
                raise NativeStreamError(
                    "FFmpeg not found. Put the compatible project-local "
                    "build under runtime/streaming/ffmpeg/."
                )

            if not self._wgc_ready():
                raise NativeStreamError(
                    "Project-local Windows Graphics Capture runtime "
                    "is missing. Re-run the v0.4 setup patch."
                )

            self._stop_locked()

            capture_target = (
                self._select_capture_target()
            )

            self._capture_target = (
                capture_target
            )

            self.data_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.log_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            metadata_path = (
                self.data_dir
                / "wgc_capture_meta.json"
            )

            try:
                metadata_path.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

            self._log_handle = open(
                self.log_path,
                "a",
                encoding="utf-8",
                errors="replace",
                buffering=1,
            )

            self._log_handle.write(
                "\n"
                + "=" * 72
                + "\n"
            )

            self._log_handle.write(
                "Starting PrivyHub Native A/V/Input Alpha "
                f"v{self.ALPHA_VERSION}\n"
            )

            self._log_handle.write(
                f"Profile: {self.PROFILE.id} "
                f"{self.WIDTH}x{self.HEIGHT}@{self.FPS}, "
                f"{self.BITRATE_KBPS}/{self.MAX_BITRATE_KBPS} kbps "
                f"H.264 NVENC, GOP={self.GOP_FRAMES}, BF={self.BFRAMES}\n"
            )

            self._log_handle.write(
                "Capture backend: Windows Graphics Capture "
                "(project-local temporary bridge)\n"
            )

            self._log_handle.write(
                "Capture: RetroArch window "
                f"(pid={capture_target['pid']}, "
                f"hwnd={capture_target['_hwnd']}, "
                f"discovered-client="
                f"{capture_target['width']}x{capture_target['height']})\n"
            )

            self._log_handle.write(
                f"Window title: {capture_target['title']}\n"
            )

            self._log_handle.write(
                "=" * 72
                + "\n"
            )

            self._log_handle.flush()

            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
                if os.name == "nt"
                else 0
            )

            environment = (
                os.environ.copy()
            )

            runtime = str(
                self._wgc_runtime_dir()
            )

            existing_pythonpath = (
                environment.get(
                    "PYTHONPATH",
                    "",
                )
            )

            environment["PYTHONPATH"] = (
                runtime
                + (
                    os.pathsep
                    + existing_pythonpath
                    if existing_pythonpath
                    else ""
                )
            )

            bridge_command = [
                sys.executable,
                str(
                    self._wgc_bridge_path()
                ),
                "--hwnd",
                str(
                    int(
                        capture_target["_hwnd"]
                    )
                ),
                "--meta",
                str(
                    metadata_path
                ),
            ]

            try:
                self._capture_process = (
                    subprocess.Popen(
                        bridge_command,
                        cwd=str(
                            self.project_root
                        ),
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=self._log_handle,
                        bufsize=0,
                        env=environment,
                        creationflags=creationflags,
                    )
                )
            except Exception as exc:
                self._stop_locked()

                raise NativeStreamError(
                    "Unable to start the Windows Graphics Capture "
                    f"bridge: {exc}"
                ) from exc

            deadline = (
                time.monotonic()
                + 5.0
            )

            metadata: dict[str, Any] | None = (
                None
            )

            while time.monotonic() < deadline:
                capture_process = (
                    self._capture_process
                )

                if (
                    capture_process is None
                    or capture_process.poll()
                    is not None
                ):
                    log_tail = (
                        self._tail_log()
                    )

                    self._stop_locked()

                    detail = (
                        f"\n\nCapture log:\n{log_tail}"
                        if log_tail
                        else ""
                    )

                    raise NativeStreamError(
                        "Windows Graphics Capture exited before "
                        "delivering its first frame."
                        + detail
                    )

                if metadata_path.is_file():
                    try:
                        candidate = json.loads(
                            metadata_path.read_text(
                                encoding="utf-8"
                            )
                        )

                        width = int(
                            candidate.get(
                                "width",
                                0,
                            )
                        )

                        height = int(
                            candidate.get(
                                "height",
                                0,
                            )
                        )

                        if (
                            width >= 64
                            and height >= 64
                        ):
                            metadata = candidate
                            break

                    except (
                        OSError,
                        ValueError,
                        TypeError,
                        json.JSONDecodeError,
                    ):
                        pass

                time.sleep(
                    0.05
                )

            if metadata is None:
                log_tail = (
                    self._tail_log()
                )

                self._stop_locked()

                detail = (
                    f"\n\nCapture log:\n{log_tail}"
                    if log_tail
                    else ""
                )

                raise NativeStreamError(
                    "Windows Graphics Capture did not deliver "
                    "a usable first frame within 5 seconds."
                    + detail
                )

            source_width = int(
                metadata.get(
                    "source_width",
                    metadata["width"],
                )
            )

            source_height = int(
                metadata.get(
                    "source_height",
                    metadata["height"],
                )
            )

            if (
                source_width < 64
                or source_height < 64
            ):
                self._stop_locked()

                raise NativeStreamError(
                    "WGC bridge reported an invalid native frame size."
                )

            capture_target = dict(
                capture_target
            )

            capture_target["width"] = (
                source_width
            )

            capture_target["height"] = (
                source_height
            )

            capture_target["backend"] = (
                "windows_graphics_capture"
            )

            self._capture_target = (
                capture_target
            )

            self._log_handle.write(
                "WGC source frame: "
                f"{source_width}x{source_height} BGRA\n"
            )

            self._log_handle.write(
                "FFmpeg input: latest-frame native BGRA "
                f"{source_width}x{source_height}; "
                f"FFmpeg pads/scales to {self.WIDTH}x{self.HEIGHT}\n"
            )

            self._log_handle.write(
                "NVENC latency: p1 / tune=ull / zerolatency=1 / "
                "delay=0 / rc-lookahead=0 / "
                f"bf={self.BFRAMES}\n"
            )

            self._log_handle.write(
                f"Video FEC: XOR {self.FEC_GROUP_SIZE}+1; "
                "FFmpeg RTP -> loopback relay -> onn; "
                f"encoder={self.BITRATE_KBPS} kbps\n"
            )

            self._log_handle.flush()

            capture_stdout = (
                self._capture_process.stdout
                if self._capture_process
                is not None
                else None
            )

            if capture_stdout is None:
                self._stop_locked()

                raise NativeStreamError(
                    "Windows Graphics Capture raw-video "
                    "pipe was not created."
                )

            try:
                self._fec_relay.start(
                    client_ip=client_ip,
                    client_port=port,
                )

                self._process = (
                    subprocess.Popen(
                        self._build_ffmpeg_command(
                            ffmpeg=ffmpeg,
                            client_ip=client_ip,
                            port=port,
                            source_width=source_width,
                            source_height=source_height,
                        ),
                        cwd=str(
                            self.project_root
                        ),
                        stdin=capture_stdout,
                        stdout=self._log_handle,
                        stderr=subprocess.STDOUT,
                        creationflags=creationflags,
                    )
                )

                # FFmpeg inherited the read handle. The parent no longer needs
                # its own duplicate, which also makes broken-pipe behavior
                # deterministic during shutdown.
                capture_stdout.close()

            except Exception as exc:
                self._stop_locked()

                raise NativeStreamError(
                    f"Unable to start FFmpeg: {exc}"
                ) from exc

            self._client_port = port

            deadline = (
                time.monotonic()
                + 0.75
            )

            while time.monotonic() < deadline:
                if (
                    self._process is None
                    or self._process.poll()
                    is not None
                ):
                    log_tail = (
                        self._tail_log()
                    )

                    self._stop_locked()

                    detail = (
                        f"\n\nFFmpeg log:\n{log_tail}"
                        if log_tail
                        else ""
                    )

                    raise NativeStreamError(
                        "FFmpeg exited during Native A/V/Input Alpha "
                        "v0.4 startup."
                        + detail
                    )

                if (
                    self._capture_process is None
                    or self._capture_process.poll()
                    is not None
                ):
                    log_tail = (
                        self._tail_log()
                    )

                    self._stop_locked()

                    detail = (
                        f"\n\nCapture log:\n{log_tail}"
                        if log_tail
                        else ""
                    )

                    raise NativeStreamError(
                        "Windows Graphics Capture exited during "
                        "Native Performance Alpha v0.6 startup."
                        + detail
                    )

                time.sleep(
                    0.05
                )

            if (
                self._capture_process is not None
                and self._process is not None
            ):
                try:
                    self._host_telemetry.start(
                        capture_process=self._capture_process,
                        ffmpeg_process=self._process,
                        metadata_path=metadata_path,
                        capture_target=(
                            self._public_capture_target(
                                capture_target
                            )
                        ),
                    )
                except Exception as exc:
                    # Telemetry is strictly fail-open. Measurement must never
                    # prevent an otherwise healthy game stream.
                    self._log_handle.write(
                        "Host telemetry startup warning: "
                        f"{exc}\n"
                    )
                    self._log_handle.flush()

            self._session_io.start(
                ffmpeg=ffmpeg,
                client_ip=client_ip,
                audio_port=self.AUDIO_PORT,
                input_port=self.INPUT_PORT,
                process_id=int(
                    capture_target["pid"]
                ),
            )

            payload = self.status()
            payload["bootstrap"] = (
                "in_band_h264_parameter_sets"
            )
            payload["fec_enabled"] = True
            payload["fec_group_size"] = self.FEC_GROUP_SIZE
            payload["source_bitrate_kbps"] = self.BITRATE_KBPS
            payload["capture_target"] = (
                self._public_capture_target(
                    capture_target
                )
            )

            return payload

    def diagnostic_c3_actuator_continuity_cycle(
        self,
    ) -> dict[str, Any]:
        """Run one same-bitrate video-only actuator continuity diagnostic.

        The actuator strategy is backend-neutral; the implementation is not.
        Windows replaces the WGC capture bridge and the FFmpeg/NVENC encoder
        together because raw frames cross an inherited pipe. Linux replaces
        only the FFmpeg/VAAPI encoder because x11grab is an input format inside
        that same process.

        Both implementations preserve FEC, process audio, the persistent
        controller and the emulator lifecycle, and both emit the same probe
        schema so the existing loopback-only action and probe runner are
        unchanged.
        """
        with self._lock:
            if self._active_bitrate_kbps != self.BITRATE_KBPS:
                raise NativeStreamError(
                    "C3 same-bitrate continuity diagnostic requires "
                    "the 7000 kbps reference stream"
                )

            if self._linux_host():
                from diagnostics.c3_linux_actuator_probe import (
                    run_c3_linux_actuator_continuity_cycle as _cycle,
                )
            elif os.name == "nt":
                from diagnostics.c3_actuator_probe import (
                    run_c3_actuator_continuity_cycle as _cycle,
                )
            else:
                raise NativeStreamError(
                    "C3 actuator continuity diagnostic is not implemented "
                    "for this host platform"
                )

            try:
                return _cycle(
                    self
                )
            except NativeStreamError:
                raise
            except Exception as exc:
                raise NativeStreamError(
                    "C3 actuator continuity diagnostic failed: "
                    + type(exc).__name__
                ) from exc

    def diagnostic_c3_fixed_bitrate_6000_cycle(
        self,
    ) -> dict[str, Any]:
        """Run the first fixed-bitrate C3 characterization point."""
        with self._lock:
            if self._linux_host():
                from diagnostics.c3_linux_actuator_probe import (
                    run_c3_linux_fixed_bitrate_cycle as _cycle,
                )

                kwargs: dict[str, Any] = {"target_bitrate_kbps": 6000}
            elif os.name == "nt":
                from diagnostics.c3_fixed_bitrate_probe import (
                    run_c3_fixed_bitrate_6000_cycle as _cycle,
                )

                kwargs = {}
            else:
                raise NativeStreamError(
                    "C3 fixed 6000 kbps characterization is not "
                    "implemented for this host platform"
                )

            try:
                return _cycle(self, **kwargs)
            except NativeStreamError:
                raise
            except Exception as exc:
                raise NativeStreamError(
                    "C3 fixed 6000 kbps characterization failed: "
                    + type(exc).__name__ + ": " + str(exc)
                ) from exc

    def diagnostic_c3_fixed_bitrate_5000_cycle(
        self,
    ) -> dict[str, Any]:
        """Run the 5000 kbps fixed-bitrate C3 characterization point."""
        with self._lock:
            if self._linux_host():
                from diagnostics.c3_linux_actuator_probe import (
                    run_c3_linux_fixed_bitrate_cycle as _cycle,
                )

                kwargs: dict[str, Any] = {"target_bitrate_kbps": 5000}
            elif os.name == "nt":
                from diagnostics.c3_fixed_bitrate_probe import (
                    run_c3_fixed_bitrate_5000_cycle as _cycle,
                )

                kwargs = {}
            else:
                raise NativeStreamError(
                    "C3 fixed 5000 kbps characterization is not "
                    "implemented for this host platform"
                )

            try:
                return _cycle(self, **kwargs)
            except NativeStreamError:
                raise
            except Exception as exc:
                raise NativeStreamError(
                    "C3 fixed 5000 kbps characterization failed: "
                    + type(exc).__name__ + ": " + str(exc)
                ) from exc

    def diagnostic_c3_fixed_bitrate_5500_cycle(
        self,
    ) -> dict[str, Any]:
        """Run the 5500 kbps fixed-bitrate C3 characterization point."""
        with self._lock:
            if self._linux_host():
                from diagnostics.c3_linux_actuator_probe import (
                    run_c3_linux_fixed_bitrate_cycle as _cycle,
                )

                kwargs: dict[str, Any] = {"target_bitrate_kbps": 5500}
            elif os.name == "nt":
                from diagnostics.c3_fixed_bitrate_probe import (
                    run_c3_fixed_bitrate_5500_cycle as _cycle,
                )

                kwargs = {}
            else:
                raise NativeStreamError(
                    "C3 fixed 5500 kbps characterization is not "
                    "implemented for this host platform"
                )

            try:
                return _cycle(self, **kwargs)
            except NativeStreamError:
                raise
            except Exception as exc:
                raise NativeStreamError(
                    "C3 fixed 5500 kbps characterization failed: "
                    + type(exc).__name__ + ": " + str(exc)
                ) from exc

    def diagnostic_c3_validated_bitrate_transition(
        self,
        target_bitrate_kbps: int,
    ) -> dict[str, Any]:
        """Run one loopback-only validated-ladder actuator transition.

        Backend-neutral strategy, platform-specific implementation, the same
        split as `diagnostic_c3_actuator_continuity_cycle` and the fixed
        bitrate cycles. Windows replaces the WGC capture bridge and the
        FFmpeg/NVENC encoder together; Linux replaces only the FFmpeg/VAAPI
        encoder because x11grab is an input format inside that process.

        Both emit `privyhub_c3_validated_bitrate_transition_v1`, so the
        existing loopback-only route is unchanged. The validated ladders
        differ by platform and each implementation enforces its own: Linux
        includes 5000 kbps on C3.L3 evidence, Windows does not.
        """
        with self._lock:
            if self._linux_host():
                from diagnostics.c3_linux_actuator_probe import (
                    run_c3_linux_validated_bitrate_transition as _cycle,
                )
            elif os.name == "nt":
                from diagnostics.c3_fixed_bitrate_probe import (
                    run_c3_validated_bitrate_transition as _cycle,
                )
            else:
                raise NativeStreamError(
                    "C3 validated bitrate transition is not implemented "
                    "for this host platform"
                )

            try:
                return _cycle(
                    self,
                    target_bitrate_kbps=int(
                        target_bitrate_kbps
                    ),
                )
            except NativeStreamError:
                raise
            except Exception as exc:
                raise NativeStreamError(
                    "C3 validated bitrate transition failed: "
                    + type(exc).__name__ + ": " + str(exc)
                ) from exc

    def stop(self) -> dict[str, Any]:
        try:
            host_resource_sampling.stop()
        except Exception:
            pass

        with self._lock:
            self._stop_locked()
            return self.status()
