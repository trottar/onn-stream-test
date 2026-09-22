#!/usr/bin/env python3
"""D-BASE-P5 supplement: the onn's counters BELOW the socket.

`/proc/net/udp`'s `drops` column counts one thing only -- datagrams the
kernel discarded because that socket's receive buffer was full. A packet
lost in the Wi-Fi driver, at the netdev queue, or in IP reassembly never
reaches it and never appears there. So a zero in `drops` is not by itself
"nothing was lost on the onn".

This closes that gap, read-only over adb, every 5 s:
  * `/proc/net/snmp` Udp: InErrors, RcvbufErrors, NoPorts (whole-device);
  * `/sys/class/net/wlan0/statistics/`: rx_dropped, rx_errors, rx_missed_errors,
    rx_over_errors, rx_fifo_errors, rx_packets.

usage: p5_onn_lowlevel.py <out.jsonl> [interval_s]
stop: touch <out.jsonl>.stop
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

NETDEV_FIELDS = (
    "rx_packets", "rx_dropped", "rx_errors",
    "rx_missed_errors", "rx_over_errors", "rx_fifo_errors",
)


def utc():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def adb(cmd, timeout=10):
    try:
        return subprocess.run(
            ["adb", "shell", cmd],
            capture_output=True, text=True, timeout=timeout,
        ).stdout
    except (subprocess.TimeoutExpired, OSError):
        return ""


def snmp_udp(text):
    lines = [l for l in text.splitlines() if l.startswith("Udp:")]
    if len(lines) < 2:
        return {}
    names = lines[0].split()[1:]
    try:
        values = [int(v) for v in lines[1].split()[1:]]
    except ValueError:
        return {}
    return dict(zip(names, values))


def main():
    out_path = sys.argv[1]
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    stop = out_path + ".stop"
    if os.path.exists(stop):
        os.unlink(stop)

    iface = "wlan0"
    cmd = (
        "cat /proc/net/snmp; echo '===NETDEV==='; "
        + "; ".join(
            "echo -n '%s '; cat /sys/class/net/%s/statistics/%s"
            % (f, iface, f)
            for f in NETDEV_FIELDS
        )
    )

    seq = 0
    with open(out_path, "a") as fh:
        while not os.path.exists(stop):
            t0 = time.time()
            text = adb(cmd)
            snmp_part, _, dev_part = text.partition("===NETDEV===")
            netdev = {}
            for line in dev_part.splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[0] in NETDEV_FIELDS:
                    try:
                        netdev[parts[0]] = int(parts[1])
                    except ValueError:
                        pass
            fh.write(json.dumps({
                "schema": "privyhub_p5_onn_lowlevel_v1",
                "seq": seq,
                "at_utc": utc(),
                "udp": snmp_udp(snmp_part),
                "wlan0": netdev,
            }) + "\n")
            fh.flush()
            seq += 1
            spent = time.time() - t0
            if spent < interval:
                time.sleep(interval - spent)
    print("stopped after %d rounds" % seq, file=sys.stderr)


if __name__ == "__main__":
    main()
