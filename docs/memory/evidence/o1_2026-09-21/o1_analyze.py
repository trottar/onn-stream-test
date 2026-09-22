#!/usr/bin/env python3
"""O1 analysis: the client's per-minute loss beside the Opal's own view.

Client side comes from the D-BASE-R5 heartbeat counters (cumulative, so a
per-minute figure is a subtraction). Opal side comes from o1_opal_sample.sh.

Two different kinds of Opal number, kept apart on purpose:

  * COUNTERS -- station tx_retries / tx_failed / rx_drop_misc / tx_packets
    and the per-interface rx/tx dropped and errors. Cumulative; differenced
    per minute.
  * INSTANTS -- airtime (a 30 ms busy/active window, which this driver does
    NOT accumulate), signal, bitrates, noise, load. Averaged per minute,
    never differenced.

Spearman is computed without scipy (rank transform + Pearson on ranks) and
is reported with its n; a rho on fewer than 10 minutes is not reported.

usage: o1_analyze.py <scratch_dir> <label> [<label> ...]
"""
import json, math, os, sys, statistics as st
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


CLIENT_COUNTERS = ["lost_packets", "forward_gap_events", "rx_packets",
                   "lost_packets_in_resyncs", "stream_resyncs",
                   "fec_recovered_packets", "fec_unrecoverable_groups"]
STA_COUNTERS = ["tx_retries", "tx_failed", "tx_packets", "rx_packets",
                "rx_drop_misc"]
STA_INSTANTS = ["signal_dbm", "signal_avg_dbm", "tx_bitrate_mbps",
                "rx_bitrate_mbps", "tx_mcs", "tx_width_mhz",
                "expected_tput_mbps"]


def per_minute(scratch, label):
    """One row per wall-clock minute, both sides on the same clock."""
    hb = load(os.path.join(scratch, "heartbeat_%s.jsonl" % label))
    air = load(os.path.join(scratch, "air_%s.jsonl" % label))
    if not hb:
        return [], {}

    t0 = ts(hb[0]["received_at_utc"])

    def minute_of(t):
        return int((t - t0).total_seconds() // 60)

    # --- client counters -> per-minute deltas ---------------------------
    client = {}
    for a, b in zip(hb, hb[1:]):
        m = minute_of(ts(a["received_at_utc"]))
        d = client.setdefault(m, {k: 0 for k in CLIENT_COUNTERS})
        for k in CLIENT_COUNTERS:
            if k in a and k in b:
                d[k] += max(0, b[k] - a[k])

    # --- Opal: the busiest station is the one under test ----------------
    # One station is associated on wlan1 in this run; if more appear, the
    # one with the largest tx_packets movement is taken and the others are
    # reported separately rather than averaged in.
    def sta_of(row):
        sts = row.get("stations") or []
        if not sts:
            return None
        return max(sts, key=lambda s: s.get("tx_packets") or 0)

    by_min = {}
    for r in air:
        t = ts(r["at_utc"])
        by_min.setdefault(minute_of(t), []).append(r)

    opal = {}
    for m, rows in by_min.items():
        rows.sort(key=lambda r: r["seq"])
        o = {}
        # instants: mean over the minute
        for k in ["utilization_pct", "busy_fraction", "noise_dbm",
                  "busy_ms"]:
            vs = [(r.get("airtime") or {}).get(k) for r in rows]
            vs = [v for v in vs if v is not None]
            if vs:
                o[k] = round(sum(vs) / len(vs), 4)
        for k in STA_INSTANTS:
            vs = [sta_of(r).get(k) for r in rows if sta_of(r)]
            vs = [v for v in vs if v is not None]
            if vs:
                o[k] = round(sum(vs) / len(vs), 3)
                o[k + "_min"] = min(vs)
        vs = [r.get("loadavg_1m") for r in rows if r.get("loadavg_1m")]
        if vs:
            o["opal_load"] = round(sum(vs) / len(vs), 3)
        vs = [r.get("round_cost_ms") for r in rows if r.get("round_cost_ms")]
        if vs:
            o["round_cost_ms"] = int(sum(vs) / len(vs))
        # counters: last-minus-first inside the minute
        first, last = rows[0], rows[-1]
        fa, la = sta_of(first), sta_of(last)
        if fa and la:
            for k in STA_COUNTERS:
                if fa.get(k) is not None and la.get(k) is not None:
                    o["d_" + k] = la[k] - fa[k]
        fs, ls = first.get("iface_stats") or {}, last.get("iface_stats") or {}
        for iface in sorted(set(fs) & set(ls)):
            for k in ["rx_dropped", "tx_dropped", "rx_errors", "tx_errors",
                      "rx_packets", "tx_packets"]:
                if k in fs[iface] and k in ls[iface]:
                    o["d_%s_%s" % (iface, k)] = ls[iface][k] - fs[iface][k]
        o["log_events"] = [e for r in rows for e in (r.get("log_events") or [])]
        o["samples"] = len(rows)
        opal[m] = o

    rows = []
    for m in sorted(set(client) | set(opal)):
        row = {"minute": m}
        row.update(client.get(m, {}))
        row.update(opal.get(m, {}))
        rows.append(row)
    meta = {
        "heartbeats": len(hb),
        "air_rounds": len(air),
        "t0": hb[0]["received_at_utc"],
        "t1": hb[-1]["received_at_utc"],
    }
    return rows, meta


def main():
    scratch, labels = sys.argv[1], sys.argv[2:]
    allrows = []
    for label in labels:
        rows, meta = per_minute(scratch, label)
        print("\n=== session %s: %s" % (label, json.dumps(meta)))
        if not rows:
            print("  no data")
            continue
        # only the minutes with both sides, and drop the partial last one
        full = [r for r in rows
                if r.get("samples", 0) >= 4 and "lost_packets" in r]
        for r in full:
            r["session"] = label
        allrows += full
        print("  full minutes: %d" % len(full))
        with open(os.path.join(scratch, "per_minute_%s.json" % label), "w") as f:
            json.dump(rows, f, indent=1)

    if not allrows:
        return
    with open(os.path.join(scratch, "per_minute_all.json"), "w") as f:
        json.dump(allrows, f, indent=1)

    loss = [r.get("lost_packets") for r in allrows]
    print("\n=== pooled: %d minutes over %d sessions" % (
        len(allrows), len(labels)))
    print("loss/min: min %s  median %s  max %s  total %s" % (
        min(loss), st.median(loss), max(loss), sum(loss)))

    candidates = ["utilization_pct", "busy_fraction", "d_tx_retries",
                  "d_tx_failed", "d_rx_drop_misc", "d_tx_packets",
                  "signal_dbm", "signal_avg_dbm", "tx_bitrate_mbps",
                  "rx_bitrate_mbps", "tx_mcs", "expected_tput_mbps",
                  "noise_dbm", "opal_load"]
    candidates += sorted({k for r in allrows for k in r
                          if k.startswith("d_") and
                          ("dropped" in k or "errors" in k)})
    print("\nSpearman of per-minute client loss against each Opal reading:")
    print("  %-28s %8s %6s  %s" % ("reading", "rho", "n", "spread"))
    results = {}
    for k in candidates:
        vals = [r.get(k) for r in allrows]
        rho, n = spearman(loss, vals)
        present = [v for v in vals if v is not None]
        spread = ("const %g" % present[0]) if present and len(set(present)) == 1 \
            else ("%g..%g" % (min(present), max(present)) if present else "absent")
        if rho is None or n < 10:
            print("  %-28s %8s %6d  %s" % (k, "-", n, spread))
        else:
            results[k] = (rho, n)
            print("  %-28s %8.3f %6d  %s" % (k, rho, n, spread))

    # forward gaps too, since they are the burst signature
    fg = [r.get("forward_gap_events") for r in allrows]
    print("\nSpearman of per-minute forward_gap_events against each:")
    for k in candidates:
        vals = [r.get(k) for r in allrows]
        rho, n = spearman(fg, vals)
        if rho is not None and n >= 10 and abs(rho) >= 0.3:
            print("  %-28s %8.3f %6d" % (k, rho, n))

    q = sorted(allrows, key=lambda r: -r["lost_packets"])
    cut = max(1, len(q) // 4)
    print("\nTop-quartile loss minutes (%d of %d), with their Opal readings:"
          % (cut, len(allrows)))
    hdr = ["sess", "min", "loss", "fgap", "util%", "d_retry", "d_fail",
           "d_drop", "sig", "txMbps", "mcs", "d_txpkt"]
    print("  " + " ".join("%7s" % h for h in hdr))
    for r in q[:cut]:
        print("  " + " ".join("%7s" % str(r.get(k, "-"))[:7] for k in
              ["session", "minute", "lost_packets", "forward_gap_events",
               "utilization_pct", "d_tx_retries", "d_tx_failed",
               "d_rx_drop_misc", "signal_dbm", "tx_bitrate_mbps", "tx_mcs",
               "d_tx_packets"]))
    print("\nBottom-quartile loss minutes, same columns:")
    for r in q[-cut:]:
        print("  " + " ".join("%7s" % str(r.get(k, "-"))[:7] for k in
              ["session", "minute", "lost_packets", "forward_gap_events",
               "utilization_pct", "d_tx_retries", "d_tx_failed",
               "d_rx_drop_misc", "signal_dbm", "tx_bitrate_mbps", "tx_mcs",
               "d_tx_packets"]))

    ev = [(r["session"], r["minute"], r["lost_packets"], e)
          for r in allrows for e in r.get("log_events", [])]
    print("\nOpal log events during the sessions: %d" % len(ev))
    for s, m, l, e in ev:
        print("  [%s min %d loss %d] %s" % (s, m, l, e))

    print("\nRetry and failure rate over the pooled minutes:")
    tp = sum(r.get("d_tx_packets") or 0 for r in allrows)
    tr = sum(r.get("d_tx_retries") or 0 for r in allrows)
    tf = sum(r.get("d_tx_failed") or 0 for r in allrows)
    if tp:
        print("  tx packets %d  retries %d (%.2f%%)  failed %d (%.2f%%)"
              % (tp, tr, 100.0 * tr / tp, tf, 100.0 * tf / tp))


if __name__ == "__main__":
    main()
