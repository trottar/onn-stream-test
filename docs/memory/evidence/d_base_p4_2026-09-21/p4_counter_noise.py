#!/usr/bin/env python3
"""D-BASE-P4: why a per-minute loss series could not be built from counters.

The plan was loss(window) = d(relay rtp sent) - d(client rx received). Both
counters exist, but the client's is only visible through the 2 s heartbeat,
so its value at an arbitrary instant must be interpolated. This measures the
resulting noise floor against the per-window loss it would have to resolve.
"""
import json, os, statistics as st
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SESS = "/home/privyhub/Projects/onn-stream-test/logs/games/decoder_sessions"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


print(f"{'run':<6}{'windows':>8}{'sum':>7}{'report':>8}{'per-window loss, interpolated':>34}")
print(f"{'':6}{'':8}{'':7}{'lost':>8}")
floors, sigs = [], []
for line in open(f"{HERE}/index.txt"):
    label, hold, report, t0, t1 = line.split()
    d = json.load(open(os.path.join(SESS, report)))["report"]
    hb = sorted((ts(x["received_at_utc"]), x["rx_packets"])
                for x in (json.loads(l) for l in
                          open(f"{HERE}/heartbeat_{label}.jsonl")))
    if len(hb) < 3:
        continue

    def rx_at(t):
        if t <= hb[0][0] or t >= hb[-1][0]:
            return None
        for (a, va), (b, vb) in zip(hb, hb[1:]):
            if a <= t <= b:
                f = (t - a).total_seconds() / max(1e-9, (b - a).total_seconds())
                return va + (vb - va) * f
        return None

    pts = []
    for r in (json.loads(l) for l in open(f"{HERE}/air_{label}.jsonl")):
        h = r.get("host") or {}
        if h.get("relay_rtp_packets"):
            x = rx_at(ts(r["at_utc"]))
            if x is not None:
                pts.append(h["relay_rtp_packets"] - x)
    deltas = [round(b - a) for a, b in zip(pts, pts[1:])]
    if not deltas:
        continue
    lost = d["video"]["lost_packets"]
    # the true per-window loss, if it were spread evenly
    sig = lost / max(1, len(deltas))
    floor = st.pstdev(deltas) if len(deltas) > 1 else 0
    floors.append(floor)
    sigs.append(sig)
    print(f"{label:<6}{len(deltas):>8}{sum(deltas):>7}{lost:>8}   "
          f"{deltas[:8]}{'...' if len(deltas) > 8 else ''}")
    print(f"{'':6}{'':8}{'':7}{'':8}   noise sd={floor:.0f} packets/window, "
          f"signal={sig:.1f} packets/window, ratio={floor/max(0.1,sig):.0f}x")

print()
print("Reading: the totals reconcile (the sums land within a few hundred of the")
print("report's own count), but every window's value is dominated by the")
print("interpolation error of a 2 s heartbeat against an ~830 packet/s stream —")
print("about +/-100 packets, against a real per-window loss of a few. Negative")
print("windows are the giveaway: the stream cannot un-lose packets.")
print()
print(f"Pooled: median noise sd {st.median(floors):.0f} packets/window against a")
print(f"median signal of {st.median(sigs):.1f}. A per-minute loss series is NOT")
print("available from these counters, and none is presented. Loss stays per")
print("session, from the report. Getting finer would need a per-tick loss")
print("counter in the client, which this task forbade changing.")
