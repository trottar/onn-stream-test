#!/usr/bin/env python3
"""D-BASE-P2 step 1 - audio underruns across the corpus, no runtime.

Reads logs/games/decoder_sessions/*.json directly. Selection matches the
Group A convention: a decoder block present, duration >= 15 s, received
2026-09-16 or later. Writes a CSV (LF line endings) and a JSON summary
beside this script.

Fits `underruns = burst + rate * minutes` by ordinary least squares, and
reports Spearman correlations between the underrun count and its
neighbours. scipy is used when present; a pure-stdlib Spearman is used
otherwise so the numbers exist either way.

Usage: python3 p2_audio_corpus.py --repo /path/to/onn-stream-test
"""
from __future__ import annotations
import argparse, csv, glob, json, math, os, statistics as st


FIELDS = (
    "underruns",
    "prolonged_starvation_events",
    "concealed_underruns",
    "concealed_loss_packets",
    "stale_drops",
    "smooth_latency_trims",
    "crossfaded_packets",
    "lost_packets",
    "packets",
    "max_queue_residence_ms",
    "avg_queue_residence_ms",
    "max_queue_depth",
)


def rank(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while (
            j + 1 < len(order)
            and values[order[j + 1]] == values[order[i]]
        ):
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def spearman(xs, ys):
    pairs = [
        (x, y)
        for x, y in zip(xs, ys)
        if x is not None and y is not None
    ]
    if len(pairs) < 4:
        return None
    rx = rank([p[0] for p in pairs])
    ry = rank([p[1] for p in pairs])
    n = len(pairs)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(
        sum((a - mx) ** 2 for a in rx)
        * sum((b - my) ** 2 for b in ry)
    )
    if den == 0:
        return None
    return {"rho": round(num / den, 3), "n": n}


def ols(xs, ys):
    """underruns = intercept + slope * minutes."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    intercept = my - slope * mx
    resid = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    ss_res = sum(r * r for r in resid)
    ss_tot = sum((y - my) ** 2 for y in ys)
    return {
        "burst_intercept": round(intercept, 1),
        "rate_per_min": round(slope, 2),
        "r2": round(1 - ss_res / ss_tot, 3) if ss_tot else None,
        "n": n,
        "residual_p50": round(st.median(resid), 1),
        "residual_max": round(max(resid), 1),
        "residual_min": round(min(resid), 1),
    }


def pct(values, q):
    if not values:
        return None
    v = sorted(values)
    i = (len(v) - 1) * q / 100.0
    lo, hi = int(i), min(int(i) + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (i - lo), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--since", default="2026-09-16")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    outdir = a.out or os.path.dirname(os.path.abspath(__file__))

    rows = []
    for path in sorted(
        glob.glob(
            os.path.join(
                a.repo, "logs", "games", "decoder_sessions", "*.json"
            )
        )
    ):
        doc = json.load(open(path))
        received = doc.get("received_at_utc") or ""
        if received < a.since:
            continue
        rep = doc["report"]
        if not (rep.get("decoder") or {}):
            continue
        dur = rep.get("duration_ms") or 0
        if dur < 15_000:
            continue
        aud = rep.get("audio") or {}
        if not aud:
            continue
        mins = dur / 60000.0
        row = {
            "file": os.path.basename(path),
            "received": received,
            "dur_s": round(dur / 1000.0, 1),
            "minutes": round(mins, 4),
        }
        for f in FIELDS:
            row[f] = aud.get(f)
        row["underruns_pm"] = (
            round(aud["underruns"] / mins, 1)
            if aud.get("underruns") is not None
            else None
        )
        row["starvation_pm"] = (
            round(aud["prolonged_starvation_events"] / mins, 1)
            if aud.get("prolonged_starvation_events") is not None
            else None
        )
        rows.append(row)

    keys = ["file", "received", "dur_s", "minutes"] + list(FIELDS) + [
        "underruns_pm",
        "starvation_pm",
    ]
    with open(
        os.path.join(outdir, "p2_audio_corpus.csv"),
        "w",
        newline="\n",
    ) as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(keys)
        for r in rows:
            w.writerow([r.get(k) for k in keys])

    have = [
        r
        for r in rows
        if r.get("underruns") is not None and r["minutes"] > 0
    ]
    fit = ols(
        [r["minutes"] for r in have],
        [float(r["underruns"]) for r in have],
    )

    # Long sessions isolate the steady rate; short ones are nearly all burst.
    longs = [r for r in have if r["dur_s"] >= 300]
    shorts = [r for r in have if r["dur_s"] < 40]

    corr = {}
    base = [
        float(r["underruns"]) if r.get("underruns") is not None else None
        for r in have
    ]
    for f in FIELDS:
        if f == "underruns":
            continue
        other = [
            float(r[f]) if r.get(f) is not None else None for r in have
        ]
        corr["underruns_vs_" + f] = spearman(base, other)

    # Does the per-minute rate fall with duration? A fixed burst plus a
    # steady rate implies it must.
    corr["underruns_pm_vs_duration"] = spearman(
        [float(r["dur_s"]) for r in have],
        [float(r["underruns_pm"]) for r in have],
    )
    corr["starvation_vs_underruns"] = corr.get(
        "underruns_vs_prolonged_starvation_events"
    )

    out = {
        "selection": {
            "since": a.since,
            "sessions": len(rows),
            "with_underruns": len(have),
            "sessions_ge_300s": len(longs),
            "sessions_lt_40s": len(shorts),
        },
        "underruns": {
            "total_p50": pct([r["underruns"] for r in have], 50),
            "total_p90": pct([r["underruns"] for r in have], 90),
            "total_max": max((r["underruns"] for r in have), default=None),
            "per_min_p50": pct([r["underruns_pm"] for r in have], 50),
            "per_min_p90": pct([r["underruns_pm"] for r in have], 90),
        },
        "fit_underruns_eq_burst_plus_rate_x_minutes": fit,
        "sessions_ge_300s": {
            "n": len(longs),
            "underruns_total_p50": pct(
                [r["underruns"] for r in longs], 50
            ),
            "underruns_pm_p50": pct(
                [r["underruns_pm"] for r in longs], 50
            ),
        },
        "sessions_lt_40s": {
            "n": len(shorts),
            "underruns_total_p50": pct(
                [r["underruns"] for r in shorts], 50
            ),
            "underruns_pm_p50": pct(
                [r["underruns_pm"] for r in shorts], 50
            ),
        },
        "spearman": corr,
    }

    with open(
        os.path.join(outdir, "p2_audio_corpus_result.json"), "w"
    ) as fh:
        json.dump(out, fh, indent=1, default=str)

    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
