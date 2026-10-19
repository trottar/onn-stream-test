#!/usr/bin/env python3
"""G4-W2: the Opus audio path (host side).

    python3 -m unittest discover -s tests/audio_codec -v

No stream, no companion, no socket: the sender runs on a real `NativeAudioStreamer`
(rooted in a temp directory) with a capturing socket and a pacer that returns at once;
the stream start runs the real `_start_linux_locked` on G8-S2's stub manager. This
process carries no flag; cases that need it load fresh module copies or set the hook's
global and restore it. Addresses are built from integers.
"""

from __future__ import annotations

import ast
import importlib.util
import ipaddress
import os
import struct
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "start_rung"))

import audio_codec as ac  # noqa: E402
import native_session_io as nsio  # noqa: E402
import native_stream as ns  # noqa: E402
import stub_manager as stub  # noqa: E402

LAN = str(ipaddress.ip_address(0xC0A80117))
OVERLAY = str(ipaddress.ip_network((0x64400000, 10))[77])
HEADER = struct.Struct("<4sBBHII")


class CaptureSocket:
    def __init__(self, log):
        self.log = log

    def setsockopt(self, *a):
        pass

    def setblocking(self, *a):
        pass

    def sendto(self, data, addr):
        self.log.append(bytes(data))

    def close(self):
        pass


def fake_socket(log):
    import socket as real
    return types.SimpleNamespace(socket=lambda *a, **k: CaptureSocket(log), AF_INET=real.AF_INET,
                                 SOCK_DGRAM=real.SOCK_DGRAM, SOL_SOCKET=real.SOL_SOCKET, SO_SNDBUF=real.SO_SNDBUF)


def run_loop(source: bytes, ticks: int, codec: ac.AudioCodec | None = None, declared: bool = True,
             tick_bytes: int = 960):
    """The real `_linux_sender_loop` for `ticks` ticks; the buffer fed `tick_bytes` per tick."""
    tmp = Path(tempfile.mkdtemp(prefix="g4_w2_test_"))
    st = nsio.NativeAudioStreamer(tmp)
    st._client_ip, st._client_port = LAN, 48101
    st.set_redundancy(copies=2, offset_packets=4)
    st._linux_prepare_sender_scheduler = lambda: True
    sent: list = []
    state = {"n": 0, "fed": 0}

    def wait_until(deadline_ns):
        if state["n"] >= ticks:
            return False
        state["n"] += 1
        chunk = source[state["fed"]: state["fed"] + tick_bytes]
        state["fed"] += len(chunk)
        with st._linux_buffer_condition:
            st._linux_buffer.extend(chunk)
        return True

    st._linux_wait_until = wait_until
    saved = (nsio.AUDIO_CODEC, nsio.socket, ac.socket)
    nsio.socket = fake_socket(sent)
    ac.socket = fake_socket(sent)
    if codec is not None:
        nsio.AUDIO_CODEC = codec
        if declared:
            codec.note_setup({"media_host": LAN, "audio_codecs": ["opus"]}, 200, {"ok": True})
        codec.prepare(st, LAN)
    try:
        st._linux_sender_loop()
    finally:
        nsio.AUDIO_CODEC, nsio.socket, ac.socket = saved
    return sent, st


def tone(seconds: float) -> bytes:
    import math
    n = int(48_000 * seconds)
    return b"".join(struct.pack("<hh", int(6000 * math.sin(2 * math.pi * 440 * i / 48_000)),
                                int(6000 * math.sin(2 * math.pi * 660 * i / 48_000))) for i in range(n))


class TestParse(unittest.TestCase):
    def test_defaults_and_parts(self):
        self.assertEqual(ac.parse("opus"), {"codec": "opus", "bitrate_kbps": 128, "frame_ms": 10})
        self.assertEqual(ac.parse(" OPUS ,bitrate=96, frame=20"), {"codec": "opus", "bitrate_kbps": 96, "frame_ms": 20})
        self.assertEqual(ac.parse("opus,frame=5")["frame_ms"], 5)

    def test_invalid(self):
        for raw in ("pcm", "", "opus,frame=40", "opus,frame=2.5", "opus,bitrate=47", "opus,bitrate=257",
                    "opus,bitrate=", "opus,bitrate=96,bitrate=96", "opus,rate=96", "opus;bitrate=96", "aac"):
            self.assertIn("invalid", ac.parse(raw), raw)

    def test_invalid_logged_once_and_inert(self):
        lines: list = []
        codec = ac.AudioCodec("opus,frame=40", log=lines.append)
        self.assertFalse(codec.active)
        st = types.SimpleNamespace()
        self.assertIsNone(codec.prepare(st, LAN))
        self.assertIsNone(codec.prepare(st, LAN))
        self.assertIsNone(ac.AudioCodec.session_for(st))
        self.assertEqual(len(lines), 1)
        self.assertIn("ignored", lines[0])

    def test_wire_numbers(self):
        self.assertEqual(ac.wire_numbers(128, 10), {"payload_bytes": 160, "datagrams_per_s": 200, "ip_bytes": 204,
                                                    "kbit_s": 326.4})
        self.assertAlmostEqual(ac.wire_numbers(128, 5)["kbit_s"], 396.8)
        self.assertAlmostEqual(ac.wire_numbers(128, 20)["kbit_s"], 291.2)
        self.assertEqual([ac.copy_offset_packets(4, f) for f in (5, 10, 20)], [4, 2, 1])


class TestLibopus(unittest.TestCase):
    def test_cbr_lookahead_roundtrip(self):
        enc = ac.OpusEncoder(128, 10)
        dec = ac.OpusDecoder()
        self.assertEqual(enc.lookahead_samples, 120)        # RESTRICTED_LOWDELAY: 2.5 ms
        pcm = tone(0.2)
        sizes = set()
        for i in range(20):
            p = enc.encode(pcm[i * 1920:(i + 1) * 1920])
            sizes.add(len(p))
            self.assertEqual(len(dec.decode(p, 480)), 1920)
        self.assertEqual(sizes, {160})                       # hard CBR
        self.assertEqual(len(dec.decode(None, 480)), 1920)   # concealment for a hole
        enc.close()
        dec.close()


class TestNegotiation(unittest.TestCase):
    def test_note_setup_records_only_ok_answers(self):
        codec = ac.AudioCodec("opus", log=lambda s: None)
        codec.note_setup({"media_host": LAN, "audio_codecs": ["opus"]}, 401, {"ok": False})
        self.assertEqual(codec.declared(LAN), ())
        codec.note_setup({"media_host": LAN, "audio_codecs": ["Opus", "pcm_s16le", 7]}, 200, {"ok": True})
        self.assertEqual(codec.declared(LAN), ("opus", "pcm_s16le"))
        codec.note_setup({"media_host": LAN}, 200, {"ok": True})          # a later setup without the field
        self.assertEqual(codec.declared(LAN), ())

    def test_overlay_host_only_with_sig_v2(self):
        codec = ac.AudioCodec("opus", log=lambda s: None)
        codec.note_setup({"media_host": LAN, "overlay_host": OVERLAY, "audio_codecs": ["opus"]}, 200, {"ok": True})
        self.assertEqual(codec.declared(OVERLAY), ())
        codec.note_setup({"media_host": LAN, "overlay_host": OVERLAY, "sig_v": 2, "audio_codecs": ["opus"]},
                         200, {"ok": True})
        self.assertEqual(codec.declared(OVERLAY), ("opus",))

    def test_install_wraps_the_instance_once(self):
        class Gate:
            def _setup(self, body, routing, refused):
                return (200, {"ok": True}) if body.get("good") else (401, {"ok": False})

        gate = Gate()
        codec = ac.AudioCodec("opus", log=lambda s: None)
        self.assertTrue(codec.install_setup_capture(gate))
        self.assertFalse(codec.install_setup_capture(gate))
        self.assertIs(Gate.__dict__["_setup"], Gate._setup)           # the class is not changed
        self.assertEqual(gate._setup({"good": True, "media_host": LAN, "audio_codecs": ["opus"]}, "lan", None),
                         (200, {"ok": True}))
        self.assertEqual(gate._setup({"media_host": OVERLAY, "audio_codecs": ["opus"]}, "lan", None),
                         (401, {"ok": False}))
        self.assertEqual(codec.declared(LAN), ("opus",))
        self.assertEqual(codec.declared(OVERLAY), ())

    def test_prepare(self):
        codec = ac.AudioCodec("opus,bitrate=96,frame=20", log=lambda s: None)
        st = types.SimpleNamespace()
        self.assertEqual(codec.prepare(st, LAN), ac.REFUSAL)
        self.assertIsNone(ac.AudioCodec.session_for(st))
        codec.note_setup({"media_host": LAN, "audio_codecs": ["opus"]}, 200, {"ok": True})
        self.assertIsNone(codec.prepare(st, LAN))
        sess = ac.AudioCodec.session_for(st)
        self.assertEqual((sess.bitrate_kbps, sess.frame_ms), (96, 20))
        self.assertEqual((codec.starts_opus, codec.starts_refused), (1, 1))


class TestStart(unittest.TestCase):
    def setUp(self):
        self.saved = ns.AUDIO_CODEC

    def tearDown(self):
        ns.AUDIO_CODEC = self.saved

    def test_absent_global_is_none(self):
        self.assertIsNone(ns.AUDIO_CODEC)
        self.assertIsNone(nsio.AUDIO_CODEC)

    def test_old_client_refused_before_anything(self):
        ns.AUDIO_CODEC = ac.AudioCodec("opus", log=lambda s: None)
        calls: list = []
        with self.assertRaises(ns.NativeStreamError) as cm:
            stub.run_start(ns, LAN, calls)
        self.assertIn("did not declare it in session/setup", str(cm.exception))
        self.assertEqual(calls, [])

    def test_declaring_client_starts_with_opus(self):
        codec = ac.AudioCodec("opus", log=lambda s: None)
        codec.note_setup({"media_host": LAN, "audio_codecs": ["opus"]}, 200, {"ok": True})
        ns.AUDIO_CODEC = codec
        out = stub.run_start(ns, LAN)
        self.assertIsNotNone(out["argv"])
        self.assertIsNotNone(ac.AudioCodec.session_for(out["manager"]._session_io.audio))

    def test_invalid_flag_starts_pcm(self):
        ns.AUDIO_CODEC = ac.AudioCodec("opus,frame=3", log=lambda s: None)
        out = stub.run_start(ns, LAN)
        self.assertIsNotNone(out["argv"])
        self.assertIsNone(ac.AudioCodec.session_for(out["manager"]._session_io.audio))


class TestSender(unittest.TestCase):
    def test_pcm_unchanged_when_session_not_opus(self):
        src = tone(0.5)
        a, _ = run_loop(src, 60)
        b, _ = run_loop(src, 60, codec=ac.AudioCodec("opus,frame=3", log=lambda s: None))   # invalid -> PCM
        self.assertEqual(a, b)
        self.assertEqual(HEADER.unpack(a[0][:16])[1], 1)
        self.assertEqual({len(x) for x in a}, {976})

    def test_opus_datagrams(self):
        src = tone(1.0)
        sent, st = run_loop(src, 30, codec=ac.AudioCodec("opus", log=lambda s: None), tick_bytes=1920)
        heads = [HEADER.unpack(x[:16]) for x in sent]
        self.assertTrue(all(h[0] == b"PHA1" and h[1] == 2 and h[2] == 2 and h[5] == 480 for h in heads))
        self.assertEqual({len(x) for x in sent}, {176})
        # originals 0..29, each followed (from tick 2 on) by the copy of n - 2
        seqs = [h[3] for h in heads]
        self.assertEqual(seqs[:5], [0, 1, 2, 0, 3])
        self.assertEqual(st._linux_packets_sent, 30)
        self.assertEqual(st._linux_duplicates_sent, 28)
        self.assertEqual([h[4] for h in heads if h[3] in (0, 1, 2)][:3], [0, 480, 960])
        self.assertEqual(st._linux_sender_underflows, 0)

    def test_opus_underflow_sends_encoded_silence(self):
        sent, st = run_loop(b"", 10, codec=ac.AudioCodec("opus", log=lambda s: None), tick_bytes=0)
        self.assertEqual(st._linux_sender_underflows, 10)
        self.assertEqual(st._linux_packets_sent, 10)

    def test_undeclared_client_never_reaches_the_opus_loop(self):
        src = tone(0.5)
        a, _ = run_loop(src, 40)
        b, _ = run_loop(src, 40, codec=ac.AudioCodec("opus", log=lambda s: None), declared=False)
        self.assertEqual(a, b)


class TestGuardedImports(unittest.TestCase):
    def _guarded(self, rel):
        tree = ast.parse((ROOT / rel).read_text())
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                src = ast.unparse(node.test)
                for sub in node.body:
                    if isinstance(sub, ast.Import) and any(a.name == "audio_codec" for a in sub.names):
                        found.append(src)
        top = [n for n in tree.body if isinstance(n, ast.Import) and any(a.name == "audio_codec" for a in n.names)]
        return found, top

    def test_imports_only_under_the_flag(self):
        for rel in ("companion/native_stream.py", "companion/native_session_io.py", "companion/privyhub_service.py"):
            found, top = self._guarded(rel)
            self.assertEqual(top, [], rel)
            self.assertEqual(len(found), 1, rel)
            self.assertIn("PRIVYHUB_AUDIO_CODEC", found[0], rel)

    def test_child_interpreter_shares_one_instance(self):
        code = ("import sys; sys.path.insert(0, 'companion'); import native_stream as ns, native_session_io as io, "
                "audio_codec as ac; print(ns.AUDIO_CODEC is io.AUDIO_CODEC is ac._SHARED, "
                "ns.AUDIO_CODEC.config['frame_ms'])")
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
        env["PRIVYHUB_AUDIO_CODEC"] = "opus,frame=20"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        out = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "True 20", out.stderr)
        env.pop("PRIVYHUB_AUDIO_CODEC")
        code2 = ("import sys; sys.path.insert(0, 'companion'); import native_stream as ns, native_session_io as io; "
                 "print(ns.AUDIO_CODEC, io.AUDIO_CODEC, 'audio_codec' in sys.modules)")
        out = subprocess.run([sys.executable, "-c", code2], cwd=str(ROOT), env=env, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "None None False", out.stderr)


if __name__ == "__main__":
    unittest.main()
