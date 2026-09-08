#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import ctypes
import json
import math
import os
import re
import socket
import statistics
import struct
import time
from collections import Counter
from pathlib import Path
from typing import Iterable

MAGIC = b"UTR1"
VERSION = 1
HEADER = struct.Struct("<4sBBHIQQQI")
HEADER_BYTES = HEADER.size
PAYLOAD_BYTES = 960
PACKET_BYTES = HEADER_BYTES + PAYLOAD_BYTES
DEFAULT_PORT = 48102


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * p
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return values[lo]
    f = rank - lo
    return values[lo] * (1.0 - f) + values[hi] * f


def _histogram_ms(values: Iterable[float]) -> dict[str, int]:
    out = Counter({
        "lt_1_ms": 0, "1_to_2_ms": 0, "2_to_4_ms": 0, "4_to_6_ms": 0,
        "6_to_10_ms": 0, "10_to_15_ms": 0, "15_to_20_ms": 0,
        "20_to_30_ms": 0, "ge_30_ms": 0,
    })
    for value in values:
        if value < 1: out["lt_1_ms"] += 1
        elif value < 2: out["1_to_2_ms"] += 1
        elif value < 4: out["2_to_4_ms"] += 1
        elif value < 6: out["4_to_6_ms"] += 1
        elif value < 10: out["6_to_10_ms"] += 1
        elif value < 15: out["10_to_15_ms"] += 1
        elif value < 20: out["15_to_20_ms"] += 1
        elif value < 30: out["20_to_30_ms"] += 1
        else: out["ge_30_ms"] += 1
    result = dict(out)
    result["lt_2_ms_total"] = result["lt_1_ms"] + result["1_to_2_ms"]
    return result


def _timing_summary(values: list[float]) -> dict[str, object]:
    return {
        "count": len(values),
        "avg_ms": statistics.fmean(values) if values else None,
        "min_ms": min(values) if values else None,
        "max_ms": max(values) if values else None,
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
        "p99_ms": _percentile(values, 0.99),
        "histogram": _histogram_ms(values),
    }


def _distortion_summary(values: list[float]) -> dict[str, object]:
    abs_values = [abs(v) for v in values]
    return {
        "count": len(values),
        "avg_ms": statistics.fmean(values) if values else None,
        "min_ms": min(values) if values else None,
        "max_ms": max(values) if values else None,
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
        "p99_ms": _percentile(values, 0.99),
        "abs_p95_ms": _percentile(abs_values, 0.95),
        "abs_p99_ms": _percentile(abs_values, 0.99),
        "max_abs_ms": max(abs_values) if abs_values else None,
    }


def _request_high_priority() -> bool:
    if os.name != "nt":
        return False
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.GetCurrentProcess()
        HIGH_PRIORITY_CLASS = 0x00000080
        return bool(kernel32.SetPriorityClass(handle, HIGH_PRIORITY_CLASS))
    except Exception:
        return False


def _parse_packet(data: bytes) -> dict[str, int] | None:
    if len(data) != PACKET_BYTES:
        return None
    magic, version, _flags, header_bytes, sequence, intended_ns, send_call_ns, sender_wall_ns, payload_bytes = HEADER.unpack_from(data)
    if magic != MAGIC or version != VERSION or header_bytes != HEADER_BYTES or payload_bytes != PAYLOAD_BYTES:
        return None
    return {
        "sequence": sequence,
        "sender_intended_ns": intended_ns,
        "sender_call_ns": send_call_ns,
        "sender_wall_ns": sender_wall_ns,
    }


def receive_probe(args: argparse.Namespace) -> int:
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "host_packets.csv"
    summary_path = outdir / "host_summary.json"

    high_priority = _request_high_priority()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, args.receive_buffer_bytes)
    actual_rcvbuf = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    sock.bind((args.bind, args.port))
    sock.settimeout(0.10)

    rows: list[dict[str, object]] = []
    invalid = 0
    first_by_sequence: dict[int, dict[str, object]] = {}
    duplicates = 0
    duplicate_same_stamp = 0
    duplicate_conflicting_stamp = 0
    reordered = 0
    last_first_sequence: int | None = None
    start_perf_ns = time.perf_counter_ns()
    start_wall_ns = time.time_ns()
    deadline = time.monotonic() + args.duration_seconds
    last_arrival_mono = 0.0

    try:
        while time.monotonic() < deadline:
            try:
                data, _source = sock.recvfrom(2048)
            except socket.timeout:
                if args.expected_packets > 0 and len(first_by_sequence) >= args.expected_packets and last_arrival_mono and time.monotonic() - last_arrival_mono > 0.25:
                    break
                continue

            recv_perf_ns = time.perf_counter_ns()
            recv_wall_ns = time.time_ns()
            last_arrival_mono = time.monotonic()
            parsed = _parse_packet(data)
            if parsed is None:
                invalid += 1
                continue

            sequence = int(parsed["sequence"])
            row = {
                **parsed,
                "recv_perf_ns": recv_perf_ns,
                "recv_wall_ns": recv_wall_ns,
                "packet_bytes": len(data),
                "valid": 1,
            }
            rows.append(row)
            prior = first_by_sequence.get(sequence)
            if prior is not None:
                duplicates += 1
                if int(prior["sender_call_ns"]) == int(row["sender_call_ns"]):
                    duplicate_same_stamp += 1
                else:
                    duplicate_conflicting_stamp += 1
                continue
            if last_first_sequence is not None and sequence < last_first_sequence:
                reordered += 1
            last_first_sequence = sequence
            first_by_sequence[sequence] = row
    finally:
        sock.close()

    end_perf_ns = time.perf_counter_ns()
    end_wall_ns = time.time_ns()

    fieldnames = [
        "sequence", "recv_perf_ns", "recv_wall_ns", "sender_intended_ns",
        "sender_call_ns", "sender_wall_ns", "packet_bytes", "valid",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    ordered_unique = []
    seen: set[int] = set()
    for row in rows:
        seq = int(row["sequence"])
        if seq in seen:
            continue
        seen.add(seq)
        ordered_unique.append(row)

    intervals = [
        (int(ordered_unique[i]["recv_perf_ns"]) - int(ordered_unique[i - 1]["recv_perf_ns"])) / 1_000_000.0
        for i in range(1, len(ordered_unique))
        if int(ordered_unique[i]["sequence"]) == int(ordered_unique[i - 1]["sequence"]) + 1
    ]

    summary = {
        "probe": "PrivyHub reverse UDP Windows receiver",
        "format_version": 1,
        "packet_magic": MAGIC.decode("ascii"),
        "packet_bytes": PACKET_BYTES,
        "port": args.port,
        "duration_seconds_requested": args.duration_seconds,
        "expected_packets": args.expected_packets,
        "valid_arrivals": len(rows),
        "unique_packets": len(first_by_sequence),
        "duplicate_packets": duplicates,
        "duplicate_same_sender_stamp": duplicate_same_stamp,
        "duplicate_conflicting_sender_stamp": duplicate_conflicting_stamp,
        "reordered_packets": reordered,
        "invalid_packets": invalid,
        "requested_socket_receive_buffer_bytes": args.receive_buffer_bytes,
        "actual_socket_receive_buffer_bytes": actual_rcvbuf,
        "high_process_priority_requested": high_priority,
        "host_perf_start_ns": start_perf_ns,
        "host_perf_end_ns": end_perf_ns,
        "host_wall_start_ns": start_wall_ns,
        "host_wall_end_ns": end_wall_ns,
        "receive_intervals_unique_consecutive": _timing_summary(intervals),
        "source_address_persisted": False,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Windows reverse receiver complete: {len(first_by_sequence)}/{args.expected_packets or '?'} unique packets")
    print(f"Windows logs: {outdir}")
    return 0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def compare_probe(args: argparse.Namespace) -> int:
    sender_rows = _read_csv(Path(args.sender_csv))
    host_rows = _read_csv(Path(args.host_csv))
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    sender_sent = {int(r["sequence"]): r for r in sender_rows if r.get("status") == "sent"}
    matching: list[dict[str, str]] = []
    foreign: list[dict[str, str]] = []
    for row in host_rows:
        seq = int(row["sequence"])
        sender = sender_sent.get(seq)
        if sender is None or int(row["sender_call_ns"]) != int(sender["send_call_ns"]):
            foreign.append(row)
        else:
            matching.append(row)

    unique: dict[int, dict[str, str]] = {}
    ordered_unique: list[dict[str, str]] = []
    duplicates = same_dup = conflicting_dup = 0
    for row in matching:
        seq = int(row["sequence"])
        prior = unique.get(seq)
        if prior is not None:
            duplicates += 1
            if row["sender_call_ns"] == prior["sender_call_ns"]:
                same_dup += 1
            else:
                conflicting_dup += 1
            continue
        unique[seq] = row
        ordered_unique.append(row)

    missing = sorted(set(sender_sent) - set(unique))
    sender_call_start_gaps: list[float] = []
    sender_completion_gaps: list[float] = []
    host_gaps: list[float] = []
    completion_distortions: list[float] = []
    call_start_distortions: list[float] = []
    sender_4_6_host_lt2 = 0
    sender_4_6_host_ge20 = 0
    call_start_4_6_host_lt2 = 0
    call_start_4_6_host_ge20 = 0
    matched_steps = 0

    prev: dict[str, str] | None = None
    for row in ordered_unique:
        seq = int(row["sequence"])
        if prev is not None:
            prev_seq = int(prev["sequence"])
            if seq == prev_seq + 1 and seq in sender_sent and prev_seq in sender_sent:
                call_start_gap = (int(sender_sent[seq]["send_call_ns"]) - int(sender_sent[prev_seq]["send_call_ns"])) / 1_000_000.0
                completion_gap = (int(sender_sent[seq]["send_done_ns"]) - int(sender_sent[prev_seq]["send_done_ns"])) / 1_000_000.0
                host_gap = (int(row["recv_perf_ns"]) - int(prev["recv_perf_ns"])) / 1_000_000.0
                sender_call_start_gaps.append(call_start_gap)
                sender_completion_gaps.append(completion_gap)
                host_gaps.append(host_gap)
                completion_distortions.append(host_gap - completion_gap)
                call_start_distortions.append(host_gap - call_start_gap)
                matched_steps += 1
                if 4.0 <= completion_gap < 6.0 and host_gap < 2.0:
                    sender_4_6_host_lt2 += 1
                if 4.0 <= completion_gap < 6.0 and host_gap >= 20.0:
                    sender_4_6_host_ge20 += 1
                if 4.0 <= call_start_gap < 6.0 and host_gap < 2.0:
                    call_start_4_6_host_lt2 += 1
                if 4.0 <= call_start_gap < 6.0 and host_gap >= 20.0:
                    call_start_4_6_host_ge20 += 1
        prev = row

    send_durations = [
        (int(r["send_done_ns"]) - int(r["send_call_ns"])) / 1_000_000.0
        for r in sender_rows if r.get("send_call_ns") and r.get("send_done_ns")
    ]
    pacing_lateness = [
        (int(r["send_call_ns"]) - int(r["intended_ns"])) / 1_000_000.0
        for r in sender_rows if r.get("send_call_ns") and r.get("intended_ns")
    ]

    summary = {
        "probe": "PrivyHub reverse UDP transport comparison",
        "format_version": 2,
        "android_sender_attempts": len(sender_rows),
        "android_sender_successes": len(sender_sent),
        "windows_current_run_arrivals": len(matching),
        "windows_unique_arrivals": len(unique),
        "windows_duplicate_arrivals": duplicates,
        "windows_duplicate_same_sender_stamp": same_dup,
        "windows_duplicate_conflicting_sender_stamp": conflicting_dup,
        "windows_foreign_or_stale_arrivals": len(foreign),
        "sender_successes_missing_on_windows": len(missing),
        "first_missing_sequences": missing[:32],
        "matched_consecutive_sequence_intervals": matched_steps,
        "android_sender_intervals_for_matched_consecutive_sequences": _timing_summary(sender_completion_gaps),
        "android_send_completion_intervals_for_matched_consecutive_sequences": _timing_summary(sender_completion_gaps),
        "android_send_call_start_intervals_for_matched_consecutive_sequences": _timing_summary(sender_call_start_gaps),
        "windows_receive_intervals_for_matched_consecutive_sequences": _timing_summary(host_gaps),
        "windows_receive_minus_android_send_interval_ms": _distortion_summary(completion_distortions),
        "windows_receive_minus_android_send_completion_interval_ms": _distortion_summary(completion_distortions),
        "windows_receive_minus_android_send_call_start_interval_ms": _distortion_summary(call_start_distortions),
        "android_send_call_duration_ms": _timing_summary(send_durations),
        "android_sender_pacing_lateness_ms": _timing_summary(pacing_lateness),
        "android_4_to_6_ms_but_windows_lt_2_ms": sender_4_6_host_lt2,
        "android_4_to_6_ms_but_windows_ge_20_ms": sender_4_6_host_ge20,
        "android_call_start_4_to_6_ms_but_windows_lt_2_ms": call_start_4_6_host_lt2,
        "android_call_start_4_to_6_ms_but_windows_ge_20_ms": call_start_4_6_host_ge20,
        "primary_sender_boundary": "send_done_ns",
        "interpretation_note": (
            "Android elapsedRealtimeNanos and Windows perf_counter_ns have unrelated epochs. "
            "Cross-device comparisons therefore use sequence-correlated interval deltas. "
            "Primary transport distortion uses Android nonblocking DatagramChannel send completion (send_done_ns). "
            "Call-start timing is retained separately for sender scheduler and blocking-call analysis."
        ),
    }

    (outdir / "combined_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = summary["android_send_completion_intervals_for_matched_consecutive_sequences"]
    sc = summary["android_send_call_start_intervals_for_matched_consecutive_sequences"]
    w = summary["windows_receive_intervals_for_matched_consecutive_sequences"]
    d = summary["windows_receive_minus_android_send_completion_interval_ms"]
    lines = [
        "PrivyHub reverse UDP transport laboratory - Android sender / Windows receiver",
        "",
        f"Android successful sends: {summary['android_sender_successes']}",
        f"Windows unique arrivals: {summary['windows_unique_arrivals']}",
        f"Sender successes missing on Windows: {summary['sender_successes_missing_on_windows']}",
        f"Windows duplicates: {duplicates} (same stamp {same_dup}, conflicting stamp {conflicting_dup})",
        f"Windows foreign/stale arrivals: {len(foreign)}",
        "",
        f"Matched consecutive intervals: {matched_steps}",
        f"Android send-completion avg/max ms: {s['avg_ms']} / {s['max_ms']}",
        f"Android call-start avg/max ms: {sc['avg_ms']} / {sc['max_ms']}",
        f"Windows receive avg/max ms: {w['avg_ms']} / {w['max_ms']}",
        f"Android 4-6 ms -> Windows <2 ms: {sender_4_6_host_lt2}",
        f"Android 4-6 ms -> Windows >=20 ms: {sender_4_6_host_ge20}",
        "",
        f"Receive-minus-send abs p95/p99/max ms: {d['abs_p95_ms']} / {d['abs_p99_ms']} / {d['max_abs_ms']}",
        "",
        "Android send-completion histogram:",
        json.dumps(s["histogram"], indent=2, sort_keys=True),
        "",
        "Android call-start histogram:",
        json.dumps(sc["histogram"], indent=2, sort_keys=True),
        "",
        "Windows receive histogram:",
        json.dumps(w["histogram"], indent=2, sort_keys=True),
        "",
        summary["interpretation_note"],
    ]
    text = "\n".join(lines) + "\n"
    (outdir / "combined_summary.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0



def pktmon_presence(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    raw_prefix = input_path.read_bytes()[:4]
    if raw_prefix.startswith(b"\xff\xfe") or raw_prefix.startswith(b"\xfe\xff"):
        encoding = "utf-16"
    elif raw_prefix.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    else:
        encoding = "utf-8"

    all_groups: set[str] = set()
    rx_groups: set[str] = set()
    tx_groups: set[str] = set()
    component_counts: Counter[str] = Counter()
    rx_appearances = 0
    tx_appearances = 0
    event_appearances = 0
    events_lost = None
    buffers_lost = None

    with input_path.open("r", encoding=encoding, errors="replace") as handle:
        for line in handle:
            if events_lost is None and "EventsLost:" in line:
                match = re.search(r"EventsLost:\s*(\d+)", line)
                if match:
                    events_lost = int(match.group(1))
            if buffers_lost is None and "BuffersLost:" in line:
                match = re.search(r"BuffersLost:\s*(\d+)", line)
                if match:
                    buffers_lost = int(match.group(1))

            if "[Microsoft-Windows-PktMon]" not in line:
                continue
            match = re.search(r"PktGroupId\s+([^,]+)", line)
            if not match:
                continue
            group = match.group(1).strip()
            all_groups.add(group)
            event_appearances += 1

            if re.search(r"Direction\s+Rx\b", line):
                rx_groups.add(group)
                rx_appearances += 1
            elif re.search(r"Direction\s+Tx\b", line):
                tx_groups.add(group)
                tx_appearances += 1

            match = re.search(r"Component\s+(\d+)", line)
            if match:
                component_counts[match.group(1)] += 1

    components = [
        {"component_id": int(component), "appearances": count}
        for component, count in sorted(component_counts.items(), key=lambda item: int(item[0]))
    ]

    if rx_groups:
        interpretation = "PktMon observed reverse UDP traffic arriving in the Windows networking stack."
    else:
        interpretation = "PktMon did not observe reverse UDP traffic arriving in the Windows networking stack."

    summary = {
        "probe": "PrivyHub reverse UDP PktMon presence summary",
        "format_version": 1,
        "privacy_note": "No IP addresses, MAC addresses, or packet payloads are persisted in this summary.",
        "packet_group_count": len(all_groups),
        "rx_packet_group_count": len(rx_groups),
        "tx_packet_group_count": len(tx_groups),
        "event_appearance_count": event_appearances,
        "rx_appearance_count": rx_appearances,
        "tx_appearance_count": tx_appearances,
        "events_lost": events_lost,
        "buffers_lost": buffers_lost,
        "components": components,
        "interpretation": interpretation,
    }

    json_path = outdir / "pktmon_presence_summary.json"
    text_path = outdir / "pktmon_presence_summary.txt"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "PrivyHub reverse UDP PktMon presence summary",
        "",
        f"Packet groups: {len(all_groups)}",
        f"Rx packet groups: {len(rx_groups)}",
        f"Tx packet groups: {len(tx_groups)}",
        f"Rx appearances: {rx_appearances}",
        f"Tx appearances: {tx_appearances}",
        f"Events lost: {events_lost}",
        f"Buffers lost: {buffers_lost}",
        "",
        interpretation,
        "",
        "Components:",
    ]
    if components:
        lines.extend(f"  {item['component_id']}: {item['appearances']} appearances" for item in components)
    else:
        lines.append("  none")
    lines.extend(["", "Privacy: no IP addresses or MAC addresses are included in this summary."])
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(text_path.read_text(encoding="utf-8"), end="")
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PrivyHub reverse UDP transport laboratory")
    subs = parser.add_subparsers(dest="command", required=True)

    recv = subs.add_parser("receive", help="receive Android-paced synthetic UDP packets on Windows")
    recv.add_argument("--bind", default="0.0.0.0")
    recv.add_argument("--port", type=int, default=DEFAULT_PORT)
    recv.add_argument("--duration-seconds", type=float, default=28.0)
    recv.add_argument("--expected-packets", type=int, default=0)
    recv.add_argument("--receive-buffer-bytes", type=int, default=1 << 20)
    recv.add_argument("--output-dir", required=True)
    recv.set_defaults(func=receive_probe)

    compare_cmd = subs.add_parser("compare", help="compare Android sender and Windows receiver timing")
    compare_cmd.add_argument("--sender-csv", required=True)
    compare_cmd.add_argument("--host-csv", required=True)
    compare_cmd.add_argument("--output-dir", required=True)
    compare_cmd.set_defaults(func=compare_probe)

    pktmon_cmd = subs.add_parser("pktmon-presence", help="summarize PktMon packet presence without persisting addresses")
    pktmon_cmd.add_argument("--input", required=True)
    pktmon_cmd.add_argument("--output-dir", required=True)
    pktmon_cmd.set_defaults(func=pktmon_presence)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "port", DEFAULT_PORT) < 1024 or getattr(args, "port", DEFAULT_PORT) > 65535:
        parser.error("port must be 1024..65535")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
