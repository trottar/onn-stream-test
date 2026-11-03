#!/usr/bin/env python3
"""B32 (host): `PRIVYHUB_STEP_IN_PLACE=1` -- a ladder step on the same stream; the explicit cap beside the umbrella.

    python3 -m unittest discover -s tests/step_in_place -v

No stream, no companion, no ffmpeg. The REAL `NativeVideoFecRelay` on loopback, a fake onn (a UDP socket recording
every RTP packet the relay sends: SSRC, sequence, timestamp, the first payload byte), fake encoders (threads sending
60-fps frames of 4 packets to the relay's port: the first frame an IDR (NAL 5), the rest P (NAL 1); the SSRC from the
argv's `-ssrc` when present, else random, as ffmpeg's RTP muxer; a random sequence and timestamp base always), and a
fake stream manager whose `diagnostic_c3_validated_bitrate_transition` is today's restart (the old encoder killed, a
new one with a random SSRC). The cap: B28's harness (`tests/remote_umbrella`, imported, unedited).
"""

from __future__ import annotations

import io
import json
import os
import random
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "start_rung"))
sys.path.insert(0, str(ROOT / "tests" / "remote_umbrella"))

import adaptive_bitrate_live as live  # noqa: E402
import native_fec_relay as nfr  # noqa: E402
import native_stream as ns  # noqa: E402
import remote_cap as rc  # noqa: E402
import remote_ladder as rl  # noqa: E402
import remote_umbrella as ru  # noqa: E402
import step_in_place as sip  # noqa: E402
import stub_manager as stub  # noqa: E402
import test_remote_umbrella as b28  # noqa: E402  (B28's harness, unedited; its tests not collected here)
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

LOOP = "127.0.0.1"
IDR, P = 0x65, 0x41
OVERLAY = b28.OVERLAY


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((LOOP, 0))
    port = s.getsockname()[1]
    s.close()
    return port


class FakeOnn:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((LOOP, 0))
        self.sock.settimeout(0.05)
        self.port = self.sock.getsockname()[1]
        self.rtp = []          # (ssrc, seq, ts, first payload byte, marker, bytes)
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def _run(self):
        while not self._stop.is_set():
            try:
                d = self.sock.recv(65535)
            except socket.timeout:
                continue
            except OSError:
                return
            if d[:4] == nfr.FEC_MAGIC:
                continue
            self.rtp.append((int.from_bytes(d[8:12], "big"), int.from_bytes(d[2:4], "big"),
                             int.from_bytes(d[4:8], "big"), d[12], bool(d[1] & 0x80), d))

    def close(self):
        self._stop.set()
        self._t.join(1)
        self.sock.close()


class FakeEncoder:
    """Popen-like: sends 60-fps RTP frames to the relay until terminated."""
    instances: list["FakeEncoder"] = []

    def __init__(self, argv, port, silent=False):
        self.argv = list(argv)
        self.ssrc = int(argv[argv.index("-ssrc") + 1]) if "-ssrc" in argv else random.getrandbits(32) | 1
        self.kbps = argv[argv.index("-b:v") + 1] if "-b:v" in argv else None
        self.port, self.silent = port, silent
        self.sent = []
        self._stop = threading.Event()
        self.returncode = None
        self.terminated = False
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        FakeEncoder.instances.append(self)

    def _run(self):
        if self.silent:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        seq, ts, frame = random.getrandbits(16), random.getrandbits(32), 0
        nxt = time.monotonic()
        while not self._stop.is_set():
            for i in range(4):
                nal = (IDR if frame == 0 else P) if i == 0 else 0x00
                pkt = (bytes([0x80, (0x80 if i == 3 else 0) | 96]) + (seq & 0xFFFF).to_bytes(2, "big")
                       + (ts & 0xFFFFFFFF).to_bytes(4, "big") + self.ssrc.to_bytes(4, "big") + bytes([nal]) + b"x" * 300)
                s.sendto(pkt, (LOOP, self.port))
                self.sent.append(pkt)
                seq += 1
            ts += 1500
            frame += 1
            nxt += 1 / 60
            time.sleep(max(0.0, nxt - time.monotonic()))
        s.close()

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self._stop.set()
        self._t.join(1)
        self.returncode = -15

    kill = terminate

    def wait(self, timeout=None):
        return self.returncode


class FakeManager:
    """The stream manager's surface the step reads; `diagnostic_c3_validated_bitrate_transition` is today's restart."""
    BITRATE_KBPS = MAX_BITRATE_KBPS = 7000
    FPS = 60
    PROFILE = types.SimpleNamespace(id="native-game-720p60-reference")

    def __init__(self, relay, start_kbps, silent_next=False):
        self._fec_relay = relay
        self._active_bitrate_kbps = start_kbps
        self._log_handle = io.StringIO()
        self.project_root = ROOT
        self._capture_target = {"_window_id": 5}
        self.today_calls = []
        self.silent_next = silent_next
        self._lock = threading.RLock()
        self._process = self.spawn(self.argv(start_kbps))

    def argv(self, kbps):
        return ["ffmpeg", "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-payload_type", "96", "-f", "rtp",
                f"rtp://127.0.0.1:{self._fec_relay.local_port}?pkt_size=1200"]

    def spawn(self, argv, silent=False):
        return FakeEncoder(argv, self._fec_relay.local_port, silent=silent)

    def popen(self, argv, **kw):
        silent, self.silent_next = self.silent_next, False
        return self.spawn(argv, silent=silent)

    # the surface
    def _reap_locked(self): pass
    def _linux_host(self): return True
    def _running_locked(self): return True
    def _find_ffmpeg(self): return "ffmpeg"

    def _build_linux_ffmpeg_command(self, ffmpeg, capture_target, bitrate_kbps, max_bitrate_kbps):
        return self.argv(bitrate_kbps)

    @staticmethod
    def _kill_managed_process(p):
        if p is not None and p.poll() is None:
            p.terminate()

    def diagnostic_c3_validated_bitrate_transition(self, target):
        """Today's restart: kill, a new process (a random SSRC), the new level."""
        self.today_calls.append(target)
        validated = probe.LINUX_VALIDATED_ADAPTIVE_BITRATES_KBPS + (
            probe.REMOTE_LADDER.actuator_levels() if probe.REMOTE_LADDER is not None else ())
        if target not in validated or self._active_bitrate_kbps not in validated:
            raise RuntimeError("unsupported_validated_bitrate")
        self._kill_managed_process(self._process)
        self._process = self.spawn(self.argv(target))
        frm, self._active_bitrate_kbps = self._active_bitrate_kbps, target
        return {"ok": True, "mode": probe.BIDIRECTIONAL_MODE, "from_bitrate_kbps": frm,
                "target_bitrate_kbps": target, "video": {"encoder_restarted": True, "first_rtp_resume_ms": 200.0}}


class StreamCase(unittest.TestCase):
    def setUp(self):
        self.saved_remote = probe.REMOTE_LADDER
        FakeEncoder.instances = []
        self.onn = FakeOnn()
        self.relay = nfr.NativeVideoFecRelay(local_port=free_port(), pacing_us=0)
        self.relay.start(LOOP, self.onn.port)

    def tearDown(self):
        for e in FakeEncoder.instances:
            e.terminate()
        self.relay.stop()
        self.onn.close()
        probe.REMOTE_LADDER = self.saved_remote

    def step(self, m, target):
        return sip.run_in_place_transition(m, target, popen_factory=m.popen, probe=probe)

    def assert_one_stream(self, rtp):
        self.assertEqual(len({r[0] for r in rtp}), 1, "the onn saw an SSRC change")
        for a, b in zip(rtp, rtp[1:]):
            self.assertEqual((b[1] - a[1]) & 0xFFFF, 1, "a sequence gap or jump")
            self.assertIn((b[2] - a[2]) & 0xFFFFFFFF, (0, 1500), "a timestamp jump")

    @staticmethod
    def idrs(rtp):
        return sum(1 for r in rtp if r[3] == IDR)


class TheLanLadder(StreamCase):
    def test_two_steps_in_place_one_ssrc_one_idr_each(self):
        m = FakeManager(self.relay, 7000)
        old = m._process
        time.sleep(0.25)
        r1 = self.step(m, 6000)
        time.sleep(0.2)
        r2 = self.step(m, 5000)
        time.sleep(0.2)
        rtp = list(self.onn.rtp)
        self.assert_one_stream(rtp)
        self.assertEqual(rtp[0][0], old.ssrc)                       # the first encoder's identity, kept throughout
        self.assertEqual(self.idrs(rtp), 3)                         # the start's IDR + one per step
        for r, frm, to in ((r1, 7000, 6000), (r2, 6000, 5000)):
            self.assertEqual((r["mode"], r["from_bitrate_kbps"], r["target_bitrate_kbps"]), (sip.MODE, frm, to))
            v = r["video"]
            self.assertEqual((v["in_place"], v["ssrc_unchanged"], v["idr_frames"]), (True, True, 1))
            self.assertLess(v["splice_gap_ms"], sip.SPLICE_BOUND_S * 1000 + 50)
        self.assertEqual(m._active_bitrate_kbps, 5000)
        self.assertEqual(m.today_calls, [])                         # never today's restart
        procs = FakeEncoder.instances
        self.assertEqual([p.kbps for p in procs], ["7000k", "6000k", "5000k"])
        self.assertTrue(procs[0].terminated and procs[1].terminated and not procs[2].terminated)
        self.assertIs(m._process, procs[2])
        self.assertIn("-ssrc", procs[1].argv)
        self.assertLess(procs[1].argv.index("-ssrc"), procs[1].argv.index("rtp"))
        st = self.relay._b32_splice.status()
        self.assertEqual(st["splices"], 2)
        self.assertGreater(st["rewritten"], 0)
        self.assertIn("B32 in-place step", m._log_handle.getvalue())

    def test_a_later_full_restart_passes_through_as_today(self):
        m = FakeManager(self.relay, 7000)
        time.sleep(0.15)
        self.step(m, 6000)
        time.sleep(0.1)
        mark = len(self.onn.rtp)
        m._kill_managed_process(m._process)                         # recovery's restart: a random SSRC
        new = m.spawn(m.argv(6000))
        time.sleep(0.2)
        after = self.onn.rtp[mark:]
        self.assertEqual({r[0] for r in after[-10:]}, {new.ssrc})   # today's SSRC change
        sent = set(new.sent)
        self.assertTrue(all(r[5] in sent for r in after if r[0] == new.ssrc))   # byte for byte, not rewritten
        self.assertEqual(self.relay._b32_splice.status()["identity_resets"], 1)


class TheRemoteLadder(StreamCase):
    def test_4000_to_5000_in_place_on_a_remote_path(self):
        ladder = rl.RemoteLadder()
        ladder.note_stream_start(OVERLAY)
        self.assertEqual(ladder.actuator_levels(), (4000,))
        probe.REMOTE_LADDER = ladder
        m = FakeManager(self.relay, 4000)
        time.sleep(0.2)
        r = self.step(m, 5000)
        time.sleep(0.2)
        self.assert_one_stream(list(self.onn.rtp))
        self.assertEqual(self.idrs(self.onn.rtp), 2)
        self.assertEqual((r["video"]["in_place"], r["from_bitrate_kbps"], m._active_bitrate_kbps), (True, 4000, 5000))
        self.assertEqual(m.today_calls, [])

    def test_4000_without_the_remote_ladder_is_todays_refusal(self):
        probe.REMOTE_LADDER = None
        m = FakeManager(self.relay, 4000)
        with self.assertRaises(RuntimeError):
            self.step(m, 5000)
        self.assertEqual(m.today_calls, [5000])                     # today's path decided, as today
        self.assertEqual(len(FakeEncoder.instances), 1)             # no second encoder spawned


class TheFallback(StreamCase):
    def test_a_new_encoder_that_never_sends_falls_back_to_todays_restart(self):
        m = FakeManager(self.relay, 7000, silent_next=True)
        time.sleep(0.15)
        r = self.step(m, 6000)
        time.sleep(0.2)
        self.assertEqual(m.today_calls, [6000])
        self.assertEqual((r["video"]["in_place"], r["video"]["in_place_fallback"]),
                         (False, "replacement_rtp_did_not_splice"))
        silent = FakeEncoder.instances[1]
        self.assertTrue(silent.terminated)
        ssrcs = [r[0] for r in self.onn.rtp]
        self.assertEqual(len(set(ssrcs)), 2)                        # today's SSRC change
        self.assertEqual(ssrcs[-1], m._process.ssrc)


class TheSplice(unittest.TestCase):
    @staticmethod
    def pkt(ssrc, seq, ts, marker=False, nal=P):
        return (bytes([0x80, (0x80 if marker else 0) | 96]) + (seq & 0xFFFF).to_bytes(2, "big")
                + (ts & 0xFFFFFFFF).to_bytes(4, "big") + ssrc.to_bytes(4, "big") + bytes([nal, 1, 2]))

    def test_idle_is_pass_through_byte_for_byte(self):
        s = sip.RtpSplice()
        stream = [self.pkt(7, 65530 + i, 4294967000 + 1500 * (i // 3), marker=i % 3 == 2) for i in range(12)]
        self.assertEqual([p for x in stream for p in s.process(x)], stream)
        self.assertEqual(s.status()["rewritten"], 0)

    def test_the_splice_waits_for_the_old_frame_end_and_wraps(self):
        t = {"now": 0.0}
        s = sip.RtpSplice(clock=lambda: t["now"])
        out = s.process(self.pkt(1, 65535, 4294967000))           # old, mid-frame (no marker)
        s.arm(2)
        self.assertEqual(s.process(self.pkt(2, 100, 9, nal=IDR)), [])        # held: the old frame not ended
        out += s.process(self.pkt(1, 0, 4294967000, marker=True))            # the old frame ends -> the splice
        out += s.process(self.pkt(1, 1, 4294968500))                          # the old encoder: dropped
        out += s.process(self.pkt(2, 101, 9, marker=True))
        got = [(int.from_bytes(p[8:12], "big"), int.from_bytes(p[2:4], "big"), int.from_bytes(p[4:8], "big"), p[12])
               for p in out]
        self.assertEqual(got, [(1, 65535, 4294967000, P), (1, 0, 4294967000, P), (1, 1, (4294967000 + 1500) % 2**32, IDR),
                               (1, 2, (4294967000 + 1500) % 2**32, P)])
        self.assertEqual(s.status()["dropped_old"], 1)

    def test_the_bound_splices_without_the_old_frame_end(self):
        t = {"now": 0.0}
        s = sip.RtpSplice(clock=lambda: t["now"])
        s.process(self.pkt(1, 5, 50))
        s.arm(2)
        self.assertEqual(s.process(self.pkt(2, 9, 90, nal=IDR)), [])
        t["now"] = sip.SPLICE_BOUND_S + 0.001
        out = s.process(self.pkt(2, 10, 90))
        self.assertEqual([int.from_bytes(p[2:4], "big") for p in out], [6, 7])
        self.assertFalse(s.status()["last_splice"]["at_old_frame_end"])

    def test_the_ssrc_goes_before_the_rtp_output_in_the_real_argv(self):
        argv = stub.run_start(ns, b28.LAN)["argv"]
        out = sip._with_ssrc(argv, 1234)
        i = out.index("-ssrc")
        self.assertEqual(out[i:i + 4], ["-ssrc", "1234", "-f", "rtp"])
        self.assertEqual([x for j, x in enumerate(out) if j not in (i, i + 1)], argv)


class TheLadderRow(unittest.TestCase):
    KEYS_TODAY = ["schema", "mode", "acted", "event", "class", "from_kbps", "to_kbps", "injected", "decision_sequence", "actuation_ms",
                  "recovery_state_at_restart", "error", "level_kbps", "state", "effective_mode", "cycle",
                  "blackout_reports"]

    def row_for(self, result):
        tmp = tempfile.mkdtemp(prefix="b32h_")
        c = live.LiveController(Path(tmp), environ={})
        c.bind(actuator=lambda k: result, context=lambda: {}, serial_lock=None, recovery_state=lambda: "PLAYING")
        c._actuate({"to_kbps": 6000, "from_kbps": 7000, "class": "routine", "decision_sequence": 1})
        rows = [json.loads(x) for x in c.log_path.read_text().splitlines()]
        return [r for r in rows if r.get("event") == "transition_done"][-1]

    def test_todays_payload_gives_todays_row(self):
        r = self.row_for({"ok": True, "target_bitrate_kbps": 6000, "video": {"first_rtp_resume_ms": 210.0}})
        self.assertEqual([k for k in r if k not in ("at_utc", "clock_ms")], self.KEYS_TODAY)

    def test_an_in_place_step_says_so(self):
        r = self.row_for({"ok": True, "target_bitrate_kbps": 6000,
                          "video": {"first_rtp_resume_ms": 30.0, "in_place": True, "ssrc_unchanged": True,
                                    "splice_gap_ms": 12.5}})
        self.assertEqual((r["in_place"], r["ssrc_unchanged"], r["splice_gap_ms"], r["to_kbps"]), (True, True, 12.5, 6000))
        self.assertNotIn("in_place_fallback", r)


class TheFlag(unittest.TestCase):
    def fresh(self, value):
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        if value is not None:
            env[sip.FLAG_ENV] = value
        code = ("import sys; import native_stream as n; "
                "print(n.STEP_IN_PLACE is not None, 'step_in_place' in sys.modules)")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "companion", env=env, capture_output=True,
                             text=True, timeout=60)
        return out.stdout.split()

    def test_nothing_imported_without_the_line(self):
        for v in (None, "", "0", "yes", "true"):
            self.assertEqual(self.fresh(v), ["False", "False"], v)
        self.assertEqual(self.fresh("1"), ["True", "True"])

    def test_the_actuator_entry_absent_is_todays_and_present_is_the_step(self):
        calls = []
        fake = types.SimpleNamespace(_lock=threading.RLock(), _active_bitrate_kbps=7000, _linux_host=lambda: True,
                                     diagnostic_c3_validated_bitrate_transition=lambda k: calls.append(("today", k)) or {})
        saved = ns.STEP_IN_PLACE
        try:
            ns.STEP_IN_PLACE = None
            ns.NativeStreamManager.adaptive_level_transition(fake, 6000)
            ns.STEP_IN_PLACE = types.SimpleNamespace(run_in_place_transition=lambda m, k: calls.append(("step", k)) or {})
            ns.NativeStreamManager.adaptive_level_transition(fake, 5500)
        finally:
            ns.STEP_IN_PLACE = saved
        self.assertEqual(calls, [("today", 6000), ("step", 5500)])


class TheCapBesideTheUmbrella(b28.Base):
    def test_an_explicit_4000_holds_the_umbrellas_ladder_at_4000(self):
        live.REMOTE_CAP = rc.from_environ({ru.CAP: "4000"}, None)            # today's import-time object: inactive
        import_obj = live.REMOTE_CAP
        self.assertEqual(import_obj.reason, "remote_ladder_flag_absent")
        u = self.umbrella({ru.CAP: "4000"})
        self.assertTrue(u.cap.active)
        self.assertIs(u.cap.ladder, u.ladder)
        out, rows = self.session(u, OVERLAY, 160)
        self.assertEqual(b28.rate(out["argv"]), ("4000k", "4000k", "4000k"))
        self.assertIs(live.REMOTE_CAP, u.cap)
        self.assertFalse([r for r in rows if r.get("event") == "transition" and r.get("to_kbps", 0) > 4000])
        self.assertTrue([r for r in rows if r.get("source") == rc.SOURCE or r.get("reason") == rc.SOURCE])
        caps = [r for r in self.rows() if r.get("event") == "remote_cap_config"]
        self.assertEqual([(r["active"], r["cap_kbps"]) for r in caps], [(True, 4000)])
        line = self.rec.rows[-1]["lines"][ru.CAP]
        self.assertEqual(line, {"in_force": True, "how": "explicit 4000 on the umbrella's ladder"})
        out, rows = self.session(u, b28.LAN, 20)                            # a LAN session: today's
        self.assertEqual(b28.rate(out["argv"]), ("7000k", "7000k", "7000k"))
        self.assertIs(live.REMOTE_CAP, import_obj)
        self.assertEqual(self.rec.rows[-1]["lines"][ru.CAP]["in_force"], False)

    def test_without_the_explicit_line_b28s_7000(self):
        u = self.umbrella()
        self.assertFalse(u.cap_on_umbrella_ladder)
        self.assertEqual((u.cap.active, u.cap.cap_kbps), (True, 7000))


if __name__ == "__main__":
    unittest.main()
