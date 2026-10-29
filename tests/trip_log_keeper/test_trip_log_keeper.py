#!/usr/bin/env python3
"""B30: the trip's log-keeper on a fake log dir that rotates (temp dirs only; no stream, no network, no companion).

    python3 -m unittest discover -s tests/trip_log_keeper -v

The secrets and the literals are built from integers; the samplers, the journal and the peer count are fakes; the
clock is fake (the run's sleep advances it).
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import trip_log_keeper as tlk  # noqa: E402

V4 = str(ipaddress.ip_address(0xC6336414))                      # a documentation-range address
V6 = str(ipaddress.ip_address((0xFD7A115CA1E0 << 80) + 0x1234))   # an overlay-range address
EP = f"{ipaddress.ip_address(0xCB007105)}:{41641}"
TAILNET = "".join(chr(c) for c in (116, 97, 105, 108, 45, 102, 97, 107, 101)) + ".example"
CLIENT = "dev-" + "".join("0123456789abcdef"[(i * 7) % 16] for i in range(16))
MACS = ":".join(f"{b:02x}" for b in (0x02, 0x11, 0x22, 0x33, 0x44, 0x55))


class Clock:
    def __init__(self, t):
        self.t = t
        self.hooks = []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += max(s, 0.5)
        for h in list(self.hooks):
            h(self.t)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="b30_"))
        self.logs = self.tmp / "logs"
        self.games = self.logs / "games"
        (self.games / "stream_log_archive").mkdir(parents=True)
        (self.games / "decoder_sessions").mkdir()
        self.out = self.tmp / "trip"
        self.clock = Clock(1_793_500_000.0)
        self.journal = []

    def keeper(self, cap_s=3600.0, start_s=0.0, secrets=(), overlay=None, session=None, copy_s=300.0, sample_s=60.0):
        return tlk.Keeper(self.out, self.clock() + cap_s, self.clock() + start_s, logs_root=self.logs,
                          redactor=tlk.Redactor(lambda: list(secrets)),
                          overlay=overlay or (lambda: {"connected": True, "path": "direct"}),
                          session=session or (lambda: {"state": "idle"}),
                          journal=lambda s, u: self.journal.pop(0) if self.journal else b"",
                          peers=lambda: 1, clock=self.clock, sleep=self.clock.sleep, copy_s=copy_s, sample_s=sample_s)

    def write(self, name, text, mode="a"):
        with open(self.games / name, mode) as fh:
            fh.write(text)

    def chunks(self, key):
        d = self.out / "raw" / key
        return sorted(d.iterdir()) if d.is_dir() else []

    def kept(self):
        return sorted(p for p in (self.out / "raw").rglob("*") if p.is_file())


class TheCopy(Base):
    def test_chunks_concatenate_across_a_rotation_and_a_truncation(self):
        self.write("native_stream_heartbeat.log", "before launch\n")
        k = self.keeper()
        k.begin()
        self.write("native_stream_heartbeat.log", "A1\nA2\n")
        k.copy()
        self.write("native_stream_heartbeat.log", "B1\n")
        os.rename(self.games / "native_stream_heartbeat.log",
                  self.games / "stream_log_archive" / "native_stream_heartbeat.log.1")   # the rotation
        self.write("native_stream_heartbeat.log", "C1\nC2 longer line\n")
        row = k.copy()
        self.assertTrue(any(x.get("rotated") for x in row["kept"]))
        self.write("native_stream_heartbeat.log", "D\n", mode="w")                     # truncated
        k.copy()
        got = b"".join(p.read_bytes() for p in self.chunks("games__native_stream_heartbeat.log"))
        self.assertEqual(got, b"A1\nA2\nB1\nC1\nC2 longer line\nD\n")                # nothing from before the launch

    def test_nothing_rewritten_and_the_manifest_grows_and_verifies(self):
        k = self.keeper()
        k.begin()
        first = {}
        for i in range(4):
            self.write("adaptive_bitrate_shadow.jsonl", json.dumps({"i": i}) + "\n")
            self.journal.append(f"journal line {i}\n".encode())
            k.copy()
            for p in self.kept():
                h = hashlib.sha256(p.read_bytes()).hexdigest()
                self.assertEqual(first.setdefault(p, h), h, p)                      # never rewritten
        lines = (self.out / "manifest.sha256").read_text().splitlines()
        self.assertEqual(len(lines), len(self.kept()))
        self.assertEqual(len(lines), 8)
        for ln in lines:
            h, rel = ln.split("  ", 1)
            self.assertEqual(hashlib.sha256((self.out / rel).read_bytes()).hexdigest(), h)

    def test_the_redactor_replaces_and_counts(self):
        k = self.keeper(secrets=[(TAILNET, "<tailnet>"), (EP, "<endpoint>")])
        k.begin()
        self.write("native_stream_recovery.log",
                   f"peer {TAILNET} via {EP} client {CLIENT} at {V4} v6 {V6} mac {MACS} loop 127.0.0.1 t 21:02:46\n")
        row = k.copy()
        text = self.chunks("games__native_stream_recovery.log")[0].read_text()
        for secret in (TAILNET, EP, CLIENT, V4, V6, MACS):
            self.assertNotIn(secret, text)
        for ph in ("<tailnet>", "<endpoint>", "<client-id>", "<ipv4>", "<ipv6>", "<mac>"):
            self.assertIn(ph, text)
        self.assertIn("127.0.0.1", text)                                           # loopback kept
        self.assertIn("21:02:46", text)                                            # a time is not an address
        counts = row["kept"][0]["redacted"]
        self.assertEqual(counts["<endpoint>"], 1)
        self.assertEqual(counts["<ipv4>"], 1)

    def test_new_decoder_reports_once_each_after_quiet(self):
        k = self.keeper()
        k.begin()
        old = self.games / "decoder_sessions" / "native_decoder_a.json"
        old.write_text('{"a": 1}')
        os.utime(old, (self.clock() - 60, self.clock() - 60))
        fresh = self.games / "decoder_sessions" / "native_decoder_b.json"
        fresh.write_text('{"b": 2}')
        os.utime(fresh, (self.clock(), self.clock()))
        k.copy()
        names = [p.name for p in self.chunks("games__decoder_sessions")]
        self.assertEqual(len(names), 1)
        self.assertTrue(names[0].endswith("native_decoder_a.json"))
        k.copy()
        self.assertEqual(len(self.chunks("games__decoder_sessions")), 1)
        k.copy(final=True)                                                         # the last copy takes the fresh one
        self.assertEqual(len(self.chunks("games__decoder_sessions")), 2)

    def test_a_new_game_log_from_its_first_byte(self):
        k = self.keeper()
        k.begin()
        name = "20261030-201500-game_snes_0123456789abcdef.log"
        self.write(name, "launch\n")
        k.copy()
        self.write(name, "stop\n")
        k.copy()
        got = b"".join(p.read_bytes() for p in self.chunks(f"games__{name}"))
        self.assertEqual(got, b"launch\nstop\n")

    def test_a_restart_that_replaces_the_file_is_followed(self):
        self.write("native_frame_sizes.jsonl", "x\n")
        k = self.keeper()
        k.begin()
        self.write("native_frame_sizes.jsonl", "y\n")
        os.rename(self.games / "native_frame_sizes.jsonl", self.tmp / "moved_away.jsonl")   # gone (a restart)
        row = k.copy()
        self.assertFalse(row.get("errors"))
        self.write("native_frame_sizes.jsonl", "z\n")                                       # back, a new inode
        k.copy()
        got = b"".join(p.read_bytes() for p in self.chunks("games__native_frame_sizes.jsonl"))
        self.assertEqual(got, b"z\n")    # "y" left with the moved file (not in the archive): the gap is a row, not a crash


class TheRun(Base):
    def test_the_cap_ends_it_with_a_last_copy(self):
        k = self.keeper(cap_s=700.0)
        self.clock.hooks.append(lambda t: self.write("native_stream_heartbeat.log", f"{t}\n"))
        self.assertEqual(k.run(), "the cap")
        self.assertIn("done (the cap)", (self.out / "status.txt").read_text())
        rows = [json.loads(x) for x in (self.out / "samples" / "copies.jsonl").read_text().splitlines()]
        self.assertEqual([r["final"] for r in rows], [False, False, True])
        self.assertGreaterEqual(len((self.out / "samples" / "overlay.jsonl").read_text().splitlines()), 11)
        self.assertEqual((self.out / "cap_utc.txt").read_text().strip(), tlk.utc(self.clock.t - (self.clock.t - k.cap)))

    def test_stop_ends_it(self):
        k = self.keeper()
        self.clock.hooks.append(lambda t: (self.out / "STOP").touch() if t > self.clock_start + 130 else None)
        self.clock_start = self.clock()
        self.assertEqual(k.run(), "STOP")
        self.assertIn("done (STOP)", (self.out / "status.txt").read_text())

    def test_a_start_in_the_future_waits(self):
        k = self.keeper(start_s=100.0, cap_s=200.0)
        t0 = self.clock()
        k.run()
        first = json.loads((self.out / "samples" / "overlay.jsonl").read_text().splitlines()[0])
        self.assertGreaterEqual(tlk.parse_utc(first["at_utc"], 0), t0 + 100 - 1)

    def test_another_cap_is_not_overwritten(self):
        self.out.mkdir(parents=True)
        (self.out / "cap_utc.txt").write_text("2026-11-01T23:59:00Z\n")
        with self.assertRaises(SystemExit):
            self.keeper(cap_s=10.0).run()
        self.assertEqual((self.out / "cap_utc.txt").read_text(), "2026-11-01T23:59:00Z\n")

    def test_the_samples_hold_no_address(self):
        k = self.keeper(cap_s=130.0, secrets=[(EP, "<endpoint>")],
                        overlay=lambda: {"connected": True, "path": "relayed", "endpoint": EP, "note": V4},
                        session=lambda: {"state": "PLAYING", "system": "snes", "client": CLIENT})
        k.run()
        text = (self.out / "samples" / "overlay.jsonl").read_text() + (self.out / "samples" / "session.jsonl").read_text()
        for secret in (EP, V4, CLIENT):
            self.assertNotIn(secret, text)
        self.assertIn('"path": "relayed"', text)
        self.assertIn('"peers_online": 1', text)


class TheTimes(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(tlk.utc(tlk.parse_utc("2026-11-01T23:59Z", 0)), "2026-11-01T23:59:00Z")
        self.assertEqual(tlk.parse_utc("now", 5.0), 5.0)
        with self.assertRaises(ValueError):
            tlk.parse_utc("Sunday", 0)


if __name__ == "__main__":
    unittest.main()
