#!/usr/bin/env python3
"""B61: does a SAVE_STATE_SLOT sent to a RUNNING Mupen64Plus-Next hang RetroArch's main loop (its network command port
silent)? A synthetic fixture ROM (a header + a two-instruction idle loop: no game, no title), the hub's RetroArch and
N64 core, temp config / states / saves / XDG folders, the joypad driver null, no stream, no pad. Prints timings only.
    python3 b61_repro.py <repo> <workdir> [--capture] [--remap] [--content <a title, read in place>]
Run it with DISPLAY / XAUTHORITY from the companion's environment (no display = RetroArch falls back to KMS and dies).
"""
import json, os, shutil, signal, socket, struct, subprocess, sys, time
from pathlib import Path

REPO, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
CAPTURE = "--capture" in sys.argv
REMAP = "--remap" in sys.argv          # B62: a core remap in the temp config, then a 5-s run
# HOME-8 stage 1 (A): --content <file> runs a real title (read in place, never written) instead of the fixture
CONTENT = Path(sys.argv[sys.argv.index("--content") + 1]) if "--content" in sys.argv else None
APP = REPO / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORE = REPO / "runtime/emulators/retroarch/cores-linux/mupen64plus_next_libretro.so"
out = {"capture": CAPTURE, "steps": []}

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_rom

def rom() -> bytes:
    return fixture_rom.build()[0]

WORK.mkdir(parents=True, exist_ok=True)
for d in ("states", "saves", "system", "xdg/retroarch/config/Mupen64Plus-Next"):
    (WORK / d).mkdir(parents=True, exist_ok=True)
if CONTENT is None:
    romf = WORK / "fixture.z64"; romf.write_bytes(rom())
else:
    romf = CONTENT
real_opt = Path.home() / ".config/retroarch/config/Mupen64Plus-Next/Mupen64Plus-Next.opt"
opt = WORK / "xdg/retroarch/config/Mupen64Plus-Next/Mupen64Plus-Next.opt"
shutil.copyfile(real_opt, opt)                                   # read-only copy of the hub's .opt (production's)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
base = (REPO / "data/games/retroarch/config/privyhub-session.cfg").read_text()
over = {"savefile_directory": WORK / "saves", "savestate_directory": WORK / "states", "system_directory": WORK / "system",
        "network_cmd_enable": "true", "network_cmd_port": port, "input_joypad_driver": "null",
        "history_list_enable": "false", "config_save_on_exit": "false", "log_dir": WORK, "savestate_auto_save": "false",
        "savestate_auto_load": "false", "savestate_thumbnail_enable": "false"}
lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over]
lines += [f'{k} = "{v}"' for k, v in over.items()]
if REMAP:
    lines += ['auto_remaps_enable = "true"', 'remap_save_on_exit = "false"']
    rd = WORK / "xdg/retroarch/config/remaps/Mupen64Plus-Next"; rd.mkdir(parents=True, exist_ok=True)
    (rd / "Mupen64Plus-Next.rmp").write_text("".join(f'input_player{n}_btn_a = "20"\ninput_player{n}_btn_x = "23"\n'
                                                     for n in range(1, 5)))
cfg = WORK / "session.cfg"; cfg.write_text("\n".join(lines) + "\n")
env = dict(os.environ, XDG_CONFIG_HOME=str(WORK / "xdg"))
log = (WORK / "ra.log").open("w")
p = subprocess.Popen([str(APP), "--config", str(cfg), "--verbose", "-L", str(CORE), str(romf)], cwd=str(APP.parent),
                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.bind(("127.0.0.1", 0))
T0 = time.monotonic()

def cmd(c, timeout=0.5, want=None):
    t = time.monotonic(); sock.sendto(c.encode(), ("127.0.0.1", port))
    if want is False:
        return None, 0.0
    sock.settimeout(timeout)
    try:
        while True:
            data, _ = sock.recvfrom(4096)
            r = data.decode(errors="replace").strip()
            if want is None or r.startswith(want):
                return r.split(" ")[0:2], round((time.monotonic() - t) * 1000, 1)
    except socket.timeout:
        return None, round((time.monotonic() - t) * 1000, 1)

def step(name, **kw):
    kw["t_s"] = round(time.monotonic() - T0, 2); kw["step"] = name; out["steps"].append(kw); print(json.dumps(kw), flush=True)

def threads():
    rows = []
    for t in sorted(Path(f"/proc/{p.pid}/task").iterdir()) if Path(f"/proc/{p.pid}").exists() else []:
        try:
            st = (t / "stat").read_text(); name = (t / "comm").read_text().strip(); wchan = (t / "wchan").read_text().strip()
            rest = st[st.rfind(")") + 2:].split(); rows.append({"comm": name, "state": rest[0], "wchan": wchan,
                                                                  "utime": int(rest[11]), "stime": int(rest[12])})
        except OSError:
            pass
    return rows

def watch(name, seconds, every=0.25):
    """GET_STATUS every `every` s for `seconds`: the longest silent gap and the answers seen."""
    end = time.monotonic() + seconds; last_ok = time.monotonic(); gap = 0.0; seen = set(); n_ok = n_to = 0
    while time.monotonic() < end:
        r, ms = cmd("GET_STATUS", 0.25, "GET_STATUS")
        now = time.monotonic()
        if r:
            n_ok += 1; seen.add(r[1]); gap = max(gap, now - last_ok); last_ok = now
        else:
            n_to += 1
        time.sleep(max(0.0, every - (time.monotonic() - now)))
    gap = max(gap, time.monotonic() - last_ok)
    step(name, answered=n_ok, timeouts=n_to, longest_silence_s=round(gap, 2), states=sorted(seen))
    return n_to == 0 or gap < seconds * 0.9

cap = None
try:
    t = time.monotonic(); r = None
    while time.monotonic() - t < 25 and r is None:
        r, _ = cmd("GET_STATUS", 0.3, "GET_STATUS")
        if p.poll() is not None:
            break
    step("up", status=r, after_s=round(time.monotonic() - t, 2), exited=p.poll())
    if r is None or REMAP:
        time.sleep(3 if REMAP else 0)
        raise SystemExit
    time.sleep(2)
    watch("baseline_running", 3)
    if CAPTURE:
        wid = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(p.pid)], capture_output=True,
                             text=True).stdout.split()
        cap = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-f", "x11grab", "-framerate", "60", "-window_id",
                                wid[-1], "-t", "20", "-i", os.environ.get("DISPLAY", ":0"), "-vf",
                                "format=yuv420p,showinfo", "-f", "null", "-"], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL) if wid else None
        step("capture_started", window_found=bool(wid))
        time.sleep(2)
    for i in range(3):                                       # A: saves into the RUNNING core, as the hold's scratch
        r, ms = cmd("SAVE_STATE_SLOT 9", 3.0, "SAVE_STATE_SLOT")
        step(f"save_running_{i+1}", ack=r, ack_ms=ms)
        if not watch(f"after_save_running_{i+1}", 4):
            step("hung", threads=threads()); raise SystemExit
    r, ms = cmd("PAUSE_TOGGLE", want=False); time.sleep(0.3)  # B: a save while PAUSED (the user's SAVE path)
    r, ms = cmd("GET_STATUS", 0.5, "GET_STATUS"); step("paused", status=r)
    r, ms = cmd("SAVE_STATE_SLOT 9", 3.0, "SAVE_STATE_SLOT"); step("save_paused", ack=r, ack_ms=ms)
    watch("after_save_paused", 2)
    cmd("PAUSE_TOGGLE", want=False); time.sleep(0.3)
    watch("resumed", 2)
finally:
    step("threads_at_end", threads=threads())
    try:
        cmd("QUIT", want=False); cmd("QUIT", want=False); p.wait(5); how = "quit"
    except subprocess.TimeoutExpired:
        p.send_signal(signal.SIGTERM)
        try:
            p.wait(5); how = "sigterm"
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait(); how = "sigkill"
    if cap is not None and cap.poll() is None:
        cap.terminate(); cap.wait()
    step("exit", how=how, returncode=p.returncode)
    (WORK / "result.json").write_text(json.dumps(out, indent=1))
