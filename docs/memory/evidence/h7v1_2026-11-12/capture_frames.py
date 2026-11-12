#!/usr/bin/env python3
"""H7-V1: frames from a kept state run forward with no pads (A's capture script; B's tools are not edited).

    python3 capture_frames.py --content <game file> --state <kept copy> --rule <rule.json> --out <run folder>
                              --work <temp folder> --seconds 40 [--stop-after-reset 20] [--every 0.5]
                              [--opt <the hub's core options file> ...]

RetroArch starts as B95's tool starts it (tools/h7_minigame_proof.py's Session: the hub's AppImage and core, its
persistent config as the base, temp saves / states / system folders, the null joypad driver, the game file read in
place) with three additions on the calling side only:
  - screenshot_directory in the temp folder (RetroArch's default is the game file's own folder — never written here),
    auto-named, no on-screen notice;
  - the hub's own core options file(s) copied into the temp config before the start (--opt), so the picture is drawn
    as the hub draws it (the render scale);
  - nothing else changed.
The state (a temp copy of the kept copy) is loaded paused (RetroArch's own load line required, as B95), then resumed.
Every --every seconds from the resume: RetroArch's SCREENSHOT command, and the rule's two values (READ_CORE_RAM).
Each frame is stored as JPEG (quality 90, at most 640 px wide) with an index CSV (seconds, file, P1, P2, the change
from the frame before: the mean absolute difference of a 64x48 grey copy, 0-255) and contact sheets (30 frames each).
The run stops at --seconds, or --stop-after-reset seconds after both values return to full having been lower (a new
round), whichever is first. Prints one JSON line.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
import h7_minigame_proof as proof  # noqa: E402  (B95's tool, imported, not edited)
from PIL import Image, ImageDraw, ImageChops, ImageStat  # noqa: E402


class CaptureSession(proof.Session):
    """B95's Session, started the same way, with the screenshot folder and the hub's core options added."""

    def __init__(self, content: Path, system: str, work: Path, opts: list[Path]):
        self.core, self.library = proof.SYSTEMS[system]
        self.work = work
        for d in ("saves", "states", "system", "xdg", "cheats", "shots"):
            (work / d).mkdir(parents=True, exist_ok=True)
        self.content = Path(content).resolve()
        if not self.content.is_file():
            raise proof.ProofError("the game file is not there")
        optdir = work / "xdg" / "retroarch" / "config" / self.library
        optdir.mkdir(parents=True, exist_ok=True)
        self.opts = []
        for o in opts:
            shutil.copyfile(o, optdir / o.name)
            self.opts.append(o.name)
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
                # H7-V1's additions
                "screenshot_directory": work / "shots", "screenshots_in_content_dir": "false",
                "auto_screenshot_filename": "true", "notification_show_screenshot": "false",
                "game_specific_options": "true"}
        lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over]
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


def read_values(s: CaptureSession, r: dict) -> tuple[int | None, int | None]:
    out = []
    for p in r["players"]:
        try:
            out.append(proof.value_of(s.ask(f"READ_CORE_RAM {p['address']:x} {p['bytes']}", 0.3), p["address"],
                                      p["bytes"], p["endian"]))
        except proof.ProofError:
            out.append(None)
    return out[0], out[1]


def small_grey(img: Image.Image) -> Image.Image:
    return img.convert("L").resize((64, 48), Image.BILINEAR)


def contact_sheets(rows: list[dict], out: Path, per: int = 30, cols: int = 6) -> int:
    n = 0
    for i in range(0, len(rows), per):
        chunk = rows[i:i + per]
        tw, th = 200, 150
        lines = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, lines * (th + 16)), (0, 0, 0))
        d = ImageDraw.Draw(sheet)
        for k, r in enumerate(chunk):
            im = Image.open(out / r["file"]).convert("RGB")
            im.thumbnail((tw, th))
            x, y = (k % cols) * tw, (k // cols) * (th + 16)
            sheet.paste(im, (x, y))
            d.text((x + 4, y + th + 2), f"{r['seconds']:.1f} s", fill=(255, 255, 0))
        n += 1
        sheet.save(out / f"sheet_{n:02d}.jpg", quality=85)
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--rule", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--stop-after-reset", type=float, default=None)
    ap.add_argument("--every", type=float, default=0.5)
    ap.add_argument("--opt", action="append", default=[])
    a = ap.parse_args(argv)
    out, work = Path(a.out), Path(a.work)
    out.mkdir(parents=True, exist_ok=False)
    work.mkdir(parents=True, exist_ok=False)
    r = proof.parse_rule(json.loads(Path(a.rule).read_text()))
    temp_state = work / "copy.state"
    shutil.copyfile(a.state, temp_state)                              # the kept copy is only read
    s = CaptureSession(Path(a.content), "ps1", work, [Path(o) for o in a.opt])
    rows: list[dict] = []
    result: dict = {"opts_given": s.opts}
    try:
        s.wait_playing(30)
        s.pause()
        result["load_line"] = s.load_state(temp_state)
        shots = work / "shots"
        s.resume()
        t0 = time.monotonic()
        k, prev, full_seen_low, reset_at, capture_size = 0, None, False, None, None
        while True:
            target = t0 + k * a.every
            now = time.monotonic()
            if target > now:
                time.sleep(target - now)
            t = time.monotonic() - t0
            if t > a.seconds or (reset_at is not None and t > reset_at + a.stop_after_reset):
                break
            before = set(shots.iterdir())
            s.send("SCREENSHOT")
            p1, p2 = read_values(s, r)
            new, end = None, time.monotonic() + 0.45
            while time.monotonic() < end:
                fresh = [p for p in set(shots.iterdir()) - before if p.suffix == ".png"]
                if fresh:
                    time.sleep(0.03)
                    new = fresh[0]
                    break
                time.sleep(0.01)
            row = {"seconds": round(t, 2), "file": "", "P1": p1, "P2": p2, "change": ""}
            if new is not None:
                try:
                    im = Image.open(new)
                    im.load()
                except Exception:
                    time.sleep(0.1)
                    im = Image.open(new)
                    im.load()
                capture_size = capture_size or f"{im.width}x{im.height}"
                im = im.convert("RGB")
                if im.width > 640:
                    im = im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS)
                name = f"f{k:04d}_{t:07.2f}s.jpg"
                im.save(out / name, quality=90)
                g = small_grey(im)
                if prev is not None:
                    row["change"] = round(ImageStat.Stat(ImageChops.difference(g, prev)).mean[0], 2)
                prev = g
                row["file"] = name
                new.unlink()                                          # A's own temp PNG, converted
            if p1 is not None and p2 is not None and a.stop_after_reset is not None:
                if p1 < 140 or p2 < 140:
                    full_seen_low = True
                elif full_seen_low and reset_at is None and p1 == 140 and p2 == 140:
                    reset_at = t
            rows.append(row)
            k += 1
        result.update({"frames": sum(1 for x in rows if x["file"]), "ticks": len(rows),
                       "missed": sum(1 for x in rows if not x["file"]),
                       "seconds_covered": rows[-1]["seconds"] if rows else 0, "capture_size": capture_size,
                       "reset_at": reset_at})
    finally:
        s.close()
    with (out / "index.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["seconds", "file", "P1", "P2", "change"])
        w.writeheader()
        w.writerows(rows)
    result["sheets"] = contact_sheets([x for x in rows if x["file"]], out)
    result["stored_size"] = None
    for x in rows:
        if x["file"]:
            im = Image.open(out / x["file"])
            result["stored_size"] = f"{im.width}x{im.height}"
            break
    log = (work / "retroarch.log").read_text(errors="replace")
    result["core_options_lines"] = [l.strip() for l in log.splitlines() if ".opt" in l and "Core Options" in l][:4]
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
