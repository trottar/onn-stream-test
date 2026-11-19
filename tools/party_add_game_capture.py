#!/usr/bin/env python3
"""B157: the add-a-game tool's picture source on the hub — a kept state loaded paused in a headless RetroArch, then
run forward with no pads, a picture every `every` seconds (H7-V1's capture, B95's Session: the hub's AppImage and core,
its persistent config as the base, temp saves / states / system folders, the null joypad driver, the game file read
in place; the screenshot folder in the temp folder). Nothing is written beside the game file or in the user's folders.

`capture(state, binding, out_dir, seconds, every) -> [(seconds, file name)]`: frames as JPEG (quality 90, at most
640 px wide) in `out_dir`. The tests replace this module (PARTY_ADD_GAME_CAPTURE) with made-up pictures.
"""
from __future__ import annotations

import shutil
import socket
import subprocess
import os
import tempfile
import time
from pathlib import Path

from PIL import Image

TOOLS = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(TOOLS))
import h7_minigame_proof as proof  # noqa: E402  (B95's tool, imported, not edited)


class _Session(proof.Session):
    """B95's Session with the screenshot folder added (H7-V1's CaptureSession, without the memory reads)."""

    def __init__(self, content: Path, system: str, work: Path):
        self.core, self.library = proof.SYSTEMS[system]
        self.work = work
        for d in ("saves", "states", "system", "xdg", "cheats", "shots"):
            (work / d).mkdir(parents=True, exist_ok=True)
        self.content = Path(content).resolve()
        if not self.content.is_file():
            raise proof.ProofError("the game file is not there")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        self.port = s.getsockname()[1]
        s.close()
        base = (proof.REPO / "data/games/retroarch/retroarch.cfg").read_text()
        over = {"savefile_directory": work / "saves", "savestate_directory": work / "states",
                "system_directory": work / "system", "cheat_database_path": work / "cheats",
                "network_cmd_enable": "true", "network_cmd_port": self.port, "input_joypad_driver": "null",
                "history_list_enable": "false", "config_save_on_exit": "false", "savestate_auto_save": "false",
                "savestate_auto_load": "false", "savestate_thumbnail_enable": "false",
                "joypad_autoconfig_dir": work / "system", "pause_nonactive": "false",
                "screenshot_directory": work / "shots", "screenshots_in_content_dir": "false",
                "auto_screenshot_filename": "true", "notification_show_screenshot": "false",
                "video_font_enable": "false"}
        lines = [ln for ln in base.splitlines() if ln.split("=")[0].strip() not in over]
        (work / "session.cfg").write_text("\n".join(lines + [f'{k} = "{v}"' for k, v in over.items()]) + "\n")
        self.logf = work / "retroarch.log"
        self.log = self.logf.open("w")
        self.proc = subprocess.Popen(
            [str(proof.APP), "--config", str(work / "session.cfg"), "--verbose", "-L", str(proof.CORES / self.core),
             str(self.content)], cwd=str(proof.APP.parent), stdin=subprocess.DEVNULL, stdout=self.log,
            stderr=subprocess.STDOUT, env=dict(os.environ, XDG_CONFIG_HOME=str(work / "xdg")), start_new_session=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))

    def resume(self) -> None:
        if "PAUSED" in (self.ask("GET_STATUS", 0.3) or ""):
            self.send("PAUSE_TOGGLE")
            end = time.monotonic() + 3
            while time.monotonic() < end and "PLAYING" not in (self.ask("GET_STATUS", 0.2) or ""):
                time.sleep(0.02)


def capture(state: Path, binding: dict, out_dir: Path, seconds: float, every: float) -> list[tuple[float, str]]:
    work = Path(tempfile.mkdtemp(prefix="add_game_capture_"))
    rows: list[tuple[float, str]] = []
    try:
        temp_state = work / "copy.state"
        shutil.copyfile(state, temp_state)                      # the kept copy is only read
        s = _Session(Path(binding["content"]), binding["system"], work)
        try:
            s.wait_playing(30)
            s.pause()
            s.load_state(temp_state)
            shots = work / "shots"
            s.resume()
            t0 = time.monotonic()
            k = 0
            while True:
                target = t0 + k * every
                if target > time.monotonic():
                    time.sleep(target - time.monotonic())
                t = time.monotonic() - t0
                if t > seconds:
                    break
                before = set(shots.iterdir())
                s.send("SCREENSHOT")
                new, end = None, time.monotonic() + 0.45
                while time.monotonic() < end:
                    fresh = [p for p in set(shots.iterdir()) - before if p.suffix == ".png"]
                    if fresh:
                        time.sleep(0.03)
                        new = fresh[0]
                        break
                    time.sleep(0.01)
                if new is not None:
                    with Image.open(new) as im:
                        im = im.convert("RGB")
                    if im.width > 640:
                        im = im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS)
                    name = f"f{k:04d}.jpg"
                    im.save(out_dir / name, quality=90)
                    rows.append((round(k * every, 2), name))
                k += 1
        finally:
            s.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return rows
