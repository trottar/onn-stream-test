#!/usr/bin/env python3
"""Bench: which cheat code forms does the hub's snes9x core apply, for a ROM byte and a RAM byte?
A synthetic LoROM (no game): every loop LDA $8100 (ROM, 0x11 in the file); STA $7E2000. A cheat that patches ROM 00:8100
(or its mirror 80:8100) shows in WRAM $2000; a RAM cheat writes $7E2100 directly. One staged cheat per run, enabled, with
apply_cheats_after_load on; READ_CORE_RAM after 3 s. Made-up names; temp folders; prints forms and bytes only."""
import json, os, signal, socket, struct, subprocess, sys, time
from pathlib import Path
R = Path("/home/privyhub/Projects/onn-stream-test")
APP = R / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORE = R / "runtime/emulators/retroarch/cores-linux/snes9x_libretro.so"
def rom():
    r = bytearray(b"\xFF" * 0x8000)
    code = bytes([0x78, 0x18, 0xFB,            # SEI CLC XCE
                  0xAD, 0x00, 0x81,            # LDA $8100
                  0x8F, 0x00, 0x20, 0x7E,      # STA $7E2000
                  0x80, 0xF7])                 # BRA -9 (to LDA)
    r[0:len(code)] = code
    r[0x0100] = 0x11
    r[0x7FC0:0x7FD5] = b"PRIVYHUB FIXTURE".ljust(21)
    r[0x7FD5] = 0x20; r[0x7FD6] = 0; r[0x7FD7] = 5; r[0x7FD8] = 0; r[0x7FD9] = 1
    for v in (0x7FE4, 0x7FE6, 0x7FE8, 0x7FEA, 0x7FEE, 0x7FF4, 0x7FF8, 0x7FFA, 0x7FFE):
        r[v:v + 2] = struct.pack("<H", 0x800A)
    r[0x7FFC:0x7FFE] = struct.pack("<H", 0x8000)
    r[0x7FDC:0x7FE0] = b"\xFF\xFF\x00\x00"; s = sum(r) & 0xFFFF; r[0x7FDC:0x7FE0] = struct.pack("<HH", s ^ 0xFFFF, s)
    return bytes(r)
def run(code, work):
    work.mkdir(parents=True, exist_ok=True)
    for d in ("saves", "states", "system", "cheats/Snes9x", "xdg"): (work / d).mkdir(parents=True, exist_ok=True)
    (work / "Made Up Fixture.sfc").write_bytes(rom())
    if code:
        (work / "cheats/Snes9x/Made Up Fixture.cht").write_text(
            f'cheats = 1\n\ncheat0_desc = "Made Up"\ncheat0_code = "{code}"\ncheat0_enable = true\n')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    base = (R / "data/games/retroarch/retroarch.cfg").read_text()
    over = {"savefile_directory": work / "saves", "savestate_directory": work / "states", "system_directory": work / "system",
            "cheat_database_path": work / "cheats", "network_cmd_enable": "true", "network_cmd_port": port,
            "input_joypad_driver": "null", "history_list_enable": "false", "config_save_on_exit": "false",
            "savestate_auto_save": "false", "savestate_auto_load": "false", "joypad_autoconfig_dir": work / "system",
            "pause_nonactive": "false", "apply_cheats_after_load": "true"}
    lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over]
    (work / "s.cfg").write_text("\n".join(lines + [f'{k} = "{v}"' for k, v in over.items()]) + "\n")
    log = (work / "ra.log").open("w")
    p = subprocess.Popen([str(APP), "--config", str(work / "s.cfg"), "--verbose", "-L", str(CORE), str(work / "Made Up Fixture.sfc")],
                         cwd=str(APP.parent), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                         env=dict(os.environ, XDG_CONFIG_HOME=str(work / "xdg")), start_new_session=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sock.bind(("127.0.0.1", 0)); sock.settimeout(0.5)
    def ask(c):
        sock.sendto(c.encode(), ("127.0.0.1", port))
        try: return sock.recvfrom(4096)[0].decode().strip()
        except socket.timeout: return None
    try:
        time.sleep(3.0)
        out = {"rom_copy_2000": (ask("READ_CORE_RAM 2000 1") or "").split()[2:], "ram_2100": (ask("READ_CORE_RAM 2100 1") or "").split()[2:]}
        t = (work / "ra.log").read_text(errors="replace")
        out["cheatfile"] = "Load game-specific cheatfile" in t; out["applying"] = t.count("Applying cheat changes")
        out["core_lines"] = [l.strip()[-90:] for l in t.splitlines() if "heat" in l and "[Cheats]" not in l][:4]
        return out
    finally:
        try: sock.sendto(b"QUIT", ("127.0.0.1", port)); p.wait(5)
        except Exception: pass
        if p.poll() is None: os.killpg(p.pid, signal.SIGKILL); p.wait(5)
        log.close()
import tempfile
cases = [("none", ""), ("raw colon, ROM 00:8100", "008100:42"), ("raw colon, ROM mirror 80:8100", "808100:42"),
         ("raw equals, ROM 00:8100", "008100=42"), ("PAR, ROM 00:8100", "00810042"), ("PAR, ROM mirror 80:8100", "80810042"),
         ("raw colon, RAM 7E:2100", "7E2100:42"), ("PAR, RAM 7E:2100", "7E210042"), ("raw equals, RAM 7E:2100", "7E2100=42")]
for name, code in cases:
    print(json.dumps({"case": name, **run(code, Path(tempfile.mkdtemp(prefix="fmt_", dir=os.getcwd())))}))
print(json.dumps({"retroarch_left": int(subprocess.run("ps -eo args | grep -c '[R]etroArch-Linux'", shell=True, capture_output=True, text=True).stdout.strip() or 0)}))
