#!/usr/bin/env python3
"""PP-H1: one display run's summary. argv[1] = runs/<label>. Reads out.txt (Godot's --print-fps lines and the probe's
lines) and samples.tsv; prints JSON. The frames a second are taken from the first printed second after the probe's
"ready" line (the scene set) to the close."""
import json, re, statistics, sys
from pathlib import Path

d = Path(sys.argv[1])
out = d.joinpath("out.txt").read_text(errors="replace").splitlines()
ready = next((i for i, l in enumerate(out) if l.startswith("PROBE ready")), None)
fps_all = [(i, float(m.group(1))) for i, l in enumerate(out) if (m := re.match(r"Project FPS: ([0-9.]+)", l))]
fps = [v for i, v in fps_all if ready is not None and i > ready]
# the first printed second after "ready" can be partial (the scene being set): drop it
fps = fps[1:] if len(fps) > 1 else fps
bad = [l for l in out if re.search(r"(?i)\b(error|crash|segmentation|abort|fatal|assert)\b", l) and not l.startswith("PROBE")]
rows = [l.split("\t") for l in d.joinpath("samples.tsv").read_text().splitlines()[1:] if l.strip()]
def col(k, conv=float):
    out_ = []
    for r in rows:
        try:
            out_.append(conv(r[k]))
        except (ValueError, IndexError):
            pass
    return out_
cpu, gpu, vram, gtt, load, tc, tg = (col(i) for i in range(1, 8))
med = lambda x: round(statistics.median(x), 1) if x else None
res = {
    "seconds_measured": len(fps),
    "fps_median": med(fps), "fps_lowest": min(fps) if fps else None, "fps_highest": max(fps) if fps else None,
    "seconds_under_59": sum(1 for v in fps if v < 59), "seconds_under_50": sum(1 for v in fps if v < 50),
    "seconds_under_30": sum(1 for v in fps if v < 30),
    "godot_cpu_pct_median": med(cpu), "godot_cpu_pct_max": max(cpu) if cpu else None,
    "gpu_busy_pct_median": med(gpu), "gpu_busy_pct_max": max(gpu) if gpu else None,
    "vram_mb_max": max(vram) if vram else None, "gtt_mb_max": max(gtt) if gtt else None,
    "load1_max": max(load) if load else None, "cpu_c_max": max(tc) if tc else None, "gpu_c_max": max(tg) if tg else None,
    "error_or_crash_lines": len(bad), "error_lines_sample": bad[:5],
    "probe_lines": [l for l in out if l.startswith("PROBE")][:3],
}
print(json.dumps(res, indent=1))
