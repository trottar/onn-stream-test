#!/usr/bin/env python3
"""B90's headless measurement (B61's / B87's form): the synthetic fixture ROMs (no game, no title), made-up cheat lists
of a given size, the hub's RetroArch and cores, temp config / saves / states / XDG folders, the joypad driver null, no
stream, no pad, a short run on the companion's display. Prints one JSON line of timings and counts only.

    python3 -I -B b90_measure.py <repo> <code_root> <workdir> --system n64|snes|ps1 --entries N --picks k
        --mode load|walk|staged [--apply-at-load 0|1] [--folder NAME] [--window S]

- load:   a file of the k picks only, each enabled; no command but GET_STATUS until --window; then RetroArch's log read
          and one index pulse per staged cheat (their on / off), and core-memory reads at each pick's address.
- walk:   the full list (all off) staged as the hub stages it; the hub's own `_apply_active_cheat_profile` from
          <code_root>/companion with PRIVYHUB_CHEAT_STAGED=0 (today's walk); pulses counted, the time measured.
- staged: the hub's own staging builder and `_apply_active_cheat_profile` from <code_root> (B90 on).
Every command the hub's code sends goes through its own `_retroarch_network_request` (wrapped to count only).
"""
import json, os, re, shutil, signal, socket, subprocess, sys, threading, time
from pathlib import Path

REPO, CODE, WORK = (Path(a).resolve() for a in sys.argv[1:4])
def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
SYSTEM = opt("--system", "n64"); N = int(opt("--entries", "12")); K = int(opt("--picks", "1"))
MODE = opt("--mode", "load"); WINDOW = float(opt("--window", "6")); APPLY = opt("--apply-at-load", "1")
APP = REPO / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORES = REPO / "runtime/emulators/retroarch/cores-linux"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixture_n64, fixture_more  # noqa: E402

SYS = {
    "n64": dict(core="mupen64plus_next_libretro.so", folder="Mupen64Plus-Next", ext=".z64",
                rom=lambda: fixture_n64.build()[0],
                code=lambda i: (f"8030{(2 * i) & 0xFFFF:04X} 00{(i % 250) + 1:02X}", 0x300000 + 2 * i, (i % 250) + 1)),
    "snes": dict(core="snes9x_libretro.so", folder="Snes9x", ext=".sfc", rom=fixture_more.snes,
                 code=lambda i: (f"7E{0x1000 + i:04X}{(i % 250) + 1:02X}", 0x1000 + i, (i % 250) + 1)),
    "ps1": dict(core="mednafen_psx_hw_libretro.so", folder="Beetle PSX HW", ext=".exe", rom=fixture_more.psx_exe,
                code=lambda i: (f"800A{(2 * i) & 0xFFFF:04X} 00{(i % 250) + 1:02X}", 0x0A0000 + 2 * i, (i % 250) + 1)),
}[SYSTEM]
FOLDER = opt("--folder", SYS["folder"])
PICKS = sorted({min(N - 1, (N * (j + 1)) // (K + 1)) for j in range(K)}) if K else []

for d in ("states", "saves", "system", "cheats", "xdg/retroarch/config", "proj/logs/games"):
    (WORK / d).mkdir(parents=True, exist_ok=True)
romf = WORK / f"Made Up Fixture{SYS['ext']}"
romf.write_bytes(SYS["rom"]())
rows = [(f"Made Up Cheat {i}", SYS["code"](i)[0]) for i in range(N)]

def cht(items, enabled):
    body = [f"cheats = {len(items)}", ""]
    for j, (desc, code) in enumerate(items):
        body += [f'cheat{j}_desc = "{desc}"', f'cheat{j}_code = "{code}"', f"cheat{j}_enable = {'true' if enabled else 'false'}", ""]
    return "\n".join(body) + "\n"

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
out = {"system": SYSTEM, "mode": MODE, "entries": N, "picks": len(PICKS), "pick_positions": PICKS}
os.environ.pop("PRIVYHUB_CHEAT_STAGED", None)
if MODE == "walk":
    os.environ["PRIVYHUB_CHEAT_STAGED"] = "0"
sys.path.insert(0, str(CODE / "companion"))
from games import emulator_manager as em  # noqa: E402
staged_extra = ""
cheat_dir = WORK / "cheats" / FOLDER
cheat_dir.mkdir(parents=True, exist_ok=True)
entries = [{"index": i, "description": d} for i, (d, _c) in enumerate(rows)]
session = {"session_kind": "cheat", "entries": entries, "enabled_cheat_indexes": list(PICKS), "profile_path": "x"}
if MODE == "load":
    (cheat_dir / f"{romf.stem}.cht").write_text(cht([rows[i] for i in PICKS], True))
    staged_extra = f'apply_cheats_after_load = "{"true" if APPLY == "1" else "false"}"\n'
elif MODE == "walk":
    (cheat_dir / f"{romf.stem}.cht").write_text(cht(rows, False))
else:   # staged: the hub's own builder (B90) writes the file and the session's staged map
    raw = cht(rows, False).encode()
    built = em.EmulatorManager._staged_cheat_file(raw, list(PICKS))
    (cheat_dir / f"{romf.stem}.cht").write_bytes(built["bytes"])
    session.update(built["session"])
    staged_extra = em.EmulatorManager.CHEAT_STAGED_CONFIG_LINES
base = (REPO / "data/games/retroarch/retroarch.cfg").read_text()
over = {"savefile_directory": WORK / "saves", "savestate_directory": WORK / "states", "system_directory": WORK / "system",
        "cheat_database_path": WORK / "cheats", "network_cmd_enable": "true", "network_cmd_port": port,
        "input_joypad_driver": "null", "history_list_enable": "false", "config_save_on_exit": "false", "log_dir": WORK,
        "savestate_auto_save": "false", "savestate_auto_load": "false", "savestate_thumbnail_enable": "false",
        "joypad_autoconfig_dir": WORK / "system", "pause_nonactive": "false"}
lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over and "apply_cheats" not in l]
lines += [f'{k} = "{v}"' for k, v in over.items()]
cfg = WORK / "session.cfg"; cfg.write_text("\n".join(lines) + "\n" + staged_extra)
env = dict(os.environ, XDG_CONFIG_HOME=str(WORK / "xdg"))
logf = WORK / "proj/logs/games/ra.log"
log = logf.open("w")
p = subprocess.Popen([str(APP), "--config", str(cfg), "--verbose", "-L", str(CORES / SYS["core"]), str(romf)],
                     cwd=str(APP.parent), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env,
                     start_new_session=True)
T0 = time.monotonic()
def t(): return round(time.monotonic() - T0, 3)
def text(): return logf.read_text(errors="replace")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.bind(("127.0.0.1", 0))
def ask(cmd, wait=0.3):
    sock.sendto(cmd.encode(), ("127.0.0.1", port)); sock.settimeout(wait)
    try:
        return sock.recvfrom(65536)[0].decode(errors="replace").strip()
    except socket.timeout:
        return None
def mem_reads():
    res = {}
    for i in PICKS[:4]:
        _c, addr, val = SYS["code"](i)
        for cmd in ("READ_CORE_MEMORY", "READ_CORE_RAM"):   # the aligned word (N64's RDRAM is word-swapped)
            r = ask(f"{cmd} {addr & ~3:x} 4")
            got = (r or "").split()[2:]
            res.setdefault(cmd, []).append({"want": f"{val:02x}", "got": " ".join(got)[-40:], "ok": f"{val:02x}" in [x.lower() for x in got]})
    return res

# the hub's own code, on a manager with only what the cheat path reads
m = em.EmulatorManager.__new__(em.EmulatorManager)
m.lock = threading.RLock(); m.process = p; m.log_handle = log; m._network_cmd_port = port
m.project_root = WORK / "proj"; m._launch_kind = "retroarch"; m._paused = False
m._active_cheat_session = session
counts = {}
real_req = em.EmulatorManager._retroarch_network_request
def counted(self, command, **kw):
    counts[command] = counts.get(command, 0) + 1
    return real_req(self, command, **kw)
m._retroarch_network_request = counted.__get__(m)
m._record_retroarch_command = lambda *a, **k: None
m.record_save_state_probe_event = lambda *a, **k: None
m._refresh_process = lambda: None
m._validate_active_cheat_profile_identity = lambda s: None
m.status = lambda: {}
try:
    while t() < 20:
        if ask("GET_STATUS", 0.1) and "PLAYING" in (ask("GET_STATUS", 0.1) or ""):
            out["playing"] = t(); break
        time.sleep(0.05)
    if MODE == "load":
        while t() < WINDOW:
            time.sleep(0.1)
        txt = text()
        out["log_cheatfile"] = "Load game-specific cheatfile" in txt
        out["log_applying"] = txt.count("Applying cheat changes")
        out["log_core_cheat_lines"] = [l[-120:] for l in txt.splitlines() if "heat" in l and "[Cheats]" not in l][:8]
        out["mem"] = mem_reads()
        states = []
        for _ in PICKS:
            n0 = len(text())
            sock.sendto(b"CHEAT_INDEX_PLUS", ("127.0.0.1", port))
            t1 = time.monotonic()
            while time.monotonic() - t1 < 1.0:
                new = text()[n0:]
                mm = re.search(r"Cheat #(\d+): (.*?): (on|off)", new)
                if mm:
                    states.append([int(mm.group(1)), mm.group(3)]); break
                time.sleep(0.02)
            else:
                states.append(None)
        out["index_states"] = states
    else:
        t1 = time.monotonic()
        try:
            r = m._apply_active_cheat_profile()
            out["error"] = None
            out["activation_verified"] = r.get("activation_verified")
        except Exception as exc:
            out["error"] = str(exc)[:200]
        out["activation_s"] = round(time.monotonic() - t1, 3)
        out["commands"] = counts
        out["pulses"] = sum(v for k, v in counts.items() if k.startswith("CHEAT_"))
        time.sleep(1.0)
        out["mem"] = mem_reads() if p.poll() is None else None
        out["log_applying"] = text().count("Applying cheat changes")
    out["running_at_end"] = p.poll() is None
finally:
    try:
        sock.sendto(b"QUIT", ("127.0.0.1", port)); p.wait(5)
    except Exception:
        pass
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGKILL); p.wait(5)
    log.close()
    out["log_head_lines"] = None
if "--keep-log" in sys.argv:
    shutil.copyfile(logf, WORK / "kept.log")
print(json.dumps(out))
