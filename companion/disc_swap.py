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


# B74: RetroArch's disk index record (`<savefile dir>/<core library name>/<content stem>.ldci`, JSON with `image_index`
# / `image_path`), read at the launch and handed to the core's set_initial_image: the set starts on the last disc used.
# The host sets it to the asked disc (1 unless the user chose one) before RetroArch starts. Paths are never returned or
# logged. Design: docs/memory/evidence/b74_2026-11-09/.
LDCI_SUFFIX = ".ldci"
CORE_LIBRARY_DIRS = {"mednafen_psx_hw_libretro": "Beetle PSX HW", "mednafen_psx_libretro": "Beetle PSX"}
CFG_SAVEFILE_RE = re.compile(r'^\s*savefile_directory\s*=\s*"([^"]*)"\s*$', re.M)


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


# --- B74: the set starts on disc 1 (or the disc asked for) ------------------------------------------------------------

def parse_start_disc(value: Any, discs: int) -> int:
    """The disc a launch asks for: 1..n, anything else (absent, malformed, out of range) -> 1."""
    try:
        j = int(str(value).strip())
    except (TypeError, ValueError):
        return 1
    return j if 1 <= j <= int(discs) else 1


def m3u_entries(path: Any) -> list[str]:
    """The `.m3u`'s disc lines (non-empty, not `#`), as written; [] when unreadable."""
    try:
        text = Path(str(path)).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return []
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def savefile_dir_from_config(config_path: Any) -> Path | None:
    """`savefile_directory` of the session config the launch wrote (None when absent / unreadable)."""
    try:
        text = Path(str(config_path)).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    found = CFG_SAVEFILE_RE.findall(text)
    return Path(found[-1]) if found and found[-1].strip() else None


def ldci_set(savefile_dir: Any, core_name: str, content_path: Any, disc: int) -> str:
    """Make RetroArch's record for this content say `disc` (1-based) before RetroArch starts.

    "set"  : a record was written (an existing one changed, or a new one for a disc > 1);
    "kept" : the record already says that disc (its bytes untouched);
    "none" : no record and disc 1 (RetroArch's own start: nothing written);
    "error": the content / record could not be read or written (the launch goes on; RetroArch decides).
    Never deletes; the write is a temp file in the same folder, then a replace; the record's other keys are kept.
    """
    import json
    try:
        content = Path(str(content_path))
        entries = m3u_entries(content)
        j = int(disc)
        if not entries or not 1 <= j <= len(entries) or not savefile_dir:
            return "error"
        root = Path(str(savefile_dir))
        name = content.stem + LDCI_SUFFIX
        want_index, want_path = j - 1, str(content.parent / entries[j - 1])
        found = [root / name] if (root / name).is_file() else []
        if root.is_dir():
            found += sorted(d / name for d in root.iterdir() if d.is_dir() and (d / name).is_file())
        if not found:
            if j == 1:
                return "none"
            lib = CORE_LIBRARY_DIRS.get(Path(str(core_name)).stem)
            found = [(root / lib / name) if lib else (root / name)]
        result = "kept"
        for rec in found:
            data: dict[str, Any] = {}
            if rec.is_file():
                try:
                    loaded = json.loads(rec.read_text(encoding="utf-8"))
                    data = loaded if isinstance(loaded, dict) else {}
                except (OSError, ValueError):
                    data = {}
                index = data.get("image_index")
                if index == want_index and (j == 1 or data.get("image_path") == want_path):
                    continue
            data.setdefault("version", "1.0")
            data["image_index"] = want_index
            data["image_path"] = want_path
            rec.parent.mkdir(parents=True, exist_ok=True)
            tmp = rec.with_name(rec.name + ".privyhub-tmp")
            tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            os.replace(tmp, rec)
            result = "set"
        return result
    except Exception:
        return "error"


def first_index(text: str, discs: int) -> int | None:
    """The first `Setting disc in tray: k/n` with this n: the disc the launch put in the tray."""
    for m in SET_RE.finditer(text or ""):
        if int(m.group(2)) == int(discs):
            return int(m.group(1))
    return None
