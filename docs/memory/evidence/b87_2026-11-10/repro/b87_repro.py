#!/usr/bin/env python3
"""B87: when does RetroArch load a game's cheat file with Mupen64Plus-Next, against when its command port answers?

B61's form: the synthetic fixture ROM (a header + a VI loop; no game, no title), the hub's RetroArch and N64 core, temp
config / states / saves / XDG folders, the joypad driver null, no stream, no pad, a short run. A fixture `.cht` (two
made-up cheats writing to RDRAM) staged as the hub stages one: `<cheat_database_path>/Mupen64Plus-Next/<content stem>.cht`.
Prints timings only (seconds from the process start): the log's `[NetCMD]` line, GET_STATUS answering PLAYING, the log's
`Load game-specific cheatfile` line; then CHEAT_INDEX_PLUS sent at PLAYING (the hub's order today) and after the
cheat-file line, each with the time to RetroArch's `Cheat #` line (or none within the window).
    python3 b87_repro.py <repo> <workdir> [--no-cht] [--window 20]
Run with DISPLAY / XAUTHORITY from the companion's environment.
"""
import json, os, re, shutil, signal, socket, subprocess, sys, time
from pathlib import Path

REPO, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
NO_CHT = "--no-cht" in sys.argv
WINDOW = float(sys.argv[sys.argv.index("--window") + 1]) if "--window" in sys.argv else 20.0
APP = REPO / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORE = REPO / "runtime/emulators/retroarch/cores-linux/mupen64plus_next_libretro.so"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_rom  # noqa: E402

WORK.mkdir(parents=True, exist_ok=True)
for d in ("states", "saves", "system", "cheats/Mupen64Plus-Next", "xdg/retroarch/config/Mupen64Plus-Next"):
    (WORK / d).mkdir(parents=True, exist_ok=True)
# --v64: the byte-swapped form (the hub's in-place titles include .v64); --name: a made-up name with spaces and brackets;
# --entries n: a made-up list of n cheats (HOME-12R's list had 677)
V64 = "--v64" in sys.argv
NAME = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else "fixture"
ENTRIES = int(sys.argv[sys.argv.index("--entries") + 1]) if "--entries" in sys.argv else 2
data = fixture_rom.build()[0]
if V64:
    data = b"".join(data[i + 1:i + 2] + data[i:i + 1] for i in range(0, len(data), 2))
romf = WORK / f"{NAME}{'.v64' if V64 else '.z64'}"
romf.write_bytes(data)
if not NO_CHT:
    body = [f"cheats = {ENTRIES}", ""]
    for i in range(ENTRIES):
        body += [f'cheat{i}_desc = "Made Up {i}"', f'cheat{i}_code = "8010{i % 0x10000:04X} 0001"', f"cheat{i}_enable = false", ""]
    # --cht-name: stage the file under another name (which name does RetroArch look for?)
    CHT_NAME = sys.argv[sys.argv.index("--cht-name") + 1] if "--cht-name" in sys.argv else NAME
    (WORK / "cheats/Mupen64Plus-Next" / f"{CHT_NAME}.cht").write_text("\n".join(body))
out_meta = {"v64": V64, "name_has_spaces": " " in NAME, "entries": ENTRIES}
real_opt = Path.home() / ".config/retroarch/config/Mupen64Plus-Next/Mupen64Plus-Next.opt"
if real_opt.is_file():
    shutil.copyfile(real_opt, WORK / "xdg/retroarch/config/Mupen64Plus-Next/Mupen64Plus-Next.opt")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
base = (REPO / "data/games/retroarch/config/privyhub-session.cfg").read_text()
over = {"savefile_directory": WORK / "saves", "savestate_directory": WORK / "states", "system_directory": WORK / "system",
        "cheat_database_path": WORK / "cheats", "network_cmd_enable": "true", "network_cmd_port": port,
        "input_joypad_driver": "null", "history_list_enable": "false", "config_save_on_exit": "false", "log_dir": WORK,
        "savestate_auto_save": "false", "savestate_auto_load": "false", "savestate_thumbnail_enable": "false"}
lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over]
lines += [f'{k} = "{v}"' for k, v in over.items()]
cfg = WORK / "session.cfg"; cfg.write_text("\n".join(lines) + "\n")
env = dict(os.environ, XDG_CONFIG_HOME=str(WORK / "xdg"))
logf = WORK / "ra.log"
log = logf.open("w")
p = subprocess.Popen([str(APP), "--config", str(cfg), "--verbose", "-L", str(CORE), str(romf)], cwd=str(APP.parent),
                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
T0 = time.monotonic()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.bind(("127.0.0.1", 0))
out = {"cht_staged": not NO_CHT, "window_s": WINDOW, **out_meta}

def t():
    return round(time.monotonic() - T0, 3)

def text():
    try:
        return logf.read_text(errors="replace")
    except OSError:
        return ""

def status():
    sock.sendto(b"GET_STATUS", ("127.0.0.1", port)); sock.settimeout(0.05)
    try:
        return sock.recvfrom(4096)[0].decode(errors="replace").split(" ")[1]
    except (socket.timeout, IndexError):
        return None

def cheat_lines():
    return len(re.findall(r"\[Cheats\] Cheat #\d+:", text()))

def index_plus(window):
    before = cheat_lines(); t1 = time.monotonic()
    sock.sendto(b"CHEAT_INDEX_PLUS", ("127.0.0.1", port))
    while time.monotonic() - t1 < window:
        if cheat_lines() > before:
            return round(time.monotonic() - t1, 3)
        time.sleep(0.02)
    return None

PROBE = "--probe" in sys.argv     # from PLAYING: a CHEAT_INDEX_PLUS every 0.25 s until RetroArch answers one

def dynarec_at():
    return "Init new dynarec" in text()

try:
    while PROBE and time.monotonic() - T0 < WINDOW:
        if "netcmd" not in out and "[NetCMD]" in text():
            out["netcmd"] = t()
        if "cheatfile" not in out and "Load game-specific cheatfile" in text():
            out["cheatfile"] = t()
        if "dynarec" not in out and dynarec_at():
            out["dynarec"] = t()
        if "playing" not in out and "netcmd" in out and status() == "PLAYING":
            out["playing"] = t()
            sent = 0
            while time.monotonic() - T0 < WINDOW:
                sent += 1
                if index_plus(0.25) is not None:
                    out["first_answer"] = t(); out["probes_sent"] = sent
                    break
                if "dynarec" not in out and dynarec_at():
                    out["dynarec"] = t()
            break
        time.sleep(0.02)
    while not PROBE and time.monotonic() - T0 < WINDOW:
        txt = text()
        if "netcmd" not in out and "[NetCMD]" in txt:
            out["netcmd"] = t()
        if "playing" not in out and "netcmd" in out and status() == "PLAYING":
            out["playing"] = t()
            out["cheat_index_plus_at_playing_answered_in_s"] = index_plus(1.0)   # the hub's order today (1-s window)
        if "cheatfile" not in out and "Load game-specific cheatfile" in txt:
            out["cheatfile"] = t()
        if "playing" in out and ("cheatfile" in out or NO_CHT) and "after" not in out:
            if "cheatfile" in out:
                out["after"] = True
                out["cheat_index_plus_after_cheatfile_answered_in_s"] = index_plus(1.0)
            break
        if p.poll() is not None:
            out["exited"] = p.returncode
            break
        time.sleep(0.02)
    out["end"] = t()
    txt = text()
    out["log_has_cheatfile_line"] = "Load game-specific cheatfile" in txt
    out["log_cheat_lines"] = cheat_lines()
    out["log_order"] = [k for k, _ in sorted(((k, txt.find(m)) for k, m in (
        ("core_api", "Version of libretro API"), ("netcmd", "[NetCMD]"), ("cheatfile", "Load game-specific cheatfile"),
        ("dynarec", "Init new dynarec")) if txt.find(m) >= 0), key=lambda kv: kv[1])]
finally:
    try:
        sock.sendto(b"QUIT", ("127.0.0.1", port)); p.wait(5)
    except Exception:
        pass
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGKILL); p.wait(5)
    log.close()
print(json.dumps(out))
