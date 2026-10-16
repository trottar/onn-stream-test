#!/usr/bin/env python3
"""G5-S1: WAN telemetry classification.

    python3 -m unittest discover -s tests/wan_telemetry -v

- Measures and classes with hand fixtures (each class triggered by its
  record §1 rule).
- Replays of three recorded runs (`fixtures/*.json`, made by
  `docs/memory/evidence/g5_s1_2026-10-16/make_fixtures.py`: counters only).
- The live object fed like the companion feeds it.
- The flag absent, byte for byte: tonight's `status()` and request handler
  (kept as goldens before G5-S1's edit) against the edited ones, in process.

With `G5_S1_REPLAY_OUT=<dir>`, each replay's per-window output is written
there.
"""

from __future__ import annotations

import ast
import io
import json
import os
import sys
import tempfile
import textwrap
import threading
import unittest
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
FIX = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT / "companion"))

import wan_telemetry as w  # noqa: E402


def row(t_ms, fps=59.9, queue=0, gap=16, lost=0, stale=0, mbps=6.9, jitter=0.8, rtt=40, fresh=True, fec=None):
    r = {"fresh": fresh, "elapsed_ms": t_ms,
         "receiver": {"recent_fps": fps, "lost_packets_delta": lost, "recent_mbps": mbps,
                      "interarrival_jitter_ms": jitter, "packets_delta": 1600, "waiting_for_idr": False},
         "decoder": {"queue_depth": queue, "stale_output_drops_delta": stale, "queue_depth_delta": 0},
         "latency": {"output_gap_ms": gap, "control_round_trip_ms": rtt}}
    if fec is not None:
        r["fec"] = {"recovered_packets_delta": fec[0], "unrecoverable_groups_delta": fec[1]}
    return r


def window(**kw):
    reps = [w.report_from_telemetry(row(2000 * (i + 1), **{k: (v[i] if isinstance(v, list) else v) for k, v in kw.items()}))
            for i in range(5)]
    return reps


class Classes(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(w.classify_window(window(), [])["classes"], ["clean"])

    def test_lossy_is_the_dbase_row_scaled(self):
        # 10/min over 10 s = 1.67 packets: 1 lost is under, 2 lost is over.
        self.assertEqual(w.classify_window(window(lost=[1, 0, 0, 0, 0]), [])["primary"], "clean")
        self.assertEqual(w.classify_window(window(lost=[1, 1, 0, 0, 0]), [])["primary"], "lossy")

    def test_starved_is_the_stale_row_scaled(self):
        self.assertEqual(w.classify_window(window(stale=[1, 1, 1, 0, 0]), [])["primary"], "clean")
        self.assertEqual(w.classify_window(window(stale=[1, 1, 1, 1, 0]), [])["primary"], "starved")

    def test_capacity_n1_and_n2(self):
        n1 = window(fps=49.0, lost=[60, 60, 60, 0, 0])
        self.assertIn("capacity-limited", w.classify_window(n1, [])["classes"])
        n2 = window(fps=[56, 56, 56, 56, 59], lost=[50, 50, 50, 0, 0])
        self.assertIn("capacity-limited", w.classify_window(n2, [])["classes"])
        not_yet = window(fps=[56, 56, 56, 59, 59], lost=[50, 50, 50, 0, 0])
        self.assertNotIn("capacity-limited", w.classify_window(not_yet, [])["classes"])

    def test_latency_queue_or_gap(self):
        self.assertEqual(w.classify_window(window(queue=[1, 1, 1, 0, 0]), [])["primary"], "latency-limited")
        self.assertEqual(w.classify_window(window(gap=[300, 260, 16, 16, 16]), [])["primary"], "latency-limited")
        self.assertEqual(w.classify_window(window(gap=[300, 250, 16, 16, 16]), [])["primary"], "clean")

    def test_path_changed_wins_priority(self):
        c = w.classify_window(window(lost=60, queue=2), [w.Event(4.0, "overlay_path", "direct->relayed")])
        self.assertEqual(c["primary"], "path-changed")
        self.assertEqual(c["classes"][:2], ["path-changed", "latency-limited"])


class Measures(unittest.TestCase):
    def test_eleven_measures_each_with_a_source(self):
        reps = window(lost=[2, 0, 0, 0, 0], fec=(3, 1))
        m = w.measures(reps, [w.Event(1.0, "recovery_pause")], {"path": "direct", "mtu": 1280})
        self.assertEqual(len(m), 11)
        for name, v in m.items():
            self.assertIn("source", v, name)
        self.assertEqual(m["packet_loss_per_min"]["value"], {"post_fec": 12.0, "pre_fec": 102.0})  # (2 + 3 x 5) in 10 s
        self.assertEqual(m["fec_groups"]["value"], {"recovered_packets": 3 * 5, "unrecoverable_groups": 5})
        self.assertEqual(m["overlay_path"]["value"], "direct")
        self.assertEqual(m["mtu_fragmentation"]["value"]["mtu"], 1280)
        self.assertEqual(m["rtt_ms"]["value"]["p50"], 40)
        self.assertEqual(m["delivered_goodput_kbps"]["value"], 6900.0)
        self.assertEqual(m["path_change_events"]["value"]["count"], 1)
        self.assertEqual(m["sender_pacing"]["value"], "not recorded")

    def test_not_fresh_is_skipped_and_repeats_deduped(self):
        sc = w.SessionClassifier()
        self.assertIsNone(w.report_from_telemetry(row(2000, fresh=False)))
        self.assertTrue(sc.add_report(w.report_from_telemetry(row(2000))))
        self.assertFalse(sc.add_report(w.report_from_telemetry(row(2000))))


class Replays(unittest.TestCase):
    """Three recorded runs; the classes those nights earned."""

    def replay(self, name):
        fx = json.loads((FIX / f"{name}.json").read_text())
        sc = w.classifier_from_fixture(fx)
        s = sc.session(heartbeat=fx.get("heartbeat"))
        out = os.environ.get("G5_S1_REPLAY_OUT")
        if out:
            Path(out).mkdir(parents=True, exist_ok=True)
            (Path(out) / f"replay_{name}.json").write_text(
                json.dumps({"session": s, "windows": sc.windows()}, indent=1) + "\n")
        return fx, s

    def test_run3_lossy_652(self):
        fx, s = self.replay("e4_s4b_run3_lossy")
        self.assertAlmostEqual(s["loss_per_min_post_fec"], fx["recorded_loss_per_min"], places=2)
        self.assertNotEqual(s["class"], "clean")
        self.assertIn("lossy", s["classes"])
        self.assertIn("capacity-limited", s["classes"])
        self.assertIn("path-changed", s["classes"])      # the ladder acted 4 times
        self.assertEqual(s["measures"]["path_change_events"]["value"]["count"], 4)
        self.assertEqual(s["measures"]["fec_groups"]["value"]["recovered_packets"], "not recorded")

    def test_run2_cleanest_still_lossy(self):
        fx, s = self.replay("e4_s4b_run2_cleanest")
        self.assertAlmostEqual(s["loss_per_min_post_fec"], fx["recorded_loss_per_min"], places=2)
        self.assertEqual(s["classes"], ["lossy"])         # 60.93/min fails the < 10 row; nothing else met
        self.assertGreater(s["window_counts"]["clean"], 0)

    def test_cl_b2_flag_run1(self):
        fx, s = self.replay("cl_b2_flag_run1")
        self.assertAlmostEqual(s["loss_per_min_post_fec"], fx["recorded_loss_per_min"], places=2)
        self.assertIn("lossy", s["classes"])
        self.assertIn("path-changed", s["classes"])      # the recovery pause at ~942 s
        kinds = [e["kind"] for e in s["measures"]["path_change_events"]["value"]["events"]]
        self.assertEqual(kinds, ["recovery_pause", "recovery_resume"])
        fec = s["measures"]["fec_groups"]["value"]
        self.assertEqual(fec, {"recovered_packets": fx["heartbeat"]["fec_recovered_packets"],
                               "unrecoverable_groups": fx["heartbeat"]["fec_unrecoverable_groups"]})
        pre = s["measures"]["packet_loss_per_min"]["value"]["pre_fec"]
        self.assertGreater(pre, s["loss_per_min_post_fec"])


class Live(unittest.TestCase):
    def test_flag(self):
        self.assertIsNone(w.from_environ({}, ROOT))
        self.assertIsNone(w.from_environ({w.FLAG_ENV: "0"}, ROOT))
        self.assertIsNotNone(w.from_environ({w.FLAG_ENV: "1"}, Path(tempfile.mkdtemp())))

    def test_observe_events_freshness_and_session_close(self):
        root = Path(tempfile.mkdtemp())
        now = [100.0]
        path = ["direct"]
        wt = w.WanTelemetry(root, overlay_state=lambda: {"path": path[0], "mtu": 1280}, clock=lambda: now[0])
        self.assertIsNone(wt.status_field())
        for i in range(10):
            wt.observe(row(2000 * (i + 1), lost=3), {"bitrate_kbps": 7000 if i < 6 else 6000})
            now[0] += 2.0
        path[0] = "relayed"
        wt.observe(row(22000), {"bitrate_kbps": 6000})
        doc = wt.status_field()
        self.assertEqual(doc["windows"], 2)
        kinds = [e["kind"] for e in doc["measures"]["path_change_events"]["value"]["events"]]
        self.assertEqual(kinds, ["ladder_transition", "overlay_path"])
        self.assertEqual(doc["class"], "path-changed")
        now[0] += 60.0
        self.assertIsNone(wt.status_field())               # no report within one window
        wt.observe(row(2000), {"bitrate_kbps": 7000})        # elapsed went back: a new session
        lines = (root / "logs" / "wan_sessions.jsonl").read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["schema"], w.SCHEMA)


# ---- the flag absent, byte for byte (in process) -----------------------------------

def _status_fn(source: str, wan: Any):
    ns = {"Any": Any, "PROJECT_ROOT": Path("/fixture/project"), "MEDIA_ROOT": Path("/fixture/project/media"),
          "CONTROL_PORT": 8765, "OVERLAY_STATUS": None, "WAN_TELEMETRY": wan}
    exec(compile(textwrap.dedent(source), "<status>", "exec"), ns)
    return ns["status"]


def _controller():
    return SimpleNamespace(lock=threading.Lock(), server=None, source_process=None, active_source_id=None,
                           catalog=SimpleNamespace(vod_storage_status=lambda: {"configured": True}),
                           _running=lambda p: False, _close_log=lambda p: None)


def _current(cls_or_fn: str) -> str:
    src = (ROOT / "companion" / "privyhub_service.py").read_text()
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == cls_or_fn:
            return ast.get_source_segment(src, node)
        if isinstance(node, ast.ClassDef) and node.name == "PrivyHubController" and cls_or_fn == "status":
            for f in node.body:
                if isinstance(f, ast.FunctionDef) and f.name == "status":
                    return ast.get_source_segment(src, f, padded=True)
    raise AssertionError(cls_or_fn)


class FakeWan:
    def __init__(self):
        self.observed = 0

    def status_field(self):
        return {"schema": w.SCHEMA, "class": "clean"}

    def observe(self, telemetry, native_status):
        self.observed += 1


class Games:
    def handle(self, action, query):
        return {"ok": True, "action": action, "active": True, "bitrate_kbps": 7000}


def _handler(source: str, wan: Any, log: list):
    snapshot = {"schema": "privyhub_stream_telemetry_v1", "fresh": True, "receiver": {"lost_packets_delta": 0}}
    abr = SimpleNamespace(observe=lambda *a, **k: None)
    ns = {
        "Any": Any, "json": json, "urlsplit": urlsplit, "parse_qs": parse_qs,
        "BaseHTTPRequestHandler": BaseHTTPRequestHandler,
        "PLUGINS": {"games": Games()}, "CONTROLLER": SimpleNamespace(status=lambda: {"service": "PrivyHub"}),
        "PROJECT_ROOT": Path("/fixture/project"),
        "access_log_path": lambda h: urlsplit(getattr(h, "path", "")).path,
        "print": lambda *a, **k: log.append(" ".join(map(str, a))),
        "SESSION_IDENTITY": None, "WAN_TELEMETRY": wan,
        "STREAM_TELEMETRY_STORE": SimpleNamespace(snapshot=lambda: dict(snapshot), accept=lambda **k: dict(snapshot)),
        "CLIENT_HEALTH_STORE": SimpleNamespace(accept=lambda p, payload_bytes: {"ok": True, "accepted": True},
                                               snapshot=lambda: {"available": True}),
        "adaptive_bitrate_controller": lambda root: abr, "adaptive_bitrate_is_live": lambda c: False,
        "CatalogError": type("CatalogError", (Exception,), {}),
        "SourceStartError": type("SourceStartError", (Exception,), {}),
    }
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "PrivyHubRequestHandler")
    exec(compile(ast.get_source_segment(source, node), "<handler>", "exec"), ns)

    class Fixed(ns["PrivyHubRequestHandler"]):
        def version_string(self):
            return "PrivyHubControl/0.6 Python/fixture"

        def date_time_string(self, timestamp=None):
            return "Thu, 01 Jan 2026 00:00:00 GMT"
    return Fixed


def _run(cls, method, target, body=b""):
    head = f"{method} {target} HTTP/1.0\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n"
    h = cls.__new__(cls)
    h.rfile, h.wfile = io.BytesIO(head.encode() + body), io.BytesIO()
    h.client_address, h.server, h.request, h.close_connection = ("fixture-client", 1), SimpleNamespace(), None, True
    h.handle_one_request()
    return h.wfile.getvalue()


REQUESTS = [
    ("GET", "/status", b""),
    ("GET", "/diagnostics/stream-telemetry", b""),
    ("POST", "/diagnostics/client-health", b'{"schema": "fixture", "report": {}}'),
    ("GET", "/plugins/games/native-stream-status", b""),
    ("GET", "/plugins/games/status", b""),
]


class FlagAbsentByteForByte(unittest.TestCase):
    def test_status_document(self):
        a = json.dumps(_status_fn((FIX / "status_method_predecessor.py.txt").read_text(), None)(_controller()), indent=2)
        b = json.dumps(_status_fn(_current("status"), None)(_controller()), indent=2)
        self.assertEqual(a, b)

    def test_status_with_flag_adds_only_wan(self):
        # The /status hook is a guarded module-level wrapper around CONTROLLER.status.
        src = (ROOT / "companion" / "privyhub_service.py").read_text()
        block = next(n for n in ast.parse(src).body if isinstance(n, ast.If)
                     and ast.get_source_segment(src, n.test) == "WAN_TELEMETRY is not None")
        code = compile(ast.Module(body=[block], type_ignores=[]), "<wan-status>", "exec")
        for wan, expect in ((None, set()), (FakeWan(), {"wan"})):
            base = {"service": "PrivyHub", "api_version": 4}
            ns = {"Any": Any, "WAN_TELEMETRY": wan, "CONTROLLER": SimpleNamespace(status=lambda: dict(base))}
            exec(code, ns)
            self.assertEqual(set(ns["CONTROLLER"].status()) - set(base), expect)

    def test_handler_requests(self):
        la, lb = [], []
        before = _handler((FIX / "handler_predecessor.py.txt").read_text(), None, la)
        after = _handler(_current("PrivyHubRequestHandler"), None, lb)
        table = []
        for method, target, body in REQUESTS:
            a, b = _run(before, method, target, body), _run(after, method, target, body)
            self.assertEqual(a, b, f"{method} {target}")
            table.append(f"| `{method} {target}` | identical ({len(a)} bytes) |")
        self.assertEqual(la, lb)
        out = os.environ.get("G5_S1_REPLAY_OUT")
        if out:
            Path(out).mkdir(parents=True, exist_ok=True)
            (Path(out) / "handler_byte_comparison.md").write_text(
                "| request | flag absent vs tonight's predecessor |\n| --- | --- |\n" + "\n".join(table) + "\n")

    def test_handler_with_flag(self):
        fake = FakeWan()
        cls = _handler(_current("PrivyHubRequestHandler"), fake, [])
        raw = _run(cls, "GET", "/diagnostics/stream-telemetry")
        self.assertIn(b'"wan"', raw)
        _run(cls, "POST", "/diagnostics/client-health", b'{"schema": "fixture"}')
        self.assertEqual(fake.observed, 1)

    def test_imported_only_under_the_flag(self):
        src = (ROOT / "companion" / "privyhub_service.py").read_text()
        tree = ast.parse(src)
        self.assertFalse([n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
                          and (getattr(n, "module", "") or "").startswith("wan_telemetry")])
        guarded = [n for n in tree.body if isinstance(n, ast.If)
                   and "PRIVYHUB_WAN_TELEMETRY" in ast.get_source_segment(src, n.test)]
        self.assertEqual(len(guarded), 1)


if __name__ == "__main__":
    unittest.main()
