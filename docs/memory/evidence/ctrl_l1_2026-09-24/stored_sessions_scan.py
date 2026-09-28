#!/usr/bin/env python3
"""CTRL-L1: the controller counters in every stored status snapshot (after
BACK) beside the client's packets_sent from the same run's decoder report,
plus the per-player true-loss lower bound. Read-only; paths relative to the
evidence directory's parent."""
import glob, json, os
EV = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
paths = sorted(glob.glob(os.path.join(EV, "*/runs/status_*.json")) + glob.glob(os.path.join(EV, "*/status_*.json")))
print(f"{'status file':<50} {'received':>8} {'lost':>6} {'sent*':>8} {'LB':>6} per-player deficit")
for st in paths:
    if "status_end_" in st:
        continue
    try:
        c = json.load(open(st)).get("controller") or {}
    except Exception:
        continue
    u = c.get("updates_by_player")
    if not u:
        continue
    rep = st.replace("status_", "report_")
    sent = None
    if os.path.exists(rep):
        r = json.load(open(rep)); r = r.get("report", r)
        sent = (r.get("controller") or {}).get("packets_sent")
    lb = sum(max(u) - x for x in u)
    print(f"{os.path.relpath(st, EV):<50} {c['packets_received']:>8} {c['lost_packets']:>6} {str(sent):>8} {lb:>6} {[max(u) - x for x in u]}")
print("* packets_sent at the client's report snapshot (BACK); the host keeps receiving ~1-8 s after it")
