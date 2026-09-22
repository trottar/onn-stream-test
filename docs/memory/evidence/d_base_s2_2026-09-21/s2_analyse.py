"""D-BASE-S2 analysis: one 3-hour session, memory growth and stream drift."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
S1 = os.path.join(os.path.dirname(HERE), "d_base_s1_2026-09-21")
sys.path.insert(0, S1)
import s1_analyse as A  # noqa: E402  (rank/spearman/heartbeat_series reused)


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


def samples(path):
    s = [x for x in jload(path) if "at_utc" in x]
    t0 = s[0]["monotonic"] if s else 0
    rows = []
    prev = None
    for x in s:
        ra = x["procs"].get("retroarch") or {}
        co = x["procs"].get("companion") or {}
        en = x["procs"].get("encoder") or {}
        row = {
            "minute": round((x["monotonic"] - t0) / 60.0, 2),
            "cpu_temp_c": x.get("cpu_temp_c"),
            "gpu_temp_c": x.get("gpu_temp_c"),
            "gpu_power_w": x.get("gpu_power_w"),
            "load1": x["loadavg"][0] if x.get("loadavg") else None,
            "mem_avail_kb": (x.get("mem") or {}).get("MemAvailable"),
            "ra_rss_kb": ra.get("rss_kb"), "ra_anon_kb": ra.get("rss_anon_kb"),
            "ra_file_kb": ra.get("rss_file_kb"), "ra_shmem_kb": ra.get("rss_shmem_kb"),
            "ra_swap_kb": ra.get("swap_kb"), "ra_vsize_kb": ra.get("vsize_kb"),
            "comp_rss_kb": co.get("rss_kb"), "comp_anon_kb": co.get("rss_anon_kb"),
            "comp_threads": co.get("threads"),
            "enc_rss_kb": en.get("rss_kb"), "enc_anon_kb": en.get("rss_anon_kb"),
            "hb_log_bytes": x["log_bytes"].get("heartbeat"),
            "rec_log_bytes": x["log_bytes"].get("recovery"),
            "archive_files": x["log_bytes"].get("archive_files"),
            "recovery_state": (x.get("recovery_block") or {}).get("state"),
            "restarts": (x.get("recovery_block") or {}).get("restarts"),
            "fec_groups": (x.get("fec") or {}).get("groups"),
            "fec_send_errors": (x.get("fec") or {}).get("send_errors"),
        }
        for name, cur in (("enc", en), ("comp", co), ("ra", ra)):
            if prev is not None and cur.get("cpu_jiffies") is not None:
                p = prev["procs"].get({"enc": "encoder", "comp": "companion",
                                       "ra": "retroarch"}[name]) or {}
                if p.get("cpu_jiffies") is not None and p.get("pid") == cur.get("pid"):
                    dt = x["monotonic"] - prev["monotonic"]
                    dj = cur["cpu_jiffies"] - p["cpu_jiffies"]
                    row[name + "_cpu_pct"] = round(dj / 100.0 / dt * 100.0, 1) if dt > 0 else None
        rows.append(row)
        prev = x
    return rows


def piecewise(rows, key, chunk_min=30):
    """Mean slope of `key` per 30 minutes, chunk by chunk."""
    out = []
    if not rows:
        return out
    end = rows[-1]["minute"]
    lo = 0.0
    while lo < end:
        hi = lo + chunk_min
        seg = [r for r in rows if lo <= r["minute"] < hi and r.get(key) is not None]
        if len(seg) >= 2:
            d = seg[-1][key] - seg[0][key]
            span = seg[-1]["minute"] - seg[0]["minute"]
            out.append((int(lo), int(min(hi, end)), seg[0][key], seg[-1][key],
                        round(d / span * chunk_min, 1) if span else None))
        lo = hi
    return out


def main():
    label, report = None, None
    for line in open(os.path.join(HERE, "s2_index.txt")):
        p = line.split()
        if len(p) == 3 and p[2] == "completed":
            label, report = p[0], p[1]
        elif len(p) >= 2 and p[1] in ("NOREPORT", "FAILED_TO_OPEN"):
            print("!! session %s did not complete: %s" % (p[0], p[1]))
    if not label:
        print("no completed session")
        return
    out = os.path.join(HERE, label)

    print("===== %s (%s) =====" % (label, report))
    summ = A.report_summary(os.path.join(out, report))
    for k, v in summ.items():
        if k in ("discontinuities", "first_idr_rows", "slow_events_top_gap"):
            continue
        print("  %-28s %s" % (k, v))
    print("  duration_hours %.2f" % (summ["duration_ms"] / 3600000.0))

    sm = samples(os.path.join(out, "samples.jsonl"))
    mins = [r["minute"] for r in sm]
    print("\n--- host samples: %d over %.1f minutes ---" % (len(sm), mins[-1] if mins else 0))
    memtotal = None
    raw = jload(os.path.join(out, "samples.jsonl"))
    if raw:
        memtotal = (raw[0].get("mem") or {}).get("MemTotal")
    print("  MemTotal %s kB (%.2f GiB)" % (memtotal, (memtotal or 0) / 1048576.0))
    for key in ("ra_rss_kb", "ra_anon_kb", "ra_file_kb", "ra_shmem_kb", "ra_swap_kb",
                "comp_rss_kb", "comp_anon_kb", "comp_threads", "enc_rss_kb",
                "cpu_temp_c", "gpu_temp_c", "gpu_power_w", "load1", "mem_avail_kb",
                "enc_cpu_pct", "ra_cpu_pct", "comp_cpu_pct"):
        vals = [r.get(key) for r in sm]
        good = [v for v in vals if v is not None]
        if good:
            print("    %-14s first=%s last=%s min=%s max=%s  Spearman %.3f"
                  % (key, good[0], good[-1], min(good), max(good), A.spearman(vals, mins)))

    for key in ("ra_rss_kb", "ra_anon_kb", "ra_file_kb", "comp_rss_kb", "enc_rss_kb"):
        pw = piecewise(sm, key)
        if pw:
            print("\n  %s per 30-min block (start_kb -> end_kb, slope kB/30min):" % key)
            for lo, hi, a, b, slope in pw:
                print("    %3d-%3d min: %9s -> %9s  %+9s" % (lo, hi, a, b, slope))

    last = sm[-1] if sm else {}
    print("\n  logs: heartbeat=%s recovery=%s archive_files=%s"
          % (last.get("hb_log_bytes"), last.get("rec_log_bytes"), last.get("archive_files")))
    print("  fec groups=%s send_errors=%s" % (last.get("fec_groups"), last.get("fec_send_errors")))
    states = sorted({r["recovery_state"] for r in sm if r["recovery_state"]})
    print("  recovery states seen: %s; restarts end=%s" % (states, last.get("restarts")))

    with open(os.path.join(out, "host_samples.csv"), "w", newline="\n") as fh:
        cols = list(sm[0].keys())
        fh.write(",".join(cols) + "\n")
        for r in sm:
            fh.write(",".join(str(r.get(c)) for c in cols) + "\n")

    hb = A.heartbeat_series(os.path.join(out, "heartbeat_lines.jsonl"))
    if hb:
        hmins = [h["minute"] for h in hb]
        print("\n--- heartbeat: %d minutes ---" % len(hb))
        for key in ("fps", "max_age_ms", "stalls_gt_120ms", "stalls_gt_1000ms"):
            vals = [h[key] for h in hb]
            good = [v for v in vals if v is not None]
            if good:
                print("    %-18s first=%s last=%s min=%s max=%s  Spearman vs minute %.3f"
                      % (key, good[0], good[-1], min(good), max(good), A.spearman(vals, hmins)))
        with open(os.path.join(out, "per_minute.csv"), "w", newline="\n") as fh:
            cols = ["minute", "ticks", "fps", "max_age_ms", "stalls_gt_120ms",
                    "stalls_gt_1000ms", "rx_packets"]
            fh.write(",".join(cols) + "\n")
            for h in hb:
                fh.write(",".join(str(h[c]) for c in cols) + "\n")
        # fps by 30-minute block
        print("\n  fps by 30-min block:")
        for lo in range(0, int(hmins[-1]) + 1, 30):
            seg = [h["fps"] for h in hb if lo <= h["minute"] < lo + 30 and h["fps"]]
            if seg:
                print("    %3d-%3d min: mean %.3f  min %.3f  max %.3f"
                      % (lo, lo + 30, sum(seg) / len(seg), min(seg), max(seg)))

    rec = jload(os.path.join(out, "recovery_lines.jsonl"))
    evs = [r for r in rec if r.get("event") not in ("session_started", "session_ended")]
    print("\n  recovery events beyond start/end: %d" % len(evs))
    for r in evs:
        print("    ", r.get("at_utc"), r.get("event"),
              {k: v for k, v in r.items()
               if k not in ("schema", "at_utc", "event") and v is not None})

    print("\n--- discontinuities ---")
    print("elapsed_ms,type,jump_packets,resync_to_idr_ms,rejected_idr_aus,"
          "dropped_non_idr_aus,au_complete,au_fec_recovered,au_fec_unrecoverable_group")
    for d, i in zip(summ["discontinuities"], summ["first_idr_rows"]):
        print("%d,%s,%d,%d,%d,%d,%s,%s,%s"
              % (d["elapsed_ms"], d["type"], d["jump_packets"], i["resync_to_idr_ms"],
                 i["rejected_idr_aus"], i["dropped_non_idr_aus"], i["au_complete"],
                 i["au_fec_recovered"], i["au_fec_unrecoverable_group"]))


if __name__ == "__main__":
    main()
