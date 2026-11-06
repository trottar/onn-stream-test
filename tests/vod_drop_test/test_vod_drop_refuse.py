"""B43: B40's drop gains a refusal window -- `drop <seconds>` appended to the trigger file keeps every new /vod/ request
reset (an RST, no HTTP response) for that long, after the one reset of the streams in flight. A plain line or `drop 0`
is B40 as built (its row byte for byte). Only the appended bytes are read. Loopback only; B40's harness reused (its own
suite unedited); the windows are scaled down (`drop 0.8`) so the suite stays quick -- the code path is the 45-s one.
"""
from __future__ import annotations

import socket
import time
import unittest

import test_vod_drop_test as b40  # B40's harness (same directory); its TestCases are not re-exported here
import vod_drop_test

DropTestCase = b40.DropTestCase


def _raw(port: int, path: str, rng: str | None = None) -> tuple[str, bytes]:
    """One request; (`eof` / the error's name, every byte received)."""
    s = socket.create_connection((b40.LOOP, port), timeout=5)
    got = b""
    try:
        s.sendall(b40._get(path, rng))
        while True:
            chunk = s.recv(1 << 20)
            if not chunk:
                return "eof", got
            got += chunk
    except OSError as exc:
        return type(exc).__name__, got
    finally:
        s.close()


class Refusal(DropTestCase):
    def append(self, line: str) -> None:
        with open(self.project / vod_drop_test.TRIGGER, "a") as fh:
            fh.write(line + "\n")

    def test_drop_seconds_resets_the_stream_then_refuses_new_vod_requests_for_the_window(self) -> None:
        player = b40._Player(self.server.port, self.path)
        b40._wait_streaming(self.test)
        self.append("drop 0.8")
        injected = self.test.poll_once()
        self.assertEqual(player.read_rest(), "ConnectionResetError")
        self.assertEqual((injected["dropped"], injected["how"], injected["refuse_s"]), (1, "rst", 0.8))
        # inside the window: a /vod/ request gets an RST and not one byte of HTTP; another path is served
        how, got = _raw(self.server.port, self.path, "bytes=1000-")
        self.assertNotIn(b"HTTP/", got)
        self.assertIn(how, ("ConnectionResetError", "eof"))
        how2, got2 = _raw(self.server.port, self.path, "bytes=2000-")
        self.assertNotIn(b"HTTP/", got2)
        live_how, live = _raw(self.server.port, "/live/channel.ts", "bytes=0-99")
        self.assertIn(b"206 Partial Content", live.split(b"\r\n", 1)[0])
        self.assertIsNone(self.test.tick())                      # the window still open
        time.sleep(0.9)
        ended = self.test.tick()
        self.assertEqual((ended["event"], ended["trigger"], ended["refuse_s"], ended["vod_refused"]),
                         ("vod_refuse_ended", 1, 0.8, 2))
        # after the window: served again (the resume)
        pos = 4_321_000
        resumed = b40._Player(self.server.port, self.path, rng=f"bytes={pos}-", first=0)
        self.assertEqual(resumed.read_rest(), "eof")
        self.assertEqual(resumed.body(), b40._payload()[pos:])
        self.assertEqual([r["event"] for r in self.rows(n=2)], ["vod_drop_injected", "vod_refuse_ended"])
        for r in self.rows():
            self.assert_redacted(r)

    def test_a_plain_line_is_b40_as_built_its_row_byte_for_byte(self) -> None:
        player = b40._Player(self.server.port, self.path)
        b40._wait_streaming(self.test)
        self.touch()                                              # B40's own command: a date line
        injected = self.test.poll_once()
        self.assertEqual(player.read_rest(), "ConnectionResetError")
        self.assertEqual(sorted(injected), ["at_utc", "dropped", "event", "how", "ids", "trigger"])
        again = b40._Player(self.server.port, self.path, rng="bytes=5-", first=0)
        self.assertEqual(again.read_rest(), "eof")               # no window: served at once
        self.assertIsNone(self.test.tick())
        self.assertEqual(self.test.refused, 0)

    def test_drop_0_is_a_plain_line(self) -> None:
        self.append("drop 0")
        row = self.test.poll_once()
        self.assertNotIn("refuse_s", row)
        self.assertFalse(self.test._refusing())

    def test_only_the_appended_bytes_are_read_an_old_drop_line_never_applies(self) -> None:
        self.append("drop 30")                                    # before this DropTest's start: the baseline
        fresh = self.make_test()
        self.touch()                                              # a plain line appended after the start
        row = fresh.poll_once()
        self.assertNotIn("refuse_s", row)
        self.append("drop 0.5")
        self.assertEqual(fresh.poll_once()["refuse_s"], 0.5)
        self.assertTrue((self.project / vod_drop_test.TRIGGER).exists())   # never removed

    def test_a_new_trigger_inside_a_window_closes_it_first(self) -> None:
        self.append("drop 5")
        first = self.test.poll_once()
        self.append("x")
        second = self.test.poll_once()
        rows = self.rows(n=3)
        self.assertEqual([r["event"] for r in rows], ["vod_drop_injected", "vod_refuse_ended", "vod_drop_injected"])
        self.assertEqual((rows[1]["trigger"], rows[1]["refuse_s"], rows[1]["vod_refused"]), (1, 5.0, 0))
        self.assertEqual((first["trigger"], second["trigger"]), (1, 2))
        self.assertNotIn("refuse_s", second)
        self.assertFalse(self.test._refusing())

    def test_a_loader_retrying_through_the_window_is_reset_every_time_then_served(self) -> None:
        # Media3's progressive loader, scaled 1:10 (0, 0.1, 0.2, 0.3, 0.4, 0.5 s ...): every attempt inside the
        # window gets a reset; the first one after it gets the body
        self.append("drop 0.8")
        self.test.poll_once()
        outcomes, n, start = [], 0, time.time()
        while True:
            time.sleep(min(max(n - 1, 0) * 0.1, 0.5))
            how, got = _raw(self.server.port, self.path, "bytes=100-199")
            n += 1
            ok = b"206 Partial Content" in got.split(b"\r\n", 1)[0]
            outcomes.append((round(time.time() - start, 2), ok))
            if ok:
                break
            self.assertLess(time.time() - start, 3.0)
        self.assertGreaterEqual(len(outcomes), 3)
        self.assertTrue(all(not ok for _, ok in outcomes[:-1]))
        self.assertGreaterEqual(outcomes[-1][0], 0.8)
        self.assertEqual(self.test.refused, len(outcomes) - 1)


class Parse(unittest.TestCase):
    def test_refuse_seconds(self) -> None:
        f = vod_drop_test.refuse_seconds
        self.assertEqual(f(b"drop 45\n"), 45.0)
        self.assertEqual(f(b"drop 45"), 45.0)
        self.assertEqual(f(b"  drop   2.5  \n\n"), 2.5)
        self.assertEqual(f(b"drop 9999\n"), vod_drop_test.REFUSE_MAX_S)
        self.assertEqual(f(b"drop 45\n2026-11-06T18:00:00Z\n"), 0.0)   # the last line wins
        self.assertEqual(f(b"2026-11-06T18:00:00Z\ndrop 3\n"), 3.0)
        for junk in (b"", b"\n", b"drop", b"drop -3", b"drop abc", b"DROP 5", b"drop 5 s", b"\xff\xfe"):
            self.assertEqual(f(junk), 0.0, junk)


if __name__ == "__main__":
    unittest.main()
