from __future__ import annotations

import os
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
    MAGIC = b"PHA1"
    VERSION = 1
    SAMPLE_RATE = 48_000
    CHANNELS = 2
    SAMPLE_BYTES = 2
    FRAMES_PER_PACKET = 240  # 5 ms at 48 kHz
    PAYLOAD_BYTES = (
        FRAMES_PER_PACKET
        * CHANNELS
        * SAMPLE_BYTES
    )
    HEADER = struct.Struct("<4sBBHII")

    def __init__(
        self,
        project_root: Path,
    ) -> None:
        self.project_root = project_root.resolve()
        self.log_dir = (
            self.project_root
            / "logs"
            / "games"
        )
        self.log_path = (
            self.log_dir
            / "native_audio_alpha.log"
        )

        self._process: subprocess.Popen[Any] | None = None
        self._thread: threading.Thread | None = None
        self._socket: socket.socket | None = None
        self._log_handle = None
        self._running = threading.Event()
        self._lock = threading.RLock()

        self._device: str | None = None
        self._client_ip: str | None = None
        self._client_port: int | None = None
        self._packets = 0
        self._bytes = 0
        self._send_errors = 0

    @staticmethod
    def _kill_process(
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
                timeout=3
            )
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass

    @staticmethod
    def _read_exact(
        stream,
        size: int,
    ) -> bytes:
        chunks: list[bytes] = []
        remaining = size

        while remaining > 0:
            chunk = stream.read(
                remaining
            )

            if not chunk:
                break

            chunks.append(
                chunk
            )
            remaining -= len(
                chunk
            )

        return b"".join(
            chunks
        )

    def _find_cable_output(
        self,
        ffmpeg: Path,
    ) -> str | None:
        try:
            result = subprocess.run(
                [
                    str(ffmpeg),
                    "-hide_banner",
                    "-list_devices",
                    "true",
                    "-f",
                    "dshow",
                    "-i",
                    "dummy",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=8,
                check=False,
            )
        except Exception:
            return None

        text = (
            result.stdout
            + "\n"
            + result.stderr
        )

        candidates = re.findall(
            r'"([^"\r\n]*CABLE Output[^"\r\n]*)"',
            text,
            flags=re.IGNORECASE,
        )

        if not candidates:
            return None

        preferred = [
            candidate
            for candidate in candidates
            if "VB-Audio Virtual Cable" in candidate
        ]

        return (
            preferred[0]
            if preferred
            else candidates[0]
        )

    def start(
        self,
        ffmpeg: Path,
        client_ip: str,
        client_port: int,
    ) -> dict[str, Any]:
        with self._lock:
            self.stop()

            device = (
                self._find_cable_output(
                    ffmpeg
                )
            )

            if not device:
                raise NativeSessionIOError(
                    "VB-CABLE recording endpoint was not found. "
                    "Expected a DirectShow audio source containing "
                    "\"CABLE Output\"."
                )

            self.log_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            self._log_handle = open(
                self.log_path,
                "ab",
                buffering=0,
            )

            command = [
                str(ffmpeg),
                "-hide_banner",
                "-loglevel",
                "warning",
                "-nostdin",
                "-f",
                "dshow",
                "-audio_buffer_size",
                "20",
                "-i",
                f"audio={device}",
                "-vn",
                "-ac",
                str(self.CHANNELS),
                "-ar",
                str(self.SAMPLE_RATE),
                "-c:a",
                "pcm_s16le",
                "-f",
                "s16le",
                "pipe:1",
            ]

            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
                if os.name == "nt"
                else 0
            )

            try:
                self._process = subprocess.Popen(
                    command,
                    cwd=str(
                        self.project_root
                    ),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=self._log_handle,
                    bufsize=0,
                    creationflags=creationflags,
                )
            except Exception as exc:
                self.stop()

                raise NativeSessionIOError(
                    f"Unable to start VB-CABLE audio capture: {exc}"
                ) from exc

            time.sleep(
                0.35
            )

            if (
                self._process is None
                or self._process.poll() is not None
                or self._process.stdout is None
            ):
                self.stop()

                raise NativeSessionIOError(
                    "VB-CABLE audio capture exited during startup. "
                    "See logs/games/native_audio_alpha.log."
                )

            self._device = device
            self._client_ip = client_ip
            self._client_port = client_port
            self._packets = 0
            self._bytes = 0
            self._send_errors = 0

            self._socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

            self._running.set()

            self._thread = threading.Thread(
                target=self._send_loop,
                name="PrivyHub-Native-Audio",
                daemon=True,
            )
            self._thread.start()

            return self.status()

    def _send_loop(
        self,
    ) -> None:
        process = self._process
        sock = self._socket
        destination = (
            self._client_ip,
            self._client_port,
        )

        if (
            process is None
            or process.stdout is None
            or sock is None
            or destination[0] is None
            or destination[1] is None
        ):
            return

        sequence = 0
        sample_timestamp = 0

        try:
            while self._running.is_set():
                payload = self._read_exact(
                    process.stdout,
                    self.PAYLOAD_BYTES,
                )

                if len(payload) != self.PAYLOAD_BYTES:
                    break

                packet = (
                    self.HEADER.pack(
                        self.MAGIC,
                        self.VERSION,
                        self.CHANNELS,
                        sequence & 0xFFFF,
                        sample_timestamp & 0xFFFFFFFF,
                        self.FRAMES_PER_PACKET,
                    )
                    + payload
                )

                try:
                    sock.sendto(
                        packet,
                        destination,
                    )
                    self._packets += 1
                    self._bytes += len(
                        payload
                    )
                except OSError:
                    self._send_errors += 1

                sequence = (
                    sequence + 1
                ) & 0xFFFF

                sample_timestamp = (
                    sample_timestamp
                    + self.FRAMES_PER_PACKET
                ) & 0xFFFFFFFF
        finally:
            self._running.clear()

    def status(
        self,
    ) -> dict[str, Any]:
        process_active = (
            self._process is not None
            and self._process.poll() is None
        )

        return {
            "active": (
                process_active
                and self._running.is_set()
            ),
            "device": self._device,
            "sample_rate": self.SAMPLE_RATE,
            "channels": self.CHANNELS,
            "format": "pcm_s16le",
            "packet_ms": 5,
            "packets_sent": self._packets,
            "payload_bytes_sent": self._bytes,
            "send_errors": self._send_errors,
            "port": self._client_port,
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

        self._kill_process(
            self._process
        )
        self._process = None

        thread = self._thread
        self._thread = None

        if (
            thread is not None
            and thread is not threading.current_thread()
        ):
            thread.join(
                timeout=1
            )

        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass

        self._log_handle = None
        self._client_ip = None
        self._client_port = None


class NativeControllerBridge:
    MAGIC = b"PHI1"
    VERSION = 1
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
        self._gamepad = None
        self._client_ip: str | None = None
        self._port: int | None = None

        self._packets = 0
        self._lost_packets = 0
        self._rejected_packets = 0
        self._bad_packets = 0
        self._updates = 0
        self._last_sequence: int | None = None
        self._last_packet_at = 0.0
        self._neutralized = True

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

    def start(
        self,
        client_ip: str,
        port: int,
    ) -> dict[str, Any]:
        self.stop()

        vg = self._load_vgamepad()

        try:
            gamepad = vg.VX360Gamepad()
        except Exception as exc:
            raise NativeSessionIOError(
                "Unable to create the temporary virtual X360 controller. "
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
        self._gamepad = gamepad
        self._client_ip = client_ip
        self._port = int(port)

        self._packets = 0
        self._lost_packets = 0
        self._rejected_packets = 0
        self._bad_packets = 0
        self._updates = 0
        self._last_sequence = None
        self._last_packet_at = 0.0
        self._neutralized = True

        self._running.set()

        self._thread = threading.Thread(
            target=self._receive_loop,
            args=(vg,),
            name="PrivyHub-Native-Controller",
            daemon=True,
        )
        self._thread.start()

        return self.status()

    def _neutralize(
        self,
    ) -> None:
        gamepad = self._gamepad

        if gamepad is None:
            return

        try:
            gamepad.reset()
            gamepad.update()
            self._neutralized = True
        except Exception:
            pass

    def _apply_report(
        self,
        buttons: int,
        lx: int,
        ly: int,
        rx: int,
        ry: int,
        lt: int,
        rt: int,
    ) -> None:
        gamepad = self._gamepad

        if gamepad is None:
            return

        # vgamepad deliberately exposes the report for advanced/full-state
        # use. One packet therefore becomes one ViGEm report instead of a
        # burst of per-control changes.
        gamepad.report.wButtons = (
            int(buttons)
            & 0xFFFF
        )

        gamepad.report.bLeftTrigger = (
            self._clamp_trigger(
                lt
            )
        )

        gamepad.report.bRightTrigger = (
            self._clamp_trigger(
                rt
            )
        )

        gamepad.report.sThumbLX = (
            self._clamp_axis(
                lx
            )
        )

        gamepad.report.sThumbLY = (
            self._clamp_axis(
                ly
            )
        )

        gamepad.report.sThumbRX = (
            self._clamp_axis(
                rx
            )
        )

        gamepad.report.sThumbRY = (
            self._clamp_axis(
                ry
            )
        )

        gamepad.update()

        self._updates += 1
        self._neutralized = False

    def _receive_loop(
        self,
        vg,
    ) -> None:
        del vg

        sock = self._socket

        if sock is None:
            return

        while self._running.is_set():
            try:
                data, source = sock.recvfrom(
                    256
                )
            except socket.timeout:
                if (
                    not self._neutralized
                    and self._last_packet_at > 0.0
                    and time.monotonic()
                    - self._last_packet_at
                    > 0.25
                ):
                    self._neutralize()

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
                or player != 0
            ):
                self._bad_packets += 1
                continue

            if self._last_sequence is not None:
                expected = (
                    self._last_sequence
                    + 1
                ) & 0xFFFFFFFF

                if sequence != expected:
                    missing = (
                        sequence - expected
                    ) & 0xFFFFFFFF

                    if missing < 0x80000000:
                        self._lost_packets += (
                            missing
                        )

            self._last_sequence = sequence
            self._packets += 1
            self._last_packet_at = (
                time.monotonic()
            )

            try:
                self._apply_report(
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
                and self._gamepad is not None
            ),
            "sink": "vigem_x360_alpha",
            "transport": "udp_full_state",
            "port": self._port,
            "packets_received": self._packets,
            "lost_packets": self._lost_packets,
            "rejected_packets": self._rejected_packets,
            "bad_packets": self._bad_packets,
            "vigem_updates": self._updates,
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

        self._neutralize()
        self._gamepad = None
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

    def start(
        self,
        ffmpeg: Path,
        client_ip: str,
        audio_port: int,
        input_port: int,
    ) -> dict[str, Any]:
        self.stop()

        self._audio_error = None
        self._controller_error = None

        try:
            self.controller.start(
                client_ip=client_ip,
                port=input_port,
            )
        except Exception as exc:
            self._controller_error = str(
                exc
            )

        try:
            self.audio.start(
                ffmpeg=ffmpeg,
                client_ip=client_ip,
                client_port=audio_port,
            )
        except Exception as exc:
            self._audio_error = str(
                exc
            )

        return self.status()

    def status(
        self,
    ) -> dict[str, Any]:
        audio = self.audio.status()
        controller = self.controller.status()

        if self._audio_error:
            audio["error"] = (
                self._audio_error
            )

        if self._controller_error:
            controller["error"] = (
                self._controller_error
            )

        return {
            "audio": audio,
            "controller": controller,
        }

    def stop(
        self,
    ) -> None:
        self.audio.stop()
        self.controller.stop()
