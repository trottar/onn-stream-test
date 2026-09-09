from __future__ import annotations

import json
import os

from collections import deque
import re
import socket
import struct
import subprocess
import sys
import threading
import time

from pathlib import Path
from typing import Any


class NativeSessionIOError(RuntimeError):
    pass


class NativeAudioStreamer:
    TIMING_PROBE_VERSION = "process_loopback_pair_pacer_v0.22"
    AUDIO_BUFFER_ARCHITECTURE = "windows_process_loopback_pair_pacer_v0.22"

    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.project_root = project_root.resolve()
        self.runtime_dir = (
            self.project_root
            / "runtime"
            / "streaming"
            / "process_audio"
        )
        self.helper_path = (
            self.runtime_dir
            / "PrivyHubProcessAudio.exe"
        )
        self.log_dir = (
            self.project_root
            / "logs"
            / "games"
        )
        self.timing_log_dir = (
            self.log_dir
            / "audio_timing"
        )
        self.helper_log_path = (
            self.log_dir
            / "native_process_audio.log"
        )
        self.status_path = (
            self.project_root
            / "data"
            / "games"
            / "native_stream"
            / "process_audio_status.json"
        )

        self._process: subprocess.Popen[Any] | None = None
        self._log_handle = None
        self._lock = threading.RLock()

        self._target_pid: int | None = None
        self._client_ip: str | None = None
        self._client_port: int | None = None
        self._timing_path: Path | None = None
        self._last_status: dict[str, Any] = {}

    @staticmethod
    def _kill_process(
        process: subprocess.Popen[Any] | None,
    ) -> None:
        if (
            process is None
            or process.poll() is not None
        ):
            return

        if os.name == "nt":
            try:
                import signal

                process.send_signal(
                    signal.CTRL_BREAK_EVENT
                )
                process.wait(
                    timeout=2.0
                )
                return
            except Exception:
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
                timeout=2
            )
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass

    def _read_status(
        self,
    ) -> dict[str, Any]:
        if not self.status_path.is_file():
            return {}

        try:
            payload = json.loads(
                self.status_path.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(
                payload,
                dict,
            ):
                self._last_status = (
                    payload
                )
                return payload
        except Exception:
            pass

        return dict(
            self._last_status
        )

    def start(
        self,
        ffmpeg: Path,
        client_ip: str,
        client_port: int,
        process_id: int,
    ) -> dict[str, Any]:
        del ffmpeg

        with self._lock:
            self.stop()

            if os.name != "nt":
                raise NativeSessionIOError(
                    "Windows process-loopback audio is Windows-only."
                )

            if not self.helper_path.is_file():
                raise NativeSessionIOError(
                    "PrivyHub process-loopback audio helper is missing. "
                    "Re-apply the v0.21.1 audio probe patch."
                )

            process_id = int(
                process_id
            )

            if process_id <= 0:
                raise NativeSessionIOError(
                    "Managed RetroArch process ID is invalid."
                )

            self.timing_log_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
            self.status_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            stamp = time.strftime(
                "%Y%m%d_%H%M%S"
            )
            self._timing_path = (
                self.timing_log_dir
                / (
                    "audio_process_loopback_"
                    + stamp
                    + ".json"
                )
            )

            try:
                self.status_path.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

            self._log_handle = open(
                self.helper_log_path,
                "ab",
                buffering=0,
            )

            command = [
                str(
                    self.helper_path
                ),
                "--pid",
                str(
                    process_id
                ),
                "--client-ip",
                client_ip,
                "--port",
                str(
                    int(
                        client_port
                    )
                ),
                "--log",
                str(
                    self._timing_path
                ),
                "--status",
                str(
                    self.status_path
                ),
            ]

            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
                if os.name == "nt"
                else 0
            )

            try:
                self._process = (
                    subprocess.Popen(
                        command,
                        cwd=str(
                            self.project_root
                        ),
                        stdin=subprocess.DEVNULL,
                        stdout=self._log_handle,
                        stderr=self._log_handle,
                        creationflags=creationflags,
                    )
                )
            except Exception as exc:
                self.stop()

                raise NativeSessionIOError(
                    "Unable to start native Windows process-loopback "
                    f"audio helper: {exc}"
                ) from exc

            self._target_pid = (
                process_id
            )
            self._client_ip = (
                client_ip
            )
            self._client_port = int(
                client_port
            )
            self._last_status = {}

            deadline = (
                time.monotonic()
                + 5.0
            )

            while time.monotonic() < deadline:
                process = (
                    self._process
                )

                if (
                    process is None
                    or process.poll()
                    is not None
                ):
                    status = (
                        self._read_status()
                    )
                    detail = str(
                        status.get(
                            "error",
                            "",
                        )
                    ).strip()

                    self.stop()

                    raise NativeSessionIOError(
                        "Windows process-loopback audio helper exited "
                        "during startup."
                        + (
                            " "
                            + detail
                            if detail
                            else ""
                        )
                    )

                status = (
                    self._read_status()
                )

                if bool(
                    status.get(
                        "ready",
                        False,
                    )
                ):
                    return self.status()

                time.sleep(
                    0.05
                )

            self.stop()

            raise NativeSessionIOError(
                "Windows process-loopback audio helper did not become "
                "ready within 5 seconds."
            )

    def status(
        self,
    ) -> dict[str, Any]:
        process_active = (
            self._process is not None
            and self._process.poll()
            is None
        )

        helper = (
            self._read_status()
        )

        return {
            "active": (
                process_active
                and bool(
                    helper.get(
                        "ready",
                        False,
                    )
                )
            ),
            "device": (
                "managed_process_audio"
            ),
            "sample_rate": 48_000,
            "channels": 2,
            "format": "pcm_s16le",
            "packet_ms": 5,
            "port": self._client_port,
            "target_pid": (
                self._target_pid
            ),
            "include_process_tree": True,
            "capture_backend": (
                "windows_wasapi_process_loopback"
            ),
            "helper": (
                "NAudio.Wasapi 3.0.1"
            ),
            "timing_probe": (
                self.TIMING_PROBE_VERSION
            ),
            "audio_buffer_architecture": (
                self.AUDIO_BUFFER_ARCHITECTURE
            ),
            "packets_sent": int(
                helper.get(
                    "send",
                    {},
                ).get(
                    "packets",
                    0,
                )
                if isinstance(
                    helper.get(
                        "send",
                        {},
                    ),
                    dict,
                )
                else 0
            ),
            "send_errors": int(
                helper.get(
                    "send",
                    {},
                ).get(
                    "errors",
                    0,
                )
                if isinstance(
                    helper.get(
                        "send",
                        {},
                    ),
                    dict,
                )
                else 0
            ),
            "timing_log": (
                str(
                    self._timing_path
                )
                if self._timing_path
                is not None
                else ""
            ),
            "helper_status": helper,
        }

    def stop(
        self,
    ) -> None:
        process = (
            self._process
        )
        self._process = None

        self._kill_process(
            process
        )

        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass

        self._log_handle = None
        self._client_ip = None
        self._client_port = None
        self._target_pid = None

class NativeControllerBridge:
    MAGIC = b"PHI1"
    VERSION = 1
    MAX_PLAYERS = 2
    POC_VERSION = "two_player_poc_v0.1"
    PACKET = struct.Struct(
        "<4sBBHIQIhhhhHH"
    )

    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.project_root = project_root.resolve()
        self.runtime_dir = (
            self.project_root
            / "runtime"
            / "streaming"
            / "input_python"
        )

        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._gamepads: list[Any] = []
        self._client_ip: str | None = None
        self._port: int | None = None

        self._packets = 0
        self._lost_packets = 0
        self._rejected_packets = 0
        self._bad_packets = 0
        self._updates = 0
        self._updates_by_player = [0, 0]
        self._last_sequence: int | None = None
        self._last_packet_at = [0.0, 0.0]
        self._neutralized = [True, True]
        self._forced_buttons = [0, 0]
        self._meta_lock = threading.RLock()

    def _load_vgamepad(
        self,
    ):
        if not self.runtime_dir.is_dir():
            raise NativeSessionIOError(
                "Project-local vgamepad runtime is missing."
            )

        runtime = str(
            self.runtime_dir
        )

        if runtime not in sys.path:
            sys.path.insert(
                0,
                runtime,
            )

        try:
            import vgamepad as vg
        except Exception as exc:
            raise NativeSessionIOError(
                f"Unable to import project-local vgamepad: {exc}"
            ) from exc

        return vg

    @staticmethod
    def _clamp_axis(
        value: int,
    ) -> int:
        return max(
            -32768,
            min(
                32767,
                int(value),
            ),
        )

    @staticmethod
    def _clamp_trigger(
        value: int,
    ) -> int:
        return max(
            0,
            min(
                255,
                int(value),
            ),
        )

    # PrivyHub Phase A3 persistent game-session controller
    def ensure_started(
        self,
        client_ip: str,
        port: int,
    ) -> dict[str, Any]:
        active = bool(
            self._running.is_set()
            and self._socket is not None
            and len(self._gamepads) == self.MAX_PLAYERS
        )
        if active and self._client_ip == client_ip and self._port == int(port):
            return self.status()
        result = self.start(client_ip=client_ip, port=port)
        time.sleep(0.35)
        return result

    def start(
        self,
        client_ip: str,
        port: int,
    ) -> dict[str, Any]:
        self.stop()

        vg = self._load_vgamepad()
        gamepads: list[Any] = []

        try:
            for _ in range(
                self.MAX_PLAYERS
            ):
                gamepads.append(
                    vg.VX360Gamepad()
                )
        except Exception as exc:
            for gamepad in gamepads:
                try:
                    gamepad.reset()
                    gamepad.update()
                except Exception:
                    pass

            raise NativeSessionIOError(
                "Unable to create two temporary virtual X360 controllers. "
                "ViGEmBus must already be installed on this Windows host."
            ) from exc

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_RCVBUF,
            256 * 1024,
        )

        sock.bind(
            (
                "0.0.0.0",
                int(port),
            )
        )

        sock.settimeout(
            0.05
        )

        self._socket = sock
        self._gamepads = gamepads
        self._client_ip = client_ip
        self._port = int(port)

        self._packets = 0
        self._lost_packets = 0
        self._rejected_packets = 0
        self._bad_packets = 0
        self._updates = 0
        self._updates_by_player = [0, 0]
        self._last_sequence = None
        self._last_packet_at = [0.0, 0.0]
        self._neutralized = [True, True]

        with self._meta_lock:
            self._forced_buttons = [0, 0]

        self._running.set()

        self._thread = threading.Thread(
            target=self._receive_loop,
            name="PrivyHub-Native-Controller",
            daemon=True,
        )
        self._thread.start()

        return self.status()

    def _neutralize(
        self,
        player: int | None = None,
    ) -> None:
        players = (
            range(
                self.MAX_PLAYERS
            )
            if player is None
            else (player,)
        )

        for index in players:
            if not (
                0 <= index < len(
                    self._gamepads
                )
            ):
                continue

            gamepad = self._gamepads[index]

            try:
                # PrivyHub A2/A3 patch 01: timeout neutralization must not
                # erase a companion-injected RetroArch meta hotkey mid-pulse.
                with self._meta_lock:
                    forced_buttons = self._forced_buttons[index]
                    gamepad.reset()
                    gamepad.report.wButtons = (
                        int(forced_buttons)
                        & 0xFFFF
                    )
                    gamepad.update()
                    self._neutralized[index] = (
                        forced_buttons == 0
                    )
            except Exception:
                pass

    def _apply_report(
        self,
        player: int,
        buttons: int,
        lx: int,
        ly: int,
        rx: int,
        ry: int,
        lt: int,
        rt: int,
    ) -> None:
        if not (
            0 <= player < len(
                self._gamepads
            )
        ):
            return

        gamepad = self._gamepads[player]

        # PrivyHub A2/A3 patch 01: serialize real reports with the forced
        # meta-button overlay so receiver traffic cannot erase a hotkey.
        with self._meta_lock:
            forced_buttons = self._forced_buttons[player]

            gamepad.report.wButtons = (
                (
                    int(buttons)
                    & 0xFFFF
                )
                | forced_buttons
            )
            gamepad.report.bLeftTrigger = (
                self._clamp_trigger(lt)
            )
            gamepad.report.bRightTrigger = (
                self._clamp_trigger(rt)
            )
            gamepad.report.sThumbLX = (
                self._clamp_axis(lx)
            )
            gamepad.report.sThumbLY = (
                self._clamp_axis(ly)
            )
            gamepad.report.sThumbRX = (
                self._clamp_axis(rx)
            )
            gamepad.report.sThumbRY = (
                self._clamp_axis(ry)
            )

            gamepad.update()

            self._updates += 1
            self._updates_by_player[player] += 1
            self._neutralized[player] = False

    # PrivyHub A2/A3 patch 02: stage RetroArch meta-hotkey edges.
    # RetroArch treats input_enable_hotkey as a modifier. A human press
    # naturally establishes Back/View before the action button; emitting both
    # bits in one XInput report can be missed by the frontend. Keep the proven
    # XInput mappings, but reproduce the physical chord ordering explicitly.
    RETROARCH_HOTKEY_ENABLE = 0x0020  # Back / View
    RETROARCH_META_ACTION_BUTTONS = {
        "save": 0x0200,  # right shoulder
        "load": 0x0100,  # left shoulder
        "pause": 0x0080,  # right thumb
        "quit": 0x0010,  # Start
    }

    def pulse_retroarch_hotkey(
        self,
        action: str,
        *,
        player: int = 0,
        hold_seconds: float = 0.18,
        modifier_settle_seconds: float = 0.08,
        release_gap_seconds: float = 0.06,
    ) -> dict[str, Any]:
        normalized_action = (
            str(action).strip().casefold()
        )
        action_mask = (
            self.RETROARCH_META_ACTION_BUTTONS.get(
                normalized_action
            )
        )
        if action_mask is None:
            raise NativeSessionIOError(
                f"Unknown RetroArch hotkey action: {action}"
            )

        if not self._running.is_set():
            raise NativeSessionIOError(
                "Native controller bridge is not running"
            )
        if not (0 <= player < len(self._gamepads)):
            raise NativeSessionIOError(
                "Requested virtual controller is unavailable"
            )

        gamepad = self._gamepads[player]
        modifier_mask = int(
            self.RETROARCH_HOTKEY_ENABLE
        )
        action_mask = int(action_mask)
        hold = max(
            0.08,
            min(0.50, float(hold_seconds)),
        )
        settle = max(
            0.04,
            min(0.20, float(modifier_settle_seconds)),
        )
        release_gap = max(
            0.03,
            min(0.20, float(release_gap_seconds)),
        )

        # 1. Establish Back/View alone.
        with self._meta_lock:
            self._forced_buttons[player] |= modifier_mask
            gamepad.report.wButtons = (
                int(gamepad.report.wButtons)
                | modifier_mask
            ) & 0xFFFF
            gamepad.update()

        time.sleep(settle)

        # 2. Press the action while the modifier is already held.
        with self._meta_lock:
            self._forced_buttons[player] |= action_mask
            gamepad.report.wButtons = (
                int(gamepad.report.wButtons)
                | action_mask
            ) & 0xFFFF
            gamepad.update()

        time.sleep(hold)

        # 3. Release the action first, preserving Back/View.
        with self._meta_lock:
            self._forced_buttons[player] &= ~action_mask
            gamepad.report.wButtons = (
                int(gamepad.report.wButtons)
                & ~action_mask
            ) & 0xFFFF
            gamepad.update()

        time.sleep(release_gap)

        # 4. Release Back/View last so RetroArch sees a complete chord.
        with self._meta_lock:
            self._forced_buttons[player] &= ~modifier_mask
            gamepad.report.wButtons = (
                int(gamepad.report.wButtons)
                & ~modifier_mask
            ) & 0xFFFF
            gamepad.update()

        return {
            "action": normalized_action,
            "player": player + 1,
            "modifier_mask": modifier_mask,
            "action_mask": action_mask,
            "mask": modifier_mask | action_mask,
            "modifier_settle_ms": int(settle * 1000),
            "hold_ms": int(hold * 1000),
            "release_gap_ms": int(release_gap * 1000),
            "edge_sequence": [
                "modifier_down",
                "action_down",
                "action_up",
                "modifier_up",
            ],
        }

    def _receive_loop(
        self,
    ) -> None:
        sock = self._socket

        if sock is None:
            return

        while self._running.is_set():
            try:
                data, source = sock.recvfrom(
                    256
                )
            except socket.timeout:
                now = time.monotonic()

                for player in range(
                    self.MAX_PLAYERS
                ):
                    if (
                        not self._neutralized[player]
                        and self._last_packet_at[player] > 0.0
                        and now - self._last_packet_at[player] > 0.25
                    ):
                        self._neutralize(
                            player
                        )

                continue
            except OSError:
                break

            if source[0] != self._client_ip:
                self._rejected_packets += 1
                continue

            if len(data) != self.PACKET.size:
                self._bad_packets += 1
                continue

            try:
                (
                    magic,
                    version,
                    player,
                    _flags,
                    sequence,
                    _client_time_us,
                    buttons,
                    lx,
                    ly,
                    rx,
                    ry,
                    lt,
                    rt,
                ) = self.PACKET.unpack(
                    data
                )
            except struct.error:
                self._bad_packets += 1
                continue

            if (
                magic != self.MAGIC
                or version != self.VERSION
                or player < 0
                or player >= self.MAX_PLAYERS
            ):
                self._bad_packets += 1
                continue

            if self._last_sequence is not None:
                expected = (
                    self._last_sequence + 1
                ) & 0xFFFFFFFF

                if sequence != expected:
                    missing = (
                        sequence - expected
                    ) & 0xFFFFFFFF

                    if missing < 0x80000000:
                        self._lost_packets += missing

            self._last_sequence = sequence
            self._packets += 1
            self._last_packet_at[player] = (
                time.monotonic()
            )

            try:
                self._apply_report(
                    player=player,
                    buttons=buttons,
                    lx=lx,
                    ly=ly,
                    rx=rx,
                    ry=ry,
                    lt=lt,
                    rt=rt,
                )
            except Exception:
                self._bad_packets += 1

        self._neutralize()

    def status(
        self,
    ) -> dict[str, Any]:
        return {
            "active": (
                self._running.is_set()
                and self._socket is not None
                and len(
                    self._gamepads
                ) == self.MAX_PLAYERS
            ),
            "sink": "vigem_x360_dual_poc",
            "transport": "udp_full_state",
            "poc_version": self.POC_VERSION,
            "players": self.MAX_PLAYERS,
            "port": self._port,
            "packets_received": self._packets,
            "lost_packets": self._lost_packets,
            "rejected_packets": self._rejected_packets,
            "bad_packets": self._bad_packets,
            "vigem_updates": self._updates,
            "vigem_updates_by_player": list(
                self._updates_by_player
            ),
        }

    def stop(
        self,
    ) -> None:
        self._running.clear()

        sock = self._socket
        self._socket = None

        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

        thread = self._thread
        self._thread = None

        if (
            thread is not None
            and thread is not threading.current_thread()
        ):
            thread.join(
                timeout=1
            )

        with self._meta_lock:
            self._forced_buttons = [0, 0]

        self._neutralize()
        self._gamepads = []
        self._client_ip = None
        self._port = None


class NativeSessionIO:
    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.audio = NativeAudioStreamer(
            project_root
        )
        self.controller = NativeControllerBridge(
            project_root
        )

        self._audio_error: str | None = None
        self._controller_error: str | None = None

    # PrivyHub Phase A3 persistent game-session controller
    def ensure_controller(
        self,
        client_ip: str,
        input_port: int,
    ) -> dict[str, Any]:
        self._controller_error = None
        try:
            return self.controller.ensure_started(client_ip=client_ip, port=input_port)
        except Exception as exc:
            self._controller_error = str(exc)
            raise

    def start(
        self,
        ffmpeg: Path,
        client_ip: str,
        audio_port: int,
        input_port: int,
        process_id: int,
    ) -> dict[str, Any]:
        self.audio.stop()
        self._audio_error = None
        try:
            self.ensure_controller(client_ip=client_ip, input_port=input_port)
        except Exception:
            pass
        try:
            self.audio.start(
                ffmpeg=ffmpeg,
                client_ip=client_ip,
                client_port=audio_port,
                process_id=process_id,
            )
        except Exception as exc:
            self._audio_error = str(exc)
        return self.status()

    def status(self) -> dict[str, Any]:
        audio = self.audio.status()
        controller = self.controller.status()
        if self._audio_error:
            audio["error"] = self._audio_error
        if self._controller_error:
            controller["error"] = self._controller_error
        return {"audio": audio, "controller": controller}

    def stop_stream(self) -> None:
        self.audio.stop()
        self._audio_error = None

    def stop(self) -> None:
        self.audio.stop()
        self.controller.stop()
        self._audio_error = None
        self._controller_error = None
