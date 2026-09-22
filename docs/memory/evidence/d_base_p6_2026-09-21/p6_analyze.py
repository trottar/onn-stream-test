#!/usr/bin/env python3
"""D-BASE-P6: frame-tail control, arm by arm.

Reads each arm's relay frame-size series (packets AND payload bytes), the
D-BASE-R5 heartbeat loss counters, the onn's socket samples and the
encoder's own progress line, and reports:

  * the per-frame size distribution per arm, in both units;
  * **loss conditional on frame-size bucket** -- see `bucket_loss()` for
    the attribution method, which is stated rather than assumed;
  * the per-minute loss series for the cross-arm comparison;
  * achieved encoder bitrate, from the relay's `rtp_bytes` and from the
    encoder log independently.

Counters (loss, forward gaps, socket drops) are differenced; instants
(max frame size, rx_queue) are maxed. The two are never mixed.

usage: p6_analyze.py <scratch_dir> <arm> [<arm> ...]
"""
import json
import math
import os
import re
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


def windows(scratch, arm, span_s):
    """One row per `span_s`, frame series and loss on one clock."""
    hb = load(os.path.join(scratch, "heartbeat_%s.jsonl" % arm))
    fr = load(os.path.join(scratch, "frames_%s.jsonl" % arm))
    sk = load(os.path.join(scratch, "socket_%s.jsonl" % arm))
    if not hb:
        return []
    hb.sort(key=lambda r: r["elapsed_ms"])
    t0 = ts(hb[0]["received_at_utc"])

    def b(t):
        return int((t - t0).total_seconds() // span_s)

    rows = {}

    def row(i):
        return rows.setdefault(i, {
            "arm": arm, "window": i, "lost_packets": 0,
            "forward_gap_events": 0, "rx_packets": 0, "hb": 0,
            "frames": 0, "frame_packets": 0, "frame_bytes": 0,
            "max_packets": 0, "max_bytes": 0, "frames_ge_40": 0,
            "frames_ge_80": 0, "frames_over_cap": 0, "frame_seconds": 0,
            "drops_delta": None, "rx_queue_peak": None, "sock_samples": 0,
        })

    for a, c in zip(hb, hb[1:]):
        r = row(b(ts(a["received_at_utc"])))
        r["lost_packets"] += max(0, c["lost_packets"] - a["lost_packets"])
        r["forward_gap_events"] += max(
            0, c["forward_gap_events"] - a["forward_gap_events"])
        r["rx_packets"] += max(0, c["rx_packets"] - a["rx_packets"])
        r["hb"] += 1

    for f in fr:
        i = b(ts(f["at_utc"]))
        if i < 0:
            continue
        r = row(i)
        r["frames"] += f.get("frames", 0)
        r["frame_packets"] += f.get("packets", 0)
        r["frame_bytes"] += f.get("payload_bytes", 0)
        r["max_packets"] = max(r["max_packets"], f.get("max_packets", 0))
        r["max_bytes"] = max(r["max_bytes"], f.get("max_bytes", 0))
        r["frames_ge_40"] += f.get("frames_ge_40", 0)
        r["frames_ge_80"] += f.get("frames_ge_80", 0)
        r["frames_over_cap"] += f.get("frames_over_cap", 0)
        r["frame_seconds"] += 1

    stream = [s for s in sk if s.get("sockets", {}).get("video_48100")]
    stream.sort(key=lambda s: s["seq"])
    grp = {}
    for s in stream:
        i = b(ts(s["at_utc"]))
        if i >= 0:
            grp.setdefault(i, []).append(s)
    for i, g in grp.items():
        r = row(i)
        r["drops_delta"] = max(
            0, g[-1]["sockets"]["video_48100"]["drops"]
            - g[0]["sockets"]["video_48100"]["drops"])
        r["rx_queue_peak"] = max(
            x["sockets"]["video_48100"]["rx_queue"] for x in g)
        r["sock_samples"] = len(g)

    out = [rows[i] for i in sorted(rows)]
    for r in out:
        if r["frames"]:
            r["mean_packets"] = round(r["frame_packets"] / r["frames"], 3)
            r["mean_bytes"] = int(r["frame_bytes"] / r["frames"])
    return [r for r in out
            if r["hb"] >= 2 and r["frame_seconds"] >= max(1, span_s // 2)]


def bucket_loss(rows):
    """Loss conditional on frame-size bucket.

    **Attribution method, stated because it is not exact.** The client
    reports loss per heartbeat, not per frame, so a lost packet cannot be
    tied to the frame it belonged to. Instead each 10 s window is assigned
    to the bucket of its LARGEST frame -- the window is "dominated by" that
    bucket -- and the loss of the window is attributed there. This measures
    "windows that contained a frame this big lost N", not "frames this big
    lost N", and it is the strongest statement the instruments support.
    """
    edges = [(0, 40, "< 40"), (40, 60, "40-59"), (60, 80, "60-79"),
             (80, 10 ** 9, ">= 80")]
    out = []
    for lo, hi, label in edges:
        sel = [r for r in rows if lo <= r["max_packets"] < hi]
        if not sel:
            out.append((label, 0, 0, None, 0))
            continue
        loss = sum(r["lost_packets"] for r in sel)
        frames = sum(r["frames"] for r in sel)
        out.append((label, len(sel), frames, loss,
                    round(loss / len(sel), 2)))
    return out


PROG = re.compile(
    r"frame=\s*(\d+) fps=[^q]*q=[^s]*size=\s*(\d+)KiB time=(\d+):(\d+):([\d.]+)")


def encoder_bitrate(path):
    """Mean achieved kbps from the encoder's own progress line."""
    if not os.path.exists(path):
        return None, None
    pts = [(int(m.group(2)), int(m.group(3)) * 3600 + int(m.group(4)) * 60
            + float(m.group(5)))
           for m in PROG.finditer(open(path, errors="replace").read())]
    if len(pts) < 10:
        return None, None
    (s0, t0), (s1, t1) = pts[0], pts[-1]
    if t1 <= t0:
        return None, None
    per_min = []
    for (a_s, a_t), (b_s, b_t) in zip(pts, pts[1:]):
        if b_t > a_t:
            per_min.append(8 * (b_s - a_s) / (b_t - a_t))
    return (round(8 * (s1 - s0) / (t1 - t0), 1),
            (round(min(per_min), 1), round(max(per_min), 1)) if per_min else None)


def arm_summary(scratch, arm):
    s = {}
    path = os.path.join(scratch, "status_%s.json" % arm)
    if os.path.exists(path):
        raw = json.load(open(path))
        fs = (raw.get("fec") or {}).get("frame_sizes") or {}
        s["frame_sizes"] = {k: v for k, v in fs.items()
                            if k not in ("buckets", "packet_histogram",
                                         "byte_histogram")}
        s["byte_histogram"] = fs.get("byte_histogram")
        s["packet_histogram"] = fs.get("packet_histogram")
        s["rtp_bytes"] = (raw.get("fec") or {}).get("rtp_bytes")
        s["send_errors"] = (raw.get("fec") or {}).get("send_errors")
        s["encoder_overrides"] = raw.get("encoder_overrides")
    rp = os.path.join(scratch, "report_%s.json" % arm)
    if os.path.exists(rp):
        r = json.load(open(rp))["report"]
        dur = r["duration_ms"] / 1000.0
        v, d, a = r["video"], r["decoder"], r["audio"]
        s["report"] = {
            "duration_s": round(dur, 1),
            "video_packets": v["packets"],
            "lost_packets": v["lost_packets"],
            "loss_pct": round(100 * v["lost_packets"] / v["packets"], 4),
            "loss_per_min": round(v["lost_packets"] / (dur / 60), 1),
            "forward_gap_events": v["forward_gap_events"],
            "max_forward_gap_packets": v["max_forward_gap_packets"],
            "sequence_resyncs": v["sequence_resyncs"],
            "audio_packets": a["packets"],
            "audio_lost": a["lost_packets"],
            "audio_loss_pct": round(100 * a["lost_packets"] / a["packets"], 4),
            "fps": round(d["rendered_frames"] / dur, 2),
            "spike_20_ms_per_min": round(d["spike_20_ms"] / (dur / 60), 1),
            "max_output_gap_ms": d["max_output_gap_ms"],
            "max_rx_to_decode_ms": d["max_rx_to_decode_ms"],
            "fec_unrecoverable_groups": v["fec_unrecoverable_groups"],
        }
    mean, rng = encoder_bitrate(os.path.join(scratch, "alpha_%s.log" % arm))
    s["encoder_kbps_mean"] = mean
    s["encoder_kbps_range"] = rng
    return s


def main():
    scratch, arms = sys.argv[1], sys.argv[2:]
    all_rows = {}
    print("=" * 74)
    for arm in arms:
        s = arm_summary(scratch, arm)
        fs = s.get("frame_sizes", {})
        rep = s.get("report", {})
        print("\n### ARM %s" % arm)
        ov = s.get("encoder_overrides") or {}
        print("  encoder: max_frame_size=%s bufsize_kbits=%s (default %s)"
              % (ov.get("max_frame_size_bytes"), ov.get("bufsize_kbits"),
                 ov.get("default_bufsize_kbits")))
        print("  frames %s  bytes/pkt %s" % (fs.get("frames"),
                                             fs.get("bytes_per_packet")))
        print("  packets  p50 %-4s p90 %-4s p99 %-4s max %-5s  >=40 %-6s >=80 %s"
              % (fs.get("p50_packets"), fs.get("p90_packets"),
                 fs.get("p99_packets"), fs.get("max_packets"),
                 fs.get("frames_ge_40"), fs.get("frames_ge_80")))
        print("  bytes    p50 %-6s p90 %-6s p99 %-6s max %-7s  over cap(%s) %s"
              % (fs.get("p50_bytes"), fs.get("p90_bytes"), fs.get("p99_bytes"),
                 fs.get("max_bytes"), fs.get("byte_cap"),
                 fs.get("frames_over_cap")))
        if rep:
            print("  loss %d (%.4f%%, %.1f/min)  fgap %d  maxgap %d pkt  resyncs %d"
                  % (rep["lost_packets"], rep["loss_pct"], rep["loss_per_min"],
                     rep["forward_gap_events"], rep["max_forward_gap_packets"],
                     rep["sequence_resyncs"]))
            print("  audio loss %d (%.4f%%)  fps %.2f  spike20/min %.1f  "
                  "max_output_gap %d ms  max_rx_to_decode %d ms"
                  % (rep["audio_lost"], rep["audio_loss_pct"], rep["fps"],
                     rep["spike_20_ms_per_min"], rep["max_output_gap_ms"],
                     rep["max_rx_to_decode_ms"]))
        print("  encoder %s kbps (per-0.5s %s)   relay rtp_bytes %s  send_errors %s"
              % (s.get("encoder_kbps_mean"), s.get("encoder_kbps_range"),
                 s.get("rtp_bytes"), s.get("send_errors")))

        w10 = windows(scratch, arm, 10)
        all_rows[arm] = {"w10": w10, "w60": windows(scratch, arm, 60),
                         "summary": s}
        if w10:
            print("  loss conditional on the window's largest frame "
                  "(10 s windows):")
            print("    %-8s %8s %9s %8s %10s"
                  % ("bucket", "windows", "frames", "loss", "loss/win"))
            for label, nwin, frames, loss, per in bucket_loss(w10):
                print("    %-8s %8d %9d %8s %10s"
                      % (label, nwin, frames, loss, per))
            drops = sum(r.get("drops_delta") or 0 for r in w10)
            print("  onn socket drops over the arm: %d" % drops)

    with open(os.path.join(scratch, "p6_arms.json"), "w") as fh:
        json.dump({a: {"summary": v["summary"],
                       "w60": v["w60"], "w10": v["w10"]}
                   for a, v in all_rows.items()}, fh, indent=1)

    print("\n" + "=" * 74)
    print("CROSS-ARM, per minute (the content-lock makes these comparable)")
    base = arms[0]
    bw = {r["window"]: r for r in all_rows[base]["w60"]}
    print("  %-5s %7s %7s %8s %9s %9s %8s" % (
        "arm", "loss", "vs A0", "fgap", "max_pkt", "max_byte", ">=80"))
    for arm in arms:
        rows = all_rows[arm]["w60"]
        if not rows:
            continue
        loss = sum(r["lost_packets"] for r in rows)
        ge80 = sum(r["frames_ge_80"] for r in rows)
        bl = sum(bw[r["window"]]["lost_packets"] for r in rows
                 if r["window"] in bw) or None
        ratio = ("%.2fx" % (loss / bl)) if bl else "-"
        print("  %-5s %7d %7s %8d %9d %9d %8d" % (
            arm, loss, ratio,
            sum(r["forward_gap_events"] for r in rows),
            max(r["max_packets"] for r in rows),
            max(r["max_bytes"] for r in rows), ge80))

    for arm in arms[1:]:
        a, b_ = all_rows[base]["w60"], all_rows[arm]["w60"]
        n = min(len(a), len(b_))
        if n < 5:
            continue
        va = [a[i]["lost_packets"] for i in range(n)]
        vb = [b_[i]["lost_packets"] for i in range(n)]
        print("  %s vs %s per-minute loss: pearson %s  spearman %s  n=%d"
              % (base, arm,
                 "-" if pearson(va, vb) is None else "%.3f" % pearson(va, vb),
                 "-" if spearman(va, vb)[0] is None else "%.3f" % spearman(va, vb)[0],
                 n))


if __name__ == "__main__":
    main()
