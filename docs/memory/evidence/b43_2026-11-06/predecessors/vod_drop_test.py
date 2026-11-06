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
"""
from __future__ import annotations

import ctypes
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
        return handler_class

    def poll_once(self) -> dict | None:
        sig = self._signature()
        if sig is None or sig == self._last:
            return None
        self._last = sig
        return self.drop_now()

    def drop_now(self) -> dict:
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
        for out in (self._out, self._range_out):
            if out is not None:
                try:
                    out.write(row)
                except Exception:
                    pass  # a row must never disturb the server
        return row

    def _run(self) -> None:
        while True:
            time.sleep(self._interval)
            try:
                self.poll_once()
            except Exception:
                pass

    def start(self) -> "DropTest":
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="vod-drop-test", daemon=True)
            self._thread.start()
        return self


def drop_test_from_environ(environ: Mapping[str, str], project_root: Path, range_log: Any = None) -> DropTest | None:
    return DropTest(project_root, range_log=range_log) if enabled(environ) else None
