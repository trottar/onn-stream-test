#!/usr/bin/env python3
"""CTRL-L1 host sampler: where the controller datagrams go missing. READ-ONLY.

    ctrl_l1_host_sample.py <out.jsonl> [interval_s=10]   stop: touch <out.jsonl>.stop

Every round (10 s):
  socket  /proc/net/udp and /proc/net/udp6 rows whose LOCAL port is the
          controller port (from native-stream-status `controller.port`,
          refreshed with the status): rx_queue (bytes) and `drops`;
  stack   /proc/net/snmp `Udp:` (InDatagrams, NoPorts, InErrors,
          RcvbufErrors, InCsumErrors, MemErrors) -- cumulative, host-wide;
          /proc/net/softnet_stat summed over CPUs (processed, dropped,
          time_squeeze);
  nic     /sys/class/net/eno1/statistics rx_packets, rx_dropped, rx_errors,
          rx_missed_errors, rx_fifo_errors, rx_over_errors, rx_crc_errors.
Every third round (30 s):
  status  GET native-stream-status -> controller packets_received,
          lost_packets, rejected_packets, bad_packets, updates_by_player,
          and whether the stream is active;
  opal    one `ssh opal cat /proc/net/dev` (READ-ONLY): per-interface
          rx/tx packets, errs, drop for wlan1 (the onn's AP), br-lan and
          eth0 (toward the host).
Only numbers and interface names are written: no address, port owner or
identifier. The sampler never writes to a socket, never binds the port,
and touches nothing the stream uses.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

OUT = sys.argv[1]
INTERVAL = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
STOP = OUT + ".stop"
NIC = "eno1"
STATUS = "http://<loopback>:8765/plugins/games/native-stream-status"  # stored copy: the loopback literal is written <loopback> (redactor); the run used the loopback address
OPAL_IFS = ("wlan1", "br-lan", "eth0", "eth0.1")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def udp_rows(port):
    rows = []
    if not port:
        return rows
    for fam in ("udp", "udp6"):
        try:
            lines = open(f"/proc/net/{fam}").read().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            f = line.split()
            if len(f) < 13:
                continue
            lport = int(f[1].rsplit(":", 1)[1], 16)
            if lport != port:
                continue
            rows.append({"fam": fam, "rx_queue": int(f[4].split(":")[1], 16),
                         "drops": int(f[12]), "inode": int(f[9])})
    return rows


def snmp_udp():
    lines = [l for l in open("/proc/net/snmp").read().splitlines() if l.startswith("Udp:")]
    keys, vals = lines[0].split()[1:], [int(x) for x in lines[1].split()[1:]]
    d = dict(zip(keys, vals))
    return {k: d.get(k) for k in ("InDatagrams", "NoPorts", "InErrors", "RcvbufErrors",
                                  "InCsumErrors", "MemErrors")}


def softnet():
    tot = [0, 0, 0]
    for line in open("/proc/net/softnet_stat"):
        f = [int(x, 16) for x in line.split()]
        for i in range(3):
            tot[i] += f[i]
    return {"processed": tot[0], "dropped": tot[1], "time_squeeze": tot[2]}


def nic():
    out = {}
    for k in ("rx_packets", "rx_dropped", "rx_errors", "rx_missed_errors", "rx_fifo_errors",
              "rx_over_errors", "rx_crc_errors"):
        try:
            out[k] = int(open(f"/sys/class/net/{NIC}/statistics/{k}").read())
        except OSError:
            out[k] = None
    return out


def status():
    try:
        with urllib.request.urlopen(STATUS, timeout=5) as r:
            d = json.load(r)
    except Exception as exc:  # noqa: BLE001
        return {"error": type(exc).__name__}
    c = d.get("controller") or {}
    return {"active": d.get("active"), "port": c.get("port") or d.get("input_port"),
            "controller_active": c.get("active"),
            "packets_received": c.get("packets_received"), "lost_packets": c.get("lost_packets"),
            "rejected_packets": c.get("rejected_packets"), "bad_packets": c.get("bad_packets"),
            "updates_by_player": c.get("updates_by_player")}


def opal():
    try:
        t = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "opal",
                            "cat /proc/net/dev"], capture_output=True, text=True, timeout=12).stdout
    except Exception:  # noqa: BLE001
        return None
    out = {}
    for line in t.splitlines()[2:]:
        name, _, rest = line.partition(":")
        name = name.strip()
        if name not in OPAL_IFS:
            continue
        f = [int(x) for x in rest.split()]
        out[name] = {"rx_packets": f[1], "rx_errs": f[2], "rx_drop": f[3],
                     "tx_packets": f[9], "tx_errs": f[10], "tx_drop": f[11]}
    return out


def main():
    seq, port = 0, None
    with open(OUT, "a") as fh:
        while not os.path.exists(STOP):
            t0 = time.monotonic()
            row = {"seq": seq, "at_utc": now()}
            if seq % 3 == 0:
                st = status()
                if st.get("port"):
                    port = int(st["port"])
                row["status"] = {k: v for k, v in st.items() if k != "port"}  # the port stays in memory
                row["opal"] = opal()
            row["port_known"] = port is not None
            row["socket"] = udp_rows(port)
            row["snmp_udp"] = snmp_udp()
            row["softnet"] = softnet()
            row["nic"] = nic()
            row["cost_ms"] = round(1000 * (time.monotonic() - t0))
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            seq += 1
            time.sleep(max(0.0, INTERVAL - (time.monotonic() - t0)))


if __name__ == "__main__":
    main()
