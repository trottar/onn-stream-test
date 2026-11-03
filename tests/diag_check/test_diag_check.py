#!/usr/bin/env python3
"""B36: the diag check -- trip_check's six lines, the sixth now `privyhub-diag` (fakes only; no adb, no network).

    python3 -m unittest discover -s tests/diag_check -v
"""

from __future__ import annotations

import io
import ipaddress
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import diag_check as dc  # noqa: E402
import trip_check as tc  # noqa: E402

V4 = str(ipaddress.ip_address(0xC6336414))


class TheLines(unittest.TestCase):
    def test_the_sixth_line_is_the_diag_keeper(self):
        self.assertEqual(dc.UNIT, "privyhub-diag")
        self.assertEqual(dc.line_keeper("2026-11-02T20:00:00Z | running | copies 3\n", "active"),
                         "diag-keeper: 2026-11-02T20:00:00Z | running | copies 3; unit privyhub-diag active")
        self.assertEqual(dc.line_keeper(None, "inactive"), "diag-keeper: not running (no status); unit privyhub-diag inactive")

    def test_lines_one_to_five_are_trip_checks(self):
        pf = {"manager": [], "environ": ["A=1"], "drop_in_x": True}
        self.assertEqual(dc.line_adopted(pf, ["A=1"]), tc.line_adopted(pf, ["A=1"]))
        self.assertEqual(dc.line_apk("ab" * 32, None, False), tc.line_apk("ab" * 32, None, False))
        self.assertEqual(dc.line_overlay({"connected": True, "path": "direct"}, 2),
                         tc.line_overlay({"connected": True, "path": "direct"}, 2))
        self.assertEqual(dc.line_routing(['{"event": "token_issued", "routing_evidence": "lan"}']),
                         tc.line_routing(['{"event": "token_issued", "routing_evidence": "lan"}']))
        self.assertEqual(dc.line_band("Frequency: 5785, x"), tc.line_band("Frequency: 5785, x"))

    def test_lines_with_every_source_down_read_the_root(self):
        with mock.patch.object(dc, "e1_suite", side_effect=OSError("no suite")), \
                mock.patch.object(dc.tlk, "overlay_state", side_effect=OSError("no provider")), \
                mock.patch.object(dc, "tail_lines", side_effect=OSError("no audit")), \
                mock.patch.object(dc, "unit_state", return_value=None):
            got = dc.lines(Path("/nonexistent-diag-root"))
        self.assertEqual([g.split(":")[0] for g in got], ["adopted", "apk", "overlay", "routing", "band", "diag-keeper"])
        self.assertEqual(got[5], "diag-keeper: not running (no status); unit privyhub-diag ?")

    def test_main_redacts(self):
        fake = ["a", f"apk: odd {V4}", "c", "d", "e", "diag-keeper: running; unit privyhub-diag active"]
        with mock.patch.object(dc, "lines", lambda root: fake), mock.patch.object(dc.tlk, "load_secrets", lambda: []):
            buf = io.StringIO()
            with redirect_stdout(buf):
                dc.main([])
        out = buf.getvalue().splitlines()
        self.assertEqual(len(out), 6)
        self.assertEqual(out[1], "apk: odd <ipv4>")


if __name__ == "__main__":
    unittest.main()
