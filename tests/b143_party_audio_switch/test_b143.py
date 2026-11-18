#!/usr/bin/env python3
"""B143 (host): the sound across a party's planned switch — through the real HTTP server on loopback.

PP-H3c's second sitting: after every planned switch the onn's audio queue stayed empty for as long as the longest
stretch already played in that client session. The hub's sender began every stream at sequence 0 and the app drops a
frame behind what it has played (`OpusReorder.offer`, LATE), so the new process's sound was not played until its own
count passed the old one's. B143: a planned switch continues the audio's sequence and timestamp.

B114's harness, its `b143` mode: the real routes (a held start, the go, practices by Start and by time, the board's
end) drive the real `PartyMinigames._switch_stream`; behind the stream stub's own start, the real
`NativeStreamManager._start_linux_locked` (G8-S2's stubbed manager, nothing spawned) and the real
`NativeAudioStreamer` (Opus, as the hub runs it; pactl answered by stubs; the capture a made-up process writing silence
at the real rate) send to a UDP socket on loopback. The datagrams are fed to `receiver_model.Receiver` (the app's rule,
ported line for line). **Two planned switches, then five (and the end's way back): after every one, the first frame
the modelled app releases comes ≤ BOUND_MS after the new stream's first datagram; every new frame released; the
sequence continuous.** HEAD's code (its companion from git, the same scenario): the silent stretches (each new stream
silent until its count passes the furthest played). A users' start: sequence 0, timestamp 0, its datagrams byte for
byte HEAD's (`UsersStart`). Temp dirs removed.

    python3 -m unittest discover -s tests/b143_party_audio_switch -v
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b114_party_minigame_hang"))
sys.path.insert(0, str(ROOT / "tests" / "b124_party_four_seats"))
sys.path.insert(0, str(HERE))
import test_b114 as b114  # noqa: E402  (its harness; its tests are not collected here)
import test_b124 as b124  # noqa: E402
import receiver_model as rm  # noqa: E402

BASELINE = "246c67da"            # queue AX's baseline: the companion before B143-B145
BOUND_MS = 50.0                  # the design's bound: the new stream's first datagram → the first frame released


def extra(work, frames):
    return {**b124.extra(work, frames), "start_rung": str(ROOT / "tests" / "start_rung")}


def run_mode(code_rev: str | None) -> dict:
    code = b114.code_of(code_rev) if code_rev else None
    if code_rev and code is None:
        raise unittest.SkipTest("git is absent")
    root, ids = b114.b99.tree(code)
    b124.IDS.clear()
    b124.IDS.update(ids)
    return b114.run(root, b114.BOTH, ids, "b143", extra=extra)["steps"]


def analyse(s: dict) -> dict:
    """The datagrams through the modelled receiver (one client session: the board's stream started it); for every
    planned switch (a start that is not the session's first): the new stream's first datagram, the first frame the
    model released after it, the silent stretch in ms, and whether the sequence went on."""
    starts = s["b143_starts"]
    copies, offset = s["b143_redundancy"]
    rec = rm.Receiver(copies=copies, offset_pcm_packets=offset, frame_samples=480)
    dg = sorted(s["b143_dg"], key=lambda d: d[0])
    released: list[tuple[float, int]] = []
    for t, seq, _v, _ts in dg:
        for sq, played in rec.feed(seq):
            if played:
                released.append((t, sq))
    def begin_of(k):
        """Where start k's stream begins: the first datagram after the switch's own gap (> 100 ms) — the old sender
        sends on for a few ms after the start is stamped, until the start stops it."""
        t = starts[k]["t_stop"]
        times = [d[0] for d in dg]
        j = next((j for j in range(1, len(dg)) if times[j] > t and times[j] - times[j - 1] > 0.1), None)
        return times[j] if j is not None else float("inf")
    out = []
    for i, st in enumerate(starts[1:], start=1):
        b0 = begin_of(i)
        nxt = begin_of(i + 1) if i + 1 < len(starts) else float("inf")
        new = [d for d in dg if b0 <= d[0] < nxt]
        if not new:
            out.append({"i": i, "no_datagrams": True})
            continue
        first_t, first_seq = new[0][0], new[0][1]
        rel = [r for r in released if b0 <= r[0] < nxt]
        old = [d for d in dg if d[0] < b0]
        last_old = max(d[1] for d in old[-8:]) if old else None      # the last original (its copies trail by k)
        span_frames = len({d[1] for d in new})
        gap_ms = round((first_t - old[-1][0]) * 1000.0, 1) if old else None   # no datagram: the switch's own gap
        out.append({"i": i, "board": st["board"], "first_seq": first_seq, "last_old_seq": last_old, "gap_ms": gap_ms,
                    "continued": last_old is not None and first_seq == (last_old + 1) & 0xFFFF,
                    "silent_ms": round((rel[0][0] - first_t) * 1000.0, 1) if rel else None,
                    "stream_ms": round((new[-1][0] - first_t) * 1000.0, 1),
                    "frames_new": span_frames, "frames_released": len({r[1] for r in rel}),
                    "audio_start": st["audio_start"]})
    return {"switches": out, "counts": rec.counts}


class AcrossSwitches(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = run_mode(None)
        cls.a = analyse(cls.s)
        if os.environ.get("B143_OUT"):
            import json
            Path(os.environ["B143_OUT"]).write_text(json.dumps({"mine": cls.a, "rows": {
                k: cls.s.get(k) for k in ("b143_thread_exc", "b143_errors", "b143_board_up", "b143_users_start", "a2", "a5", "a2_switch_rows", "a5_switch_rows", "a2_starts", "a5_starts")}},
                indent=1))

    def test_0_the_scenario_played(self):
        s = self.s
        self.assertIsNone(s.get("b143_errors"), s.get("b143_errors"))      # every real start went through
        self.assertIsNone(s.get("b143_thread_exc"), s.get("b143_thread_exc"))
        self.assertEqual(s["a2"]["state"], "ended", s["a2"])
        self.assertEqual(s["a5"]["state"], "ended", s["a5"])
        self.assertEqual(s["a5"].get("practices"), 2, s["a5"])
        two = [r["window"] for r in s["a2_switch_rows"] if r.get("switched")]
        five = [r["window"] for r in s["a5_switch_rows"] if r.get("switched")]
        self.assertEqual(two, ["minigame", "board"])
        self.assertEqual(five, ["minigame", "board", "minigame", "board", "minigame", "board"])
        self.assertEqual(s["b143_users_start"], [0, 0])                  # the board's own (users') start: 0, 0
        self.assertTrue(s["b143_starts"][0]["board"])

    def test_1_every_planned_switch_heard_at_once(self):
        sw = self.a["switches"]
        planned = [x for x in sw if not x.get("no_datagrams")]
        self.assertEqual(len(planned), 8, sw)                          # 2 + 6 starts after the board's own
        for x in planned:
            self.assertTrue(x["continued"], x)                          # the sequence goes on across the switch
            self.assertIsNotNone(x["silent_ms"], x)
            self.assertLessEqual(x["silent_ms"], BOUND_MS, x)
            self.assertGreaterEqual(x["frames_released"], x["frames_new"] - 3, x)   # every frame (the last k held)
        self.assertEqual(self.a["counts"]["late"], 0, self.a["counts"])


class HeadGivesTheSilence(unittest.TestCase):
    """The mutation that shows the fault: HEAD's companion, the same scenario."""

    @classmethod
    def setUpClass(cls):
        cls.s = run_mode(BASELINE)
        cls.a = analyse(cls.s)
        if os.environ.get("B143_OUT_HEAD"):
            import json
            Path(os.environ["B143_OUT_HEAD"]).write_text(json.dumps({"head": cls.a}, indent=1))

    def test_head_restarts_at_zero_and_the_new_streams_are_silent(self):
        planned = [x for x in self.a["switches"] if not x.get("no_datagrams")]
        self.assertEqual(len(planned), 8, self.a["switches"])
        self.assertTrue(all(x["first_seq"] == 0 for x in planned), planned)
        silent = [x for x in planned if x["silent_ms"] is None or x["silent_ms"] > BOUND_MS]
        self.assertGreaterEqual(len(silent), 6, planned)                 # most switches silent past the bound
        self.assertGreater(self.a["counts"]["late"], 500, self.a["counts"])


class ModelChecks(unittest.TestCase):
    """The modelled receiver against the app's own cases (OpusFraming.kt's OpusReorder, k = 2 at 10-ms frames)."""

    def test_the_rule(self):
        r = rm.Receiver(copies=2, offset_pcm_packets=4, frame_samples=480)
        self.assertEqual(r.k, 2)
        self.assertEqual(r.feed(100), [(100, True)])                   # the first frame starts the run
        self.assertEqual(r.feed(101), [(101, True)])                   # in order: released at once
        self.assertEqual(r.feed(101), [])                              # a duplicate (the receive path's window)
        self.assertEqual(r.feed(103), [])                              # 102 missing: held for its copy (k = 2)
        self.assertEqual(r.feed(104), [])
        self.assertEqual(r.feed(105), [(102, False), (103, True), (104, True), (105, True)])   # given up after k
        self.assertEqual(r.feed(0), [])                                # far behind: LATE, dropped
        self.assertEqual(r.counts["late"], 1)
        self.assertEqual(r.feed(106 + 64), [(106 + 64, True)])         # 64 ahead: a JUMP, taken at once
        self.assertEqual(r.counts["jump"], 1)
        fresh = rm.Receiver()
        played = [x for sq in range(300) for x in fresh.feed(sq)]      # a stream of 300 frames
        played += [x for sq in range(250) for x in fresh.feed(sq)]     # a new one at 0: 250 frames, all LATE
        played += [x for sq in range(250, 320) for x in fresh.feed(sq)]
        self.assertEqual(len(played), 300 + 20)                        # only what passed 300 is played


SENDER = r'''
import json, os, sys, threading, time, types
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import native_session_io as nsio, audio_codec as ac
codec = sys.argv[2]
class Sock:
    def __init__(s): s.log = []
    def setsockopt(s, *a): pass
    def setblocking(s, *a): pass
    def sendto(s, d, a): s.log.append(bytes(d).hex())
    def close(s): pass
out = []
a = nsio.NativeAudioStreamer(Path(sys.argv[3]))
a._redundancy_copies, a._redundancy_offset_packets = 2, 4
if hasattr(a, "party_continue_next"):
    a.party_continue_next(424242)                     # an arm for another process: must not touch this start
for run in range(2):
    sock = Sock()
    if hasattr(a, "_audio_start_counters"):
        a._audio_start = a._audio_start_counters(os.getpid())    # as `_start_linux_locked` does, for this process
    a._linux_stop_event = threading.Event()
    n = {"k": 0}
    def wait_until(deadline):
        n["k"] += 1
        if n["k"] > 60:
            a._linux_stop_event.set()
            return False
        return True
    a._linux_wait_until = wait_until
    a._client_ip, a._client_port = "127.0.0.1", 9
    if codec == "opus":
        a._audio_codec_opus = ac.OpusSession(128, 10)
        ac.run_opus_sender(a, a._audio_codec_opus, "127.0.0.1", 9, sock_factory=lambda: sock)
    else:
        import socket as real
        nsio.socket = types.SimpleNamespace(socket=lambda *x: sock, AF_INET=real.AF_INET, SOCK_DGRAM=real.SOCK_DGRAM,
                                            SOL_SOCKET=real.SOL_SOCKET, SO_SNDBUF=real.SO_SNDBUF)
        a._linux_prepare_sender_scheduler = lambda: True
        nsio.AUDIO_CODEC = None
        a._linux_sender_loop()
    out.append(sock.log)
print(json.dumps(out))
'''


class UsersStart(unittest.TestCase):
    """A users' start (no arm for its process; an arm for another): sequence and timestamp 0, byte for byte HEAD's —
    the Opus sender (as the hub runs) and the PCM one, two starts each, 60 ticks each."""

    def datagrams(self, companion: Path, codec: str, tmp: Path) -> list:
        import json
        r = subprocess.run([sys.executable, "-I", "-B", "-c", SENDER, str(companion), codec, str(tmp)],
                           capture_output=True, text=True, timeout=120, env={k: v for k, v in os.environ.items()
                                                                             if not k.startswith("PRIVYHUB_")})
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_users_start_byte_for_byte(self):
        import tempfile
        head = b114.code_of(BASELINE)
        if head is None:
            self.skipTest("git is absent")
        tmp = Path(tempfile.mkdtemp(prefix="b143_users_"))
        for codec in ("opus", "pcm"):
            mine = self.datagrams(ROOT / "companion", codec, tmp)
            theirs = self.datagrams(head / "companion", codec, tmp)
            self.assertEqual(len(mine), 2)
            self.assertTrue(all(len(x) >= 60 for x in mine), [len(x) for x in mine])
            self.assertEqual(mine, theirs, codec)
            for run in mine:                                       # each start at sequence 0, timestamp 0
                first = bytes.fromhex(run[0])
                self.assertEqual(first[6:8], b"\x00\x00")
                self.assertEqual(first[8:12], b"\x00\x00\x00\x00")


if __name__ == "__main__":
    unittest.main()
