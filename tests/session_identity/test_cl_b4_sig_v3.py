#!/usr/bin/env python3
"""CL-B4: `sig_v` 3 — v2's fields plus the declared audio codecs, signed.

    python3 -m unittest discover -s tests/session_identity -v

- v3 accepted; `token_issued` carries `sig_v` 3 and `audio_codecs`;
- a v3 claim without the field (or with a malformed one) refused, a tampered list refused;
- v1 / v2 byte for byte as HEAD's module (`fixtures/session_identity_predecessor_cl_b4.py.txt`):
  the same scenarios on both, statuses, payloads and audit rows equal (tokens made deterministic);
- the vector the APK's JVM test checks (`SessionProtocolV3Test.kt`).
"""

from __future__ import annotations

import hashlib
import hmac
import importlib.machinery
import importlib.util
import itertools
import json
import sys
import tempfile
import unittest
from pathlib import Path

from common import (
    KEY_HEX, LAN_DECLARED, LAN_NET, LAN_SRC, LOCAL_SRC, OVERLAY_DECLARED, OVERLAY_SRC, Clock,
    audit_lines, make_gate, pair, setup, si,
)
from test_g3s3 import setup_v2, sign_v2

FIX = Path(__file__).resolve().parent / "fixtures"


def sign_v3(device_id, nonce, media_host, video_port, audio_port, overlay_host, codecs, key_hex=KEY_HEX):
    canon = "\n".join([si.SETUP_CANON_V3, device_id, nonce, media_host, str(video_port),
                       "" if audio_port is None else str(audio_port), overlay_host or "", ",".join(codecs)])
    return hmac.new(bytes.fromhex(key_hex), canon.encode(), hashlib.sha256).hexdigest()


def setup_v3(gate, device_id, source=LAN_SRC, media_host=LAN_DECLARED, video_port=48100, audio_port=48101,
             overlay_host=None, codecs=("opus",), tamper=None, drop=()):
    _, n = gate.session_route("POST", "/session/nonce", {}, None, source)
    body = {"device_id": device_id, "nonce": n["nonce"], "media_host": media_host,
            "video_port": video_port, "audio_port": audio_port, "audio_codecs": list(codecs), "sig_v": 3,
            "sig": sign_v3(device_id, n["nonce"], media_host, video_port, audio_port, overlay_host, codecs)}
    if overlay_host is not None:
        body["overlay_host"] = overlay_host
    if tamper:
        body.update(tamper)
    for k in drop:
        body.pop(k, None)
    return gate.session_route("POST", "/session/setup", body, None, source)


def issued(gate):
    return [a for a in audit_lines(gate) if a["event"] == "token_issued"][-1]


class SetupV3(unittest.TestCase):
    def test_v3_accepted_and_audited(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v3(g, dev)
        self.assertEqual(st, 200, p)
        self.assertTrue(p["token"] and p["media_token"])
        row = issued(g)
        self.assertEqual((row["sig_v"], row["audio_codecs"], row["media_token_issued"]), (3, "opus", True))
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=48100", p["token"], LAN_SRC)
        self.assertEqual((d.allowed, d.media_host), (True, LAN_DECLARED))

    def test_v3_without_the_field_refused(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v3(g, dev, drop=("audio_codecs",))
        self.assertEqual((st, p["reason"]), (403, "audio-codecs-invalid"))
        for bad in ([], [""], ["OPUS"], [7], "opus", ["opus"] * 9, ["a" * 17], [None], {"opus": 1}):
            st, p = setup_v3(g, dev, tamper={"audio_codecs": bad})
            self.assertEqual((st, p["reason"]), (403, "audio-codecs-invalid"), bad)
        self.assertFalse([a for a in audit_lines(g) if a["event"] == "token_issued"])

    def test_v3_tampered_fields_refused(self):
        g = make_gate()
        dev = pair(g)
        for tamper in ({"audio_codecs": ["opus", "pcm"]}, {"audio_codecs": ["pcm"]}, {"audio_port": 48999},
                       {"video_port": 48102}):
            st, p = setup_v3(g, dev, tamper=tamper)
            self.assertEqual((st, p["reason"]), (401, "bad-signature"), tamper)

    def test_signatures_do_not_cross_versions(self):
        g = make_gate()
        dev = pair(g)
        # a v2 signature presented as v3
        _, n = g.session_route("POST", "/session/nonce", {}, None, LAN_SRC)
        body = {"device_id": dev, "nonce": n["nonce"], "media_host": LAN_DECLARED, "video_port": 48100,
                "audio_port": 48101, "audio_codecs": ["opus"], "sig_v": 3,
                "sig": sign_v2(dev, n["nonce"], LAN_DECLARED, 48100, 48101, None)}
        self.assertEqual(g.session_route("POST", "/session/setup", body, None, LAN_SRC)[1]["reason"], "bad-signature")
        # a v3 signature presented as v2
        _, n = g.session_route("POST", "/session/nonce", {}, None, LAN_SRC)
        body = {"device_id": dev, "nonce": n["nonce"], "media_host": LAN_DECLARED, "video_port": 48100,
                "audio_port": 48101, "audio_codecs": ["opus"], "sig_v": 2,
                "sig": sign_v3(dev, n["nonce"], LAN_DECLARED, 48100, 48101, None, ["opus"])}
        self.assertEqual(g.session_route("POST", "/session/setup", body, None, LAN_SRC)[1]["reason"], "bad-signature")
        # sig_v true is not 3 (bool excluded, as for 2): verified as v1, so a v3 signature fails
        st, p = setup_v3(g, dev, tamper={"sig_v": True})
        self.assertEqual((st, p["reason"]), (401, "bad-signature"))

    def test_v2_with_an_unsigned_field_is_v2_as_today(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v2(g, dev, tamper={"audio_codecs": ["opus"]})
        self.assertEqual(st, 200, p)
        row = issued(g)
        self.assertEqual(row["sig_v"], 2)
        self.assertNotIn("audio_codecs", row)

    def test_v3_over_the_overlay(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v3(g, dev, source=OVERLAY_SRC, media_host=LAN_DECLARED, overlay_host=OVERLAY_DECLARED)
        self.assertEqual(st, 200, p)
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=48100", p["token"], OVERLAY_SRC)
        self.assertEqual((d.allowed, d.media_host), (True, OVERLAY_DECLARED))
        self.assertEqual((issued(g)["overlay_declared"], issued(g)["sig_v"]), (True, 3))

    def test_the_client_vector(self):
        # The APK's SessionProtocolV3Test checks the same inputs and digest.
        key = "11" * 32
        canon = "\n".join([si.SETUP_CANON_V3, "dev-fixture", "nonce-fixture", "media-host", "48100", "48101", "", "opus"])
        self.assertEqual(canon, "privyhub-session-setup-v3\ndev-fixture\nnonce-fixture\nmedia-host\n48100\n48101\n\nopus")
        digest = hmac.new(bytes.fromhex(key), canon.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(digest, VECTOR_V3)


VECTOR_V3 = hmac.new(bytes.fromhex("11" * 32),
                     b"privyhub-session-setup-v3\ndev-fixture\nnonce-fixture\nmedia-host\n48100\n48101\n\nopus",
                     hashlib.sha256).hexdigest()


# ---- v1 / v2 byte for byte against HEAD's module ------------------------------------------------

def load_predecessor():
    loader = importlib.machinery.SourceFileLoader("session_identity_head",
                                                  str(FIX / "session_identity_predecessor_cl_b4.py.txt"))
    spec = importlib.util.spec_from_loader("session_identity_head", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["session_identity_head"] = mod
    loader.exec_module(mod)
    return mod


class _Det:
    """Deterministic `secrets` for both modules: the same call order gives the same values."""

    def __init__(self):
        self.n = itertools.count(1)

    def token_urlsafe(self, nbytes=None):
        return "tok%06d" % next(self.n)

    def token_hex(self, nbytes=None):
        return "%032x" % next(self.n)

    def randbelow(self, k):
        return next(self.n) % k

    def choice(self, seq):
        return seq[next(self.n) % len(seq)]


def scenarios(mod):
    """Run v1 / v2 scenarios on a gate built from `mod`; return every answer and the audit rows."""
    det = _Det()
    real = mod.secrets
    mod.secrets = det
    try:
        d = Path(tempfile.mkdtemp(prefix="cl_b4_cmp_"))
        clock = Clock()
        gate = mod.SessionGate(mode="v2", config_dir=d / "config", audit_path=d / "audit.jsonl",
                               classifier=mod.RoutingClassifier(lan_reader=lambda: [LAN_NET], clock=clock),
                               clock=clock, wall=lambda: 1_792_000_000.0)
        out = []

        def route(path, body, source):
            st, p = gate.session_route("POST", path, body, None, source)
            out.append((path, st, json.dumps(p, sort_keys=True)))
            return st, p

        _, opened = route("/session/pairing/open", {}, LOCAL_SRC)
        _, paired = route("/session/pair", {"code": opened["code"], "device_name": "onn-fixture", "key": KEY_HEX},
                          LAN_SRC)
        dev = paired["device_id"]

        def v1(tamper=None, source=LAN_SRC, media_host=LAN_DECLARED, port=48100):
            _, n = route("/session/nonce", {}, source)
            canon = "\n".join([mod.SETUP_CANON, dev, n["nonce"], media_host, str(port)])
            body = {"device_id": dev, "nonce": n["nonce"], "media_host": media_host, "video_port": port,
                    "sig": hmac.new(bytes.fromhex(KEY_HEX), canon.encode(), hashlib.sha256).hexdigest()}
            body.update(tamper or {})
            return route("/session/setup", body, source)

        def v2(tamper=None, source=LAN_SRC, media_host=LAN_DECLARED, overlay=None, audio=48101):
            _, n = route("/session/nonce", {}, source)
            body = {"device_id": dev, "nonce": n["nonce"], "media_host": media_host, "video_port": 48100,
                    "audio_port": audio, "sig_v": 2,
                    "sig": sign_v2(dev, n["nonce"], media_host, 48100, audio, overlay)}
            if overlay:
                body["overlay_host"] = overlay
            body.update(tamper or {})
            return route("/session/setup", body, source)

        v1()
        v1({"video_port": 48102})
        v1(port=80)
        v1({"sig_v": "3"})
        v1({"sig_v": 4})
        v1({"sig_v": True})
        v1({"audio_codecs": ["opus"]})
        st, p = v2()
        v2({"audio_codecs": ["opus"]})
        v2({"audio_codecs": "junk"})
        v2({"audio_port": 48999})
        v2(audio=80)
        v2(source=OVERLAY_SRC, overlay=OVERLAY_DECLARED)
        v2(source=OVERLAY_SRC)
        v2(overlay=LAN_DECLARED)
        v2({"device_id": "nosuch"})
        v2({"nonce": "nosuch"})
        dec = gate.authorize("POST", "/plugins/games/native-stream-start", "port=48100", p["token"], LAN_SRC)
        out.append(("authorize", dec.allowed, dec.status, dec.reason, dec.media_host))
        audit = (d / "audit.jsonl").read_text()
        return out, audit
    finally:
        mod.secrets = real


class V2ByteForByte(unittest.TestCase):
    def test_v1_v2_identical_to_head(self):
        head = load_predecessor()
        self.assertFalse(hasattr(head, "SETUP_CANON_V3"))
        a_out, a_audit = scenarios(head)
        b_out, b_audit = scenarios(si)
        self.assertEqual(len(a_out), len(b_out))
        for x, y in zip(a_out, b_out):
            self.assertEqual(x, y)
        self.assertEqual(a_audit, b_audit)
        self.assertGreater(a_audit.count("token_issued"), 3)
        out = __import__("os").environ.get("CL_B4_COMPARE_OUT")
        if out:
            Path(out).write_text(json.dumps({
                "answers": len(a_out), "answers_equal": a_out == b_out,
                "audit_rows": a_audit.count("\n"), "audit_equal": a_audit == b_audit,
                "statuses": [r[1] for r in a_out],
                "audit_sha256_head": hashlib.sha256(a_audit.encode()).hexdigest(),
                "audit_sha256_edited": hashlib.sha256(b_audit.encode()).hexdigest()}, indent=1) + "\n")


if __name__ == "__main__":
    unittest.main()
