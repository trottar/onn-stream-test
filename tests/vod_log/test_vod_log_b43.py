"""B43: the client log's whitelist gains `reason` / `kind` / `token_refetched` (a B43 client inside vod_retry=1); a
B35 client's rows (none of the three) are written as before, field for field."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import vod_log  # noqa: E402


def _rows(d: str) -> list[dict]:
    p = Path(d) / "logs" / vod_log.CLIENT_LOG_NAME
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


class B43Fields(unittest.TestCase):
    base = {"event": "vod_retry", "media": "0123456789ab", "attempt": 2, "position_ms": 6_600_000,
            "delay_ms": 2000, "elapsed_ms": 1003, "bound_ms": 150_000, "error_code": 2004,
            "error_name": "ERROR_CODE_IO_BAD_HTTP_STATUS"}

    def test_the_new_fields_written_when_valid(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            log = vod_log.ClientLog(Path(d), clock=lambda: 0.0)
            log.accept(dict(self.base, reason="401", token_refetched=True))
            for r in ("reset", "refused", "timeout", "403"):
                log.accept({"event": "vod_error", "media": "0123456789ab", "reason": r})
            for k in ("lost", "refused"):
                log.accept({"event": "vod_gave_up", "media": "0123456789ab", "attempts": 3, "reason": "401", "kind": k})
            rows = _rows(d)
            self.assertEqual((rows[0]["reason"], rows[0]["token_refetched"]), ("401", True))
            self.assertEqual([r["reason"] for r in rows[1:5]], ["reset", "refused", "timeout", "403"])
            self.assertEqual([r["kind"] for r in rows[5:]], ["lost", "refused"])

    def test_junk_refused_and_nothing_written(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            log = vod_log.ClientLog(Path(d), clock=lambda: 0.0)
            for bad in ({"reason": "500"}, {"reason": 401}, {"reason": "x" * 80}, {"kind": "gone"},
                        {"token_refetched": 1}, {"token_refetched": "true"}):
                with self.assertRaises(ValueError):
                    log.accept(dict(self.base, **bad))
            self.assertEqual(_rows(d), [])

    def test_a_b35_row_is_written_as_before(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            vod_log.ClientLog(Path(d), clock=lambda: 0.0).accept(dict(self.base))
            self.assertEqual(_rows(d), [dict({"at_utc": vod_log.utc_ms(0.0)}, **self.base)])


if __name__ == "__main__":
    unittest.main()
