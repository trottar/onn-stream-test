#!/usr/bin/env python3
"""B103 settle (synthetic fixtures, B61's form: RetroArch headless, the hub's AppImage, cores and base config, temp
folders, the companion's display; no game, no stream). The cheapest way to get the running game's picture about once a
second without touching the stream. Per system (PS1: the core's own per-frame word, B99's; SNES: the fixture's frame
counter $0000), six windows of WIN s each, in this order:
  none · W1 the window read in process (Pillow's X11 grab of the window's area on the display; the window found by
  xdotool as the stream finds it) · none · W2 the window read by a one-shot ffmpeg x11grab of the window (B52's
  form, 320 × 240 grey) · none · R RetroArch's own SCREENSHOT command (the PNG it writes read back and removed, as A's
  capture did).
For each window: the game's frames (the counter, read at the window's start and end only), RetroArch's CPU (its
process group, /proc), the X server's CPU, the reader's own CPU (this process; its children for ffmpeg), the wall
time of one picture (median / worst), the pictures got / asked, what was written (files, bytes) in the content folder
(RetroArch's default screenshot folder) and the log lines RetroArch added. Prints one JSON line per window.
usage: picture.py <repo> <seconds per window> [R]
Second run (R): only "none" and R per system, R reading RetroArch's own screenshot folder (`screenshots/` under its
config folder, the session's XDG_CONFIG_HOME) — the first run looked in the content folder, where nothing is
written, and got 0 of 60 (its RetroArch costs stand: RetroArch took every picture)."""
import json, os, resource, shutil, subprocess, sys, tempfile, time
from pathlib import Path
REPO = Path(sys.argv[1]); WIN = float(sys.argv[2]); ONLY_R = len(sys.argv) > 3 and sys.argv[3] == "R"
sys.path.insert(0, str(REPO / "tools")); sys.path.insert(0, str(REPO / "tests/h7_rule_search"))
import h7_minigame_proof as P, fixtures as F
from PIL import Image, ImageGrab
DISPLAY = os.environ.get("DISPLAY", ":0")
TICK = os.sysconf("SC_CLK_TCK")


def cpu_of(pids):
    total = 0
    for pid in pids:
        try:
            f = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            total += int(f[11]) + int(f[12])
        except (OSError, IndexError, ValueError):
            pass
    return total / TICK


def group(sid):
    out = []
    for d in Path("/proc").iterdir():
        if d.name.isdigit():
            try:
                if int(d.joinpath("stat").read_text().rsplit(")", 1)[1].split()[3]) == sid:  # pgrp
                    out.append(int(d.name))
            except (OSError, IndexError, ValueError):
                pass
    return out


def xorg():
    r = subprocess.run(["pgrep", "-x", "Xorg"], capture_output=True, text=True)
    return [int(x) for x in r.stdout.split()]


def window(pid):
    r = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(pid)], capture_output=True, text=True,
                       env=dict(os.environ, DISPLAY=DISPLAY))
    best = None
    for w in r.stdout.split():
        g = subprocess.run(["xdotool", "getwindowgeometry", "--shell", w], capture_output=True, text=True,
                           env=dict(os.environ, DISPLAY=DISPLAY)).stdout
        kv = dict(l.split("=", 1) for l in g.splitlines() if "=" in l)
        geo = (int(kv["X"]), int(kv["Y"]), int(kv["WIDTH"]), int(kv["HEIGHT"]))
        if best is None or geo[2] * geo[3] > best[1][2] * best[1][3]:
            best = (int(w), geo)
    return best


def counter(s, addr, n):
    a = s.ask(f"READ_CORE_RAM {addr:x} {n}", 0.5)
    p = (a or "").split()
    assert len(p) == n + 2 and int(p[1], 16) == addr, a
    return int.from_bytes(bytes(int(b, 16) for b in p[2:]), "little")


def w1(win, geo, shots):
    x, y, w, h = geo
    im = ImageGrab.grab(bbox=(x, y, x + w, y + h), xdisplay=DISPLAY)
    return im.size == (w, h)


def w2(win, geo, shots):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "x11grab", "-window_id", str(win), "-i", DISPLAY,
                        "-frames:v", "1", "-vf", "scale=320:240,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True, timeout=5, check=False, env=dict(os.environ, DISPLAY=DISPLAY))
    return r.returncode == 0 and len(r.stdout) == 320 * 240


def rshot(s, folder):
    def take(win, geo, shots):
        before = set(folder.glob("*.png"))
        s.send("SCREENSHOT")
        end = time.monotonic() + 1.0
        while time.monotonic() < end:
            new = [p for p in folder.glob("*.png") if p not in before]
            if new:
                time.sleep(0.02)
                try:
                    with Image.open(new[0]) as im:
                        im.load()
                        ok = im.size[0] > 0
                    shots.append(new[0].stat().st_size)
                    new[0].unlink()
                    return ok
                except OSError:
                    pass
            time.sleep(0.01)
        return False
    return take


def measure(s, kind, take, addr, n, wrap, win, geo, folder):
    folder.mkdir(parents=True, exist_ok=True)
    files0 = {p: p.stat().st_size for p in folder.iterdir()}
    log0 = len(s.text())
    pg, xs = group(s.proc.pid), xorg()
    ra0, x0 = cpu_of(pg), cpu_of(xs)
    me0 = time.process_time()
    ch0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    c0 = counter(s, addr, n)
    t0 = time.monotonic()
    walls, got, asked, shots = [], 0, 0, []
    k = 0
    while True:
        nxt = t0 + k * 1.0
        if nxt >= t0 + WIN:
            break
        time.sleep(max(0.0, nxt - time.monotonic()))
        if take is not None:
            a = time.perf_counter()
            ok = take(win, geo, shots)
            walls.append((time.perf_counter() - a) * 1000)
            got += bool(ok)
            asked += 1
        k += 1
    time.sleep(max(0.0, t0 + WIN - time.monotonic()))
    c1 = counter(s, addr, n)
    dt = time.monotonic() - t0
    ch1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    me = time.process_time() - me0
    ra, xx = cpu_of(group(s.proc.pid)) - ra0, cpu_of(xs) - x0
    files1 = {p: p.stat().st_size for p in folder.iterdir()}
    added = [p for p in files1 if p not in files0]
    new_log = s.text()[log0:]
    walls.sort()
    return {"window": kind, "seconds": round(dt, 2), "frames": (c1 - c0) % wrap,
            "frames_per_s": round(((c1 - c0) % wrap) / dt, 3),
            "retroarch_cpu_s": round(ra, 2), "xorg_cpu_s": round(xx, 2),
            "reader_cpu_s": round(me + (ch1.ru_utime + ch1.ru_stime) - (ch0.ru_utime + ch0.ru_stime), 3),
            "pictures": [got, asked],
            "picture_ms_median": round(walls[len(walls) // 2], 1) if walls else None,
            "picture_ms_worst": round(walls[-1], 1) if walls else None,
            "files_left": len(added), "screenshots_written": len(shots), "screenshot_bytes_median":
                (sorted(shots)[len(shots) // 2] if shots else 0),
            "log_lines_added": len([l for l in new_log.splitlines() if l.strip()]),
            "log_screenshot_lines": len([l for l in new_log.splitlines() if "creenshot" in l])}


SPEC = {"ps1": ("Made Up.exe", F.psx_exe, 0x44EE0, 4, 1 << 32), "snes": ("Made Up.sfc", F.snes, 0x0000, 2, 1 << 16)}
tmp = Path(tempfile.mkdtemp(prefix="b103_settle_", dir=os.environ.get("TMPDIR")))
try:
    for system, (name, build, addr, n, wrap) in SPEC.items():
        content = tmp / system
        content.mkdir()
        rom = content / name
        rom.write_bytes(build())
        s = P.Session(rom, system, tmp / f"{system}_work")
        try:
            s.wait_playing()
            time.sleep(2.0)
            win, geo = window(s.proc.pid)
            print(json.dumps({"system": system, "window_size": [geo[2], geo[3]]}), flush=True)
            shots = s.work / "xdg" / "retroarch" / "screenshots"        # RetroArch's own screenshot folder
            plan = ((("none", None), ("R_retroarch_screenshot", rshot(s, shots))) if ONLY_R else
                    (("none", None), ("W1_window_read_in_process", w1), ("none", None),
                     ("W2_window_read_ffmpeg_one_shot", w2), ("none", None),
                     ("R_retroarch_screenshot", rshot(s, content))))
            for kind, take in plan:
                folder = shots if (ONLY_R and take is not None) else content
                print(json.dumps({"system": system, **measure(s, kind, take, addr, n, wrap, win, geo, folder)}),
                      flush=True)
        finally:
            s.close()
            time.sleep(0.5)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
r = subprocess.run(["pgrep", "-c", "-f", "RetroArch-Linux"], capture_output=True, text=True)
print(json.dumps({"retroarch_left": int((r.stdout or "0").strip() or 0)}), flush=True)
