#!/usr/bin/env python3
"""D-BASE-S3: three hours on the adopted 90 KB cap.

Answers the three questions the task asks:
  1. does the cap hold its 7-9x for hours, or does drift eat it;
  2. what the RESIDUAL loss tracks now that the tail is gone;
  3. whether the frame-size and heartbeat logs rotate cleanly mid-session.

Per-minute and per-10 s series, the bucketed loss table from P6 §5, hourly
totals, rotation checks, and the S2 / A1 comparisons.

usage: s3_analyze.py <scratch_dir> <arm>
"""
import json
import os
import statistics as st
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "d_base_p6_2026-09-21"))
from p6_analyze import (  # noqa: E402
    load, ts, pearson, spearman, windows, bucket_loss, encoder_bitrate,
)


def hourly(rows, key, span_s):
    """Totals per wall-clock hour of the session."""
    per = {}
    for r in rows:
        h = (r["window"] * span_s) // 3600
        per[h] = per.get(h, 0) + (r.get(key) or 0)
    return [per.get(h, 0) for h in sorted(per)]


def rotation_check(live, archive_glob):
    """Did the log rotate, and does the series continue across it?"""
    import glob
    arch = sorted(glob.glob(archive_glob))
    return {
        "live": live,
        "live_bytes": os.path.getsize(live) if os.path.exists(live) else 0,
        "archived": [(os.path.basename(a), os.path.getsize(a)) for a in arch],
        "rotations": len(arch),
    }


def main():
    scratch, arm = sys.argv[1], sys.argv[2]
    repo = "/home/privyhub/Projects/onn-stream-test"

    w60 = windows(scratch, arm, 60)
    w10 = windows(scratch, arm, 10)
    print("=" * 74)
    print("D-BASE-S3 -- %d one-minute windows, %d ten-second windows"
          % (len(w60), len(w10)))

    # ---- the gate: every minute zero >=80 and <=90,000 bytes -----------
    bad80 = [r for r in w60 if r["frames_ge_80"] > 0]
    badby = [r for r in w60 if r["max_bytes"] > 90_000]
    print("\n--- the cap held? ---")
    print("  minutes with >=80-packet frames : %d %s"
          % (len(bad80), "" if not bad80 else [r["window"] for r in bad80[:10]]))
    print("  minutes with a frame > 90,000 B : %d %s"
          % (len(badby), "" if not badby else
             [(r["window"], r["max_bytes"]) for r in badby[:10]]))
    print("  max frame bytes over the session: %d"
          % max((r["max_bytes"] for r in w60), default=0))
    print("  max packets per frame           : %d"
          % max((r["max_packets"] for r in w60), default=0))

    # ---- loss ----------------------------------------------------------
    loss = [r["lost_packets"] for r in w60]
    print("\n--- loss ---")
    print("  total %d over %d min = %.1f/min (bar for SOAK VALIDATED: <= 30)"
          % (sum(loss), len(loss), sum(loss) / len(loss) if loss else 0))
    print("  per-minute min %d median %.1f max %d"
          % (min(loss), st.median(loss), max(loss)))
    hl = hourly(w60, "lost_packets", 60)
    print("  hourly totals: %s" % hl)
    if len(hl) >= 2 and min(hl) > 0:
        print("  worst/best hour ratio: %.2fx (drift flagged above 2.0)"
              % (max(hl) / min(hl)))
    # NB: the true max FORWARD GAP is a session field in the decoder
    # report, printed below. Per-window we only have the largest frame.
    print("  forward-gap events %d (max forward gap: see the report)"
          % sum(r["forward_gap_events"] for r in w60))
    print("  per-minute series:")
    print("   " + " ".join(str(x) for x in loss))

    # ---- what the residual tracks --------------------------------------
    print("\n--- what the RESIDUAL tracks (pre-registered) ---")
    for span, rows, name in ((10, w10, "10 s"), (60, w60, "per minute")):
        print("  %s windows, n=%d" % (name, len(rows)))
        for k in ("max_packets", "max_bytes", "frames_ge_40", "mean_packets",
                  "frames", "rx_packets"):
            rho, n = spearman([r["lost_packets"] for r in rows],
                              [r.get(k) for r in rows])
            print("    %-14s rho %s  n=%d"
                  % (k, "-" if rho is None else "%+.3f" % rho, n))

    print("\n  bucketed loss (windows assigned by their largest frame):")
    print("    %-8s %8s %9s %8s %10s"
          % ("bucket", "windows", "frames", "loss", "loss/win"))
    for label, nwin, frames, l, per in bucket_loss(w10):
        print("    %-8s %8d %9d %8s %10s" % (label, nwin, frames, l, per))

    # ---- session-level -------------------------------------------------
    rp = os.path.join(scratch, "report_%s.json" % arm)
    if os.path.exists(rp):
        r = json.load(open(rp))["report"]
        dur = r["duration_ms"] / 1000.0
        v, d, a = r["video"], r["decoder"], r["audio"]
        print("\n--- session report (%.1f min) ---" % (dur / 60))
        print("  video %d pkts, loss %d (%.4f%%, %.1f/min), fgap %d, "
              "max gap %d pkt, resyncs %d, ssrc %d"
              % (v["packets"], v["lost_packets"],
                 100 * v["lost_packets"] / v["packets"],
                 v["lost_packets"] / (dur / 60), v["forward_gap_events"],
                 v["max_forward_gap_packets"], v["sequence_resyncs"],
                 v["ssrc_changes"]))
        print("  audio %d pkts, loss %d (%.4f%%), underruns %d, "
              "starvation %d (%.1f/min)"
              % (a["packets"], a["lost_packets"],
                 100 * a["lost_packets"] / a["packets"], a["underruns"],
                 a["prolonged_starvation_events"],
                 a["prolonged_starvation_events"] / (dur / 60)))
        print("  fps %.2f, spike20 %.1f/min, max output gap %d ms, "
              "max rx->decode %d ms"
              % (d["rendered_frames"] / dur, d["spike_20_ms"] / (dur / 60),
                 d["max_output_gap_ms"], d["max_rx_to_decode_ms"]))
    mean, rng = encoder_bitrate(os.path.join(scratch, "alpha_%s.log" % arm))
    print("  encoder %s kbps (per-0.5 s %s)" % (mean, rng))

    # ---- rotation ------------------------------------------------------
    print("\n--- rotation ---")
    for live, name in (
        (repo + "/logs/games/native_frame_sizes.jsonl", "frame sizes"),
        (repo + "/logs/games/native_stream_heartbeat.log", "heartbeat"),
    ):
        info = rotation_check(
            live, repo + "/logs/games/stream_log_archive/"
            + os.path.basename(live) + "*")
        print("  %-12s live %9d B, %d archived %s"
              % (name, info["live_bytes"], info["rotations"],
                 info["archived"]))
    fr = load(os.path.join(scratch, "frames_%s.jsonl" % arm))
    if fr:
        secs = [f["t"] for f in fr]
        gaps = [b - a for a, b in zip(secs, secs[1:]) if b - a != 1]
        print("  frame-size series: %d seconds, %d discontinuities %s"
              % (len(fr), len(gaps), gaps[:10]))
    hb = load(os.path.join(scratch, "heartbeat_%s.jsonl" % arm))
    if hb:
        hb.sort(key=lambda r: r["elapsed_ms"])
        iv = [b["elapsed_ms"] - a["elapsed_ms"] for a, b in zip(hb, hb[1:])]
        print("  heartbeat: %d lines, interval min %d max %d ms"
              % (len(hb), min(iv), max(iv)))

    # ---- socket + opal --------------------------------------------------
    drops = sum(r.get("drops_delta") or 0 for r in w10)
    print("\n  onn socket drops over three hours: %d" % drops)
    air = load(os.path.join(scratch, "air_%s.jsonl" % arm))
    if air:
        util = [(a.get("airtime") or {}).get("utilization_pct")
                for a in air]
        util = [u for u in util if u is not None]
        ks = [r["window"] for r in w60]
        print("  opal: %d rounds, channel utilization mean %.2f%% (%.1f-%.1f)"
              % (len(air), sum(util) / len(util), min(util), max(util)))
        # per-minute utilisation against loss
        t0 = ts(hb[0]["received_at_utc"])
        per = {}
        for a in air:
            m = int((ts(a["at_utc"]) - t0).total_seconds() // 60)
            u = (a.get("airtime") or {}).get("utilization_pct")
            if u is not None and m >= 0:
                per.setdefault(m, []).append(u)
        pu = [(st.mean(per[r["window"]]) if r["window"] in per else None)
              for r in w60]
        rho, n = spearman([r["lost_packets"] for r in w60], pu)
        print("  opal utilization vs loss, per minute: rho %s  n=%d"
              % ("-" if rho is None else "%+.3f" % rho, n))
    else:
        print("  opal: not sampled")

    out = {"w60": w60, "w10": w10}
    with open(os.path.join(scratch, "s3_windows.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
