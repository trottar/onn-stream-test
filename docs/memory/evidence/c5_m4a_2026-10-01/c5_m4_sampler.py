#!/usr/bin/env python3
"""C5-M4 -- the host-table sampler, one hold per call. Stops when <out_prefix>.stop exists.

    c5_m4_sampler.py <out_prefix> [--telemetry] [--thumbs <dir>]

Writes, all with UTC timestamps:
  <out_prefix>_host.jsonl   every 1 s: per-logical-CPU busy % (/proc/stat), GPU busy % (amdgpu
                            gpu_busy_percent), GPU power W (amdgpu power1_average), temperatures
                            (k10temp Tctl, amdgpu edge), and CPU % of one core for RetroArch and for
                            the companion's encoder (ffmpeg ... h264_vaapi), from /proc/<pid>/stat.
  <out_prefix>_title.txt    RetroArch's window title, every change, as `xprop -spy` delivers it
                            ("<epoch_s> <title>"). RetroArch rewrites "|| FPS: x || Frames: n" every
                            256 frames (fps_show / framecount_show, set by the measurement override
                            with the OSD font and widgets off, so nothing is drawn on the picture).
  <out_prefix>_telemetry.jsonl  (--telemetry) every 2 s: /diagnostics/stream-telemetry's decoder,
                            latency and receiver blocks (the client's C2 report as the companion holds it).
  <dir>/thumb_<n>.png       (--thumbs) one 480x270 frame of the window every 30 s, to say what the
                            attract loop was showing.
Read-only on everything; it never writes outside its outputs.
"""
import json, os, subprocess, sys, threading, time, urllib.request

PREFIX = sys.argv[1]
TELEM = "--telemetry" in sys.argv
THUMBS = sys.argv[sys.argv.index("--thumbs") + 1] if "--thumbs" in sys.argv else None
STOP = PREFIX + ".stop"
CLK = os.sysconf("SC_CLK_TCK")
ENV = dict(os.environ, DISPLAY=":0")


def utc():
    t = time.time()
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + ".%03dZ" % int((t % 1) * 1000)


def hwmon():
    out = {}
    for h in os.listdir("/sys/class/hwmon"):
        p = "/sys/class/hwmon/" + h
        try:
            name = open(p + "/name").read().strip()
        except OSError:
            continue
        if name == "k10temp":
            out["tctl_c"] = int(open(p + "/temp1_input").read()) / 1000
        elif name == "amdgpu":
            try:
                out["gpu_edge_c"] = int(open(p + "/temp1_input").read()) / 1000
            except OSError:
                pass
            for f in ("power1_average", "power1_input"):
                try:
                    out["gpu_power_w"] = int(open(p + "/" + f).read()) / 1e6
                    break
                except OSError:
                    pass
    return out


def cpus():
    rows = {}
    for line in open("/proc/stat"):
        if line.startswith("cpu") and line[3:4].isdigit():
            f = line.split()
            v = list(map(int, f[1:]))
            rows[f[0]] = (sum(v), v[3] + v[4])
    return rows


def find_pids():
    """By /proc/<pid>/comm: the AppImage process is "RetroArch-Linux" (15-char truncation)."""
    ra = enc = None
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            comm = open(f"/proc/{pid}/comm").read().strip()
            if comm in ("retroarch", "RetroArch-Linux"):
                ra = int(pid)
            elif comm == "ffmpeg":
                cmd = open(f"/proc/{pid}/cmdline", "rb").read()
                if b"h264_vaapi" in cmd and b"x11grab" in cmd:
                    enc = int(pid)
        except OSError:
            continue
    return ra, enc


def ticks(pid):
    try:
        f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
        return int(f[11]) + int(f[12])
    except (OSError, IndexError, TypeError):
        return None


def host_loop():
    c0, p0, t0 = cpus(), {}, time.monotonic()
    with open(PREFIX + "_host.jsonl", "w") as fh:
        while not os.path.exists(STOP):
            time.sleep(1)
            c1, t1 = cpus(), time.monotonic()
            per = {k: round(100 * (1 - (c1[k][1] - c0[k][1]) / max(1, c1[k][0] - c0[k][0])), 1) for k in c1 if k in c0}
            ra, enc = find_pids()
            proc = {}
            for name, pid in (("retroarch", ra), ("encoder", enc)):
                tk = ticks(pid) if pid else None
                if tk is not None and pid in p0:
                    proc[name + "_cpu_pct"] = round(100 * (tk - p0[pid]) / CLK / (t1 - t0), 1)
                if tk is not None:
                    p0[pid] = tk
            try:
                g = int(open("/sys/class/drm/card0/device/gpu_busy_percent").read())
            except OSError:
                g = None
            row = {"at_utc": utc(), "cpu_pct": per, "cpu_max_pct": max(per.values()) if per else None,
                   "cpu_mean_pct": round(sum(per.values()) / len(per), 1) if per else None, "gpu_busy_pct": g}
            row.update(hwmon())
            row.update(proc)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            c0, t0 = c1, t1


def window():
    r = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "^RetroArch "], capture_output=True,
                       text=True, env=ENV)
    w = r.stdout.split()
    return w[0] if w else None


def title_loop():
    w = None
    for _ in range(60):
        w = window()
        if w or os.path.exists(STOP):
            break
        time.sleep(1)
    with open(PREFIX + "_title.txt", "w") as fh:
        if not w:
            fh.write("# no RetroArch window\n")
            return
        fh.write(f"# window {w}\n")
        p = subprocess.Popen(["xprop", "-spy", "-id", w, "WM_NAME"], stdout=subprocess.PIPE, text=True, env=ENV)
        stopper = threading.Thread(target=lambda: (wait_stop(), p.terminate()), daemon=True)
        stopper.start()
        for line in p.stdout:
            fh.write("%.3f %s\n" % (time.time(), line.strip()))
            fh.flush()


def wait_stop():
    while not os.path.exists(STOP):
        time.sleep(0.5)


def telem_loop():
    with open(PREFIX + "_telemetry.jsonl", "w") as fh:
        while not os.path.exists(STOP):
            try:
                d = json.load(urllib.request.urlopen("http://localhost:8765/diagnostics/stream-telemetry", timeout=2))
                fh.write(json.dumps({"at_utc": utc(), "fresh": d.get("fresh"), "elapsed_ms": d.get("session_elapsed_ms"),
                                     "decoder": d.get("decoder"), "latency": d.get("latency"),
                                     "receiver": d.get("receiver")}) + "\n")
                fh.flush()
            except Exception as e:
                fh.write(json.dumps({"at_utc": utc(), "error": str(e)[:80]}) + "\n")
            time.sleep(2)


def thumb_loop():
    os.makedirs(THUMBS, exist_ok=True)
    n = 0
    while not os.path.exists(STOP):
        w = window()
        if w:
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "x11grab", "-window_id", w,
                            "-i", ":0", "-frames:v", "1", "-vf", "scale=480:-2", f"{THUMBS}/thumb_{n:02d}.png"],
                           env=ENV, stdin=subprocess.DEVNULL)
            n += 1
        for _ in range(60):
            if os.path.exists(STOP):
                break
            time.sleep(0.5)


ts = [threading.Thread(target=host_loop), threading.Thread(target=title_loop)]
if TELEM:
    ts.append(threading.Thread(target=telem_loop))
if THUMBS:
    ts.append(threading.Thread(target=thumb_loop))
for t in ts:
    t.start()
for t in ts:
    t.join()
