#!/usr/bin/env python3
"""B139 settle (B61's form, disclosed: the hub's RetroArch with its N64 core on B137's made-up ROM (flat colours) and its
PS1 core on the made-up PS-EXE (the core's OpenBIOS animation runs); temp config / states / saves / system / XDG
folders; read-only copies of the hub's core option files; the joypad driver null; no stream, no game, no title).

Which of RetroArch's own settings, written into the per-session config, leave the window with nothing of RetroArch's
on it — "Paused.", the notices, the content banner — paused and running; and the command port, GET_STATUS and the
session log's load line as before. A made-up cheat file for the fixture (an enabled code writing an unused word) is
offered, so that a cheat notice may show.

Measured per grab (numbers only, nothing kept unless <workdir>/keep exists — then a few PNGs there for a look):
  bars  — full screen only: pixels brighter than 24 in the pillarbox bars (the cores draw nothing there);
  tr / bl / mid — pixels in the top-right 220 x 80 box, the bottom-left 520 px x (78-97 % of the height) box and a
          middle band (40-60 % of the height), 12 px in from the picture's edges, that differ by more than 40 from that box's median grey (the fixture's flat colours; OpenBIOS's
          dark-blue field) — RetroArch's text and boxes there.
usage: osd_probe.py <repo> <workdir> n64|ps1 full|window <variant>   (variants: see VARIANTS)"""
import json, os, shutil, signal, socket, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image
REPO, WORK, CORE_KIND, SHAPE, VARIANT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3], sys.argv[4], sys.argv[5]
VARIANTS = {
    "today": {},
    "font_off": {"video_font_enable": "false"},
    "anim_off": {"menu_show_load_content_animation": "false"},
    "widgets_off": {"menu_enable_widgets": "false"},
    "notif_off": {k: "false" for k in ("notification_show_autoconfig", "notification_show_cheats_applied",
                                       "notification_show_patch_applied", "notification_show_remap_load",
                                       "notification_show_config_override_load", "notification_show_set_initial_disk")},
    "all": {"video_font_enable": "false", "menu_show_load_content_animation": "false"},
}
APP = REPO / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
sys.path.insert(0, str(Path(__file__).resolve().parent))
if CORE_KIND == "ps1":
    import fixture_counter_psexe as fxp
    CORE = REPO / "runtime/emulators/retroarch/cores-linux/mednafen_psx_hw_libretro.so"
    FOLDER, EXT, BUILD = "Beetle PSX HW", "exe", fxp.build
else:
    import fixture_counter_rom as fx
    CORE = REPO / "runtime/emulators/retroarch/cores-linux/mupen64plus_next_libretro.so"
    FOLDER, EXT, BUILD = "Mupen64Plus-Next", "z64", fx.build
for d in ("states", "saves", "system", f"xdg/retroarch/config/{FOLDER}", "frames", f"cheats/{FOLDER}"):
    (WORK / d).mkdir(parents=True, exist_ok=True)
rom = WORK / f"fixture.{EXT}"; rom.write_bytes(BUILD()[0])
shutil.copyfile(Path.home() / f".config/retroarch/config/{FOLDER}/{FOLDER}.opt", WORK / f"xdg/retroarch/config/{FOLDER}/{FOLDER}.opt")
(WORK / f"cheats/{FOLDER}/fixture.cht").write_text(
    'cheats = "1"\n\ncheat0_desc = "fixture"\ncheat0_code = "80300300 0001"\ncheat0_enable = "true"\n')
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
base = (REPO / "data/games/retroarch/config/privyhub-session.cfg").read_text()
over = {"savefile_directory": WORK / "saves", "savestate_directory": WORK / "states", "system_directory": WORK / "system",
        "network_cmd_enable": "true", "network_cmd_port": port, "input_joypad_driver": "null",
        "history_list_enable": "false", "config_save_on_exit": "false", "log_dir": WORK, "savestate_auto_save": "false",
        "savestate_auto_load": "false", "savestate_thumbnail_enable": "false",
        "cheat_database_path": WORK / "cheats", "apply_cheats_after_load": "true",
        "video_fullscreen": "true" if SHAPE == "full" else "false"}
if SHAPE != "full":
    over.update({"video_windowed_position_width": 960, "video_windowed_position_height": 720,
                 "video_window_custom_size_enable": "true"})
over.update(VARIANTS[VARIANT])
lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over] + [f'{k} = "{v}"' for k, v in over.items()]
cfg = WORK / "session.cfg"; cfg.write_text("\n".join(lines) + "\n")
env = dict(os.environ, XDG_CONFIG_HOME=str(WORK / "xdg"))
log = (WORK / "ra.log").open("w")
p = subprocess.Popen([str(APP), "--config", str(cfg), "--verbose", "-L", str(CORE), str(rom)], cwd=str(APP.parent),
                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.bind(("127.0.0.1", 0))
out = {"core": CORE_KIND, "shape": SHAPE, "variant": VARIANT, "settings": VARIANTS[VARIANT], "steps": []}
T0 = time.monotonic()
KEEP = (WORK / "keep").exists()


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


WID = [None]


def grab():
    if WID[0] is None:
        ids = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(p.pid)], capture_output=True, text=True).stdout.split()
        WID[0] = ids[-1] if ids else None
    f = WORK / "frames" / "g.png"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab", "-framerate", "60", "-draw_mouse", "0",
                    "-window_id", WID[0], "-i", os.environ.get("DISPLAY", ":0"), "-frames:v", "1", "-y", str(f)],
                   capture_output=True, timeout=20)
    return np.asarray(Image.open(f).convert("L")).astype(int), f


def marks(a):
    h, w = a.shape
    m = {"size": [w, h]}
    if SHAPE == "full":
        pw = int(round(h * 4 / 3)); bx = (w - pw) // 2
        bars = np.concatenate([a[:, : bx - 2].ravel(), a[:, w - bx + 2:].ravel()])
        m["bars"] = int((bars > 24).sum())
        x0, x1 = bx, w - bx
    else:
        x0, x1 = 0, w

    def dev(reg):
        return int((np.abs(reg - np.median(reg)) > 40).sum())
    x0, x1 = x0 + 12, x1 - 12                       # the fixture's own edge strips left out
    m["tr"] = dev(a[:80, x1 - 220:x1])
    m["bl"] = dev(a[int(h * 0.78):int(h * 0.97), x0:x0 + 520])
    m["mid"] = dev(a[int(h * 0.4):int(h * 0.6), x0:x1])
    return m


def look(name, **kw):
    a, f = grab()
    r = marks(a); r.update(kw); r["status"] = status()
    r["t_s"] = round(time.monotonic() - T0, 2); r["step"] = name
    out["steps"].append(r); print(json.dumps(r), flush=True)
    if KEEP:
        shutil.copyfile(f, WORK / "keep" / f"{len(out['steps']):02d}_{name}.png")


try:
    t = time.monotonic(); r = None
    while time.monotonic() - t < 25 and r is None:
        r = cmd("GET_STATUS", 0.1, "GET_STATUS")
        if p.poll() is not None:
            break
    out["up_s"] = round(time.monotonic() - t, 2)
    if r is None:
        raise SystemExit
    for at in (0.3, 0.8, 1.5, 2.5, 4.0, 7.0):
        time.sleep(max(0.0, t + out["up_s"] + at - time.monotonic()))
        look("running", after_up_s=at)
    cmd("PAUSE_TOGGLE", want=False); tp = time.monotonic()
    for at in (0.5, 3.0):
        time.sleep(max(0.0, tp + at - time.monotonic()))
        look("paused", after_pause_s=at)
    out["save_ack"] = cmd("SAVE_STATE_SLOT 1", 3.0, "SAVE_STATE_SLOT")
    time.sleep(0.5)
    out["load_ack"] = cmd("LOAD_STATE_SLOT 1", 3.0, "LOAD_STATE_SLOT"); tl = time.monotonic()
    for at in (0.3, 1.5):
        time.sleep(max(0.0, tl + at - time.monotonic()))
        look("paused_after_load", after_load_s=at)
    cmd("FRAMEADVANCE", want=False); time.sleep(0.3); look("paused_after_advance")
    cmd("PAUSE_TOGGLE", want=False); time.sleep(0.5); look("running_again")
finally:
    try:
        cmd("QUIT", want=False); cmd("QUIT", want=False); p.wait(5); how = "quit"
    except subprocess.TimeoutExpired:
        p.send_signal(signal.SIGTERM)
        try:
            p.wait(5); how = "sigterm"
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait(); how = "sigkill"
    log.close()
    text = (WORK / "ra.log").read_text(errors="replace")
    out["log"] = {"load_line": "[State] Loading state" in text, "cheat_lines": text.count("[Cheat"),
                  "cmd_listening": "network_cmd" in text.lower() or "Network command" in text or "command" in text.lower()}
    out["exit"] = how
    (WORK / "result.json").write_text(json.dumps(out, indent=1))
