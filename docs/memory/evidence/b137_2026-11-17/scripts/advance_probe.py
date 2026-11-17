#!/usr/bin/env python3
"""B137 settle (B61's form, disclosed: the hub's RetroArch and N64 core on a made-up fixture ROM — no game, no title;
temp config / states / saves / system / XDG folders, a read-only copy of the hub's Mupen64Plus-Next .opt, the joypad
driver null; no stream, no real pad). The fixture (`fixture_counter_rom.py`) draws a frame counter as its colour and
pad 1's buttons as a bottom bar, read through the PIF; RetroArch's network remote stands in for a pad (port 1).

Asked: a state loaded into a PAUSED core — does the window then show it? After RetroArch's FRAMEADVANCE on the command
port: does the window show the loaded state, does GET_STATUS stay PAUSED, how many frames until the picture is the
loaded one, does the core read the pads in those frames? How do back-to-back FRAMEADVANCE commands count?

Numbers only; no frame kept. usage (DISPLAY / XAUTHORITY from the companion's environment):
  advance_probe.py <repo> <workdir>"""
import json, os, shutil, signal, socket, struct, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image
REPO, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
APP = REPO / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
SYSTEM = sys.argv[3] if len(sys.argv) > 3 else "n64"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_counter_rom as fx
if SYSTEM == "ps1":                     # the hub's PS1 core on a made-up PS-EXE (its built-in OpenBIOS: no BIOS file)
    import fixture_counter_psexe as fxp
    CORE = REPO / "runtime/emulators/retroarch/cores-linux/mednafen_psx_hw_libretro.so"
    FOLDER, EXT, BUILD = "Beetle PSX HW", "exe", fxp.build
    LEVELS = tuple(int(x) for x in sys.argv[4].split(",")) if len(sys.argv) > 4 else (0, 80, 160, 240)
else:
    CORE = REPO / "runtime/emulators/retroarch/cores-linux/mupen64plus_next_libretro.so"
    FOLDER, EXT, BUILD, LEVELS = "Mupen64Plus-Next", "z64", fx.build, fx.LEVELS
for d in ("states", "saves", "system", f"xdg/retroarch/config/{FOLDER}", "frames"):
    (WORK / d).mkdir(parents=True, exist_ok=True)
romf = WORK / f"fixture.{EXT}"; romf.write_bytes(BUILD()[0])
shutil.copyfile(Path.home() / f".config/retroarch/config/{FOLDER}/{FOLDER}.opt",
                WORK / f"xdg/retroarch/config/{FOLDER}/{FOLDER}.opt")
if SYSTEM == "ps1" and os.environ.get("B137_PS1_SKIP_BIOS") == "1":     # the temp copy only
    o = WORK / f"xdg/retroarch/config/{FOLDER}/{FOLDER}.opt"
    o.write_text(o.read_text().replace('beetle_psx_hw_skip_bios = "disabled"', 'beetle_psx_hw_skip_bios = "enabled"'))


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close()
    return p


port, rport = free_port(), free_port()
base = (REPO / "data/games/retroarch/config/privyhub-session.cfg").read_text()
over = {"savefile_directory": WORK / "saves", "savestate_directory": WORK / "states", "system_directory": WORK / "system",
        "network_cmd_enable": "true", "network_cmd_port": port, "input_joypad_driver": "null",
        "network_remote_enable": "true", "network_remote_enable_user_p1": "true", "network_remote_base_port": rport,
        "history_list_enable": "false", "config_save_on_exit": "false", "log_dir": WORK, "savestate_auto_save": "false",
        "savestate_auto_load": "false", "savestate_thumbnail_enable": "false"}
lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over] + [f'{k} = "{v}"' for k, v in over.items()]
cfg = WORK / "session.cfg"; cfg.write_text("\n".join(lines) + "\n")
env = dict(os.environ, XDG_CONFIG_HOME=str(WORK / "xdg"))
log = (WORK / "ra.log").open("w")
p = subprocess.Popen([str(APP), "--config", str(cfg), "--verbose", "-L", str(CORE), str(romf)], cwd=str(APP.parent),
                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.bind(("127.0.0.1", 0))
rsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
out = {"steps": []}; T0 = time.monotonic()
ORDER = ["<"]


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


def status():
    r = cmd("GET_STATUS", 0.4, "GET_STATUS")
    return (r or "").split(" ")[1] if r else None


def remote(down):
    """RetroArch's network remote, user 1: RetroPad B, Y, A, X, Up held (down) or released."""
    for bid in (0, 1, 8, 9, 4):
        rsock.sendto(struct.pack(ORDER[0] + "iiiiHxx", 0, 1, 0, bid, 1 if down else 0), ("127.0.0.1", rport))


def step(name, **kw):
    kw["t_s"] = round(time.monotonic() - T0, 2); kw["step"] = name; out["steps"].append(kw); print(json.dumps(kw), flush=True)


WID = [None]
ARR, KEPT = [None], {}          # the last picture (in memory only) and the kept ones by step, for the comparisons


def mad(x, y):
    """the mean absolute difference of two pictures (0-255), the notice corners left out"""
    h, w, _ = x.shape
    sl = (slice(int(h * 0.08), int(h * 0.9)), slice(int(w * 0.02), int(w * 0.85)))
    return round(float(np.abs(x[sl].astype(int) - y[sl].astype(int)).mean()), 2)


def read():
    """-> {counter, bar (bottom-right brightness 0-1), notice (bright share, lower-left)} of one grab by window id."""
    if WID[0] is None:
        ids = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(p.pid)], capture_output=True, text=True).stdout.split()
        WID[0] = ids[-1] if ids else None
    f = WORK / "frames" / "g.png"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab", "-framerate", "60", "-draw_mouse", "0",
                    "-window_id", WID[0], "-i", os.environ.get("DISPLAY", ":0"), "-frames:v", "1", "-y", str(f)],
                   capture_output=True, timeout=20)
    a = np.asarray(Image.open(f).convert("RGB")).astype(int)
    h, w, _ = a.shape
    top = a[int(h * 0.15):int(h * 0.55), int(w * 0.55):int(w * 0.9)].reshape(-1, 3)
    med = [int(np.median(top[:, k])) for k in range(3)]
    bar = a[int(h * 0.82):int(h * 0.97), int(w * 0.6):int(w * 0.95)]
    q = a[h // 2:, : w // 2]
    ARR[0] = a.astype(np.uint8)
    return {"counter": fx.decode(med, LEVELS), "rgb": med, "bar": round(float(bar.mean()) / 255, 3),
            "notice": round(float(((q > 200).all(axis=2)).mean()), 5), "size": [w, h]}


def look(name, **kw):
    r = read(); r.update(kw); r["status"] = status()
    key = name + (f"_{kw['n']}" if "n" in kw else "")
    KEPT[key] = ARR[0]
    if "paused_after_save" in KEPT and "paused_before_load" in KEPT and key not in ("paused_after_save", "paused_before_load"):
        r["mad_vs_saved"] = mad(ARR[0], KEPT["paused_after_save"])
        r["mad_vs_preload"] = mad(ARR[0], KEPT["paused_before_load"])
    step(name, **r); return r


try:
    t = time.monotonic(); r = None
    while time.monotonic() - t < 25 and r is None:
        r = cmd("GET_STATUS", 0.3, "GET_STATUS")
        if p.poll() is not None:
            break
    step("up", status=(r or "").split(" ")[1] if r else None, after_s=round(time.monotonic() - t, 2))
    if r is None:
        raise SystemExit
    time.sleep(3.0)
    a1 = look("running_1"); time.sleep(1.0); a2 = look("running_2")
    step("running_rate", frames_per_s_mod64=(a2["counter"] - a1["counter"]) % 64)
    # the network remote works at all (running): the bar white while held
    remote(True); time.sleep(0.5); look("running_remote_held")
    rh = out["steps"][-1]["bar"]
    if rh < 0.5:                                  # the other byte order
        remote(False); ORDER[0] = ">"; remote(True); time.sleep(0.5); look("running_remote_held_be")
    remote(False); time.sleep(0.5); look("running_remote_released")
    cmd("PAUSE_TOGGLE", want=False); time.sleep(0.6)
    s1 = look("paused_1"); time.sleep(0.6); look("paused_2")
    step("save_paused", ack=cmd("SAVE_STATE_SLOT 1", 3.0, "SAVE_STATE_SLOT"))
    time.sleep(3.2)                                       # the save's notice runs out
    look("paused_after_save")
    cmd("PAUSE_TOGGLE", want=False); time.sleep(3.0)      # runs on: the counter moves away from the saved one
    cmd("PAUSE_TOGGLE", want=False); time.sleep(0.6)
    pre = look("paused_before_load")
    step("load_paused", ack=cmd("LOAD_STATE_SLOT 1", 3.0, "LOAD_STATE_SLOT"))
    for k in range(4):
        time.sleep(0.5); look("paused_after_load", n=k)
    # one FRAMEADVANCE at a time, a picture and the status after each
    for k in range(1, 6):
        cmd("FRAMEADVANCE", want=False); time.sleep(0.4)
        look("after_advance", n=k, from_saved=None)
        out["steps"][-1]["from_saved"] = (out["steps"][-1]["counter"] - s1["counter"]) % 64
    # GET_STATUS and the window for 4 s after: still paused, the notices run out
    for k in range(8):
        time.sleep(0.5); look("paused_after_advances", n=k)
    # back-to-back advances: how do they count
    for gap in (0.002, 0.020, 0.050, 0.100):
        b0 = read()["counter"]
        for _ in range(5):
            cmd("FRAMEADVANCE", want=False); time.sleep(gap)
        time.sleep(0.4)
        b1 = look("burst_of_5", gap_s=gap)
        out["steps"][-1]["frames_run"] = (b1["counter"] - b0) % 64
    # the pads during an advance: held while paused (nothing runs), then one advance with it held, then released
    remote(True); time.sleep(0.6); look("paused_remote_held_no_advance")
    cmd("FRAMEADVANCE", want=False); time.sleep(0.4); look("advance_with_remote_held")
    remote(False); time.sleep(0.3); look("paused_remote_released_no_advance")
    cmd("FRAMEADVANCE", want=False); time.sleep(0.4); look("advance_with_remote_released")
    # a pad held while the state is loaded into the paused core (no advance): does the load itself read it
    cmd("PAUSE_TOGGLE", want=False); time.sleep(1.3); cmd("PAUSE_TOGGLE", want=False); time.sleep(0.6)
    look("paused_before_held_load")
    remote(True); time.sleep(0.4)
    step("load_paused_remote_held", ack=cmd("LOAD_STATE_SLOT 1", 3.0, "LOAD_STATE_SLOT"))
    time.sleep(0.6); look("after_held_load")
    out["steps"][-1]["from_saved"] = (out["steps"][-1]["counter"] - s1["counter"]) % 64
    remote(False); time.sleep(0.3)
    cmd("FRAMEADVANCE", want=False); time.sleep(0.4); look("advance_after_held_load_released")
    # the load again, then the advances at the planned spacing (the design's number), the picture each time
    cmd("PAUSE_TOGGLE", want=False); time.sleep(2.0); cmd("PAUSE_TOGGLE", want=False); time.sleep(0.6)
    look("paused_before_second_load")
    step("load_paused_2", ack=cmd("LOAD_STATE_SLOT 1", 3.0, "LOAD_STATE_SLOT"))
    time.sleep(0.2)
    for k in range(1, 4):
        cmd("FRAMEADVANCE", want=False); time.sleep(0.05)
    time.sleep(0.4)
    look("second_load_three_advances_50ms")
    out["steps"][-1]["from_saved"] = (out["steps"][-1]["counter"] - s1["counter"]) % 64
finally:
    try:
        remote(False)
    except Exception:
        pass
    try:
        cmd("QUIT", want=False); cmd("QUIT", want=False); p.wait(5); how = "quit"
    except subprocess.TimeoutExpired:
        p.send_signal(signal.SIGTERM)
        try:
            p.wait(5); how = "sigterm"
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait(); how = "sigkill"
    step("exit", how=how, returncode=p.returncode, byte_order=ORDER[0])
    (WORK / "result.json").write_text(json.dumps(out, indent=1))
