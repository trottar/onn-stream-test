#!/usr/bin/env python3
"""PrivyHub standalone UDP transport laboratory.

This probe intentionally excludes RetroArch, WASAPI, AudioTrack, MediaCodec,
and the production native stream stack. It can send synthetic audio-sized UDP
packets at a fixed cadence and compare host-send timing with Android socket
arrival timing using sequence-correlated CSV logs.
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import json
import math
import os
import socket
import statistics
import struct
import sys
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

MAGIC = b"UTP1"
VERSION = 1
HEADER = struct.Struct("<4sBBHIQQQI")
HEADER_BYTES = HEADER.size
PAYLOAD_BYTES = 960
PACKET_BYTES = HEADER_BYTES + PAYLOAD_BYTES
DEFAULT_PORT = 48120
DEFAULT_INTERVAL_MS = 5.0


def _histogram_ms(intervals_ms: Iterable[float]) -> dict[str, int]:
    bins = Counter({
        "lt_1_ms": 0,
        "1_to_2_ms": 0,
        "2_to_4_ms": 0,
        "4_to_6_ms": 0,
        "6_to_10_ms": 0,
        "10_to_15_ms": 0,
        "15_to_20_ms": 0,
        "20_to_30_ms": 0,
        "ge_30_ms": 0,
    })
    for value in intervals_ms:
        if value < 1.0:
            bins["lt_1_ms"] += 1
        elif value < 2.0:
            bins["1_to_2_ms"] += 1
        elif value < 4.0:
            bins["2_to_4_ms"] += 1
        elif value < 6.0:
            bins["4_to_6_ms"] += 1
        elif value < 10.0:
            bins["6_to_10_ms"] += 1
        elif value < 15.0:
            bins["10_to_15_ms"] += 1
        elif value < 20.0:
            bins["15_to_20_ms"] += 1
        elif value < 30.0:
            bins["20_to_30_ms"] += 1
        else:
            bins["ge_30_ms"] += 1
    result = dict(bins)
    result["lt_2_ms_total"] = result["lt_1_ms"] + result["1_to_2_ms"]
    return result


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * percentile
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return values[low]
    fraction = rank - low
    return values[low] * (1.0 - fraction) + values[high] * fraction


def _timing_summary(values_ms: list[float]) -> dict[str, object]:
    if not values_ms:
        return {
            "count": 0,
            "avg_ms": None,
            "min_ms": None,
            "max_ms": None,
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "histogram": _histogram_ms([]),
        }
    return {
        "count": len(values_ms),
        "avg_ms": statistics.fmean(values_ms),
        "min_ms": min(values_ms),
        "max_ms": max(values_ms),
        "p50_ms": _percentile(values_ms, 0.50),
        "p95_ms": _percentile(values_ms, 0.95),
        "p99_ms": _percentile(values_ms, 0.99),
        "histogram": _histogram_ms(values_ms),
    }


@contextmanager
def _windows_timer_resolution():
    """Request 1 ms Windows timer resolution for the duration of the probe."""
    winmm = None
    enabled = False
    if os.name == "nt":
        try:
            winmm = ctypes.WinDLL("winmm")
            enabled = winmm.timeBeginPeriod(1) == 0
        except Exception:
            enabled = False
    try:
        yield enabled
    finally:
        if enabled and winmm is not None:
            try:
                winmm.timeEndPeriod(1)
            except Exception:
                pass


def _wait_until_ns(deadline_ns: int) -> None:
    """Hybrid wait: sleep most of the interval, then yield/spin near deadline."""
    while True:
        now = time.perf_counter_ns()
        remaining = deadline_ns - now
        if remaining <= 0:
            return
        if remaining > 1_000_000:
            time.sleep((remaining - 500_000) / 1_000_000_000)
        elif remaining > 150_000:
            time.sleep(0)
        else:
            # Deliberately short spin only in the final ~150 us.
            pass


def send_probe(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "host_packets.csv"
    summary_path = output_dir / "host_summary.json"

    interval_ns = int(round(args.interval_ms * 1_000_000.0))
    planned_packets = int(round(args.duration_seconds * 1000.0 / args.interval_ms))
    if planned_packets <= 0:
        raise SystemExit("duration/interval produced zero packets")

    payload = bytes((i % 251 for i in range(PAYLOAD_BYTES)))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    if args.send_buffer_bytes > 0:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, args.send_buffer_bytes)
    actual_send_buffer = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)

    rows: list[dict[str, object]] = []
    start_wall_ns = time.time_ns()
    with _windows_timer_resolution() as timer_resolution_requested:
        first_deadline_ns = time.perf_counter_ns() + 250_000_000
        for sequence in range(planned_packets):
            intended_deadline_ns = first_deadline_ns + sequence * interval_ns
            _wait_until_ns(intended_deadline_ns)

            packet_stamp_ns = time.perf_counter_ns()
            host_wall_ns = time.time_ns()
            header = HEADER.pack(
                MAGIC,
                VERSION,
                0,
                HEADER_BYTES,
                sequence & 0xFFFFFFFF,
                intended_deadline_ns,
                packet_stamp_ns,
                host_wall_ns,
                PAYLOAD_BYTES,
            )
            packet = header + payload

            send_call_start_ns = time.perf_counter_ns()
            status = "sent"
            bytes_sent = 0
            error_text = ""
            try:
                bytes_sent = sock.sendto(packet, (args.target, args.port))
            except BlockingIOError as exc:
                status = "would_block"
                error_text = str(exc)
            except OSError as exc:
                if getattr(exc, "winerror", None) == 10035:
                    status = "would_block"
                else:
                    status = "error"
                error_text = str(exc)
            send_call_end_ns = time.perf_counter_ns()

            rows.append({
                "sequence": sequence,
                "intended_deadline_ns": intended_deadline_ns,
                "packet_stamp_ns": packet_stamp_ns,
                "host_wall_ns": host_wall_ns,
                "send_call_start_ns": send_call_start_ns,
                "send_call_end_ns": send_call_end_ns,
                "send_call_duration_us": (send_call_end_ns - send_call_start_ns) / 1000.0,
                "pacing_lateness_us": (send_call_start_ns - intended_deadline_ns) / 1000.0,
                "status": status,
                "bytes_sent": bytes_sent,
                "error": error_text,
            })

    sock.close()
    end_wall_ns = time.time_ns()

    fieldnames = [
        "sequence",
        "intended_deadline_ns",
        "packet_stamp_ns",
        "host_wall_ns",
        "send_call_start_ns",
        "send_call_end_ns",
        "send_call_duration_us",
        "pacing_lateness_us",
        "status",
        "bytes_sent",
        "error",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    successful = [row for row in rows if row["status"] == "sent"]
    send_intervals_ms = [
        (int(successful[i]["send_call_start_ns"]) - int(successful[i - 1]["send_call_start_ns"])) / 1_000_000.0
        for i in range(1, len(successful))
    ]
    send_durations_us = [float(row["send_call_duration_us"]) for row in rows]
    pacing_lateness_us = [float(row["pacing_lateness_us"]) for row in rows]
    statuses = Counter(str(row["status"]) for row in rows)

    summary = {
        "probe": "PrivyHub UDP transport laboratory",
        "format_version": 1,
        "packet_magic": MAGIC.decode("ascii"),
        "packet_bytes": PACKET_BYTES,
        "header_bytes": HEADER_BYTES,
        "payload_bytes": PAYLOAD_BYTES,
        "port": args.port,
        "duration_seconds_requested": args.duration_seconds,
        "interval_ms_requested": args.interval_ms,
        "planned_packets": planned_packets,
        "status_counts": dict(statuses),
        "actual_socket_send_buffer_bytes": actual_send_buffer,
        "timer_resolution_1ms_requested": timer_resolution_requested,
        "host_wall_start_ns": start_wall_ns,
        "host_wall_end_ns": end_wall_ns,
        "send_intervals": _timing_summary(send_intervals_ms),
        "send_call_duration_us": {
            "avg": statistics.fmean(send_durations_us) if send_durations_us else None,
            "max": max(send_durations_us) if send_durations_us else None,
            "p95": _percentile(send_durations_us, 0.95),
            "p99": _percentile(send_durations_us, 0.99),
        },
        "pacing_lateness_us": {
            "avg": statistics.fmean(pacing_lateness_us) if pacing_lateness_us else None,
            "max": max(pacing_lateness_us) if pacing_lateness_us else None,
            "p95": _percentile(pacing_lateness_us, 0.95),
            "p99": _percentile(pacing_lateness_us, 0.99),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Host probe complete: {len(successful)}/{planned_packets} packets sent")
    print(f"Host logs: {output_dir}")
    return 0 if statuses.get("error", 0) == 0 else 2


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _optional_int(row: dict[str, str], key: str) -> int | None:
    value = row.get(key, "").strip()
    if not value:
        return None
    return int(value)


def _distortion_summary(values_ms: list[float]) -> dict[str, object]:
    abs_values = [abs(value) for value in values_ms]
    return {
        "count": len(values_ms),
        "avg_ms": statistics.fmean(values_ms) if values_ms else None,
        "min_ms": min(values_ms) if values_ms else None,
        "max_ms": max(values_ms) if values_ms else None,
        "p50_ms": _percentile(values_ms, 0.50),
        "p95_ms": _percentile(values_ms, 0.95),
        "p99_ms": _percentile(values_ms, 0.99),
        "abs_p95_ms": _percentile(abs_values, 0.95),
        "abs_p99_ms": _percentile(abs_values, 0.99),
        "max_abs_ms": max(abs_values) if abs_values else None,
    }


def compare_probe(args: argparse.Namespace) -> int:
    host_rows = _read_csv(Path(args.host_csv))
    android_rows = _read_csv(Path(args.android_csv))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    host_sent: dict[int, dict[str, str]] = {
        int(row["sequence"]): row for row in host_rows if row.get("status") == "sent"
    }

    android_valid = [row for row in android_rows if row.get("valid", "1") == "1"]

    matching_current: list[dict[str, str]] = []
    foreign_or_stale: list[dict[str, str]] = []
    for row in android_valid:
        seq = int(row["sequence"])
        host = host_sent.get(seq)
        if host is None:
            foreign_or_stale.append(row)
            continue
        android_stamp = _optional_int(row, "host_packet_stamp_ns")
        host_stamp = int(host["packet_stamp_ns"])
        if android_stamp is not None and android_stamp != host_stamp:
            foreign_or_stale.append(row)
            continue
        matching_current.append(row)

    unique_android: dict[int, dict[str, str]] = {}
    ordered_unique: list[dict[str, str]] = []
    duplicates = 0
    duplicate_same_stamp = 0
    duplicate_conflicting_stamp = 0
    for row in matching_current:
        seq = int(row["sequence"])
        prior = unique_android.get(seq)
        if prior is not None:
            duplicates += 1
            if prior.get("host_packet_stamp_ns", "") == row.get("host_packet_stamp_ns", ""):
                duplicate_same_stamp += 1
            else:
                duplicate_conflicting_stamp += 1
            continue
        unique_android[seq] = row
        ordered_unique.append(row)

    host_sequences = set(host_sent)
    android_sequences = set(unique_android)
    missing_on_android = sorted(host_sequences - android_sequences)

    host_intervals: list[float] = []
    app_intervals: list[float] = []
    kernel_intervals: list[float] = []
    app_distortions: list[float] = []
    kernel_distortions: list[float] = []
    app_minus_kernel_interval_ms: list[float] = []
    same_sequence_step_count = 0
    kernel_same_sequence_step_count = 0
    host_4_6_app_lt2 = 0
    host_4_6_app_ge20 = 0
    host_4_6_kernel_lt2 = 0
    host_4_6_kernel_ge20 = 0

    previous: dict[str, str] | None = None
    for row in ordered_unique:
        seq = int(row["sequence"])
        if previous is not None:
            prev_seq = int(previous["sequence"])
            if seq == prev_seq + 1 and seq in host_sent and prev_seq in host_sent:
                host_gap_ms = (
                    int(host_sent[seq]["send_call_start_ns"])
                    - int(host_sent[prev_seq]["send_call_start_ns"])
                ) / 1_000_000.0
                app_gap_ms = (
                    int(row["rx_elapsed_ns"]) - int(previous["rx_elapsed_ns"])
                ) / 1_000_000.0
                host_intervals.append(host_gap_ms)
                app_intervals.append(app_gap_ms)
                app_distortions.append(app_gap_ms - host_gap_ms)
                same_sequence_step_count += 1
                if 4.0 <= host_gap_ms < 6.0 and app_gap_ms < 2.0:
                    host_4_6_app_lt2 += 1
                if 4.0 <= host_gap_ms < 6.0 and app_gap_ms >= 20.0:
                    host_4_6_app_ge20 += 1

                kernel_ns = _optional_int(row, "kernel_rx_realtime_ns")
                prev_kernel_ns = _optional_int(previous, "kernel_rx_realtime_ns")
                if kernel_ns is not None and prev_kernel_ns is not None:
                    kernel_gap_ms = (kernel_ns - prev_kernel_ns) / 1_000_000.0
                    kernel_intervals.append(kernel_gap_ms)
                    kernel_distortions.append(kernel_gap_ms - host_gap_ms)
                    app_minus_kernel_interval_ms.append(app_gap_ms - kernel_gap_ms)
                    kernel_same_sequence_step_count += 1
                    if 4.0 <= host_gap_ms < 6.0 and kernel_gap_ms < 2.0:
                        host_4_6_kernel_lt2 += 1
                    if 4.0 <= host_gap_ms < 6.0 and kernel_gap_ms >= 20.0:
                        host_4_6_kernel_ge20 += 1
        previous = row

    summary = {
        "probe": "PrivyHub UDP transport laboratory comparison",
        "format_version": 2,
        "host_attempts": len(host_rows),
        "host_successful_sends": len(host_sent),
        "android_valid_arrivals": len(android_valid),
        "android_current_run_arrivals": len(matching_current),
        "android_foreign_or_stale_arrivals": len(foreign_or_stale),
        "android_unique_arrivals": len(unique_android),
        "android_duplicate_arrivals": duplicates,
        "android_duplicate_same_host_packet_stamp": duplicate_same_stamp,
        "android_duplicate_conflicting_host_packet_stamp": duplicate_conflicting_stamp,
        "host_successes_missing_on_android": len(missing_on_android),
        "first_missing_sequences": missing_on_android[:32],
        "same_sequence_step_count": same_sequence_step_count,
        "kernel_same_sequence_step_count": kernel_same_sequence_step_count,
        "host_send_intervals_for_matched_consecutive_sequences": _timing_summary(host_intervals),
        "android_app_arrival_intervals_for_matched_consecutive_sequences": _timing_summary(app_intervals),
        "android_kernel_arrival_intervals_for_matched_consecutive_sequences": _timing_summary(kernel_intervals),
        "app_arrival_minus_send_interval_ms": _distortion_summary(app_distortions),
        "kernel_arrival_minus_send_interval_ms": _distortion_summary(kernel_distortions),
        "app_minus_kernel_interval_ms": _distortion_summary(app_minus_kernel_interval_ms),
        "host_4_to_6_ms_but_app_lt_2_ms": host_4_6_app_lt2,
        "host_4_to_6_ms_but_app_ge_20_ms": host_4_6_app_ge20,
        "host_4_to_6_ms_but_kernel_lt_2_ms": host_4_6_kernel_lt2,
        "host_4_to_6_ms_but_kernel_ge_20_ms": host_4_6_kernel_ge20,
        "interpretation_note": (
            "Host perf_counter_ns, Android elapsedRealtimeNanos, and kernel SO_TIMESTAMPNS have unrelated "
            "epochs. All cross-layer comparisons therefore use sequence-correlated interval deltas. "
            "app_minus_kernel_interval_ms shows how much additional interval distortion appears between "
            "kernel timestamping and post-recv userspace observation."
        ),
    }

    json_path = output_dir / "combined_summary.json"
    txt_path = output_dir / "combined_summary.txt"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    host_timing = summary["host_send_intervals_for_matched_consecutive_sequences"]
    app_timing = summary["android_app_arrival_intervals_for_matched_consecutive_sequences"]
    kernel_timing = summary["android_kernel_arrival_intervals_for_matched_consecutive_sequences"]
    app_kernel_delta = summary["app_minus_kernel_interval_ms"]

    lines = [
        "PrivyHub UDP transport laboratory - kernel timestamp comparison",
        "",
        f"Host successful sends: {summary['host_successful_sends']}",
        f"Android current-run unique arrivals: {summary['android_unique_arrivals']}",
        f"Host successes missing on Android: {summary['host_successes_missing_on_android']}",
        f"Android duplicates: {summary['android_duplicate_arrivals']} "
        f"(same stamp {duplicate_same_stamp}, conflicting stamp {duplicate_conflicting_stamp})",
        f"Android foreign/stale arrivals: {summary['android_foreign_or_stale_arrivals']}",
        "",
        f"Matched consecutive sequence intervals: {same_sequence_step_count}",
        f"Kernel-timestamp matched intervals: {kernel_same_sequence_step_count}",
        f"Host send avg/max ms: {host_timing['avg_ms']} / {host_timing['max_ms']}",
        f"Android app arrival avg/max ms: {app_timing['avg_ms']} / {app_timing['max_ms']}",
        f"Android kernel arrival avg/max ms: {kernel_timing['avg_ms']} / {kernel_timing['max_ms']}",
        "",
        f"Host 4-6 ms -> app <2 ms: {host_4_6_app_lt2}",
        f"Host 4-6 ms -> app >=20 ms: {host_4_6_app_ge20}",
        f"Host 4-6 ms -> kernel <2 ms: {host_4_6_kernel_lt2}",
        f"Host 4-6 ms -> kernel >=20 ms: {host_4_6_kernel_ge20}",
        "",
        f"App-minus-kernel interval delta p50/p95/p99/max-abs ms: "
        f"{app_kernel_delta['p50_ms']} / {app_kernel_delta['p95_ms']} / "
        f"{app_kernel_delta['p99_ms']} / {app_kernel_delta['max_abs_ms']}",
        "",
        "Host send histogram:",
        json.dumps(host_timing["histogram"], indent=2, sort_keys=True),
        "",
        "Android app-arrival histogram:",
        json.dumps(app_timing["histogram"], indent=2, sort_keys=True),
        "",
        "Android kernel-arrival histogram:",
        json.dumps(kernel_timing["histogram"], indent=2, sort_keys=True),
        "",
        summary["interpretation_note"],
    ]
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(txt_path.read_text(encoding="utf-8"))
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PrivyHub standalone UDP transport laboratory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send = subparsers.add_parser("send", help="send a paced synthetic UDP stream")
    send.add_argument("--target", required=True, help="ONN_IP supplied locally; never committed")
    send.add_argument("--port", type=int, default=DEFAULT_PORT)
    send.add_argument("--duration-seconds", type=float, default=60.0)
    send.add_argument("--interval-ms", type=float, default=DEFAULT_INTERVAL_MS)
    send.add_argument("--send-buffer-bytes", type=int, default=0)
    send.add_argument("--output-dir", required=True)
    send.set_defaults(func=send_probe)

    compare_cmd = subparsers.add_parser("compare", help="compare host and Android packet logs")
    compare_cmd.add_argument("--host-csv", required=True)
    compare_cmd.add_argument("--android-csv", required=True)
    compare_cmd.add_argument("--output-dir", required=True)
    compare_cmd.set_defaults(func=compare_probe)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "port", DEFAULT_PORT) < 1024 or getattr(args, "port", DEFAULT_PORT) > 65535:
        parser.error("port must be 1024..65535")
    if getattr(args, "duration_seconds", 1.0) <= 0:
        parser.error("duration must be positive")
    if getattr(args, "interval_ms", 1.0) <= 0:
        parser.error("interval must be positive")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
