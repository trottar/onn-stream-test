#!/usr/bin/env python3
"""G3-S3: the range server's handler, in process, byte for byte.

The baseline's `range_server.py` (HEAD, kept as
`fixtures/range_server_predecessor.py.txt`) and the edited one are loaded as
modules and fed the same raw HTTP requests over a fixture media tree: VOD
full and ranged reads (start-end, open-ended, suffix, unsatisfiable), HEAD,
the live HLS playlist, artwork, a missing file, a traversal, a directory
listing, and a request carrying `?media_token=`. With the flag absent every
response (status line, headers, body) and every log line must be identical.
With the gate set (in process, its transport wired to a `SessionGate`):
the LAN as today, the overlay refused without a token and served with the
header or the media token, and the media token masked in the log. No socket
is opened. If `G3_S3_RANGE_REPLAY_OUT` is set, the table is written there.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

from common import LAN_DECLARED, LAN_SRC, LOCAL_SRC, OVERLAY_DECLARED, OVERLAY_SRC, ROOT, make_gate, pair, si
from test_g3s3 import setup_v2

FIX = Path(__file__).resolve().parent / "fixtures"
LABELS = {LAN_SRC: "lan", LOCAL_SRC: "loopback", OVERLAY_SRC: "overlay"}

REQUESTS = [
    ("GET", "/vod/movie.mp4", {}),
    ("GET", "/vod/movie.mp4", {"Range": "bytes=0-1023"}),
    ("GET", "/vod/movie.mp4", {"Range": "bytes=70000-"}),
    ("GET", "/vod/movie.mp4", {"Range": "bytes=-500"}),
    ("GET", "/vod/movie.mp4", {"Range": "bytes=999999-"}),
    ("HEAD", "/vod/movie.mp4", {}),
    ("GET", "/live/stream.m3u8", {}),
    ("GET", "/artwork/game.png", {}),
    ("GET", "/vod/missing.mp4", {}),
    ("GET", "/vod/../secret.txt", {}),
    ("GET", "/live/", {}),
    ("GET", "/vod/movie.mp4?media_token=fixture-value", {"Range": "bytes=0-99"}),
]


def media_tree() -> tuple[Path, Path]:
    base = Path(tempfile.mkdtemp(prefix="g3_s3_range_"))
    root, vod = base / "media", base / "vod"
    (root / "live").mkdir(parents=True)
    (root / "artwork").mkdir()
    vod.mkdir()
    data = b"".join(hashlib.sha256(i.to_bytes(4, "big")).digest() for i in range(2500))   # 80,000 bytes
    (vod / "movie.mp4").write_bytes(data)
    (root / "live" / "stream.m3u8").write_text("#EXTM3U\n#EXT-X-VERSION:3\nseg0.ts\n")
    (root / "artwork" / "game.png").write_bytes(b"\x89PNG fixture")
    (base / "secret.txt").write_text("outside the roots\n")
    for p in (vod / "movie.mp4", root / "live" / "stream.m3u8", root / "artwork" / "game.png"):
        os.utime(p, (1_790_000_000, 1_790_000_000))
    return root, vod


def load(name: str, source: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__file__ = str(ROOT / "companion" / "range_server.py")
    exec(compile(source, f"<{name}>", "exec"), mod.__dict__)
    return mod


def handler_class(mod: types.ModuleType):
    class Fixed(mod.RangeRequestHandler):   # deterministic Date / Server / log time
        def version_string(self) -> str:
            return "PrivyHubMedia/0.3 Python/fixture"

        def date_time_string(self, timestamp=None) -> str:
            return "Thu, 01 Jan 2026 00:00:00 GMT"

        def log_date_time_string(self) -> str:
            return "01/Jan/2026 00:00:00"

    return Fixed


def run(cls, root: Path, vod: Path, method: str, target: str, source: str,
        headers: dict[str, str] | None = None) -> tuple[bytes, str]:
    lines = [f"{method} {target} HTTP/1.0"] + [f"{k}: {v}" for k, v in (headers or {}).items()]
    raw = ("\r\n".join(lines) + "\r\n\r\n").encode()
    h = cls.__new__(cls)
    h._range = None
    h._vod_directory = Path(os.path.abspath(vod))
    h.directory = str(root)
    h.rfile = io.BytesIO(raw)
    h.wfile = io.BytesIO()
    h.client_address = (source, 50123)
    h.server = SimpleNamespace()
    h.request = None
    h.close_connection = True
    err, sys.stderr = sys.stderr, io.StringIO()
    try:
        h.handle_one_request()
        log = sys.stderr.getvalue()
    finally:
        sys.stderr = err
    return h.wfile.getvalue(), log


def short(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:12]


def wired_gate():
    g = make_gate()

    def transport(url, body):
        st, payload = g.session_route("POST", si.MEDIA_CHECK_PATH, json.loads(body), None, LOCAL_SRC)
        return st, json.dumps(payload).encode()

    return g, si.MediaGate("v2", g.devices._file.path.parent, g.audit.path, classifier=g.classifier,
                           transport=transport)


class RangeReplay(unittest.TestCase):
    table: list[str] = []

    @classmethod
    def setUpClass(cls):
        cls.root, cls.vod = media_tree()
        cls.before = load("range_before", (FIX / "range_server_predecessor.py.txt").read_text())
        cls.after = load("range_after", (ROOT / "companion" / "range_server.py").read_text())
        cls.table = ["| source | request | baseline | flag absent | v2 (the gate) |", "| --- | --- | --- | --- | --- |"]

    @classmethod
    def tearDownClass(cls):
        out = os.environ.get("G3_S3_RANGE_REPLAY_OUT")
        if out:
            Path(out).write_text("\n".join(cls.table) + "\n")

    def test_flag_absent_byte_for_byte(self):
        self.assertIsNone(self.after.RANGE_GATE)   # the environment carries no flag here
        before, after = handler_class(self.before), handler_class(self.after)
        for method, target, headers in REQUESTS:
            for src in (LAN_SRC, LOCAL_SRC, OVERLAY_SRC):
                a, la = run(before, self.root, self.vod, method, target, src, headers)
                b, lb = run(after, self.root, self.vod, method, target, src, headers)
                self.assertEqual(a, b, f"flag absent differs: {method} {target} {headers}")
                self.assertEqual(la, lb, f"log differs: {method} {target}")
                self.assertTrue(a.startswith(b"HTTP/1.0 "))
                rng = f" `{headers['Range']}`" if headers else ""
                self.table.append(f"| {LABELS[src]} | `{method} {target}`{rng} | {short(a)} | identical | (below) |")

    def test_gate_lan_today_overlay_needs_a_token(self):
        g, gate = wired_gate()
        self.after.RANGE_GATE = gate
        try:
            before, after = handler_class(self.before), handler_class(self.after)
            # the LAN with no token, and the hub itself: today's bytes
            for method, target, headers in REQUESTS:
                for src in (LAN_SRC, LOCAL_SRC):
                    a, _ = run(before, self.root, self.vod, method, target, src, headers)
                    b, _ = run(after, self.root, self.vod, method, target, src, headers)
                    if src == LAN_SRC and "media_token=" in target:
                        # a presented credential that fails is refused; it never
                        # falls back to the legacy path (G3-S1's token rule)
                        self.assertIn(b'"reason": "media-token-unknown"', b)
                        continue
                    self.assertEqual(a, b, f"v2 LAN differs: {target}")
            self.table.append("| lan, loopback | all of the above, no token | — | — | identical to the baseline |")
            self.table.append("| lan | `GET /vod/movie.mp4?media_token=fixture-value` (not issued) | — | — | 401 `media-token-unknown` (no fallback) |")
            # the overlay, no token: refused
            raw, _ = run(after, self.root, self.vod, "GET", "/vod/movie.mp4", OVERLAY_SRC, {"Range": "bytes=0-99"})
            self.assertTrue(raw.startswith(b"HTTP/1.0 401"))
            self.assertIn(b'"reason": "legacy-overlay"', raw)
            self.assertNotIn(b"\x89PNG", raw)
            self.table.append("| overlay | `GET /vod/movie.mp4` no token | — | — | 401 `legacy-overlay` |")
            raw, _ = run(after, self.root, self.vod, "HEAD", "/vod/movie.mp4", OVERLAY_SRC)
            self.assertTrue(raw.startswith(b"HTTP/1.0 401"))
            self.assertTrue(raw.endswith(b"\r\n\r\n"))   # HEAD: no body
            # a paired session over the overlay: the header, then the media token
            dev = pair(g)
            st, p = setup_v2(g, dev, source=OVERLAY_SRC, media_host=OVERLAY_DECLARED)
            self.assertEqual(st, 200)
            want, _ = run(before, self.root, self.vod, "GET", "/vod/movie.mp4", LAN_SRC, {"Range": "bytes=0-1023"})
            raw, _ = run(after, self.root, self.vod, "GET", "/vod/movie.mp4", OVERLAY_SRC,
                         {"Range": "bytes=0-1023", si.SESSION_HEADER: p["token"]})
            self.assertEqual(raw, want)
            self.table.append("| overlay | `GET /vod/movie.mp4` `bytes=0-1023` + header | — | — | 206, the baseline's bytes |")
            raw, log = run(after, self.root, self.vod, "GET", "/vod/movie.mp4?media_token=" + p["media_token"],
                           OVERLAY_SRC, {"Range": "bytes=0-1023"})
            self.assertEqual(raw, want)
            self.assertNotIn(p["media_token"], log)
            self.assertIn("media_token=<redacted>", log)
            self.table.append("| overlay | `GET /vod/movie.mp4?media_token=…` `bytes=0-1023` | — | — | 206, the baseline's bytes; the log masks the value |")
            raw, log = run(after, self.root, self.vod, "GET", "/vod/movie.mp4?media_token=forged", OVERLAY_SRC)
            self.assertIn(b'"reason": "media-token-unknown"', raw)
            self.assertNotIn("forged", log)
            self.table.append("| overlay | `GET /vod/movie.mp4?media_token=forged` | — | — | 401 `media-token-unknown` |")
            # a LAN session sends its header: checked, audited once
            raw, _ = run(after, self.root, self.vod, "GET", "/artwork/game.png", LAN_SRC, {si.SESSION_HEADER: p["token"]})
            self.assertTrue(raw.startswith(b"HTTP/1.0 200"))
            events = [json.loads(x)["event"] for x in g.audit.path.read_text().splitlines()]
            self.assertIn("media_session", events)
            self.assertNotIn(p["media_token"], g.audit.path.read_text())
        finally:
            self.after.RANGE_GATE = None


class Glue(unittest.TestCase):
    def test_imported_only_under_the_flag(self):
        import ast
        tree = ast.parse((ROOT / "companion" / "range_server.py").read_text())
        top_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any(getattr(n, "module", "") == "session_identity" for n in top_imports))
        guarded = [n for n in tree.body if isinstance(n, ast.If)
                   and any(isinstance(m, ast.ImportFrom) and m.module == "session_identity" for m in n.body)]
        self.assertEqual(len(guarded), 1)
        self.assertIn("PRIVYHUB_SESSION_IDENTITY", ast.unparse(guarded[0].test))


if __name__ == "__main__":
    unittest.main()
