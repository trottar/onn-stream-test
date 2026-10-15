#!/usr/bin/env python3
"""E4-S2 probe, part A (before the pre-registration): is a drop-in with CPUQuota= and MemoryMax= accepted by the user
manager, and does it take effect on the companion's cgroup? A 60-s idle check at CPUQuota=100% + MemoryMax=4G, then
removed. Uses tools/e1_suite.py's own helpers (unit_props, cgroup_read, restart_unit, the state check).
-> probe/idle_check.json. Writes only the drop-in e4_constraint.conf (removed at the end on every path)."""
import importlib.util
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("e1_suite", os.path.join(REPO, "tools/e1_suite.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
CONS = ["CPUQuota=100%", "MemoryMax=4G"]


def state():
    return json.loads(subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_state.py")], capture_output=True,
                                     text=True).stdout)


def main():
    os.makedirs(os.path.join(HERE, "probe"), exist_ok=True)
    out = {"constraint": CONS, "state_before": state(), "props_before": m.unit_props()}
    if not out["state_before"]["ok"] or m.E4_DROPIN.exists():
        out["refused"] = "the adopted state is not clean before the probe"
        json.dump(out, open(os.path.join(HERE, "probe", "idle_check.json"), "w"), indent=1)
        return 1
    try:
        m.E4_DROPIN.write_text("[Service]\n" + "".join(f"{kv}\n" for kv in CONS))
        out["dropin_text"] = m.E4_DROPIN.read_text()
        m.sh(["systemctl", "--user", "daemon-reload"], 60)
        out["restart"] = m.restart_unit()
        out["props_under"] = p = m.unit_props()
        out["takes_effect"] = m.constraint_holds(CONS, p)
        out["environ_under"] = m.environ_flags(m.mainpid())
        cg = m.cgroup_path()
        a = m.cgroup_read(cg)
        time.sleep(60)
        b = m.cgroup_read(cg)
        out["idle_60s"] = {"start": a, "end": b,
                           "usage_cores": round((b.get("cpu.usage_usec", 0) - a.get("cpu.usage_usec", 0)) / 1e6 / 60, 4),
                           "nr_periods": b.get("cpu.nr_periods", 0) - a.get("cpu.nr_periods", 0),
                           "nr_throttled": b.get("cpu.nr_throttled", 0) - a.get("cpu.nr_throttled", 0),
                           "throttled_s": (b.get("cpu.throttled_usec", 0) - a.get("cpu.throttled_usec", 0)) / 1e6,
                           "memory_current_mb": round(b.get("memory.current", 0) / 2**20, 1)}
        out["serving_under"] = m.http("GET", "/plugins/games/status", 10)[0]
    finally:
        m.E4_DROPIN.unlink(missing_ok=True)
        m.sh(["systemctl", "--user", "daemon-reload"], 60)
        out["restart_after"] = m.restart_unit()
        out["props_after"] = p = m.unit_props()
        out["lifted"] = (p.get("CPUQuotaPerSecUSec") == "infinity" and p.get("MemoryMax") == "infinity"
                         and p.get("memory.max") == "max" and p.get("cpu.max") in (None, "max 100000"))
        out["state_after"] = state()
        json.dump(out, open(os.path.join(HERE, "probe", "idle_check.json"), "w"), indent=1)
    print(json.dumps({k: out.get(k) for k in ("takes_effect", "idle_60s", "lifted")}, default=str))
    print("props_under", json.dumps(out.get("props_under")))
    print("props_after", json.dumps(out.get("props_after")))
    print("state_after ok", out["state_after"].get("ok"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
