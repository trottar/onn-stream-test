#!/usr/bin/env python3
"""D-BASE-P4 air-telemetry sampler.

Host-side only: reads the onn's radio state over adb and the companion's own
relay counters, so the host's send rate and the onn's receive state sit on one
clock. No client or companion code changes; nothing is installed on the onn.

Every identifier is redacted before anything is written: MACs/BSSIDs, quoted
SSIDs, the SSID string itself and IPv4 addresses all become <redacted>.
Band, channel, width and counters are what matter and are kept.

usage: p4_sample.py <outfile> [interval_s] [stopfile]
"""
import json, re, subprocess, sys, time
from datetime import datetime, timezone

OUT = sys.argv[1]
INTERVAL = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
STOP = sys.argv[3] if len(sys.argv) > 3 else OUT + ".stop"

STATUS_URL = "http://localhost:8765/plugins/games/native-stream-status"

_MAC = re.compile(r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b")
_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_QSSID = re.compile(r'SSID:\s*"[^"]*"')
_QUOTED = re.compile(r'"[^"\n]{1,32}"')


def redact(text):
    """Applied to raw device TEXT only, never to serialized JSON — a quoted
    string in JSON would otherwise be mistaken for an SSID."""
    if not isinstance(text, str) or not text:
        return text
    text = _MAC.sub("<redacted>", text)
    text = _IP.sub("<redacted>", text)
    text = _QSSID.sub("SSID: <redacted>", text)
    text = _QUOTED.sub("<redacted>", text)
    return text


def adb(cmd, timeout=15):
    try:
        r = subprocess.run(["adb", "shell", cmd], capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout
    except Exception:
        return None


# One adb round trip per sample: /proc/net/wireless plus the scanner log's
# scan-event tail. Measured 77-87 ms on-device, well under the 300 ms bar.
ROUND = (
    "cat /proc/net/wireless 2>/dev/null; echo '===SCAN==='; "
    "S=$(dumpsys wifiscanner 2>/dev/null); "
    "echo \"$S\" | grep -c 'start scan'; "
    "echo \"$S\" | grep 'start scan' | tail -1"
)


def parse_wireless(block):
    """/proc/net/wireless: status, link quality, level, noise, discarded
    counters and missed beacons, for wlan0 only."""
    for line in (block or "").splitlines():
        if not line.strip().startswith("wlan0:"):
            continue
        f = line.replace("wlan0:", " ").split()
        try:
            return {
                "status": f[0],
                "link_quality": float(f[1].rstrip(".")),
                "level_dbm": float(f[2].rstrip(".")),
                "noise_dbm": float(f[3].rstrip(".")),
                "disc_nwid": int(f[4]), "disc_crypt": int(f[5]),
                "disc_frag": int(f[6]), "disc_retry": int(f[7]),
                "disc_misc": int(f[8]), "missed_beacon": int(f[9]),
            }
        except (IndexError, ValueError):
            return {"parse_error": True, "raw": line.strip()}
    return None


def host_counters():
    try:
        import urllib.request
        with urllib.request.urlopen(STATUS_URL, timeout=4) as r:
            d = json.loads(r.read().decode())
    except Exception:
        return None
    n = d.get("native_stream", d)
    fec = n.get("fec") or {}
    hb = n.get("last_heartbeat") or {}
    return {
        "relay_running": fec.get("running"),
        "relay_rtp_packets": fec.get("rtp_packets"),
        "relay_parity_packets": fec.get("parity_packets"),
        "relay_sent_bytes": fec.get("sent_bytes"),
        "relay_send_errors": fec.get("send_errors"),
        "client_rx_packets": hb.get("rx_packets"),
        "client_rendered_frames": hb.get("rendered_frames"),
        "client_elapsed_ms": hb.get("elapsed_ms"),
        "client_last_output_age_ms": hb.get("last_output_age_ms"),
    }


def main():
    seq = 0
    with open(OUT, "a", buffering=1) as fh:
        while True:
            import os
            if os.path.exists(STOP):
                return
            t0 = time.perf_counter()
            now = datetime.now(timezone.utc)
            raw = adb(ROUND)
            if raw is not None:
                raw = redact(raw)
            cost_ms = round((time.perf_counter() - t0) * 1000.0, 1)

            wireless = scan_count = scan_last = None
            if raw is not None:
                parts = raw.split("===SCAN===")
                wireless = parse_wireless(parts[0])
                if len(parts) > 1:
                    tail = [x for x in parts[1].strip().splitlines() if x.strip()]
                    if tail:
                        try:
                            scan_count = int(tail[0].strip())
                        except ValueError:
                            scan_count = None
                    if len(tail) > 1:
                        m = re.match(r"\s*(\S+)\s*-", tail[1])
                        scan_last = m.group(1) if m else None

            row = {
                "schema": "privyhub_p4_air_sample_v1",
                "seq": seq,
                "at_utc": now.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "sample_cost_ms": cost_ms,
                "onn_wireless": wireless,
                "onn_scan_total": scan_count,
                "onn_scan_last_local": scan_last,
                "host": host_counters(),
            }
            fh.write(json.dumps(row) + "\n")
            seq += 1
            time.sleep(max(0.0, INTERVAL - (time.perf_counter() - t0)))


if __name__ == "__main__":
    main()
