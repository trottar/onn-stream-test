#!/usr/bin/env python3
"""H2-P1 harness (one title, one run). Reads the paths file itself; writes raw files only under
data/games/gamecube/probe/<tag>_r<run>/ (gitignored). Prints no path, filename, title or window name.

usage: gc_probe.py <T1|T2> <run 1|2> <idle1_s> <idle2_s or 0> <spin 0|1>
  launch -> boot (P0b / P0c, 120 s of screenshots) -> idle1 (P1; the first-span capture for M4 runs from the window
  to here) -> P0e (pause / resume) -> P0f (save / load) -> the 60-s capture (P2 / P4) -> idle2 (P5)
  -> [provoked read + spin-up] -> exit (SIGTERM, SIGKILL after 5 s)
"""
import hashlib, json, os, re, signal, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path.home() / "Projects/onn-stream-test"
APP = ROOT / "runtime/emulators/dolphin/dolphin-2609b-x64.AppImage"
USER = ROOT / "data/games/gamecube/user"
DEV = "sda"
HWMON = "/sys/class/hwmon/hwmon3/temp1_input"  # k10temp Tctl
GPU = "/sys/class/drm/card0/device/gpu_busy_percent"
BLACK_Y = 24.0


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


def comm(p, t=None):
    try:
        return Path(f"/proc/{p}/task/{t}/comm" if t else f"/proc/{p}/comm").read_text().strip()
    except OSError:
        return None


def threads(pid):
    try:
        return {int(t): comm(pid, t) for t in os.listdir(f"/proc/{pid}/task")}
    except OSError:
        return {}


def ticks(pid, tid):
    try:
        f = Path(f"/proc/{pid}/task/{tid}/stat").read_text().rsplit(")", 1)[1].split()
        return int(f[11]) + int(f[12])
    except OSError:
        return None


def dstat():
    return Path(f"/sys/block/{DEV}/stat").read_text().split()


class Sampler(threading.Thread):
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
                s = dstat()
                alive = int(bool(self.pids_fn()))
                o.write(f"{utc(t)},{t - t0:.1f},{g},{tc},{s[0]},{s[2]},{s[3]},{s[8]},{s[9]},{s[4]},{alive}\n")
                o.flush()
                time.sleep(max(0, 1 - (time.time() - t)))


def shot(out, name, win=None, full=False):
    src = ["-window_id", win] if win else ["-video_size", "1920x1080"]
    vf = [] if full else ["-vf", "scale=640:-1"]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "x11grab", *src, "-i", ENV["DISPLAY"],
                    "-frames:v", "1", *vf, str(out / f"{name}.png")], env=ENV, capture_output=True)


def hname(s):
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def windows(pids, visible=True):
    rows = []
    for p in pids:
        for w in sh(["xdotool", "search", *(["--onlyvisible"] if visible else []), "--pid", str(p)]).split():
            geo = " ".join(sh(["xdotool", "getwindowgeometry", w]).split()[3:])
            rows.append({"pid_depth": pids.index(p), "wid": w, "geo": geo,
                         "name_h": hname(sh(["xdotool", "getwindowname", w]).strip())})
    return rows


def area(geo):
    m = re.search(r"(\d+)x(\d+)", geo or "")
    return int(m.group(1)) * int(m.group(2)) if m else 0


def grab_check(src, seconds, fps, path):
    """B52's picture check: frames' checksum and Y mean over `seconds` -> distinct non-black frames."""
    subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "x11grab", "-framerate", str(fps), *src,
                    "-t", str(seconds), "-i", ENV["DISPLAY"], "-vf", "format=yuv420p,showinfo", "-f", "null", "-"],
                   stdout=subprocess.DEVNULL, stderr=open(path, "w"), env=ENV)
    fr = []
    for ln in open(path, errors="replace"):
        m = re.search(r"pts_time:([\d.]+).*?checksum:([0-9A-Fa-f]+).*?mean:\[(\d+)", ln)
        if m:
            fr.append((float(m.group(1)), m.group(2), float(m.group(3))))
    if not fr:
        return {"frames": 0}
    t0 = fr[0][0]
    first3 = None
    seen = set()
    for t, c, y in fr:
        if y > BLACK_Y and c not in seen:
            seen.add(c)
            if len(seen) == 3 and first3 is None:
                first3 = round(t - t0, 2)
    return {"frames": len(fr), "distinct_nonblack": len(seen), "third_distinct_at_s": first3,
            "black_frames": sum(y <= BLACK_Y for _, _, y in fr)}


def key(win, *keys, hold=0.12):
    sh(["xdotool", "windowactivate", "--sync", win])
    sh(["xdotool", "windowfocus", "--sync", win])
    sh(["xdotool", "keydown", *keys])
    time.sleep(hold)
    sh(["xdotool", "keyup", *reversed(keys)])


def main():
    tag, run, idle1, idle2, spin = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5] == "1"
    P = paths()
    titles = json.loads((ROOT / "data/games/gamecube/probe/titles.json").read_text())
    game = os.path.join(P["GAMECUBE_DIR"], titles[tag])
    out = ROOT / "data/games/gamecube/probe" / f"{tag.lower()}_r{run}"
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
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT,
                             env={**ENV, "LC_ALL": "C", "S_TIME_FORMAT": "ISO"})
        procs.append(p)
        return p

    started = {"pid": None}

    def emu_pids():
        p = started["pid"]
        return [q for q in tree(p) if comm(q)] if p else []

    # the Dolphin render-time log and the file log start fresh each run
    logs = USER / "Logs"
    for f in ("render_times.txt", "vblank_times.txt", "dolphin.log"):
        if (logs / f).exists():
            (logs / f).rename(logs / f"{f}.prev")
    smp = Sampler(out / "sys_1hz.csv", emu_pids)
    smp.start()
    bg("mpstat.txt", ["mpstat", "-P", "ALL", "1"])
    bg("iostat.txt", ["iostat", "-x", "-t", "-d", DEV, "1"])
    time.sleep(3)

    t_launch = time.time()
    emu = subprocess.Popen([str(APP), "-b", "-u", str(USER), "-e", game], cwd=str(USER),
                           stdout=open(out / "emu_stdout.txt", "w"), stderr=subprocess.STDOUT, env=ENV,
                           start_new_session=True)
    started["pid"] = emu.pid
    log("launch", run=run)
    time.sleep(1.0)
    log("started_pid", comm=comm(emu.pid), tree=[comm(p) for p in emu_pids()])

    p0b = p0c = None
    win = None
    src = None
    first = None
    for i in range(40):
        time.sleep(3)
        t = time.time() - t_launch
        shot(out, f"boot_{int(t):03d}")
        pids = emu_pids()
        if p0b is None:
            direct = windows([emu.pid])
            if direct:
                best = max(direct, key=lambda r: area(r["geo"]))
                p0b = {"hit": True, "pid_is": "started", "comm": comm(emu.pid), "visible_windows": len(direct),
                       "geo": best["geo"], "at_s": round(t, 1)}
                win = best["wid"]
            else:
                kids = [r for r in windows(pids) if r["pid_depth"] > 0]
                if kids:
                    best = max(kids, key=lambda r: area(r["geo"]))
                    p0b = {"hit": False, "found_by": "child_pid", "depth": best["pid_depth"], "geo": best["geo"],
                           "at_s": round(t, 1)}
                    win = best["wid"]
            if p0b is None and i in (3, 9, 19):
                log("no_visible_window_yet", at_s=round(t, 1), hidden=len(windows(pids, visible=False)))
            if win and first is None:
                time.sleep(2)  # let the window settle into fullscreen before the first-span capture
                geo = " ".join(sh(["xdotool", "getwindowgeometry", win]).split()[3:])
                full = "1920x1080" in geo
                src = ["-video_size", "1920x1080"] if full else ["-window_id", win]
                log("capture_source", fullscreen=full, geo=geo)
                first = subprocess.Popen(["ffmpeg", "-hide_banner", "-nostats", "-f", "x11grab", "-framerate", "60",
                                          *src, "-i", ENV["DISPLAY"], "-vf", "format=yuv420p,showinfo", "-f", "null",
                                          "-"], stdout=subprocess.DEVNULL, stderr=open(out / "first_showinfo.txt", "w"),
                                         env=ENV)
                log("first_span_start", at_s=round(time.time() - t_launch, 1))
        if p0c is None and t > 10:
            si = sh(["pactl", "list", "sink-inputs"])
            byp = {}
            for b in si.split("Sink Input #")[1:]:
                m = re.search(r'application\.process\.id = "(\d+)"', b)
                if m:
                    byp[int(m.group(1))] = byp.get(int(m.group(1)), 0) + 1
            if any(p in byp for p in pids):
                p0c = {"started_pid_inputs": byp.get(emu.pid, 0),
                       "child_inputs": sum(byp.get(p, 0) for p in pids[1:]), "at_s": round(t, 1)}
        if emu.poll() is not None:
            log("emu_exited_early", rc=emu.returncode)
            break
        if p0b is None and t > 30:
            log("abort_no_window", at_s=round(t, 1), hidden=len(windows(pids, visible=False)))
            idle1 = idle2 = 0
            spin = False
            break
    log("p0b", **(p0b or {"hit": False, "found_by": None}))
    log("p0c", **(p0c or {"started_pid_inputs": 0, "child_inputs": 0}))
    pids = emu_pids()
    log("tree", comms=[comm(p) for p in pids])
    th = threads(emu.pid)
    names = sorted(set(th.values()))
    log("threads", n=len(th), names=names, llvmpipe=sum("llvmpipe" in (n or "") for n in th.values()))
    cpu_tid = next((t for t, n in sorted(th.items()) if n and n.lower().startswith("cpu")), None)
    log("cpu_thread", name=th.get(cpu_tid))
    bg("pidstat.txt", ["pidstat", "-t", "-u", "-h", "-p", str(emu.pid), "1"])

    def watch(seconds, label, every=60):
        t_end = time.time() + seconds
        n = 0
        while time.time() < t_end and emu.poll() is None:
            time.sleep(min(every, max(0, t_end - time.time())))
            n += 1
            shot(out, f"{label}_{n:02d}")
            w = windows(emu_pids())
            log("watch", label=label, n=n, windows=len(w), name_hashes=sorted({x["name_h"] for x in w}))
        return emu.poll() is None

    # P1: idle at the menu (the boot loop's 120 s count toward it)
    ok = watch(max(0, idle1 - (time.time() - t_launch - 3)), "idle1")
    log("idle1_done", alive=ok, since_launch_s=round(time.time() - t_launch, 1))
    if first:
        first.send_signal(signal.SIGINT)
        first.wait(10)
        log("first_span_end", at_s=round(time.time() - t_launch, 1))

    def standing(tid, window=0.5, limit=1.5, want_stand=True):
        """poll the thread's CPU ticks every 0.05 s; return the seconds until a `window` with no growth (or with
        growth, want_stand False), or None within `limit`."""
        t0 = time.time()
        hist = []
        while time.time() - t0 < limit + window:
            hist.append((time.time() - t0, ticks(emu.pid, tid)))
            for j in reversed(range(len(hist))):
                if hist[-1][0] - hist[j][0] >= window:
                    a, b = hist[j][1], hist[-1][1]
                    if a is not None and b is not None and ((b == a) if want_stand else (b - a) >= 3):
                        start = hist[j][0]
                        if start <= limit:
                            return round(start if want_stand else hist[-1][0], 2)
                    break
            time.sleep(0.05)
        return None

    # P0e: pause / resume by the hotkey, confirmed by the CPU thread's time
    p0e = {"cpu_thread": th.get(cpu_tid)}
    if ok and win and cpu_tid:
        a = ticks(emu.pid, cpu_tid); time.sleep(1); b = ticks(emu.pid, cpu_tid)
        p0e["running_ticks_per_s"] = b - a
        tp = time.time()
        key(win, "F10")
        p0e["hotkey_pause_stand_s"] = standing(cpu_tid)
        if p0e["hotkey_pause_stand_s"] is not None:
            shot(out, "paused_a", full=True); time.sleep(0.5); shot(out, "paused_b", full=True)
            p0e["paused_picture_same"] = (out / "paused_a.png").read_bytes() == (out / "paused_b.png").read_bytes()
            time.sleep(2)
            key(win, "F10")
            p0e["hotkey_resume_grow_s"] = standing(cpu_tid, want_stand=False)
            p0e["method"] = "hotkey" if p0e["hotkey_resume_grow_s"] is not None else "hotkey_pause_only"
        if p0e.get("method") != "hotkey":
            if p0e["hotkey_pause_stand_s"] is None:
                time.sleep(1)
            os.kill(emu.pid, signal.SIGSTOP)
            p0e["sigstop_stand_s"] = standing(cpu_tid)
            time.sleep(2)
            os.kill(emu.pid, signal.SIGCONT)
            p0e["sigcont_grow_s"] = standing(cpu_tid, want_stand=False)
            if p0e["sigcont_grow_s"] is None and p0e.get("hotkey_pause_stand_s") is not None:
                key(win, "F10")  # a paused emulator left by a half-working hotkey is resumed
                p0e["extra_resume_grow_s"] = standing(cpu_tid, want_stand=False)
            p0e["method"] = "sigstop"
        a = ticks(emu.pid, cpu_tid); time.sleep(1); b = ticks(emu.pid, cpu_tid)
        p0e["after_ticks_per_s"] = b - a
    log("p0e", **p0e)
    time.sleep(3)

    # P0f: a save and a load by hotkey (slot 1)
    p0f = {}
    sdir = USER / "StateSaves"
    if emu.poll() is None and win:
        before = {f.name: f.stat().st_mtime for f in sdir.glob("*.s01")} if sdir.exists() else {}
        tp = time.time()
        key(win, "Shift_L", "F1")
        seen = None
        last = None
        stable_since = None
        while time.time() - tp < 10:
            fs = [f for f in sdir.glob("*.s01")] if sdir.exists() else []
            fs = [f for f in fs if f.stat().st_mtime > tp - 0.05]
            if fs:
                f = fs[0]
                cur = (f.stat().st_size, f.stat().st_mtime)
                if seen is None:
                    seen = time.time() - tp
                if cur != last:
                    last, stable_since = cur, time.time()
                elif time.time() - stable_since >= 0.5:
                    p0f.update(save_file_seen_s=round(seen, 2), save_stable_s=round(stable_since - tp, 2),
                               save_mib=round(cur[0] / 2**20, 1), save_ok=True,
                               slot_existed_before=bool(before))
                    break
            time.sleep(0.05)
        else:
            p0f["save_ok"] = False
        time.sleep(3)
        shot(out, "before_load", full=True)
        tp = time.time()
        key(win, "F1")
        pc = grab_check(src or ["-window_id", win], 5, 10, out / "load_showinfo.txt")
        p0f.update(load_picture=pc, load_ok=bool(pc.get("third_distinct_at_s") is not None
                                                 and pc["third_distinct_at_s"] <= 5),
                   load_check_from_press_s=round(time.time() - tp, 2))
        shot(out, "after_load", full=True)
    log("p0f", **p0f)
    time.sleep(5)

    # P2 / P4: the 60-s capture (the window or the screen it fills), every frame's checksum and Y mean
    if emu.poll() is None and win:
        shot(out, "osd_full_before", full=True)
        log("capture_start")
        subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "x11grab", "-framerate", "60", *src, "-t", "60",
                        "-i", ENV["DISPLAY"], "-vf", "format=yuv420p,showinfo", "-f", "null", "-"],
                       stdout=subprocess.DEVNULL, stderr=open(out / "capture_showinfo.txt", "w"), env=ENV)
        shot(out, "osd_full_after", full=True)
        log("capture_done")

    # P5: the idle at the menu
    if idle2 and emu.poll() is None:
        s0 = dstat()
        ok = watch(idle2, "idle2")
        s1 = dstat()
        log("idle2_done", alive=ok, reads_in_idle=int(s1[0]) - int(s0[0]))
    if spin and emu.poll() is None and win:
        s0 = dstat()
        t_press = time.time()
        log("provoke", keys="Return (Start), then x (A) twice")
        key(win, "Return")
        time.sleep(1.5)
        key(win, "x")
        time.sleep(1.5)
        key(win, "x")
        firstr = None
        t_end = t_press + 40
        while time.time() < t_end:
            s = dstat()
            if firstr is None and int(s[0]) > int(s0[0]):
                firstr = time.time() - t_press
            time.sleep(0.05)
        s1 = dstat()
        log("provoke_result", first_read_done_s=round(firstr, 2) if firstr else None,
            reads=int(s1[0]) - int(s0[0]), read_ms=int(s1[3]) - int(s0[3]))
        shot(out, "after_provoke")

    # exit
    t_exit = time.time()
    rc = emu.poll()
    if rc is None:
        os.kill(emu.pid, signal.SIGTERM)
        try:
            emu.wait(5)
            how = "sigterm"
        except subprocess.TimeoutExpired:
            os.kill(emu.pid, signal.SIGKILL)
            emu.wait(10)
            how = "sigkill"
    else:
        how = "already_exited"
    t_gone = round(time.time() - t_exit, 2)
    time.sleep(2)
    left = sh(["pgrep", "-f", "dolphin-2609b"]).split()
    time.sleep(3)
    left5 = sh(["pgrep", "-f", "dolphin-2609b"]).split()
    log("exit", how=how, rc=emu.returncode, exit_s=t_gone, left=len(left), left_5s=len(left5))
    smp.stop = True
    for p in procs:
        p.terminate()
    for f in ("render_times.txt", "vblank_times.txt", "dolphin.log"):
        if (logs / f).exists():
            os.replace(logs / f, out / f)
    log("done")


if __name__ == "__main__":
    main()
