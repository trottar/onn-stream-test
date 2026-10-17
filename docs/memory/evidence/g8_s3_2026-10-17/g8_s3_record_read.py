#!/usr/bin/env python3
"""G8-S3 record: read the driver's files (cells.jsonl, runs/) once, plus three read-only logs for the wire-rate
accounting, and write record_read.json. Read-only; nothing outside this directory is written.

Logs read (read-only):
  - logs/games/native_frame_sizes.jsonl -- the FEC relay's per-second frame log: frames, RTP data packets and the
    H.264 RTP payload bytes per second (no RTP header, no parity), the largest frame per second.
  - logs/games/native_video_alpha.log -- the encoder's own log: per session the output rate in its argv banner, the
    progress records (cumulative size / time / bitrate), the muxing overhead, and the C3-F1 recovery-restart lines.
    Only counts and numbers are taken; nothing of the text is copied.
  - the run's impairment_run1.jsonl (the shim's per-second lines, copied by the driver).
The wire terms (code): the shim sees each RTP data datagram (12-B RTP header + payload) and each XOR parity
datagram (23-B FEC header, `FEC_HEADER` in native_fec_relay.py, + the group's largest payload); a group is up to 8
data packets and closes at each frame's end. Audio is not on the shim (the shim is built only inside
NativeVideoFecRelay).
"""
import json
import re
import statistics as stx
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
S1 = HERE.parent / "g8_s1_2026-10-16"
FRAMES = REPO / "logs/games/native_frame_sizes.jsonl"
ENCLOG = REPO / "logs/games/native_video_alpha.log"
RTP_HDR, FEC_HDR, MAX_PAYLOAD = 12, 23, 1188
CAP = {"cap-6000": 6000, "cap-4500": 4500}


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))] if xs else None


def r(x, n=1):
    return None if x is None else round(x, n)


def cells():
    return [json.loads(l) for l in open(HERE / "cells.jsonl")]


def frame_rows(t0, t1):
    out = []
    with open(FRAMES) as fh:
        for l in fh:
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if t0 <= d.get("t", 0) <= t1:
                out.append(d)
    return out


def enc_sessions():
    """The encoder log's backend sessions: per session the output kb/s of each encoder start, the restarts, the last
    progress record's cumulative bitrate per encoder start, the muxing overhead per encoder start."""
    txt = open(ENCLOG, "rb").read().decode(errors="replace").replace("\r", "\n").split("\n")
    starts = [i for i, l in enumerate(txt) if "Starting PrivyHub Linux native-video backend" in l]
    P = re.compile(r"frame=\s*(\d+).*?L?size=\s*(\d+)KiB\s+time=(\d+):(\d+):([\d.]+)\s+bitrate=\s*([\d.]+)kbits/s")
    out = []
    for s, e in zip(starts, starts[1:] + [len(txt)]):
        seg = txt[s:e]
        encs, cur = [], None
        for l in seg:
            m = re.search(r"h264 \(High\).*?(\d+) kb/s, 60 fps", l)
            if m:
                cur = {"out_kbps": int(m.group(1)), "progress": []}
                encs.append(cur)
                continue
            m = P.search(l)
            if m and cur is not None:
                cur["progress"].append((int(m.group(1)), int(m.group(2)),
                                        int(m.group(3)) * 3600 + int(m.group(4)) * 60 + float(m.group(5)), float(m.group(6))))
            m = re.search(r"video:(\d+)KiB.*muxing overhead: ([\d.]+)%", l)
            if m and cur is not None:
                cur["video_kib"], cur["mux_pct"] = int(m.group(1)), float(m.group(2))
        out.append({"line": s, "encoder_starts": encs,
                    "recovery_restarts": sum(1 for l in seg if "C3-F1 Linux recovery restart" in l and "cycle begin" in l)})
    return out


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


def align(shim, fr):
    """The shim's seconds against the frame log's (both per second, different clocks): the lag that best matches
    shim packets_in to the frame log's data packets x (1 + parity), searched around the session's first second."""
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


def wire(cell, upto_first_pause=False):
    """Term by term over the window, per second (only seconds present in both logs); with upto_first_pause, only the
    window's seconds before its first client pause."""
    s = json.loads((HERE / cell["run_dir"] / "summary.json").read_text())
    w0, w1 = ts(s["window"]["from"]), ts(s["window"]["to"])
    cp = [ts(x["at_utc"]) for x in ((cell.get("pauses") or {}).get("client_pauses") or []) if w0 <= ts(x["at_utc"]) < w1]
    if upto_first_pause:
        if not cp:
            return None
        w1 = min(cp)
    shim = [x for x in map(json.loads, open(HERE / "runs" / cell["cell"] / "impairment_run1.jsonl"))]
    fr = sorted(frame_rows(int(w0) - 900, int(w1) + 120), key=lambda d: d["t"])
    # the session's frame rows: the contiguous run (no gap > 60 s) that contains the window's start
    runs, cur = [], []
    for d in fr:
        if cur and d["t"] - cur[-1]["t"] > 60:
            runs.append(cur)
            cur = []
        cur.append(d)
    runs.append(cur)
    fr = next((x for x in runs if x and x[0]["t"] <= w0 <= x[-1]["t"]), [])
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
        par_pk = pk - dpk
        par_by = by - pay - RTP_HDR * dpk
        secs.append({"t": t, "frames": f.get("frames"), "payload_kbps": pay * 8 / 1000, "rtp_hdr_kbps": RTP_HDR * dpk * 8 / 1000,
                     "data_packets": dpk, "shim_packets": pk, "parity_packets": par_pk, "parity_kbps": par_by * 8 / 1000,
                     "parity_bytes_per_packet": par_by / par_pk if par_pk > 0 else None, "shim_in_kbps": by * 8 / 1000,
                     "shim_out_kbps": (x.get("bytes_out") or 0) * 8 / 1000, "dropped_queue": x.get("dropped_queue") or 0,
                     "max_frame_bytes": f.get("max_bytes"), "mean_frame_bytes": f.get("mean_bytes"),
                     "max_frame_packets": f.get("max_packets"), "mean_frame_packets": f.get("mean_packets")})
    m = lambda key: stx.mean([q[key] for q in secs if q[key] is not None])
    pay = [q["payload_kbps"] for q in secs]
    inn = [q["shim_in_kbps"] for q in secs]
    capk = CAP[cell["profile"]]
    tot_in = sum(q["shim_packets"] for q in secs)
    tot_drop = sum(q["dropped_queue"] for q in secs)
    over = [q for q in secs if q["shim_in_kbps"] > capk]
    frames = sum(q["frames"] or 0 for q in secs)
    groups_min = sum(-(-int(round((q["mean_frame_packets"] or 0) * (q["frames"] or 0))) // 8) for q in secs)  # a floor only
    return {"window_s": len(secs), "align_lag_score": r(sc, 3),
            "payload_kbps": {"mean": r(m("payload_kbps")), "median": r(stx.median(pay)), "p95": r(pct(pay, 95)),
                             "max": r(max(pay)), "share_seconds_over_5000": r(sum(1 for v in pay if v > 5000) / len(pay), 3)},
            "rtp_hdr_kbps_mean": r(m("rtp_hdr_kbps")), "parity_kbps_mean": r(m("parity_kbps")),
            "parity_packets_per_s": r(m("parity_packets")), "data_packets_per_s": r(m("data_packets")),
            "parity_per_data_packet": r(sum(q["parity_packets"] for q in secs) / max(1, sum(q["data_packets"] for q in secs)), 4),
            "parity_bytes_per_packet": r(sum(q["parity_kbps"] for q in secs) * 125 / max(1, sum(q["parity_packets"] for q in secs)), 1),
            "parity_per_frame": r(sum(q["parity_packets"] for q in secs) / max(1, frames), 3),
            "frames_per_s": r(frames / len(secs), 2), "mean_frame_packets": r(m("mean_frame_packets"), 2),
            "max_frame_bytes": {"median": r(stx.median([q["max_frame_bytes"] for q in secs])), "max": max(q["max_frame_bytes"] for q in secs)},
            "mean_frame_bytes_mean": r(m("mean_frame_bytes")),
            "shim_in_kbps": {"mean": r(stx.mean(inn)), "median": r(stx.median(inn)), "p95": r(pct(inn, 95)), "max": r(max(inn)),
                             "share_seconds_over_cap": r(len(over) / len(secs), 3)},
            "sum_of_terms_kbps": r(m("payload_kbps") + m("rtp_hdr_kbps") + m("parity_kbps")),
            "shim_out_kbps_mean": r(m("shim_out_kbps")),
            "drop_frac_window": r(tot_drop / tot_in, 4) if tot_in else None,
            "drop_frac_in_seconds_over_cap": r(sum(q["dropped_queue"] for q in over) / max(1, sum(q["shim_packets"] for q in over)), 4),
            "drop_frac_in_seconds_at_or_under_cap": r(sum(q["dropped_queue"] for q in secs if q not in over) /
                                                      max(1, sum(q["shim_packets"] for q in secs if q not in over)), 4),
            "share_of_drops_in_seconds_over_cap": r(sum(q["dropped_queue"] for q in over) / max(1, tot_drop), 3),
            "per_second_drop_frac": {"median": r(stx.median([q["dropped_queue"] / q["shim_packets"] for q in secs if q["shim_packets"]]), 4),
                                     "p95": r(pct([q["dropped_queue"] / q["shim_packets"] for q in secs if q["shim_packets"]], 95), 4)}}


def shim_starts(cell):
    rows = [json.loads(l) for l in open(HERE / "runs" / cell["cell"] / "impairment_run1.jsonl")]
    out = []
    for sg in shim_segments(rows):
        st = [x for x in sg if (x.get("t_s") or 0) > 2.5]
        pin = sum(x.get("packets_in") or 0 for x in sg)
        ink = sorted((x.get("bytes_in") or 0) * 8 / 1000 for x in st)
        outk = [(x.get("bytes_out") or 0) * 8 / 1000 for x in st]
        out.append({"seconds": round(max(x.get("t_s") or 0 for x in sg), 1), "packets_in": pin,
                    "packets_out": sum(x.get("packets_out") or 0 for x in sg), "dropped_queue": sum(x.get("dropped_queue") or 0 for x in sg),
                    "drop_frac": round(sum(x.get("dropped_queue") or 0 for x in sg) / pin, 4) if pin else None,
                    "steady_in_kbps": [round(ink[0], 1), round(ink[len(ink) // 2], 1), round(ink[-1], 1)] if ink else None,
                    "steady_out_kbps_max": round(max(outk), 1) if outk else None,
                    "steady_drop_frac": round(sum(x.get("dropped_queue") or 0 for x in st) / max(1, sum(x.get("packets_in") or 0 for x in st)), 4),
                    "queue_max": max(x.get("queue_max") or 0 for x in sg)})
    return out


def main():
    cs = cells()
    s1 = {json.loads(l)["cell"]: json.loads(l) for l in open(S1 / "cells.jsonl")}
    enc = enc_sessions()
    out = {"cells": {}, "g8_s1": {}, "encoder_log_sessions_at_5000": []}
    # the encoder log's sessions with a 5000 output after G8-S3's launch: the last sessions of the log
    at5000 = [e for e in enc if e["encoder_starts"] and e["encoder_starts"][0]["out_kbps"] == 5000]
    for e in at5000[-8:]:
        out["encoder_log_sessions_at_5000"].append({
            "encoder_starts": len(e["encoder_starts"]), "recovery_restarts": e["recovery_restarts"],
            "out_kbps": sorted({x["out_kbps"] for x in e["encoder_starts"]}),
            "per_start": [{"frames": x["progress"][-1][0] if x["progress"] else None, "s": x["progress"][-1][2] if x["progress"] else None,
                           "cum_bitrate_kbps": x["progress"][-1][3] if x["progress"] else None, "mux_pct": x.get("mux_pct"),
                           "video_kib": x.get("video_kib")} for x in e["encoder_starts"]]})
    for c in cs:
        k = c["cell"]
        rd = HERE / c["run_dir"]
        s = json.loads((rd / "summary.json").read_text())
        rec = {x: c.get(x) for x in ("n", "profile", "arm", "outcome", "validity", "profile_applied", "suite_attempts", "playing_attempt",
                                     "s_to_playing", "start_rung_first_row", "wire_bitrate_kbps_seen", "encoder_bv_seen", "rung_path",
                                     "transitions", "rules_by_id", "flags_at_stream", "flags_under_load", "environ_at_stream_count",
                                     "loss_per_min", "rendered_fps", "resyncs", "stale_per_min", "spikes20_per_min", "client_pauses", "pauses",
                                     "fec_recovered", "fec_unrecoverable", "wan_class", "wan_windows", "retroarch_fps", "capture_fps",
                                     "dupdrop_per_min", "host_gates", "host_gates_met", "host_cpu", "companion_cpu", "shim",
                                     "flags_absent_after", "final_flags_absent", "failed_attempts", "journal", "window", "report_fields")}
        lad = [json.loads(l) for l in open(HERE / "runs" / k / "ladder_log_run1.jsonl")]
        ev = {}
        for x in lad:
            key = f"{x.get('event')}:{x.get('reason') or x.get('rule') or ''}:{x.get('class') or x.get('ladder_result') or ''}"
            ev[key] = ev.get(key, 0) + 1
        rec["ladder_events"] = ev
        rec["ladder_sample_states"] = {}
        for x in lad:
            if x.get("event") == "sample":
                rec["ladder_sample_states"][x.get("state")] = rec["ladder_sample_states"].get(x.get("state"), 0) + 1
        rec["suggestions"] = {}
        for x in lad:
            if x.get("event") == "wan_suggestion":
                kk = f"{x.get('rule')} {x.get('suggestion')} -> {x.get('ladder_result')}"
                rec["suggestions"][kk] = rec["suggestions"].get(kk, 0) + 1
        rec["recovery_rows"] = [json.loads(l) for l in open(rd / "recovery.jsonl")] if (rd / "recovery.jsonl").exists() else None
        gp = [json.loads(l) for l in open(rd / "gaps.jsonl")] if (rd / "gaps.jsonl").exists() else []
        rec["gaps"] = {"rows": len(gp), "max_ms": max((g.get("gap_ms") or g.get("ms") or 0) for g in gp) if gp else None}
        rec["shim_starts"] = shim_starts(c)
        if c["outcome"] == "playing":
            rec["wire"] = wire(c)
            rec["wire_before_first_client_pause"] = wire(c, True)
        rec["summary_key_heartbeat"] = (s.get("key") or {}).get("heartbeat")
        out["cells"][k] = rec
        g = s1.get(c["g8_s1"]) or {}
        out["g8_s1"][c["g8_s1"]] = {x: g.get(x) for x in ("validity", "status", "shim", "wan_class", "wan_windows", "rendered_fps", "loss_per_min")}
    (HERE / "record_read.json").write_text(json.dumps(out, indent=1, default=str))
    for k, v in out["cells"].items():
        print(k, json.dumps({x: v.get(x) for x in ("outcome", "rung_path", "ladder_events", "suggestions", "recovery_rows", "gaps")}, default=str)[:1500])
        print("  shim_starts", json.dumps(v["shim_starts"])[:900])
        if "wire" in v:
            print("  wire", json.dumps(v["wire"]))
            print("  wire_pre", json.dumps(v["wire_before_first_client_pause"]))
    print("enc", json.dumps(out["encoder_log_sessions_at_5000"])[:2500])


if __name__ == "__main__":
    main()
