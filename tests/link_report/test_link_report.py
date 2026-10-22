#!/usr/bin/env python3
"""B3: the host side of the client's Wi-Fi link report (PRIVYHUB_LINK_REPORT=1).

    python3 -m unittest discover -s tests/link_report -v

client_feedback's parser, the ladder telemetry's link.*, the heartbeat log's fields; flag absent = the parsers as
today. No stream, no companion. The flagged modules are re-imported in a fresh process with the flag set.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
FLAG = "PRIVYHUB_LINK_REPORT"

PAYLOAD = {
    "schema": "privyhub_client_health_v1", "sequence": 7, "interval_ms": 2000, "session_elapsed_ms": 60_000,
    "video": {"packets": 1000, "lost_packets": 3, "dropped_frames": 0, "fec_recovered_packets": 1,
              "fec_unrecoverable_groups": 0, "late_or_reordered_packets": 0, "forward_gap_events": 0,
              "recent_fps": 59.9, "recent_mbps": 7.1, "waiting_for_idr": False},
    "decoder": {"queued_frames": 120, "rendered_frames": 119, "dropped_frames": 0, "queue_overflow_drops": 0,
                "stale_output_drops": 0, "queue_depth": 0, "latest_rx_to_decode_ms": 9, "latest_output_gap_ms": 16,
                "hardware_accelerated": True, "vendor_codec": True, "low_latency_enabled": True},
}
LINK = {"rssi_dbm": -58, "tx_mbps": 866, "rx_mbps": 780, "frequency_mhz": 5180, "wifi_standard": 5}


def run(code: str, flag: bool) -> str:
    env = {k: v for k, v in os.environ.items() if k != FLAG}
    if flag:
        env[FLAG] = "1"
    out = subprocess.run([sys.executable, "-B", "-c", "import sys, json; sys.path.insert(0, 'companion'); " + code],
                         cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    if out.returncode:
        raise AssertionError(out.stderr[-1500:])
    return out.stdout.strip()


class ClientFeedback(unittest.TestCase):
    def norm(self, payload, flag):
        code = ("from diagnostics.client_feedback import normalize_client_health as n; "
                f"print(json.dumps(n(json.loads({json.dumps(json.dumps(payload))})), sort_keys=True))")
        return json.loads(run(code, flag))

    def test_absent_link_ignored_as_today(self):
        a = self.norm(PAYLOAD, False)
        b = self.norm(dict(PAYLOAD, link=LINK), False)
        self.assertEqual(a, b)
        self.assertNotIn("link", b)

    def test_on_link_normalized(self):
        b = self.norm(dict(PAYLOAD, link=LINK), True)
        self.assertEqual(b["link"], LINK)
        a = self.norm(PAYLOAD, True)
        self.assertNotIn("link", a)                     # an old client: nothing new

    def test_on_bad_link_never_rejects_the_report(self):
        bad = {"rssi_dbm": -127, "tx_mbps": "fast", "rx_mbps": True, "frequency_mhz": 5180.0, "ssid": "x",
               "wifi_standard": 99}
        b = self.norm(dict(PAYLOAD, link=bad), True)
        self.assertEqual(b["link"], {"frequency_mhz": 5180})
        self.assertEqual(b["sequence"], 7)
        c = self.norm(dict(PAYLOAD, link=[1, 2]), True)
        self.assertNotIn("link", c)


class Telemetry(unittest.TestCase):
    def tel(self, link, flag):
        report = dict(PAYLOAD, **({"link": link} if link is not None else {}))
        code = ("from diagnostics.stream_telemetry import StreamTelemetryStore as S; "
                f"r = json.loads({json.dumps(json.dumps(report))}); "
                "t = S().accept(client_health_feedback={'available': True, 'fresh': True, 'report': r, "
                "'delta_available': False, 'delta': {}}, native_stream_status={}); "
                "print(json.dumps(t.get('link'), sort_keys=True))")
        return json.loads(run(code, flag))

    def test_on_link_star(self):
        self.assertEqual(self.tel(LINK, True), {"rssi": -58, "tx_mbps": 866, "rx_mbps": 780, "frequency_mhz": 5180,
                                                "band": "5", "wifi_standard": 5})
        self.assertEqual(self.tel({"frequency_mhz": 2437}, True)["band"], "2.4")
        self.assertEqual(self.tel({"frequency_mhz": 5955}, True)["band"], "6")

    def test_absent_no_link(self):
        self.assertIsNone(self.tel(LINK, False))
        self.assertIsNone(self.tel(None, True))

    def test_the_ladder_reads_nothing_new(self):
        src = (ROOT / "companion" / "adaptive_bitrate.py").read_text()
        fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "_sample")
        self.assertNotIn("link", ast.unparse(fn))


class HeartbeatLog(unittest.TestCase):
    def rec(self, flag):
        code = ("import tempfile, pathlib; from games.native_stream_heartbeat import append_native_stream_heartbeat "
                "as a, LINK_FIELDS; root = pathlib.Path(tempfile.mkdtemp(prefix='b3_hb_')); "
                "a(root, {'sequence': 1, 'link_rssi_dbm': -60, 'link_tx_mbps': 400}); "
                "p = next(root.rglob('native_stream_heartbeat.log')); "
                "print(json.dumps([LINK_FIELDS, json.loads(p.read_text().splitlines()[-1])]))")
        return json.loads(run(code, flag))

    def test_absent_not_recorded(self):
        fields, row = self.rec(False)
        self.assertIsNone(fields)
        self.assertNotIn("link_rssi_dbm", row)

    def test_on_recorded(self):
        fields, row = self.rec(True)
        self.assertEqual(len(fields), 5)
        self.assertEqual((row["link_rssi_dbm"], row["link_tx_mbps"]), (-60, 400))


class Shapes(unittest.TestCase):
    def test_guards(self):
        g = ast.parse((ROOT / "companion" / "plugins" / "games.py").read_text())
        guarded = [n for n in g.body if isinstance(n, ast.If) and "LINK_FIELDS" in ast.unparse(n)]
        self.assertEqual(len(guarded), 1)
        self.assertIn(FLAG, ast.unparse(guarded[0].test))
        hooks = [n for n in ast.walk(g) if isinstance(n, ast.If) and ast.unparse(n.test) == "_LINK_FIELDS is not None"]
        self.assertEqual(len(hooks), 1)
        for rel, test in (("diagnostics/client_feedback.py", "_LINK_REPORT and isinstance(root.get('link'), dict)"),
                          ("diagnostics/stream_telemetry.py", "_LINK_REPORT and isinstance(report.get('link'), dict)"),
                          ("games/native_stream_heartbeat.py", "LINK_FIELDS is not None")):
            t = ast.parse((ROOT / "companion" / rel).read_text())
            self.assertEqual(sum(1 for n in ast.walk(t) if isinstance(n, ast.If) and ast.unparse(n.test) == test), 1,
                             rel)


if __name__ == "__main__":
    unittest.main()
