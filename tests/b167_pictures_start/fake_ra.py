#!/usr/bin/env python3
"""B167's tests: a made-up RetroArch standing in for the hub's AppImage. Called as RetroArch is
(`--config <cfg> --verbose -L <core> <content>`); writes made-up log lines to stdout (the capture's log) and, by the
mode in FAKE_RA_MODE, exits with one of RetroArch's own failure lines or answers its network commands:

    display  "[ERROR] [Video] Cannot open video driver. Exiting..."      content  "Failed to load content"
    core     "Failed to open libretro core"                              config   "Failed to load config"
    other    an error line no reason knows                               silent   runs, never answers
    state    plays, refuses the state                                    ok       plays, loads it, screenshots

It logs what it was given (the core's file name, DISPLAY, the core options it finds, game_specific_options) as
"FAKE …" lines. Nothing real: no game, no picture but a made-up one."""
import json
import os
import socket
import sys
import time
from pathlib import Path

args = sys.argv[1:]
cfg = Path(args[args.index("--config") + 1])
core = Path(args[args.index("-L") + 1]).name
conf = {}
for ln in cfg.read_text().splitlines():
    k, _, v = ln.partition("=")
    conf[k.strip()] = v.strip().strip('"')
mode = os.environ.get("FAKE_RA_MODE", "ok")
say = lambda t: (print(t), sys.stdout.flush())
say("[INFO] RetroArch made-up")
say(f"FAKE core {core}")
say(f"FAKE display {os.environ.get('DISPLAY', '')}")
optroot = Path(os.environ.get("XDG_CONFIG_HOME", "")) / "retroarch" / "config"
say("FAKE opts " + json.dumps(sorted(p.name for p in optroot.rglob("*.opt")) if optroot.is_dir() else []))
say(f"FAKE game_specific_options {conf.get('game_specific_options')}")
lines = {"display": "[ERROR] [Video] Cannot open video driver. Exiting...",
         "content": "[ERROR] Failed to load content's file.", "core": "[ERROR] Failed to open libretro core",
         "config": "[ERROR] Failed to load config file.", "other": "[ERROR] Something made up went wrong."}
if mode in lines:
    say(lines[mode])
    sys.exit(1)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("127.0.0.1", int(conf["network_cmd_port"])))
paused, end = False, time.monotonic() + 60
shots = Path(conf["screenshot_directory"])
k = 0
while time.monotonic() < end:
    s.settimeout(0.5)
    try:
        data, addr = s.recvfrom(4096)
    except socket.timeout:
        continue
    cmd = data.decode().strip()
    if mode == "silent":
        continue
    if cmd == "GET_STATUS":
        s.sendto(("GET_STATUS " + ("PAUSED" if paused else "PLAYING") + " made_up,x,crc32=0").encode(), addr)
    elif cmd == "PAUSE_TOGGLE":
        paused = not paused
    elif cmd.startswith("LOAD_STATE_SLOT"):
        say('[ERROR] [State] Failed to load state from "x".' if mode == "state"
            else '[INFO] [State] Loading state "x", 100 bytes.')
    elif cmd == "SCREENSHOT":
        from PIL import Image
        Image.new("RGB", (64, 48), (k * 7 % 255, 40, 90)).save(shots / f"shot_{k:04d}.png")
        k += 1
    elif cmd == "QUIT":
        break
