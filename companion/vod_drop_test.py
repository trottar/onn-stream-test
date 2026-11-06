"""B40: a hub-side VOD connection drop for the bench, only with `PRIVYHUB_VOD_DROP_TEST=1` (per-run, never adopted).

Absent = today: this module is never imported, the range server's handler class is not touched, no thread runs.

- The control is a file, `<repo>/runtime/vod_drop_test.trigger`, appended to from a shell on the hub
  (`mkdir -p runtime && date -u +%FT%TZ >> runtime/vod_drop_test.trigger`). A thread polls its (mtime_ns, size)
  every 250 ms; the signature at the start is the baseline (a stale trigger never fires); each change fires one drop.
  The file is never written, read or removed here (consumed by its signature, nothing deleted).
- The drop: every `/vod/` connection streaming a body is reset -- SO_LINGER {1, 0}, then a Linux `connect()` with
  AF_UNSPEC (tcp_disconnect: a RST; a writer blocked in sendall wakes with ConnectionResetError, so B35's row reads
  `client_reset`, and the player's next read fails at once). Fallback `shutdown(SHUT_RDWR)`, said in the row.
- One `vod_drop_injected` row per trigger into `logs/vod_drop_test.jsonl`, and into B35's `logs/vod_range.jsonl`
  when that log is on. Redacted by construction: opaque ids only.

Design: `docs/memory/evidence/b40_2026-11-02/design_written_before_code.md`.

B43: the appended line may say `drop <seconds>` (0-600): after the one reset, every new `/vod/` request is answered by
an immediate RST and no HTTP response for that long (a dead link, as the player sees it: its own reconnect then runs out
of buffer and gives up, so B35's retry runs). Only the appended bytes are read (opened read-only from the last seen
size; the file is still never written or removed). Any other line, or `drop 0`, is B40 as built, its row byte for
byte. `vod_drop_injected` gains `refuse_s` (only when > 0); a `vod_refuse_ended` row (`vod_refused`, the count) closes
each window. Design: `docs/memory/evidence/b43_2026-11-06/design_written_before_code.md`.
"""
from __future__ import annotations

import ctypes
import re
import socket
import struct
import threading
import time
from pathlib import Path
from typing import Any, Mapping

from vod_log import _Writer, _kind, opaque_id, utc_ms

FLAG_ENV = "PRIVYHUB_VOD_DROP_TEST"
TRIGGER = Path("runtime") / "vod_drop_test.trigger"
LOG_NAME = "vod_drop_test.jsonl"
INTERVAL_S = 0.25
# B43: the refusal window's line, its cap, and how much of an append is read
_DROP_LINE = re.compile(r"^\s*drop\s+(\d{1,6}(?:\.\d{1,3})?)\s*$")
REFUSE_MAX_S = 600.0
READ_MAX = 4096


def refuse_seconds(appended: bytes) -> float:
    """B43: the last non-empty line `drop <seconds>` → seconds (capped); anything else → 0 (B40's one-shot)."""
    lines = [ln for ln in appended.decode("utf-8", "replace").splitlines() if ln.strip()]
    if not lines:
        return 0.0
    m = _DROP_LINE.match(lines[-1])
    return min(float(m.group(1)), REFUSE_MAX_S) if m else 0.0


def enabled(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


class _SockaddrUnspec(ctypes.Structure):
    _fields_ = [("sa_family", ctypes.c_ushort), ("sa_data", ctypes.c_char * 14)]


def _libc_connect():
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        return libc.connect
    except (OSError, AttributeError):
        return None


def reset(sock: socket.socket, connect=None) -> str:
    """Abort one TCP connection: `rst` (AF_UNSPEC connect) or, failing that, `shutdown`."""
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    except OSError:
        pass
    if connect is not None:
        sa = _SockaddrUnspec(socket.AF_UNSPEC)
        if connect(sock.fileno(), ctypes.byref(sa), ctypes.sizeof(sa)) == 0:
            return "rst"
    sock.shutdown(socket.SHUT_RDWR)
    return "shutdown"


class DropTest:
    def __init__(self, project_root: Path, *, range_log: Any = None, clock=time.time,
                 interval: float = INTERVAL_S, connect: Any = "libc") -> None:
        self.trigger = Path(project_root) / TRIGGER
        self._out = _Writer(project_root, LOG_NAME)
        self._range_out = getattr(range_log, "_out", None)
        self._clock = clock
        self._interval = interval
        self._connect = _libc_connect() if connect == "libc" else connect
        self._lock = threading.Lock()
        self._live: dict[int, tuple[socket.socket, str]] = {}
        self._last = self._signature()
        self.triggers = 0
        # B43: the refusal window (none = B40 as built)
        self._refuse_until: float | None = None
        self._refuse_s = 0.0
        self._refuse_trigger = 0
        self.refused = 0
        self._thread: threading.Thread | None = None

    def _signature(self):
        try:
            st = self.trigger.stat()
        except OSError:
            return None
        return (st.st_mtime_ns, st.st_size)

    def install(self, handler_class: type) -> type:
        test = self
        orig_copyfile = handler_class.copyfile

        def copyfile(self, source, outputfile):
            path = getattr(self, "path", "") or ""
            if _kind(path) != "vod":
                return orig_copyfile(self, source, outputfile)
            key = id(self)
            with test._lock:
                test._live[key] = (self.connection, opaque_id(path))
            try:
                return orig_copyfile(self, source, outputfile)
            finally:
                with test._lock:
                    test._live.pop(key, None)

        handler_class.copyfile = copyfile

        # B43: inside a refusal window a /vod/ request is reset before anything else runs (no gate, no file, no log)
        for name in ("do_GET", "do_HEAD"):
            orig = getattr(handler_class, name)

            def refusing(self, _orig=orig):
                path = getattr(self, "path", "") or ""
                if _kind(path) == "vod" and test._refusing():
                    test._refuse(self)
                    return None
                return _orig(self)

            setattr(handler_class, name, refusing)
        return handler_class

    def _refusing(self) -> bool:
        with self._lock:
            return self._refuse_until is not None and self._clock() < self._refuse_until

    def _refuse(self, handler: Any) -> None:
        handler.close_connection = True
        try:
            reset(handler.connection, self._connect)
        except OSError:
            pass
        with self._lock:
            self.refused += 1

    def poll_once(self) -> dict | None:
        sig = self._signature()
        if sig is None or sig == self._last:
            return None
        before = self._last
        self._last = sig
        return self.drop_now(self._appended_refuse_s(before, sig))

    def _appended_refuse_s(self, before, sig) -> float:
        """B43: only the bytes appended since the last signature (read-only); a shrunk / new file → 0."""
        old_size = before[1] if before is not None else 0
        new_size = sig[1]
        if new_size <= old_size:
            return 0.0
        try:
            with open(self.trigger, "rb") as fh:
                fh.seek(old_size)
                data = fh.read(min(new_size - old_size, READ_MAX))
        except OSError:
            return 0.0
        return refuse_seconds(data)

    def tick(self) -> dict | None:
        """B43: a window past its end closes with its row (the polling thread calls this)."""
        with self._lock:
            if self._refuse_until is None or self._clock() < self._refuse_until:
                return None
        return self._end_window()

    def _end_window(self) -> dict | None:
        with self._lock:
            if self._refuse_until is None:
                return None
            row = {"at_utc": utc_ms(self._clock()), "event": "vod_refuse_ended", "trigger": self._refuse_trigger,
                   "refuse_s": self._refuse_s, "vod_refused": self.refused}
            self._refuse_until = None
            self._refuse_s = 0.0
            self.refused = 0
        self._write(row)
        return row

    def _write(self, row: dict) -> None:
        for out in (self._out, self._range_out):
            if out is not None:
                try:
                    out.write(row)
                except Exception:
                    pass  # a row must never disturb the server

    def drop_now(self, refuse_s: float = 0.0) -> dict:
        if self._refuse_until is not None:
            self._end_window()   # B43: a new trigger closes the open window first
        self.triggers += 1
        t = self._clock()   # before the resets: the row's time falls inside the reset request's span
        with self._lock:
            live = list(self._live.values())
        ids, hows, errors = [], set(), []
        for sock, media in live:
            try:
                hows.add(reset(sock, self._connect))
                ids.append(media)
            except OSError as exc:
                errors.append(type(exc).__name__)
        row = {"at_utc": utc_ms(t), "event": "vod_drop_injected", "trigger": self.triggers,
               "dropped": len(ids), "ids": ids,
               "how": "/".join(sorted(hows)) if hows else "none"}
        if errors:
            row["errors"] = errors
        if refuse_s > 0:
            # B43: the refusal window starts with the reset (row key only when > 0: B40's row as built otherwise)
            row["refuse_s"] = refuse_s
            with self._lock:
                self._refuse_until = t + refuse_s
                self._refuse_s = refuse_s
                self._refuse_trigger = self.triggers
                self.refused = 0
        self._write(row)
        return row

    def _run(self) -> None:
        while True:
            time.sleep(self._interval)
            try:
                self.poll_once()
                self.tick()
            except Exception:
                pass

    def start(self) -> "DropTest":
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="vod-drop-test", daemon=True)
            self._thread.start()
        return self


def drop_test_from_environ(environ: Mapping[str, str], project_root: Path, range_log: Any = None) -> DropTest | None:
    return DropTest(project_root, range_log=range_log) if enabled(environ) else None
