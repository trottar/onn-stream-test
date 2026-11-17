#!/usr/bin/env python3
"""H7-C1 (H7-V2's picture keeper, its window fixed to the visible window of class retroarch): once a second while RetroArch runs, the game's window (its largest visible window by
xdotool, Pillow's X11 grab on :0, as B103's WindowPicture) saved as JPEG q90 under the run folder, with index.csv
(seconds since the keeper started, UTC, file, grab_ms, save_ms). Sends nothing to the game. Usage: keeper.py <run dir>"""
import csv, os, subprocess, sys, time, datetime
from PIL import ImageGrab
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
DISPLAY = ":0"; ENV = dict(os.environ, DISPLAY=DISPLAY)
def ra_pids():
    out = []
    for p in os.listdir("/proc"):
        if p.isdigit():
            try:
                if open(f"/proc/{p}/comm").read().strip() in ("retroarch", "RetroArch-Linux"):
                    out.append(int(p))
            except OSError:
                pass
    return out
def find(pid):
    r = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(pid)], capture_output=True, text=True, timeout=2, env=ENV)
    best = None
    for w in r.stdout.split():
        g = subprocess.run(["xdotool", "getwindowgeometry", "--shell", w], capture_output=True, text=True, timeout=2, env=ENV)
        kv = dict(l.split("=", 1) for l in g.stdout.splitlines() if "=" in l)
        try:
            geo = (int(kv["X"]), int(kv["Y"]), int(kv["WIDTH"]), int(kv["HEIGHT"]))
        except (KeyError, ValueError):
            continue
        if geo[2] < 64 or geo[3] < 64:
            continue
        if best is None or geo[2] * geo[3] > best[2] * best[3]:
            best = geo
    return best
def find_class():
    r = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "retroarch"], capture_output=True, text=True, timeout=2, env=ENV)
    best = None
    for w in r.stdout.split():
        g = subprocess.run(["xdotool", "getwindowgeometry", "--shell", w], capture_output=True, text=True, timeout=2, env=ENV)
        kv = dict(l.split("=", 1) for l in g.stdout.splitlines() if "=" in l)
        try:
            geo = (int(kv["X"]), int(kv["Y"]), int(kv["WIDTH"]), int(kv["HEIGHT"]))
        except (KeyError, ValueError):
            continue
        if geo[2] >= 64 and geo[3] >= 64 and (best is None or geo[2] * geo[3] > best[2] * best[3]):
            best = geo
    return best
t0 = time.monotonic(); n = 0; win = None; pid = None
idx = open(os.path.join(OUT, "index.csv"), "a", newline=""); w = csv.writer(idx)
if idx.tell() == 0:
    w.writerow(["seconds", "utc", "file", "grab_ms", "save_ms"]); idx.flush()
log = open(os.path.join(OUT, "keeper_log.txt"), "a")
nxt = time.monotonic()
while True:
    nxt += 1.0
    pids = ra_pids()
    if not pids:
        win = None; pid = None
    else:
        try:
            if pid != pids[0] or win is None:
                pid = pids[0]
                ppid = int(open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[1])
                win = find_class()
                log.write(f"{datetime.datetime.utcnow().isoformat()}Z window {win} pid-found\n"); log.flush()
            if win:
                a = time.perf_counter()
                x, y, ww, hh = win
                im = ImageGrab.grab(bbox=(x, y, x + ww, y + hh), xdisplay=DISPLAY)
                b = time.perf_counter()
                n += 1
                name = f"f{n:06d}.jpg"
                im.convert("RGB").save(os.path.join(OUT, name), "JPEG", quality=90)
                c = time.perf_counter()
                w.writerow([f"{time.monotonic() - t0:.2f}", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z", name, f"{(b - a) * 1000:.1f}", f"{(c - b) * 1000:.1f}"]); idx.flush()
        except Exception as e:
            win = None
            log.write(f"{datetime.datetime.utcnow().isoformat()}Z error {e}\n"); log.flush()
    time.sleep(max(0.0, nxt - time.monotonic()))
