#!/usr/bin/env python3
"""G1-S1: the overlay provider boundary.

    python3 -m unittest discover -s tests/overlay -v

Fixtures stand in for `tailscale status --json` (connected-direct,
connected-relayed, connected with no peer, stopped, needs-login) and for a
missing binary; no fixture holds an address (the overlay endpoint is an
opaque placeholder). Nothing here runs tailscale, starts the companion or
touches the host. The status-document test compares today's
`PrivyHubController.status()` (the baseline's method, kept as a golden in
`fixtures/`) with the edited one, byte for byte, with the flag absent.
"""

from __future__ import annotations

import ast
import json
import sys
import textwrap
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIX = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT / "companion"))

import overlay  # noqa: E402
from overlay import (  # noqa: E402
    OVERLAY_PROVIDER_ENV,
    NoneProvider,
    OverlayStatusReporter,
    TailscaleProvider,
    reporter_from_environ,
    select_provider,
)

ENDPOINT = "<overlay-endpoint-fixture>"
ALLOWED_ARGV = {("status", "--json"), ("netcheck", "--format=json")}


class FakeTailscale:
    """`which` + `runner` for a fixture; records every argv it is given."""

    def __init__(self, status_fixture: str | None, status_rc: int = 0, binary: bool = True,
                 status_text: str | None = None) -> None:
        self.binary = binary
        self.status = status_text if status_text is not None else (
            (FIX / status_fixture).read_text() if status_fixture else "")
        self.status_rc = status_rc
        self.calls: list[tuple[str, ...]] = []

    def which(self, name: str) -> str | None:
        return "/fixture/bin/tailscale" if (self.binary and name == "tailscale") else None

    def runner(self, argv: list[str]) -> tuple[int, str]:
        self.calls.append(tuple(argv[1:]))
        if argv[1:] == ["status", "--json"]:
            return self.status_rc, self.status
        if argv[1:] == ["netcheck", "--format=json"]:
            return 0, (FIX / "netcheck.json").read_text()
        return 99, ""


def provider_for(fake: FakeTailscale, clock=lambda: 0.0) -> TailscaleProvider:
    return TailscaleProvider(which=fake.which, runner=fake.runner, mtu_reader=lambda: 1280, clock=clock)


class Selection(unittest.TestCase):
    def test_absent_is_today(self):
        self.assertIsNone(select_provider({}))
        self.assertIsNone(select_provider({OVERLAY_PROVIDER_ENV: ""}))
        self.assertIsNone(select_provider({OVERLAY_PROVIDER_ENV: "   "}))
        self.assertIsNone(reporter_from_environ({}))

    def test_named_providers(self):
        self.assertIsInstance(select_provider({OVERLAY_PROVIDER_ENV: "none"}), NoneProvider)
        self.assertIsInstance(select_provider({OVERLAY_PROVIDER_ENV: "tailscale"}), TailscaleProvider)
        self.assertIsInstance(select_provider({OVERLAY_PROVIDER_ENV: " TailScale "}), TailscaleProvider)

    def test_unknown_name_fails_closed(self):
        p = select_provider({OVERLAY_PROVIDER_ENV: "wireguard"})
        self.assertIsInstance(p, NoneProvider)
        s = p.state()
        self.assertFalse(s.connected)
        self.assertEqual(s.reason, "unknown-provider")


class NoneProviderState(unittest.TestCase):
    def test_always_absent(self):
        pub = NoneProvider().state().public()
        self.assertEqual(pub, {
            "provider": "none", "available": False, "connected": False, "path": "none",
            "peer_ready": None, "mtu": None, "reason": "absent",
            "endpoint": "absent", "endpoint_hash": None,
        })


class TailscaleStates(unittest.TestCase):
    def assert_read_only(self, fake: FakeTailscale) -> None:
        for argv in fake.calls:
            self.assertIn(argv, ALLOWED_ARGV, f"non-read-only tailscale call: {argv}")
        self.assertNotIn(("up",), {a[:1] for a in fake.calls})

    def test_binary_absent(self):
        fake = FakeTailscale(None, binary=False)
        s = provider_for(fake).state()
        self.assertFalse(s.available)
        self.assertFalse(s.connected)
        self.assertEqual(s.reason, "binary-absent")
        self.assertEqual(fake.calls, [], "nothing is run when the binary is absent")

    def test_connected_direct(self):
        fake = FakeTailscale("status_connected_direct.json")
        s = provider_for(fake).state()
        self.assertTrue(s.available and s.connected)
        self.assertEqual((s.path, s.peer_ready, s.mtu, s.reason), ("direct", True, 1280, "running"))
        self.assertEqual(s.endpoint, ENDPOINT)
        self.assertEqual(s.diagnostics["netcheck_udp"], True)
        self.assertEqual(s.diagnostics["peers_online"], 1)
        self.assert_read_only(fake)
        self.assertEqual(fake.calls, [("status", "--json"), ("netcheck", "--format=json")])

    def test_connected_relayed(self):
        fake = FakeTailscale("status_connected_relayed.json")
        s = provider_for(fake).state()
        self.assertEqual((s.connected, s.path, s.peer_ready), (True, "relayed", True))
        self.assert_read_only(fake)

    def test_connected_no_peer(self):
        s = provider_for(FakeTailscale("status_connected_no_peer.json")).state()
        self.assertEqual((s.connected, s.path, s.peer_ready), (True, "no-peer", False))

    def test_stopped(self):
        fake = FakeTailscale("status_stopped.json")
        s = provider_for(fake).state()
        self.assertEqual((s.available, s.connected, s.path, s.reason), (True, False, "none", "stopped"))
        self.assertIsNone(s.endpoint)
        self.assertEqual(fake.calls, [("status", "--json")], "no netcheck unless Running")

    def test_needs_login(self):
        s = provider_for(FakeTailscale("status_needs_login.json")).state()
        self.assertEqual((s.connected, s.reason), (False, "needs-login"))

    def test_daemon_down(self):
        fake = FakeTailscale(None, status_rc=1, status_text="failed to connect to local tailscaled\n")
        s = provider_for(fake).state()
        self.assertEqual((s.available, s.connected, s.reason), (False, False, "error"))
        self.assertEqual(s.diagnostics, {"status_rc": 1, "status_json": False})

    def test_cache(self):
        now = [0.0]
        fake = FakeTailscale("status_connected_direct.json")
        p = provider_for(fake, clock=lambda: now[0])
        p.state(); p.state()
        self.assertEqual(len(fake.calls), 2)
        now[0] = TailscaleProvider.CACHE_S + 0.1
        p.state()
        self.assertEqual(len(fake.calls), 4)


class PublicFormAndLog(unittest.TestCase):
    def test_endpoint_never_exported(self):
        s = provider_for(FakeTailscale("status_connected_direct.json")).state()
        pub = s.public()
        text = json.dumps(pub)
        self.assertNotIn(ENDPOINT, text)
        self.assertEqual(pub["endpoint"], "present")
        self.assertEqual(len(pub["endpoint_hash"]), 8)
        self.assertNotIn("diagnostics", pub)
        self.assertNotIn(ENDPOINT, repr(s))

    def test_one_log_line_per_change(self):
        lines: list[str] = []
        fake = FakeTailscale("status_connected_direct.json")
        now = [0.0]
        rep = OverlayStatusReporter(provider_for(fake, clock=lambda: now[0]), log=lines.append)
        rep.status_field(); rep.status_field()
        self.assertEqual(len(lines), 1)
        fake.status = (FIX / "status_connected_relayed.json").read_text()
        now[0] = 100.0
        rep.status_field(); rep.status_field()
        self.assertEqual(len(lines), 2)
        self.assertIn("path=relayed", lines[1])
        for line in lines:
            self.assertNotIn(ENDPOINT, line)


def _status_function(source: str, overlay_status: Any):
    ns: dict[str, Any] = {
        "Any": Any,
        "PROJECT_ROOT": Path("/fixture/project"),
        "MEDIA_ROOT": Path("/fixture/project/media"),
        "CONTROL_PORT": 8765,
        "OVERLAY_STATUS": overlay_status,
    }
    exec(compile(textwrap.dedent(source), "<status>", "exec"), ns)
    return ns["status"]


def _fake_controller() -> SimpleNamespace:
    return SimpleNamespace(
        lock=threading.Lock(),
        server=None,
        source_process=None,
        active_source_id=None,
        catalog=SimpleNamespace(vod_storage_status=lambda: {"configured": True, "present": True}),
        _running=lambda proc: False,
        _close_log=lambda proc: None,
    )


def _current_status_source() -> str:
    src = (ROOT / "companion" / "privyhub_service.py").read_text()
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == "PrivyHubController":
            for f in node.body:
                if isinstance(f, ast.FunctionDef) and f.name == "status":
                    return ast.get_source_segment(src, f, padded=True)
    raise AssertionError("status() not found")


class StatusDocument(unittest.TestCase):
    """The companion's /status document: today's bytes without the flag."""

    def test_flag_absent_byte_for_byte(self):
        before = _status_function((FIX / "status_method_predecessor.py.txt").read_text(), None)
        after = _status_function(_current_status_source(), None)
        a = json.dumps(before(_fake_controller()), indent=2).encode()
        b = json.dumps(after(_fake_controller()), indent=2).encode()
        self.assertEqual(a, b)

    def test_flag_set_adds_only_overlay(self):
        before = _status_function((FIX / "status_method_predecessor.py.txt").read_text(), None)
        rep = OverlayStatusReporter(NoneProvider(), log=lambda line: None)
        after = _status_function(_current_status_source(), rep)
        a, b = before(_fake_controller()), after(_fake_controller())
        self.assertEqual(set(b) - set(a), {"overlay"})
        b.pop("overlay")
        self.assertEqual(a, b)

    def test_service_imports_overlay_only_under_the_flag(self):
        src = (ROOT / "companion" / "privyhub_service.py").read_text()
        tree = ast.parse(src)
        top_level_imports = [
            n for n in tree.body
            if isinstance(n, (ast.Import, ast.ImportFrom))
            and (getattr(n, "module", "") or "").startswith("overlay")
        ]
        self.assertEqual(top_level_imports, [], "overlay must not be imported unconditionally")
        guarded = [
            n for n in tree.body
            if isinstance(n, ast.If) and "PRIVYHUB_OVERLAY_PROVIDER" in ast.get_source_segment(src, n.test)
        ]
        self.assertEqual(len(guarded), 1)
        self.assertTrue(any(isinstance(s, ast.ImportFrom) and s.module == "overlay" for s in guarded[0].body))


if __name__ == "__main__":
    unittest.main()
