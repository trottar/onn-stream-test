#!/usr/bin/env python3
"""H7's first step (B93): a mini game as "a save state + a fixed time + a win rule read from game memory".

    python3 tools/h7_minigame_proof.py --content <rom> --system snes --state <file> --seconds 10 --rule <rule.json>
    python3 tools/h7_minigame_proof.py ... --no-state                      # from boot (a control)
    python3 tools/h7_minigame_proof.py --content <rom> --system snes --make-state <out> [--after 1.0] [--write 0x0104=01]

RetroArch runs headless in temp folders (the hub's AppImage and cores, its persistent config as the base, the joypad
driver null, no stream; the hub's own saves and states are never touched): start → PLAYING → the state copied into the
temp states folder and loaded with LOAD_STATE_SLOT 0 (RetroArch's own log line is the evidence) → run --seconds →
pause → read each player's value (READ_CORE_RAM / READ_CORE_MEMORY) → QUIT. Prints one JSON line.

The rule (JSON): {"players": [{"name": "P1", "address": "0x0100", "bytes": 2, "endian": "little"}, ...],
                  "winner": "max" | "min", "memory": "ram" | "memory"}
Run with DISPLAY / XAUTHORITY of the companion's session (RetroArch needs a display).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APP = REPO / "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORES = REPO / "runtime/emulators/retroarch/cores-linux"
SYSTEMS = {   # system → (core file, the core's library name: RetroArch's per-core states folder)
    "snes": ("snes9x_libretro.so", "Snes9x"),
    "n64": ("mupen64plus_next_libretro.so", "Mupen64Plus-Next"),
    "ps1": ("mednafen_psx_hw_libretro.so", "Beetle PSX HW"),
}


class ProofError(RuntimeError):
    pass


def parse_rule(rule: dict) -> dict:
    players = rule.get("players")
    if not isinstance(players, list) or len(players) < 2:
        raise ProofError("the rule needs at least two players")
    out = []
    for p in players:
        n = int(p.get("bytes", 1))
        if n not in (1, 2, 4):
            raise ProofError("a player's value is 1, 2 or 4 bytes")
        if p.get("endian", "little") not in ("little", "big"):
            raise ProofError("endian is little or big")
        out.append({"name": str(p["name"]), "address": int(str(p["address"]), 0), "bytes": n,
                    "endian": p.get("endian", "little")})
    if rule.get("winner", "max") not in ("max", "min"):
        raise ProofError("winner is max or min")
    if rule.get("memory", "ram") not in ("ram", "memory"):
        raise ProofError("memory is ram or memory")
    return {"players": out, "winner": rule.get("winner", "max"), "memory": rule.get("memory", "ram")}


def decide(values: dict[str, int], winner: str) -> str:
    best = (max if winner == "max" else min)(values.values())
    top = [k for k, v in values.items() if v == best]
    return top[0] if len(top) == 1 else "tie"


def value_of(answer: str | None, address: int, n: int, endian: str) -> int:
    """`READ_CORE_RAM <addr> <b1> <b2> …` → the value; `… -1` (no memory there) → ProofError."""
    parts = (answer or "").split()
    if len(parts) < 3 or parts[2] == "-1" or len(parts) < 2 + n:
        raise ProofError(f"no memory answer at {address:#x}")
    try:
        data = bytes(int(b, 16) for b in parts[2:2 + n])
    except ValueError as exc:
        raise ProofError(f"an unreadable memory answer at {address:#x}") from exc
    return int.from_bytes(data, endian)


class Session:
    def __init__(self, content: Path, system: str, work: Path):
        if system not in SYSTEMS:
            raise ProofError(f"system not supported: {system}")
        self.core, self.library = SYSTEMS[system]
        self.work = work
        for d in ("saves", "states", "system", "xdg", "cheats"):
            (work / d).mkdir(parents=True, exist_ok=True)
        self.content = work / content.name
        shutil.copyfile(content, self.content)          # a copy: the library's file is only read
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        self.port = s.getsockname()[1]
        s.close()
        base = (REPO / "data/games/retroarch/retroarch.cfg").read_text()
        over = {"savefile_directory": work / "saves", "savestate_directory": work / "states",
                "system_directory": work / "system", "cheat_database_path": work / "cheats",
                "network_cmd_enable": "true", "network_cmd_port": self.port, "input_joypad_driver": "null",
                "history_list_enable": "false", "config_save_on_exit": "false", "savestate_auto_save": "false",
                "savestate_auto_load": "false", "savestate_thumbnail_enable": "false",
                "joypad_autoconfig_dir": work / "system", "pause_nonactive": "false"}
        lines = [l for l in base.splitlines() if l.split("=")[0].strip() not in over]
        (work / "session.cfg").write_text("\n".join(lines + [f'{k} = "{v}"' for k, v in over.items()]) + "\n")
        self.logf = work / "retroarch.log"
        self.log = self.logf.open("w")
        self.proc = subprocess.Popen(
            [str(APP), "--config", str(work / "session.cfg"), "--verbose", "-L", str(CORES / self.core),
             str(self.content)], cwd=str(APP.parent), stdin=subprocess.DEVNULL, stdout=self.log,
            stderr=subprocess.STDOUT, env=dict(os.environ, XDG_CONFIG_HOME=str(work / "xdg")), start_new_session=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))

    def ask(self, command: str, wait: float = 0.5) -> str | None:
        """Send `command`; return RetroArch's answer to it (late answers to earlier commands are dropped)."""
        self.sock.setblocking(False)
        try:
            while True:
                self.sock.recvfrom(65536)
        except (BlockingIOError, OSError):
            pass
        self.sock.sendto(command.encode(), ("127.0.0.1", self.port))
        end = time.monotonic() + wait
        word = command.split()[0]
        while True:
            left = end - time.monotonic()
            if left <= 0:
                return None
            self.sock.settimeout(left)
            try:
                answer = self.sock.recvfrom(65536)[0].decode(errors="replace").strip()
            except (socket.timeout, OSError):
                return None
            if answer.split()[:1] == [word]:
                return answer

    def send(self, command: str) -> None:
        self.sock.sendto(command.encode(), ("127.0.0.1", self.port))

    def text(self) -> str:
        self.log.flush()
        return self.logf.read_text(errors="replace")

    def wait_playing(self, bound: float = 20.0) -> None:
        end = time.monotonic() + bound
        while time.monotonic() < end:
            if self.proc.poll() is not None:
                raise ProofError("RetroArch exited during startup")
            if "PLAYING" in (self.ask("GET_STATUS", 0.2) or ""):
                return
            time.sleep(0.05)
        raise ProofError("RetroArch did not reach PLAYING")

    def state_path(self) -> Path:
        d = self.work / "states" / self.library
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{self.content.stem}.state"

    def load_state(self, state: Path, bound: float = 10.0) -> str:
        shutil.copyfile(state, self.state_path())
        before = len(self.text())
        self.send("LOAD_STATE_SLOT 0")
        end = time.monotonic() + bound
        while time.monotonic() < end:
            for line in self.text()[before:].splitlines():
                if "[State]" in line and "oad" in line and self.content.stem in line:
                    return line.strip()
            time.sleep(0.05)
        raise ProofError("RetroArch did not report the state loaded")

    def save_state(self, out: Path, bound: float = 10.0) -> None:
        target = self.state_path()
        if target.exists():
            target.unlink()
        self.send("SAVE_STATE_SLOT 0")
        end = time.monotonic() + bound
        while time.monotonic() < end:
            if target.is_file() and target.stat().st_size > 0:
                time.sleep(0.3)
                shutil.copyfile(target, out)
                return
            time.sleep(0.05)
        raise ProofError("RetroArch did not write the state")

    def pause(self) -> None:
        if "PLAYING" in (self.ask("GET_STATUS", 0.3) or ""):
            self.send("PAUSE_TOGGLE")
            end = time.monotonic() + 3
            while time.monotonic() < end and "PAUSED" not in (self.ask("GET_STATUS", 0.2) or ""):
                time.sleep(0.05)

    def close(self) -> None:
        try:
            self.send("QUIT")
            self.proc.wait(5)
        except Exception:
            pass
        if self.proc.poll() is None:
            os.killpg(self.proc.pid, signal.SIGKILL)
            self.proc.wait(5)
        self.log.close()
        self.sock.close()


def run_proof(content: Path, system: str, state: Path | None, seconds: float, rule: dict) -> dict:
    r = parse_rule(rule)
    work = Path(tempfile.mkdtemp(prefix="h7_proof_"))
    s = Session(content, system, work)
    try:
        s.wait_playing()
        out: dict = {"system": system, "seconds": seconds, "state_loaded": False}
        if state is not None:
            s.load_state(state)
            out["state_loaded"] = True
        time.sleep(seconds)
        s.pause()
        command = "READ_CORE_RAM" if r["memory"] == "ram" else "READ_CORE_MEMORY"
        values = {p["name"]: value_of(s.ask(f"{command} {p['address']:x} {p['bytes']}"), p["address"], p["bytes"],
                                      p["endian"]) for p in r["players"]}
        out["values"] = values
        out["winner"] = decide(values, r["winner"])
        return out
    finally:
        s.close()
        shutil.rmtree(work, ignore_errors=True)


def make_state(content: Path, system: str, out: Path, after: float, writes: list[tuple[int, bytes]]) -> dict:
    work = Path(tempfile.mkdtemp(prefix="h7_state_"))
    s = Session(content, system, work)
    try:
        s.wait_playing()
        time.sleep(after)
        for address, data in writes:
            s.send(f"WRITE_CORE_RAM {address:x} " + " ".join(f"{b:02x}" for b in data))
            time.sleep(0.1)
        s.save_state(out)
        return {"state_written": True, "bytes": out.stat().st_size, "writes": len(writes)}
    finally:
        s.close()
        shutil.rmtree(work, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--content", required=True, type=Path)
    ap.add_argument("--system", default="snes", choices=sorted(SYSTEMS))
    ap.add_argument("--state", type=Path)
    ap.add_argument("--no-state", action="store_true")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--rule", type=Path)
    ap.add_argument("--make-state", type=Path)
    ap.add_argument("--after", type=float, default=1.0)
    ap.add_argument("--write", action="append", default=[], help="ADDRESS=HEXBYTES for --make-state, e.g. 0x0104=01")
    a = ap.parse_args(argv)
    try:
        if a.make_state:
            writes = [(int(w.split("=")[0], 0), bytes.fromhex(w.split("=")[1])) for w in a.write]
            print(json.dumps(make_state(a.content, a.system, a.make_state, a.after, writes)))
            return 0
        if a.rule is None or (a.state is None and not a.no_state):
            ap.error("--rule and --state (or --no-state) are needed")
        print(json.dumps(run_proof(a.content, a.system, None if a.no_state else a.state, a.seconds,
                                   json.loads(a.rule.read_text()))))
        return 0
    except ProofError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
