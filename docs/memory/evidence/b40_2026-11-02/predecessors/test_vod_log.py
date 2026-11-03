"""B35: the range server's per-request log and the movie player's retry rows, behind PRIVYHUB_VOD_LOG=1.

Loopback only. A real RangeRequestHandler (a subclass, so the module's own class is never touched) with the log
installed, over a temp root with a 16 MiB file under vod/. Absent = today: the module imports nothing new, the class
is the base file's AST, and the same request gets the same bytes from the base and the new server.
"""
from __future__ import annotations

import ast
import ipaddress
import json
import os
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
BASE = Path(os.environ.get("B35_BASE_COMPANION", "/tmp/b_q31l_base/companion"))

import range_server  # noqa: E402
import vod_log  # noqa: E402

LOOP = str(ipaddress.ip_address(0x7F000001))
SIZE = 16 * 1024 * 1024     # more than loopback's socket buffers hold, so a reset lands mid-body
TITLE = "A Long Feature (2026).mkv"


def _payload() -> bytes:
    return (bytes(range(251)) * (SIZE // 251 + 1))[:SIZE]


class _Server:
    def __init__(self, root: Path, handler_cls: type) -> None:
        handler = partial(handler_cls, directory=str(root), vod_directory=str(root / "vod"))
        self.httpd = ThreadingHTTPServer((LOOP, 0), handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.httpd.handle_error = lambda *a: None      # the test's own resets: no traceback noise
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def _raw(port: int, request: bytes, read_limit: int | None = None, reset: bool = False) -> bytes:
    s = socket.create_connection((LOOP, port), timeout=5)
    s.sendall(request)
    got = b""
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            got += chunk
            if read_limit is not None and len(got) >= read_limit:
                break
    finally:
        if reset:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        s.close()
    return got


def _get(path: str, rng: str | None = None, method: str = "GET") -> bytes:
    lines = [f"{method} {path} HTTP/1.1", "Host: hub", "Connection: close"]
    if rng:
        lines.append(f"Range: {rng}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode()


class RangeLogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "media"
        (self.root / "vod").mkdir(parents=True)
        (self.root / "vod" / TITLE).write_bytes(_payload())
        self.project = Path(self.tmp.name) / "project"
        cls = type("Logged", (range_server.RangeRequestHandler,), {})
        cls.log_message = lambda *a, **k: None
        vod_log.RangeLog(self.project).install(cls)
        self.server = _Server(self.root, cls)
        self.path = "/vod/" + TITLE.replace(" ", "%20").replace("(", "%28").replace(")", "%29") + "?media_token=secret"

    def tearDown(self) -> None:
        self.server.close()
        self.tmp.cleanup()

    def rows(self, n: int, timeout: float = 5.0) -> list[dict]:
        p = self.project / "logs" / "vod_range.jsonl"
        end = time.time() + timeout
        while time.time() < end:
            if p.exists():
                rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
                if len(rows) >= n:
                    return rows
            time.sleep(0.02)
        self.fail(f"fewer than {n} rows")

    def assert_redacted(self, row: dict) -> None:
        text = json.dumps(row)
        for bad in ("Long", "Feature", "mkv", "vod/", "secret", "media_token", LOOP):
            self.assertNotIn(bad, text)
        self.assertRegex(row["id"], r"^[0-9a-f]{12}$")

    def test_a_drop_mid_body_is_a_reset_or_broken_pipe_with_the_bytes_so_far(self) -> None:
        _raw(self.server.port, _get(self.path, "bytes=0-"), read_limit=100 * 1024, reset=True)
        row = self.rows(1)[0]
        self.assertEqual(row["event"], "vod_range")
        self.assertEqual(row["method"], "GET")
        self.assertEqual(row["kind"], "vod")
        self.assertEqual(row["range"], "bytes=0-")
        self.assertEqual(row["status"], 206)
        self.assertEqual(row["length"], SIZE)
        self.assertIn(row["closed"], ("client_reset", "broken_pipe"))
        self.assertLess(row["bytes"], SIZE)
        self.assertGreaterEqual(row["duration_ms"], 0)
        self.assertRegex(row["at_utc"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")
        self.assert_redacted(row)

    def test_a_full_read_and_a_resume_at_a_position_are_complete(self) -> None:
        body = _raw(self.server.port, _get(self.path, "bytes=0-"))
        self.assertTrue(body.endswith(_payload()))
        pos = 654_321
        body = _raw(self.server.port, _get(self.path, f"bytes={pos}-"))
        self.assertTrue(body.endswith(_payload()[pos:]))
        a, b = self.rows(2)
        self.assertEqual((a["closed"], a["bytes"], a["status"]), ("complete", SIZE, 206))
        self.assertEqual((b["closed"], b["bytes"], b["range"]), ("complete", SIZE - pos, f"bytes={pos}-"))
        self.assertEqual(a["id"], b["id"])      # the same media, the same opaque id
        self.assert_redacted(a)

    def test_missing_head_and_no_range(self) -> None:
        _raw(self.server.port, _get("/vod/nothing-here.mkv"))
        _raw(self.server.port, _get(self.path, method="HEAD"))
        _raw(self.server.port, _get(self.path))
        _raw(self.server.port, _get(self.path, "bytes=x-"))
        r = self.rows(4)
        self.assertEqual((r[0]["status"], r[0]["closed"]), (404, "no_body"))
        self.assertEqual((r[1]["method"], r[1]["closed"], r[1]["bytes"]), ("HEAD", "no_body", 0))
        self.assertEqual((r[2]["status"], r[2]["closed"], r[2]["bytes"], r[2]["range"]), (200, "complete", SIZE, None))
        self.assertEqual((r[3]["status"], r[3]["range"]), (416, "invalid"))
        for row in r:
            self.assert_redacted(row)


class ClientLogTest(unittest.TestCase):
    def test_the_four_rows_and_nothing_else(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            log = vod_log.ClientLog(Path(d))
            for ev in vod_log.CLIENT_EVENTS:
                log.accept({"event": ev, "media": "0123456789ab", "attempt": 2, "position_ms": 6_600_000,
                            "error_code": 2001, "error_name": "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED",
                            "delay_ms": 2000, "elapsed_ms": 3000, "bound_ms": 150000})
            for bad in ({"event": "other"}, [], {"event": "vod_error", "url": "http://x/y"},
                        {"event": "vod_error", "media": "Long Feature"}, {"event": "vod_error", "attempt": "2"},
                        {"event": "vod_error", "error_name": "failed: http://host/vod/x.mkv"},
                        {"event": "vod_error", "attempt": True}):
                with self.assertRaises(ValueError):
                    log.accept(bad)
            rows = [json.loads(x) for x in (Path(d) / "logs" / "vod_client.jsonl").read_text().splitlines()]
            self.assertEqual([r["event"] for r in rows], list(vod_log.CLIENT_EVENTS))
            self.assertEqual(rows[0]["position_ms"], 6_600_000)
            self.assertIn("at_utc", rows[0])


class AbsentTest(unittest.TestCase):
    def test_flag_parse(self) -> None:
        for v, on in (("1", True), (" 1 ", True), ("", False), ("0", False), ("yes", False), (None, False)):
            env = {} if v is None else {"PRIVYHUB_VOD_LOG": v}
            self.assertEqual(vod_log.enabled(env), on, v)
            self.assertEqual(vod_log.range_log_from_environ(env, Path("/nonexistent")) is not None, on)

    def test_absent_imports_nothing_and_leaves_the_class_alone(self) -> None:
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys, range_server; print(range_server.VOD_LOG is None, 'vod_log' in sys.modules, "
                "range_server.RangeRequestHandler.do_GET.__qualname__, "
                "range_server.RangeRequestHandler.copyfile.__qualname__)")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "companion", env=env,
                             capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(out, ["True", "False", "RangeRequestHandler.do_GET", "RangeRequestHandler.copyfile"])
        env["PRIVYHUB_VOD_LOG"] = "0"
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "companion", env=env,
                             capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(out[:2], ["True", "False"])

    def test_the_class_ast_is_the_base_files(self) -> None:
        if not (BASE / "range_server.py").exists():
            self.skipTest("no base copy")

        def cls(p: Path) -> str:
            tree = ast.parse(p.read_text())
            return ast.dump(next(n for n in tree.body if isinstance(n, ast.ClassDef)))

        self.assertEqual(cls(ROOT / "companion" / "range_server.py"), cls(BASE / "range_server.py"))
        new = ast.parse((ROOT / "companion" / "range_server.py").read_text())
        old = ast.parse((BASE / "range_server.py").read_text())
        added = [ast.unparse(n) for n in new.body if ast.dump(n) not in {ast.dump(o) for o in old.body}]
        self.assertEqual(len(added), 2, added)          # VOD_LOG = None, and the guarded block
        self.assertTrue(added[1].startswith("if os.environ.get('PRIVYHUB_VOD_LOG', '').strip() == '1':"))

    def test_the_same_bytes_from_the_base_and_the_new_server(self) -> None:
        if not (BASE / "range_server.py").exists():
            self.skipTest("no base copy")
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "vod").mkdir()
            (root / "vod" / "f.bin").write_bytes(_payload()[:200_000])
            outs = []
            for comp in (BASE, ROOT / "companion"):
                s = socket.socket()
                s.bind((LOOP, 0))
                port = s.getsockname()[1]
                s.close()
                p = subprocess.Popen([sys.executable, str(comp / "range_server.py"), "--root", str(root),
                                      "--vod-root", str(root / "vod"), "--host", LOOP, "--port", str(port)],
                                     cwd=d, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    for _ in range(100):
                        try:
                            socket.create_connection((LOOP, port), timeout=0.2).close()
                            break
                        except OSError:
                            time.sleep(0.05)
                    got = []
                    for req in (_get("/vod/f.bin", "bytes=1000-"), _get("/vod/f.bin"), _get("/vod/none"),
                                _get("/vod/f.bin", method="HEAD"), _get("/vod/f.bin", "bytes=999999-")):
                        raw = _raw(port, req)
                        got.append(b"\r\n".join(x for x in raw.split(b"\r\n") if not x.startswith(b"Date:")))
                    outs.append(got)
                finally:
                    p.terminate()
                    p.wait(5)
            self.assertEqual(outs[0], outs[1])
            self.assertFalse((root / "logs").exists())

    def test_the_service_blocks_are_guarded(self) -> None:
        tree = ast.parse((ROOT / "companion" / "privyhub_service.py").read_text())
        top = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any("vod_log" in t for t in top))
        guarded = [n for n in tree.body if isinstance(n, ast.If) and "vod_log" in ast.unparse(n)]
        self.assertEqual(len(guarded), 1)
        self.assertIn("os.environ.get('PRIVYHUB_VOD_LOG', '').strip() == '1'", ast.unparse(guarded[0].test))
        uses = [n for n in ast.walk(tree) if isinstance(n, ast.If) and "/diagnostics/vod-client" in ast.unparse(n.test)]
        self.assertEqual(len(uses), 1)
        self.assertTrue(ast.unparse(uses[0].test).startswith(
            "(_vod_client_log := globals().get('VOD_CLIENT_LOG')) is not None and"))


if __name__ == "__main__":
    unittest.main()
