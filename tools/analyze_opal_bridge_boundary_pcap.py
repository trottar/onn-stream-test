#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import struct
from pathlib import Path

UTP1 = struct.Struct("<4sBBHIQQQI")
MAGIC = b"UTP1"


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
    frac = rank - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def read_pcap(path):
    raw = path.read_bytes()
    if len(raw) < 24:
        raise ValueError("truncated pcap")

    magic = raw[:4]
    if magic == b"\xd4\xc3\xb2\xa1":
        endian, scale = "<", 1_000_000
    elif magic == b"\xa1\xb2\xc3\xd4":
        endian, scale = ">", 1_000_000
    elif magic == b"\x4d\x3c\xb2\xa1":
        endian, scale = "<", 1_000_000_000
    elif magic == b"\xa1\xb2\x3c\x4d":
        endian, scale = ">", 1_000_000_000
    else:
        raise ValueError("unsupported pcap magic")

    gh = struct.Struct(endian + "IHHIIII")
    _, major, minor, _, _, _, linktype = gh.unpack_from(raw, 0)
    if major != 2:
        raise ValueError(f"unexpected pcap version {major}.{minor}")

    ph = struct.Struct(endian + "IIII")
    offset = gh.size
    total = 0
    rows = []

    while offset + ph.size <= len(raw):
        sec, frac, incl_len, orig_len = ph.unpack_from(raw, offset)
        offset += ph.size
        if offset + incl_len > len(raw):
            raise ValueError(f"truncated record {total}")
        data = raw[offset:offset + incl_len]
        offset += incl_len
        total += 1

        pos = data.find(MAGIC)
        if pos < 0 or pos + UTP1.size > len(data):
            continue

        fields = UTP1.unpack_from(data, pos)
        m, version, _, header_bytes, seq, _, send_call_ns, _, payload_bytes = fields
        if m != MAGIC or version != 1 or header_bytes != UTP1.size or payload_bytes != 960:
            continue

        capture_ns = int(sec * 1_000_000_000 + (frac * 1_000_000_000 / scale))
        rows.append({
            "sequence": int(seq),
            "send_call_ns": int(send_call_ns),
            "capture_ns": capture_ns,
        })

    if offset != len(raw):
        raise ValueError(f"trailing/incomplete bytes at offset {offset}")

    return {
        "pcap_bytes": len(raw),
        "linktype": linktype,
        "total_records": total,
        "utp1_rows": rows,
    }


def host_successes(path):
    out = {}
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("status") == "sent":
                out[int(r["sequence"])] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    args = ap.parse_args()
    session = Path(args.session)

    p = read_pcap(session / "router_bridge.pcap")
    host = host_successes(session / "host_packets.csv")
    combined = json.loads((session / "combined_summary.json").read_text(encoding="utf-8"))

    first = {}
    same_stamp_dups = 0
    conflicting_dups = 0
    for row in p["utp1_rows"]:
        seq = row["sequence"]
        prior = first.get(seq)
        if prior is None:
            first[seq] = row
        elif prior["send_call_ns"] == row["send_call_ns"]:
            same_stamp_dups += 1
        else:
            conflicting_dups += 1

    ordered = sorted(first.values(), key=lambda x: x["capture_ns"])
    intervals = []
    for a, b in zip(ordered, ordered[1:]):
        if b["sequence"] == a["sequence"] + 1:
            intervals.append((b["capture_ns"] - a["capture_ns"]) / 1_000_000.0)

    host_seqs = set(host)
    bridge_seqs = set(first)
    host_count = len(host_seqs)

    if p["total_records"] == 0:
        classification = "BRIDGE_CAPTURE_EMPTY"
    elif len(first) == 0:
        classification = "BRIDGE_CAPTURE_HAS_RECORDS_BUT_NO_UTP1"
    elif len(first) < max(20, int(host_count * 0.25)):
        classification = "BRIDGE_CAPTURE_INSUFFICIENT_UTP1_COVERAGE"
    elif same_stamp_dups >= 20:
        classification = "DUPLICATION_VISIBLE_AT_BRIDGE_BOUNDARY"
    else:
        classification = "BRIDGE_BOUNDARY_SEES_UTP1_WITHOUT_LARGE_DUPLICATION"

    result = {
        "probe": "PrivyHub Opal br-lan boundary probe",
        "pcap_bytes": p["pcap_bytes"],
        "pcap_linktype": p["linktype"],
        "pcap_total_records": p["total_records"],
        "matched_utp1_packets": len(p["utp1_rows"]),
        "unique_utp1_sequences": len(first),
        "same_stamp_duplicates": same_stamp_dups,
        "conflicting_stamp_duplicates": conflicting_dups,
        "host_successful_sends": host_count,
        "host_successes_missing_at_bridge": len(host_seqs - bridge_seqs),
        "bridge_sequences_not_in_host_successes": len(bridge_seqs - host_seqs),
        "android_unique_arrivals": int(combined["android_unique_arrivals"]),
        "android_duplicate_arrivals": int(combined["android_duplicate_arrivals"]),
        "android_missing_host_successes": int(combined["host_successes_missing_on_android"]),
        "capture_interval_p95_ms": percentile(intervals, 0.95),
        "capture_interval_max_ms": max(intervals) if intervals else None,
        "classification": classification,
        "privacy_note": "Raw PCAP remains local and may contain network addresses.",
    }

    (session / "opal_bridge_boundary_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "=== OPAL BRIDGE-BOUNDARY RESULT ===",
        f"host_successful_sends = {result['host_successful_sends']}",
        f"bridge_pcap_bytes = {result['pcap_bytes']}",
        f"bridge_total_pcap_records = {result['pcap_total_records']}",
        f"bridge_linktype = {result['pcap_linktype']}",
        f"bridge_matched_utp1_packets = {result['matched_utp1_packets']}",
        f"bridge_unique_utp1_sequences = {result['unique_utp1_sequences']}",
        f"bridge_same_stamp_duplicates = {result['same_stamp_duplicates']}",
        f"bridge_conflicting_stamp_duplicates = {result['conflicting_stamp_duplicates']}",
        f"missing_at_bridge = {result['host_successes_missing_at_bridge']}",
        f"bridge_only_sequences = {result['bridge_sequences_not_in_host_successes']}",
        f"bridge_p95_ms = {result['capture_interval_p95_ms']}",
        f"bridge_max_ms = {result['capture_interval_max_ms']}",
        f"android_unique = {result['android_unique_arrivals']}",
        f"android_duplicates = {result['android_duplicate_arrivals']}",
        f"android_missing = {result['android_missing_host_successes']}",
        f"classification = {classification}",
        f"session = {session}",
        "privacy = Raw PCAP contains local network metadata; do not upload it.",
    ]
    text = "\n".join(lines) + "\n"
    (session / "opal_bridge_boundary_summary.txt").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
