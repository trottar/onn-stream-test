#!/usr/bin/env python3
"""D6-R1: the six valid runs beside the last pre-B2 runs, and the classification
pre-registered in d6_r1_preregistration.txt (SIGNATURE = >= 20 same-stamp
duplicates in a run, the suite's own analyzer threshold; REPRODUCED >= 2 of 3,
NOT REPRODUCED 0 of 3, INDETERMINATE 1 of 3 or not runnable). Read-only.
Pre-B2 references are read from logs/transport_probe and logs/transport_reverse
(argv[1] = repo root)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "..", "..")
FWD = [("fwd1", "valid"), ("fwd2", "valid"), ("fwd3", "INVALID: the onn's screensaver ended the receiver after 0.7 s"),
       ("fwd3b", "valid (retry of fwd3)")]
REV = [("rev1", "valid"), ("rev2", "INVALID: the onn's screensaver ended the sender at 2,088 packets"),
       ("rev3", "INVALID: the onn's screensaver ended the sender at 2,095 packets"),
       ("rev2b", "valid (retry of rev2)"), ("rev3b", "valid (retry of rev3)")]
PRE_FWD = [("Test A (linux_idle, 2026-09-15 09:40)", "logs/transport_probe/linux_idle_20260915_094026"),
           ("D082 (opal_bridge, 2026-09-15 14:12)", "logs/transport_probe/opal_bridge_20260915_141216")]
PRE_REV = [("Test B (linux_reverse_idle, 2026-09-15 09:45)", "logs/transport_reverse/linux_reverse_idle_20260915_094554")]


def fwd_row(path):
    c = json.load(open(os.path.join(path, "combined_summary.json")))
    k = c.get("android_kernel_arrival_intervals_for_matched_consecutive_sequences", {})
    return {"sent": c["host_successful_sends"], "arrived": c["android_unique_arrivals"],
            "missing": c["host_successes_missing_on_android"],
            "dup_same": c["android_duplicate_same_host_packet_stamp"],
            "dup_conf": c["android_duplicate_conflicting_host_packet_stamp"],
            "lt2": c.get("host_4_to_6_ms_but_kernel_lt_2_ms"), "ge20": c.get("host_4_to_6_ms_but_kernel_ge_20_ms"),
            "p95": k.get("p95_ms"), "max": k.get("max_ms"), "reordered": None}


def rev_row(path):
    c = json.load(open(os.path.join(path, "combined_summary.json")))
    h = json.load(open(os.path.join(path, "host_summary.json")))
    return {"sent": c["android_sender_successes"], "arrived": c["windows_unique_arrivals"],
            "missing": c["sender_successes_missing_on_windows"],
            "dup_same": c["windows_duplicate_same_sender_stamp"], "dup_conf": c["windows_duplicate_conflicting_sender_stamp"],
            "lt2": c.get("android_4_to_6_ms_but_windows_lt_2_ms"), "ge20": c.get("android_4_to_6_ms_but_windows_ge_20_ms"),
            "p95": (c.get("windows_receive_intervals_for_matched_consecutive_sequences") or {}).get("p95_ms"),
            "max": (c.get("windows_receive_intervals_for_matched_consecutive_sequences") or {}).get("max_ms"),
            "reordered": h.get("reordered_packets")}


def android_reordered(path):
    try:
        a = json.load(open(os.path.join(path, "android_summary.json")))
        return (a.get("stats") or {}).get("reordered_packets")
    except Exception:
        return None


HDR = f"  {'run':<44} {'sent':>5} {'arrived':>7} {'missing':>7} {'dup same':>8} {'dup conf':>8} {'4-6->lt2':>8} {'4-6->ge20':>9} {'p95 ms':>7} {'max ms':>7} {'reord':>5}"


def line(name, r):
    f = lambda v: "-" if v is None else (f"{v:.1f}" if isinstance(v, float) else str(v))  # noqa: E731
    return (f"  {name:<44} {f(r['sent']):>5} {f(r['arrived']):>7} {f(r['missing']):>7} {f(r['dup_same']):>8} "
            f"{f(r['dup_conf']):>8} {f(r['lt2']):>8} {f(r['ge20']):>9} {f(r['p95']):>7} {f(r['max']):>7} {f(r['reordered']):>5}")


verdict = {}
for label, runs, pre, fn in (("FORWARD host -> onn", FWD, PRE_FWD, fwd_row), ("REVERSE onn -> host", REV, PRE_REV, rev_row)):
    print(f"=== {label} ===")
    print(HDR)
    for name, d in pre:
        p = os.path.join(ROOT, d)
        r = fn(p)
        if fn is fwd_row:
            r["reordered"] = android_reordered(p)
        print(line("pre-B2 " + name, r))
    valid = []
    for name, status in runs:
        p = os.path.join(HERE, name)
        try:
            r = fn(p)
            if fn is fwd_row:
                r["reordered"] = android_reordered(p)
        except Exception as exc:  # noqa: BLE001
            print(f"  {name:<44} unreadable ({type(exc).__name__}) -- {status}")
            continue
        print(line(f"{name} [{status}]", r))
        if status.startswith("valid"):
            valid.append((name, r))
    sig = [n for n, r in valid if r["dup_same"] >= 20]
    n = len(valid)
    if n < 3:
        v = "INDETERMINATE (fewer than 3 valid runs)"
    elif len(sig) >= 2:
        v = "REPRODUCED"
    elif len(sig) == 0:
        v = "NOT REPRODUCED"
    else:
        v = "INDETERMINATE (1 of 3)"
    verdict[label] = v
    print(f"  valid runs {n}; signature (>= 20 same-stamp duplicates) in {len(sig)}: {sig}")
    print(f"  -> {v}")
    print()
print("=== CLASSIFICATION (pre-registered) ===")
for k, v in verdict.items():
    print(f"  {k}: {v}")
if all(v == "NOT REPRODUCED" for v in verdict.values()):
    print("  -> roadmap D6: the pathology is SPECIFIC TO THE OLD ENVIRONMENT (not reproduced on the representative path)")
elif all(v == "REPRODUCED" for v in verdict.values()):
    print("  -> roadmap D6: reproduced in both directions (broader-transport claims admissible)")
elif any(v == "REPRODUCED" for v in verdict.values()):
    print("  -> roadmap D6: REPRODUCED ON THE REPRESENTATIVE PATH in one direction")
else:
    print("  -> roadmap D6: not classifiable on this replay")
