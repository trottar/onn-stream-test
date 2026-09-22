#!/usr/bin/env python3
"""D-BASE-R5 validation: does the heartbeat now carry a usable loss series?"""
import json, os, statistics as st, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SESS = "/home/privyhub/Projects/onn-stream-test/logs/games/decoder_sessions"
NEW = ("lost_packets", "lost_packets_in_resyncs", "forward_gap_events",
       "max_forward_gap_packets", "stream_resyncs", "fec_recovered_packets",
       "fec_unrecoverable_groups")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


label, hold, report, t0, t1 = open(f"{HERE}/index.txt").read().split()
rep = json.load(open(os.path.join(SESS, report)))["report"]
v, dec = rep["video"], rep["decoder"]
hb = [json.loads(l) for l in open(f"{HERE}/heartbeat_{label}.jsonl")]
hb = [h for h in hb if "elapsed_ms" in h]
hb.sort(key=lambda h: h["elapsed_ms"])

print(f"===== {label}: {len(hb)} heartbeats over {rep['duration_ms']/1000:.0f} s =====")

# --- check 1: every heartbeat carries the new fields --------------------
missing = [h["sequence"] for h in hb if any(f not in h for f in NEW)]
schemas = {h.get("schema") for h in hb}
print("\n-- CHECK 1: every heartbeat carries the new fields --")
print(f"   schema(s) seen: {schemas}")
print(f"   heartbeats missing any new field: {len(missing)} of {len(hb)}"
      + (f"  {missing[:5]}" if missing else "")
      + ("   PASS" if not missing else "   FAIL"))

# --- check 2: last heartbeat vs the report ------------------------------
last = hb[-1]
print("\n-- CHECK 2: last heartbeat's cumulative values vs the report --")
pairs = [
    ("lost_packets", v["lost_packets"]),
    ("lost_packets_in_resyncs", v["lost_packets_in_resyncs"]),
    ("forward_gap_events", v["forward_gap_events"]),
    ("max_forward_gap_packets", v["max_forward_gap_packets"]),
    ("stream_resyncs", v["sequence_resyncs"] + v["ssrc_changes"]),
    ("fec_recovered_packets", v["fec_recovered_packets"]),
    ("fec_unrecoverable_groups", v["fec_unrecoverable_groups"]),
    ("rx_packets", v["packets"]),
]
tail_ms = rep["duration_ms"] - last["elapsed_ms"]
exact = 0
print(f"   {'field':<26}{'heartbeat':>10}{'report':>9}{'delta':>7}")
for name, rv in pairs:
    hv = last.get(name)
    d = None if hv is None else rv - hv
    exact += (d == 0)
    print(f"   {name:<26}{str(hv):>10}{rv:>9}{('-' if d is None else d):>7}")
print(f"   last heartbeat at elapsed {last['elapsed_ms']} ms; report duration "
      f"{rep['duration_ms']} ms -> {tail_ms} ms of stream after it")
print(f"   exact matches: {exact} of {len(pairs)}")

# --- check 3: per-minute series sums to the report ----------------------
print("\n-- CHECK 3: per-minute loss series from heartbeat deltas --")
buckets = {}
for a, b in zip(hb, hb[1:]):
    if "lost_packets" not in a or "lost_packets" not in b:
        continue
    m = int(a["elapsed_ms"] // 60000)
    d = b["lost_packets"] - a["lost_packets"]
    buckets.setdefault(m, {"lost": 0, "gaps": 0, "rx": 0, "n": 0})
    buckets[m]["lost"] += d
    buckets[m]["gaps"] += b["forward_gap_events"] - a["forward_gap_events"]
    buckets[m]["rx"] += b["rx_packets"] - a["rx_packets"]
    buckets[m]["n"] += 1
series_sum = sum(x["lost"] for x in buckets.values())
head = hb[0].get("lost_packets", 0)
tail = v["lost_packets"] - last.get("lost_packets", 0)
print(f"   series sum {series_sum}  + first-heartbeat head {head}"
      f"  + post-last-heartbeat tail {tail}  = {series_sum + head + tail}")
print(f"   report lost_packets = {v['lost_packets']}"
      + ("   PASS (accounts exactly)"
         if series_sum + head + tail == v["lost_packets"] else "   FAIL"))

# --- check 4: the series itself, with the radio beside it ---------------
harvest = json.load(open(f"{HERE}/air_harvest_{label}.json"))
ring = [(ts(r["at_utc"]), r) for r in harvest["score_report_rows"] if r["at_utc"]]
ring = [r for r in ring if ts(t0) <= r[0] <= ts(t1)]
T0 = ts(t0)


def radio_for_minute(m):
    lo, hi = m * 60, (m + 1) * 60
    rows = [r for t, r in ring if lo <= (t - T0).total_seconds() < hi]
    if not rows:
        return None, None
    return (st.median(float(r["rssi"]) for r in rows),
            st.median(float(r["txLinkSpeed"]) for r in rows))


print("\n-- CHECK 4: the 20-minute loss series, radio alongside --")
print(f"   {'min':>4}{'lost':>7}{'loss/min':>10}{'gaps':>6}{'rx':>8}"
      f"{'rssi':>7}{'txLink':>8}")
vals = []
for m in sorted(buckets):
    b = buckets[m]
    rssi, tx = radio_for_minute(m)
    vals.append(b["lost"])
    print(f"   {m:>4}{b['lost']:>7}{b['lost']:>10}{b['gaps']:>6}{b['rx']:>8}"
          + (f"{rssi:>7.0f}" if rssi is not None else f"{'-':>7}")
          + (f"{tx:>8.0f}" if tx is not None else f"{'-':>8}"))
if vals:
    med = st.median(vals)
    burst = [m for m in sorted(buckets) if buckets[m]["lost"] >= max(2 * med, med + 10)]
    print(f"\n   per-minute loss: {vals}")
    print(f"   median {med:.0f}/min, min {min(vals)}, max {max(vals)}, "
          f"{max(vals)/max(1,min(vals)):.0f}x spread within ONE session")
    print(f"   burst minutes (>= 2x median): {burst if burst else 'none'}")
    for m in burst:
        rssi, tx = radio_for_minute(m)
        print(f"     minute {m}: {buckets[m]['lost']} lost, "
              f"{buckets[m]['gaps']} gap events, rssi "
              + (f"{rssi:.0f}" if rssi is not None else "-")
              + ", txLink " + (f"{tx:.0f}" if tx is not None else "-"))

# --- check 5: cost ------------------------------------------------------
print("\n-- CHECK 5: did the heartbeat get more expensive? --")
sizes = [len(json.dumps(h, separators=(", ", ": ")).encode()) for h in hb]
print(f"   heartbeat line bytes now: min {min(sizes)} median "
      f"{st.median(sizes):.0f} max {max(sizes)}")
mins = rep["duration_ms"] / 60000.0
print(f"   spike_20_ms/min {dec['spike_20_ms']/mins:.1f}  "
      f"(P4's seven sessions: 40.6-62.4)")
print(f"   rendered fps {dec['rendered_frames']/(rep['duration_ms']/1000):.2f}")
print(f"   max_output_gap_ms {dec['max_output_gap_ms']}, "
      f"discontinuities {len(rep.get('stream_discontinuities') or [])}")
