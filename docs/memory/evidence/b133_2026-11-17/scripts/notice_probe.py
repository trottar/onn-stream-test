#!/usr/bin/env python3
"""B133 settle 2 (B61's form: the hub's RetroArch and N64 core on B61's synthetic ROM — no game, no title; temp
config / states / saves / XDG folders, a read-only copy of the hub's .opt, the joypad driver null; no stream, no pad):
do RetroArch's notices run out while the core is PAUSED? A state saved while running (its notice is let run out), the
core paused, the state loaded while paused (RetroArch's "loaded" notice), then the window grabbed by its id (the
stream's grab) every 0.5 s for 20 s still paused, then released and grabbed 12 s more. Measured: the share of bright
pixels (all channels > 200) in the window's lower-left quarter, where RetroArch draws its notices. Numbers only; the
frames are not kept. usage (DISPLAY / XAUTHORITY from the companion's environment): notice_probe.py <repo> <workdir>"""
import json, os, shutil, signal, socket, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image
REPO, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
APP = REPO / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORE = REPO / "runtime/emulators/retroarch/cores-linux/mupen64plus_next_libretro.so"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_rom
for d in ("states", "saves", "system", "xdg/retroarch/config/Mupen64Plus-Next", "frames"):
    (WORK / d).mkdir(parents=True, exist_ok=True)
romf = WORK / "fixture.z64"; romf.write_bytes(fixture_rom.build()[0])
shutil.copyfile(Path.home() / ".config/retroarch/config/Mupen64Plus-Next/Mupen64Plus-Next.opt",
                WORK / "xdg/retroarch/config/Mupen64Plus-Next/Mupen64Plus-Next.opt")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
base = (REPO / "data/games/retroarch/config/privyhub-session.cfg").read_text()
over = {"savefile_directory": WORK / "saves", "savestate_directory": WORK / "states", "system_directory": WORK / "system",
        "network_cmd_enable": "true", "network_cmd_port": port, "input_joypad_driver": "null",
        "history_list_enable": "false", "config_save_on_exit": "false", "log_dir": WORK, "savestate_auto_save": "false",
        "savestate_auto_load": "false", "savestate_thumbnail_enable": "false"}
lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over] + [f'{k} = "{v}"' for k, v in over.items()]
cfg = WORK / "session.cfg"; cfg.write_text("\n".join(lines) + "\n")
env = dict(os.environ, XDG_CONFIG_HOME=str(WORK / "xdg"))
log = (WORK / "ra.log").open("w")
p = subprocess.Popen([str(APP), "--config", str(cfg), "--verbose", "-L", str(CORE), str(romf)], cwd=str(APP.parent),
                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.bind(("127.0.0.1", 0))
out = {"steps": []}; T0 = time.monotonic()
def cmd(c, timeout=0.5, want=None):
    sock.sendto(c.encode(), ("127.0.0.1", port))
    if want is False:
        return None
    sock.settimeout(timeout)
    try:
        while True:
            r = sock.recvfrom(4096)[0].decode(errors="replace").strip()
            if want is None or r.startswith(want):
                return r
    except socket.timeout:
        return None
def step(name, **kw):
    kw["t_s"] = round(time.monotonic() - T0, 2); kw["step"] = name; out["steps"].append(kw); print(json.dumps(kw), flush=True)
WID = [None]
def bright():
    if WID[0] is None:
        ids = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(p.pid)], capture_output=True, text=True).stdout.split()
        WID[0] = ids[-1] if ids else None
    f = WORK / "frames" / "g.png"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab", "-framerate", "60", "-draw_mouse", "0",
                    "-window_id", WID[0], "-i", os.environ.get("DISPLAY", ":0"), "-frames:v", "1", "-y", str(f)],
                   capture_output=True, timeout=20)
    a = np.asarray(Image.open(f).convert("RGB")).astype(int)
    h, w, _ = a.shape
    q = a[h // 2:, : w // 2]
    return round(float(((q > 200).all(axis=2)).mean()), 5), [w, h]
def series(name, seconds, every=0.5):
    vals = []; end = time.monotonic() + seconds; t1 = time.monotonic()
    while time.monotonic() < end:
        b, size = bright(); st = cmd("GET_STATUS", 0.3, "GET_STATUS")
        vals.append([round(time.monotonic() - t1, 1), b, (st or "").split(" ")[1] if st else None])
        time.sleep(max(0.0, every - 0.2))
    step(name, size=size, reads=vals)
try:
    t = time.monotonic(); r = None
    while time.monotonic() - t < 25 and r is None:
        r = cmd("GET_STATUS", 0.3, "GET_STATUS")
        if p.poll() is not None:
            break
    step("up", status=(r or "").split(" ")[1] if r else None, after_s=round(time.monotonic() - t, 2))
    if r is None:
        raise SystemExit
    series("running_from_start", 10)                        # the launch's own notices, running
    step("save_running", ack=cmd("SAVE_STATE_SLOT 1", 3.0, "SAVE_STATE_SLOT"))
    series("running_after_save", 10)                        # the save's notice, running: does it run out
    cmd("PAUSE_TOGGLE", want=False); time.sleep(0.5)
    series("paused_before_load", 2)
    step("load_paused", ack=cmd("LOAD_STATE_SLOT 1", 3.0, "LOAD_STATE_SLOT"))
    series("paused_after_load", 20)                         # the load's notice, paused: does it run out
    cmd("PAUSE_TOGGLE", want=False); time.sleep(0.3)
    series("released_after_load", 12)
finally:
    try:
        cmd("QUIT", want=False); cmd("QUIT", want=False); p.wait(5); how = "quit"
    except subprocess.TimeoutExpired:
        p.send_signal(signal.SIGTERM)
        try:
            p.wait(5); how = "sigterm"
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait(); how = "sigkill"
    step("exit", how=how, returncode=p.returncode)
    (WORK / "result.json").write_text(json.dumps(out, indent=1))
