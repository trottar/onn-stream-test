#!/usr/bin/env python3
"""G1-S2: the companion's cost over 60 s, read the same way in both arms (flag on / flag off), 10 s after a restart.
GET /status every 5 s (the provider is read only through /status; its 10-s cache); the unit cgroup's cpu.stat
usage_usec delta (includes the provider's tailscale child processes) as % of one core; the MainPID's PSS
(smaps_rollup) at the end. Read-only. usage: g1_s2_cost.py <label> -> cost_<label>.json beside this file."""
import json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UNIT = "privyhub-companion"


def prop(p):
    return subprocess.run(["systemctl", "--user", "show", "-p", p, "--value", UNIT], capture_output=True, text=True).stdout.strip()


def usage(cg):
    for l in open(f"/sys/fs/cgroup{cg}/cpu.stat"):
        if l.startswith("usage_usec"):
            return int(l.split()[1])


def pss_kb(pid):
    for l in open(f"/proc/{pid}/smaps_rollup"):
        if l.startswith("Pss:"):
            return int(l.split()[1])


def main():
    label = sys.argv[1]
    pid, cg = int(prop("MainPID")), prop("ControlGroup")
    t0, u0, pss0 = time.time(), usage(cg), pss_kb(pid)
    polls, last = 0, None
    while time.time() - t0 < 60:
        with urllib.request.urlopen("http://localhost:8765/status", timeout=10) as r:
            last = json.loads(r.read())
        polls += 1
        time.sleep(5)
    t1, u1, pss1 = time.time(), usage(cg), pss_kb(pid)
    out = {"label": label, "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "span_s": round(t1 - t0, 2),
           "polls": polls, "cgroup_cpu_pct_of_core": round(100 * (u1 - u0) / 1e6 / (t1 - t0), 3),
           "pss_kb_start": pss0, "pss_kb_end": pss1, "mainpid_same": int(prop("MainPID")) == pid,
           "overlay_last": (last or {}).get("overlay")}
    json.dump(out, open(os.path.join(HERE, f"cost_{label}.json"), "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
