#!/usr/bin/env python3
"""G3-S3: hardening — every new accept / refuse case.

    python3 -m unittest discover -s tests/session_identity -v

The setup canon v2 (the audio port and the overlay address signed), the
declared-port binding, `diagnostics` as a grantable permission, TV / EPG
with a token, the media token, the companion's `/session/media-check`, the
range server's `MediaGate`, and the status document. Addresses are built
from integers in memory, as in G3-S1's tests; no token value is written.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import unittest

from common import (
    ALL_ADDRESSES, KEY_HEX, LAN_DECLARED, LAN_SRC, LOCAL_SRC, OVERLAY_DECLARED, OVERLAY_SRC,
    UNKNOWN_SRC, Clock, audit_lines, make_gate, pair, setup, si,
)


def sign_v2(device_id, nonce, media_host, video_port, audio_port, overlay_host, key_hex=KEY_HEX):
    canon = "\n".join([si.SETUP_CANON_V2, device_id, nonce, media_host, str(video_port),
                       "" if audio_port is None else str(audio_port), overlay_host or ""])
    return hmac.new(bytes.fromhex(key_hex), canon.encode(), hashlib.sha256).hexdigest()


def setup_v2(gate, device_id, source=LAN_SRC, media_host=LAN_DECLARED, video_port=48100,
             audio_port=48101, overlay_host=None, tamper=None):
    _, n = gate.session_route("POST", "/session/nonce", {}, None, source)
    body = {"device_id": device_id, "nonce": n["nonce"], "media_host": media_host,
            "video_port": video_port, "audio_port": audio_port, "sig_v": 2,
            "sig": sign_v2(device_id, n["nonce"], media_host, video_port, audio_port, overlay_host)}
    if overlay_host is not None:
        body["overlay_host"] = overlay_host
    if tamper:
        body.update(tamper)
    return gate.session_route("POST", "/session/setup", body, None, source)


def reasons(gate):
    return [line.get("reason") for line in audit_lines(gate) if line.get("reason")]


def media_check(gate, routing, path="/vod/fixture.mp4", source=LOCAL_SRC, **creds):
    return gate.session_route("POST", si.MEDIA_CHECK_PATH, {"routing": routing, "path": path, **creds},
                              None, source)


class SetupV2(unittest.TestCase):
    def test_v2_accepted_with_media_token(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v2(g, dev)
        self.assertEqual(st, 200, p)
        self.assertTrue(p["media_token"])
        self.assertNotEqual(p["media_token"], p["token"])
        issued = [a for a in audit_lines(g) if a["event"] == "token_issued"][-1]
        self.assertEqual((issued["sig_v"], issued["media_token_issued"]), (2, True))

    def test_v1_still_accepted(self):
        g = make_gate()
        dev = pair(g)
        (st, p), _ = setup(g, dev)
        self.assertEqual(st, 200)
        self.assertIn("media_token", p)
        issued = [a for a in audit_lines(g) if a["event"] == "token_issued"][-1]
        self.assertEqual(issued["sig_v"], 1)

    def test_signed_audio_port_and_overlay_host(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v2(g, dev, tamper={"audio_port": 48999})
        self.assertEqual((st, p["reason"]), (401, "bad-signature"))
        st, p = setup_v2(g, dev, overlay_host=OVERLAY_DECLARED, tamper={"overlay_host": str(si.OVERLAY_NETWORKS[0][7])})
        self.assertEqual((st, p["reason"]), (401, "bad-signature"))
        # a v1 signature presented as v2 fails too
        _, n = g.session_route("POST", "/session/nonce", {}, None, LAN_SRC)
        from common import sign
        body = {"device_id": dev, "nonce": n["nonce"], "media_host": LAN_DECLARED, "video_port": 48100,
                "sig_v": 2, "sig": sign(dev, n["nonce"], LAN_DECLARED, 48100)}
        st, p = g.session_route("POST", "/session/setup", body, None, LAN_SRC)
        self.assertEqual((st, p["reason"]), (401, "bad-signature"))

    def test_invalid_audio_port_or_overlay_host(self):
        g = make_gate()
        dev = pair(g)
        self.assertEqual(setup_v2(g, dev, audio_port=80)[1]["reason"], "endpoint-invalid")
        self.assertEqual(setup_v2(g, dev, overlay_host=LAN_DECLARED)[1]["reason"], "endpoint-invalid")
        self.assertEqual(setup_v2(g, dev, overlay_host="not-an-address")[1]["reason"], "endpoint-invalid")

    def test_overlay_source_streams_to_the_overlay_address(self):
        g = make_gate()
        dev = pair(g)
        # off-site: the route-local address is a LAN-class one (the remote
        # network), the overlay interface address is declared beside it.
        st, p = setup_v2(g, dev, source=OVERLAY_SRC, media_host=LAN_DECLARED, overlay_host=OVERLAY_DECLARED)
        self.assertEqual(st, 200, p)
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=48100", p["token"], OVERLAY_SRC)
        self.assertEqual((d.allowed, d.media_host), (True, OVERLAY_DECLARED))
        # at home the same declaration streams to the LAN address
        st, p = setup_v2(g, dev, source=LAN_SRC, media_host=LAN_DECLARED, overlay_host=OVERLAY_DECLARED)
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=48100", p["token"], LAN_SRC)
        self.assertEqual((d.allowed, d.media_host), (True, LAN_DECLARED))

    def test_overlay_source_without_an_overlay_address_still_mismatches(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v2(g, dev, source=OVERLAY_SRC, media_host=LAN_DECLARED)
        self.assertEqual((st, p["reason"]), (403, "endpoint-class-mismatch"))


class PortBinding(unittest.TestCase):
    def _token(self, v2=True):
        g = make_gate()
        dev = pair(g)
        if v2:
            st, p = setup_v2(g, dev)
        else:
            (st, p), _ = setup(g, dev, port=48100)
        self.assertEqual(st, 200)
        return g, p["token"]

    def test_bound(self):
        g, tok = self._token()
        for q in ("port=48100", "port=48100&audio_port=48101"):
            self.assertTrue(g.authorize("POST", "/plugins/games/native-stream-start", q, tok, LAN_SRC).allowed, q)

    def test_mismatch_refused_and_audited(self):
        g, tok = self._token()
        cases = [("port=48102", "video"), ("", "video"), ("port=", "video"), ("port=48100&port=48100", "video"),
                 ("port=48100&audio_port=48105", "audio"), ("port=48100&audio_port=", "audio"),
                 ("port=48100&controller_port=48103", "controller")]
        for q, kind in cases:
            d = g.authorize("POST", "/plugins/games/native-stream-start", q, tok, LAN_SRC)
            self.assertEqual((d.allowed, d.status, d.reason), (False, 403, "endpoint-port-mismatch"), q)
            last = audit_lines(g)[-1]
            self.assertEqual((last["reason"], last["port_kind"]), ("endpoint-port-mismatch", kind), q)

    def test_v1_session_naming_an_audio_port_is_refused(self):
        g, tok = self._token(v2=False)
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=48100&audio_port=48101", tok, LAN_SRC)
        self.assertEqual(d.reason, "endpoint-port-mismatch")

    def test_legacy_lan_unchanged(self):
        g = make_gate()
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=40000", None, LAN_SRC)
        self.assertTrue(d.allowed)
        self.assertEqual(d.kind, "legacy")


class Diagnostics(unittest.TestCase):
    def _store(self, g, edit):
        path = g.devices._file.path
        doc = json.loads(path.read_text())
        edit(doc["devices"][0])
        path.write_text(json.dumps(doc))

    def test_default_on_for_a_new_pairing(self):
        g = make_gate()
        dev = pair(g)
        (st, p), _ = setup(g, dev)
        self.assertIn("diagnostics", p["permissions"])
        for path in ("/status", "/diagnostics/health", "/diagnostics/stream-telemetry"):
            self.assertTrue(g.authorize("GET", path, "", p["token"], OVERLAY_SRC).allowed, path)

    def test_record_paired_before_g3_s3_is_granted_diagnostics(self):
        g = make_gate()
        dev = pair(g)
        self._store(g, lambda d: (d.pop("permissions_v"), d.update(permissions=["games", "tv", "vod"])))
        (st, p), _ = setup(g, dev)
        self.assertEqual(p["permissions"], ["games", "tv", "vod", "diagnostics"])
        self.assertTrue(g.authorize("GET", "/status", "", p["token"], LAN_SRC).allowed)

    def test_revoked_at_next_use(self):
        g = make_gate()
        dev = pair(g)
        (st, p), _ = setup(g, dev)
        self.assertTrue(g.authorize("GET", "/diagnostics/health", "", p["token"], LAN_SRC).allowed)
        self._store(g, lambda d: d.update(permissions=["games", "tv", "vod"]))
        d = g.authorize("GET", "/diagnostics/health", "", p["token"], LAN_SRC)
        self.assertEqual((d.allowed, d.status, d.reason), (False, 403, "permission-denied"))
        self.assertEqual(audit_lines(g)[-1]["permission"], "diagnostics")

    def test_client_health_stays_games(self):
        self.assertEqual(si.required_permission("/diagnostics/client-health"), "games")

    def test_overlay_without_token_refused(self):
        g = make_gate()
        for path in ("/status", "/diagnostics/health"):
            d = g.authorize("GET", path, "", None, OVERLAY_SRC)
            self.assertEqual((d.allowed, d.reason), (False, "legacy-overlay"))
        self.assertTrue(g.authorize("GET", "/status", "", None, LAN_SRC).allowed)   # LAN legacy: today


class TvAndEpg(unittest.TestCase):
    PATHS = ("/plugins/tv_state/state", "/plugins/epg/guide", "/plugins/epg/prefetch", "/plugins/iptv_org/channels")

    def test_token_allowed_over_the_overlay(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v2(g, dev, source=OVERLAY_SRC, media_host=OVERLAY_DECLARED)
        for path in self.PATHS:
            self.assertTrue(g.authorize("GET", path, "", p["token"], OVERLAY_SRC).allowed, path)

    def test_no_token_over_the_overlay_refused_lan_legacy(self):
        g = make_gate()
        for path in self.PATHS:
            self.assertEqual(g.authorize("GET", path, "", None, OVERLAY_SRC).reason, "legacy-overlay")
            self.assertEqual(g.authorize("GET", path, "", None, UNKNOWN_SRC).reason, "legacy-unknown-network")
            self.assertTrue(g.authorize("GET", path, "", None, LAN_SRC).allowed)

    def test_tv_revoked(self):
        g = make_gate()
        dev = pair(g)
        path = g.devices._file.path
        doc = json.loads(path.read_text())
        doc["devices"][0]["permissions"] = ["games", "vod", "diagnostics"]
        path.write_text(json.dumps(doc))
        (st, p), _ = setup(g, dev)
        d = g.authorize("POST", "/plugins/tv_state/state", "", p["token"], LAN_SRC)
        self.assertEqual((d.allowed, d.reason), (False, "permission-denied"))


class MediaCheck(unittest.TestCase):
    def _session(self, source=OVERLAY_SRC, host=OVERLAY_DECLARED):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v2(g, dev, source=source, media_host=host)
        self.assertEqual(st, 200, p)
        return g, dev, p

    def test_host_local_only(self):
        g, _, p = self._session()
        for src in (LAN_SRC, OVERLAY_SRC):
            st, body = media_check(g, "overlay", source=src, token=p["token"])
            self.assertEqual((st, body["reason"]), (403, "host-local-only"))

    def test_header_token_over_the_overlay(self):
        g, dev, p = self._session()
        for _ in range(3):
            st, body = media_check(g, "overlay", token=p["token"])
            self.assertEqual((st, body["kind"], body["client_id"]), (200, "session", dev))
        seen = [a for a in audit_lines(g) if a["event"] == "media_session"]
        self.assertEqual(len(seen), 1)            # audited once per token, not per range request
        self.assertEqual((seen[0]["media_token_used"], seen[0]["routing_evidence"]), (False, "overlay"))

    def test_media_token_over_the_overlay(self):
        g, dev, p = self._session()
        st, body = media_check(g, "overlay", media_token=p["media_token"])
        self.assertEqual((st, body["client_id"]), (200, dev))
        seen = [a for a in audit_lines(g) if a["event"] == "media_session"]
        self.assertEqual(seen[-1]["media_token_used"], True)

    def test_media_token_refusals(self):
        g, dev, p = self._session()
        self.assertEqual(media_check(g, "overlay", media_token="forged")[1]["reason"], "media-token-unknown")
        # the session token is not a media token, and vice versa
        self.assertEqual(media_check(g, "overlay", media_token=p["token"])[1]["reason"], "media-token-unknown")
        self.assertEqual(media_check(g, "overlay", token=p["media_token"])[1]["reason"], "token-unknown")
        # ends with the session
        g.session_route("POST", "/session/end", {}, p["token"], OVERLAY_SRC)
        self.assertEqual(media_check(g, "overlay", media_token=p["media_token"])[1]["reason"], "media-token-unknown")

    def test_media_token_expires_with_the_session(self):
        clock = Clock()
        g = make_gate(clock=clock)
        dev = pair(g)
        st, p = setup_v2(g, dev, source=OVERLAY_SRC, media_host=OVERLAY_DECLARED)
        clock.t += si.TOKEN_TTL_S + 1
        self.assertEqual(media_check(g, "overlay", media_token=p["media_token"])[1]["reason"], "token-expired")
        self.assertEqual(media_check(g, "overlay", media_token=p["media_token"])[1]["reason"], "media-token-unknown")

    def test_bound_to_the_device(self):
        g, dev, p = self._session()
        path = g.devices._file.path
        path.write_text(json.dumps({"version": 1, "devices": []}))
        self.assertEqual(media_check(g, "overlay", media_token=p["media_token"])[1]["reason"], "device-revoked")

    def test_vod_permission(self):
        g = make_gate()
        dev = pair(g)
        path = g.devices._file.path
        doc = json.loads(path.read_text())
        doc["devices"][0]["permissions"] = ["games", "tv", "diagnostics"]
        path.write_text(json.dumps(doc))
        st, p = setup_v2(g, dev, source=OVERLAY_SRC, media_host=OVERLAY_DECLARED)
        st, body = media_check(g, "overlay", media_token=p["media_token"])
        self.assertEqual((st, body["reason"]), (403, "permission-denied"))
        self.assertEqual(audit_lines(g)[-1]["permission"], "vod")

    def test_no_credentials(self):
        g = make_gate()
        self.assertEqual(media_check(g, "overlay")[1]["reason"], "legacy-overlay")
        self.assertEqual(media_check(g, "unknown")[1]["reason"], "legacy-unknown-network")
        self.assertEqual(media_check(g, "bogus")[1]["reason"], "legacy-unknown-network")
        self.assertEqual(media_check(g, "lan")[0], 200)
        g.settings._file.path.parent.mkdir(parents=True, exist_ok=True)
        g.settings._file.path.write_text(json.dumps({"legacy_unpaired_lan": False}))
        self.assertEqual(media_check(g, "lan")[1]["reason"], "legacy-disabled")

    def test_legacy_token_never_over_the_overlay(self):
        g = make_gate()
        d = g.authorize("POST", "/plugins/games/launch", "id=x", None, LAN_SRC)
        self.assertEqual(media_check(g, "lan", token=d.issued_token)[0], 200)
        self.assertEqual(media_check(g, "overlay", token=d.issued_token)[1]["reason"], "legacy-overlay")

    def test_unknown_flag_value(self):
        g = make_gate(mode="v3")
        self.assertEqual(media_check(g, "overlay", token="x")[1]["reason"], "identity-flag-unknown")

    def test_path_audited_without_query(self):
        g, _, p = self._session()
        media_check(g, "overlay", path="/vod/a.mp4?media_token=" + p["media_token"], media_token="forged")
        self.assertEqual(audit_lines(g)[-1]["path"], "/vod/a.mp4")


class StatusDocument(unittest.TestCase):
    def test_permissions_and_media_token_boolean(self):
        g, = (make_gate(),)
        dev = pair(g)
        st, p = setup_v2(g, dev)
        g.authorize("POST", "/plugins/games/launch", "id=x", None, LAN_SRC)   # one legacy token too
        st, doc = g.session_route("GET", "/session/status", None, None, LOCAL_SRC)
        self.assertEqual(st, 200)
        self.assertEqual(doc["permissions_known"], list(si.PERMISSIONS))
        self.assertIn("diagnostics", doc["default_paired_permissions"])
        mine = [s for s in doc["sessions"] if s["client_id"] == dev][0]
        self.assertEqual((mine["kind"], mine["media_token_live"]), ("session", True))
        self.assertEqual(mine["permissions"], ["games", "tv", "vod", "diagnostics"])
        legacy = [s for s in doc["sessions"] if s["kind"] == "legacy"][0]
        self.assertFalse(legacy["media_token_live"])
        text = json.dumps(doc)
        self.assertNotIn(p["token"], text)
        self.assertNotIn(p["media_token"], text)


class RangeGate(unittest.TestCase):
    """`MediaGate` with its transport wired to a gate in process (no socket)."""

    def _gates(self, raising=False):
        g = make_gate()
        calls = []

        def transport(url, body):
            calls.append(json.loads(body))
            if raising:
                raise OSError("companion down")
            st, payload = g.session_route("POST", si.MEDIA_CHECK_PATH, json.loads(body), None, LOCAL_SRC)
            return st, json.dumps(payload).encode()

        m = si.MediaGate("v2", g.devices._file.path.parent, g.audit.path, classifier=g.classifier,
                         transport=transport)
        return g, m, calls

    def test_check_url_is_loopback(self):
        _, m, _ = self._gates()
        self.assertTrue(m.check_url.endswith(":8765" + si.MEDIA_CHECK_PATH))
        self.assertEqual(si.RoutingClassifier().classify(m.check_url.split("/")[2].rsplit(":", 1)[0]), "local")

    def test_local_and_lan_legacy_need_no_call(self):
        _, m, calls = self._gates()
        self.assertIsNone(m.decide(LOCAL_SRC, "/vod/a.mp4", None))
        self.assertIsNone(m.decide(LAN_SRC, "/vod/a.mp4", None))
        self.assertEqual(calls, [])

    def test_overlay(self):
        g, m, calls = self._gates()
        st, body = m.decide(OVERLAY_SRC, "/vod/a.mp4", None)
        self.assertEqual((st, body["reason"]), (401, "legacy-overlay"))
        dev = pair(g)
        _, p = setup_v2(g, dev, source=OVERLAY_SRC, media_host=OVERLAY_DECLARED)
        self.assertIsNone(m.decide(OVERLAY_SRC, "/vod/a.mp4", p["token"]))
        self.assertIsNone(m.decide(OVERLAY_SRC, "/vod/a.mp4?media_token=" + p["media_token"], None))
        st, body = m.decide(OVERLAY_SRC, "/vod/a.mp4?media_token=forged", None)
        self.assertEqual((st, body["reason"]), (401, "media-token-unknown"))
        self.assertEqual(calls[-1]["path"], "/vod/a.mp4")          # no query forwarded
        self.assertNotIn(LAN_SRC, json.dumps(calls))
        self.assertNotIn(OVERLAY_SRC, json.dumps(calls))            # the class, never the address
        self.assertEqual({c["routing"] for c in calls}, {"overlay"})

    def test_lan_with_a_token_is_checked(self):
        g, m, calls = self._gates()
        dev = pair(g)
        (st, p), _ = setup(g, dev)
        self.assertIsNone(m.decide(LAN_SRC, "/vod/a.mp4", p["token"]))
        self.assertEqual(len(calls), 1)
        self.assertEqual([a for a in audit_lines(g) if a["event"] == "media_session"][-1]["routing_evidence"], "lan")

    def test_companion_unreachable_fails_closed(self):
        g, m, _ = self._gates(raising=True)
        st, body = m.decide(OVERLAY_SRC, "/vod/a.mp4?media_token=abc", None)
        self.assertEqual((st, body["reason"]), (503, "identity-unavailable"))
        last = audit_lines(g)[-1]
        self.assertEqual((last["event"], last["reason"], last["media_token_used"]),
                         ("media_refused", "identity-unavailable", True))

    def test_mask(self):
        line = 'GET /vod/a.mp4?x=1&media_token=SECRETVALUE&y=2 HTTP/1.1'
        self.assertEqual(si.MediaGate.mask(line), 'GET /vod/a.mp4?x=1&media_token=<redacted>&y=2 HTTP/1.1')
        self.assertEqual(si.MediaGate.mask("GET /a?media_token=Z"), "GET /a?media_token=<redacted>")
        self.assertEqual(si.MediaGate.mask("GET /a"), "GET /a")

    def test_flag_absent_builds_nothing(self):
        self.assertIsNone(si.media_gate_from_environ({}, ROOT_PATH))
        self.assertIsNone(si.media_gate_from_environ({si.FLAG_ENV: " "}, ROOT_PATH))


class AuditPrivacy(unittest.TestCase):
    def test_no_address_token_or_media_token(self):
        g = make_gate()
        dev = pair(g)
        st, p = setup_v2(g, dev, source=OVERLAY_SRC, media_host=LAN_DECLARED, overlay_host=OVERLAY_DECLARED)
        media_check(g, "overlay", media_token=p["media_token"])
        media_check(g, "overlay", media_token="forged")
        g.authorize("POST", "/plugins/games/native-stream-start", "port=1", p["token"], OVERLAY_SRC)
        text = g.audit.path.read_text()
        for secret in (p["token"], p["media_token"], KEY_HEX, *ALL_ADDRESSES):
            self.assertNotIn(secret, text)
        for line in audit_lines(g):
            self.assertIn(line["routing_evidence"], ("lan", "overlay", "unknown"))


from common import ROOT as ROOT_PATH  # noqa: E402

if __name__ == "__main__":
    unittest.main()
