#!/usr/bin/env python3
"""LINK-L1 A2 -- the Opal's air view, read-only, numbers only.

    link_l1_air.py snapshot <out.jsonl> <label>
    link_l1_air.py loop <out.jsonl> <label> [interval_s=30]     stop: touch <out.jsonl>.stop

READ-ONLY ON THE OPAL. One `ssh opal` per round running only reads:
`iw dev wlan1 info`, `iw dev wlan1 survey dump`, `iw dev wlan1 station dump`, and (snapshot
only) `ubus call repeater scan {"cached":true}` -- the GL repeater daemon's cached scan list,
returned without triggering a scan. Nothing is set, committed, installed or written on the Opal.

PRIVACY: nothing the Opal prints is stored. SSIDs and BSSIDs are counted in memory and dropped;
the onn's hardware address is read once from `adb shell cmd wifi status`, held in memory only to
find its station row, and never written. Only numbers and fixed labels are written. Whether the
cached neighbour set changed since the previous snapshot is written as counts (added / removed),
computed from a salted in-memory hash that is never written.
"""
import hashlib, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

IF5 = "wlan1"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "opal"]
MAC = re.compile(r"([0-9a-f]{2}(?::[0-9a-f]{2}){5})", re.I)
STATE = "/tmp/link_l1_air_prev_set"   # salted hashes only, outside the repo; deleted at the end
SALT_F = "/tmp/link_l1_air_salt"       # a random per-run salt, outside the repo; deleted at the end
if not os.path.exists(SALT_F):
    with open(SALT_F, "w") as fh:
        fh.write(os.urandom(16).hex())
_salt = open(SALT_F).read().strip()


def run(cmd, timeout=25):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL).stdout
    except Exception as exc:
        return f"__error__ {type(exc).__name__}"


def num(pat, text, cast=float):
    m = re.search(pat, text)
    return cast(m.group(1)) if m else None


def onn_mac():
    t = run(["adb", "shell", "cmd wifi status"], timeout=10)
    m = re.search(r"MAC: " + MAC.pattern, t, re.I)
    return m.group(1).lower() if m else None


def block80(ch):
    """The 80 MHz block index of a 5 GHz primary channel (36-48 -> 0, 52-64 -> 1, ...)."""
    if 36 <= ch <= 64:
        return (ch - 36) // 16
    if 100 <= ch <= 144:
        return 2 + (ch - 100) // 16
    if 149 <= ch <= 177:
        return 5 + (ch - 149) // 16
    return None


def neighbours(raw, own_ch5, own_ch24):
    try:
        survey = json.loads(raw).get("survey") or []
    except Exception:
        return {"error": "scan cache not readable"}
    own_blk = block80(own_ch5) if own_ch5 else None
    out = {"entries": len(survey), "band_5g": 0, "band_2g": 0, "other_band": 0,
           "5g_same_primary": 0, "5g_in_use_80mhz_block": 0, "5g_adjacent_blocks": 0,
           "5g_in_block_signal_ge_-70": 0, "5g_in_block_signal_-70_to_-80": 0, "5g_in_block_signal_lt_-80": 0,
           "2g_same_channel": 0, "2g_overlapping_within_4": 0}
    keys = set()
    for e in survey:
        ch, freq, sig = e.get("channel"), e.get("freq") or 0, e.get("signal")
        b = e.get("bssid") or ""
        if b:
            keys.add(hashlib.sha256((_salt + b.lower()).encode()).hexdigest())
        if 4900 <= freq <= 5900:
            out["band_5g"] += 1
            if ch == own_ch5:
                out["5g_same_primary"] += 1
            blk = block80(ch) if isinstance(ch, int) else None
            if blk is not None and own_blk is not None:
                if blk == own_blk:
                    out["5g_in_use_80mhz_block"] += 1
                    if isinstance(sig, (int, float)):
                        k = ("5g_in_block_signal_ge_-70" if sig >= -70 else
                             "5g_in_block_signal_-70_to_-80" if sig >= -80 else "5g_in_block_signal_lt_-80")
                        out[k] += 1
                elif abs(blk - own_blk) == 1 and not (own_blk == 1 and blk == 2):
                    out["5g_adjacent_blocks"] += 1
        elif 2400 <= freq <= 2500:
            out["band_2g"] += 1
            if own_ch24 and ch == own_ch24:
                out["2g_same_channel"] += 1
            if own_ch24 and isinstance(ch, int) and abs(ch - own_ch24) <= 4:
                out["2g_overlapping_within_4"] += 1
        else:
            out["other_band"] += 1
    prev = set()
    if os.path.exists(STATE):
        prev = set(open(STATE).read().split())
    out["set_changed_since_previous_snapshot"] = (keys != prev) if prev else None
    out["added_since_previous"] = len(keys - prev) if prev else None
    out["removed_since_previous"] = len(prev - keys) if prev else None
    with open(STATE, "w") as fh:
        fh.write("\n".join(sorted(keys)))
    return out


def round_(mac, with_scan):
    cmd = (f"iw dev {IF5} info; echo @@S@@; iw dev {IF5} survey dump; echo @@S@@; "
           f"iw dev {IF5} station dump; echo @@S@@; iw dev wlan0 info; echo @@S@@; cat /proc/loadavg")
    if with_scan:
        cmd += "; echo @@S@@; ubus call repeater scan '{\"cached\":true}'"
    t0 = time.monotonic()
    t = run(SSH + [cmd])
    cost = round((time.monotonic() - t0) * 1000)
    if t.startswith("__error__"):
        return {"error": t, "cost_ms": cost}
    p = t.split("@@S@@")
    info, survey, sta, info24 = p[0], p[1], p[2], p[3]
    in_use = ""
    for blk in re.split(r"(?=frequency:)", survey):
        if "[in use]" in blk:
            in_use = blk
    ch5 = num(r"channel (\d+) \(", info, int)
    ch24 = num(r"channel (\d+) \(", info24, int)
    r = {"cost_ms": cost,
         "channel": ch5, "width_mhz": num(r"width: (\d+) MHz", info, int),
         "channel_utilization_pct": num(r"channel utilization ([\d.]+)%", info),
         "noise_dbm": num(r"noise:\s*(-?\d+)", in_use, int),
         "survey_active_ms": num(r"channel active time:\s*(\d+)", in_use, int),
         "survey_busy_ms": num(r"channel busy time:\s*(\d+)", in_use, int),
         "txpower_dbm": num(r"txpower ([\d.]+) dBm", info),
         "stations_5g": len(re.findall(r"^Station ", sta, re.M)),
         "ch24": ch24, "ch24_width_mhz": num(r"width: (\d+) MHz", info24, int),
         "ch24_utilization_pct": num(r"channel utilization ([\d.]+)%", info24),
         "opal_load1": num(r"^([\d.]+)", p[4].strip()),
         "onn_row_found": False}
    if mac:
        for b in re.split(r"(?=^Station )", sta, flags=re.M):
            if b.lower().startswith("station " + mac):
                r.update({"onn_row_found": True,
                          "signal_dbm": num(r"signal:\s*(-?\d+)", b, int),
                          "signal_avg_dbm": num(r"signal avg:\s*(-?\d+)", b, int),
                          "tx_bitrate_mbps": num(r"tx bitrate:\s*([\d.]+)", b),
                          "tx_mcs": num(r"tx bitrate:[^\n]*?MCS (\d+)", b, int),
                          "tx_nss": num(r"tx bitrate:[^\n]*?NSS (\d+)", b, int),
                          "tx_width_mhz": num(r"tx bitrate:[^\n]*?(\d+)MHz", b, int),
                          "rx_bitrate_mbps": num(r"rx bitrate:\s*([\d.]+)", b),
                          "rx_mcs": num(r"rx bitrate:[^\n]*?MCS (\d+)", b, int),
                          "tx_packets": num(r"tx packets:\s*(\d+)", b, int),
                          "tx_retries": num(r"tx retries:\s*(\d+)", b, int),
                          "tx_failed": num(r"tx failed:\s*(\d+)", b, int),
                          "rx_drop_misc": num(r"rx drop misc:\s*(\d+)", b, int),
                          "connected_s": num(r"connected time:\s*(\d+)", b, int)})
    if with_scan:
        r["neighbours"] = neighbours(p[5] if len(p) > 5 else "", ch5, ch24)
    return r


def stamp():
    now = datetime.now(timezone.utc)
    return now.isoformat(timespec="seconds").replace("+00:00", "Z"), datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def write(out, row):
    with open(out, "a") as fh:
        fh.write(json.dumps(row) + "\n")


def main():
    mode, out, label = sys.argv[1], sys.argv[2], sys.argv[3]
    mac = onn_mac()
    if mode == "snapshot":
        u, l = stamp()
        write(out, {"kind": "snapshot", "label": label, "at_utc": u, "local": l, **round_(mac, True)})
        return
    interval = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0
    stop = out + ".stop"
    seq, nxt = 0, time.monotonic()
    while not os.path.exists(stop):
        u, l = stamp()
        write(out, {"kind": "loop", "label": label, "seq": seq, "at_utc": u, **round_(mac, False)})
        seq += 1
        nxt += interval
        time.sleep(max(0.0, nxt - time.monotonic()))
    os.remove(stop)


if __name__ == "__main__":
    main()
