#!/usr/bin/env python3
"""G8-S5 record: read the driver's files (cells.jsonl, runs/) once and write record_read.json; G8-S3 cell 1 is read
from G8-S3's record_read.json (its §3 figures) for the comparison. Read-only outside this directory.

Built from g8_s3_record_read.py (the per-second term table, the shim/frame-log alignment by packet count, the shim's
stream starts). Changed: the frame rows come from the driver's copy (runs/<cell>/frame_sizes_run<n>.jsonl), the
per-second drop max is added, the whole-stream tail drop beside the window's, the encoder command check (A's masked
argv with encoder_rc.apply_to(.., "tight", 5000) applied against B's), and the audio / encoder-CPU columns.
"""
import importlib.util
import json
import statistics as stx
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
S3 = HERE.parent / "g8_s3_2026-10-17"
RTP_HDR = 12
CAP = {"cap-6000": 6000}
spec = importlib.util.spec_from_file_location("encoder_rc", REPO / "companion/encoder_rc.py")
ERC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ERC)


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))] if xs else None


def r(x, n=1):
    return None if x is None else round(x, n)


def jl(p):
    out = []
    try:
        for l in open(p):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def align(shim, fr):
    if not fr or not shim:
        return None, None
    fpk = {d["t"]: d.get("packets") or 0 for d in fr}
    t_first = min(fpk)
    best = None
    for lag in range(-5, 6):
        diffs = []
        for x in shim:
            t = t_first + int(round(x["t_s"])) - 1 + lag
            if t in fpk and fpk[t]:
                diffs.append(abs((x.get("packets_in") or 0) / fpk[t] - 1.2))
        if len(diffs) > 30:
            sc = stx.median(diffs)
            if best is None or sc < best[1]:
                best = (lag, sc)
    return (t_first - 1 + best[0], best[1]) if best else (None, None)


def shim_segments(rows):
    segs, cur, last = [], [], None
    for x in rows:
        t = x.get("t_s") or 0
        if last is not None and t < last:
            segs.append(cur)
            cur = []
        cur.append(x)
        last = t
    segs.append(cur)
    return segs


def wire(cell, attempt, span_s=None):
    """Over the window, or its first span_s seconds (the paired split at cell A's first client pause)."""
    s = json.loads((HERE / cell["run_dir"] / "summary.json").read_text())
    w0, w1 = ts(s["window"]["from"]), ts(s["window"]["to"])
    if span_s is not None:
        w1 = min(w1, w0 + span_s)
    cdir = HERE / "runs" / cell["cell"]
    shim_all = jl(cdir / f"impairment_run{attempt}.jsonl")
    segs = shim_segments(shim_all)
    fr_all = sorted(jl(cdir / f"frame_sizes_run{attempt}.jsonl"), key=lambda d: d["t"])
    runs, cur = [], []
    for d in fr_all:
        if cur and d["t"] - cur[-1]["t"] > 60:
            runs.append(cur)
            cur = []
        cur.append(d)
    runs.append(cur)
    fr = next((x for x in runs if x and x[0]["t"] <= w0 <= x[-1]["t"]), [])
    # the shim segment of the session that holds the window: the last segment (one stream start expected)
    shim = segs[-1] if segs else []
    base, sc = align(shim, [d for d in fr if d["t"] <= int(w0)])
    fmap = {d["t"]: d for d in fr}
    secs = []
    for x in shim:
        t = base + int(round(x["t_s"])) if base is not None else None
        if t is None or not (w0 <= t < w1) or t not in fmap:
            continue
        f = fmap[t]
        dpk, pay = f.get("packets") or 0, f.get("payload_bytes") or 0
        pk, by = x.get("packets_in") or 0, x.get("bytes_in") or 0
        par_pk, par_by = pk - dpk, by - pay - RTP_HDR * dpk
        secs.append({"t": t, "frames": f.get("frames"), "payload_kbps": pay * 8 / 1000, "rtp_hdr_kbps": RTP_HDR * dpk * 8 / 1000,
                     "data_packets": dpk, "shim_packets": pk, "parity_packets": par_pk, "parity_kbps": par_by * 8 / 1000,
                     "shim_in_kbps": by * 8 / 1000, "shim_out_kbps": (x.get("bytes_out") or 0) * 8 / 1000,
                     "dropped_queue": x.get("dropped_queue") or 0, "max_frame_bytes": f.get("max_bytes"),
                     "mean_frame_packets": f.get("mean_packets"), "frames_over_cap": f.get("frames_over_cap") or 0})
    if not secs:
        return {"window_s": 0, "align": [base, sc]}
    m = lambda key: stx.mean([q[key] for q in secs if q[key] is not None])
    pay = [q["payload_kbps"] for q in secs]
    inn = [q["shim_in_kbps"] for q in secs]
    capk = CAP[cell["profile"]]
    tot_in, tot_drop = sum(q["shim_packets"] for q in secs), sum(q["dropped_queue"] for q in secs)
    over = [q for q in secs if q["shim_in_kbps"] > capk]
    frames = sum(q["frames"] or 0 for q in secs)
    psd = [q["dropped_queue"] / q["shim_packets"] for q in secs if q["shim_packets"]]
    whole_in = sum(x.get("packets_in") or 0 for x in shim_all)
    whole_drop = sum(x.get("dropped_queue") or 0 for x in shim_all)
    mfb = [q["max_frame_bytes"] for q in secs if q["max_frame_bytes"] is not None]
    return {"window_s": len(secs), "align_lag_score": r(sc, 3), "shim_stream_starts": len(segs),
            "payload_kbps": {"mean": r(m("payload_kbps")), "median": r(stx.median(pay)), "p95": r(pct(pay, 95)), "max": r(max(pay)),
                             "share_seconds_over_5000": r(sum(1 for v in pay if v > 5000) / len(pay), 3)},
            "rtp_hdr_kbps_mean": r(m("rtp_hdr_kbps")), "parity_kbps_mean": r(m("parity_kbps")),
            "parity_per_data_packet": r(sum(q["parity_packets"] for q in secs) / max(1, sum(q["data_packets"] for q in secs)), 4),
            "parity_per_frame": r(sum(q["parity_packets"] for q in secs) / max(1, frames), 3),
            "frames_per_s": r(frames / len(secs), 2), "mean_frame_packets": r(m("mean_frame_packets"), 2),
            "max_frame_bytes": {"median": r(stx.median(mfb)), "p95": pct(mfb, 95), "max": max(mfb)},
            "frames_over_cap_total": sum(q["frames_over_cap"] for q in secs),
            "shim_in_kbps": {"mean": r(stx.mean(inn)), "median": r(stx.median(inn)), "p95": r(pct(inn, 95)), "max": r(max(inn)),
                             "share_seconds_over_cap": r(len(over) / len(secs), 3)},
            "sum_of_terms_kbps": r(m("payload_kbps") + m("rtp_hdr_kbps") + m("parity_kbps")),
            "shim_out_kbps_mean": r(m("shim_out_kbps")), "shim_out_kbps_max": r(max(q["shim_out_kbps"] for q in secs)),
            "drop_frac_window": r(tot_drop / tot_in, 4) if tot_in else None,
            "drop_frac_whole_stream": r(whole_drop / whole_in, 4) if whole_in else None,
            "drop_frac_in_seconds_over_cap": r(sum(q["dropped_queue"] for q in over) / max(1, sum(q["shim_packets"] for q in over)), 4),
            "drop_frac_in_seconds_at_or_under_cap": r(sum(q["dropped_queue"] for q in secs if q not in over) /
                                                      max(1, sum(q["shim_packets"] for q in secs if q not in over)), 4),
            "share_of_drops_in_seconds_over_cap": r(sum(q["dropped_queue"] for q in over) / max(1, tot_drop), 3),
            "per_second_drop_frac": {"median": r(stx.median(psd), 4), "p95": r(pct(psd, 95), 4), "max": r(max(psd), 4)}}


def cmd_check(cells):
    """A's masked argv (flag absent) and B's (tight): A has no -rc_mode and -maxrate = -bufsize = -b:v; tight applied
    to A at A's own -b:v target equals B, byte for byte."""
    first = {}
    for c in cells:
        rows = jl(HERE / "runs" / c["cell"] / f"encoder_cmd_run{c.get('attempt', 1)}.jsonl")
        first[c["arm"]] = rows
    out = {arm: {"reads": len(rows), "distinct_masked_sha256": sorted({x["masked_sha256"] for x in rows}),
                 "rate_options": sorted({f"-b:v {x['b_v']} -maxrate {x['maxrate']} -bufsize {x['bufsize']} -rc_mode {x['rc_mode']}" for x in rows})}
           for arm, rows in first.items()}
    a, b = first.get("control") or [], first.get("tight") or []
    if a and b:
        av = a[0]["masked_argv"]
        t = int(str(a[0]["b_v"]).rstrip("k"))
        applied = ERC.apply_to(av, "tight", t)
        out["control_is_today"] = all(x["rc_mode"] is None and x["maxrate"] == x["bufsize"] == x["b_v"] for x in a)
        out["tight_applied_to_control_equals_tight"] = all(applied == x["masked_argv"] for x in b)
        out["tight_options"] = {"-rc_mode": b[0]["rc_mode"], "-maxrate": b[0]["maxrate"], "-bufsize": b[0]["bufsize"]}
        out["argv_diff_positions"] = [i for i, (p, q) in enumerate(zip(av, b[0]["masked_argv"])) if p != q] + \
            ([f"len {len(av)} vs {len(b[0]['masked_argv'])}"] if len(av) != len(b[0]["masked_argv"]) else [])
    return out


def main():
    cells = [json.loads(l) for l in open(HERE / "cells.jsonl")]
    last = {}
    for c in cells:
        last[c["cell"]] = c          # a repeated attempt replaces the first
    out = {"cells": {}, "encoder_cmd": cmd_check(list(last.values()))}
    for k, c in last.items():
        rd = HERE / c["run_dir"] if c.get("run_dir") else None
        s = json.loads((rd / "summary.json").read_text()) if rd and (rd / "summary.json").exists() else {}
        rec = {x: c.get(x) for x in ("n", "arm", "outcome", "validity", "profile_applied", "suite_attempts", "playing_attempt",
                                     "s_to_playing", "start_rung_first_row", "start_rung_kbps", "start_rung_source",
                                     "wire_bitrate_kbps_seen", "encoder_bv_seen", "encoder_rc_seen", "rung_path", "transitions",
                                     "flags_at_stream", "environ_at_stream_count", "flags_under_load", "environ_under_load_count",
                                     "shim_live_under_load", "loss_per_min", "rendered_fps", "resyncs", "stale_per_min",
                                     "spikes20_per_min", "client_pauses", "pauses", "fec_recovered", "fec_unrecoverable", "wan_class",
                                     "wan_windows", "retroarch_fps", "capture_fps", "dupdrop_per_min", "host_gates", "host_gates_met",
                                     "host_cpu", "companion_cpu", "encoder_cpu", "max_output_gap_ms", "audio_underruns",
                                     "audio_underruns_heartbeat", "audio_lost_packets", "spikes50", "spikes80", "shim",
                                     "flags_absent_after", "final_flags_absent", "failed_attempts", "window", "report_fields", "frame_rows")}
        lad = jl(HERE / "runs" / k / f"ladder_log_run{c.get('attempt', 1)}.jsonl")
        ev, states = {}, {}
        for x in lad:
            key = f"{x.get('event')}:{x.get('reason') or x.get('rule') or ''}:{x.get('class') or x.get('ladder_result') or ''}"
            ev[key] = ev.get(key, 0) + 1
            if x.get("event") == "sample":
                states[x.get("state")] = states.get(x.get("state"), 0) + 1
        rec["ladder_events"], rec["ladder_sample_states"] = ev, states
        rec["recovery_rows"] = jl(rd / "recovery.jsonl") if rd and (rd / "recovery.jsonl").exists() else None
        rec["summary_key_heartbeat"] = (s.get("key") or {}).get("heartbeat")
        if c.get("outcome") == "playing":
            rec["wire"] = wire(c, c.get("attempt", 1))
        out["cells"][k] = rec
    # the paired split: every playing cell over the first N s of its window, N = the earliest first client pause
    # (seconds into the window) of any cell; G8-S3 §3 split its cell 2 the same way
    firsts = []
    for k, c in last.items():
        s = json.loads((HERE / c["run_dir"] / "summary.json").read_text()) if c.get("run_dir") else {}
        cp = ((c.get("pauses") or {}).get("client_pauses") or [])
        if cp and s.get("window"):
            firsts.append(ts(cp[0]["at_utc"]) - ts(s["window"]["from"]))
    out["split_s"] = r(min(firsts), 1) if firsts else None
    if firsts:
        for k, c in last.items():
            if c.get("outcome") == "playing":
                out["cells"][k]["wire_first_split_s"] = wire(c, c.get("attempt", 1), min(firsts))
    g = json.loads((S3 / "record_read.json").read_text())["cells"]["01_cap-6000_floor_off"]
    out["g8_s3_cell1"] = {"wire": g.get("wire"), **{x: g.get(x) for x in ("loss_per_min", "rendered_fps", "resyncs", "stale_per_min",
                                                                         "fec_recovered", "fec_unrecoverable", "wan_class", "wan_windows",
                                                                         "host_cpu", "companion_cpu", "client_pauses")},
                          "max_output_gap_ms": (g.get("report_fields") or {}).get("max_output_gap_ms"),
                          "audio_underruns": (g.get("report_fields") or {}).get("audio.underruns")}
    (HERE / "record_read.json").write_text(json.dumps(out, indent=1, default=str))
    print("encoder_cmd", json.dumps(out["encoder_cmd"]))
    for k, v in out["cells"].items():
        print(k, json.dumps({x: v.get(x) for x in ("outcome", "validity", "rung_path", "rendered_fps", "loss_per_min", "encoder_cpu",
                                                  "audio_underruns", "max_output_gap_ms", "ladder_sample_states")}, default=str))
        if "wire" in v:
            print("  wire", json.dumps(v["wire"]))
        if "wire_first_split_s" in v:
            print("  wire_first", out["split_s"], json.dumps(v["wire_first_split_s"]))
    print("g8_s3_cell1 wire", json.dumps(out["g8_s3_cell1"]["wire"]))


if __name__ == "__main__":
    main()
