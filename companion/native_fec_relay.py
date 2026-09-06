from __future__ import annotations

import socket
import struct
import threading

from dataclasses import dataclass
from typing import Any


FEC_MAGIC = b"PHF1"
FEC_VERSION = 1

# 8 data RTP packets + 1 XOR parity datagram.
DEFAULT_GROUP_SIZE = 8

# FFmpeg sends only to loopback. This relay is the sole sender to the onn.
DEFAULT_LOCAL_PORT = 48110

# Header:
# magic[4], version[1], count[1], base_seq[2], timestamp[4], ssrc[4],
# marker_mask[1], rtp_byte0[1], payload_type[1], length_xor[2], parity_len[2]
FEC_HEADER = struct.Struct("!4sBBHIIBBBHH")


@dataclass
class _RtpData:
    sequence: int
    timestamp: int
    ssrc: int
    marker: bool
    byte0: int
    payload_type: int
    payload: bytes


class NativeVideoFecRelay:
    """Immediate RTP forwarding with small-block XOR parity.

    Original RTP packets are forwarded immediately. Parity is emitted after
    each complete group and after the marker packet of a final partial group.
    The normal no-loss path therefore gains no client-side presentation buffer.
    """

    def __init__(
        self,
        local_port: int = DEFAULT_LOCAL_PORT,
        group_size: int = DEFAULT_GROUP_SIZE,
    ) -> None:
        self.local_port = int(local_port)
        self.group_size = int(group_size)

        self._lock = threading.RLock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._recv_socket: socket.socket | None = None
        self._send_socket: socket.socket | None = None
        self._client: tuple[str, int] | None = None
        self._group: list[_RtpData] = []
        self._group_timestamp: int | None = None

        self._rtp_packets = 0
        self._rtp_bytes = 0
        self._parity_packets = 0
        self._parity_bytes = 0
        self._groups = 0
        self._skipped_packets = 0
        self._send_errors = 0

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def start(
        self,
        client_ip: str,
        client_port: int,
    ) -> None:
        with self._lock:
            self.stop()

            recv_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )
            recv_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_RCVBUF,
                2 * 1024 * 1024,
            )
            recv_socket.bind(
                (
                    "127.0.0.1",
                    self.local_port,
                )
            )
            recv_socket.settimeout(
                0.25
            )

            send_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )
            send_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_SNDBUF,
                2 * 1024 * 1024,
            )

            self._recv_socket = recv_socket
            self._send_socket = send_socket
            self._client = (
                client_ip,
                int(client_port),
            )
            self._group = []
            self._group_timestamp = None

            self._rtp_packets = 0
            self._rtp_bytes = 0
            self._parity_packets = 0
            self._parity_bytes = 0
            self._groups = 0
            self._skipped_packets = 0
            self._send_errors = 0

            self._running = True
            self._thread = threading.Thread(
                target=self._run,
                name="PrivyHub-Native-FEC",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._running = False

            recv_socket = self._recv_socket
            self._recv_socket = None

            if recv_socket is not None:
                try:
                    recv_socket.close()
                except OSError:
                    pass

            thread = self._thread
            self._thread = None

        if (
            thread is not None
            and thread is not threading.current_thread()
        ):
            thread.join(
                timeout=1.0
            )

        with self._lock:
            send_socket = self._send_socket
            self._send_socket = None

            if send_socket is not None:
                try:
                    send_socket.close()
                except OSError:
                    pass

            self._client = None
            self._group = []
            self._group_timestamp = None

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "enabled": True,
                "running": self._running,
                "version": "xor8_1",
                "group_size": self.group_size,
                "local_port": self.local_port,
                "rtp_packets": self._rtp_packets,
                "rtp_bytes": self._rtp_bytes,
                "parity_packets": self._parity_packets,
                "parity_bytes": self._parity_bytes,
                "groups": self._groups,
                "skipped_packets": self._skipped_packets,
                "send_errors": self._send_errors,
            }

    def _run(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    return
                recv_socket = self._recv_socket

            if recv_socket is None:
                return

            try:
                packet, _address = recv_socket.recvfrom(
                    65535
                )
            except socket.timeout:
                continue
            except OSError:
                with self._lock:
                    if self._running:
                        self._running = False
                return

            self._handle_rtp(
                packet
            )

    def _handle_rtp(
        self,
        packet: bytes,
    ) -> None:
        parsed = self._parse_simple_rtp(
            packet
        )

        # Always forward the encoder output immediately. Unsupported RTP header
        # shapes only lose FEC protection; they never stop the live stream.
        self._send(
            packet,
            parity=False,
        )

        if parsed is None:
            with self._lock:
                self._skipped_packets += 1
                self._group = []
                self._group_timestamp = None
            return

        with self._lock:
            self._rtp_packets += 1
            self._rtp_bytes += len(packet)

            if (
                self._group_timestamp is not None
                and parsed.timestamp != self._group_timestamp
            ):
                self._emit_group_locked()
                self._group = []

            if not self._group:
                self._group_timestamp = parsed.timestamp

            self._group.append(
                parsed
            )

            if (
                len(self._group) >= self.group_size
                or parsed.marker
            ):
                self._emit_group_locked()
                self._group = []
                self._group_timestamp = None

    def _emit_group_locked(self) -> None:
        group = self._group

        if not group:
            return

        # Only protect consecutive packets sharing one RTP timestamp and SSRC.
        base = group[0]
        expected = base.sequence

        for item in group:
            if (
                item.sequence != expected
                or item.timestamp != base.timestamp
                or item.ssrc != base.ssrc
                or item.byte0 != base.byte0
                or item.payload_type != base.payload_type
            ):
                self._skipped_packets += len(group)
                return

            expected = (
                expected + 1
            ) & 0xFFFF

        marker_mask = 0
        length_xor = 0
        parity_length = max(
            len(item.payload)
            for item in group
        )

        parity = bytearray(
            parity_length
        )

        for index, item in enumerate(group):
            if item.marker:
                marker_mask |= (
                    1 << index
                )

            payload_length = len(
                item.payload
            )
            length_xor ^= payload_length

            for offset, value in enumerate(
                item.payload
            ):
                parity[offset] ^= value

        header = FEC_HEADER.pack(
            FEC_MAGIC,
            FEC_VERSION,
            len(group),
            base.sequence,
            base.timestamp,
            base.ssrc,
            marker_mask,
            base.byte0,
            base.payload_type,
            length_xor,
            parity_length,
        )

        fec_packet = (
            header +
            bytes(parity)
        )

        self._groups += 1

        self._send(
            fec_packet,
            parity=True,
        )

    def _send(
        self,
        packet: bytes,
        parity: bool,
    ) -> None:
        with self._lock:
            send_socket = self._send_socket
            client = self._client

        if (
            send_socket is None
            or client is None
        ):
            return

        try:
            send_socket.sendto(
                packet,
                client,
            )

            if parity:
                with self._lock:
                    self._parity_packets += 1
                    self._parity_bytes += len(
                        packet
                    )
        except OSError:
            with self._lock:
                self._send_errors += 1

    @staticmethod
    def _parse_simple_rtp(
        packet: bytes,
    ) -> _RtpData | None:
        if len(packet) < 13:
            return None

        byte0 = packet[0]
        version = (
            byte0 >> 6
        ) & 0x03

        if version != 2:
            return None

        # FFmpeg's current native RTP output uses the ordinary 12-byte header.
        # If that changes, fail open to plain forwarding rather than trying to
        # protect a header shape the Android recovery code cannot reconstruct.
        if (
            byte0 & 0x3F
        ) != 0:
            return None

        byte1 = packet[1]
        payload_type = (
            byte1 & 0x7F
        )
        marker = (
            byte1 & 0x80
        ) != 0

        sequence = int.from_bytes(
            packet[2:4],
            "big",
        )
        timestamp = int.from_bytes(
            packet[4:8],
            "big",
        )
        ssrc = int.from_bytes(
            packet[8:12],
            "big",
        )

        payload = packet[12:]

        if not payload:
            return None

        return _RtpData(
            sequence=sequence,
            timestamp=timestamp,
            ssrc=ssrc,
            marker=marker,
            byte0=byte0,
            payload_type=payload_type,
            payload=payload,
        )
