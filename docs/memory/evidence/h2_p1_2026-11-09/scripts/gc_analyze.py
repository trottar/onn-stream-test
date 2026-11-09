#!/usr/bin/env python3
"""H2-P1: numbers out of one run's raw probe files -> CSVs (no path / filename / title / window name) + summary.json.
usage: gc_analyze.py <raw_dir> <out_dir> [first_span_s]"""
import csv, json, re, statistics as st, sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "Projects/onn-stream-test/tools"))
import n64_frames as nf  # noqa: E402
import ps2_p2_frames as p2  # noqa: E402

raw, out = Path(sys.argv[1]), Path(sys.argv[2])
span = float(sys.argv[3]) if len(sys.argv) > 3 else None
out.mkdir(parents=True, exist_ok=True)
S = {}


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return round(xs[f] + (xs[c] - xs[f]) * (k - f), 2)


def distinct_times(frames):
    return [t for i, (t, c, _) in enumerate(frames) if i == 0 or c != frames[i - 1][1]]


# M1 / M4: the 60-s capture
cap = raw / "capture_showinfo.txt"
if cap.exists():
    fr = p2.parse(cap.read_text(errors="replace"))
    if fr:
        S["m1_n64_frames"] = nf.analyze(fr)
        t0 = fr[0][0]
        dt = [t - t0 for t in distinct_times(fr)]
        per = {}
        for t in dt:
            per[int(t)] = per.get(int(t), 0) + 1
        last = int(fr[-1][0] - t0)
        secs = [per.get(i, 0) for i in range(last)]  # full seconds only
        iv = [(b - a) * 1000 for a, b in zip(dt, dt[1:])]
        with open(out / "m1_distinct_fps_per_s.csv", "w") as f:
            f.write("second,distinct_frames\n")
            f.writelines(f"{i},{n}\n" for i, n in enumerate(secs))
        with open(out / "m4_frame_intervals_ms.csv", "w") as f:
            f.write("index,interval_ms\n")
            f.writelines(f"{i},{v:.2f}\n" for i, v in enumerate(iv))
        S["m1_raw"] = {"captured_frames": len(fr), "seconds": len(secs), "distinct": len(dt),
                       "median_fps": st.median(secs) if secs else None, "min_fps": min(secs) if secs else None,
                       "black_frames": sum(y <= p2.BLACK_Y for _, _, y in fr)}
        S["m4"] = {"p50_ms": q(iv, .5), "p95_ms": q(iv, .95), "p99_ms": q(iv, .99),
                   "max_ms": round(max(iv), 2) if iv else None, "gaps_gt_100ms": sum(v > 100 for v in iv)}

# M4: the first span (window -> the end of the P1 idle), gaps > 100 ms in the distinct frames
fs = raw / "first_showinfo.txt"
if fs.exists():
    fr = p2.parse(fs.read_text(errors="replace"))
    if fr:
        t0 = fr[0][0]
        dt = [t - t0 for t in distinct_times(fr)]
        if span:
            dt = [t for t in dt if t <= span]
        iv = [(b - a) * 1000 for a, b in zip(dt, dt[1:])]
        S["m4_first_span"] = {"span_s": round(dt[-1], 1) if dt else 0, "distinct": len(dt),
                              "gaps_gt_100ms": sum(v > 100 for v in iv), "gaps_gt_50ms": sum(v > 50 for v in iv),
                              "max_gap_ms": round(max(iv), 1) if iv else None}
        with open(out / "m4_first_span_gaps_gt_100ms.csv", "w") as f:
            f.write("at_s,gap_ms\n")
            f.writelines(f"{a:.2f},{(b - a) * 1000:.1f}\n" for a, b in zip(dt, dt[1:]) if (b - a) > 0.1)

# Dolphin's own counters (GFX LogRenderTimeToFile): render_times (presented frames) and vblank_times (emulated VIs)
for fname, key in (("render_times.txt", "dolphin_render_times"), ("vblank_times.txt", "dolphin_vblank_times")):
    rt = raw / fname
    if not rt.exists():
        continue
    vals = []
    for ln in rt.read_text(errors="replace").split():
        try:
            vals.append(float(ln))
        except ValueError:
            pass
    if not vals:
        continue
    cum, c = [], 0.0
    for v in vals:
        c += v
        cum.append(c)
    first = [v for v, t in zip(vals, cum) if span is None or t <= span * 1000]
    S[key] = {"n": len(vals), "total_s": round(cum[-1] / 1000, 1), "mean_per_s": round(len(vals) / (cum[-1] / 1000), 2),
              "p50_ms": q(vals, .5), "p95_ms": q(vals, .95), "p99_ms": q(vals, .99), "max_ms": round(max(vals), 1),
              "gt_20ms": sum(v > 20 for v in vals), "gt_34ms": sum(v > 34 for v in vals),
              "gt_100ms": sum(v > 100 for v in vals), "first_span_gt_100ms": sum(v > 100 for v in first),
              "first_span_gt_34ms": sum(v > 34 for v in first)}


# M2: mpstat per core
def mpstat(path):
    rows, hdr = [], None
    for ln in path.read_text().splitlines():
        p = ln.split()
        if len(p) > 3 and "CPU" in p[1:3]:
            hdr = ["time"] + p[1:]
            continue
        if hdr and len(p) == len(hdr) and p[0][:2].isdigit():
            rows.append(dict(zip(hdr, p)))
    return rows


cores = {}
for r in mpstat(raw / "mpstat.txt"):
    c = r.get("CPU")
    if c is None or c == "all":
        continue
    cores.setdefault(int(c), []).append(100 - float(r["%idle"]))
n = min(len(v) for v in cores.values()) if cores else 0
with open(out / "m2_core_busy_1hz.csv", "w") as f:
    f.write("second," + ",".join(f"cpu{c}" for c in sorted(cores)) + "\n")
    for i in range(n):
        f.write(f"{i}," + ",".join(f"{cores[c][i]:.1f}" for c in sorted(cores)) + "\n")


def longest_run(vals, thr):
    best = cur = 0
    for v in vals:
        cur = cur + 1 if v >= thr else 0
        best = max(best, cur)
    return best


S["m2"] = {"cores": len(cores), "per_core_median": {c: round(st.median(cores[c]), 1) for c in sorted(cores)},
           "per_core_max": {c: round(max(cores[c]), 1) for c in sorted(cores)},
           "longest_run_ge90_s": max((longest_run(cores[c], 90) for c in cores), default=0)}
S["m2"]["busiest_core"] = max(cores, key=lambda c: st.median(cores[c])) if cores else None
S["m2"]["max_core_pct"] = max((max(v) for v in cores.values()), default=None)

pt = raw / "pidstat.txt"
if pt.exists():
    th, hdr2 = {}, None
    for ln in pt.read_text().splitlines():
        p = ln.split()
        if ln.startswith("#"):
            hdr2 = ln[1:].split()
            continue
        if hdr2 and len(p) >= len(hdr2):
            d = dict(zip(hdr2, p[:len(hdr2) - 1] + [" ".join(p[len(hdr2) - 1:])]))
            if d.get("TID", "-") != "-":
                name = re.sub(r"^\|__", "", d["Command"])
                th.setdefault(name, []).append(float(d["%CPU"]))
    top = sorted(((round(st.mean(v), 1), round(max(v), 1), longest_run(v, 90), k) for k, v in th.items()),
                 reverse=True)[:10]
    with open(out / "m2_threads_cpu.csv", "w") as f:
        f.write("thread,mean_pct,max_pct,longest_ge90_s\n")
        f.writelines(f"{k},{m},{x},{r}\n" for m, x, r, k in top)
    S["m2"]["threads_top"] = [{"thread": k, "mean": m, "max": x, "longest_ge90_s": r} for m, x, r, k in top]

# M3 / M6 / M5
sysr = list(csv.DictReader(open(raw / "sys_1hz.csv")))
g = [float(r["gpu_busy_pct"]) for r in sysr if r["gpu_busy_pct"] and r["emu_alive"] == "1"]
tc = [float(r["tctl_c"]) for r in sysr if r["tctl_c"] and r["emu_alive"] == "1"]
S["m3"] = {"samples": len(g), "median": st.median(g) if g else None, "p95": q(g, .95), "max": max(g) if g else None}
S["m6"] = {"samples": len(tc), "median": st.median(tc) if tc else None, "max": max(tc) if tc else None}
with open(out / "m3_m6_gpu_tctl_1hz.csv", "w") as f:
    f.write("second,gpu_busy_pct,tctl_c,emu_alive\n")
    f.writelines(f"{i},{r['gpu_busy_pct']},{r['tctl_c']},{r['emu_alive']}\n" for i, r in enumerate(sysr))
rows = []
for a, b in zip(sysr, sysr[1:]):
    dr = int(b["rd_ios"]) - int(a["rd_ios"])
    dms = int(b["rd_ms"]) - int(a["rd_ms"])
    rows.append((dr, dms, round(dms / dr, 1) if dr else 0.0, int(b["rd_sectors"]) - int(a["rd_sectors"]),
                 int(b["wr_ios"]) - int(a["wr_ios"])))
with open(out / "m5_disk_1hz.csv", "w") as f:
    f.write("second,reads,read_ms,avg_wait_ms,sectors_read,writes\n")
    f.writelines(f"{i},{a},{b},{c},{d},{e}\n" for i, (a, b, c, d, e) in enumerate(rows))
io, hdr3 = [], None
for ln in (raw / "iostat.txt").read_text().splitlines():
    p = ln.split()
    if p and p[0] == "Device":
        hdr3 = p
        continue
    if hdr3 and p and p[0] == "sda" and len(p) == len(hdr3):
        d = dict(zip(hdr3, p))
        io.append((float(d.get("r_await", 0)), float(d.get("%util", 0)), float(d.get("r/s", 0))))
io = io[1:]
with open(out / "m5_iostat_1hz.csv", "w") as f:
    f.write("second,r_per_s,r_await_ms,util_pct\n")
    f.writelines(f"{i},{c},{a},{u}\n" for i, (a, u, c) in enumerate(io))
stalls = [i for i, (a, u, c) in enumerate(io) if a > 500]
late = [i for i in stalls if i >= 63]  # iostat starts 3 s before the launch: "after the first 60 s"
S["m5"] = {"iostat_seconds": len(io), "stall_seconds": len(stalls), "stall_seconds_after_60s": len(late),
           "stall_at_s": stalls[:20], "max_r_await_ms": max((a for a, _, _ in io), default=0),
           "max_r_await_after_60s_ms": max((a for i, (a, _, _) in enumerate(io) if i >= 63), default=0),
           "busy_read_seconds": sum(1 for a, u, c in io if c > 0), "reads_total": sum(r[0] for r in rows),
           "writes_total": sum(r[4] for r in rows)}

ev = [json.loads(l) for l in open(raw / "events.jsonl")]
keep = ("launch", "started_pid", "p0b", "p0c", "tree", "threads", "cpu_thread", "capture_source", "first_span_start",
        "first_span_end", "idle1_done", "p0e", "p0f", "capture_start", "capture_done", "idle2_done", "provoke",
        "provoke_result", "exit", "emu_exited_early", "abort_no_window", "no_visible_window_yet")
S["events"] = [{k: v for k, v in e.items() if k not in ("name_hashes", "geo")} for e in ev if e["event"] in keep]
w = [e for e in ev if e["event"] == "watch"]
S["watch"] = {"checks": len(w), "max_windows": max((e["windows"] for e in w), default=0),
              "distinct_window_names": len({h for e in w for h in e.get("name_hashes", [])}),
              "alive_through": all(e["windows"] >= 1 for e in w)}
json.dump(S, open(out / "summary.json", "w"), indent=1)
print(json.dumps({k: S[k] for k in S if k != "events"}, indent=1))
