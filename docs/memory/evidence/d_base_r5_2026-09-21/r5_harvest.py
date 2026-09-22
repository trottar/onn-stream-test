#!/usr/bin/env python3
"""D-BASE-P4: harvest the onn's own radio series after a session.

The device keeps a WifiScoreReport ring at ~3 s cadence with wall-clock
timestamps, and wifiscanner keeps a timestamped scan-event log. Both are
append-only, so one dump after a session recovers the whole session at 3 s
resolution having cost the radio nothing while it ran — finer and cheaper
than sampling `dumpsys wifi` (368-387 ms on-device) during play.

usage: p4_harvest.py <label> <outdir>
"""
import json, re, subprocess, sys
from datetime import datetime, timedelta, timezone

LABEL, OUTDIR = sys.argv[1], sys.argv[2]

_MAC = re.compile(r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b")
_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_QUOTED = re.compile(r'"[^"\n]{1,32}"')


def redact_text(t):
    """For raw device TEXT: also strips any quoted string, which is where an
    SSID would appear."""
    if not isinstance(t, str):
        return t
    t = _MAC.sub("<redacted>", t)
    t = _IP.sub("<redacted>", t)
    return _QUOTED.sub("<redacted>", t)


def redact_json(t):
    """For SERIALIZED JSON: MAC and IP only. The quoted-string rule would eat
    every JSON key. Nothing extracted below is an SSID or BSSID by
    construction - only numbers, enums and package names reach the output."""
    t = _MAC.sub("<redacted>", t)
    return _IP.sub("<redacted>", t)


def adb(cmd, timeout=40):
    try:
        return subprocess.run(["adb", "shell", cmd], capture_output=True,
                              text=True, timeout=timeout).stdout
    except Exception:
        return ""


# device UTC offset, so the log's local stamps can be put on the host clock
off_raw = adb("date '+%z'").strip()
try:
    sign = 1 if off_raw.startswith("+") else -1
    off = sign * timedelta(hours=int(off_raw[1:3]), minutes=int(off_raw[3:5]))
except Exception:
    off = timedelta(0)

wifi = adb("dumpsys wifi")
scanner = adb("dumpsys wifiscanner")

# --- association snapshot -------------------------------------------------
assoc = {}
m = re.search(r"mWifiInfo (.+)", wifi)
if m:
    line = m.group(1)
    for key, pat, cast in (
        ("rssi_dbm", r"RSSI:\s*(-?\d+)", int),
        ("tx_link_speed_mbps", r"Tx Link speed:\s*(\d+)", int),
        ("rx_link_speed_mbps", r"Rx Link speed:\s*(\d+)", int),
        ("max_tx_link_speed_mbps", r"Max Supported Tx Link speed:\s*(\d+)", int),
        ("frequency_mhz", r"Frequency:\s*(\d+)", int),
        ("wifi_standard", r"Wi-Fi standard:\s*(\d+)", int),
        ("score", r"score:\s*(\d+)", int),
    ):
        mm = re.search(pat, line)
        if mm:
            assoc[key] = cast(mm.group(1))
    mm = re.search(r"Supplicant state:\s*(\w+)", line)
    if mm:
        assoc["supplicant_state"] = mm.group(1)
mm = re.search(r"channelWidth = (\d+)", wifi)
if mm:
    w = int(mm.group(1))
    assoc["channel_width_code"] = w
    assoc["channel_width_mhz"] = {0: 20, 1: 40, 2: 80, 3: 160, 4: 80}.get(w)
if assoc.get("frequency_mhz"):
    f = assoc["frequency_mhz"]
    assoc["band"] = "5GHz" if f >= 4900 else ("6GHz" if f >= 5925 else "2.4GHz")
    assoc["channel"] = (f - 5000) // 5 if f >= 4900 else (f - 2407) // 5

# --- WifiScoreReport: the 3 s series --------------------------------------
COLS = ("time,session,netid,rssi,filtered_rssi,rssi_threshold,freq,txLinkSpeed,"
        "rxLinkSpeed,txTput,rxTput,bcnCnt,tx_good,tx_retry,tx_bad,rx_pps,"
        "nudrq,nuds,s1,s2,score")
names = COLS.split(",")
rows = []
for line in wifi.splitlines():
    if not re.match(r"^\d+-\d+ \d+:\d+:\d+\.\d+,", line):
        continue
    parts = line.split(",")
    if len(parts) != len(names):
        continue
    d = dict(zip(names, parts))
    try:
        t = datetime.strptime("2026-" + d["time"], "%Y-%m-%d %H:%M:%S.%f")
        d["at_utc"] = (t - off).replace(tzinfo=timezone.utc).isoformat(
            timespec="milliseconds").replace("+00:00", "Z")
    except Exception:
        d["at_utc"] = None
    rows.append(d)

# --- scan events ----------------------------------------------------------
scans = []
for line in scanner.splitlines():
    m = re.match(r"\s*(\d{4}-\d{2}-\d{2}T[\d:.]+)\s*-\s*(.*)", line)
    if not m:
        continue
    kind = m.group(2)
    if not re.search(r"start scan|addSingleScanRequest|singleScanResults", kind):
        continue
    try:
        t = datetime.strptime(m.group(1)[:26], "%Y-%m-%dT%H:%M:%S.%f")
        at = (t - off).replace(tzinfo=timezone.utc).isoformat(
            timespec="milliseconds").replace("+00:00", "Z")
    except Exception:
        at = None
    ev = ("start_scan" if "start scan" in kind else
          "scan_request" if "addSingleScanRequest" in kind else "scan_results")
    band = None
    bm = re.search(r"band:([^ ]+(?: & [^ ]+)*)", kind)
    if bm:
        band = bm.group(1)
    nres = None
    rm = re.search(r"results=(\d+)", kind)
    if rm:
        nres = int(rm.group(1))
    pm = re.search(r"package ([\w.]+)", kind)
    scans.append({"at_utc": at, "event": ev, "requested_band": band,
                  "results": nres, "package": pm.group(1) if pm else None})

out = {
    "schema": "privyhub_p4_air_harvest_v1",
    "label": LABEL,
    "harvested_at_utc": datetime.now(timezone.utc).isoformat(
        timespec="milliseconds").replace("+00:00", "Z"),
    "device_utc_offset": off_raw,
    "association": assoc,
    "score_report_rows": rows,
    "score_report_columns": names,
    "scan_events": scans,
    "notes": {
        "tx_retry_tx_bad_bcnCnt": "present as columns, identically 0 on this "
                                  "build - the driver does not populate them",
        "proc_net_wireless_discards": "present as columns, identically 0",
        "noise_dbm": "-256 means the driver does not report noise",
    },
}
path = f"{OUTDIR}/air_harvest_{LABEL}.json"
with open(path, "w") as fh:
    json.dump(json.loads(redact_json(json.dumps(out))), fh, indent=1)
print(f"[{LABEL}] harvest: {len(rows)} score rows, {len(scans)} scan events, "
      f"band={assoc.get('band')} ch={assoc.get('channel')} "
      f"width={assoc.get('channel_width_mhz')}MHz rssi={assoc.get('rssi_dbm')} "
      f"tx={assoc.get('tx_link_speed_mbps')} rx={assoc.get('rx_link_speed_mbps')}")
