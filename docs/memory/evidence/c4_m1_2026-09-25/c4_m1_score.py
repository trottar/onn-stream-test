#!/usr/bin/env python3
"""C4-M1 step 4: score the night, pre-registered, against its own noise. Read-only.

Holds B1 A1 B2 A2 B3 A3 (runs/index.txt T0..T1; runs/report_*.json; the
heartbeat copies runs/heartbeat_*.jsonl; runs/status_end_*.json for the
relay's parity counters).

Rules (handoffs/C4-M1_FEC_MEASURED_ARM_TASK.md):
  RECOVERS THE RESIDUAL  video loss/min post-FEC lower in the A hold of >= 2 of
                         3 pairs (B1,A1) (B2,A2) (B3,A3) AND the pooled A
                         median <= 60 % of the pooled B median; NOT SHOWN
                         otherwise.
  cost rows (spikes/min, rendered fps, stale drops/min, max output gap, audio
  underruns/min): WITHIN NOISE unless all three A holds are worse than the
  worst B hold AND the A median is beyond that worst B by more than the B
  holds' own spread (max - min); "worse" is higher, except fps (lower).
  Recovery latency, as a number: the client's `fec_max_hold_ms` (the longest a
  gap was held waiting for repair) per hold; the relay emits Q right after P
  (same group completion) so no added completion delay.
"""
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
HOLDS = ["B1", "A1", "B2", "A2", "B3", "A3"]
idx = {}
for line in open(os.path.join(R, "index.txt")):
    f = line.split()
    if f and f[0] in HOLDS and len(f) >= 6:
        idx[f[0]] = f


def gaps(arm):
    p = os.path.join(R, f"heartbeat_{arm}.jsonl")
    if not os.path.exists(p):
        return None
    rows = [json.loads(l) for l in open(p)]
    rows = [r for r in rows if "lost_packets" in r]
    rows.sort(key=lambda r: r["elapsed_ms"])
    sizes = []
    for a, b in zip(rows, rows[1:]):
        dg = b["forward_gap_events"] - a["forward_gap_events"]
        dl = (b["lost_packets"] - b.get("lost_packets_in_resyncs", 0)) - (a["lost_packets"] - a.get("lost_packets_in_resyncs", 0))
        if dg == 1 and b.get("stream_resyncs", 0) == a.get("stream_resyncs", 0):
            sizes.append(dl)
    return sizes


rows = {}
print("C4-M1 night -- scoring (pre-registered)")
print(f"{'hold':<5} {'min':>6} {'vloss/min':>9} {'rec/min':>8} {'unrec/min':>9} {'spikes/min':>10} {'fps':>6} "
      f"{'stale/min':>9} {'maxgap':>6} {'aund/min':>8} {'hold_ms':>7} {'ssrc':>4} {'resync':>6} {'Q sent':>7}  gap sizes b=1/2/3/>=4")
for arm in HOLDS:
    if arm not in idx:
        print(f"{arm:<5} NOT RUN")
        continue
    rp = os.path.join(R, f"report_{arm}.json")
    if not os.path.exists(rp):
        print(f"{arm:<5} no report")
        continue
    rep = json.load(open(rp))["report"]
    d, v, a = rep["decoder"], rep["video"], rep["audio"]
    secs = rep["duration_ms"] / 1000.0
    m = secs / 60.0
    se = os.path.join(R, f"status_end_{arm}.json")
    q = None
    if os.path.exists(se):
        q = (json.load(open(se)).get("fec") or {}).get("q_parity_packets")
    g = gaps(arm) or []
    row = dict(min=m, vloss=(v["lost_packets"] - v["lost_packets_in_resyncs"]) / m,
               rec=v["fec_recovered_packets"] / m, unrec=v["fec_unrecoverable_groups"] / m,
               spikes=d["spike_20_ms"] / m, fps=d["rendered_frames"] / secs,
               stale=d["stale_output_drops"] / m, maxgap=d["max_output_gap_ms"],
               aund=a["underruns"] / m, hold=v.get("fec_max_hold_ms"), ssrc=v["ssrc_changes"],
               resync=v["sequence_resyncs"], q=q,
               g=(sum(1 for b in g if b == 1), sum(1 for b in g if b == 2), sum(1 for b in g if b == 3),
                  sum(1 for b in g if b >= 4)))
    rows[arm] = row
    print(f"{arm:<5} {m:6.2f} {row['vloss']:9.2f} {row['rec']:8.2f} {row['unrec']:9.2f} {row['spikes']:10.1f} "
          f"{row['fps']:6.2f} {row['stale']:9.2f} {row['maxgap']:6} {row['aund']:8.2f} {str(row['hold']):>7} "
          f"{row['ssrc']:4} {row['resync']:6} {str(q):>7}  {row['g']}")

print()
pairs = [("B1", "A1"), ("B2", "A2"), ("B3", "A3")]
done = [(b, a) for b, a in pairs if b in rows and a in rows]
lower = [(b, a) for b, a in done if rows[a]["vloss"] < rows[b]["vloss"]]
B = [rows[k]["vloss"] for k in ("B1", "B2", "B3") if k in rows]
A = [rows[k]["vloss"] for k in ("A1", "A2", "A3") if k in rows]
if len(done) < 3 or len(A) < 3 or len(B) < 3:
    print(f"primary: only {len(done)} complete pairs -> INDETERMINATE (the rule needs 3 pairs)")
    primary = "INDETERMINATE"
else:
    mb, ma = statistics.median(B), statistics.median(A)
    ok = len(lower) >= 2 and ma <= 0.6 * mb
    primary = "RECOVERS THE RESIDUAL" if ok else "NOT SHOWN"
    print(f"primary (video loss/min post-FEC): A lower in {len(lower)} of 3 pairs {[p[1] for p in lower]}; "
          f"pooled median A {ma:.2f} vs B {mb:.2f} = {100 * ma / mb:.0f} % (rule <= 60 %) -> {primary}")
print()
print("cost rows (WITHIN NOISE unless all three A worse than the worst B AND the A median beyond it by > the B spread):")
for key, name, higher_worse in (("spikes", "spikes/min", True), ("fps", "rendered fps", False),
                                ("stale", "stale drops/min", True), ("maxgap", "max output gap ms", True),
                                ("aund", "audio underruns/min", True)):
    b = [rows[k][key] for k in ("B1", "B2", "B3") if k in rows]
    a = [rows[k][key] for k in ("A1", "A2", "A3") if k in rows]
    if len(a) < 3 or len(b) < 3:
        print(f"  {name:<22} incomplete")
        continue
    spread = max(b) - min(b)
    if higher_worse:
        worst = max(b)
        worse = all(x > worst for x in a) and statistics.median(a) - worst > spread
    else:
        worst = min(b)
        worse = all(x < worst for x in a) and worst - statistics.median(a) > spread
    print(f"  {name:<22} B {[round(x, 2) for x in b]}  A {[round(x, 2) for x in a]}  worst B {worst:.2f}, "
          f"B spread {spread:.2f}, A median {statistics.median(a):.2f} -> {'WORSE' if worse else 'WITHIN NOISE'}")
print()
hb = [rows[k]["hold"] for k in ("B1", "B2", "B3") if k in rows]
ha = [rows[k]["hold"] for k in ("A1", "A2", "A3") if k in rows]
print(f"recovery latency (client fec_max_hold_ms per hold): B {hb}, A {ha}; Q is emitted right after P "
      f"(same group completion)")
print(f"\nOUTCOME: {primary}")
