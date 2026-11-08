#!/usr/bin/env python3
"""H3-P1: numbers out of one title's raw probe files -> CSVs (no path / filename / title) + a summary JSON.
usage: analyze.py <raw_dir> <out_dir> <native_hz>"""
import csv, json, re, statistics as st, sys
from datetime import datetime
from pathlib import Path

raw, out, native = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
S = {}


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


# M1 / M4: unique frames from mpdecimate + showinfo
cap = raw / "capture_showinfo.txt"
if cap.exists():
    ts = [float(m.group(1)) for m in re.finditer(r"pts_time:([\d.]+)", cap.read_text())]
    if ts:
        t0 = ts[0]
        ts = [t - t0 for t in ts]
        per_s = {}
        for t in ts:
            per_s[int(t)] = per_s.get(int(t), 0) + 1
        secs = [per_s.get(i, 0) for i in range(int(max(ts)) + 1)]
        full = secs[:-1] if len(secs) > 1 else secs  # drop the partial last second
        iv = [(b - a) * 1000 for a, b in zip(ts, ts[1:])]
        with open(out / "m1_unique_fps_per_s.csv", "w") as f:
            f.write("second,unique_frames\n")
            f.writelines(f"{i},{n}\n" for i, n in enumerate(secs))
        with open(out / "m4_frame_intervals_ms.csv", "w") as f:
            f.write("index,interval_ms\n")
            f.writelines(f"{i},{v:.2f}\n" for i, v in enumerate(iv))
        S["m1"] = {"seconds": len(full), "unique_frames": len(ts), "median_fps": st.median(full), "min_fps": min(full),
                   "max_fps": max(full), "mean_fps": round(len(ts) / max(ts), 2), "native": native}
        S["m4"] = {"p50_ms": round(q(iv, .5), 2), "p95_ms": round(q(iv, .95), 2), "p99_ms": round(q(iv, .99), 2),
                   "max_ms": round(max(iv), 2), "gaps_gt_100ms": sum(v > 100 for v in iv)}

# M2: mpstat per core (busy = 100 - idle), over the whole run and over the capture window
def mpstat(path):
    rows = []
    hdr = None
    for ln in path.read_text().splitlines():
        p = ln.split()
        if len(p) > 3 and p[1] == "CPU" or (len(p) > 3 and p[2] == "CPU"):
            hdr = ["time"] + p[1:]
            continue
        if hdr and len(p) == len(hdr) and p[0][:2].isdigit():
            rows.append(dict(zip(hdr, p)))
    return hdr, rows


hdr, rows = mpstat(raw / "mpstat.txt")
cores = {}
tkey = hdr[0] if hdr else None
ckey = "CPU"
for r in rows:
    c = r.get(ckey)
    if c is None or c == "all":
        continue
    cores.setdefault(int(c), []).append((r[tkey], 100 - float(r["%idle"])))
with open(out / "m2_core_busy_1hz.csv", "w") as f:
    n = min(len(v) for v in cores.values()) if cores else 0
    f.write("second," + ",".join(f"cpu{c}" for c in sorted(cores)) + "\n")
    for i in range(n):
        f.write(f"{i}," + ",".join(f"{cores[c][i][1]:.1f}" for c in sorted(cores)) + "\n")


def longest_run(vals, thr):
    best = cur = 0
    for v in vals:
        cur = cur + 1 if v >= thr else 0
        best = max(best, cur)
    return best


S["m2"] = {"cores": len(cores), "per_core_median": {c: round(st.median([v for _, v in cores[c]]), 1) for c in sorted(cores)},
           "per_core_max": {c: round(max(v for _, v in cores[c]), 1) for c in sorted(cores)},
           "longest_run_ge90_s": max((longest_run([v for _, v in cores[c]], 90) for c in cores), default=0)}
busiest = max(cores, key=lambda c: st.median([v for _, v in cores[c]])) if cores else None
S["m2"]["busiest_core"] = busiest

# pidstat threads: mean %CPU per thread name
pt = raw / "pidstat.txt"
if pt.exists():
    th = {}
    hdr2 = None
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
    top = sorted(((round(st.mean(v), 1), round(max(v), 1), k) for k, v in th.items()), reverse=True)[:8]
    with open(out / "m2_threads_mean_cpu.csv", "w") as f:
        f.write("thread,mean_pct,max_pct\n")
        f.writelines(f"{k},{m},{x}\n" for m, x, k in top)
    S["m2"]["threads_top"] = [{"thread": k, "mean": m, "max": x} for m, x, k in top]

# M3 / M6 / M5 from sys_1hz.csv
sysr = list(csv.DictReader(open(raw / "sys_1hz.csv")))
g = [float(r["gpu_busy_pct"]) for r in sysr if r["gpu_busy_pct"] and r["emu_alive"] == "1"]
tc = [float(r["tctl_c"]) for r in sysr if r["tctl_c"] and r["emu_alive"] == "1"]
S["m3"] = {"samples": len(g), "median": st.median(g) if g else None, "p95": q(g, .95), "max": max(g) if g else None}
S["m6"] = {"samples": len(tc), "median": st.median(tc) if tc else None, "max": max(tc) if tc else None}
with open(out / "m3_m6_gpu_tctl_1hz.csv", "w") as f:
    f.write("second,gpu_busy_pct,tctl_c,emu_alive\n")
    f.writelines(f"{i},{r['gpu_busy_pct']},{r['tctl_c']},{r['emu_alive']}\n" for i, r in enumerate(sysr))
# per-second read wait from /sys/block stat deltas (ms of read time per completed read)
st_rows = []
for a, b in zip(sysr, sysr[1:]):
    dr = int(b["rd_ios"]) - int(a["rd_ios"])
    dms = int(b["rd_ms"]) - int(a["rd_ms"])
    st_rows.append((dr, dms, round(dms / dr, 1) if dr else 0.0, int(b["rd_sectors"]) - int(a["rd_sectors"]), int(b["wr_ios"]) - int(a["wr_ios"])))
with open(out / "m5_disk_1hz.csv", "w") as f:
    f.write("second,reads,read_ms,avg_wait_ms,sectors_read,writes\n")
    f.writelines(f"{i},{a},{b},{c},{d},{e}\n" for i, (a, b, c, d, e) in enumerate(st_rows))
# iostat r_await per second
io = []
hdr3 = None
for ln in (raw / "iostat.txt").read_text().splitlines():
    p = ln.split()
    if p and p[0] == "Device":
        hdr3 = p
        continue
    if hdr3 and p and p[0] == "sda" and len(p) == len(hdr3):
        d = dict(zip(hdr3, p))
        io.append((float(d.get("r_await", 0)), float(d.get("%util", 0)), float(d.get("r/s", 0))))
io = io[1:]  # the first report is since boot
with open(out / "m5_iostat_1hz.csv", "w") as f:
    f.write("second,r_per_s,r_await_ms,util_pct\n")
    f.writelines(f"{i},{c},{a},{u}\n" for i, (a, u, c) in enumerate(io))
stalls = [i for i, (a, u, c) in enumerate(io) if a > 500]
S["m5"] = {"iostat_seconds": len(io), "stall_seconds_r_await_gt_500": len(stalls), "stall_at_s": stalls[:20],
           "max_r_await_ms": max((a for a, _, _ in io), default=0), "writes_total": sum(r[4] for r in st_rows),
           "reads_total": sum(r[0] for r in st_rows)}

ev = [json.loads(l) for l in open(raw / "events.jsonl")]
S["events"] = [{k: v for k, v in e.items() if k not in ("names",)} for e in ev if e["event"] in
               ("launch", "p0b", "p0c", "tree", "emu_main", "window", "idle1_done", "capture_start", "capture_done",
                "idle2_done", "provoke", "provoke_result", "exit", "emu_exited_early", "exit_timeout")]
S["windows_seen"] = {"distinct_names": len({n for e in ev if e["event"] == "watch" for n in e.get("names", [])}), "max_windows": max((e.get("windows", 0) for e in ev if e["event"] == "watch"), default=0)}
json.dump(S, open(out / "summary.json", "w"), indent=1)
print(json.dumps({k: S[k] for k in S if k not in ("events",)}, indent=1))
