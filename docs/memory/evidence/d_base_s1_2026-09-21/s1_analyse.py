"""D-BASE-S1 analysis: time-dependence over four 30-minute sessions."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    rk = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            rk[order[k]] = avg
        i = j + 1
    return rk


def spearman(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 3:
        return float("nan")
    ra, rb = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    n = len(pairs)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((x - mb) ** 2 for x in rb) ** 0.5
    return num / (da * db) if da and db else float("nan")


def jload(path):
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def heartbeat_series(path):
    """Per-minute rendered fps and stall counts from the 2 s heartbeat."""
    hb = [h["heartbeat"] if "heartbeat" in h else h for h in jload(path)]
    hb = [h for h in hb if isinstance(h, dict) and "elapsed_ms" in h]
    hb.sort(key=lambda h: h["elapsed_ms"])
    buckets = {}
    for h in hb:
        m = int(h["elapsed_ms"] // 60000)
        buckets.setdefault(m, []).append(h)
    rows = []
    for m in sorted(buckets):
        b = buckets[m]
        if len(b) < 2:
            continue
        d_frames = b[-1]["rendered_frames"] - b[0]["rendered_frames"]
        d_ms = b[-1]["elapsed_ms"] - b[0]["elapsed_ms"]
        ages = [h.get("last_output_age_ms", -1) for h in b]
        rows.append({
            "minute": m,
            "ticks": len(b),
            "fps": round(d_frames / (d_ms / 1000.0), 3) if d_ms > 0 else None,
            "max_age_ms": max(ages),
            "stalls_gt_120ms": len([a for a in ages if a > 120]),
            "stalls_gt_1000ms": len([a for a in ages if a > 1000]),
            "rx_packets": b[-1].get("rx_packets"),
        })
    return rows


def sample_series(path):
    s = jload(path)
    s = [x for x in s if "at_utc" in x]
    rows = []
    prev = None
    t0 = s[0]["monotonic"] if s else 0
    for x in s:
        row = {
            "minute": round((x["monotonic"] - t0) / 60.0, 2),
            "cpu_temp_c": x.get("cpu_temp_c"),
            "gpu_temp_c": x.get("gpu_temp_c"),
            "gpu_power_w": x.get("gpu_power_w"),
            "load1": x["loadavg"][0] if x.get("loadavg") else None,
            "enc_rss_kb": (x["procs"].get("encoder") or {}).get("rss_kb"),
            "comp_rss_kb": (x["procs"].get("companion") or {}).get("rss_kb"),
            "comp_threads": (x["procs"].get("companion") or {}).get("threads"),
            "ra_rss_kb": (x["procs"].get("retroarch") or {}).get("rss_kb"),
            "hb_log_bytes": x["log_bytes"].get("heartbeat"),
            "rec_log_bytes": x["log_bytes"].get("recovery"),
            "archive_bytes": x["log_bytes"].get("archive_total"),
            "archive_files": x["log_bytes"].get("archive_files"),
            "recovery_state": (x.get("recovery_block") or {}).get("state"),
            "restarts": (x.get("recovery_block") or {}).get("restarts"),
            "fec_groups": (x.get("fec") or {}).get("groups"),
            "fec_send_errors": (x.get("fec") or {}).get("send_errors"),
            "fec_rtp_packets": (x.get("fec") or {}).get("rtp_packets"),
        }
        enc = x["procs"].get("encoder") or {}
        if prev is not None and enc.get("cpu_jiffies") is not None:
            penc = prev["procs"].get("encoder") or {}
            if penc.get("cpu_jiffies") is not None and penc.get("pid") == enc.get("pid"):
                dt = x["monotonic"] - prev["monotonic"]
                dj = enc["cpu_jiffies"] - penc["cpu_jiffies"]
                row["enc_cpu_pct"] = round(dj / 100.0 / dt * 100.0, 1) if dt > 0 else None
        comp = x["procs"].get("companion") or {}
        if prev is not None and comp.get("cpu_jiffies") is not None:
            pcomp = prev["procs"].get("companion") or {}
            if pcomp.get("cpu_jiffies") is not None and pcomp.get("pid") == comp.get("pid"):
                dt = x["monotonic"] - prev["monotonic"]
                dj = comp["cpu_jiffies"] - pcomp["cpu_jiffies"]
                row["comp_cpu_pct"] = round(dj / 100.0 / dt * 100.0, 1) if dt > 0 else None
        rows.append(row)
        prev = x
    return rows


def report_summary(path):
    r = json.load(open(path))["report"]
    v, a, d = r["video"], r["audio"], r["decoder"]
    secs = r["duration_ms"] / 1000.0
    mins = secs / 60.0
    return {
        "duration_ms": r["duration_ms"],
        "rendered_fps": round(d["rendered_frames"] / secs, 3),
        "received_au_fps": round(v["frames"] / secs, 3),
        "max_output_gap_ms": d.get("max_output_gap_ms"),
        "output_age_at_end_ms": r.get("output_age_at_end_ms"),
        "terminal_slow_event": r.get("terminal_slow_event"),
        "spike_20_ms_per_min": round((d.get("spike_20_ms") or 0) / mins, 1),
        "stale_drops_per_min": round((d.get("stale_output_drops") or 0) / mins, 1),
        "lost_packets": v["lost_packets"],
        "lost_per_min": round(v["lost_packets"] / mins, 1),
        "lost_packets_in_resyncs": v.get("lost_packets_in_resyncs"),
        "forward_gap_events": v.get("forward_gap_events"),
        "max_forward_gap_packets": v.get("max_forward_gap_packets"),
        "late_or_reordered_packets": v.get("late_or_reordered_packets"),
        "sequence_resyncs": v.get("sequence_resyncs"),
        "ssrc_changes": v.get("ssrc_changes"),
        "fec_recovered_packets": v.get("fec_recovered_packets"),
        "fec_unrecoverable_groups": v.get("fec_unrecoverable_groups"),
        "idr_aus_rejected": v.get("idr_aus_rejected_waiting_for_idr"),
        "non_idr_aus_dropped": v.get("non_idr_aus_dropped_waiting_for_idr"),
        "underruns": a.get("underruns"),
        "prolonged_starvation_events": a.get("prolonged_starvation_events"),
        "concealed_underruns": a.get("concealed_underruns"),
        "avg_queue_residence_ms": round(a.get("avg_queue_residence_ms") or 0, 2),
        "startup_wait_ms": a.get("startup_wait_ms"),
        "tick_series_rows": len(a.get("tick_series") or []),
        "discontinuities": r["stream_discontinuities"],
        "first_idr_rows": r["first_idr_after_discontinuity"],
        "slow_events_top_gap": r.get("slow_events_top_gap"),
    }


def main():
    idx = os.path.join(HERE, "s1_index.txt")
    sessions = []
    for line in open(idx):
        p = line.split()
        if len(p) == 3 and p[2] == "completed":
            sessions.append((p[0], p[1]))
        elif len(p) >= 2 and p[1] in ("NOREPORT", "FAILED_TO_OPEN"):
            print("!! session %s did not complete: %s" % (p[0], p[1]))

    all_disc = []
    for label, rep in sessions:
        out = os.path.join(HERE, label)
        print("\n===== %s (%s) =====" % (label, rep))
        summ = report_summary(os.path.join(out, rep))
        for k, v in summ.items():
            if k in ("discontinuities", "first_idr_rows", "slow_events_top_gap"):
                continue
            print("  %-28s %s" % (k, v))
        for d, i in zip(summ["discontinuities"], summ["first_idr_rows"]):
            all_disc.append((label, d, i))

        hb = heartbeat_series(os.path.join(out, "heartbeat_lines.jsonl"))
        if hb:
            mins = [h["minute"] for h in hb]
            print("  heartbeat minutes: %d" % len(hb))
            for key in ("fps", "max_age_ms", "stalls_gt_120ms", "stalls_gt_1000ms"):
                vals = [h[key] for h in hb]
                good = [v for v in vals if v is not None]
                if good:
                    print("    %-18s first=%s last=%s min=%s max=%s  Spearman vs minute %.3f"
                          % (key, good[0], good[-1], min(good), max(good),
                             spearman(vals, mins)))
            with open(os.path.join(out, "per_minute.csv"), "w", newline="\n") as fh:
                cols = ["minute", "ticks", "fps", "max_age_ms",
                        "stalls_gt_120ms", "stalls_gt_1000ms", "rx_packets"]
                fh.write(",".join(cols) + "\n")
                for h in hb:
                    fh.write(",".join(str(h[c]) for c in cols) + "\n")

        sm = sample_series(os.path.join(out, "samples.jsonl"))
        if sm:
            mins = [s["minute"] for s in sm]
            print("  host samples: %d" % len(sm))
            for key in ("cpu_temp_c", "gpu_temp_c", "gpu_power_w", "load1",
                        "enc_cpu_pct", "enc_rss_kb", "comp_rss_kb",
                        "comp_threads", "ra_rss_kb"):
                vals = [s.get(key) for s in sm]
                good = [v for v in vals if v is not None]
                if good:
                    print("    %-14s first=%s last=%s min=%s max=%s  Spearman %.3f"
                          % (key, good[0], good[-1], min(good), max(good),
                             spearman(vals, mins)))
            last = sm[-1]
            print("    logs: heartbeat=%s recovery=%s archive=%s (%s files)"
                  % (last["hb_log_bytes"], last["rec_log_bytes"],
                     last["archive_bytes"], last["archive_files"]))
            print("    fec groups=%s send_errors=%s rtp_packets=%s"
                  % (last["fec_groups"], last["fec_send_errors"],
                     last["fec_rtp_packets"]))
            states = sorted({s["recovery_state"] for s in sm if s["recovery_state"]})
            print("    recovery states seen: %s; restarts end=%s"
                  % (states, last["restarts"]))
            with open(os.path.join(out, "host_samples.csv"), "w", newline="\n") as fh:
                cols = ["minute", "cpu_temp_c", "gpu_temp_c", "gpu_power_w", "load1",
                        "enc_cpu_pct", "comp_cpu_pct", "enc_rss_kb", "comp_rss_kb",
                        "comp_threads", "ra_rss_kb", "hb_log_bytes", "rec_log_bytes",
                        "archive_bytes", "archive_files", "recovery_state", "restarts",
                        "fec_groups", "fec_send_errors", "fec_rtp_packets"]
                fh.write(",".join(cols) + "\n")
                for s in sm:
                    fh.write(",".join(str(s.get(c)) for c in cols) + "\n")

        rec = jload(os.path.join(out, "recovery_lines.jsonl"))
        evs = [r for r in rec if r.get("event") not in ("session_started", "session_ended")]
        print("  recovery events beyond start/end: %d" % len(evs))
        for r in evs:
            print("    ", r.get("at_utc"), r.get("event"),
                  {k: v for k, v in r.items()
                   if k not in ("schema", "at_utc", "event") and v is not None})

    print("\n===== discontinuities across the soak =====")
    print("session,elapsed_ms,type,jump_packets,resync_to_idr_ms,rejected_idr_aus,"
          "dropped_non_idr_aus,au_complete,au_fec_recovered,au_fec_unrecoverable_group")
    for label, d, i in all_disc:
        print("%s,%d,%s,%d,%d,%d,%d,%s,%s,%s"
              % (label, d["elapsed_ms"], d["type"], d["jump_packets"],
                 i["resync_to_idr_ms"], i["rejected_idr_aus"],
                 i["dropped_non_idr_aus"], i["au_complete"],
                 i["au_fec_recovered"], i["au_fec_unrecoverable_group"]))
    seq = [(l, d, i) for l, d, i in all_disc if d["type"] == "sequence_resync"]
    over = [(l, d, i) for l, d, i in seq if i["resync_to_idr_ms"] > 250]
    under = [(l, d, i) for l, d, i in seq if i["resync_to_idr_ms"] <= 250]
    print("\ntotal %d (sequence_resync %d, ssrc_change %d); over 250 ms: %d"
          % (len(all_disc), len(seq), len(all_disc) - len(seq), len(over)))
    if len(all_disc) < 6 or not over:
        print("C5a verdict: INDETERMINATE (%d discontinuities, %d over 250 ms)"
              % (len(all_disc), len(over)))
    elif all(i["rejected_idr_aus"] >= 1 for _, _, i in over) and \
            all(i["rejected_idr_aus"] == 0 for _, _, i in under):
        print("C5a verdict: CONFIRMED")
    elif any(i["rejected_idr_aus"] == 0 for _, _, i in over):
        print("C5a verdict: FALSIFIED (a resync over 250 ms rejected no IDR)")
    else:
        print("C5a verdict: MIXED")


if __name__ == "__main__":
    main()
