#!/usr/bin/env python3
"""O1: turn one redacted sampling round into a JSON line.

Input is the already-redacted text of a round on stdin; identifiers are
gone by this point (station MACs are stable labels such as sta-A).

Anything the driver does not populate is recorded as absent, never as 0 --
`D-BASE-P4` showed how much that distinction matters on this stack. Two
shapes of that rule are load-bearing here:

  * This driver's `survey dump` does NOT accumulate. `channel active time`
    reads a fixed 30 ms on every call and the other survey fields
    (receive/transmit/extension-busy time) are absent entirely. So the
    survey pair is an instantaneous 30 ms window, not a counter: it is
    recorded as `airtime.window_ms` / `airtime.busy_ms`, never differenced.
  * `iw dev <if> info` prints `channel utilization` on this build. It is
    the same measurement rounded -- busy_ms/window_ms -- so it is kept
    beside the pair rather than instead of it, and disagreement between
    them is itself a signal.
"""
import json, os, re, sys

txt = sys.stdin.read()
sec, cur = {}, None
for line in txt.splitlines():
    m = re.match(r"===([A-Z0-9]+)===", line.strip())
    if m:
        cur = m.group(1)
        sec[cur] = []
    elif cur is not None:
        sec[cur].append(line)
blk = {k: "\n".join(v) for k, v in sec.items()}


def num(pat, text, cast=int):
    m = re.search(pat, text or "")
    try:
        return cast(m.group(1)) if m else None
    except (TypeError, ValueError):
        return None


# --- airtime: the point of the exercise ---------------------------------
info = blk.get("INFO", "")
airtime = {
    "channel": num(r"channel\s+(\d+)", info),
    "width_mhz": num(r"width:\s*(\d+)", info),
    "txpower_dbm": num(r"txpower\s+([\d.]+)", info, float),
    "noise_dbm_info": num(r"noise\s+(-?\d+)\s*dbm", info),
    "utilization_pct": num(r"channel utilization\s+([\d.]+)\s*%", info, float),
}

s = blk.get("SURVEY", "")
for b in re.split(r"(?=Survey data from)", s):
    if "[in use]" not in b:
        continue
    airtime.update({
        "frequency_mhz": num(r"frequency:\s*(\d+)", b),
        "noise_dbm": num(r"noise:\s*(-?\d+)", b),
        "window_ms": num(r"channel active time:\s*(\d+)", b),
        "busy_ms": num(r"channel busy time:\s*(\d+)", b),
        # absent on this driver; parsed anyway so a different one is caught
        "ext_busy_ms": num(r"extension channel busy time:\s*(\d+)", b),
        "rx_ms": num(r"channel receive time:\s*(\d+)", b),
        "tx_ms": num(r"channel transmit time:\s*(\d+)", b),
    })
    break
if airtime.get("window_ms") and airtime.get("busy_ms") is not None:
    airtime["busy_fraction"] = round(
        airtime["busy_ms"] / airtime["window_ms"], 5)
airtime = {k: v for k, v in airtime.items() if v is not None} or None

# --- stations -----------------------------------------------------------
stations = []
for b in re.split(r"(?=Station )", blk.get("STATION", "")):
    if not b.strip().startswith("Station"):
        continue
    row = {
        "station": (re.search(r"Station\s+(\S+)", b) or [None, None])[1],
        "signal_dbm": num(r"signal:\s*(-?\d+)", b),
        "signal_avg_dbm": num(r"signal avg:\s*(-?\d+)", b),
        "tx_bitrate_mbps": num(r"tx bitrate:\s*([\d.]+)", b, float),
        "rx_bitrate_mbps": num(r"rx bitrate:\s*([\d.]+)", b, float),
        "tx_width_mhz": num(r"tx bitrate:[^\n]*?\b(\d+)MHz", b),
        "tx_mcs": num(r"tx bitrate:[^\n]*?MCS\s+(\d+)", b),
        "tx_nss": num(r"tx bitrate:[^\n]*?NSS\s+(\d+)", b),
        "tx_packets": num(r"tx packets:\s*(\d+)", b),
        "tx_bytes": num(r"tx bytes:\s*(\d+)", b),
        "tx_retries": num(r"tx retries:\s*(\d+)", b),
        "tx_failed": num(r"tx failed:\s*(\d+)", b),
        "rx_packets": num(r"rx packets:\s*(\d+)", b),
        "rx_bytes": num(r"rx bytes:\s*(\d+)", b),
        "rx_drop_misc": num(r"rx drop misc:\s*(\d+)", b),
        "expected_tput_mbps": num(r"expected throughput:\s*([\d.]+)", b, float),
        "connected_time_s": num(r"connected time:\s*(\d+)", b),
        "inactive_time_ms": num(r"inactive time:\s*(\d+)", b),
    }
    stations.append({k: v for k, v in row.items() if v is not None})

# --- interface counters -------------------------------------------------
stats = {}
for line in blk.get("STATS", "").splitlines():
    p = line.split()
    if len(p) == 3 and p[2].isdigit():
        stats.setdefault(p[0], {})[p[1]] = int(p[2])

load = blk.get("LOAD", "").split()
row = {
    "schema": "privyhub_o1_opal_sample_v1",
    "seq": int(os.environ.get("SEQ", 0)),
    "at_utc": os.environ.get("NOW"),
    "round_cost_ms": int(os.environ.get("COST_MS", 0)),
    "iface": os.environ.get("IFACE"),
    "airtime": airtime,
    "stations": stations,
    "iface_stats": stats or None,
    "loadavg_1m": float(load[0]) if load else None,
    "mem_free_kb": num(r"MemFree:\s*(\d+)", blk.get("MEM", "")),
    "log_events": [l for l in blk.get("LOG", "").splitlines() if l.strip()],
}
print(json.dumps(row))
