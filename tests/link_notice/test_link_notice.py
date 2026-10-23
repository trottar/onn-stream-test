#!/usr/bin/env python3
"""B14 (host): the client's link notice from the heartbeat -- recorded beside the link fields and its transitions
logged, only with PRIVYHUB_LINK_REPORT=1. B3's tests keep their own file.

    python3 -m unittest discover -s tests/link_notice -v
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import link_notice as ln  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402
from games import native_stream_heartbeat as nsh  # noqa: E402


def recovery():
    return ldr.LinkDropRecovery(
        Path(tempfile.mkdtemp(prefix="b14_rec_")), pause_game=lambda: None, resume_game=lambda: None,
        save_recovery_state=lambda: {}, restart_encoder=lambda: {}, full_start_encoder=lambda: {},
        stream_active=lambda: True, end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
        recovery_save_detail=lambda: {})


def rows(rec):
    p = rec.log_path()
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


class Transitions(unittest.TestCase):
    def test_shown_once_cleared_once(self):
        rec, log = recovery(), ln.NoticeLog()
        seq = [0, 0, 1, 1, 1, 3, 0, 0, 2, 0]
        out = [log.note(rec, b, {"sequence": i, "link_frequency_mhz": 2412, "link_rssi_dbm": -68, "link_tx_mbps": 121})
               for i, b in enumerate(seq)]
        self.assertEqual(out, [None, None, "link_notice_shown", None, None, None, "link_notice_cleared", None,
                               "link_notice_shown", "link_notice_cleared"])
        r = rows(rec)
        self.assertEqual([x["event"] for x in r], ["link_notice_shown", "link_notice_cleared", "link_notice_shown",
                                                   "link_notice_cleared"])
        self.assertEqual((r[0]["reasons"], r[0]["reason_names"], r[0]["link_frequency_mhz"]), (1, ["band_2_4_ghz"], 2412))
        self.assertEqual(r[2]["reason_names"], ["rssi_weak"])
        self.assertEqual(ln.names(7), ["band_2_4_ghz", "rssi_weak", "tx_slow"])


class TheHeartbeat(unittest.TestCase):
    def test_recorded_only_with_the_link_report(self):
        root = Path(tempfile.mkdtemp(prefix="b14_hb_"))
        values = {"sequence": 1, "link_notice": 1}
        saved = nsh.LINK_FIELDS
        try:
            nsh.LINK_FIELDS = None
            nsh.append_native_stream_heartbeat(root, values)
            nsh.LINK_FIELDS = ("link_rssi_dbm",)
            nsh.append_native_stream_heartbeat(root, values)
            nsh.append_native_stream_heartbeat(root, {"sequence": 2})       # an older client: no key, nothing new
        finally:
            nsh.LINK_FIELDS = saved
        lines = [json.loads(x) for x in nsh.heartbeat_log_path(root).read_text().splitlines()]
        self.assertNotIn("link_notice", lines[0])
        self.assertEqual(lines[1]["link_notice"], 1)
        self.assertNotIn("link_notice", lines[2])


class FlagAbsent(unittest.TestCase):
    def _run(self, extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        env.update(extra)
        code = ("import sys, ast, pathlib; sys.path.insert(0, 'companion'); "
                "src = pathlib.Path('companion/plugins/games.py').read_text(); t = ast.parse(src); "
                "g = [n for n in t.body if isinstance(n, ast.If) and 'import link_notice' in ast.unparse(n)]; "
                "ns = {'os': __import__('os')}; exec(compile(ast.Module(body=g, type_ignores=[]), 'g', 'exec'), ns); "
                "print('link_notice' in sys.modules)")
        out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                             timeout=120)
        return out.stdout.strip(), out.stderr[-400:]

    def test_the_import_follows_the_link_report_flag(self):
        self.assertEqual(self._run({})[0], "False")
        self.assertEqual(self._run({"PRIVYHUB_LINK_REPORT": "1"})[0], "True")

    def test_hook_shapes(self):
        def ifs(rel, text):
            tree = ast.parse((ROOT / "companion" / rel).read_text())
            return [n for n in ast.walk(tree) if isinstance(n, ast.If) and ast.unparse(n.test).startswith(text)]
        self.assertEqual(len(ifs("plugins/games.py", "_link_notice is not None")), 3)
        self.assertEqual(len(ifs("games/native_stream_heartbeat.py", "'link_notice' in values")), 1)


if __name__ == "__main__":
    unittest.main()
