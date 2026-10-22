#!/usr/bin/env python3
"""B10 (host): the client's keyframe request, through the real controller receive loop; a fake encoder control.

    python3 -m unittest discover -s tests/keyframe_request -v
"""

from __future__ import annotations

import ast
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import keyframe_request as kr  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402
from games import native_stream_heartbeat as nsh  # noqa: E402

LOOP = "127.0.0.1"


def recovery():
    rec = ldr.LinkDropRecovery(
        Path(tempfile.mkdtemp(prefix="b10_rec_")), pause_game=lambda: None, resume_game=lambda: None,
        save_recovery_state=lambda: {}, restart_encoder=lambda: {}, full_start_encoder=lambda: {},
        stream_active=lambda: True, end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
        recovery_save_detail=lambda: {})
    return rec


def rows(rec):
    p = rec.log_path()
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


class FakeControl:
    def __init__(self):
        self.calls = 0

    def force_idr(self):
        self.calls += 1
        return {"forced": True, "via": "fake_encoder"}


def request(seq, delivered=1000, drops=1):
    return kr.PACKET.pack(kr.MAGIC, kr.KIND_REQUEST, 0, 0, seq, delivered, drops)


def through_the_loop(requests_obj, datagrams, spacing=0.0):
    """The real NativeControllerBridge receive loop; returns its bad-packet count."""
    import native_session_io as nsio
    br = nsio.NativeControllerBridge(Path(tempfile.mkdtemp(prefix="b10_bridge_")))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LOOP, 0))
    sock.settimeout(0.05)
    br._socket, br._client_ip = sock, LOOP
    br._neutralize = lambda player=None: None
    if requests_obj is not None:
        br.set_keyframe_request(requests_obj)
    br._running.set()
    th = threading.Thread(target=br._receive_loop, daemon=True)
    th.start()
    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for d in datagrams:
        tx.sendto(d, (LOOP, sock.getsockname()[1]))
        if spacing:
            time.sleep(spacing)
    time.sleep(0.3)
    br._running.clear()
    th.join(timeout=2)
    tx.close()
    return br._bad_packets


class TheFlagAndThePacket(unittest.TestCase):
    def test_parse_and_decode(self):
        self.assertEqual(kr.parse(None), (False, None))
        self.assertEqual(kr.parse("1"), (True, None))
        self.assertFalse(kr.parse("yes")[0])
        self.assertEqual(kr.decode(request(5, 77, 2)), (5, 77, 2))
        self.assertIsNone(kr.decode(request(5)[:23]))
        self.assertIsNone(kr.decode(b"PHS1" + request(5)[4:]))               # B7's stall is not a request
        self.assertEqual(kr.PACKET.size, 24)


class TheRequestPath(unittest.TestCase):
    def test_one_request_one_forced_idr(self):
        rec, ctl = recovery(), FakeControl()
        k = kr.KeyframeRequests(rec, ctl, threaded=False)
        k.handle((1, 1000, 1), time.monotonic())
        self.assertEqual(ctl.calls, 1)
        r = [x for x in rows(rec) if x["event"] == "keyframe_forced"]
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["client_seq"], r[0]["via"]), (1, "fake_encoder"))

    def test_the_rate_limit_one_per_500_ms(self):
        rec, ctl = recovery(), FakeControl()
        k = kr.KeyframeRequests(rec, ctl, threaded=False)
        t0 = 1000.0
        for i in range(10):
            k.handle((i, 1000 + i, 1), t0 + i * 0.04)                          # 10 in 360 ms
        self.assertEqual(ctl.calls, 1)
        self.assertEqual(k.counts(), (10, 1, 9, 1, 0))
        k.handle((10, 2000, 1), t0 + 0.55)                                     # 550 ms after the acted one
        self.assertEqual(ctl.calls, 2)

    def test_today_no_runtime_idr_forces_nothing_and_says_why(self):
        rec = recovery()
        k = kr.KeyframeRequests(rec, threaded=False)
        t = [0.0]
        k._clock = lambda: t[0]
        k._last_summary = 0.0
        k.handle((1, 10, 1), 1.0)
        k.handle((2, 20, 1), 1.1)
        t[0] = 61.0
        k.maybe_summary(61.0)
        self.assertEqual([x["event"] for x in rows(rec)], ["keyframe_requests"])
        s = rows(rec)[0]
        self.assertEqual((s["received"], s["acted"], s["rate_limited"], s["forced"], s["unforced"]), (2, 1, 1, 0, 1))
        self.assertIn("no runtime IDR path", s["reason"])
        k.maybe_summary(125.0)                                                 # nothing new: no row
        self.assertEqual(len(rows(rec)), 1)

    def test_through_the_receive_loop(self):
        rec, ctl = recovery(), FakeControl()
        k = kr.KeyframeRequests(rec, ctl, threaded=True)
        bad = through_the_loop(k, [request(1), request(2), b"PHK1" + b"\x00" * 30], spacing=0.01)
        self.assertEqual(k.received, 2)
        self.assertEqual(ctl.calls, 1)
        self.assertEqual(bad, 1)                                               # a 34-byte datagram: bad, as today

    def test_absent_a_request_is_a_bad_packet_as_today(self):
        bad = through_the_loop(None, [request(1), request(2)])
        self.assertEqual(bad, 2)

    def test_wire(self):
        rec = recovery()

        class Ctrl:
            k = None

            def set_keyframe_request(self, k):
                self.k = k
        c = Ctrl()
        self.assertIsNone(kr.wire(rec, c, {}))
        self.assertIsNone(kr.wire(rec, c, {"PRIVYHUB_LOSS_GUARD": "on"}))
        self.assertIsNotNone(kr.wire(rec, c, {"PRIVYHUB_LOSS_GUARD": "1"}))
        self.assertIsInstance(c.k.control, kr.NoRuntimeIdr)
        cfg = [x for x in rows(rec) if x["event"] == "loss_guard_config"]
        self.assertEqual([x["ignored"] for x in cfg], [True, False])
        self.assertEqual(cfg[1]["control"], "NoRuntimeIdr")


class TheHeartbeat(unittest.TestCase):
    def test_fields_only_with_the_flag(self):
        root = Path(tempfile.mkdtemp(prefix="b10_hb_"))
        values = {"sequence": 1, "frames_after_dropped_reference": 42, "loss_guard_episodes": 6,
                  "loss_guard_frames_held": 40}
        saved = nsh.LOSS_GUARD_FIELDS
        try:
            nsh.LOSS_GUARD_FIELDS = None
            nsh.append_native_stream_heartbeat(root, values)
            nsh.LOSS_GUARD_FIELDS = ("frames_after_dropped_reference", "loss_guard_episodes", "loss_guard_frames_held")
            nsh.append_native_stream_heartbeat(root, values)
        finally:
            nsh.LOSS_GUARD_FIELDS = saved
        lines = [json.loads(x) for x in nsh.heartbeat_log_path(root).read_text().splitlines()]
        self.assertNotIn("frames_after_dropped_reference", lines[0])
        self.assertEqual(lines[1]["frames_after_dropped_reference"], 42)
        self.assertEqual(lines[1]["loss_guard_frames_held"], 40)


class FlagAbsent(unittest.TestCase):
    def test_not_imported_and_no_fields(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        code = ("import sys; sys.path.insert(0, 'companion'); import native_session_io as n; "
                "from games import native_stream_heartbeat as h; "
                "print('keyframe_request' in sys.modules, n.NativeControllerBridge._keyframe_request, "
                "h.LOSS_GUARD_FIELDS)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        self.assertEqual(out.stdout.strip(), "False None None", out.stderr[-400:])

    def test_hook_shapes(self):
        def ifs(rel, text):
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test).startswith(text)]
        self.assertEqual(len(ifs("native_session_io.py", "self._keyframe_request is not None")), 1)
        self.assertEqual(len(ifs("plugins/games.py", "_keyframe_request is not None")), 1)
        self.assertEqual(len(ifs("plugins/games.py", "_LOSS_GUARD_FIELDS is not None")), 1)
        self.assertEqual(len(ifs("games/native_stream_heartbeat.py", "LOSS_GUARD_FIELDS is not None")), 1)


if __name__ == "__main__":
    unittest.main()
