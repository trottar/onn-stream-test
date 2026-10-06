#!/usr/bin/env python3
"""E3-S3 -- the companion's reaped-children CPU (cutime + cstime from /proc/<MainPID>/stat), every <interval> s.

    e3_children_log.py <out.jsonl> [--interval 5]       stop: touch <out.jsonl>.stop

Exact for short-lived children (the EPG grabber chain: npm, sh, node, all waited for), which the 1-s sampler
undercounts (a process's first sample has no delta). Read-only; numbers only.
"""
import json
import os
import subprocess
import sys
import time

CLK = os.sysconf("SC_CLK_TCK")


def main(argv):
    out = argv[0]
    iv = float(argv[argv.index("--interval") + 1]) if "--interval" in argv else 5.0
    with open(out, "a") as fh:
        while not os.path.exists(out + ".stop"):
            v = subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value", "privyhub-companion"],
                               capture_output=True, text=True).stdout.strip()
            row = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z", "pid": int(v) if v.isdigit() else None}
            try:
                f = open(f"/proc/{row['pid']}/stat").read().rsplit(")", 1)[1].split()
                row["children_cpu_s"] = round((int(f[13]) + int(f[14])) / CLK, 2)
                row["self_cpu_s"] = round((int(f[11]) + int(f[12])) / CLK, 2)
            except (OSError, ValueError, IndexError, TypeError):
                pass
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            time.sleep(iv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
