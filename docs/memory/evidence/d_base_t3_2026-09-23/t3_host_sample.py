#!/usr/bin/env python3
"""D-BASE-T3 host sampler, every INTERVAL s (default 2):

  * the audio sender's own counters from native-stream-status
    (`audio.packets_sent`, `send_errors`, `helper_status.send.underflows`)
    -- the sender increments the RTP sequence for every packet it sends OR
    fails to send, so sent + send_errors = sequence advance and
    send_errors is the host-side share of the client's `lost_packets`;
  * the kernel's UDP counters (/proc/net/snmp Udp: OutDatagrams,
    SndbufErrors -- where a qdisc/sndbuf drop goes when sendto still
    returns success -- RcvbufErrors, InErrors) and Ip OutDiscards;
  * eno1 tx/rx drops and errors (/proc/net/dev);
  * the sender thread (native_tid from the status): the CPU it last ran on
    and the companion's Cpus_allowed_list; the encoder's CPU % and CPU.

Numbers only; nothing identifying.
    t3_host_sample.py <out.jsonl> [interval_s]    stop: touch <out.jsonl>.stop
"""
import json, os, subprocess, sys, time
from datetime import datetime, timezone

OUT = sys.argv[1]
INTERVAL = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
STOP = OUT + ".stop"
CLK = os.sysconf("SC_CLK_TCK")
prev = {}


def snmp():
    out, lines = {}, open("/proc/net/snmp").read().splitlines()
    for a, b in zip(lines, lines[1:]):
        if a.split(":")[0] == b.split(":")[0] and a.split()[1:] and not a.split()[1].isdigit():
            proto = a.split(":")[0]
            for k, v in zip(a.split()[1:], b.split()[1:]):
                if (proto, k) in (("Udp", "OutDatagrams"), ("Udp", "SndbufErrors"), ("Udp", "RcvbufErrors"),
                                  ("Udp", "InErrors"), ("Ip", "OutDiscards")):
                    out[f"{proto}.{k}"] = int(v)
    return out


def netdev():
    for line in open("/proc/net/dev"):
        if line.strip().startswith("eno1:"):
            v = [int(x) for x in line.split(":", 1)[1].split()]
            return {"rx_drop": v[3], "rx_errs": v[2], "tx_drop": v[11], "tx_errs": v[10], "tx_packets": v[9]}
    return {}


def stat_fields(path):
    try:
        return open(path).read().rsplit(")", 1)[1].split()
    except Exception:
        return None


def cpu_pct(key, fields):
    ticks = int(fields[11]) + int(fields[12])
    now = time.monotonic()
    p = prev.get(key)
    prev[key] = (ticks, now)
    return round(100.0 * (ticks - p[0]) / CLK / (now - p[1]), 1) if p else None


def companion_pid():
    try:
        return int(subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value",
                                   "privyhub-companion"], capture_output=True, text=True, timeout=3).stdout.strip())
    except Exception:
        return None


def encoder_pid():
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                if os.path.basename(os.readlink(f"/proc/{pid}/exe")) == "ffmpeg" and \
                   b"h264_vaapi" in open(f"/proc/{pid}/cmdline", "rb").read():
                    return int(pid)
            except Exception:
                pass
    return None


while not os.path.exists(STOP):
    t0 = time.monotonic()
    row = {"at_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")}
    try:
        st = json.loads(subprocess.run(["curl", "-s", "-m", "1.5", "localhost:8765/plugins/games/native-stream-status"],
                                       capture_output=True, text=True, timeout=3).stdout)
        a = st.get("audio") or {}
        hs = a.get("helper_status") or {}
        row["sender"] = {"active": a.get("active"), "packets_sent": a.get("packets_sent"),
                         "send_errors": a.get("send_errors"),
                         "underflows": (hs.get("send") or {}).get("underflows"),
                         "native_tid": (hs.get("scheduler") or {}).get("native_tid")}
    except Exception as exc:
        row["sender"] = {"error": type(exc).__name__}
    row["snmp"] = snmp()
    row["eno1"] = netdev()
    cp = companion_pid()
    tid = (row.get("sender") or {}).get("native_tid")
    if cp and tid:
        f = stat_fields(f"/proc/{cp}/task/{tid}/stat")
        if f:
            row["sender_thread"] = {"last_cpu": int(f[36]), "cpu_pct": cpu_pct("sender", f)}
        try:
            row["cpus_allowed"] = [l.split(":", 1)[1].strip() for l in open(f"/proc/{cp}/task/{tid}/status")
                                   if l.startswith("Cpus_allowed_list")][0]
        except Exception:
            pass
    ep = encoder_pid()
    if ep:
        f = stat_fields(f"/proc/{ep}/stat")
        if f:
            row["encoder"] = {"last_cpu": int(f[36]), "cpu_pct": cpu_pct(f"enc{ep}", f)}
    row["cost_ms"] = round((time.monotonic() - t0) * 1000)
    with open(OUT, "a") as fh:
        fh.write(json.dumps(row) + "\n")
    time.sleep(max(0.0, INTERVAL - (time.monotonic() - t0)))
