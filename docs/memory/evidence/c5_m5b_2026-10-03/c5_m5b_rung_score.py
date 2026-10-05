#!/usr/bin/env python3
"""C5-M5B section 5 -- the full look preset at the rung: C5-M4's rows over the 1080p minutes only.
Read-only.   c5_m5b_rung_score.py <runs dir> <arm>  -> prints; writes <arm>_rung_score.{txt,json} beside the dir.

The window is [inject_up_utc + 10 s, rung_end_utc] from rung_times_<arm>.txt (c5_m5b_rung_hook.sh).
  R1  RetroArch's counter (<arm>_title.txt, xprop -spy epoch stamps) in the window: fps >= 59.88 and no
      256-frame interval > 256/60 s + 12 ms (C5-M4's bar).
  R2  the encoder's progress lines of the LAST encoder run in alpha_<arm>.log (the rung's 1920x1080 run; a
      restart resets ffmpeg's frame counter), past its first 5 s: median per-line fps >= 59.5 and dup+drop
      growth <= 0.5 % of frames.
Reported: GPU busy mean / p95, GPU W, Tctl max (<arm>_host.jsonl), RetroArch and encoder % of a core (T2), the
per-second largest frame p50 / p90 and cap hits s/min (>= 95 % of 90,000 B; frames_<arm>.jsonl), the client's
fps / stale / loss per minute (C2 telemetry), all in the window.
"""
import json, os, re, statistics, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
R, A = os.path.join(HERE, sys.argv[1]), sys.argv[2]
NOMINAL = 256 / 60.0
CAP = 90_000


def ts(s):
    s = s.rstrip("Z")
    return datetime.strptime(s[:23], "%Y-%m-%dT%H:%M:%S.%f" if "." in s else "%Y-%m-%dT%H:%M:%S") \
        .replace(tzinfo=timezone.utc).timestamp()


def jl(p):
    out = []
    if os.path.exists(p):
        for line in open(p, errors="replace"):
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def pct(a, q):
    a = sorted(x for x in a if x is not None)
    return a[min(len(a) - 1, int(round(q * (len(a) - 1))))] if a else None


times = dict(l.split() for l in open(os.path.join(R, f"rung_times_{A}.txt")) if l.strip())
W0, W1 = ts(times["inject_up_utc"]) + 10.0, ts(times["rung_end_utc"])

# R1
rows = []
for line in open(os.path.join(R, f"{A}_title.txt"), errors="replace"):
    m = re.match(r"([0-9.]+) .*FPS:\s*([0-9.]+) \|\| Frames: (\d+)", line)
    if m and W0 <= float(m.group(1)) <= W1:
        rows.append((float(m.group(1)), int(m.group(3))))
dts = [(b[0] - a[0], b[1] - a[1]) for a, b in zip(rows, rows[1:])]
span_t = rows[-1][0] - rows[0][0] if len(rows) > 1 else 0
span_f = rows[-1][1] - rows[0][1] if len(rows) > 1 else 0
ra_fps = span_f / span_t if span_t else None
ivmax = max((d for d, f in dts if f == 256), default=None)
r1 = bool(ra_fps and ra_fps >= 59.88 and ivmax is not None and ivmax <= (NOMINAL + 0.012))

# R2: the last encoder run
txt = open(os.path.join(R, f"alpha_{A}.log"), errors="replace").read().replace("\r", "\n")
runs, cur, last_f = [], [], None
for line in txt.splitlines():
    m = re.match(r"frame=\s*(\d+).*?time=(\d+):(\d+):([\d.]+)", line)
    if not m:
        continue
    f = int(m.group(1))
    if last_f is not None and f < last_f:
        runs.append(cur)
        cur = []
    last_f = f
    t = int(m.group(2)) * 3600 + int(m.group(3)) * 60 + float(m.group(4))
    dup, drop = re.search(r"dup=(\d+)", line), re.search(r"drop=(\d+)", line)
    cur.append((f, t, int(dup.group(1)) if dup else 0, int(drop.group(1)) if drop else 0))
runs.append(cur)
pr = [x for x in runs[-1] if x[1] >= 5.0]
fr = [(b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(pr, pr[1:]) if b[1] > a[1]]
enc_med = statistics.median(fr) if fr else None
frames = pr[-1][0] - pr[0][0] if len(pr) > 1 else 0
dd = (pr[-1][2] - pr[0][2]) + (pr[-1][3] - pr[0][3]) if len(pr) > 1 else None
r2 = bool(enc_med is not None and enc_med >= 59.5 and dd is not None and dd <= 0.005 * frames)

# host, T2, stream, client in the window
host = [r for r in jl(os.path.join(R, f"{A}_host.jsonl")) if W0 <= ts(r["at_utc"]) <= W1]
t2 = [r for r in jl(os.path.join(R, "t2_samples.jsonl")) if r.get("at_utc") and W0 <= ts(r["at_utc"]) <= W1]
fr_rows = [r for r in jl(os.path.join(R, f"frames_{A}.jsonl")) if r.get("at_utc") and W0 <= ts(r["at_utc"]) <= W1]
tel = [r for r in jl(os.path.join(R, f"{A}_telemetry.jsonl")) if r.get("fresh") and W0 <= ts(r["at_utc"]) <= W1]
mins = (W1 - W0) / 60.0
mean = lambda a: round(statistics.fmean([x for x in a if x is not None]), 2) if [x for x in a if x is not None] else None
rend = sum((r.get("decoder") or {}).get("rendered_frames_delta") or 0 for r in tel)
tspan = (ts(tel[-1]["at_utc"]) - ts(tel[0]["at_utc"])) if len(tel) > 1 else None
out = {
    "window_utc": [times["inject_up_utc"], times["rung_end_utc"]], "window_min": round(mins, 2),
    "HOLDS_60": r1 and r2, "r1": r1, "ra_fps": round(ra_fps, 3) if ra_fps else None,
    "longest_256_interval_ms": round(ivmax * 1000, 1) if ivmax else None, "r1_updates": len(rows),
    "r2": r2, "enc_fps_median": round(enc_med, 2) if enc_med else None, "enc_frames": frames, "dup_drop": dd,
    "encoder_runs_in_log": len(runs),
    "gpu_busy_mean": mean([r.get("gpu_busy_pct") for r in host]), "gpu_busy_p95": pct([r.get("gpu_busy_pct") for r in host], 0.95),
    "gpu_w_mean": mean([r.get("gpu_power_w") for r in host]), "tctl_max": max((r.get("tctl_c") or 0 for r in host), default=None),
    "t2_ra_cpu": mean([((r.get("host") or {}).get("retroarch") or {}).get("cpu_pct") for r in t2]),
    "t2_enc_cpu": mean([((r.get("host") or {}).get("encoder") or {}).get("cpu_pct") for r in t2]),
    "frame_max_p50": pct([r.get("max_bytes") for r in fr_rows], 0.5), "frame_max_p90": pct([r.get("max_bytes") for r in fr_rows], 0.9),
    "cap_hits_s_per_min": round(sum(1 for r in fr_rows if (r.get("max_bytes") or 0) >= 0.95 * CAP) / mins, 1) if mins else None,
    "client_fps": round(rend / tspan, 2) if tspan else None,
    "stale_per_min": round(sum((r.get("decoder") or {}).get("stale_output_drops_delta") or 0 for r in tel) / mins, 2),
    "loss_per_min": round(sum((r.get("receiver") or {}).get("lost_packets_delta") or 0 for r in tel) / mins, 2),
}
text = (f"C5-M5B the full look preset at the rung ({A}), the 1080p window {times['inject_up_utc']} +10 s .. "
        f"{times['rung_end_utc']} ({out['window_min']} min)\n" + "\n".join(f"  {k}: {v}" for k, v in out.items()) + "\n")
print(text)
open(os.path.join(HERE, f"{A}_rung_score.txt"), "w").write(text)
json.dump(out, open(os.path.join(HERE, f"{A}_rung_score.json"), "w"), indent=1)
