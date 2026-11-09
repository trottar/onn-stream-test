"""B71: "Change disc" on a multi-disc PS1 session (an `.m3u` with more than one disc), over RetroArch's network
command port.

RetroArch 1.22.2 has `DISK_EJECT_TOGGLE`, `DISK_NEXT` and `DISK_PREV` over the port (no argument, no reply, no
set-index, no index query), so the index is read from RetroArch's own log lines in the game log:
`[Disc] Setting disc in tray: k/n[ - <label>]`, `[Disc] Removed disk from tray.`, `[Disc] Ejected virtual disc tray.`,
`[Disc] Closed virtual disc tray.` and the `Failed to ...` forms. Only the two numbers are ever read; the label is
never kept or logged.

The sequence is the Quick Menu's, with the game left paused: open the tray, step the selected disc to the target
(each step confirmed by its line), close the tray; 0.4 s between commands. `PRIVYHUB_DISC_SWAP=0` = today (no
multi-disc session is ever recognised, the action unknown). Design: docs/memory/evidence/b71_2026-11-09/.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Callable

ENV = "PRIVYHUB_DISC_SWAP"
EJECT = "DISK_EJECT_TOGGLE"
NEXT = "DISK_NEXT"
PREV = "DISK_PREV"
GAP_S = 0.4                 # between commands: each in its own pass of RetroArch's loop
LINE_BOUND_S = 1.5          # each command's own log line
POLL_S = 0.05
CONTROL = "retroarch_network_disk_control"

SET_RE = re.compile(r"\[Disc\] Setting disc in tray: (\d+)/(\d+)")
REMOVED_RE = re.compile(r"\[Disc\] Removed dis[ck] from tray")
EJECTED_RE = re.compile(r"\[Disc\] Ejected virtual disc tray")
CLOSED_RE = re.compile(r"\[Disc\] Closed virtual disc tray")
FAILED_RE = re.compile(r"\[Disc\] Failed to (?:set disc|remove dis[ck]|eject virtual disc tray|close virtual disc tray)")


class DiscSwapError(Exception):
    disc: int | None = None          # the disc RetroArch last reported (None = unknown)


def enabled(environ: Any = None) -> bool:
    env = os.environ if environ is None else environ
    return (env.get(ENV) or "").strip() != "0"


def m3u_discs(path: Path) -> int:
    """The disc lines of an `.m3u` (non-empty, not `#`); 0 when unreadable."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip() and not line.strip().startswith("#"))


def session_for(content_path: Any, system: str, environ: Any = None) -> dict[str, Any] | None:
    """`{"discs": n, "disc": 1}` for a PS1 `.m3u` launch with n > 1 (the knob on); else None (= today)."""
    if not enabled(environ) or str(system or "").strip().lower() != "ps1":
        return None
    p = Path(str(content_path or ""))
    if p.suffix.lower() != ".m3u":
        return None
    n = m3u_discs(p)
    return {"discs": n, "disc": 1} if n > 1 else None


def last_index(text: str, discs: int) -> int | None:
    """The newest `Setting disc in tray: k/n` with this n (1-based); None when there is none."""
    found = None
    for m in SET_RE.finditer(text or ""):
        if int(m.group(2)) == int(discs):
            found = int(m.group(1))
    return found


class LogTail:
    """Reads the game log from an offset (the only reader of RetroArch's disc lines)."""

    def __init__(self, path: Any, offset: int = 0):
        self.path = Path(str(path)) if path else None
        self.offset = int(offset)

    def read(self) -> str:
        if self.path is None:
            return ""
        try:
            with self.path.open("rb") as h:
                h.seek(self.offset)
                data = h.read(256 * 1024)
        except OSError:
            return ""
        self.offset += len(data)
        return data.decode("utf-8", errors="replace")


class Swapper:
    """One swap: `send(cmd)` puts a command on the port; `tail` reads the log; `clock` / `sleep` injectable."""

    def __init__(self, send: Callable[[str], Any], tail: LogTail, discs: int,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep):
        self.send, self.tail, self.discs = send, tail, int(discs)
        self.clock, self.sleep = clock, sleep
        self.sent: list[str] = []
        self.buf = ""

    def _cmd(self, cmd: str) -> None:
        self.sent.append(cmd)
        self.send(cmd)

    def _await(self, *patterns: re.Pattern) -> re.Match | None:
        """The first line matching any pattern (or a failure line) within the bound; None at the bound."""
        deadline = self.clock() + LINE_BOUND_S
        while True:
            self.buf += self.tail.read()
            best = None
            for p in (*patterns, FAILED_RE):
                m = p.search(self.buf)
                if m and (best is None or m.start() < best.start()):
                    best = m
            if best is not None:
                self.buf = self.buf[best.end():]
                return best
            if self.clock() >= deadline:
                return None
            self.sleep(POLL_S)

    def run(self, current: int | None, target: int) -> dict[str, Any]:
        n = self.discs
        steps = 0
        self.buf += self.tail.read()          # anything before the first command is not ours
        self.buf = ""
        self._cmd(EJECT)
        m = self._await(EJECTED_RE)
        if m is None or m.re is FAILED_RE:
            err = DiscSwapError("the tray did not open" if m is None else "RetroArch could not open the tray")
            err.disc = current
            raise err
        cur = current
        try:
            while cur != target:
                if steps >= 2 * n:
                    raise DiscSwapError(f"disc {target} not reached in {steps} steps")
                self.sleep(GAP_S)
                self._cmd(NEXT if (cur is None or cur < target) else PREV)
                steps += 1
                m = self._await(SET_RE, REMOVED_RE)
                if m is None:
                    raise DiscSwapError("no disc line from RetroArch")
                if m.re is FAILED_RE:
                    raise DiscSwapError("RetroArch could not set the disc")
                if m.re is REMOVED_RE:
                    cur = n + 1                # past the end: no disc selected
                else:
                    if int(m.group(2)) != n:
                        raise DiscSwapError("the disc count RetroArch reports differs")
                    cur = int(m.group(1))
        except DiscSwapError as exc:
            self._close()
            err = DiscSwapError(str(exc))
            err.disc = cur if cur is None or 1 <= cur <= n else None
            raise err from exc
        self.sleep(GAP_S)
        if not self._close():
            err = DiscSwapError("the tray did not close")
            err.disc = cur
            raise err
        return {"disc": cur, "steps": steps}

    def _close(self) -> bool:
        self._cmd(EJECT)
        m = self._await(CLOSED_RE)
        return m is not None and m.re is CLOSED_RE
