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
from native_host_telemetry import NativeHostTelemetryProfiler


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

    WIDTH = 1280
    HEIGHT = 720
    FPS = 60
    GOP_FRAMES = 15
    BITRATE_KBPS = 7000
    PAYLOAD_TYPE = 96
    DEFAULT_PORT = 48100
    FEC_INPUT_PORT = 48110
    FEC_GROUP_SIZE = 8
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
        self._capture_target: dict[str, Any] | None = None
        self._last_capture_target: dict[str, Any] | None = None
        self._session_io = NativeSessionIO(
            self.project_root
        )
        self._fec_relay = NativeVideoFecRelay(
            local_port=self.FEC_INPUT_PORT,
            group_size=self.FEC_GROUP_SIZE,
        )
        self._host_telemetry = NativeHostTelemetryProfiler(
            self.project_root
        )

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

    def _running_locked(self) -> bool:
        return (
            self._process is not None
            and self._process.poll() is None
            and self._capture_process is not None
            and self._capture_process.poll() is None
            and self._fec_relay.running
        )

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

    def status(self) -> dict[str, Any]:
        with self._lock:
            self._reap_locked()

            ffmpeg = self._find_ffmpeg()
            wgc_ready = self._wgc_ready()
            active = self._running_locked()

            if os.name != "nt":
                ready = False
                message = (
                    "Native Performance Alpha v0.6 currently implements "
                    "the Windows Graphics Capture host only."
                )
            elif ffmpeg is None:
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
                    "Windows Graphics Capture using a fixed 1280x720 "
                    "frame envelope and streaming H.264 RTP/UDP."
                )
            else:
                ready = True
                message = (
                    "Native Performance Alpha v0.6 is ready. Launch a game first, "
                    "then open the native receiver on the onn."
                )

            session_io = (
                self._session_io.status()
            )

            return {
                "ok": True,
                "kind": "native_stream_host",
                "alpha_version": self.ALPHA_VERSION,
                "title": "Native Streaming Alpha",
                "ready": ready,
                "active": active,
                "managed": active,
                "capture_backend": (
                    "windows_graphics_capture"
                    if os.name == "nt"
                    else "unavailable"
                ),
                "encoder": "h264_nvenc",
                "transport": "rtp_udp_xor_fec",
                "fec": self._fec_relay.status(),
                "host_telemetry": self._host_telemetry.status(),
                "fec_enabled": True,
                "fec_group_size": self.FEC_GROUP_SIZE,
                "source_bitrate_kbps": self.BITRATE_KBPS,
                "width": self.WIDTH,
                "height": self.HEIGHT,
                "fps": self.FPS,
                "gop_frames": self.GOP_FRAMES,
                "bitrate_kbps": self.BITRATE_KBPS,
                "payload_type": self.PAYLOAD_TYPE,
                "video_port": self._client_port,
                "audio_port": self.AUDIO_PORT,
                "input_port": self.INPUT_PORT,
                "audio": session_io["audio"],
                "controller": session_io["controller"],
                "ffmpeg_found": ffmpeg is not None,
                "wgc_runtime_found": wgc_ready,
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

    def _retroarch_executable(self) -> Path:
        return (
            self.project_root
            / "runtime"
            / "emulators"
            / "retroarch"
            / "retroarch.exe"
        ).resolve()

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

    def _find_retroarch_window(
        self,
    ) -> dict[str, Any] | None:
        """Return the largest visible top-level window owned by RetroArch.

        The Android client never supplies a title, PID, or HWND.  PrivyHub
        derives the target from the exact project-managed RetroArch executable.
        """

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
    ) -> dict[str, Any]:
        # Fail closed. Native game streaming must never silently broaden from
        # the PrivyHub-owned emulator window to the user's whole desktop.
        deadline = time.monotonic() + 2.0

        while time.monotonic() < deadline:
            window = self._find_retroarch_window()

            if window is not None:
                return window

            time.sleep(0.10)

        raise NativeStreamError(
            "No visible window owned by the project-managed RetroArch "
            "executable was found. Whole-desktop capture is intentionally "
            "disabled in Native Performance Alpha v0.6."
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
    ) -> list[str]:
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
            f"{self.BITRATE_KBPS}k",
            "-maxrate",
            f"{self.BITRATE_KBPS}k",
            "-bufsize",
            "1000k",
            "-g",
            str(self.GOP_FRAMES),
            "-bf",
            "0",
            "-pix_fmt",
            "yuv420p",
            "-payload_type",
            str(self.PAYLOAD_TYPE),
            "-f",
            "rtp",
            destination,
        ]

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

        self._session_io.stop()

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
        self._client_port = None

        if self._capture_target is not None:
            self._last_capture_target = self._capture_target

        self._capture_target = None

        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass

            self._log_handle = None

    def start(
        self,
        client_ip: str,
        port: int = DEFAULT_PORT,
    ) -> dict[str, Any]:
        client_ip = self._validated_ipv4(
            client_ip
        )

        port = self._validated_port(
            int(port)
        )

        with self._lock:
            if os.name != "nt":
                raise NativeStreamError(
                    "Native Performance Alpha v0.6 currently supports "
                    "the Windows host only."
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
                f"Profile: {self.WIDTH}x{self.HEIGHT}@{self.FPS}, "
                f"{self.BITRATE_KBPS} kbps H.264 NVENC, "
                f"GOP={self.GOP_FRAMES}\n"
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
                "delay=0 / rc-lookahead=0 / bf=0\n"
            )

            self._log_handle.write(
                "Video FEC: XOR 8+1; FFmpeg RTP -> loopback relay -> onn; "
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

    def stop(self) -> dict[str, Any]:
        with self._lock:
            self._stop_locked()
            return self.status()
