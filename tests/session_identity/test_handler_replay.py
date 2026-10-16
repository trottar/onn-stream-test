#!/usr/bin/env python3
"""G3-S1: the request handler, in process, byte for byte.

The baseline's `PrivyHubRequestHandler` (`3107fb5`, kept as
`fixtures/handler_predecessor.py.txt`) and the edited one are executed with
the same stubs (plugins, controller) and fed the same raw HTTP requests:

- the D6-R1 suite's companion requests (`GET /plugins/games/native-stream-status`,
  `GET /plugins/games/status`);
- today's client's setup and in-session calls (launch, native-stream-start,
  heartbeat) and `GET /status`.

With the flag absent every response (status line, headers, body) and every
access-log line must be identical. With `v2` on the legacy LAN path the
bodies are identical; the setup calls add one `X-PrivyHub-Session` header.
No socket is opened; no companion runs. If `G3_S1_REPLAY_OUT` is set, the
comparison table is written there (labels only, no address).
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import unittest
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs, urlsplit

from common import (
    LAN_DECLARED, LAN_SRC, LOCAL_SRC, OVERLAY_SRC, ROOT, make_gate, pair, setup, si,
)

FIX = Path(__file__).resolve().parent / "fixtures"
LABELS = {LAN_SRC: "source", LAN_DECLARED: "declared", LOCAL_SRC: "loopback"}

REQUESTS = [
    ("d6-r1", "GET", "/plugins/games/native-stream-status"),
    ("d6-r1", "GET", "/plugins/games/status"),
    ("client", "POST", "/plugins/games/launch?id=fixture-game"),
    ("client", "POST", "/plugins/games/native-stream-start?port=50000"),
    ("client", "POST", "/plugins/games/native-stream-heartbeat?seq=1"),
    ("client", "GET", "/status"),
    ("client", "GET", "/plugins/nosuch/status"),
    # G3-S3: TV-sync, EPG and diagnostics, now carrying the token (tv / diagnostics)
    ("g3-s3", "GET", "/plugins/tv_state/state"),
    ("g3-s3", "GET", "/plugins/epg/guide?channels=a,b&hours=6"),
    ("g3-s3", "GET", "/plugins/epg/prefetch?channels=a"),
    ("g3-s3", "GET", "/sources"),
    ("g3-s3", "GET", "/diagnostics/health"),
    ("g3-s3", "GET", "/diagnostics/stream-telemetry"),
]


class TvStateStub:
    def handle(self, action: str, query: str) -> dict[str, Any]:
        return {"ok": True, "plugin": "tv_state", "action": action}


class EpgStub:
    def handle(self, action: str, query: str) -> dict[str, Any]:
        return {"ok": True, "plugin": "epg", "action": action, "query": parse_qs(query)}


class CatalogStub:
    def public_catalog(self) -> dict[str, Any]:
        return {"ok": True, "sources": ["fixture"]}


class SnapshotStub:
    def snapshot(self) -> dict[str, Any]:
        return {"ok": True, "fixture": "snapshot"}


class GamesStub:
    def handle(self, action: str, query: str) -> dict[str, Any]:
        return {"ok": True, "plugin": "games", "action": action, "query": parse_qs(query), "active": False}

    def handle_post_request(self, action: str, query: str, client_ip: str) -> dict[str, Any]:
        return {"ok": True, "plugin": "games", "action": action, "active": True,
                "target": LABELS.get(client_ip, "other")}


class ControllerStub:
    catalog = CatalogStub()

    def status(self) -> dict[str, Any]:
        return {"service": "PrivyHub", "api_version": 4, "control_port": 8765}


def handler_class(source: str, session_identity: Any, log: list[str]):
    ns: dict[str, Any] = {
        "__name__": "privyhub_service_fixture",
        "Any": Any, "json": json, "urlsplit": urlsplit, "parse_qs": parse_qs,
        "BaseHTTPRequestHandler": BaseHTTPRequestHandler,
        "PLUGINS": {"games": GamesStub(), "tv_state": TvStateStub(), "epg": EpgStub()},
        "build_live_health_snapshot": lambda **kw: {"ok": True, "fixture": "health"},
        "CLIENT_HEALTH_STORE": SnapshotStub(),
        "STREAM_TELEMETRY_STORE": SnapshotStub(),
        "WAN_TELEMETRY": None,
        "CONTROLLER": ControllerStub(),
        "PROJECT_ROOT": Path("/fixture/project"),
        "access_log_path": lambda h: urlsplit(getattr(h, "path", "")).path,
        "print": lambda *a, **k: log.append(" ".join(str(x) for x in a)),
        "SESSION_IDENTITY": session_identity,
        "CatalogError": type("CatalogError", (Exception,), {}),
        "SourceStartError": type("SourceStartError", (Exception,), {}),
    }
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PrivyHubRequestHandler")
    exec(compile(ast.get_source_segment(source, node), "<handler>", "exec"), ns)
    base = ns["PrivyHubRequestHandler"]

    class Fixed(base):  # deterministic Date / Server headers
        def version_string(self) -> str:
            return "PrivyHubControl/0.6 Python/fixture"

        def date_time_string(self, timestamp=None) -> str:
            return "Thu, 01 Jan 2026 00:00:00 GMT"

    return Fixed


def current_source() -> str:
    return (ROOT / "companion" / "privyhub_service.py").read_text()


def run(cls, method: str, target: str, source: str, headers: dict[str, str] | None = None) -> bytes:
    lines = [f"{method} {target} HTTP/1.0"]
    for k, v in (headers or {}).items():
        lines.append(f"{k}: {v}")
    if method == "POST":
        lines.append("Content-Length: 0")
    raw = ("\r\n".join(lines) + "\r\n\r\n").encode()
    h = cls.__new__(cls)
    h.rfile = io.BytesIO(raw)
    h.wfile = io.BytesIO()
    h.client_address = (source, 50123)
    h.server = SimpleNamespace()
    h.request = None
    h.close_connection = True
    h.handle_one_request()
    return h.wfile.getvalue()


def without_session_header(raw: bytes) -> bytes:
    head, _, body = raw.partition(b"\r\n\r\n")
    kept = [ln for ln in head.split(b"\r\n") if not ln.lower().startswith(si.SESSION_HEADER.lower().encode() + b":")]
    return b"\r\n".join(kept) + b"\r\n\r\n" + body


def short(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:12]


class HandlerReplay(unittest.TestCase):
    table: list[str] = []

    @classmethod
    def setUpClass(cls):
        cls.table = ["| source | request | baseline | flag absent | v2, legacy LAN |", "| --- | --- | --- | --- | --- |"]

    @classmethod
    def tearDownClass(cls):
        out = os.environ.get("G3_S1_REPLAY_OUT")
        if out:
            Path(out).write_text("\n".join(cls.table) + "\n")

    def test_flag_absent_and_legacy(self):
        before_log: list[str] = []
        absent_log: list[str] = []
        before = handler_class((FIX / "handler_predecessor.py.txt").read_text(), None, before_log)
        absent = handler_class(current_source(), None, absent_log)
        gate = make_gate()
        v2 = handler_class(current_source(), gate, [])
        for origin, method, target in REQUESTS:
            for src in (LAN_SRC, LOCAL_SRC):
                a = run(before, method, target, src)
                b = run(absent, method, target, src)
                c = run(v2, method, target, src)
                self.assertEqual(a, b, f"flag absent differs: {method} {target}")
                path = urlsplit(target).path
                if src == LAN_SRC and path in si.SETUP_PATHS:
                    self.assertIn(si.SESSION_HEADER.encode(), c)
                    self.assertEqual(without_session_header(c), a, f"v2 legacy differs beyond the header: {target}")
                    v2_cell = f"same + `{si.SESSION_HEADER}` header"
                else:
                    self.assertEqual(c, a, f"v2 legacy differs: {method} {target}")
                    v2_cell = "identical"
                self.table.append(f"| {LABELS[src]} ({origin}) | `{method} {target}` | {short(a)} | identical ({short(b)}) | {v2_cell} |")
        self.assertEqual(before_log, absent_log, "the access-log lines differ")
        self.assertTrue(before_log)

    def test_v2_refusals_and_declared_target(self):
        gate = make_gate()
        v2 = handler_class(current_source(), gate, [])
        raw = run(v2, "GET", "/plugins/games/status", OVERLAY_SRC)
        self.assertTrue(raw.startswith(b"HTTP/1.0 401"))
        self.assertIn(b'"reason": "legacy-overlay"', raw)

        dev = pair(gate)
        (st, p), _ = setup(gate, dev)
        self.assertEqual(st, 200)
        raw = run(v2, "POST", "/plugins/games/native-stream-start?port=50000", LAN_SRC,
                  {si.SESSION_HEADER: p["token"]})
        self.assertTrue(raw.startswith(b"HTTP/1.0 200"))
        self.assertIn(b'"target": "declared"', raw)
        raw = run(v2, "POST", "/plugins/games/native-stream-start?port=50000", LAN_SRC)
        self.assertIn(b'"target": "source"', raw)   # legacy: as today
        # G3-S3: `diagnostics` is on for a paired device: /status answers.
        raw = run(v2, "GET", "/status", LAN_SRC, {si.SESSION_HEADER: p["token"]})
        self.assertTrue(raw.startswith(b"HTTP/1.0 200"))

    def test_g3_s3_tv_epg_diagnostics_over_the_overlay(self):
        from test_g3s3 import setup_v2
        from common import OVERLAY_DECLARED
        gate = make_gate()
        v2 = handler_class(current_source(), gate, [])
        paths = [t for o, m, t in REQUESTS if o == "g3-s3"]
        for target in paths:
            raw = run(v2, "GET", target, OVERLAY_SRC)
            self.assertTrue(raw.startswith(b"HTTP/1.0 401"), target)
            self.assertIn(b'"reason": "legacy-overlay"', raw)
        dev = pair(gate)
        st, p = setup_v2(gate, dev, source=OVERLAY_SRC, media_host=OVERLAY_DECLARED)
        self.assertEqual(st, 200)
        absent = handler_class(current_source(), None, [])
        for target in paths:
            raw = run(v2, "GET", target, OVERLAY_SRC, {si.SESSION_HEADER: p["token"]})
            self.assertTrue(raw.startswith(b"HTTP/1.0 200"), target)
            self.assertEqual(raw, run(absent, "GET", target, OVERLAY_SRC), target)   # the same answer as today's LAN
        raw = run(v2, "POST", "/plugins/games/native-stream-start?port=48101", OVERLAY_SRC,
                  {si.SESSION_HEADER: p["token"]})
        self.assertTrue(raw.startswith(b"HTTP/1.0 403"))
        self.assertIn(b'"reason": "endpoint-port-mismatch"', raw)
        raw = run(v2, "POST", "/plugins/games/native-stream-start?port=48100", OVERLAY_SRC,
                  {si.SESSION_HEADER: p["token"]})
        self.assertIn(b'"target": "other"', raw)    # the declared overlay host (not a LAN label)

    def test_session_routes_over_http(self):
        gate = make_gate()
        v2 = handler_class(current_source(), gate, [])
        raw = run(v2, "POST", "/session/nonce", LAN_SRC)
        self.assertTrue(raw.startswith(b"HTTP/1.0 200"))
        self.assertIn(b'"nonce"', raw)
        raw = run(v2, "GET", "/session/status", LOCAL_SRC)
        self.assertIn(b'"paired_devices": 0', raw)
        raw = run(v2, "GET", "/session/status", LAN_SRC)
        self.assertTrue(raw.startswith(b"HTTP/1.0 403"))


if __name__ == "__main__":
    unittest.main()
