#!/usr/bin/env python3
"""H3-P1 stage-1 harness (one title per run). Reads the paths file itself; writes raw files only under
data/games/ps2/probe/<tag>/ (gitignored). Prints no path, filename or title.

usage: probe.py <tag T1|T2> <idle1_s> <idle2_s or 0> <spin 0|1>
  boot -> idle1 (P1) -> 60-s capture (P2/P4) -> idle2 (P5) -> [provoked read + spin-up] -> exit
"""
import json, os, re, signal, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path.home() / "Projects/onn-stream-test"
APP = ROOT / "runtime/emulators/pcsx2/pcsx2-v2.8.2-linux-appimage-x64-Qt.AppImage"
DATAPATH = ROOT / "data/games/ps2/config"
DEV = "sda"
HWMON = "/sys/class/hwmon/hwmon3/temp1_input"  # k10temp Tctl (sensors' source)
GPU = "/sys/class/drm/card0/device/gpu_busy_percent"


def paths():
    d = {}
    for ln in (ROOT / "runtime/h3_p1_paths.txt").read_text().splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            d[k.strip()] = v
    return d


def utc(t=None):
    t = time.time() if t is None else t
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + f".{int((t % 1) * 1000):03d}Z"


def env():
    pid = subprocess.run(["systemctl", "--user", "show", "privyhub-companion", "-p", "MainPID", "--value"],
                         capture_output=True, text=True).stdout.strip()
    e = dict(os.environ)
    for kv in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
        k, _, v = kv.decode(errors="replace").partition("=")
        if k in ("DISPLAY", "XAUTHORITY"):
            e[k] = v
    return e


ENV = env()


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, env=ENV, **kw).stdout


def tree(pid):
    out, todo = [], [pid]
    while todo:
        p = todo.pop()
        out.append(p)
        try:
            for c in Path(f"/proc/{p}/task/{p}/children").read_text().split():
                todo.append(int(c))
        except OSError:
            pass
    return out


def comm(p):
    try:
        return Path(f"/proc/{p}/comm").read_text().strip()
    except OSError:
        return None


class Sampler(threading.Thread):
    """1 Hz: gpu busy, Tctl, /sys/block/<dev>/stat, process alive."""

    def __init__(self, f, pids_fn):
        super().__init__(daemon=True)
        self.f, self.pids_fn, self.stop = f, pids_fn, False

    def run(self):
        with open(self.f, "w") as o:
            o.write("t_utc,t_rel_s,gpu_busy_pct,tctl_c,rd_ios,rd_sectors,rd_ms,in_flight,io_ms,wr_ios,emu_alive\n")
            t0 = time.time()
            while not self.stop:
                t = time.time()
                try:
                    g = Path(GPU).read_text().strip()
                except OSError:
                    g = ""
                try:
                    tc = int(Path(HWMON).read_text()) / 1000
                except OSError:
                    tc = ""
                s = Path(f"/sys/block/{DEV}/stat").read_text().split()
                alive = int(bool(self.pids_fn()))
                o.write(f"{utc(t)},{t - t0:.1f},{g},{tc},{s[0]},{s[2]},{s[3]},{s[8]},{s[9]},{s[4]},{alive}\n")
                o.flush()
                time.sleep(max(0, 1 - (time.time() - t)))


def shot(out, name):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "x11grab", "-video_size", "1920x1080", "-i",
                    ENV["DISPLAY"], "-frames:v", "1", "-vf", "scale=640:-1", str(out / f"{name}.png")],
                   env=ENV, capture_output=True)


def frame_stats(png):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(png), "-vf", "signalstats,metadata=print",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"YAVG=([\d.]+)", r.stderr + r.stdout)
    return float(m.group(1)) if m else None


def windows(pids):
    rows = []
    for p in pids:
        for w in sh(["xdotool", "search", "--onlyvisible", "--pid", str(p)]).split():
            rows.append((p, w, sh(["xdotool", "getwindowname", w]).strip()))
    return rows


def main():
    tag, idle1, idle2, spin = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] == "1"
    P = paths()
    game = os.path.join(P["GAMES_DIR"], P[tag])
    out = ROOT / "data/games/ps2/probe" / (tag.lower() + os.environ.get("H3P1_SUFFIX", ""))
    out.mkdir(parents=True, exist_ok=True)
    ev = open(out / "events.jsonl", "a")

    def log(event, **kw):
        kw = {"at_utc": utc(), "event": event, **kw}
        ev.write(json.dumps(kw) + "\n")
        ev.flush()
        print(json.dumps(kw), flush=True)

    procs = []

    def bg(name, cmd):
        f = open(out / name, "w")
        procs.append(subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, env={**ENV, "LC_ALL": "C", "S_TIME_FORMAT": "ISO"}))

    started = {"pid": None}

    def emu_pids():
        p = started["pid"]
        return [q for q in tree(p) if comm(q)] if p else []

    smp = Sampler(out / "sys_1hz.csv", emu_pids)
    smp.start()
    bg("mpstat.txt", ["mpstat", "-P", "ALL", "1"])
    bg("iostat.txt", ["iostat", "-x", "-t", "-d", DEV, "1"])
    time.sleep(3)

    t_launch = time.time()
    emu = subprocess.Popen([str(APP), "-datapath", str(DATAPATH), "-nogui", "-fullscreen",
                            "-logfile", str(out / "emulog.txt"), "--", game],
                           stdout=open(out / "emu_stdout.txt", "w"), stderr=subprocess.STDOUT, env=ENV,
                           start_new_session=True)
    started["pid"] = emu.pid
    log("launch", started_pid_comm=comm(emu.pid))

    # boot: screenshots every 3 s for 120 s; the window by PID (P0b) and the sink-input (P0c)
    p0b = p0c = None
    win = None
    for i in range(40):
        time.sleep(3)
        t = time.time() - t_launch
        shot(out, f"boot_{int(t):03d}")
        pids = emu_pids()
        if p0b is None:
            direct = sh(["xdotool", "search", "--onlyvisible", "--pid", str(emu.pid)]).split()
            if direct:
                p0b = {"hit": True, "pid_is": "started", "at_s": round(t, 1)}
                win = direct[0]
            else:
                kids = [(p, sh(["xdotool", "search", "--onlyvisible", "--pid", str(p)]).split()) for p in pids[1:]]
                kids = [(p, w) for p, w in kids if w]
                if kids:
                    p0b = {"hit": False, "found_by": "child_pid", "child_comm": comm(kids[0][0]),
                           "depth": pids.index(kids[0][0]), "at_s": round(t, 1)}
                    win = kids[0][1][0]
        if p0c is None and t > 10:
            si = sh(["pactl", "list", "sink-inputs"])
            blocks = si.split("Sink Input #")[1:]
            byp = {}
            for b in blocks:
                m = re.search(r'application\.process\.id = "(\d+)"', b)
                if m:
                    byp.setdefault(int(m.group(1)), 0)
                    byp[int(m.group(1))] += 1
            if any(p in byp for p in pids):
                p0c = {"started_pid_inputs": byp.get(emu.pid, 0),
                       "child_inputs": {comm(p): byp[p] for p in pids[1:] if p in byp}, "at_s": round(t, 1)}
        if emu.poll() is not None:
            log("emu_exited_early", rc=emu.returncode)
            break
    log("p0b", **(p0b or {"hit": False, "found_by": None}))
    log("p0c", **(p0c or {"started_pid_inputs": 0, "child_inputs": {}}))
    pids = emu_pids()
    log("tree", comms=[comm(p) for p in pids])
    emu_main = next((p for p in pids if comm(p) and "pcsx2" in comm(p).lower()), pids[-1] if pids else None)
    log("emu_main", comm=comm(emu_main) if emu_main else None)
    if emu_main:
        bg("pidstat.txt", ["pidstat", "-t", "-u", "-h", "-p", str(emu_main), "1"])
    if win:
        geo = sh(["xdotool", "getwindowgeometry", win])
        log("window", geometry=" ".join(geo.split()[3:]) if geo else None)

    def watch(seconds, label, every=60):
        t_end = time.time() + seconds
        n = 0
        while time.time() < t_end and emu.poll() is None:
            time.sleep(min(every, max(0, t_end - time.time())))
            n += 1
            shot(out, f"{label}_{n:02d}")
            w = windows(emu_pids())
            log("watch", label=label, n=n, windows=len(w), names=sorted({x[2] for x in w}))
        return emu.poll() is None

    # P1 idle
    ok = watch(idle1, "idle1")
    log("idle1_done", alive=ok)

    # P2/P4: 60-s capture at the window's native size -> mpdecimate unique frames (no video kept)
    if ok and win:
        log("capture_start")
        cmd = ["ffmpeg", "-hide_banner", "-nostats", "-f", "x11grab", "-framerate", "60", "-window_id", win,
               "-t", "60", "-i", ENV["DISPLAY"], "-map", "0", "-vf", "mpdecimate,showinfo", "-f", "null", "-"]
        if os.environ.get("H3P1_KEEP_VIDEO") == "1":  # diagnostic: a low-res copy to classify low seconds
            cmd += ["-map", "0", "-vf", "scale=480:-2", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
                    "-y", str(out / "capture_lowres.mp4")]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=open(out / "capture_showinfo.txt", "w"), env=ENV)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "x11grab", "-window_id", win, "-i", ENV["DISPLAY"],
                        "-frames:v", "1", str(out / "osd_full.png")], env=ENV, capture_output=True)
        log("capture_done")

    # P5 idle at the menu
    if idle2 and emu.poll() is None:
        ok = watch(idle2, "idle2")
        log("idle2_done", alive=ok)
    if spin and emu.poll() is None and win:
        s0 = Path(f"/sys/block/{DEV}/stat").read_text().split()
        sh(["xdotool", "windowactivate", "--sync", win])
        t_press = time.time()
        log("provoke", keys="Return,k (Start, then Cross)")
        sh(["xdotool", "key", "--window", win, "Return"])
        time.sleep(1.5)
        sh(["xdotool", "key", "--window", win, "k"])
        first = None
        t_end = time.time() + 40
        while time.time() < t_end:
            s = Path(f"/sys/block/{DEV}/stat").read_text().split()
            if first is None and int(s[0]) > int(s0[0]):
                first = time.time() - t_press
            time.sleep(0.05)
        s1 = Path(f"/sys/block/{DEV}/stat").read_text().split()
        log("provoke_result", first_read_done_s=round(first, 2) if first else None,
            reads=int(s1[0]) - int(s0[0]), read_ms=int(s1[3]) - int(s0[3]))
        shot(out, "after_provoke")

    # exit
    t_exit = time.time()
    if emu.poll() is None:
        os.kill(emu.pid, signal.SIGTERM)  # the started PID is the emulator (the AppImage runtime execs AppRun)
        try:
            emu.wait(30)
        except subprocess.TimeoutExpired:
            log("exit_timeout")
    time.sleep(2)
    left = sh(["pgrep", "-f", "pcsx2-v2.8.2"]).split()
    log("exit", rc=emu.returncode, exit_s=round(time.time() - t_exit, 1), left=len(left))
    time.sleep(3)
    smp.stop = True
    for p in procs:
        p.terminate()
    log("done")


if __name__ == "__main__":
    main()
