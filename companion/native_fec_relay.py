from __future__ import annotations

import json
import os
import socket
import struct
import threading
import time

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from games.log_rotation import append_line


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

# D-BASE-P3, diagnostic, DEFAULT OFF. Read from the environment at start().
# 0 (or unset) is today's behaviour byte for byte: forward on arrival.
PACING_ENV = "PRIVYHUB_FEC_PACING_US"

# A frame's packets must all be on the wire within this budget, measured from
# the arrival of the frame's first packet — so the queueing wait for the
# marker is inside it, and the worst added latency is the budget. At 60 fps
# the frame interval is 16.7 ms, so 8 ms stays under half a frame.
PACING_FRAME_BUDGET_US = 8_000

# Achieved-spacing histogram: 5 us buckets to 4 ms, plus one overflow bucket.
# A histogram rather than a sample list so a long session stays bounded.
SPACING_BUCKET_US = 5
SPACING_BUCKETS = 800

# D-BASE-P5, diagnostic, always on: how many packets each encoded frame is.
# `O1` located the loss at a per-frame micro-burst meeting a queue but could
# not say which queue, and nothing on the host recorded how big the bursts
# actually are. This counts them. It does not pace, delay, reorder, drop or
# otherwise touch a byte on the forwarding path.
#
# A frame is the run of packets sharing one RTP timestamp, ended by the
# marker packet. A frame that ends because the timestamp changed instead is
# counted too, and separately, as `unmarked_frames` -- an encoder restart
# mid-frame is the usual cause and reading it as a normal frame would
# understate the large ones.
FRAME_SIZE_SCHEMA = "privyhub_native_frame_sizes_v1"

# One bucket per second of relay wall time, 1,800 s of them: half an hour,
# which covers a 20-minute session with room either side.
FRAME_BUCKET_SECONDS = 1_800

# The two thresholds the record reports counts for. 40 is a little over
# twice D-BASE-P3's measured mean frame of 15.85 packets; 80 is where P3's
# 8 ms pacing budget has already given up (it clamps above 53 at 150 us).
FRAME_LARGE_PACKETS = 40
FRAME_HUGE_PACKETS = 80

# Packets-per-frame histogram, so p50/p90/p99 are exact over a whole
# session without keeping a sample per frame. Index N holds frames of
# exactly N packets; the last index is "N or more".
FRAME_HIST_BUCKETS = 512

# Matches the heartbeat log: 4 MiB, three rotations, into the sibling
# `stream_log_archive/` that `tools/diagnostic_retention.py` already bounds.
# One line per second of streaming at ~190 bytes is ~680 KB/h.
MAX_FRAME_LOG_BYTES = 4 * 1024 * 1024
KEEP_FRAME_LOG = 3

# D-BASE-P6. A frame's size in PAYLOAD BYTES, not just packets, because
# that is the unit `h264_vaapi -max_frame_size` is set in and a cap can
# only be checked against the thing it caps. Bytes are the sum of the RTP
# payload lengths sharing one timestamp -- no RTP headers, no FEC parity.
# 1 KiB buckets to 256 KiB plus an overflow bucket; at `pkt_size=1200` a
# 207-packet frame is ~246 KB, so the range covers the observed maximum.
FRAME_BYTE_BUCKET = 1024
FRAME_BYTE_BUCKETS = 256

# The cap the run is testing, in bytes, so `frames_over_cap` is recorded
# per second beside the distribution. Read from the environment at
# start(), like the pacing knob; 0 or unset means no cap is under test and
# the counter stays at 0. This does NOT set anything on the encoder -- it
# is the yardstick the encoder is measured against.
FRAME_BYTE_CAP_ENV = "PRIVYHUB_FRAME_BYTE_CAP"


def _utc(
    epoch_seconds: float,
) -> str:
    return (
        datetime.fromtimestamp(
            epoch_seconds,
            timezone.utc,
        )
        .isoformat(
            timespec="milliseconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


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
        pacing_us: int | None = None,
        frame_size_log: Path | None = None,
    ) -> None:
        self.local_port = int(local_port)
        self.group_size = int(group_size)

        # D-BASE-P5. None keeps the counters in memory only; a path also
        # writes one JSON line per second. The counting is identical either
        # way, so a relay constructed without a path (a test) still counts.
        self.frame_size_log = (
            Path(frame_size_log)
            if frame_size_log is not None
            else None
        )

        # D-BASE-P3. An explicit argument wins (tests); otherwise the
        # environment, re-read on every start() so a companion restart is the
        # only thing needed to change arms.
        self._pacing_override = pacing_us
        self.pacing_us = self._configured_pacing_us()

        self._lock = threading.RLock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._recv_socket: socket.socket | None = None
        self._send_socket: socket.socket | None = None
        self._client: tuple[str, int] | None = None
        self._group: list[_RtpData] = []
        self._group_timestamp: int | None = None

        # D-BASE-P3 pacing state.
        self._pace_cv = threading.Condition(self._lock)
        self._pace_queue: deque[tuple[list[tuple[bytes, bool]], int]] = deque()
        self._pace_thread: threading.Thread | None = None
        self._pending: list[tuple[bytes, bool]] = []
        self._pending_first_ns = 0
        self._spacing_hist = [0] * (SPACING_BUCKETS + 1)
        self._spacing_samples = 0
        self._paced_frames = 0
        self._paced_packets = 0
        self._pacing_clamped_frames = 0
        self._pacing_late_frames = 0
        self._last_spacing_us = 0.0
        self._max_start_delay_us = 0.0
        self._pace_queue_max = 0

        self._rtp_packets = 0
        self._rtp_bytes = 0
        self._parity_packets = 0
        self._parity_bytes = 0
        self._groups = 0
        self._skipped_packets = 0
        self._send_errors = 0
        self._send_calls = 0
        self._sent_bytes = 0
        self._send_call_total_ns = 0
        self._send_call_max_ns = 0

        # D-BASE-P5 frame-size state, extended with bytes by D-BASE-P6.
        self._frame_timestamp: int | None = None
        self._frame_packets = 0
        self._frame_payload_bytes = 0
        self.frame_byte_cap = self._configured_frame_byte_cap()
        self._frame_byte_hist = [0] * (FRAME_BYTE_BUCKETS + 1)
        self._frame_bytes_total = 0
        self._frame_max_bytes = 0
        self._frame_max_bytes_at: str | None = None
        self._frames_over_cap = 0
        self._frame_bucket: dict[str, Any] | None = None
        self._frame_buckets: deque[dict[str, Any]] = deque(
            maxlen=FRAME_BUCKET_SECONDS
        )
        self._frame_unwritten: deque[dict[str, Any]] = deque()
        self._frame_hist = [0] * (FRAME_HIST_BUCKETS + 1)
        self._frames_total = 0
        self._frame_packets_total = 0
        self._frame_max_packets = 0
        self._frame_max_at: str | None = None
        self._frames_large = 0
        self._frames_huge = 0
        self._frames_unmarked = 0
        self._frame_log_lines = 0
        self._frame_log_errors = 0
        self._frame_log_rotations = 0
        self._frame_thread: threading.Thread | None = None

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

            # D-BASE-P3: re-read the knob, so the arm is whatever the
            # companion process was started with.
            self.pacing_us = self._configured_pacing_us()
            self._pace_queue.clear()
            self._pending = []
            self._pending_first_ns = 0
            self._spacing_hist = [0] * (SPACING_BUCKETS + 1)
            self._spacing_samples = 0
            self._paced_frames = 0
            self._paced_packets = 0
            self._pacing_clamped_frames = 0
            self._pacing_late_frames = 0
            self._last_spacing_us = 0.0
            self._max_start_delay_us = 0.0
            self._pace_queue_max = 0

            self._rtp_packets = 0
            self._rtp_bytes = 0
            self._parity_packets = 0
            self._parity_bytes = 0
            self._groups = 0
            self._skipped_packets = 0
            self._send_errors = 0
            self._send_calls = 0
            self._sent_bytes = 0
            self._send_call_total_ns = 0
            self._send_call_max_ns = 0

            # D-BASE-P5: per-session, like every other counter here.
            self._frame_timestamp = None
            self._frame_packets = 0
            self._frame_payload_bytes = 0
            self.frame_byte_cap = self._configured_frame_byte_cap()
            self._frame_byte_hist = [0] * (FRAME_BYTE_BUCKETS + 1)
            self._frame_bytes_total = 0
            self._frame_max_bytes = 0
            self._frame_max_bytes_at = None
            self._frames_over_cap = 0
            self._frame_bucket = None
            self._frame_buckets.clear()
            self._frame_unwritten.clear()
            self._frame_hist = [0] * (FRAME_HIST_BUCKETS + 1)
            self._frames_total = 0
            self._frame_packets_total = 0
            self._frame_max_packets = 0
            self._frame_max_at = None
            self._frames_large = 0
            self._frames_huge = 0
            self._frames_unmarked = 0
            self._frame_log_lines = 0
            self._frame_log_errors = 0
            self._frame_log_rotations = 0

            self._running = True
            self._thread = threading.Thread(
                target=self._run,
                name="PrivyHub-Native-FEC",
                daemon=True,
            )
            self._thread.start()

            # D-BASE-P5: the per-second line is written from here, never
            # from the receive thread, so the forwarding path never waits
            # on the filesystem.
            self._frame_thread = threading.Thread(
                target=self._frame_log_run,
                name="PrivyHub-Native-FEC-Frames",
                daemon=True,
            )
            self._frame_thread.start()

            if self.pacing_us > 0:
                self._pace_thread = threading.Thread(
                    target=self._pace_run,
                    name="PrivyHub-Native-FEC-Pacer",
                    daemon=True,
                )
                self._pace_thread.start()

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

            pace_thread = self._pace_thread
            self._pace_thread = None

            frame_thread = self._frame_thread
            self._frame_thread = None

            # D-BASE-P5: close the frame in flight and the open bucket, so
            # the last second of a session is on disk like every other.
            self._close_frame_locked(
                time.time(),
                marked=False,
            )
            self._roll_frame_bucket_locked()

            self._pace_queue.clear()
            self._pending = []
            self._pace_cv.notify_all()

        if (
            thread is not None
            and thread is not threading.current_thread()
        ):
            thread.join(
                timeout=1.0
            )

        if (
            pace_thread is not None
            and pace_thread is not threading.current_thread()
        ):
            pace_thread.join(
                timeout=1.0
            )

        if (
            frame_thread is not None
            and frame_thread is not threading.current_thread()
        ):
            frame_thread.join(
                timeout=1.0
            )

        # Whatever the writer had not reached yet, including the tail just
        # closed above.
        self._flush_frame_log()

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
                "send_calls": self._send_calls,
                "sent_bytes": self._sent_bytes,
                "send_call_total_us": (
                    self._send_call_total_ns / 1_000.0
                ),
                "send_call_max_us": (
                    self._send_call_max_ns / 1_000.0
                ),
                "pacing": self._pacing_status_locked(),
                "frame_sizes": self._frame_size_status_locked(),
            }

    def pacing_status(self) -> dict[str, Any]:
        """D-BASE-P3: the pacing block alone, for the session log's host
        metadata. Same numbers as `status()["pacing"]`."""

        with self._lock:
            return self._pacing_status_locked()

    def _pacing_status_locked(self) -> dict[str, Any]:
        return {
            "enabled": self.pacing_us > 0,
            "configured_us": self.pacing_us,
            "source": PACING_ENV,
            "frame_budget_us": PACING_FRAME_BUDGET_US,
            "paced_frames": self._paced_frames,
            "paced_packets": self._paced_packets,
            "clamped_frames": self._pacing_clamped_frames,
            "late_frames": self._pacing_late_frames,
            "last_spacing_us": round(
                self._last_spacing_us,
                3,
            ),
            "achieved_spacing_samples": self._spacing_samples,
            "achieved_spacing_p50_us": (
                self._spacing_percentile_locked(0.50)
            ),
            "achieved_spacing_p99_us": (
                self._spacing_percentile_locked(0.99)
            ),
            "max_start_delay_us": round(
                self._max_start_delay_us,
                3,
            ),
            "queue_depth": len(self._pace_queue),
            "max_queue_depth": self._pace_queue_max,
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
                # D-BASE-P3: a frame whose marker never arrived (encoder
                # restart mid-frame) must not sit in the pending buffer.
                if self.pacing_us > 0:
                    with self._lock:
                        self._flush_pending_locked()
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

        # D-BASE-P5: counting only, and before the pacing branch so both
        # arms are measured the same way. An unparseable packet is not
        # attributed to a frame -- it has no timestamp to attribute it to.
        if parsed is not None:
            self._note_frame_packet(
                parsed
            )

        if self.pacing_us > 0:
            self._handle_rtp_paced(
                packet,
                parsed,
            )
            return

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

    # ---- D-BASE-P5: frame size ---------------------------------------
    #
    # Counting only. Nothing below forwards, delays, drops or inspects a
    # payload; it reads the RTP timestamp and marker bit the parser has
    # already extracted for FEC grouping.

    def _note_frame_packet(
        self,
        parsed: _RtpData,
    ) -> None:
        now = time.time()

        with self._lock:
            if (
                self._frame_timestamp is not None
                and parsed.timestamp != self._frame_timestamp
            ):
                # The previous frame's marker never arrived. Close it and
                # say so rather than folding its packets into this one.
                self._close_frame_locked(
                    now,
                    marked=False,
                )

            self._frame_timestamp = parsed.timestamp
            self._frame_packets += 1
            self._frame_payload_bytes += len(parsed.payload)

            if parsed.marker:
                self._close_frame_locked(
                    now,
                    marked=True,
                )

    def _close_frame_locked(
        self,
        now: float,
        *,
        marked: bool,
    ) -> None:
        packets = self._frame_packets
        payload_bytes = self._frame_payload_bytes

        self._frame_packets = 0
        self._frame_payload_bytes = 0
        self._frame_timestamp = None

        if packets <= 0:
            return

        second = int(now)
        bucket = self._frame_bucket

        if (
            bucket is not None
            and bucket["t"] != second
        ):
            self._roll_frame_bucket_locked()
            bucket = None

        if bucket is None:
            bucket = {
                "t": second,
                "frames": 0,
                "packets": 0,
                "max_packets": 0,
                "max_at_utc": None,
                "frames_ge_40": 0,
                "frames_ge_80": 0,
                "unmarked_frames": 0,
                # D-BASE-P6: the same frames measured in payload bytes.
                "payload_bytes": 0,
                "max_bytes": 0,
                "max_bytes_at_utc": None,
                "frames_over_cap": 0,
            }
            self._frame_bucket = bucket

        bucket["frames"] += 1
        bucket["packets"] += packets
        bucket["payload_bytes"] += payload_bytes

        if packets > bucket["max_packets"]:
            bucket["max_packets"] = packets
            bucket["max_at_utc"] = _utc(now)

        if payload_bytes > bucket["max_bytes"]:
            bucket["max_bytes"] = payload_bytes
            bucket["max_bytes_at_utc"] = _utc(now)

        if self.frame_byte_cap > 0 and payload_bytes > self.frame_byte_cap:
            bucket["frames_over_cap"] += 1
            self._frames_over_cap += 1

        if packets >= FRAME_LARGE_PACKETS:
            bucket["frames_ge_40"] += 1
            self._frames_large += 1

        if packets >= FRAME_HUGE_PACKETS:
            bucket["frames_ge_80"] += 1
            self._frames_huge += 1

        if not marked:
            bucket["unmarked_frames"] += 1
            self._frames_unmarked += 1

        self._frames_total += 1
        self._frame_packets_total += packets
        self._frame_bytes_total += payload_bytes
        self._frame_hist[
            min(packets, FRAME_HIST_BUCKETS)
        ] += 1
        self._frame_byte_hist[
            min(
                payload_bytes // FRAME_BYTE_BUCKET,
                FRAME_BYTE_BUCKETS,
            )
        ] += 1

        if packets > self._frame_max_packets:
            self._frame_max_packets = packets
            self._frame_max_at = _utc(now)

        if payload_bytes > self._frame_max_bytes:
            self._frame_max_bytes = payload_bytes
            self._frame_max_bytes_at = _utc(now)

    def _roll_frame_bucket_locked(self) -> None:
        bucket = self._frame_bucket

        if bucket is None:
            return

        self._frame_bucket = None

        bucket["mean_packets"] = round(
            bucket["packets"] / bucket["frames"],
            3,
        ) if bucket["frames"] else 0.0
        bucket["mean_bytes"] = int(
            bucket["payload_bytes"] / bucket["frames"]
        ) if bucket["frames"] else 0

        self._frame_buckets.append(bucket)
        self._frame_unwritten.append(bucket)

    def _frame_log_run(self) -> None:
        """Close the previous second's bucket and write it out.

        Runs at 1 Hz on its own thread. A bucket is only closed once the
        wall clock has passed its second, so a line is never written while
        frames can still land in it.
        """

        while True:
            with self._lock:
                if not self._running:
                    return

                bucket = self._frame_bucket

                if (
                    bucket is not None
                    and bucket["t"] < int(time.time())
                ):
                    self._roll_frame_bucket_locked()

            self._flush_frame_log()

            time.sleep(0.5)

    def _flush_frame_log(self) -> None:
        path = self.frame_size_log

        with self._lock:
            pending = list(self._frame_unwritten)
            self._frame_unwritten.clear()

        if path is None or not pending:
            return

        for bucket in pending:
            record = {
                "schema": FRAME_SIZE_SCHEMA,
                "at_utc": _utc(bucket["t"]),
            }
            record.update(bucket)

            try:
                rotated = append_line(
                    path,
                    json.dumps(
                        record,
                        sort_keys=False,
                    ),
                    max_bytes=MAX_FRAME_LOG_BYTES,
                    keep=KEEP_FRAME_LOG,
                )
            except OSError:
                with self._lock:
                    self._frame_log_errors += 1
                continue

            with self._lock:
                self._frame_log_lines += 1

                if rotated:
                    self._frame_log_rotations += 1

    def _frame_percentile_locked(
        self,
        fraction: float,
    ) -> int | None:
        total = self._frames_total

        if total <= 0:
            return None

        target = fraction * total
        seen = 0

        for packets, count in enumerate(self._frame_hist):
            seen += count

            if seen >= target:
                return packets

        return None

    def _configured_frame_byte_cap(self) -> int:
        raw = os.environ.get(FRAME_BYTE_CAP_ENV, "")

        try:
            value = int(str(raw).strip() or 0)
        except (TypeError, ValueError):
            return 0

        return value if value > 0 else 0

    def _frame_byte_percentile_locked(
        self,
        fraction: float,
    ) -> int | None:
        """The upper edge of the 1 KiB bucket holding this percentile.

        Reported as an upper bound rather than interpolated: the histogram
        knows the bucket, not the value inside it, and a fabricated
        interpolation would read as a measurement.
        """

        total = self._frames_total

        if total <= 0:
            return None

        target = fraction * total
        seen = 0

        for index, count in enumerate(self._frame_byte_hist):
            seen += count

            if seen >= target:
                return (index + 1) * FRAME_BYTE_BUCKET

        return None

    def frame_size_status(self) -> dict[str, Any]:
        """D-BASE-P5: the frame-size block alone."""

        with self._lock:
            return self._frame_size_status_locked()

    def _frame_size_status_locked(self) -> dict[str, Any]:
        frames = self._frames_total

        return {
            "schema": FRAME_SIZE_SCHEMA,
            "frames": frames,
            "packets": self._frame_packets_total,
            "mean_packets": (
                round(
                    self._frame_packets_total / frames,
                    3,
                )
                if frames
                else None
            ),
            "p50_packets": self._frame_percentile_locked(0.50),
            "p90_packets": self._frame_percentile_locked(0.90),
            "p99_packets": self._frame_percentile_locked(0.99),
            "max_packets": (
                self._frame_max_packets or None
            ),
            "max_at_utc": self._frame_max_at,
            # D-BASE-P6: the same distribution in payload bytes, the unit
            # `-max_frame_size` is set in. Percentiles are the UPPER EDGE
            # of a 1 KiB bucket, not an interpolated value.
            "payload_bytes": self._frame_bytes_total,
            "mean_bytes": (
                int(self._frame_bytes_total / frames)
                if frames
                else None
            ),
            "p50_bytes": self._frame_byte_percentile_locked(0.50),
            "p90_bytes": self._frame_byte_percentile_locked(0.90),
            "p99_bytes": self._frame_byte_percentile_locked(0.99),
            "max_bytes": (
                self._frame_max_bytes or None
            ),
            "max_bytes_at_utc": self._frame_max_bytes_at,
            "bytes_per_packet": (
                round(self._frame_bytes_total / self._frame_packets_total, 2)
                if self._frame_packets_total
                else None
            ),
            "byte_cap": self.frame_byte_cap or None,
            "byte_cap_source": FRAME_BYTE_CAP_ENV,
            "frames_over_cap": self._frames_over_cap,
            "byte_bucket": FRAME_BYTE_BUCKET,
            "frames_ge_40": self._frames_large,
            "frames_ge_80": self._frames_huge,
            "unmarked_frames": self._frames_unmarked,
            "large_threshold": FRAME_LARGE_PACKETS,
            "huge_threshold": FRAME_HUGE_PACKETS,
            "log_path": (
                self.frame_size_log.as_posix()
                if self.frame_size_log is not None
                else None
            ),
            "log_lines": self._frame_log_lines,
            "log_rotations": self._frame_log_rotations,
            "log_errors": self._frame_log_errors,
            "bucket_seconds": FRAME_BUCKET_SECONDS,
            # The whole-session distributions, so an arm's shape is
            # recoverable without re-reading every per-second row.
            "packet_histogram": list(self._frame_hist),
            "byte_histogram": list(self._frame_byte_hist),
            "buckets": list(self._frame_buckets),
        }

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

        self._emit_locked(
            fec_packet,
            parity=True,
        )

    def _handle_rtp_paced(
        self,
        packet: bytes,
        parsed: "_RtpData | None",
    ) -> None:
        """D-BASE-P3. Nothing goes out on arrival: a frame's packets are
        accumulated in arrival order, parity inserted directly after the group
        it protects, and the whole frame handed to the sender thread when its
        marker lands. Byte-for-byte the same packets in the same order as the
        unpaced path — only their spacing differs."""

        with self._lock:
            if parsed is None:
                # Unsupported header shape: close the open frame, then pass
                # this packet straight through, still in order.
                self._flush_pending_locked()
                self._pending = [(packet, False)]
                self._pending_first_ns = time.perf_counter_ns()
                self._flush_pending_locked()
                self._skipped_packets += 1
                self._group = []
                self._group_timestamp = None
                return

            self._rtp_packets += 1
            self._rtp_bytes += len(packet)

            if (
                self._group_timestamp is not None
                and parsed.timestamp != self._group_timestamp
            ):
                # A new frame began without a marker on the old one.
                self._emit_group_locked()
                self._group = []
                self._group_timestamp = None
                self._flush_pending_locked()

            if not self._pending:
                self._pending_first_ns = time.perf_counter_ns()

            self._pending.append(
                (packet, False)
            )

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

            if parsed.marker:
                self._flush_pending_locked()

    def _emit_locked(
        self,
        packet: bytes,
        parity: bool,
    ) -> None:
        if self.pacing_us > 0:
            self._pending.append(
                (packet, parity)
            )
            return

        self._send(
            packet,
            parity=parity,
        )

    def _flush_pending_locked(self) -> None:
        if not self._pending:
            return

        self._pace_queue.append(
            (
                self._pending,
                self._pending_first_ns,
            )
        )
        self._pace_queue_max = max(
            self._pace_queue_max,
            len(self._pace_queue),
        )
        self._pending = []
        self._pending_first_ns = 0
        self._pace_cv.notify()

    def _pace_run(self) -> None:
        while True:
            with self._lock:
                while (
                    self._running
                    and not self._pace_queue
                ):
                    self._pace_cv.wait(
                        0.25
                    )

                if not self._running:
                    return

                frame, first_ns = self._pace_queue.popleft()
                pacing_us = self.pacing_us

            self._send_frame_paced(
                frame,
                first_ns,
                pacing_us,
            )

    def _send_frame_paced(
        self,
        frame: list[tuple[bytes, bool]],
        first_ns: int,
        pacing_us: int,
    ) -> None:
        count = len(frame)

        if count <= 0:
            return

        # The schedule is anchored on the moment this thread actually starts
        # the frame, not on the first packet's arrival: the frame is only
        # queued once its marker lands, and waking this thread costs more
        # again, so anchoring on arrival would leave the first packets already
        # due and send them back to back — measured, that put the achieved
        # p50 at 7.5 us instead of 150.
        start_ns = time.perf_counter_ns()
        start_delay_us = (
            start_ns - first_ns
        ) / 1_000.0

        # The hard cap, as specified: PACING_US is clamped to
        # frame-budget / packets-in-frame, so a large frame cannot push its
        # own tail past the budget. The budget is still measured from the
        # first packet's ARRIVAL, so whatever accumulating and waking cost is
        # spent above comes out of it and the latency bound holds.
        spacing_us = float(pacing_us)
        clamped = False
        remaining_us = max(
            0.0,
            PACING_FRAME_BUDGET_US - start_delay_us,
        )
        max_spacing_us = remaining_us / count

        if spacing_us > max_spacing_us:
            spacing_us = max_spacing_us
            clamped = True

        previous_ns = 0

        for index, (packet, parity) in enumerate(frame):
            if index:
                self._wait_until(
                    start_ns
                    + int(
                        index * spacing_us * 1_000.0
                    )
                )

            now_ns = time.perf_counter_ns()

            if index:
                self._record_spacing(
                    now_ns - previous_ns
                )

            previous_ns = now_ns

            self._send(
                packet,
                parity=parity,
            )

        late = (
            time.perf_counter_ns() - first_ns
        ) > (
            PACING_FRAME_BUDGET_US * 1_000
        )

        with self._lock:
            self._paced_frames += 1
            self._paced_packets += count
            self._last_spacing_us = spacing_us
            self._max_start_delay_us = max(
                self._max_start_delay_us,
                start_delay_us,
            )

            if clamped:
                self._pacing_clamped_frames += 1

            if late:
                self._pacing_late_frames += 1

    @staticmethod
    def _wait_until(
        target_ns: int,
    ) -> None:
        """Measured on this host 2026-09-21: `time.sleep` carries a ~55 us
        floor of overshoot — `sleep(150 us)` returns after ~205 us — so it
        cannot place a 150 us gap. Sleep only the bulk of a long wait and
        busy-wait the tail, which lands within ~0.3 us."""

        remaining_ns = target_ns - time.perf_counter_ns()

        if remaining_ns <= 0:
            return

        if remaining_ns > 300_000:
            time.sleep(
                (remaining_ns - 200_000)
                / 1_000_000_000.0
            )

        while time.perf_counter_ns() < target_ns:
            pass

    def _record_spacing(
        self,
        gap_ns: int,
    ) -> None:
        bucket = int(
            gap_ns
            // (SPACING_BUCKET_US * 1_000)
        )

        if bucket < 0:
            bucket = 0
        elif bucket > SPACING_BUCKETS:
            bucket = SPACING_BUCKETS

        with self._lock:
            self._spacing_hist[bucket] += 1
            self._spacing_samples += 1

    def _spacing_percentile_locked(
        self,
        fraction: float,
    ) -> float | None:
        total = self._spacing_samples

        if total <= 0:
            return None

        want = fraction * total
        seen = 0

        for bucket, hits in enumerate(self._spacing_hist):
            if not hits:
                continue

            seen += hits

            if seen >= want:
                if bucket >= SPACING_BUCKETS:
                    # Overflow bucket: report its floor, not a fiction.
                    return float(
                        SPACING_BUCKETS * SPACING_BUCKET_US
                    )

                # Bucket midpoint, to 5 us resolution.
                return (
                    bucket * SPACING_BUCKET_US
                ) + (
                    SPACING_BUCKET_US / 2.0
                )

        return None

    @staticmethod
    def _configured_pacing_us_from_env() -> int:
        raw = os.environ.get(
            PACING_ENV,
            "",
        ).strip()

        if not raw:
            return 0

        try:
            value = int(raw)
        except ValueError:
            return 0

        return value if value > 0 else 0

    def _configured_pacing_us(self) -> int:
        if self._pacing_override is not None:
            value = int(self._pacing_override)
            return value if value > 0 else 0

        return self._configured_pacing_us_from_env()

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

        started_ns = time.perf_counter_ns()

        try:
            sent = send_socket.sendto(
                packet,
                client,
            )
            duration_ns = max(
                0,
                time.perf_counter_ns() - started_ns,
            )

            with self._lock:
                self._send_calls += 1
                self._sent_bytes += int(sent)
                self._send_call_total_ns += duration_ns
                self._send_call_max_ns = max(
                    self._send_call_max_ns,
                    duration_ns,
                )

                if parity:
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
