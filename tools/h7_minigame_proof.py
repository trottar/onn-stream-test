#!/usr/bin/env python3
"""H7's first step (B93): a mini game as "a save state + a fixed time + a win rule read from game memory".

    python3 tools/h7_minigame_proof.py --content <rom> --system snes --state <file> --seconds 10 --rule <rule.json>
    python3 tools/h7_minigame_proof.py ... --no-state                      # from boot (a control)
    python3 tools/h7_minigame_proof.py ... --as-is [--runs 3]               # B95: the state read as it stands
    python3 tools/h7_minigame_proof.py --content <rom> --system snes --make-state <out> [--after 1.0] [--write 0x0104=01]

RetroArch runs headless in temp folders (the hub's AppImage and cores, its persistent config as the base, the joypad
driver null, no stream; the hub's own saves and states are never touched): start → PLAYING → the state copied into the
temp states folder and loaded with LOAD_STATE_SLOT 0 (RetroArch's own log line is the evidence) → run --seconds →
pause → read each player's value (READ_CORE_RAM / READ_CORE_MEMORY) → QUIT. Prints one JSON line.

The rule (JSON): {"players": [{"name": "P1", "address": "0x0100", "bytes": 2, "endian": "little"}, ...],
                  "winner": "max" | "min", "memory": "ram" | "memory",
                  "none_when": "equal" | {"floor": V}}            # B95: "no winner yet", distinct from a tie
            or B94's single field: {"address": "0x…", "bytes": 1, "values": {"P1": v1, "P2": v2}, "none_value": v0}

B95: --as-is (or --seconds 0) pauses first and loads the state paused: no frame runs before the read (0 frames, measured
on the fixtures of snes9x, Beetle PSX HW and Mupen64Plus-Next). --runs N repeats the whole load-and-read with a fresh
RetroArch and reports the agreement ("k of N"); a disagreement is reported ("winner": "disagree"), never hidden.

The proof (B95, replacing B93's): Met on a real game when, read as they stand, the 'end' state names the player the TV
showed, the 'begin' state names no winner, and — where the user has made one — an 'end' state won by another player
names that player; the same on 3 loads each. The fixed run with real players is tested later, on the stream.
Run with DISPLAY / XAUTHORITY of the companion's session (RetroArch needs a display).
"""
from __future__ import annotations

import argparse
import json
import os
import re
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
    if rule.get("memory", "ram") not in ("ram", "memory"):
        raise ProofError("memory is ram or memory")
    if "address" in rule and not rule.get("players"):            # B95: B94's single winner field
        n = int(rule.get("bytes", 1))
        if n not in (1, 2, 4) or not isinstance(rule.get("values"), dict) or len(rule["values"]) < 2:
            raise ProofError("a single-field rule needs 1, 2 or 4 bytes and a value per winner")
        return {"field": {"name": "field", "address": int(str(rule["address"]), 0), "bytes": n,
                          "endian": rule.get("endian", "little")},
                "values": {str(k): int(v) for k, v in rule["values"].items()},
                "none_value": None if rule.get("none_value") is None else int(rule["none_value"]),
                "memory": rule.get("memory", "ram")}
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
    none_when = rule.get("none_when")
    if not (none_when is None or none_when == "equal"
            or (isinstance(none_when, dict) and isinstance(none_when.get("floor"), int))):
        raise ProofError('none_when is "equal" or {"floor": V}')
    return {"players": out, "winner": rule.get("winner", "max"), "memory": rule.get("memory", "ram"),
            "none_when": none_when}


def decide(values: dict[str, int], winner: str) -> str:
    best = (max if winner == "max" else min)(values.values())
    top = [k for k, v in values.items() if v == best]
    return top[0] if len(top) == 1 else "tie"


def answer(r: dict, values: dict[str, int]) -> tuple[str | None, str | None]:
    """B95: the winner, or None with the reason "no winner yet" (the rule's none_when / a single field's none_value)."""
    if "field" in r:
        v = values["field"]
        if r["none_value"] is not None and v == r["none_value"]:
            return None, "no winner yet"
        hits = [k for k, x in r["values"].items() if x == v]
        return (hits[0], None) if len(hits) == 1 else ("unknown", "a value no rule names")
    nw = r.get("none_when")
    if nw == "equal" and len(set(values.values())) == 1:
        return None, "no winner yet"
    if isinstance(nw, dict) and all(v <= nw["floor"] for v in values.values()):
        return None, "no winner yet"
    return decide(values, r["winner"]), None


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
        # B95: the game read in place (RetroArch only reads it; a .cue keeps its tracks beside it; no large copy)
        self.content = Path(content).resolve()
        if not self.content.is_file():
            raise ProofError("the game file is not there")
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

    LOADING = re.compile(r'\[State\] Loading state ".*", (\d+) bytes\.')

    def load_state(self, state: Path, bound: float = 10.0, settle: float = 1.0) -> str:
        """B95: RetroArch 1.22.2 logs `[State] Loading state "…", N bytes.` — N > 0 when the file was read — and on a
        failure `Failed to load state from "…"`; a load counts when N > 0 and no failure line follows within `settle`."""
        shutil.copyfile(state, self.state_path())
        before = len(self.text())
        self.send("LOAD_STATE_SLOT 0")
        end = time.monotonic() + bound
        seen, line = None, ""
        while time.monotonic() < end:
            new = self.text()[before:]
            if "Failed to load state" in new:
                raise ProofError("RetroArch failed to load the state")
            m = self.LOADING.search(new)
            if m and seen is None:
                if int(m.group(1)) == 0:
                    raise ProofError("RetroArch read 0 bytes of the state")
                seen, line = time.monotonic(), m.group(0)
            if seen is not None and time.monotonic() - seen >= settle:
                return line
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
            self.proc.wait(1)
        except Exception:
            pass
        if self.proc.poll() is None:                   # B95: a paused RetroArch does not act on QUIT; SIGTERM first
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(3)
            except Exception:
                pass
        if self.proc.poll() is None:
            os.killpg(self.proc.pid, signal.SIGKILL)
            self.proc.wait(5)
        self.log.close()
        self.sock.close()


def run_once(content: Path, system: str, state: Path | None, seconds: float, r: dict, as_is: bool = False) -> dict:
    """One fresh RetroArch: load (paused first when as-is: no frame runs), run `seconds` unless as-is, pause, read."""
    work = Path(tempfile.mkdtemp(prefix="h7_proof_"))
    s = Session(content, system, work)
    try:
        s.wait_playing()
        out: dict = {"system": system, "seconds": 0 if as_is else seconds, "state_loaded": False}
        if as_is:
            s.pause()
            out["as_is"] = True
        if state is not None:
            s.load_state(state)
            out["state_loaded"] = True
        if not as_is:
            time.sleep(seconds)
            s.pause()
        command = "READ_CORE_RAM" if r["memory"] == "ram" else "READ_CORE_MEMORY"
        fields = [r["field"]] if "field" in r else r["players"]
        values = {p["name"]: value_of(s.ask(f"{command} {p['address']:x} {p['bytes']}"), p["address"], p["bytes"],
                                      p["endian"]) for p in fields}
        out["values"] = values
        winner, reason = answer(r, values)
        out["winner"] = winner
        if reason:
            out["reason"] = reason
        return out
    finally:
        s.close()
        shutil.rmtree(work, ignore_errors=True)


def run_proof(content: Path, system: str, state: Path | None, seconds: float, rule: dict, as_is: bool = False,
              runs: int = 1) -> dict:
    r = parse_rule(rule)
    as_is = as_is or seconds == 0
    if runs <= 1:
        return run_once(content, system, state, seconds, r, as_is)
    return agree([run_once(content, system, state, seconds, r, as_is) for _ in range(runs)])


def agree(results: list[dict]) -> dict:
    """B95: N runs in one line — the agreed winner only when every run names it; else "disagree"."""
    names = [json.dumps(x.get("winner")) for x in results]
    top = max(set(names), key=names.count)
    k = names.count(top)
    out = {k2: v for k2, v in results[0].items() if k2 not in ("values", "winner", "reason")}
    out.update({"runs": len(results), "agreement": f"{k} of {len(results)}",
                "winner": json.loads(top) if k == len(results) else "disagree",
                "per_run": [{"winner": x.get("winner"), "values": x.get("values"),
                             **({"reason": x["reason"]} if x.get("reason") else {})} for x in results]})
    if k == len(results) and results[0].get("reason"):
        out["reason"] = results[0]["reason"]
    return out


def make_state(content: Path, system: str, out: Path, after: float, writes: list[tuple[int, bytes]]) -> dict:
    work = Path(tempfile.mkdtemp(prefix="h7_state_"))
    s = Session(content, system, work)
    try:
        s.wait_playing()
        time.sleep(after)
        s.pause()                                      # B95: written and saved paused — the state holds what was written
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
    ap.add_argument("--as-is", action="store_true", help="B95: read the state as it stands (no frame run)")
    ap.add_argument("--runs", type=int, default=1, help="B95: repeat the whole load-and-read; the agreement reported")
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
                                   json.loads(a.rule.read_text()), a.as_is, a.runs)))
        return 0
    except ProofError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
