#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

IFACES = ("wlan0", "wlan1", "br-lan")
FIELDS = ("rx_packets", "tx_packets", "rx_bytes", "tx_bytes", "rx_dropped", "tx_dropped")


def load_samples(path: Path):
    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 2:
        raise ValueError("counter sample file has fewer than two rows")

    parsed = []
    for row in rows:
        item = {"sample": int(row["sample"])}
        for iface in IFACES:
            for field in FIELDS:
                key = f"{iface}_{field}"
                item[key] = int(row[key])
        parsed.append(item)
    return parsed


def delta(a, b, iface, field):
    return b[f"{iface}_{field}"] - a[f"{iface}_{field}"]


def iface_summary(samples, iface):
    first, last = samples[0], samples[-1]
    result = {field: delta(first, last, iface, field) for field in FIELDS}

    per_interval = []
    for a, b in zip(samples, samples[1:]):
        per_interval.append({
            "rx_packets": delta(a, b, iface, "rx_packets"),
            "tx_packets": delta(a, b, iface, "tx_packets"),
            "rx_bytes": delta(a, b, iface, "rx_bytes"),
            "tx_bytes": delta(a, b, iface, "tx_bytes"),
        })

    result["max_interval_rx_packets"] = max(x["rx_packets"] for x in per_interval)
    result["max_interval_tx_packets"] = max(x["tx_packets"] for x in per_interval)
    result["max_interval_rx_bytes"] = max(x["rx_bytes"] for x in per_interval)
    result["max_interval_tx_bytes"] = max(x["tx_bytes"] for x in per_interval)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    args = ap.parse_args()
    session = Path(args.session)

    samples = load_samples(session / "router_netdev_counters.csv")
    combined = json.loads((session / "combined_summary.json").read_text(encoding="utf-8"))

    summaries = {iface: iface_summary(samples, iface) for iface in IFACES}
    host_success = int(combined["host_successful_sends"])
    android_unique = int(combined["android_unique_arrivals"])
    android_dups = int(combined["android_duplicate_arrivals"])
    android_missing = int(combined["host_successes_missing_on_android"])

    w0 = summaries["wlan0"]
    w1 = summaries["wlan1"]
    br = summaries["br-lan"]

    radio_signal = max(
        w0["rx_packets"], w0["tx_packets"],
        w1["rx_packets"], w1["tx_packets"],
    )

    if radio_signal < max(50, int(host_success * 0.10)):
        classification = "LITTLE_OR_NO_NORMAL_NETDEV_ACCOUNTING_SIGNAL"
    elif max(br["rx_packets"], br["tx_packets"]) < max(50, int(host_success * 0.10)):
        classification = "RADIO_NETDEV_ACCOUNTING_WITH_LITTLE_BRIDGE_MASTER_SIGNAL"
    else:
        classification = "NORMAL_NETDEV_ACCOUNTING_SIGNAL_PRESENT"

    result = {
        "probe": "PrivyHub Opal netdev counter probe",
        "samples": len(samples),
        "host_successful_sends": host_success,
        "android_unique_arrivals": android_unique,
        "android_duplicate_arrivals": android_dups,
        "android_missing_host_successes": android_missing,
        "interfaces": summaries,
        "classification": classification,
        "caution": "Interface counters are aggregate accounting signals and cannot prove packet identity or duplication origin.",
    }

    (session / "opal_netdev_counter_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "=== OPAL NETDEV-COUNTER RESULT ===",
        f"samples = {len(samples)}",
        f"host_successful_sends = {host_success}",
    ]

    for iface in IFACES:
        s = summaries[iface]
        prefix = iface.replace("-", "_")
        lines.extend([
            f"{prefix}_rx_packets_delta = {s['rx_packets']}",
            f"{prefix}_tx_packets_delta = {s['tx_packets']}",
            f"{prefix}_rx_bytes_delta = {s['rx_bytes']}",
            f"{prefix}_tx_bytes_delta = {s['tx_bytes']}",
            f"{prefix}_rx_dropped_delta = {s['rx_dropped']}",
            f"{prefix}_tx_dropped_delta = {s['tx_dropped']}",
            f"{prefix}_max_1s_rx_packets = {s['max_interval_rx_packets']}",
            f"{prefix}_max_1s_tx_packets = {s['max_interval_tx_packets']}",
        ])

    lines.extend([
        f"android_unique = {android_unique}",
        f"android_duplicates = {android_dups}",
        f"android_missing = {android_missing}",
        f"classification = {classification}",
        f"session = {session}",
        "caution = Interface counters are aggregate; they do not identify individual UTP1 packets.",
    ])

    text = "\n".join(lines) + "\n"
    (session / "opal_netdev_counter_summary.txt").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
