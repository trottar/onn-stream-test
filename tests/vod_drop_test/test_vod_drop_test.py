"""B40: a hub-side VOD drop for the bench, behind PRIVYHUB_VOD_DROP_TEST=1 (per-run, never adopted).

Loopback only. A real RangeRequestHandler (a subclass, so the module's own class is never touched) over a temp root
with a 16 MiB file under vod/; a fake player (a raw socket) that reads part of the body and then stops reading, as a
player with a full buffer does. The trigger is a file appended to; nothing is deleted. Absent = today: the module is
not imported, the class is the base file's, and the base and the new server give the same bytes.
"""
from __future__ import annotations

import ast
import ipaddress
import json
import os
import socket
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
BASE = Path(os.environ.get("B40_BASE_COMPANION", "/tmp/b_q02m_base/companion"))

import range_server  # noqa: E402
import vod_drop_test  # noqa: E402
import vod_log  # noqa: E402

LOOP = str(ipaddress.ip_address(0x7F000001))
SIZE = 16 * 1024 * 1024     # more than loopback's socket buffers hold: the server is mid-body when the player stops
TITLE = "A Long Feature (2026).mkv"


def _payload() -> bytes:
    return (bytes(range(251)) * (SIZE // 251 + 1))[:SIZE]


def _get(path: str, rng: str | None = None) -> bytes:
    lines = [f"GET {path} HTTP/1.1", "Host: hub", "Connection: close"]
    if rng:
        lines.append(f"Range: {rng}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode()


class _Server:
    def __init__(self, root: Path, handler_cls: type) -> None:
        handler = partial(handler_cls, directory=str(root), vod_directory=str(root / "vod"))
        self.httpd = ThreadingHTTPServer((LOOP, 0), handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.httpd.handle_error = lambda *a: None      # the injected resets: no traceback noise in the test output
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


class _Player:
    """A fake player: one open-ended GET, a part of the body read, then no reading (a full buffer)."""

    def __init__(self, port: int, path: str, rng: str = "bytes=0-", first: int = 100 * 1024) -> None:
        self.s = socket.create_connection((LOOP, port), timeout=5)
        self.s.sendall(_get(path, rng))
        self.got = b""
        while len(self.got) < first:
            chunk = self.s.recv(65536)
            if not chunk:
                break
            self.got += chunk

    def read_rest(self) -> str:
        """Read until the end: `eof` (the whole body arrived) or the error's name."""
        try:
            while True:
                chunk = self.s.recv(1 << 20)
                if not chunk:
                    return "eof"
                self.got += chunk
        except OSError as exc:
            return type(exc).__name__
        finally:
            self.s.close()

    def body(self) -> bytes:
        return self.got.split(b"\r\n\r\n", 1)[1]


def _wait_streaming(test: vod_drop_test.DropTest, n: int = 1, timeout: float = 5.0) -> None:
    end = time.time() + timeout
    while time.time() < end:
        with test._lock:
            if len(test._live) >= n:
                return
        time.sleep(0.01)
    raise AssertionError("no stream in flight")


class DropTestCase(unittest.TestCase):
    with_range_log = False

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "media"
        (self.root / "vod").mkdir(parents=True)
        (self.root / "vod" / TITLE).write_bytes(_payload())
        (self.root / "live").mkdir()
        (self.root / "live" / "channel.ts").write_bytes(_payload())
        self.project = Path(self.tmp.name) / "project"
        (self.project / "runtime").mkdir(parents=True)
        cls = type("Dropped", (range_server.RangeRequestHandler,), {})
        cls.log_message = lambda *a, **k: None
        self.range_log = vod_log.RangeLog(self.project) if self.with_range_log else None
        if self.range_log is not None:
            self.range_log.install(cls)
        self.test = self.make_test()
        self.test.install(cls)
        self.server = _Server(self.root, cls)
        self.path = "/vod/" + TITLE.replace(" ", "%20").replace("(", "%28").replace(")", "%29") + "?media_token=secret"

    def make_test(self, **kw) -> vod_drop_test.DropTest:
        return vod_drop_test.DropTest(self.project, range_log=self.range_log, **kw)

    def tearDown(self) -> None:
        self.server.close()
        self.tmp.cleanup()

    def touch(self) -> None:
        """A appends one line (the bench's command); the file is never removed."""
        with open(self.project / vod_drop_test.TRIGGER, "a") as fh:
            fh.write("2026-11-02T20:00:00Z\n")

    def rows(self, name: str = vod_drop_test.LOG_NAME, n: int = 0, timeout: float = 5.0) -> list[dict]:
        p = self.project / "logs" / name
        end = time.time() + timeout
        while True:
            rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
            if len(rows) >= n or time.time() > end:
                return rows
            time.sleep(0.02)

    def assert_redacted(self, row: dict) -> None:
        text = json.dumps(row)
        for bad in ("Long", "Feature", "mkv", "vod/", "secret", "media_token", "channel", LOOP, "2026-11-02T20"):
            self.assertNotIn(bad, text)


class TheDrop(DropTestCase):
    def test_a_player_mid_stream_gets_one_reset_at_the_trigger(self) -> None:
        player = _Player(self.server.port, self.path)
        _wait_streaming(self.test)
        self.assertIsNone(self.test.poll_once())               # no trigger yet: nothing
        self.touch()
        row = self.test.poll_once()
        self.assertEqual(player.read_rest(), "ConnectionResetError")
        self.assertLess(len(player.body()), SIZE)
        self.assertEqual((row["event"], row["trigger"], row["dropped"], row["how"]), ("vod_drop_injected", 1, 1, "rst"))
        self.assertEqual(row["ids"], [vod_log.opaque_id(self.path)])
        self.assertRegex(row["ids"][0], r"^[0-9a-f]{12}$")
        self.assertEqual(self.rows(), [row])
        self.assert_redacted(row)
        self.assertIsNone(self.test.poll_once())               # consumed: one drop per trigger
        self.assertTrue((self.project / vod_drop_test.TRIGGER).exists())   # nothing deleted

    def test_no_trigger_no_drop(self) -> None:
        player = _Player(self.server.port, self.path)
        _wait_streaming(self.test)
        for _ in range(3):
            self.assertIsNone(self.test.poll_once())
        self.assertEqual(player.read_rest(), "eof")
        self.assertEqual(player.body(), _payload())
        self.assertEqual(self.rows(), [])

    def test_a_trigger_left_from_before_the_start_never_fires(self) -> None:
        self.touch()
        self.touch()
        fresh = self.make_test()                               # the baseline is taken here
        self.assertIsNone(fresh.poll_once())
        self.touch()
        self.assertEqual(fresh.poll_once()["trigger"], 1)

    def test_two_appends_two_drops_one_each(self) -> None:
        for n in (1, 2):
            player = _Player(self.server.port, self.path)
            _wait_streaming(self.test)
            self.touch()
            row = self.test.poll_once()
            self.assertEqual((row["trigger"], row["dropped"]), (n, 1))
            self.assertEqual(player.read_rest(), "ConnectionResetError")
        self.assertIsNone(self.test.poll_once())
        self.assertEqual([r["trigger"] for r in self.rows()], [1, 2])

    def test_a_trigger_with_nothing_in_flight_is_consumed(self) -> None:
        self.touch()
        row = self.test.poll_once()
        self.assertEqual((row["dropped"], row["ids"], row["how"]), (0, [], "none"))
        player = _Player(self.server.port, self.path)          # the next stream is not dropped
        _wait_streaming(self.test)
        self.assertIsNone(self.test.poll_once())
        self.assertEqual(player.read_rest(), "eof")

    def test_a_path_outside_vod_is_never_dropped(self) -> None:
        live = _Player(self.server.port, "/live/channel.ts")
        time.sleep(0.2)
        self.touch()
        row = self.test.poll_once()
        self.assertEqual(row["dropped"], 0)
        self.assertEqual(live.read_rest(), "eof")
        self.assertEqual(live.body(), _payload())

    def test_the_fallback_without_libc_connect_is_a_shutdown_and_says_so(self) -> None:
        self.test._connect = None
        player = _Player(self.server.port, self.path)
        _wait_streaming(self.test)
        self.touch()
        row = self.test.poll_once()
        self.assertEqual((row["dropped"], row["how"]), (1, "shutdown"))
        self.assertIn(player.read_rest(), ("eof", "ConnectionResetError"))
        self.assertLess(len(player.body()), SIZE)

    def test_the_thread_polls_by_itself(self) -> None:
        self.test._interval = 0.05
        self.test.start()
        player = _Player(self.server.port, self.path)
        _wait_streaming(self.test)
        self.touch()
        self.assertEqual(player.read_rest(), "ConnectionResetError")
        self.assertEqual(self.rows(n=1)[0]["dropped"], 1)


class WithTheRangeLog(DropTestCase):
    with_range_log = True

    def test_the_injection_the_reset_and_the_reconnect_in_one_file(self) -> None:
        player = _Player(self.server.port, self.path)
        _wait_streaming(self.test)
        self.touch()
        injected = self.test.poll_once()
        self.assertEqual(player.read_rest(), "ConnectionResetError")
        pos = 4_321_000
        resumed = _Player(self.server.port, self.path, rng=f"bytes={pos}-", first=0)
        self.assertEqual(resumed.read_rest(), "eof")
        self.assertEqual(resumed.body(), _payload()[pos:])
        self.assertIn(b"206 Partial Content", resumed.got.split(b"\r\n", 1)[0])
        rows = self.rows(vod_log.RANGE_LOG_NAME, n=3)
        # the file's order is the order the rows were written (the reset's handler may finish first); the times say
        # what happened when: the injection inside the reset request's span, the reconnect after it
        self.assertEqual(sorted(r["event"] for r in rows), ["vod_drop_injected", "vod_range", "vod_range"])
        self.assertIn(injected, rows)
        reset_row, again = [r for r in rows if r["event"] == "vod_range"]
        self.assertEqual((reset_row["closed"], reset_row["range"]), ("client_reset", "bytes=0-"))
        self.assertLess(reset_row["bytes"], SIZE)
        self.assertEqual((again["closed"], again["range"], again["status"]), ("complete", f"bytes={pos}-", 206))
        self.assertEqual(reset_row["id"], injected["ids"][0])
        self.assertTrue(reset_row["at_utc"] <= injected["at_utc"] <= reset_row["end_utc"] <= again["at_utc"])
        self.assertEqual(self.rows(), [injected])              # its own file too
        for r in rows:
            self.assert_redacted(r)


class Absent(unittest.TestCase):
    def test_flag_parse(self) -> None:
        for v, on in (("1", True), (" 1 ", True), ("", False), ("0", False), ("true", False), ("yes", False),
                      (None, False)):
            env = {} if v is None else {"PRIVYHUB_VOD_DROP_TEST": v}
            self.assertEqual(vod_drop_test.enabled(env), on, v)
            self.assertEqual(vod_drop_test.drop_test_from_environ(env, Path("/nonexistent")) is not None, on)

    def test_absent_imports_nothing_and_leaves_the_class_alone(self) -> None:
        base_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys, threading, range_server; print(range_server.VOD_DROP_TEST is None, "
                "'vod_drop_test' in sys.modules, range_server.RangeRequestHandler.copyfile.__qualname__, "
                "any(t.name == 'vod-drop-test' for t in threading.enumerate()))")
        for v in (None, "", "0", "true", "yes"):
            env = dict(base_env)
            if v is not None:
                env["PRIVYHUB_VOD_DROP_TEST"] = v
            out = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "companion", env=env,
                                 capture_output=True, text=True, check=True).stdout.split()
            self.assertEqual(out, ["True", "False", "RangeRequestHandler.copyfile", "False"], v)

    def test_on_installs_and_starts(self) -> None:
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        env["PRIVYHUB_VOD_DROP_TEST"] = "1"
        code = ("import threading, range_server; print(range_server.VOD_DROP_TEST is not None, "
                "range_server.RangeRequestHandler.copyfile.__qualname__, "
                "any(t.name == 'vod-drop-test' for t in threading.enumerate()))")
        with tempfile.TemporaryDirectory() as d:
            out = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "companion", env=env,
                                 capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(out, ["True", "DropTest.install.<locals>.copyfile", "True"])

    def test_the_module_minus_the_guarded_block_is_the_base(self) -> None:
        if not (BASE / "range_server.py").exists():
            self.skipTest("no base copy")
        new = ast.parse((ROOT / "companion" / "range_server.py").read_text())
        old = ast.parse((BASE / "range_server.py").read_text())
        old_dumps = [ast.dump(o) for o in old.body]
        added = [n for n in new.body if ast.dump(n) not in old_dumps]
        # B47 (disclosed): the PRIVYHUB_VOD_LOG block gained the SIGTERM row; B40's two nodes are checked as before
        log_guard = "if os.environ.get('PRIVYHUB_VOD_LOG', '').strip() == '1':"
        b47 = [n for n in added if ast.unparse(n).startswith(log_guard)]
        self.assertLessEqual(len(b47), 1)
        drop = [n for n in added if n not in b47]
        self.assertEqual([ast.unparse(n) for n in drop][0], "VOD_DROP_TEST = None")
        self.assertEqual(len(drop), 2)
        self.assertTrue(ast.unparse(drop[1]).startswith(
            "if os.environ.get('PRIVYHUB_VOD_DROP_TEST', '').strip() == '1':"))
        old_rest = [d for o, d in zip(old.body, old_dumps) if not (b47 and ast.unparse(o).startswith(log_guard))]
        self.assertEqual([ast.dump(n) for n in new.body if n not in added], old_rest)

    def test_the_same_bytes_from_the_base_and_the_new_server(self) -> None:
        if not (BASE / "range_server.py").exists():
            self.skipTest("no base copy")
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "vod").mkdir()
            (root / "vod" / "f.bin").write_bytes(_payload()[:200_000])
            (root / "runtime").mkdir()
            (root / "runtime" / "vod_drop_test.trigger").write_text("x\n")
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
                                _get("/vod/f.bin", "bytes=999999-")):
                        c = socket.create_connection((LOOP, port), timeout=5)
                        c.sendall(req)
                        raw = b""
                        while True:
                            chunk = c.recv(65536)
                            if not chunk:
                                break
                            raw += chunk
                        c.close()
                        got.append(b"\r\n".join(x for x in raw.split(b"\r\n") if not x.startswith(b"Date:")))
                    with open(root / "runtime" / "vod_drop_test.trigger", "a") as fh:
                        fh.write("y\n")                      # a trigger with the flag absent: nothing happens
                    time.sleep(0.6)
                    self.assertIsNone(p.poll())
                    outs.append(got)
                finally:
                    p.terminate()
                    p.wait(5)
            self.assertEqual(outs[0], outs[1])
            self.assertFalse((root / "logs").exists())


if __name__ == "__main__":
    unittest.main()
