#!/usr/bin/env python3
"""B47 (host): a range request still open when the range server stops (a companion restart: SIGTERM to the cgroup)
gets its row, `closed: "shutdown"`; a request finishing after the flush writes no second row. Without
PRIVYHUB_VOD_LOG=1 no handler is installed (today). Loopback only; the process test runs a copy of the range server
in a temp tree, so its log is the temp tree's, never the hub's.

    python3 -m unittest discover -s tests/vod_log -p 'test_vod_log_b47.py' -v
"""

from __future__ import annotations

import ipaddress
import json
import os
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import range_server  # noqa: E402
import vod_log  # noqa: E402

LOOP = str(ipaddress.ip_address(0x7F000001))
SIZE = 16 * 1024 * 1024
NAME = "feature-b47.mkv"


def _payload() -> bytes:
    return (bytes(range(251)) * (SIZE // 251 + 1))[:SIZE]


def _open_slow(port: int, rng: str) -> socket.socket:
    """A GET whose client reads a little and then holds the socket (the server blocks once the buffers fill)."""
    s = socket.create_connection((LOOP, port), timeout=5)
    s.sendall(f"GET /vod/{NAME} HTTP/1.1\r\nHost: hub\r\nRange: {rng}\r\nConnection: close\r\n\r\n".encode())
    got = 0
    while got < 200_000:
        got += len(s.recv(65536))
    return s


def _reset(s: socket.socket) -> None:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    s.close()


def _rows(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def _wait(cond, timeout=5.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


class FlushOpen(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        media = Path(self.tmp.name) / "media"
        (media / "vod").mkdir(parents=True)
        (media / "vod" / NAME).write_bytes(_payload())
        self.project = Path(self.tmp.name) / "project"
        cls = type("Logged", (range_server.RangeRequestHandler,), {})
        cls.log_message = lambda *a, **k: None
        self.log = vod_log.RangeLog(self.project)
        self.log.install(cls)
        handler = partial(cls, directory=str(media), vod_directory=str(media / "vod"))
        self.httpd = ThreadingHTTPServer((LOOP, 0), handler)
        self.httpd.daemon_threads = True
        self.httpd.handle_error = lambda *a: None
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.port = self.httpd.server_address[1]
        self.path = self.project / "logs" / "vod_range.jsonl"

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()

    def test_an_open_request_gets_a_shutdown_row_and_no_second_row(self) -> None:
        s = _open_slow(self.port, "bytes=1048576-")
        self.assertTrue(_wait(lambda: len(self.log._open) == 1))
        self.assertEqual(self.log.flush_open(), 1)
        rows = _rows(self.path)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["closed"], r["status"], r["range"]), ("shutdown", 206, "bytes=1048576-"))
        self.assertGreater(r["bytes"], 0)
        self.assertLess(r["bytes"], r["length"])
        self.assertNotIn(NAME, json.dumps(r))
        _reset(s)                                   # the request now ends (reset): no second row
        time.sleep(0.5)
        self.assertEqual(len(_rows(self.path)), 1)
        self.assertEqual(self.log._open, {})

    def test_nothing_open_writes_nothing_and_a_closed_request_is_today(self) -> None:
        self.assertEqual(self.log.flush_open(), 0)
        self.assertFalse(self.path.exists())
        s = socket.create_connection((LOOP, self.port), timeout=5)
        s.sendall(f"GET /vod/{NAME} HTTP/1.1\r\nHost: hub\r\nRange: bytes=0-1023\r\nConnection: close\r\n\r\n".encode())
        while s.recv(65536):
            pass
        s.close()
        self.assertTrue(_wait(lambda: len(_rows(self.path)) == 1))
        self.assertEqual(_rows(self.path)[0]["closed"], "complete")
        self.assertEqual(self.log.flush_open(), 0)


class Process(unittest.TestCase):
    """The range server as the companion runs it, from a copy in a temp tree, then SIGTERM."""

    def run_server(self, with_line: bool):
        tmp = Path(tempfile.mkdtemp(prefix="b47_rs_"))
        comp = tmp / "companion"
        (comp / "games").mkdir(parents=True)
        for f in ("range_server.py", "vod_log.py", "storage_presence.py"):
            shutil.copy(ROOT / "companion" / f, comp / f)
        shutil.copy(ROOT / "companion" / "games" / "log_rotation.py", comp / "games" / "log_rotation.py")
        (comp / "games" / "__init__.py").write_text("")
        media = tmp / "media"
        (media / "vod").mkdir(parents=True)
        (media / "vod" / NAME).write_bytes(_payload())
        with socket.socket() as probe:
            probe.bind((LOOP, 0))
            port = probe.getsockname()[1]
        env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(comp)}
        if with_line:
            env["PRIVYHUB_VOD_LOG"] = "1"
        p = subprocess.Popen([sys.executable, str(comp / "range_server.py"), "--root", str(media), "--host", LOOP,
                              "--port", str(port)], cwd=str(tmp), env=env, stdout=subprocess.DEVNULL,
                             stderr=subprocess.PIPE)
        self.assertTrue(_wait(lambda: _connectable(port), 10), "the range server did not listen")
        return tmp, p, port

    def test_sigterm_with_the_line_writes_the_open_row_and_exits_0(self) -> None:
        tmp, p, port = self.run_server(True)
        try:
            s = _open_slow(port, "bytes=2097152-")
            time.sleep(0.3)
            p.send_signal(signal.SIGTERM)
            self.assertEqual(p.wait(10), 0)
            rows = _rows(tmp / "logs" / "vod_range.jsonl")
            self.assertEqual([r["closed"] for r in rows], ["shutdown"])
            self.assertEqual(rows[0]["range"], "bytes=2097152-")
            _reset(s)
        finally:
            if p.poll() is None:
                p.kill()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_sigterm_without_the_line_is_todays_default_action(self) -> None:
        tmp, p, port = self.run_server(False)
        try:
            s = _open_slow(port, "bytes=0-")
            p.send_signal(signal.SIGTERM)
            self.assertEqual(p.wait(10), -signal.SIGTERM)
            self.assertFalse((tmp / "logs").exists())
            _reset(s)
        finally:
            if p.poll() is None:
                p.kill()
            shutil.rmtree(tmp, ignore_errors=True)


def _connectable(port: int) -> bool:
    try:
        with socket.create_connection((LOOP, port), timeout=0.2):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    unittest.main()
