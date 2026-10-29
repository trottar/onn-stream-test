#!/usr/bin/env python3
"""B30: the trip check's six lines from fakes (no adb, no network, no companion).

    python3 -m unittest discover -s tests/trip_check -v
"""

from __future__ import annotations

import io
import ipaddress
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import trip_check as tc  # noqa: E402

ADOPTED = sorted(["PRIVYHUB_A=1", "PRIVYHUB_B=1", "PRIVYHUB_REMOTE=1"])
PIN = "9719ea822ed5f7d13799ff7e02ba814cd0a2abe79b8a2e3d631d0aecb13c0110"
V4 = str(ipaddress.ip_address(0xC6336414))


def preflight(**over):
    d = {"manager": [], "environ": list(ADOPTED), "adb": True, "drop_in_a": True, "drop_in_remote": True,
         "e3_dropin_absent": True, "e4_constraint_absent": True, "game_active": False}
    d.update(over)
    return d


class TheLines(unittest.TestCase):
    def test_adopted(self):
        self.assertEqual(tc.line_adopted(preflight(), ADOPTED), "adopted: 3 lines; host check ok")
        bad = tc.line_adopted(preflight(environ=ADOPTED[:2], drop_in_remote=False), ADOPTED)
        self.assertEqual(bad, "adopted: 3 lines; host check NOT ok (environ missing PRIVYHUB_REMOTE; drop_in_remote)")
        self.assertIn("host check ok", tc.line_adopted(preflight(adb=False), ADOPTED))       # adb is not a host field

    def test_apk(self):
        self.assertEqual(tc.line_apk(PIN, PIN, True), "apk: on the pin 9719ea82…")
        self.assertEqual(tc.line_apk(PIN, "0" * 64, True), "apk: NOT on the pin (the pin 9719ea82…)")
        self.assertEqual(tc.line_apk(PIN, None, False), "apk: pin 9719ea82…, not read (adb off-LAN)")

    def test_overlay(self):
        self.assertEqual(tc.line_overlay({"connected": True, "path": "direct", "endpoint": V4}, 2),
                         "overlay: connected yes, path direct, peers 2")
        self.assertEqual(tc.line_overlay({"connected": False, "path": None}, None), "overlay: connected no, path none, peers ?")

    def test_routing(self):
        tail = [json.dumps({"event": "token_issued", "routing_evidence": "lan", "t": "2026-10-27T21:00:00Z",
                            "client_id": "dev-0123456789abcdef"}),
                "not json",
                json.dumps({"event": "token_issued", "routing_evidence": "overlay", "t": "2026-10-30T20:15:00Z",
                            "client_id": "dev-0123456789abcdef"}),
                json.dumps({"event": "media_check"})]
        line = tc.line_routing(tail)
        self.assertEqual(line, "routing: newest token_issued overlay at 2026-10-30T20:15:00Z")
        self.assertNotIn("dev-", line)
        self.assertEqual(tc.line_routing([]), "routing: no token_issued in the audit log")

    def test_band(self):
        self.assertEqual(tc.line_band("mWifiInfo SSID: <x>, RSSI: -60, Frequency: 5180, Tx Link speed: 433"),
                         "band: 5 GHz (5180 MHz)")
        self.assertEqual(tc.line_band("mWifiInfo RSSI: -60, Frequency: 2412"), "band: 2.4 GHz (2412 MHz)")
        self.assertEqual(tc.line_band(None), "band: adb off-LAN")

    def test_keeper(self):
        self.assertEqual(tc.line_keeper("2026-10-30T20:00:00Z | running | copies 3\n", "active"),
                         "log-keeper: 2026-10-30T20:00:00Z | running | copies 3; unit active")
        self.assertEqual(tc.line_keeper(None, "inactive"), "log-keeper: not running (no status); unit inactive")


class TheOutput(unittest.TestCase):
    def test_six_lines_redacted_and_a_failing_reader_still_prints(self):
        fake = ["adopted: 13 lines; host check ok", f"apk: odd {V4}", "overlay: connected yes, path direct, peers 1",
                "routing: newest token_issued overlay at x", "band: adb off-LAN", "log-keeper: running; unit active"]
        with mock.patch.object(tc, "lines", lambda trip_dir: fake), \
                mock.patch.object(tc.tlk, "load_secrets", lambda: []):
            buf = io.StringIO()
            with redirect_stdout(buf):
                tc.main([])
        out = buf.getvalue().splitlines()
        self.assertEqual(len(out), 6)
        self.assertNotIn(V4, "\n".join(out))
        self.assertEqual(out[1], "apk: odd <ipv4>")
        self.assertEqual(tc.safe(lambda: 1 / 0, "band"), "band: unknown (ZeroDivisionError)")

    def test_lines_with_every_source_down(self):
        with mock.patch.object(tc, "e1_suite", side_effect=OSError("no suite")), \
                mock.patch.object(tc.tlk, "overlay_state", side_effect=OSError("no provider")), \
                mock.patch.object(tc, "tail_lines", side_effect=OSError("no audit")), \
                mock.patch.object(tc, "unit_state", return_value=None):
            got = tc.lines(Path("/nonexistent-trip-dir"))
        self.assertEqual(len(got), 6)
        self.assertEqual([g.split(":")[0] for g in got], ["adopted", "apk", "overlay", "routing", "band", "log-keeper"])
        self.assertTrue(got[0].startswith("adopted: unknown"))
        self.assertEqual(got[4], "band: adb off-LAN")


if __name__ == "__main__":
    unittest.main()
