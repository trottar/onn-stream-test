#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import struct
from pathlib import Path

UTP1 = struct.Struct("<4sBBHIQQQI")
UTP1_MAGIC = b"UTP1"
UTP1_VERSION = 1
UTP1_HEADER_BYTES = UTP1.size
UTP1_PAYLOAD_BYTES = 960


def percentile(values, p):
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    rank = (len(xs) - 1) * p
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return xs[lo]
    f = rank - lo
    return xs[lo] * (1.0 - f) + xs[hi] * f


def timing(values):
    return {
        "count": len(values),
        "avg_ms": statistics.fmean(values) if values else None,
        "p50_ms": percentile(values, 0.50),
        "p95_ms": percentile(values, 0.95),
        "p99_ms": percentile(values, 0.99),
        "max_ms": max(values) if values else None,
        "lt_2_ms": sum(v < 2.0 for v in values),
        "ge_20_ms": sum(v >= 20.0 for v in values),
    }


def read_pcap(path):
    raw = path.read_bytes()
    if len(raw) < 24:
        raise ValueError(f"{path}: truncated pcap")

    magic = raw[:4]
    if magic == b"\xd4\xc3\xb2\xa1":
        endian, scale = "<", 1_000_000.0
    elif magic == b"\xa1\xb2\xc3\xd4":
        endian, scale = ">", 1_000_000.0
    elif magic == b"\x4d\x3c\xb2\xa1":
        endian, scale = "<", 1_000_000_000.0
    elif magic == b"\xa1\xb2\x3c\x4d":
        endian, scale = ">", 1_000_000_000.0
    else:
        raise ValueError(f"{path}: unsupported pcap magic {magic.hex()}")

    gh = struct.Struct(endian + "IHHIIII")
    _, major, minor, _tz, _sig, _snap, linktype = gh.unpack_from(raw, 0)
    if major != 2:
        raise ValueError(f"{path}: unexpected pcap version {major}.{minor}")

    ph = struct.Struct(endian + "IIII")
    offset = gh.size
    rows = []
    packet_index = 0
    total_records = 0

    while offset + ph.size <= len(raw):
        ts_sec, ts_frac, incl_len, orig_len = ph.unpack_from(raw, offset)
        offset += ph.size
        if offset + incl_len > len(raw):
            raise ValueError(f"{path}: truncated packet data at record {packet_index}")
        data = raw[offset:offset + incl_len]
        offset += incl_len

        pos = data.find(UTP1_MAGIC)
        if pos >= 0 and pos + UTP1.size <= len(data):
            fields = UTP1.unpack_from(data, pos)
            magic2, version, _flags, header_bytes, sequence, intended_ns, send_call_ns, sender_wall_ns, payload_bytes = fields
            if (
                magic2 == UTP1_MAGIC
                and version == UTP1_VERSION
                and header_bytes == UTP1_HEADER_BYTES
                and payload_bytes == UTP1_PAYLOAD_BYTES
            ):
                rows.append({
                    "packet_index": packet_index,
                    "capture_ns": int(ts_sec * 1_000_000_000 + (ts_frac * 1_000_000_000 / scale)),
                    "sequence": int(sequence),
                    "intended_ns": int(intended_ns),
                    "send_call_ns": int(send_call_ns),
                    "sender_wall_ns": int(sender_wall_ns),
                    "captured_bytes": int(incl_len),
                    "original_bytes": int(orig_len),
                })
        packet_index += 1
        total_records += 1

    if offset != len(raw):
        raise ValueError(f"{path}: trailing or incomplete pcap bytes at offset {offset}")

    return rows, linktype, total_records, len(raw)


def summarize_capture(path):
    rows, linktype, total_records, pcap_bytes = read_pcap(path)
    first = {}
    same = 0
    conflicting = 0
    for row in rows:
        seq = row["sequence"]
        prior = first.get(seq)
        if prior is None:
            first[seq] = row
        elif prior["send_call_ns"] == row["send_call_ns"]:
            same += 1
        else:
            conflicting += 1

    ordered = sorted(first.values(), key=lambda r: r["capture_ns"])
    intervals = []
    for a, b in zip(ordered, ordered[1:]):
        if b["sequence"] == a["sequence"] + 1:
            intervals.append((b["capture_ns"] - a["capture_ns"]) / 1_000_000.0)

    return {
        "pcap": str(path),
        "pcap_bytes": pcap_bytes,
        "linktype": linktype,
        "total_pcap_records": total_records,
        "matched_utp1_packets": len(rows),
        "unique_sequences": len(first),
        "same_stamp_duplicates": same,
        "conflicting_stamp_duplicates": conflicting,
        "first_by_sequence": first,
        "capture_intervals_unique_consecutive": timing(intervals),
    }


def read_host_successes(path):
    out = {}
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("status") == "sent":
                out[int(r["sequence"])] = r
    return out


def stripped(summary):
    return {k: v for k, v in summary.items() if k != "first_by_sequence"}


def classify(ingress, egress, android_dups, host_successes):
    if ingress["matched_utp1_packets"] == 0 or egress["matched_utp1_packets"] == 0:
        return "INVALID_ROUTER_CAPTURE_NO_UTP1_AT_ONE_OR_BOTH_BOUNDARIES"

    minimum_expected = max(20, int(host_successes * 0.25))
    if (
        ingress["unique_sequences"] < minimum_expected
        or egress["unique_sequences"] < minimum_expected
    ):
        return "INVALID_ROUTER_CAPTURE_INSUFFICIENT_UTP1_COVERAGE"

    i = ingress["same_stamp_duplicates"]
    e = egress["same_stamp_duplicates"]
    if i >= 20:
        return "DUPLICATION_PRESENT_AT_LINUX_FACING_OPAL_BOUNDARY"
    if e >= 20:
        return "DUPLICATION_APPEARS_BETWEEN_OPAL_RADIO_BOUNDARIES"
    if android_dups >= 20:
        return "ROUTER_BOUNDARIES_CLEAN_DUPLICATION_DOWNSTREAM_OF_ONN_FACING_BOUNDARY"
    return "NO_LARGE_DUPLICATION_REPRODUCED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    args = ap.parse_args()

    root = Path(args.session)
    ingress = summarize_capture(root / "router_linux_radio.pcap")
    egress = summarize_capture(root / "router_onn_radio.pcap")
    host = read_host_successes(root / "host_packets.csv")
    combined = json.loads((root / "combined_summary.json").read_text(encoding="utf-8"))

    host_seqs = set(host)
    in_seqs = set(ingress["first_by_sequence"])
    out_seqs = set(egress["first_by_sequence"])

    android_dups = int(combined["android_duplicate_arrivals"])

    result = {
        "probe": "PrivyHub Opal dual-boundary UTP1 forward probe",
        "format_version": 1,
        "privacy_note": "Raw PCAPs remain local and may contain network addresses. Share the sanitized result, not the PCAPs.",
        "host_successful_sends": len(host_seqs),
        "router_linux_radio": stripped(ingress),
        "router_onn_radio": stripped(egress),
        "host_successes_missing_at_linux_radio": len(host_seqs - in_seqs),
        "host_successes_missing_at_onn_radio": len(host_seqs - out_seqs),
        "sequences_seen_linux_radio_not_onn_radio": len(in_seqs - out_seqs),
        "sequences_seen_onn_radio_not_linux_radio": len(out_seqs - in_seqs),
        "android_unique_arrivals": int(combined["android_unique_arrivals"]),
        "android_duplicate_arrivals": android_dups,
        "android_missing_host_successes": int(combined["host_successes_missing_on_android"]),
        "classification": classify(ingress, egress, android_dups, len(host_seqs)),
    }

    (root / "opal_dual_boundary_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    a = result["router_linux_radio"]
    b = result["router_onn_radio"]
    lines = [
        "=== OPAL DUAL-BOUNDARY RESULT ===",
        f"host_successful_sends = {result['host_successful_sends']}",
        f"linux_radio_pcap_bytes = {a['pcap_bytes']}",
        f"linux_radio_total_pcap_records = {a['total_pcap_records']}",
        f"linux_radio_linktype = {a['linktype']}",
        f"linux_radio_matched_utp1_packets = {a['matched_utp1_packets']}",
        f"linux_radio_unique = {a['unique_sequences']}",
        f"linux_radio_same_stamp_duplicates = {a['same_stamp_duplicates']}",
        f"linux_radio_p95_ms = {a['capture_intervals_unique_consecutive']['p95_ms']}",
        f"linux_radio_max_ms = {a['capture_intervals_unique_consecutive']['max_ms']}",
        f"onn_radio_pcap_bytes = {b['pcap_bytes']}",
        f"onn_radio_total_pcap_records = {b['total_pcap_records']}",
        f"onn_radio_linktype = {b['linktype']}",
        f"onn_radio_matched_utp1_packets = {b['matched_utp1_packets']}",
        f"onn_radio_unique = {b['unique_sequences']}",
        f"onn_radio_same_stamp_duplicates = {b['same_stamp_duplicates']}",
        f"onn_radio_p95_ms = {b['capture_intervals_unique_consecutive']['p95_ms']}",
        f"onn_radio_max_ms = {b['capture_intervals_unique_consecutive']['max_ms']}",
        f"missing_at_linux_radio = {result['host_successes_missing_at_linux_radio']}",
        f"missing_at_onn_radio = {result['host_successes_missing_at_onn_radio']}",
        f"linux_only_sequences = {result['sequences_seen_linux_radio_not_onn_radio']}",
        f"onn_only_sequences = {result['sequences_seen_onn_radio_not_linux_radio']}",
        f"android_unique = {result['android_unique_arrivals']}",
        f"android_duplicates = {result['android_duplicate_arrivals']}",
        f"android_missing = {result['android_missing_host_successes']}",
        f"classification = {result['classification']}",
        f"session = {root}",
        "privacy = Raw PCAPs contain local network metadata; do not upload them unless specifically required.",
    ]
    text = "\n".join(lines) + "\n"
    (root / "opal_dual_boundary_summary.txt").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
