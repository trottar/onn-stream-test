#!/usr/bin/env python3
"""B26: under `PRIVYHUB_RESTART_FAST_UNLOCK=1`, nothing from the old encoder forwarded after the relay's stop.

    python3 -m unittest discover -s tests/restart_fast_unlock_relay -v

B24's harness (`tests/restart_fast_unlock/test_restart_fast_unlock.py`, imported as a module, unedited; it imports
B22's) with the REAL `NativeVideoFecRelay` on loopback in place of the fake relay: one fixed free port for the old
and the new relay (as in production), a fake onn (a UDP socket recording every arrival), and fake encoders that send
the held picture's frames at 60 fps: 14 packets, an 8-byte unmarked first packet, 13 x 1,188 B, the marker on the
last (CL-B14: 840 packets / 876,856 B a second). The old encoder's SSRC is A, the new one's B.

CL-B14's window: the relay's `stop()` joins the impairment shim's thread (<= 50 ms) under its lock, before it closes
the receive socket, so the receive thread reads the next frame's first packet, waits on the lock, and notes and sends
it after. `FakeShim` holds the lock the same 50 ms but leaves the send target the onn (the twelve lines' path).
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "restart_fast_unlock"))

import test_restart_fast_unlock as u  # noqa: E402  (B24's harness, unedited; its tests not collected here)
import native_fec_relay as nfr  # noqa: E402
import impairment  # noqa: E402

h = u.h
SSRC_OLD, SSRC_NEW = 0xA0A0A0A0, 0xB0B0B0B0
FRAME_S = 1.0 / 60.0
LOOP = impairment.LOOPBACK   # the loopback, built as the shim builds it


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((LOOP, 0))
    port = s.getsockname()[1]
    s.close()
    return port


def rtp(seq, ts, ssrc, marker, payload):
    return (bytes([0x80, (0x80 if marker else 0) | 96]) + (seq & 0xFFFF).to_bytes(2, "big")
            + (ts & 0xFFFFFFFF).to_bytes(4, "big") + ssrc.to_bytes(4, "big") + payload)


class FakeOnn:
    """Every datagram the relay sends: (time, kind, ssrc, ts, payload length)."""

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((LOOP, 0))
        self.sock.settimeout(0.05)
        self.port = self.sock.getsockname()[1]
        self.rows = []
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def _run(self):
        while not self._stop.is_set():
            try:
                data = self.sock.recv(65535)
            except socket.timeout:
                continue
            except OSError:
                return
            t = h.now()
            if data[:4] == nfr.FEC_MAGIC:
                self.rows.append((t, "parity", None, None, len(data)))
            else:
                self.rows.append((t, "rtp", int.from_bytes(data[8:12], "big"), int.from_bytes(data[4:8], "big"),
                                  len(data) - 12))

    def stop(self):
        self._stop.set()
        self._t.join(2)
        self.sock.close()


class Encoder(h.FakeProc):
    """A fake encoder process that also sends frames to the relay's port while it lives."""

    def __init__(self, registry, window, exit_delay_s, events, name, port, ssrc, exit_packet=False):
        super().__init__(registry, window, exit_delay_s, events, name)
        self.port, self.ssrc, self.exit_packet = port, ssrc, exit_packet
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.frames = []                 # (first packet's send time, ts)
        self.ends = {}                   # ts -> its last packet's send time
        self.burst_done = threading.Event()
        self.sending = True
        self.halt = threading.Event()
        self._seq, self._ts = 1000, 90000
        threading.Thread(target=self._run, daemon=True).start()

    def alive(self):
        return not self._done and (self._exit_at is None or time.monotonic() < self._exit_at)

    def _send(self, data):
        try:
            self.sock.sendto(data, (LOOP, self.port))
        except OSError:
            pass

    def _run(self):
        nxt = time.monotonic()
        while not self.halt.is_set() and self.alive():
            if self.sending:
                self.burst_done.clear()
                self._ts += 1500
                self.frames.append((h.now(), self._ts))
                self._send(rtp(self._seq, self._ts, self.ssrc, False, b"\x41" + b"\x9a" * 7))
                for i in range(13):
                    self._seq += 1
                    last = i == 12
                    self._send(rtp(self._seq, self._ts, self.ssrc, last,
                                   bytes([0x7C, 0x0C | (0x40 if last else 0)]) + b"\x00" * 1186))
                self._seq += 1
                self.ends[self._ts] = h.now()
                self.burst_done.set()
            nxt += FRAME_S
            time.sleep(max(0.0, nxt - time.monotonic()))

    def terminate(self):
        super().terminate()
        if self.exit_packet:             # the queue's question: 8 bytes at exit, nothing after
            self.sending = False
            self._ts += 1500
            self.frames.append((h.now(), self._ts))
            self._send(rtp(self._seq, self._ts, self.ssrc, False, b"\x41" + b"\x9a" * 7))
            self._seq += 1


class FakeShim:
    """The real shim's `stop()` cost (its thread's join, <= 50 ms) under the relay's lock; sends nothing itself."""

    def stop(self):
        time.sleep(0.050)


class RealRelay(u.Unlocked):
    def setUp(self):
        super().setUp()
        self.port = free_port()
        self.onn = FakeOnn()
        self.encoders = []
        self.relay = nfr.NativeVideoFecRelay(local_port=self.port, pacing_us=0,
                                             frame_size_log=Path(self.tmp) / "native_frame_sizes.jsonl")

    def tearDown(self):
        for e in self.encoders:
            e.halt.set()
        for p in self.plugins:
            w = getattr(getattr(p, "_restart_fast", None), "_worker", None)
            if w is not None:
                w.join(10)
        self.relay.stop()                 # before the harness's patches (the shim's module) are undone
        super().tearDown()
        self.onn.stop()

    def run_restart(self, shim, exit_packet=False, old_exit_s=1.0):
        """`shim`: None (no shim: the twelve lines), "fake" (the 50-ms hold, target the onn), "real" (none@post-fec)."""
        if shim == "real":
            shimmer = types.SimpleNamespace(relay_shim_from_environ=lambda env, port, target, root: impairment.RelayShim(
                impairment.parse("none@post-fec,seed=1"), port, target, None))
        else:
            shimmer = types.SimpleNamespace(relay_shim_from_environ=lambda env, port, target, root: None)
        patch = h.mock.patch.object(nfr, "_impairment", shimmer if shim else None)
        patch.start()
        self.patches.append(patch)
        self.relay.start(LOOP, self.onn.port)
        if shim == "fake":
            self.relay._shim = FakeShim()
        calls = []
        stop = self.relay.stop

        def traced():
            calls.append(h.now())
            stop()

        self.relay.stop = traced
        m = h.manager(self.events, self.registry, self.tmp, old_exit_s=old_exit_s)
        m._fec_relay = self.relay
        self.registry.down("w1")         # h.manager's own fake old encoder is replaced by this one
        old = Encoder(self.registry, "w1", old_exit_s, self.events, "old_encoder", self.port, SSRC_OLD, exit_packet)
        m._process = old
        self.encoders.append(old)

        def popen(cmd, **kw):
            time.sleep(0.3)
            self.events.add("new_encoder_spawned")
            e = Encoder(self.registry, cmd[-1], 0.05, self.events, "new_encoder", self.port, SSRC_NEW)
            self.encoders.append(e)
            return e

        m._popen = popen
        self.popen = popen
        time.sleep(0.3)                   # the old stream established
        p = h.plugin(u.G_UNLOCK, m, self.events)
        p._restart_fast = u.G_UNLOCK._restart_fast_unlock.RestartFastUnlock(p._recovery._log)
        self.plugins.append(p)
        old.burst_done.wait(1.0)          # just after a frame: the stop lands between frames
        old.burst_done.clear()
        old.burst_done.wait(1.0)
        time.sleep(0.006)                 # the relay has handled that frame: its receive thread idle, as at CL-B14's stops
        p.handle_post_request("native-stream-start", f"port={self.onn.port}&guard_end=1", LOOP)
        p._restart_fast._worker.join(10)
        time.sleep(0.4)                   # the new stream's frames
        self.relay.stop = stop
        return old, calls[0]

    def after(self, old, stop_at):
        """Every old packet the onn received more than 10 ms after the stop's call (a packet whose send began before
        the stop arrives within it; the held one comes after the lock's release, >= 50 ms with the hold), and any
        parity between then and the new stream's first packet."""
        first_new = min((t for t, k, s, ts, n in self.onn.rows if s == SSRC_NEW), default=float("inf"))
        data = [r for r in self.onn.rows if r[2] == SSRC_OLD and r[0] > stop_at + 0.010]
        parity = [r for r in self.onn.rows if r[1] == "parity" and stop_at + 0.010 < r[0] < first_new]
        return data, parity

    def frame_rows(self):
        path = Path(self.tmp) / "native_frame_sizes.jsonl"
        return [json.loads(x) for x in path.read_text().splitlines()] if path.is_file() else []

    def strays(self):
        return [r for r in self.frame_rows() if r["frames"] == 1 and r["packets"] == 1 and r["unmarked_frames"] == 1]

    def dump(self, tag, old, stop_at):
        d = os.environ.get("B26_TIMELINE")
        if not d:
            return
        data, parity = self.after(old, stop_at)
        done = next((r[2] for r in self.events.rows if r[1] == "restart_fast_done"), {})
        with open(os.path.join(d, f"relay_{tag}.txt"), "w") as f:
            f.write(f"restart_fast_done: {done}\n")
            f.write(f"old frames begun after the stop's call: {sum(1 for t, _ in old.frames if t > stop_at)}\n")
            f.write(f"old data packets at the onn > 10 ms after the call (ms after it, payload B): {len(data)} "
                    f"{[(round((t - stop_at) * 1000, 1), n) for t, _, _, _, n in data]}\n")
            f.write(f"old parity at the onn > 10 ms after the call, before the new stream: {len(parity)}\n")
            f.write(f"new (SSRC B) packets at the onn: {sum(1 for r in self.onn.rows if r[2] == SSRC_NEW)}\n")
            f.write(f"1-packet unmarked frame rows in the frame log: {self.strays()}\n")


class TheStrayPacket(RealRelay):
    def test_8_bytes_at_exit_nothing_forwarded_after_the_stop(self):
        old, stop_at = self.run_restart(None, exit_packet=True)
        self.dump("exit_packet", old, stop_at)
        data, parity = self.after(old, stop_at)
        self.assertEqual(data, [])
        self.assertEqual(parity, [])
        self.assertEqual(self.strays(), [])
        self.assertIn("old_encoder_terminated", self.events.names())

    def test_cl_b14s_window_on_the_onns_path_nothing_forwarded(self):
        old, stop_at = self.run_restart("fake")
        self.dump("fake_shim_window", old, stop_at)
        self.assertTrue(any(t > stop_at for t, _ in old.frames))      # a frame began inside the stop
        data, parity = self.after(old, stop_at)
        self.assertEqual(data, [], "an old frame begun after the stop reached the onn")
        self.assertEqual(parity, [])
        self.assertEqual(self.strays(), [])

    def test_cl_b14_reproduced_with_the_real_post_fec_shim(self):
        old, stop_at = self.run_restart("real")
        self.dump("real_shim", old, stop_at)
        data, parity = self.after(old, stop_at)
        self.assertEqual(data, [])                                    # as CL-B14: never reached the onn
        self.assertEqual(self.strays(), [])                           # and now no 1-packet row


class TheRestartStillWorks(RealRelay):
    def test_the_new_encoders_frames_and_the_rows(self):
        old, stop_at = self.run_restart("fake")
        new = [r for r in self.onn.rows if r[2] == SSRC_NEW]
        self.assertGreater(len(new), 14 * 10)
        done = next(r[2] for r in self.events.rows if r[1] == "restart_fast_done")
        self.assertEqual(set(done), {"lock_ms", "relay_stopped_ms", "released_ms", "spawned_ms", "checked_ms",
                                     "unlocked_ms"})
        self.assertLessEqual(done["unlocked_ms"] - done["checked_ms"], 20.0)
        self.assertTrue(self.relay.running)
        self.assertEqual(self.registry.max_live, {"w1": 1})
        # every old frame sent whole before the stop's call forwarded whole (the relay's ordinary path untouched)
        before = {ts for ts, end in old.ends.items() if end < stop_at - 0.020}   # the receive thread's lag allowed
        got = {}
        for r in self.onn.rows:
            if r[2] == SSRC_OLD and r[3] in before:
                got[r[3]] = got.get(r[3], 0) + 1
        self.assertTrue(before)
        self.assertEqual({ts: n for ts, n in got.items() if n != 14}, {})
        self.assertEqual(set(got), before)


class TheHelper(unittest.TestCase):
    def test_a_relay_without_the_internals_is_stopped_as_is(self):
        events = h.Events()
        r = h.FakeRelay(events)
        u.rfu.RestartFastUnlock._stop_relay(r)
        self.assertFalse(r.running)
        self.assertEqual(events.names(), ["relay_stop"])


if __name__ == "__main__":
    unittest.main()
