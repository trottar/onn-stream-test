#!/usr/bin/env python3
"""G-A5 (G-A4's g_a4_state.py, plus the routing class of the newest token_issued, the class and time only): one read-only state snapshot (the precondition / after-restart / end reads). Writes nothing but stdout (JSON):
tools/e3_state.py's line; the privyhub-* units active; /session/status (counts only); the UTC clock and whether it is in
04:30-05:30Z; the onn's band (mWifiInfo parsed in memory: frequency / band / standard / RSSI / tx / rx only); the seven
client properties (values only); e3_flag.conf present. adb for reads only (getprop, dumpsys).
    python3 -B g_a4_state.py
"""
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

REPO = Path(__file__).resolve().parents[4]
PROPS = ("restart_guard", "stall_signal", "link_notice", "link_report", "loss_guard", "wifi_lock", "opus_decode")
WIFI = {"Wi-Fi standard": "standard", "RSSI": "rssi_dbm", "Tx Link speed": "tx_mbps", "Rx Link speed": "rx_mbps",
        "Frequency": "freq_mhz"}


def run(cmd, t=30):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=t).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


now = datetime.now(timezone.utc)
mins = now.hour * 60 + now.minute
r = {"at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "in_watch_hour": 270 <= mins < 330}
try:
    r["e3_state"] = json.loads(run([sys.executable, "-B", str(REPO / "tools/e3_state.py")], 120) or "{}")
except ValueError:
    r["e3_state"] = None
r["units_active"] = [l.split()[0] for l in run(["systemctl", "--user", "list-units", "--state=active", "--no-legend",
                                                "--plain", "privyhub-*"]).splitlines() if l.strip()]
try:
    with urllib.request.urlopen("http://127.0.0.1:8765/session/status", timeout=10) as fh:
        s = json.loads(fh.read())
    r["session_status"] = {k: s.get(k) for k in ("ok", "mode", "paired_devices", "active_sessions", "pairing_window_open")}
except Exception as e:      # noqa: BLE001
    r["session_status"] = {"error": type(e).__name__}
line = run(["adb", "shell", "dumpsys wifi | grep -m1 '^mWifiInfo'"])
b = {}
for k, n in WIFI.items():
    m = re.search(r"(?:^|, )" + re.escape(k) + r": (-?\d+)", line)
    b[n] = int(m.group(1)) if m else None
f = b.get("freq_mhz")
b["band"] = None if f is None else "5" if 4900 <= f < 5900 else "2.4" if 2400 <= f < 2500 else "6" if f >= 5925 else "?"
r["band"] = b
r["props"] = {p: run(["adb", "shell", "getprop", f"debug.privyhub.{p}"]).strip() for p in PROPS}
r["props_all_empty"] = all(v == "" for v in r["props"].values())
r["e3_flag_conf_present"] = (Path.home() / ".config/systemd/user/privyhub-companion.service.d/e3_flag.conf").exists()
r["dropins"] = sorted(p.name for p in (Path.home() / ".config/systemd/user/privyhub-companion.service.d").glob("*.conf"))
try:
    _t = [l for l in open(REPO / "logs/session_audit.jsonl") if "\"token_issued\"" in l][-1]
    _d = json.loads(_t)
    r["routing_newest_token"] = {"t": _d.get("t"), "routing_evidence": _d.get("routing_evidence")}
except (OSError, ValueError, IndexError):
    r["routing_newest_token"] = None
print(json.dumps(r))
