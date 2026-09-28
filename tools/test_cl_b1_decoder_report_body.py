#!/usr/bin/env python3
"""CL-B1: the decoder report as a POST body -- companion unit tests.

    python3 -m unittest tools/test_cl_b1_decoder_report_body.py -v

The companion itself is not imported (its import starts a reconcile thread):
the pure helpers it calls (`games.decoder_report_http`) and the writer
(`games.decoder_session_log`) are tested directly, and the 414 path on a
throwaway `http.server` whose access log is the companion's guard.
"""

from __future__ import annotations

import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "companion"))

from games import decoder_report_http as h  # noqa: E402
from games import decoder_session_log as dsl  # noqa: E402

LOOPBACK = ".".join(("127", "0", "0", "1"))   # built, so no address literal is stored
R3_REPORT = ROOT / "docs/memory/evidence/c3_l3a_r3_2026-09-24/native_decoder_20260924_193658_993.json"


def the_report() -> str:
    return json.dumps(json.loads(R3_REPORT.read_text())["report"], separators=(",", ":"), ensure_ascii=False)


class BodyFormTests(unittest.TestCase):

    def test_body_and_target_forms_store_identical_reports(self):
        """Rule: a body POST and a target POST of the same report write the same report."""
        report = the_report()
        target_query = "report=" + quote(report, safe="")
        from_target = parse_qs(target_query)["report"][0].strip()      # games.py's target path
        from_json = h.report_from_body(report.encode("utf-8"), "application/json; charset=utf-8")
        from_form = h.report_from_body(target_query.encode("utf-8"), "application/x-www-form-urlencoded")
        self.assertEqual(from_target, report)
        self.assertEqual(from_json, report)
        self.assertEqual(from_form, report)
        with tempfile.TemporaryDirectory() as d:
            a = dsl.write_decoder_session_log(Path(d), from_target)
            import time
            time.sleep(0.01)
            b = dsl.write_decoder_session_log(Path(d), from_json)
            files = sorted((Path(d) / "logs/games/decoder_sessions").glob("*.json"))
            self.assertEqual(len(files), 2)
            ra, rb = (json.loads(f.read_text())["report"] for f in files)
            self.assertEqual(ra, rb)

    def test_the_cap_is_the_only_limit(self):
        """Rule: MAX_REPORT_CHARS (128,000) is the limit; the body bound never refuses
        a report within it (4 bytes/char), and over it the writer refuses with 400's reason."""
        self.assertEqual(dsl.MAX_REPORT_CHARS, 128_000)
        self.assertEqual(h.body_length({"Content-Length": str(4 * 128_000)}), 512_000)
        with self.assertRaises(ValueError):
            h.body_length({"Content-Length": str(4 * 128_000 + 1)})
        with tempfile.TemporaryDirectory() as d:
            big = json.dumps({"x": "y" * 128_100})
            with self.assertRaises(ValueError) as cm:
                dsl.write_decoder_session_log(Path(d), big)
            self.assertIn("too large", str(cm.exception))
            ok = json.dumps({"x": "y" * 60_000})                    # above the old 48,000
            dsl.write_decoder_session_log(Path(d), ok)

    def test_service_logs_the_warning_on_a_refused_body(self):
        """Rule: the body branch keeps R2B's WARNING line and says it arrived as a body."""
        src = (ROOT / "companion/privyhub_service.py").read_text()
        i = src.index('action == "decoder-session-log"\n                    and hasattr(plugin, "handle_decoder_session_log")')
        branch = src[i:i + 2200]
        self.assertIn("WARNING decoder-session-log rejected (400)", branch)
        self.assertIn("decoder-session-log received as body", branch)
        self.assertIn("access_log_path(self)", src)

    def test_request_line_over_the_limit_does_not_crash_the_logger(self):
        """Rule: a request line over 65,536 bytes gets its 414 -- the access log no longer
        reads a `path` that http.server never set (the old logger raised AttributeError)."""

        class Guarded(BaseHTTPRequestHandler):
            def log_message(self, format, *args):        # the companion's guard
                if h.access_log_path(self).startswith("/diagnostics/"):
                    return

        class Old(BaseHTTPRequestHandler):
            def log_message(self, format, *args):        # the pre-CL-B1 shape
                if urlsplit(self.path).path.startswith("/diagnostics/"):
                    return

        def status_for(handler_cls):
            srv = ThreadingHTTPServer((LOOPBACK, 0), handler_cls)
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            err = io.StringIO()
            try:
                with redirect_stderr(err):
                    c = http.client.HTTPConnection(LOOPBACK, srv.server_address[1], timeout=5)
                    c.putrequest("POST", "/plugins/games/decoder-session-log?report=" + "x" * 70_000,
                                 skip_host=True, skip_accept_encoding=True)
                    c.endheaders()
                    try:
                        code = c.getresponse().status
                    except Exception:
                        code = None
                    c.close()
            finally:
                srv.shutdown()
                srv.server_close()
            return code, err.getvalue()

        code_new, err_new = status_for(Guarded)
        self.assertEqual(code_new, 414)
        self.assertNotIn("AttributeError", err_new)
        code_old, err_old = status_for(Old)
        self.assertNotEqual(code_old, 414)       # the defect this fixes: no 414 was sent


if __name__ == "__main__":
    unittest.main()
