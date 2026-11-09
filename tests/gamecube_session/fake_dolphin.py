"""B69 tests: a fake Dolphin -- a fake /proc tree (the started PID's `CPU thread` with a clock that grows while it runs),
a fake `xdotool` / `pactl` runner (the F10 toggle, Shift+F<n> writing a fake state file 0.2 s later, F<n> a load),
fake signals and a fake window grab. No real process, display or file outside the test's temp dir."""

from __future__ import annotations

import signal
import types
from pathlib import Path

FAKE_ID = "FAKE01"          # a made-up game id (the state file's prefix)


class FakeDolphin:
    def __init__(self, root: Path, pid: int = 4242, *, rate: float = 30.0, hotkeys: bool = True,
                 clock_ok: bool = True, window: bool = True, writes_state: bool = True, picture: str = "moving",
                 save_delay: float = 0.2, user_dir: Path | None = None, sink: bool = True) -> None:
        self.root = Path(root)
        self.proc = self.root / "proc"
        self.pid = pid
        self.rate = rate
        self.hotkeys = hotkeys
        self.clock_ok = clock_ok
        self.has_window = window
        self.writes_state = writes_state
        self.picture = picture
        self.save_delay = save_delay
        self.sink = sink
        self.user_dir = Path(user_dir) if user_dir is not None else self.root / "user"
        self.t = 0.0
        self.ticks = 100.0
        self.paused = False
        self.stopped = False
        self.keys: list[str] = []
        self.signals: list[int] = []
        self.loaded: list[int] = []
        self.pending: list[tuple[float, int]] = []
        self.saves = 0
        self.cmds: list[list[str]] = []
        self.ignore_keys = 0                            # the next N keys are not read (a missed key)
        self.task = self.proc / str(pid) / "task"
        (self.task / str(pid)).mkdir(parents=True, exist_ok=True)
        (self.task / str(pid) / "comm").write_text("AppRun\n")
        if clock_ok:
            (self.task / str(pid + 1)).mkdir(parents=True, exist_ok=True)
            (self.task / str(pid + 1) / "comm").write_text("CPU thread\n")
        (self.task / str(pid + 2)).mkdir(parents=True, exist_ok=True)
        (self.task / str(pid + 2) / "comm").write_text("Video thread\n")
        self._write()

    # -- the clock -------------------------------------------------------------------------------------------------
    def running(self) -> bool:
        return not (self.paused or self.stopped)

    def _write(self) -> None:
        if self.clock_ok:
            u = int(self.ticks)
            (self.task / str(self.pid + 1) / "stat").write_text(
                f"{self.pid + 1} (CPU thread) S 1 1 1 0 -1 0 0 0 0 0 {u} 0 0 0 20 0 9 0 0 0 0\n")

    def sleep(self, d: float) -> None:
        self.t += d
        if self.running():
            self.ticks += self.rate * d
        self._write()
        due = [p for p in self.pending if p[0] <= self.t]
        self.pending = [p for p in self.pending if p[0] > self.t]
        for _, n in due:
            self._state_file(n)

    def clock(self) -> float:
        return self.t

    # -- the keys, the signals, the picture ----------------------------------------------------------------------
    def _state_file(self, n: int) -> None:
        folder = self.user_dir / "StateSaves"
        folder.mkdir(parents=True, exist_ok=True)
        self.saves += 1
        p = folder / f"{FAKE_ID}.s{n:02d}"
        tmp = folder / f"{FAKE_ID}.s{n:02d}.tmp"
        tmp.write_bytes(b"S" * (1000 + self.saves))
        tmp.replace(p)                                  # Dolphin writes a temp file and renames it

    def run(self, cmd, **kw):
        cmd = list(cmd)
        self.cmds.append(cmd)
        if cmd[:2] == ["xdotool", "search"]:
            return types.SimpleNamespace(stdout="77\n" if self.has_window else "")
        if cmd[:2] == ["xdotool", "keyup"]:
            keys = tuple(reversed(cmd[2:]))
            self.keys.append("+".join(keys))
            if self.ignore_keys > 0:
                self.ignore_keys -= 1
            elif self.hotkeys and not self.stopped:
                self._on_key(keys)
        if cmd[:3] == ["pactl", "list", "sink-inputs"]:
            return types.SimpleNamespace(stdout=f'application.process.id = "{self.pid}"\n' if self.sink else "")
        return types.SimpleNamespace(stdout="")

    def _on_key(self, keys: tuple[str, ...]) -> None:
        if keys == ("F10",):
            self.paused = not self.paused
        elif keys[0] == "Shift_L":
            if self.writes_state:
                self.pending.append((self.t + self.save_delay, int(keys[1][1:])))
        else:
            self.loaded.append(int(keys[0][1:]))

    def kill(self, pid: int, sig: int) -> None:
        self.signals.append(int(sig))
        if sig == signal.SIGSTOP:
            self.stopped = True
        elif sig == signal.SIGCONT:
            self.stopped = False

    def grab(self, window: str) -> bytes:
        if self.picture == "static":
            return bytes([100]) * 2304
        frame = int(self.ticks)
        return bytes([40 + frame % 200]) * 2304

    # -- the session (gamecube_session.Session wired to this fake) ------------------------------------------------
    def session(self, gc, log=None, log_path: Path | None = None):
        lines: list[str] = []
        self.lines = lines
        return gc.Session(self.pid, log or lines.append, run=self.run, kill=self.kill, sleep=self.sleep,
                          clock=self.clock, proc_root=self.proc, grab=self.grab, log_path=log_path,
                          user_dir=self.user_dir)
