#!/usr/bin/env python3
"""O1, second pass: the same comparison at the sampler's own 10 s cadence.

Why a second resolution. The two Opal instruments are not alike:

  * `tx retries` is a CUMULATIVE counter. It integrates every transmission,
    so differencing it over any window is complete -- nothing between the
    samples escapes it. It can be pushed to 10 s and gains power.
  * airtime is an INSTANTANEOUS 30 ms window read once per round, i.e. the
    radio is observed for 30 ms in every 10,000 -- a 0.3 % duty cycle. More
    rows do not make that instrument see more; a contention burst shorter
    than a few seconds is simply missed. Its rho is reported with that
    caveat attached and is not evidence of absence.

Client loss per window comes from the D-BASE-R5 heartbeat counters, which
are cumulative too, so the window edges are exact on both sides.

usage: o1_fine.py <scratch_dir> <label> [<label> ...]
"""
import json, os, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o1_analyze import load, ts, spearman  # noqa: E402


def windows(scratch, label):
    hb = load(os.path.join(scratch, "heartbeat_%s.jsonl" % label))
    air = load(os.path.join(scratch, "air_%s.jsonl" % label))
    if not hb or not air:
        return []
    hb.sort(key=lambda r: r["elapsed_ms"])
    air = [r for r in air if r.get("stations")]
    air.sort(key=lambda r: r["seq"])

    def sta(r):
        return max(r["stations"], key=lambda s: s.get("tx_packets") or 0)

    out = []
    for a, b in zip(air, air[1:]):
        t0, t1 = ts(a["at_utc"]), ts(b["at_utc"])
        inside = [h for h in hb if t0 <= ts(h["received_at_utc"]) <= t1]
        if len(inside) < 3:
            continue
        sa, sb = sta(a), sta(b)
        dt = (t1 - t0).total_seconds()
        if not 8.0 <= dt <= 13.0:
            continue
        row = {
            "session": label,
            "dt_s": round(dt, 2),
            "loss": inside[-1]["lost_packets"] - inside[0]["lost_packets"],
            "fgap": (inside[-1]["forward_gap_events"]
                     - inside[0]["forward_gap_events"]),
            "cli_rx": inside[-1]["rx_packets"] - inside[0]["rx_packets"],
            "d_tx_retries": (sb.get("tx_retries", 0) - sa.get("tx_retries", 0)),
            "d_tx_packets": (sb.get("tx_packets", 0) - sa.get("tx_packets", 0)),
            "d_rx_drop_misc": (sb.get("rx_drop_misc", 0)
                               - sa.get("rx_drop_misc", 0)),
            # instants, taken at the window's close
            "utilization_pct": (b.get("airtime") or {}).get("utilization_pct"),
            "signal_dbm": sb.get("signal_dbm"),
            "tx_bitrate_mbps": sb.get("tx_bitrate_mbps"),
            "tx_mcs": sb.get("tx_mcs"),
            "noise_dbm": (b.get("airtime") or {}).get("noise_dbm"),
        }
        if row["d_tx_packets"] > 0:
            row["retry_rate"] = round(
                row["d_tx_retries"] / row["d_tx_packets"], 5)
        out.append(row)
    return out


def main():
    scratch, labels = sys.argv[1], sys.argv[2:]
    rows = []
    for label in labels:
        w = windows(scratch, label)
        print("session %s: %d ten-second windows" % (label, len(w)))
        rows += w
    if not rows:
        return
    with open(os.path.join(scratch, "fine_windows.json"), "w") as f:
        json.dump(rows, f, indent=1)

    loss = [r["loss"] for r in rows]
    print("\npooled %d windows; loss/window min %d median %d max %d total %d"
          % (len(rows), min(loss), sorted(loss)[len(loss) // 2], max(loss),
             sum(loss)))
    zero = sum(1 for x in loss if x == 0)
    print("windows with zero loss: %d (%.0f%%)" % (zero, 100.0 * zero / len(loss)))

    print("\nSpearman against per-window loss (n = number of paired windows):")
    for k in ["d_tx_retries", "retry_rate", "d_rx_drop_misc", "d_tx_packets",
              "utilization_pct", "signal_dbm", "tx_bitrate_mbps", "tx_mcs",
              "noise_dbm", "cli_rx"]:
        vals = [r.get(k) for r in rows]
        rho, n = spearman(loss, vals)
        present = [v for v in vals if v is not None]
        if not present:
            print("  %-18s absent" % k)
        elif len(set(present)) == 1:
            print("  %-18s %8s %5d  const %g" % (k, "-", n, present[0]))
        else:
            print("  %-18s %8.3f %5d  %g..%g"
                  % (k, rho, n, min(present), max(present)))

    fg = [r["fgap"] for r in rows]
    print("\nSpearman against per-window forward_gap_events:")
    for k in ["d_tx_retries", "retry_rate", "utilization_pct", "signal_dbm"]:
        rho, n = spearman(fg, [r.get(k) for r in rows])
        if rho is not None:
            print("  %-18s %8.3f %5d" % (k, rho, n))

    # The sharpest form of the question: do the worst windows look different
    # on the Opal from the quiet ones?
    ranked = sorted(rows, key=lambda r: -r["loss"])
    cut = max(1, len(ranked) // 10)
    worst, quiet = ranked[:cut], [r for r in rows if r["loss"] == 0]
    print("\nworst %d windows vs the %d zero-loss windows:" % (cut, len(quiet)))
    for k in ["d_tx_retries", "retry_rate", "utilization_pct", "signal_dbm",
              "tx_bitrate_mbps", "d_tx_packets"]:
        def mean(g):
            v = [r.get(k) for r in g if r.get(k) is not None]
            return sum(v) / len(v) if v else float("nan")
        print("  %-18s worst %10.3f   zero-loss %10.3f"
              % (k, mean(worst), mean(quiet)))
    print("  %-18s worst %10.3f   zero-loss %10.3f"
          % ("loss", sum(r["loss"] for r in worst) / len(worst), 0.0))


if __name__ == "__main__":
    main()
