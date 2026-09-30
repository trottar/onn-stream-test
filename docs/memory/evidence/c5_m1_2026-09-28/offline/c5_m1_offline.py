#!/usr/bin/env python3
"""C5-M1 step 1c: encoder headroom offline. One x11grab of the RetroArch
window through the companion's own h264_vaapi argv (native_stream.py
_build_linux_ffmpeg_command, 2026-09-28) with only width/height/bitrate/cap
changed, to `-f null`, for DURATION s. No stream is running (the game was
launched without one and unpaused through RetroArch's command port).

Per second: frames encoded (ffmpeg -progress), host CPU busy % (/proc/stat),
GPU busy % (amdgpu gpu_busy_percent), ffmpeg process CPU %.
usage: c5_m1_offline.py <label> <W> <H> <kbps> <cap_bytes> <window_id> <seconds> [out_file]
out_file default '-' with -f null; otherwise the H.264 elementary stream
is written there (for the IDR-size check, 1d)."""
import json, os, subprocess, sys, time
label, W, H, kbps, cap, wid, dur = sys.argv[1:8]
out = sys.argv[8] if len(sys.argv) > 8 else None
W, H, kbps, cap, dur = int(W), int(H), int(kbps), int(cap), int(dur)
vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=fast_bilinear,"
      f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,format=nv12,hwupload")
argv = ["/usr/bin/ffmpeg", "-hide_banner", "-loglevel", "info", "-nostdin",
        "-vaapi_device", "/dev/dri/renderD128", "-f", "x11grab", "-framerate", "60",
        "-window_id", wid, "-i", ":0", "-vf", vf, "-an", "-c:v", "h264_vaapi",
        "-profile:v", "high", "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k",
        "-bufsize", f"{kbps}k"]
if cap > 0:
    argv += ["-max_frame_size", str(cap)]
argv += ["-g", "15", "-bf", "0", "-t", str(dur), "-progress", "pipe:1", "-stats_period", "1"]
argv += (["-f", "h264", out] if out else ["-f", "null", "-"])
GPU = "/sys/class/drm/card0/device/gpu_busy_percent"
def cpu():
    v = list(map(int, open("/proc/stat").readline().split()[1:]))
    idle = v[3] + v[4]; return sum(v), idle
def pcpu(pid):
    try:
        f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
        return int(f[11]) + int(f[12])
    except Exception:
        return None
tick = os.sysconf("SC_CLK_TCK")
p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
rows, prev_frame, prev_t = [], 0, time.monotonic()
c0, pc0 = cpu(), pcpu(p.pid)
blk = {}
for line in p.stdout:
    k, _, v = line.strip().partition("=")
    blk[k] = v
    if k == "progress":
        t = time.monotonic(); c1 = cpu(); pc1 = pcpu(p.pid)
        try: frame = int(blk.get("frame", "0"))
        except ValueError: frame = prev_frame
        dt = t - prev_t
        busy = 100.0 * (1 - (c1[1] - c0[1]) / max(1, c1[0] - c0[0]))
        try: gpu = int(open(GPU).read().strip())
        except Exception: gpu = None
        proc = (100.0 * (pc1 - pc0) / tick / dt) if (pc1 is not None and pc0 is not None and dt > 0) else None
        rows.append({"t": round(t, 3), "frame": frame, "fps": round((frame - prev_frame) / dt, 2) if dt > 0 else None,
                     "speed": blk.get("speed"), "dup": blk.get("dup_frames"), "drop": blk.get("drop_frames"),
                     "host_cpu_busy_pct": round(busy, 1), "ffmpeg_cpu_pct": None if proc is None else round(proc, 1),
                     "gpu_busy_pct": gpu, "progress": v})
        prev_frame, prev_t, c0, pc0 = frame, t, c1, pc1
err = p.stderr.read(); p.wait()
open(f"{label}_ffmpeg_stderr.log", "w").write(err)
json.dump({"label": label, "argv": argv, "rows": rows, "rc": p.returncode}, open(f"{label}.json", "w"), indent=1)
steady = [r for r in rows[2:] if r["progress"] == "continue" and r["fps"] is not None]
fps = sorted(r["fps"] for r in steady)
def pct(a, q): return a[min(len(a) - 1, max(0, int(round(q * (len(a) - 1)))))] if a else None
def mean(a): a = [x for x in a if x is not None]; return round(sum(a) / len(a), 2) if a else None
last = rows[-1] if rows else {}
summary = {"label": label, "W": W, "H": H, "kbps": kbps, "cap": cap, "rc": p.returncode,
           "frames_total": last.get("frame"), "seconds_scored": len(steady),
           "fps_mean": mean(fps), "fps_p5": pct(fps, 0.05), "fps_min": fps[0] if fps else None,
           "final_speed": last.get("speed"), "dup_frames": last.get("dup"), "drop_frames": last.get("drop"),
           "host_cpu_busy_mean": mean([r["host_cpu_busy_pct"] for r in steady]),
           "ffmpeg_cpu_mean": mean([r["ffmpeg_cpu_pct"] for r in steady]),
           "gpu_busy_mean": mean([r["gpu_busy_pct"] for r in steady]),
           "gpu_busy_max": max([r["gpu_busy_pct"] for r in steady if r["gpu_busy_pct"] is not None], default=None)}
print(json.dumps(summary))
