#!/usr/bin/env python3
"""CTRL-L1: where the controller datagrams go missing. Read-only analysis.

Inputs (this directory): runs/index.txt (each hold's T0/T1), runs/status_*.json
(after BACK) and runs/status_end_*.json when present, runs/report_*.json (the
client's decoder report: controller packets_sent / send_errors),
host_samples.jsonl (ctrl_l1_host_sample.py), t2_samples.jsonl (t2_sample.py),
runs/onn_snmp_udp.txt (the onn's Udp line, read between holds only).

Pre-registered reading (handoffs/CTRL-L1_CONTROLLER_LOSS_LOCATION_TASK.md):
  HOST SOCKET      socket `drops` deltas >= 80 % of `lost_packets` deltas in
                   >= 2 of 3 holds;
  HOST STACK/NIC   the NIC / stack counters (RcvbufErrors, InErrors, softnet
                   dropped, NIC rx_dropped / missed / fifo / errors) do;
  PATH             every host-side counter +0 while lost_packets accumulates
                   (the T3 outcome, mirrored);
  REORDERING, NOT LOSS  if step 1 shows the counter counting late arrivals;
  INDETERMINATE    otherwise.
What the counter counts (companion/native_session_io.py, the source):
  one global 32-bit sequence over all four player datagrams of a tick; a
  forward jump adds (seq - expected); a late packet adds nothing but resets
  the expectation, so the NEXT packet adds again: a swap of two adjacent
  packets adds 2 though both arrived; a duplicate adds 0. The client
  (NativeControllerSender.kt) advances the sequence even on a send
  exception, so a client send error also reads as a gap.
Lower bound on true non-arrival: every tick sends players 0-3 once each, so
per-player receive counts can differ only by loss (+-1 at the ends) or
duplication; sum(max - n_i) <= packets that never arrived.
"""
import json
import math
import os
import statistics
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
WARM_C = 67.5


def ts(s):
    s = s.rstrip("Z")
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in s else "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(s[:26], fmt).replace(tzinfo=timezone.utc).timestamp()


def spearman(x, y):
    n = len(x)
    if n < 4:
        return float("nan")

    def rank(v):
        o = sorted(range(n), key=lambda i: v[i]); r = [0.0] * n; i = 0
        while i < n:
            j = i
            while j + 1 < n and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    a, b = rank(x), rank(y)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num / den if den else float("nan")


host = [json.loads(l) for l in open(os.path.join(HERE, "host_samples.jsonl"))]
t2 = [json.loads(l) for l in open(os.path.join(HERE, "t2_samples.jsonl"))] \
    if os.path.exists(os.path.join(HERE, "t2_samples.jsonl")) else []
holds = []
for line in open(os.path.join(RUNS, "index.txt")):
    f = line.split()
    if len(f) >= 5 and f[0] in ("C", "W1", "W2"):
        holds.append((f[0], f[3], ts(f[3]), ts(f[4])))

HOST_KEYS = [("socket drops", lambda r: sum(s["drops"] for s in r["socket"]) if r["socket"] else None),
             ("Udp RcvbufErrors", lambda r: r["snmp_udp"]["RcvbufErrors"]),
             ("Udp InErrors", lambda r: r["snmp_udp"]["InErrors"]),
             ("Udp InCsumErrors", lambda r: r["snmp_udp"]["InCsumErrors"]),
             ("Udp MemErrors", lambda r: r["snmp_udp"]["MemErrors"]),
             ("softnet dropped", lambda r: r["softnet"]["dropped"]),
             ("softnet time_squeeze", lambda r: r["softnet"]["time_squeeze"]),
             ("NIC rx_dropped", lambda r: r["nic"]["rx_dropped"]),
             ("NIC rx_missed_errors", lambda r: r["nic"]["rx_missed_errors"]),
             ("NIC rx_fifo_errors", lambda r: r["nic"]["rx_fifo_errors"]),
             ("NIC rx_errors", lambda r: r["nic"]["rx_errors"])]
OPAL_KEYS = [(f"Opal {i} {k}", i, k) for i in ("wlan1", "br-lan", "eth0")
             for k in ("rx_drop", "rx_errs", "tx_drop", "tx_errs")]

print("CTRL-L1 analysis -- read-only")
print(f"host samples {len(host)}, t2 samples {len(t2)}, holds {[h[0] for h in holds]}")
print()
verdict_rows = []
for arm, t0s, t0, t1 in holds:
    rows = [r for r in host if t0 - 1 <= ts(r["at_utc"]) <= t1 + 1]
    st = [r for r in rows if (r.get("status") or {}).get("packets_received") is not None
          and r["status"].get("controller_active")]
    print(f"=== hold {arm}: {t0s}, {len(rows)} host rows, {len(st)} status rows ===")
    if len(st) < 2:
        print("  not enough status rows")
        continue
    a, b = st[0], st[-1]
    dmin = (ts(b["at_utc"]) - ts(a["at_utc"])) / 60.0
    lost = b["status"]["lost_packets"] - a["status"]["lost_packets"]
    rcv = b["status"]["packets_received"] - a["status"]["packets_received"]
    print(f"  span {dmin:.1f} min (first to last status in the hold): lost_packets +{lost} "
          f"({lost / dmin:.1f}/min), packets_received +{rcv} ({rcv / dmin:.0f}/min), "
          f"rejected +{b['status']['rejected_packets'] - a['status']['rejected_packets']}, "
          f"bad +{b['status']['bad_packets'] - a['status']['bad_packets']}")
    ha, hb = rows[0], rows[-1]
    deltas = {}
    for name, fn in HOST_KEYS:
        va, vb = fn(a), fn(b)
        deltas[name] = None if va is None or vb is None else vb - va
    oa, ob = a.get("opal") or {}, b.get("opal") or {}
    for name, i, k in OPAL_KEYS:
        deltas[name] = (ob[i][k] - oa[i][k]) if i in oa and i in ob else None
    for name, v in deltas.items():
        print(f"  {name:<24} {'n/a' if v is None else f'+{v}'}")
    rxq = [s["rx_queue"] for r in rows for s in r["socket"]]
    print(f"  socket rx_queue bytes: max {max(rxq) if rxq else 'n/a'}, samples {len(rxq)}")
    sock = deltas["socket drops"] or 0
    stack = sum((deltas[k] or 0) for k in ("Udp RcvbufErrors", "Udp InErrors", "softnet dropped",
                                           "NIC rx_dropped", "NIC rx_missed_errors",
                                           "NIC rx_fifo_errors", "NIC rx_errors"))
    stack_ex_sock = max(0, stack - 2 * sock)   # a socket drop also raises RcvbufErrors+InErrors
    host_all = sock + stack
    frac_sock = sock / lost if lost else float("nan")
    frac_stack = stack_ex_sock / lost if lost else float("nan")
    print(f"  socket drops / lost = {frac_sock:.2f}; stack/NIC (beyond the socket's own) / lost = {frac_stack:.2f}")
    # per minute
    print(f"  {'min':>3} {'lost':>5} {'rcv/min':>7} {'sockdrop':>8} {'rcvbuf':>6} {'softnet':>7} {'nicdrop':>7} {'onn C':>6}")
    per_min = []
    mins = {}
    for r in st:
        m = int((ts(r["at_utc"]) - t0) // 60)
        mins.setdefault(m, []).append(r)
    keys = sorted(mins)
    for m0, m1 in zip(keys, keys[1:]):
        r0, r1 = mins[m0][0], mins[m1][0]
        dt = (ts(r1["at_utc"]) - ts(r0["at_utc"])) / 60.0
        L = (r1["status"]["lost_packets"] - r0["status"]["lost_packets"]) / dt
        R = (r1["status"]["packets_received"] - r0["status"]["packets_received"]) / dt
        sd = (HOST_KEYS[0][1](r1) or 0) - (HOST_KEYS[0][1](r0) or 0)
        rb = r1["snmp_udp"]["RcvbufErrors"] - r0["snmp_udp"]["RcvbufErrors"]
        sn = r1["softnet"]["dropped"] - r0["softnet"]["dropped"]
        nd = r1["nic"]["rx_dropped"] - r0["nic"]["rx_dropped"]
        tt = [x["onn"]["cpu_thermal_c"] for x in t2 if ts(r0["at_utc"]) <= ts(x["at_utc"]) <= ts(r1["at_utc"])
              and (x.get("onn") or {}).get("cpu_thermal_c") is not None]
        onn_c = sum(tt) / len(tt) if tt else None
        per_min.append(dict(L=L, R=R, onn=onn_c))
        print(f"  {m0:3} {L:5.1f} {R:7.0f} {sd:8} {rb:6} {sn:7} {nd:7} {'' if onn_c is None else f'{onn_c:6.1f}'}")
    Ls = [p["L"] for p in per_min]
    Rs = [p["R"] for p in per_min]
    th = [(p["L"], p["onn"]) for p in per_min if p["onn"] is not None]
    print(f"  per-minute lost vs packets_received rate: rho {spearman(Ls, Rs):+.2f}; "
          f"vs onn cpu-thermal: rho {spearman([a for a, _ in th], [b for _, b in th]):+.2f} (n {len(th)}); "
          f"warm minutes (>= {WARM_C} C) {sum(1 for _, b in th if b >= WARM_C)} of {len(th)}, lost/min "
          f"warm {statistics.mean([a for a, b in th if b >= WARM_C]) if any(b >= WARM_C for _, b in th) else float('nan'):.1f} "
          f"cool {statistics.mean([a for a, b in th if b < WARM_C]) if any(b < WARM_C for _, b in th) else float('nan'):.1f}")
    # session totals: status after BACK, the client's report
    sp = os.path.join(RUNS, f"status_{arm}.json")
    rp = os.path.join(RUNS, f"report_{arm}.json")
    if os.path.exists(sp):
        c = json.load(open(sp)).get("controller") or {}
        u = c.get("updates_by_player") or []
        lb = sum(max(u) - x for x in u) if u else None
        print(f"  whole session (status after BACK): received {c.get('packets_received')}, lost_packets "
              f"{c.get('lost_packets')}, per player {u}, true-loss lower bound {lb}"
              + (f" = {100.0 * lb / c['lost_packets']:.0f} % of the counter" if lb is not None and c.get('lost_packets') else ""))
        if u:
            print(f"    per-player deficit vs the best player: {[max(u) - x for x in u]}")
    if os.path.exists(rp):
        rep = json.load(open(rp)).get("report") or {}
        cc = rep.get("controller") or {}
        print(f"  client report: packets_sent {cc.get('packets_sent')} (at the report snapshot), send_errors "
              f"{cc.get('send_errors')}, motion_events {cc.get('motion_events')}")
    host_names = [k for k, _ in HOST_KEYS if k != "softnet time_squeeze"]
    all_zero = all((deltas[k] or 0) == 0 for k in host_names)
    opal_nonzero = {k: v for k, v in deltas.items() if k.startswith("Opal") and v}
    print(f"  Opal counters that moved: {opal_nonzero or 'none'}")
    verdict_rows.append(dict(arm=arm, lost=lost, sock=sock, frac_sock=frac_sock, frac_stack=frac_stack,
                             all_zero=all_zero))
    print()

onn_path = os.path.join(RUNS, "onn_snmp_udp.txt")
if os.path.exists(onn_path):
    print("=== the onn's Udp counters, read between holds ===")
    rows = [l.split() for l in open(onn_path) if l.strip()]
    keys = ["InDatagrams", "NoPorts", "InErrors", "OutDatagrams", "RcvbufErrors", "SndbufErrors",
            "InCsumErrors", "IgnoredMulti", "MemErrors"]
    vals = {}
    for r in rows:
        nums = [int(x) for x in r[3:3 + len(keys)]] if len(r) >= 3 + len(keys) else None
        vals[r[0]] = nums
    for arm, *_ in holds:
        b, a = vals.get(f"before_{arm}"), vals.get(f"after_{arm}")
        if a and b:
            print(f"  {arm}: " + ", ".join(f"{k} +{y - x}" for k, x, y in zip(keys, b, a)))
    print()

print("=== READING (pre-registered) ===")
n = len(verdict_rows)
sock_holds = sum(1 for v in verdict_rows if v["lost"] and v["frac_sock"] >= 0.8)
stack_holds = sum(1 for v in verdict_rows if v["lost"] and v["frac_stack"] >= 0.8)
path_holds = sum(1 for v in verdict_rows if v["lost"] > 0 and v["all_zero"])
print(f"holds {n}; socket drops >= 80 % of lost: {sock_holds}; stack/NIC >= 80 %: {stack_holds}; "
      f"every host counter +0 while lost accumulated: {path_holds}")
for v in verdict_rows:
    print(f"  {v['arm']}: lost +{v['lost']}, socket drops +{v['sock']}, all host counters +0: {v['all_zero']}")
if sock_holds >= 2:
    print("-> HOST SOCKET")
elif stack_holds >= 2:
    print("-> HOST STACK/NIC")
elif n and path_holds == n:
    print("-> PATH (every host-side counter +0 while lost_packets accumulated, in every hold)")
elif n and path_holds >= 2:
    print("-> PATH in >= 2 of 3 holds")
else:
    print("-> INDETERMINATE by the location rule (see the record)")
