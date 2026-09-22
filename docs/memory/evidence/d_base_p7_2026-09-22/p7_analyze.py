#!/usr/bin/env python3
"""D-BASE-P7: what `prolonged_starvation_events` counts.

Per 2 s heartbeat tick (n ~ 600) and per minute (n = 20), the starvation
delta against:
  * the audio rx-packet count, and its DEFICIT against the sender's
    cadence (one packet per 5 ms => 400 expected per 2 s tick);
  * the maximum audio inter-arrival gap that same tick measured;
  * the audio loss delta (a deficit with loss flat is jitter, not loss);
  * the video loss delta, queue depth and queue ms.

Counters are differenced; the arrival gap is a per-tick maximum and is
never differenced.

usage: p7_analyze.py <scratch_dir> <arm>
"""
import json
import math
import os
import statistics as st
import sys
from datetime import datetime, timezone

PACKET_MS = 5          # NativeAudioReceiver.PACKET_MS
FADE_CONCEAL_PACKETS = 2   # the latch threshold


def load(path):
    out = []
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def ts(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(
        tzinfo=timezone.utc)


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def pearson(a, b):
    n = len(a)
    if n < 3:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va <= 0 or vb <= 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def spearman(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 3:
        return None, 0
    xs, ys = zip(*pairs)
    return pearson(rank(list(xs)), rank(list(ys))), len(pairs)


def ticks(hb):
    """One row per heartbeat interval."""
    hb = [r for r in hb if "audio_prolonged_starvation_events" in r]
    hb.sort(key=lambda r: r["elapsed_ms"])
    out = []
    for a, b in zip(hb, hb[1:]):
        dt_ms = b["elapsed_ms"] - a["elapsed_ms"]
        if not 1000 <= dt_ms <= 6000:
            continue
        expected = dt_ms / PACKET_MS
        rx = b["audio_rx_packets"] - a["audio_rx_packets"]
        out.append({
            "elapsed_ms": b["elapsed_ms"],
            "dt_ms": dt_ms,
            "starv": b["audio_prolonged_starvation_events"]
                     - a["audio_prolonged_starvation_events"],
            "audio_rx": rx,
            "audio_expected": round(expected, 1),
            "audio_deficit": round(expected - rx, 1),
            "audio_lost": b["audio_lost_packets"] - a["audio_lost_packets"],
            "conc_under": b["audio_concealed_underruns"]
                          - a["audio_concealed_underruns"],
            "max_gap_ms": b.get("audio_max_arrival_gap_ms"),
            "queue_depth": b.get("audio_queue_depth"),
            "queue_ms": b.get("audio_queue_ms"),
            "video_lost": b["lost_packets"] - a["lost_packets"],
        })
    return out


def report(rows, target, cands, title):
    print("\n--- %s: Spearman of %s, n=%d ---" % (title, target, len(rows)))
    v = [r[target] for r in rows]
    for k in cands:
        rho, n = spearman(v, [r.get(k) for r in rows])
        col = [r.get(k) for r in rows if r.get(k) is not None]
        spread = ("const %g" % col[0]) if col and len(set(col)) == 1 else (
            "%g..%g" % (min(col), max(col)) if col else "absent")
        print("  %-16s %8s %6d  %s"
              % (k, "-" if rho is None else "%+.3f" % rho, n, spread))


def main():
    scratch, arm = sys.argv[1], sys.argv[2]
    hb = load(os.path.join(scratch, "heartbeat_%s.jsonl" % arm))
    rows = ticks(hb)
    print("=" * 74)
    print("heartbeats with audio fields: %d, usable tick intervals: %d"
          % (len([r for r in hb if "audio_rx_packets" in r]), len(rows)))
    if not rows:
        print("NO AUDIO FIELDS — the client or the companion dropped them")
        return

    starv = [r["starv"] for r in rows]
    print("\n--- is the counter quantized? ---")
    dist = {}
    for s in starv:
        dist[s] = dist.get(s, 0) + 1
    print("  starvation delta per 2 s tick: %s"
          % dict(sorted(dist.items())))
    print("  total %d, mean %.2f, sd %.2f, per minute %.1f"
          % (sum(starv), st.mean(starv),
             st.pstdev(starv), st.mean(starv) * 30))
    print("  ticks with zero starvation: %d of %d (%.0f%%)"
          % (starv.count(0), len(starv), 100.0 * starv.count(0) / len(starv)))
    print("  NOTE the code: one increment per CONTIGUOUS run of >%d empty"
          % FADE_CONCEAL_PACKETS)
    print("       %d ms polls, latched by starvationEpisodeCounted, so it"
          % PACKET_MS)
    print("       counts EPISODES (a gap > ~%d ms), not polls."
          % ((FADE_CONCEAL_PACKETS + 1) * PACKET_MS))

    gaps = [r["max_gap_ms"] for r in rows if r.get("max_gap_ms") is not None]
    if gaps:
        print("\n--- the audio arrival gap ---")
        print("  per-tick max gap: min %d median %.0f p90 %.0f max %d ms"
              % (min(gaps), st.median(gaps),
                 sorted(gaps)[int(0.9 * len(gaps))], max(gaps)))
        thr = (FADE_CONCEAL_PACKETS + 1) * PACKET_MS
        over = sum(1 for g in gaps if g > thr)
        print("  ticks whose max gap exceeds the %d ms episode threshold: "
              "%d of %d (%.0f%%)" % (thr, over, len(gaps),
                                     100.0 * over / len(gaps)))

    cands = ["max_gap_ms", "audio_deficit", "audio_lost", "conc_under",
             "queue_depth", "queue_ms", "video_lost", "audio_rx"]
    report(rows, "starv", cands, "per 2 s tick")

    # per minute
    per = {}
    for r in rows:
        m = r["elapsed_ms"] // 60000
        d = per.setdefault(m, {"starv": 0, "audio_deficit": 0.0,
                               "audio_lost": 0, "video_lost": 0,
                               "conc_under": 0, "max_gap_ms": 0,
                               "queue_depth": 0, "queue_ms": 0, "n": 0})
        d["starv"] += r["starv"]
        d["audio_deficit"] += r["audio_deficit"]
        d["audio_lost"] += r["audio_lost"]
        d["video_lost"] += r["video_lost"]
        d["conc_under"] += r["conc_under"]
        d["max_gap_ms"] = max(d["max_gap_ms"], r.get("max_gap_ms") or 0)
        d["queue_depth"] += r.get("queue_depth") or 0
        d["queue_ms"] += r.get("queue_ms") or 0
        d["n"] += 1
    mins = [per[m] for m in sorted(per) if per[m]["n"] >= 20]
    for d in mins:
        d["queue_depth"] = round(d["queue_depth"] / d["n"], 2)
        d["queue_ms"] = round(d["queue_ms"] / d["n"], 2)
    report(mins, "starv", cands, "per minute")

    q = sorted(rows, key=lambda r: -r["starv"])
    cut = max(1, len(q) // 10)
    print("\nTop %d ticks by starvation:" % cut)
    print("  %8s %6s %8s %8s %9s %8s %8s %8s"
          % ("elapsed", "starv", "max_gap", "deficit", "audio_rx",
             "a_lost", "v_lost", "q_depth"))
    for r in q[:cut]:
        print("  %8d %6d %8s %8.1f %9d %8d %8d %8s"
              % (r["elapsed_ms"], r["starv"], r.get("max_gap_ms"),
                 r["audio_deficit"], r["audio_rx"], r["audio_lost"],
                 r["video_lost"], r.get("queue_depth")))
    print("\nTicks with zero starvation, same columns (first %d):" % cut)
    for r in [x for x in rows if x["starv"] == 0][:cut]:
        print("  %8d %6d %8s %8.1f %9d %8d %8d %8s"
              % (r["elapsed_ms"], r["starv"], r.get("max_gap_ms"),
                 r["audio_deficit"], r["audio_rx"], r["audio_lost"],
                 r["video_lost"], r.get("queue_depth")))

    with open(os.path.join(scratch, "p7_ticks.json"), "w") as fh:
        json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    main()
