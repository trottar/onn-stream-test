#!/usr/bin/env python3
"""D-BASE-P5: which queue drops the burst.

Three series on one clock (host UTC):

  * frame size, from the relay's per-second buckets
    (`logs/games/native_frame_sizes.jsonl`);
  * the onn's `/proc/net/udp6` receive-queue `drops` and `rx_queue`,
    sampled every 2 s over adb;
  * client loss, from the D-BASE-R5 heartbeat counters.

Counters are differenced (loss, forward gaps, socket drops); instants are
maxed or averaged over the window (rx_queue, max packets per frame). The
two are never mixed, which is the rule `O1` had to learn about the Opal's
airtime instrument.

Spearman is computed without scipy: rank transform, then Pearson on ranks.

usage: p5_analyze.py <scratch_dir> <label> [<label> ...]
"""
import json
import math
import os
import statistics as st
import sys
from datetime import datetime, timezone


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
        tzinfo=timezone.utc
    )


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


def windows(scratch, label, span_s):
    """One row per `span_s` of the session, all three series aligned."""
    hb = load(os.path.join(scratch, "heartbeat_%s.jsonl" % label))
    fr = load(os.path.join(scratch, "frames_%s.jsonl" % label))
    sk = load(os.path.join(scratch, "socket_%s.jsonl" % label))
    if not hb:
        return []

    t0 = ts(hb[0]["received_at_utc"])

    def bucket(t):
        return int((t - t0).total_seconds() // span_s)

    rows = {}

    def row(i):
        return rows.setdefault(
            i,
            {
                "session": label,
                "window": i,
                "lost_packets": 0,
                "forward_gap_events": 0,
                "rx_packets": 0,
                "hb": 0,
                "frames": 0,
                "frame_packets": 0,
                "max_packets": 0,
                "frames_ge_40": 0,
                "frames_ge_80": 0,
                "frame_seconds": 0,
                "drops_delta": None,
                "rx_queue_peak": None,
                "sock_samples": 0,
            },
        )

    # client loss: cumulative, so difference consecutive heartbeats
    hb.sort(key=lambda r: r["elapsed_ms"])
    for a, b in zip(hb, hb[1:]):
        r = row(bucket(ts(a["received_at_utc"])))
        r["lost_packets"] += max(0, b["lost_packets"] - a["lost_packets"])
        r["forward_gap_events"] += max(
            0, b["forward_gap_events"] - a["forward_gap_events"]
        )
        r["rx_packets"] += max(0, b["rx_packets"] - a["rx_packets"])
        r["hb"] += 1

    # frame size: per-second buckets, summed / maxed into the window
    for f in fr:
        i = bucket(ts(f["at_utc"]))
        if i < 0:
            continue
        r = row(i)
        r["frames"] += f.get("frames", 0)
        r["frame_packets"] += f.get("packets", 0)
        r["max_packets"] = max(r["max_packets"], f.get("max_packets", 0))
        r["frames_ge_40"] += f.get("frames_ge_40", 0)
        r["frames_ge_80"] += f.get("frames_ge_80", 0)
        r["frame_seconds"] += 1

    # socket: drops are cumulative, rx_queue is an instant
    stream = [s for s in sk if s.get("sockets", {}).get("video_48100")]
    stream.sort(key=lambda s: s["seq"])
    by_window = {}
    for s in stream:
        i = bucket(ts(s["at_utc"]))
        if i < 0:
            continue
        by_window.setdefault(i, []).append(s)
    for i, group in by_window.items():
        r = row(i)
        first = group[0]["sockets"]["video_48100"]
        last = group[-1]["sockets"]["video_48100"]
        r["drops_delta"] = max(0, last["drops"] - first["drops"])
        r["rx_queue_peak"] = max(
            g["sockets"]["video_48100"]["rx_queue"] for g in group
        )
        r["audio_drops_delta"] = max(
            0,
            group[-1]["sockets"].get("audio_48101", {}).get("drops", 0)
            - group[0]["sockets"].get("audio_48101", {}).get("drops", 0),
        )
        r["sock_samples"] = len(group)

    out = [rows[i] for i in sorted(rows)]
    for r in out:
        if r["frames"]:
            r["mean_packets"] = round(r["frame_packets"] / r["frames"], 3)
    # keep only windows with all three instruments actually reporting
    return [
        r
        for r in out
        if r["hb"] >= 2 and r["frame_seconds"] >= max(1, span_s // 2)
        and r["sock_samples"] >= 1
    ]


CANDIDATES = [
    "max_packets",
    "frames_ge_40",
    "frames_ge_80",
    "mean_packets",
    "drops_delta",
    "rx_queue_peak",
    "frames",
    "rx_packets",
]


def report(rows, title, target="lost_packets"):
    print("\n--- %s: Spearman of %s, n=%d ---" % (title, target, len(rows)))
    vals = [r[target] for r in rows]
    print("  %-16s %8s %6s  %s" % ("reading", "rho", "n", "spread"))
    for k in CANDIDATES:
        col = [r.get(k) for r in rows]
        rho, n = spearman(vals, col)
        present = [v for v in col if v is not None]
        if not present:
            spread = "absent"
        elif len(set(present)) == 1:
            spread = "const %g" % present[0]
        else:
            spread = "%g..%g" % (min(present), max(present))
        print(
            "  %-16s %8s %6d  %s"
            % (k, "-" if rho is None else "%.3f" % rho, n, spread)
        )


def main():
    scratch, labels = sys.argv[1], sys.argv[2:]
    for span, name in ((10, "10 s windows"), (60, "per minute")):
        pooled = []
        for label in labels:
            w = windows(scratch, label, span)
            print("\n=== session %s, %s: %d windows" % (label, name, len(w)))
            pooled += w
            with open(
                os.path.join(scratch, "p5_windows_%s_%ds.json" % (label, span)),
                "w",
            ) as fh:
                json.dump(w, fh, indent=1)
        if not pooled:
            continue
        with open(
            os.path.join(scratch, "p5_windows_pooled_%ds.json" % span), "w"
        ) as fh:
            json.dump(pooled, fh, indent=1)

        loss = [r["lost_packets"] for r in pooled]
        drops = [r.get("drops_delta") or 0 for r in pooled]
        print(
            "\npooled %s: %d windows, loss total %d (min %d median %d max %d)"
            % (name, len(pooled), sum(loss), min(loss), st.median(loss), max(loss))
        )
        print(
            "onn socket drops total %d  (= %.2f %% of lost_packets)"
            % (sum(drops), 100.0 * sum(drops) / sum(loss) if sum(loss) else 0.0)
        )
        adrops = sum(r.get("audio_drops_delta") or 0 for r in pooled)
        print("onn audio-socket drops total %d" % adrops)
        peaks = [r["rx_queue_peak"] for r in pooled if r.get("rx_queue_peak")]
        if peaks:
            print(
                "video rx_queue: max %d bytes, median window peak %d"
                % (max(peaks), st.median(peaks))
            )

        report(pooled, "pooled %s" % name, "lost_packets")
        report(pooled, "pooled %s" % name, "forward_gap_events")

        if span == 10:
            q = sorted(pooled, key=lambda r: -r["lost_packets"])
            cut = max(1, len(q) // 4)
            hdr = [
                "sess", "win", "loss", "fgap", "maxpkt", "ge40", "ge80",
                "meanpkt", "drops", "rxq_peak",
            ]
            keys = [
                "session", "window", "lost_packets", "forward_gap_events",
                "max_packets", "frames_ge_40", "frames_ge_80", "mean_packets",
                "drops_delta", "rx_queue_peak",
            ]
            print("\nTop-quartile loss windows (%d of %d):" % (cut, len(pooled)))
            print("  " + " ".join("%9s" % h for h in hdr))
            for r in q[:cut]:
                print("  " + " ".join("%9s" % str(r.get(k, "-"))[:9] for k in keys))
            print("\nBottom-quartile loss windows:")
            for r in q[-cut:]:
                print("  " + " ".join("%9s" % str(r.get(k, "-"))[:9] for k in keys))

            advanced = [r for r in pooled if (r.get("drops_delta") or 0) > 0]
            print(
                "\nWindows where the onn's drops counter advanced: %d of %d"
                % (len(advanced), len(pooled))
            )
            for r in advanced:
                print(
                    "  [%s win %d] drops +%d  loss %d  fgap %d  maxpkt %d  rxq %s"
                    % (
                        r["session"], r["window"], r["drops_delta"],
                        r["lost_packets"], r["forward_gap_events"],
                        r["max_packets"], r.get("rx_queue_peak"),
                    )
                )

    # the content-lock control, and frame size's own reproducibility
    print("\n=== the control: does each series repeat across sessions? ===")
    if len(labels) >= 2:
        per = {}
        for label in labels[:2]:
            per[label] = windows(scratch, label, 60)
        a, b = per[labels[0]], per[labels[1]]
        n = min(len(a), len(b))
        for key in ("lost_packets", "max_packets", "frames_ge_40",
                    "frames_ge_80", "mean_packets", "forward_gap_events"):
            va = [a[i].get(key) for i in range(n)]
            vb = [b[i].get(key) for i in range(n)]
            p = pearson(
                [x for x in va if x is not None],
                [y for y in vb if y is not None],
            )
            s, _ = spearman(va, vb)
            print(
                "  %-20s pearson %s  spearman %s  (n=%d)"
                % (
                    key,
                    "-" if p is None else "%.3f" % p,
                    "-" if s is None else "%.3f" % s,
                    n,
                )
            )


if __name__ == "__main__":
    main()
