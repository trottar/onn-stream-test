#!/usr/bin/env python3
"""B137 settle (B61's form, disclosed: the hub's RetroArch and PS1 core on the made-up PS-EXE — its built-in OpenBIOS
animation runs, no game, no title; temp folders, the hub's session config with the listed overrides). RetroArch's
"Paused." label: where it sits and how big at the window's size (full screen = T88's shape; 960 x 720 = T89's), and
whether it stays for as long as the core is paused. The label's own pixels (the top-right box, cut from the window) are
written to <workdir> for the overlay check (a temp folder, never git). Numbers only on stdout.
usage: label_probe.py <repo> <workdir> full|window"""
import json, os, shutil, signal, socket, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image
REPO, WORK, SHAPE = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
APP = REPO / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORE = REPO / "runtime/emulators/retroarch/cores-linux/mednafen_psx_hw_libretro.so"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_counter_psexe as fxp
FOLDER = "Beetle PSX HW"
for d in ("states", "saves", "system", f"xdg/retroarch/config/{FOLDER}", "frames"):
    (WORK / d).mkdir(parents=True, exist_ok=True)
exe = WORK / "fixture.exe"; exe.write_bytes(fxp.build()[0])
shutil.copyfile(Path.home() / f".config/retroarch/config/{FOLDER}/{FOLDER}.opt", WORK / f"xdg/retroarch/config/{FOLDER}/{FOLDER}.opt")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
base = (REPO / "data/games/retroarch/config/privyhub-session.cfg").read_text()
over = {"savefile_directory": WORK / "saves", "savestate_directory": WORK / "states", "system_directory": WORK / "system",
        "network_cmd_enable": "true", "network_cmd_port": port, "input_joypad_driver": "null",
        "history_list_enable": "false", "config_save_on_exit": "false", "log_dir": WORK, "savestate_auto_save": "false",
        "savestate_auto_load": "false", "savestate_thumbnail_enable": "false",
        "video_fullscreen": "true" if SHAPE == "full" else "false"}
if SHAPE != "full":
    over.update({"video_windowed_position_width": 960, "video_windowed_position_height": 720,
                 "video_window_custom_size_enable": "true"})
lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over] + [f'{k} = "{v}"' for k, v in over.items()]
cfg = WORK / "session.cfg"; cfg.write_text("\n".join(lines) + "\n")
env = dict(os.environ, XDG_CONFIG_HOME=str(WORK / "xdg"))
log = (WORK / "ra.log").open("w")
p = subprocess.Popen([str(APP), "--config", str(cfg), "--verbose", "-L", str(CORE), str(exe)], cwd=str(APP.parent),
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


def grab():
    if WID[0] is None:
        ids = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(p.pid)], capture_output=True, text=True).stdout.split()
        WID[0] = ids[-1] if ids else None
    f = WORK / "frames" / "g.png"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab", "-framerate", "60", "-draw_mouse", "0",
                    "-window_id", WID[0], "-i", os.environ.get("DISPLAY", ":0"), "-frames:v", "1", "-y", str(f)],
                   capture_output=True, timeout=20)
    return np.asarray(Image.open(f).convert("RGB"))


def label_box(a):
    """The label: the dark box in the top-right corner (all channels < 60) holding bright text (> 200)."""
    h, w, _ = a.shape
    reg = a[: h // 8, w // 2:].astype(int)
    text = (reg > 200).all(axis=2)
    if not text.any():
        return None, 0
    ys, xs = np.nonzero(text)
    y0, y1, x0, x1 = max(0, ys.min() - 4), ys.max() + 4, xs.min() - 4, xs.max() + 4
    # widen to the box: the dark rows / columns around the text
    dark = (reg < 70).all(axis=2)
    while y1 + 1 < reg.shape[0] and dark[y1 + 1, x0:x1].mean() > 0.6:
        y1 += 1
    while y0 > 0 and dark[y0 - 1, x0:x1].mean() > 0.6:
        y0 -= 1
    while x0 > 0 and dark[y0:y1, x0 - 1].mean() > 0.6:
        x0 -= 1
    while x1 + 1 < reg.shape[1] and dark[y0:y1, x1 + 1].mean() > 0.6:
        x1 += 1
    return (int(y0), int(y1 + 1), int(x0 + w // 2), int(x1 + 1 + w // 2)), int(text.sum())


try:
    t = time.monotonic(); r = None
    while time.monotonic() - t < 25 and r is None:
        r = cmd("GET_STATUS", 0.3, "GET_STATUS")
        if p.poll() is not None:
            break
    step("up", status=(r or "").split(" ")[1] if r else None)
    time.sleep(4.0)
    a = grab(); box, n = label_box(a)
    step("running", size=[a.shape[1], a.shape[0]], label=box, text_px=n)
    cmd("PAUSE_TOGGLE", want=False)
    t1 = time.monotonic()
    for at in (0.5, 3.0, 6.0, 12.0, 25.0):
        time.sleep(max(0.0, t1 + at - time.monotonic()))
        a = grab(); box, n = label_box(a)
        st = cmd("GET_STATUS", 0.4, "GET_STATUS")
        step("paused", after_s=round(time.monotonic() - t1, 1), size=[a.shape[1], a.shape[0]], label=box, text_px=n,
             status=(st or "").split(" ")[1] if st else None)
        if box is not None:
            y0, y1, x0, x1 = box
            Image.fromarray(a[y0:y1, x0:x1]).save(WORK / f"label_{SHAPE}.png")
            (WORK / f"label_{SHAPE}.json").write_text(json.dumps({"box": box, "size": [a.shape[1], a.shape[0]]}))
    cmd("FRAMEADVANCE", want=False); time.sleep(0.5)
    a = grab(); box, n = label_box(a)
    step("paused_after_one_advance", label=box, text_px=n)
finally:
    try:
        cmd("QUIT", want=False); cmd("QUIT", want=False); p.wait(5); how = "quit"
    except subprocess.TimeoutExpired:
        p.send_signal(signal.SIGTERM)
        try:
            p.wait(5); how = "sigterm"
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait(); how = "sigkill"
    step("exit", how=how)
    (WORK / "result.json").write_text(json.dumps(out, indent=1))
