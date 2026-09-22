#!/usr/bin/env python3
"""D-BASE-P5 instrument 2: the onn's UDP receive-queue drops.

Host-side over adb. **No client change and nothing installed on the onn** —
this reads `/proc/net/udp`, which lists every UDP socket with, as its last
field, the number of datagrams the kernel discarded because the socket's
receive buffer was full. That counter is exactly the "the onn's own receive
path is the queue" hypothesis, measured at the kernel rather than inferred.

Ports are matched in hex as the kernel prints them: 48100 video is BBE4,
48101 audio is BBE5. **Both `/proc/net/udp` and `/proc/net/udp6` are read.**
The client's `DatagramSocket(port)` is a Java socket, so it binds the IPv6
wildcard and appears only in `udp6` -- the first version of this script read
`udp` alone and saw the stream's sockets in none of 76 rounds.

Only the two stream ports are recorded; no address, no other socket, no
device identifier.

usage: p5_socket_sample.py <out.jsonl> [interval_s]
stop with Ctrl-C, or: touch <out.jsonl>.stop
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

PORTS = {"BBE4": "video_48100", "BBE5": "audio_48101"}


def utc():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def adb(args, timeout=10):
    try:
        out = subprocess.run(
            ["adb", "shell"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return out.stdout
    except (subprocess.TimeoutExpired, OSError):
        return ""


def parse_udp(text, family, rows):
    """Add the stream's rows from one /proc/net/udp* listing.

    **The header names fifteen columns and a row has thirteen fields**,
    because `tx_queue:rx_queue` and `tr:tm->when` are each printed as one
    colon-joined token. Counting header words and demanding fourteen fields
    rejected every row -- that is how the first version of this script came
    back empty for a whole session while the ports were plainly there.
    Fields, 0-indexed: 0 sl, 1 local_address, 2 rem_address, 3 st,
    4 tx_queue:rx_queue, 5 tr:tm->when, 6 retrnsmt, 7 uid, 8 timeout,
    9 inode, 10 ref, 11 pointer, 12 drops. `drops` is read as the **last**
    field, which is what it is in both files and in every kernel that
    carries it.

    A row whose shape does not match is skipped rather than guessed at. The
    local address itself is never recorded -- only its port is read, to
    decide whether the row is ours.
    """
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 13:
            continue
        local = parts[1]
        if ":" not in local:
            continue
        port_hex = local.rsplit(":", 1)[1].upper()
        role = PORTS.get(port_hex)
        if role is None:
            continue
        queues = parts[4].split(":")
        if len(queues) != 2:
            continue
        try:
            rows[role] = {
                "family": family,
                "tx_queue": int(queues[0], 16),
                "rx_queue": int(queues[1], 16),
                "drops": int(parts[-1]),
                "inode": int(parts[9]),
            }
        except ValueError:
            continue
    return rows


def read_sockets():
    rows = {}
    parse_udp(adb(["cat", "/proc/net/udp"]), "ipv4", rows)
    parse_udp(adb(["cat", "/proc/net/udp6"]), "ipv6", rows)
    return rows


def main():
    out_path = sys.argv[1]
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    stop = out_path + ".stop"

    # Once, for the record: the kernel's ceiling, and whether any tool on
    # this device will show the socket's *granted* receive buffer.
    # `/proc/net/udp` does not carry SO_RCVBUF. `ss -uanm` would, in its
    # `skmem(...)` field, but `ss` cannot open a netlink socket as the
    # shell user here and falls back to a listing without it. So this
    # records **whether** the figure was obtainable, never a number that
    # was not measured.
    #
    # `ss` output carries addresses, so it is never stored: only the
    # presence of `skmem` and the row count are kept.
    ss_text = adb(["ss", "-uanm"])
    head = {
        "schema": "privyhub_p5_socket_head_v1",
        "at_utc": utc(),
        "rmem_max": adb(["cat", "/proc/sys/net/core/rmem_max"]).strip(),
        "rmem_default": adb(
            ["cat", "/proc/sys/net/core/rmem_default"]
        ).strip(),
        "wmem_max": adb(["cat", "/proc/sys/net/core/wmem_max"]).strip(),
        "ss_available": bool(ss_text.strip()),
        "ss_shows_skmem": "skmem" in ss_text,
        "ss_rows": len(ss_text.splitlines()),
        "ss_netlink_denied": "netlink" in ss_text.lower(),
        "granted_rcvbuf_obtainable": "skmem" in ss_text,
        "proc_net_udp_readable": bool(
            adb(["cat", "/proc/net/udp"]).strip()
        ),
        "proc_net_udp6_readable": bool(
            adb(["cat", "/proc/net/udp6"]).strip()
        ),
    }
    with open(out_path + ".head.json", "w") as fh:
        json.dump(head, fh, indent=1)
    print("head written; rmem_max=%s" % head["rmem_max"], file=sys.stderr)

    if os.path.exists(stop):
        os.unlink(stop)

    seq = 0
    with open(out_path, "a") as fh:
        while not os.path.exists(stop):
            t0 = time.time()
            sockets = read_sockets()
            row = {
                "schema": "privyhub_p5_socket_sample_v1",
                "seq": seq,
                "at_utc": utc(),
                "cost_ms": int((time.time() - t0) * 1000),
                "sockets": sockets,
            }
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            seq += 1
            spent = time.time() - t0
            if spent < interval:
                time.sleep(interval - spent)
    print("stopped after %d rounds" % seq, file=sys.stderr)


if __name__ == "__main__":
    main()
