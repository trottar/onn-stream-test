#!/usr/bin/env python3
"""G3-S1: the session gate — every accept / refuse case.

    python3 -m unittest discover -s tests/session_identity -v

Stores and audit logs live in a temporary directory (removed at exit); the
addresses are built from integers in memory and never written.
"""

from __future__ import annotations

import ast
import json
import os
import stat
import unittest

from common import (
    ALL_ADDRESSES, KEY_HEX, LAN_DECLARED, LAN_SRC, LOCAL_SRC, OVERLAY_DECLARED, OVERLAY_SRC, ROOT,
    UNKNOWN_SRC, Clock, audit_lines, make_gate, pair, setup, sign, si,
)


def reasons(gate) -> list[str]:
    return [line.get("reason") for line in audit_lines(gate) if line.get("reason")]


class Routing(unittest.TestCase):
    def test_classes(self):
        g = make_gate()
        c = g.classifier.classify
        self.assertEqual(c(LOCAL_SRC), "local")
        self.assertEqual(c(LAN_SRC), "lan")
        self.assertEqual(c(OVERLAY_SRC), "overlay")
        self.assertEqual(c(UNKNOWN_SRC), "unknown")
        self.assertEqual(c("not-an-address"), "unknown")

    def test_flag_absent_builds_nothing(self):
        self.assertIsNone(si.gate_from_environ({}, ROOT))
        self.assertIsNone(si.gate_from_environ({si.FLAG_ENV: " "}, ROOT))


class Pairing(unittest.TestCase):
    def test_window_closed(self):
        g = make_gate()
        st, p = g.session_route("POST", "/session/pair", {"code": "000000", "device_name": "x", "key": KEY_HEX}, None, LAN_SRC)
        self.assertEqual((st, p["reason"]), (403, "pairing-closed"))

    def test_open_needs_host_or_admin(self):
        g = make_gate()
        st, p = g.session_route("POST", "/session/pairing/open", {}, None, LAN_SRC)
        self.assertEqual((st, p["reason"]), (403, "pairing-admin-required"))
        st, p = g.session_route("POST", "/session/pairing/open", {}, None, OVERLAY_SRC)
        self.assertEqual((st, p["reason"]), (403, "pairing-admin-required"))

    def test_pair_ok_store_has_no_address(self):
        g = make_gate()
        dev = pair(g)
        self.assertTrue(dev.startswith("dev-"))
        path = g.devices._file.path
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        text = path.read_text()
        for a in ALL_ADDRESSES:
            self.assertNotIn(a, text)
        self.assertEqual(json.loads(text)["devices"][0]["permissions"], ["games", "tv", "vod"])
        # the window closes on success
        st, p = g.session_route("POST", "/session/pair", {"code": "000000", "device_name": "x", "key": KEY_HEX}, None, LAN_SRC)
        self.assertEqual(p["reason"], "pairing-closed")

    def test_pair_over_overlay_or_unknown_refused(self):
        g = make_gate()
        _, opened = g.session_route("POST", "/session/pairing/open", {}, None, LOCAL_SRC)
        st, p = g.session_route("POST", "/session/pair", {"code": opened["code"], "device_name": "x", "key": KEY_HEX}, None, OVERLAY_SRC)
        self.assertEqual((st, p["reason"]), (403, "pairing-not-lan"))
        st, p = g.session_route("POST", "/session/pair", {"code": opened["code"], "device_name": "x", "key": KEY_HEX}, None, UNKNOWN_SRC)
        self.assertEqual((st, p["reason"]), (401, "network-unknown"))

    def test_bad_code_and_exhaustion(self):
        g = make_gate()
        _, opened = g.session_route("POST", "/session/pairing/open", {}, None, LOCAL_SRC)
        wrong = "%06d" % ((int(opened["code"]) + 1) % 10**6)
        for _ in range(si.PAIRING_MAX_ATTEMPTS - 1):
            st, p = g.session_route("POST", "/session/pair", {"code": wrong, "device_name": "x", "key": KEY_HEX}, None, LAN_SRC)
            self.assertEqual(p["reason"], "pairing-bad-code")
        st, p = g.session_route("POST", "/session/pair", {"code": wrong, "device_name": "x", "key": KEY_HEX}, None, LAN_SRC)
        self.assertEqual(p["reason"], "pairing-attempts-exhausted")
        st, p = g.session_route("POST", "/session/pair", {"code": opened["code"], "device_name": "x", "key": KEY_HEX}, None, LAN_SRC)
        self.assertEqual(p["reason"], "pairing-closed")

    def test_window_expires(self):
        clock = Clock()
        g = make_gate(clock=clock)
        _, opened = g.session_route("POST", "/session/pairing/open", {}, None, LOCAL_SRC)
        clock.t += si.PAIRING_WINDOW_S + 1
        st, p = g.session_route("POST", "/session/pair", {"code": opened["code"], "device_name": "x", "key": KEY_HEX}, None, LAN_SRC)
        self.assertEqual(p["reason"], "pairing-closed")

    def test_short_key_refused(self):
        g = make_gate()
        _, opened = g.session_route("POST", "/session/pairing/open", {}, None, LOCAL_SRC)
        st, p = g.session_route("POST", "/session/pair", {"code": opened["code"], "device_name": "x", "key": "ab" * 8}, None, LAN_SRC)
        self.assertEqual((st, p["reason"]), (400, "pairing-bad-request"))


class Setup(unittest.TestCase):
    def test_signed_setup_accepted(self):
        g = make_gate()
        dev = pair(g)
        (st, p), _ = setup(g, dev)
        self.assertEqual(st, 200)
        self.assertEqual(p["client_id"], dev)
        self.assertEqual(p["expires_in_s"], int(si.TOKEN_TTL_S))
        d = g.authorize("POST", "/plugins/games/launch", "id=x", p["token"], LAN_SRC)
        self.assertTrue(d.allowed)
        self.assertEqual((d.kind, d.media_host), ("session", LAN_DECLARED))

    def test_wrong_signature(self):
        g = make_gate()
        dev = pair(g)
        _, n = g.session_route("POST", "/session/nonce", {}, None, LAN_SRC)
        body = {"device_id": dev, "nonce": n["nonce"], "media_host": LAN_DECLARED, "video_port": 50000,
                "sig": sign(dev, n["nonce"], LAN_DECLARED, 50001)}
        st, p = g.session_route("POST", "/session/setup", body, None, LAN_SRC)
        self.assertEqual((st, p["reason"]), (401, "bad-signature"))

    def test_replayed_nonce(self):
        g = make_gate()
        dev = pair(g)
        (st, _), body = setup(g, dev)
        self.assertEqual(st, 200)
        st, p = g.session_route("POST", "/session/setup", body, None, LAN_SRC)
        self.assertEqual((st, p["reason"]), (401, "nonce-replayed"))

    def test_expired_and_unknown_nonce(self):
        clock = Clock()
        g = make_gate(clock=clock)
        dev = pair(g)
        _, n = g.session_route("POST", "/session/nonce", {}, None, LAN_SRC)
        clock.t += si.NONCE_TTL_S + 1
        body = {"device_id": dev, "nonce": n["nonce"], "media_host": LAN_DECLARED, "video_port": 50000,
                "sig": sign(dev, n["nonce"], LAN_DECLARED, 50000)}
        st, p = g.session_route("POST", "/session/setup", body, None, LAN_SRC)
        self.assertEqual(p["reason"], "nonce-expired")
        body["nonce"] = "never-issued"
        st, p = g.session_route("POST", "/session/setup", body, None, LAN_SRC)
        self.assertEqual(p["reason"], "nonce-unknown")

    def test_unknown_device(self):
        g = make_gate()
        (st, p), _ = setup(g, "dev-0000000000000000")
        self.assertEqual((st, p["reason"]), (401, "unknown-device"))

    def test_expired_token(self):
        clock = Clock()
        g = make_gate(clock=clock)
        (st, p), _ = setup(g, pair(g))
        clock.t += si.TOKEN_TTL_S + 1
        d = g.authorize("GET", "/plugins/games/status", "", p["token"], LAN_SRC)
        self.assertEqual((d.allowed, d.status, d.reason), (False, 401, "token-expired"))

    def test_unknown_token_never_falls_back(self):
        g = make_gate()
        d = g.authorize("GET", "/plugins/games/status", "", "forged", LAN_SRC)
        self.assertEqual((d.allowed, d.reason), (False, "token-unknown"))

    def test_session_end(self):
        g = make_gate()
        (_, p), _ = setup(g, pair(g))
        st, _ = g.session_route("POST", "/session/end", {}, p["token"], LAN_SRC)
        self.assertEqual(st, 200)
        self.assertEqual(g.authorize("GET", "/plugins/games/status", "", p["token"], LAN_SRC).reason, "token-unknown")

    def test_revoked_device(self):
        g = make_gate()
        dev = pair(g)
        (_, p), _ = setup(g, dev)
        path = g.devices._file.path
        doc = json.loads(path.read_text())
        doc["devices"] = []
        path.write_text(json.dumps(doc))
        d = g.authorize("GET", "/plugins/games/status", "", p["token"], LAN_SRC)
        self.assertEqual((d.allowed, d.reason), (False, "device-revoked"))

    def test_overlay_session_with_overlay_endpoint(self):
        g = make_gate()
        dev = pair(g)
        (st, p), _ = setup(g, dev, source=OVERLAY_SRC, media_host=OVERLAY_DECLARED)
        self.assertEqual(st, 200)
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=50000", p["token"], OVERLAY_SRC)
        self.assertEqual((d.allowed, d.media_host), (True, OVERLAY_DECLARED))


class Endpoints(unittest.TestCase):
    def test_class_mismatch(self):
        g = make_gate()
        (st, p), _ = setup(g, pair(g), source=LAN_SRC, media_host=OVERLAY_DECLARED)
        self.assertEqual((st, p["reason"]), (403, "endpoint-class-mismatch"))
        g2 = make_gate()
        (st, p), _ = setup(g2, pair(g2), source=OVERLAY_SRC, media_host=LAN_DECLARED)
        self.assertEqual(p["reason"], "endpoint-class-mismatch")

    def test_invalid(self):
        g = make_gate()
        dev = pair(g)
        (st, p), _ = setup(g, dev, media_host=LOCAL_SRC)
        self.assertEqual(p["reason"], "endpoint-invalid")
        (st, p), _ = setup(g, dev, port=80)
        self.assertEqual(p["reason"], "endpoint-invalid")
        (st, p), _ = setup(g, dev, media_host="not-an-address")
        self.assertEqual(p["reason"], "endpoint-invalid")

    def test_port_mismatch(self):
        g = make_gate()
        (_, p), _ = setup(g, pair(g), port=50000)
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=50002", p["token"], LAN_SRC)
        self.assertEqual((d.allowed, d.reason), (False, "endpoint-port-mismatch"))

    def test_client_target_declared_not_source(self):
        g = make_gate()
        (_, p), _ = setup(g, pair(g))
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=50000", p["token"], LAN_SRC)

        class H:
            client_address = (LAN_SRC, 1)
        h = H()
        h._session_decision = d
        self.assertEqual(si.SessionGate.client_target(h), LAN_DECLARED)
        h._session_decision = si.Decision(True, kind="legacy")
        self.assertEqual(si.SessionGate.client_target(h), LAN_SRC)


class Permissions(unittest.TestCase):
    def _session(self, perms):
        g = make_gate()
        dev = pair(g)
        path = g.devices._file.path
        doc = json.loads(path.read_text())
        doc["devices"][0]["permissions"] = perms
        path.write_text(json.dumps(doc))
        (_, p), _ = setup(g, dev)
        return g, p["token"]

    def test_denied(self):
        g, tok = self._session(["tv"])
        d = g.authorize("POST", "/plugins/games/launch", "id=x", tok, LAN_SRC)
        self.assertEqual((d.allowed, d.status, d.reason), (False, 403, "permission-denied"))
        self.assertTrue(g.authorize("GET", "/sources", "", tok, LAN_SRC).allowed)

    def test_unknown_permission_denied(self):
        g, tok = self._session(["games", "tv", "vod"])
        for path in ("/status", "/diagnostics/health", "/no/such/route"):
            d = g.authorize("GET", path, "", tok, LAN_SRC)
            self.assertEqual((d.allowed, d.reason), (False, "permission-unknown"), path)

    def test_pairing_admin(self):
        g, tok = self._session(["games", "pairing-admin"])
        st, p = g.session_route("POST", "/session/pairing/open", {}, tok, LAN_SRC)
        self.assertEqual(st, 200)
        g2, tok2 = self._session(["games"])
        st, p = g2.session_route("POST", "/session/pairing/open", {}, tok2, LAN_SRC)
        self.assertEqual(p["reason"], "pairing-admin-required")


class Legacy(unittest.TestCase):
    def test_lan_accepted_and_audited(self):
        g = make_gate()
        d = g.authorize("GET", "/plugins/games/status", "", None, LAN_SRC)
        self.assertEqual((d.allowed, d.kind, d.issued_token), (True, "legacy", None))
        d = g.authorize("POST", "/plugins/games/native-stream-start", "port=50000", None, LAN_SRC)
        self.assertTrue(d.allowed and d.issued_token)
        lines = audit_lines(g)
        self.assertEqual(lines[-1]["event"], "legacy_setup")
        self.assertEqual(lines[-1]["client_id"], "legacy-lan")
        self.assertEqual(lines[-1]["routing_evidence"], "lan")

    def test_overlay_and_unknown_refused(self):
        g = make_gate()
        self.assertEqual(g.authorize("GET", "/plugins/games/status", "", None, OVERLAY_SRC).reason, "legacy-overlay")
        self.assertEqual(g.authorize("GET", "/plugins/games/status", "", None, UNKNOWN_SRC).reason,
                         "legacy-unknown-network")

    def test_legacy_token_never_over_overlay(self):
        g = make_gate()
        d = g.authorize("POST", "/plugins/games/launch", "id=x", None, LAN_SRC)
        d2 = g.authorize("GET", "/plugins/games/status", "", d.issued_token, OVERLAY_SRC)
        self.assertEqual((d2.allowed, d2.reason), (False, "legacy-overlay"))

    def test_turned_off(self):
        g = make_gate()
        p = g.settings._file.path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"legacy_unpaired_lan": False}))
        self.assertEqual(g.authorize("GET", "/plugins/games/status", "", None, LAN_SRC).reason, "legacy-disabled")

    def test_broken_settings_fail_closed(self):
        g = make_gate()
        p = g.settings._file.path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{not json")
        self.assertEqual(g.authorize("GET", "/plugins/games/status", "", None, LAN_SRC).reason, "legacy-disabled")

    def test_host_local_always(self):
        g = make_gate()
        p = g.settings._file.path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"legacy_unpaired_lan": False}))
        d = g.authorize("POST", "/plugins/games/launch", "id=x", None, LOCAL_SRC)
        self.assertEqual((d.allowed, d.kind), (True, "host-local"))


class UnknownMode(unittest.TestCase):
    def test_fails_closed(self):
        g = make_gate(mode="v3")
        self.assertEqual(g.authorize("GET", "/plugins/games/status", "", None, LAN_SRC).reason, "identity-flag-unknown")
        self.assertTrue(g.authorize("GET", "/plugins/games/status", "", None, LOCAL_SRC).allowed)
        st, p = g.session_route("POST", "/session/nonce", {}, None, LAN_SRC)
        self.assertEqual(p["reason"], "identity-flag-unknown")


class AuditPrivacy(unittest.TestCase):
    def test_no_address_key_or_token(self):
        g = make_gate()
        dev = pair(g)
        (_, p), _ = setup(g, dev)
        g.authorize("GET", "/plugins/games/status", "", None, OVERLAY_SRC)
        g.authorize("GET", "/plugins/games/status", "", "forged", UNKNOWN_SRC)
        g.authorize("POST", "/plugins/games/launch", "id=x", None, LAN_SRC)
        text = g.audit.path.read_text()
        for secret in (*ALL_ADDRESSES, KEY_HEX, p["token"]):
            self.assertNotIn(secret, text)
        for line in audit_lines(g):
            if "routing_evidence" in line:
                self.assertIn(line["routing_evidence"], ("lan", "overlay", "unknown"))


class ServiceGlue(unittest.TestCase):
    def test_imported_only_under_the_flag(self):
        src = (ROOT / "companion" / "privyhub_service.py").read_text()
        tree = ast.parse(src)
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
               and (getattr(n, "module", "") or "").startswith("session_identity")]
        self.assertEqual(top, [])
        guarded = [n for n in tree.body if isinstance(n, ast.If)
                   and "PRIVYHUB_SESSION_IDENTITY" in ast.get_source_segment(src, n.test)]
        self.assertEqual(len(guarded), 1)


if __name__ == "__main__":
    unittest.main()
