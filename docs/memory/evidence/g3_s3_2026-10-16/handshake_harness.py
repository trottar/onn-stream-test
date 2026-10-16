#!/usr/bin/env python3
"""G3-S3: the handshake harness, extended — client bytes against the host, in process.

The client side is a line-for-line port of the APK's G3-S3 protocol
(`identity/SessionProtocol.kt`: the v2 canon, the compact v2 setup body in the
client's field order, the overlay-block test; `IdentitySession.kt`: the
header where a granted permission is needed, `diagnostics` implied for a
paired device, one retry on a token refusal), first checked against the
host-made v2 vectors. The host side is the edited `SessionGate`, its
`MediaGate`, and the edited range server's request handler run in process
over a fixture media tree (G3-S3's replay helpers). Each step prints its
verdict; addresses are built from integers and printed only as labels.

    python3 docs/memory/evidence/g3_s3_2026-10-16/handshake_harness.py
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tests" / "session_identity"))

from common import LAN_DECLARED, LAN_SRC, LOCAL_SRC, OVERLAY_DECLARED, OVERLAY_SRC, Clock, make_gate, si  # noqa: E402
import test_range_replay as rr  # noqa: E402

# ---- the client, ported from SessionProtocol.kt / IdentitySession.kt (G3-S3) ---
SETUP_CANON_V2 = "privyhub-session-setup-v2"
IMPLIED_FOR_PAIRED = {"diagnostics"}
RETRYABLE = {"token-unknown", "token-expired"}


def canonical_v2(device_id, nonce, media_host, video_port, audio_port, overlay_host):
    return "\n".join([SETUP_CANON_V2, device_id, nonce, media_host, str(video_port), str(audio_port), overlay_host or ""])


def sign_v2(key_hex, *fields):
    return hmac.new(bytes.fromhex(key_hex), canonical_v2(*fields).encode(), hashlib.sha256).hexdigest()


def setup_body_v2(device_id, nonce, media_host, video_port, audio_port, overlay_host, sig) -> str:
    # SessionProtocol.setupBodyV2: compact, this field order; overlay_host only when present.
    return ("{" + f"\"device_id\":{json.dumps(device_id)},\"nonce\":{json.dumps(nonce)},"
            f"\"media_host\":{json.dumps(media_host)},\"video_port\":{video_port},\"audio_port\":{audio_port},"
            + (f"\"overlay_host\":{json.dumps(overlay_host)}," if overlay_host is not None else "")
            + f"\"sig_v\":2,\"sig\":{json.dumps(sig)}" + "}")


def is_overlay_ipv4(address: str) -> bool:
    parts = address.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return False
    v = (int(parts[0]) << 24) | (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])
    return (v & 0xFFC00000) == 0x64400000


class Client:
    """IdentitySession's decisions, ported."""

    def __init__(self, gate, key_hex, source, media_host, overlay_host=None):
        self.gate, self.key, self.source = gate, key_hex, source
        self.media_host, self.overlay_host = media_host, overlay_host
        self.device_id = None
        self.pairing_permissions: list[str] = []
        self.token = None
        self.granted: set[str] = set()
        self.media_token = None
        self.setups = 0
        self.shown: list[str] = []

    def pair(self):
        _, opened = self.gate.session_route("POST", "/session/pairing/open", {}, None, LOCAL_SRC)
        st, body = self.gate.session_route("POST", "/session/pair",
                                           {"code": opened["code"], "device_name": "harness", "key": self.key},
                                           None, self.source)
        self.device_id, self.pairing_permissions = body.get("device_id"), body.get("permissions", [])
        return st, body

    def setup(self):
        self.setups += 1
        _, n = self.gate.session_route("POST", "/session/nonce", {}, None, self.source)
        overlay = self.overlay_host if self.overlay_host and is_overlay_ipv4(self.overlay_host) else None
        sig = sign_v2(self.key, self.device_id, n["nonce"], self.media_host, 48100, 48101, overlay)
        raw = setup_body_v2(self.device_id, n["nonce"], self.media_host, 48100, 48101, overlay, sig)
        st, body = self.gate.session_route("POST", "/session/setup", json.loads(raw), None, self.source)
        if st == 200:
            self.token, self.granted, self.media_token = body["token"], set(body["permissions"]), body["media_token"]
            self.pairing_permissions = body["permissions"]
        return st, body

    def header_for(self, path):
        perm = si.required_permission(path)
        if perm is None or (perm not in self.pairing_permissions and perm not in IMPLIED_FOR_PAIRED):
            return None
        if self.token is None:
            self.setup()
        return self.token if perm in self.granted else None

    def call(self, method, path, query=""):
        """One control call through the gate; one retry on a token refusal; else the reason shown."""
        for attempt in (0, 1):
            d = self.gate.authorize(method, path, query, self.header_for(path), self.source)
            if d.allowed:
                return d
            if d.reason in RETRYABLE and attempt == 0:
                self.token = None
                continue
            self.shown.append(d.reason)
            return d
        return d


# ---- the run -----------------------------------------------------------------
results: list[tuple[str, bool, str]] = []


def step(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")


def ip(hexint):
    return None if hexint is None else str(ipaddress.ip_address(int(hexint, 16)))


def main() -> int:
    vectors = json.loads((HERE / "setup_vectors_v2.json").read_text())
    good = 0
    for v in vectors["vectors"]:
        c = canonical_v2(v["device_id"], v["nonce"], ip(v["media_host"]), v["video_port"], v["audio_port"], ip(v["overlay_host"]))
        good += (hashlib.sha256(c.encode()).hexdigest() == v["canonical_sha256"]
                 and sign_v2(v["key_hex"], v["device_id"], v["nonce"], ip(v["media_host"]), v["video_port"],
                             v["audio_port"], ip(v["overlay_host"])) == v["sig"])
    step("port matches the host-made v2 vectors", good == 3, f"{good}/3 canon + signature")

    clock = Clock()
    gate = make_gate(clock=clock)
    key = hashlib.sha256(b"g3-s3 harness key").hexdigest()

    # at home: pair, then a LAN session
    home = Client(gate, key, LAN_SRC, LAN_DECLARED)
    st, body = home.pair()
    step("pair on the LAN (window opened on the hub's loopback)", st == 200 and "diagnostics" in body["permissions"],
         f"{st}, permissions {','.join(body.get('permissions', []))}")
    st, body = home.setup()
    step("LAN v2 setup", st == 200 and bool(body.get("media_token")), f"{st}, media token issued: {bool(body.get('media_token'))}")
    d = home.call("POST", "/plugins/games/native-stream-start", "port=48100")
    step("LAN stream start to the declared LAN host", d.allowed and d.media_host == LAN_DECLARED,
         f"target {'lan-declared' if d.media_host == LAN_DECLARED else 'other'}")

    # off-site: the same device over the overlay, declaring its overlay interface address
    away = Client(gate, key, OVERLAY_SRC, OVERLAY_DECLARED, overlay_host=OVERLAY_DECLARED)
    away.device_id, away.pairing_permissions = home.device_id, home.pairing_permissions
    st, body = away.setup()
    step("overlay v2 setup with the overlay address declared", st == 200, f"{st}")
    d = away.call("POST", "/plugins/games/native-stream-start", "port=48100")
    step("overlay stream start to the declared overlay host", d.allowed and d.media_host == OVERLAY_DECLARED,
         f"target {'overlay-declared' if d.media_host == OVERLAY_DECLARED else 'other'}")
    d = away.call("POST", "/plugins/games/native-stream-start", "port=48102")
    step("port mismatch refused, shown, not retried", (not d.allowed) and d.status == 403
         and away.shown[-1:] == ["endpoint-port-mismatch"] and away.setups == 1, f"{d.status} {d.reason}")
    d = away.call("POST", "/plugins/games/native-stream-start", "port=48100&audio_port=48101")
    step("signed audio port accepted", d.allowed, "port + audio_port as signed")

    for label, method, path in (("TV-sync GET", "GET", "/plugins/tv_state/state"),
                                ("TV-sync POST", "POST", "/plugins/tv_state/state"),
                                ("EPG guide", "GET", "/plugins/epg/guide"),
                                ("EPG prefetch", "POST", "/plugins/epg/prefetch"),
                                ("diagnostics /status", "GET", "/status"),
                                ("diagnostics health", "GET", "/diagnostics/health")):
        d = away.call(method, path)
        bare = gate.authorize(method, path, "", None, OVERLAY_SRC)
        step(f"{label} over the overlay with the token", d.allowed and bare.reason == "legacy-overlay",
             f"with token allowed; without: {bare.reason}")

    # the range server over the overlay
    root, vod = rr.media_tree()
    after = rr.load("range_after", (ROOT / "companion" / "range_server.py").read_text())

    def transport(url, raw):
        s, payload = gate.session_route("POST", si.MEDIA_CHECK_PATH, json.loads(raw), None, LOCAL_SRC)
        return s, json.dumps(payload).encode()

    after.RANGE_GATE = si.MediaGate("v2", gate.devices._file.path.parent, gate.audit.path,
                                    classifier=gate.classifier, transport=transport)
    before = rr.load("range_before", (rr.FIX / "range_server_predecessor.py.txt").read_text())
    H, B = rr.handler_class(after), rr.handler_class(before)
    want, _ = rr.run(B, root, vod, "GET", "/vod/movie.mp4", LAN_SRC, {"Range": "bytes=0-4095"})
    raw, _ = rr.run(H, root, vod, "GET", "/vod/movie.mp4", OVERLAY_SRC, {"Range": "bytes=0-4095"})
    step("range server, overlay, no token", raw.startswith(b"HTTP/1.0 401") and b"legacy-overlay" in raw, "401 legacy-overlay")
    raw, _ = rr.run(H, root, vod, "GET", "/vod/movie.mp4", OVERLAY_SRC,
                    {"Range": "bytes=0-4095", si.SESSION_HEADER: away.token})
    step("range server, overlay, the header (the client's player)", raw == want, "206, the baseline's bytes")
    raw, log = rr.run(H, root, vod, "GET", f"/vod/movie.mp4?media_token={away.media_token}", OVERLAY_SRC,
                      {"Range": "bytes=0-4095"})
    step("range server, overlay, the media token (a header-less player)",
         raw == want and away.media_token not in log, "206, the baseline's bytes; the log masks it")
    raw, _ = rr.run(H, root, vod, "GET", "/vod/movie.mp4?media_token=forged", OVERLAY_SRC)
    step("range server, a forged media token", b"media-token-unknown" in raw, "401 media-token-unknown")
    raw, _ = rr.run(H, root, vod, "GET", "/vod/movie.mp4", LAN_SRC, {"Range": "bytes=0-4095"})
    step("range server, LAN, no token (legacy)", raw == want, "today's bytes")
    raw, _ = rr.run(H, root, vod, "GET", "/artwork/game.png", LAN_SRC, {si.SESSION_HEADER: home.token})
    step("range server, LAN, the header (artwork)", raw.startswith(b"HTTP/1.0 200"), "200, checked and audited")

    # expiry: one fresh setup and one retry
    clock.t += si.TOKEN_TTL_S + 5
    before_setups = away.setups
    d = away.call("GET", "/plugins/tv_state/state")
    step("expiry: token-expired, one fresh setup, one retry", d.allowed and away.setups == before_setups + 1, "allowed after the retry")

    # revoking diagnostics in the record
    store = gate.devices._file.path
    doc = json.loads(store.read_text())
    doc["devices"][0]["permissions"] = ["games", "tv", "vod"]
    store.write_text(json.dumps(doc))
    d = away.call("GET", "/status")
    step("diagnostics revoked: refused, shown", (not d.allowed) and away.shown[-1] == "permission-denied", f"{d.status} {d.reason}")

    st, status = gate.session_route("GET", "/session/status", None, None, LOCAL_SRC)
    live = [s for s in status["sessions"] if s["kind"] == "session"]
    step("status document: permission set and media-token boolean",
         st == 200 and live and all(isinstance(s["media_token_live"], bool) for s in live)
         and "diagnostics" in status["permissions_known"], f"{len(live)} live sessions listed")

    audit = gate.audit.path.read_text()
    secrets = [home.token, away.token, home.media_token, away.media_token, key, LAN_SRC, LAN_DECLARED, OVERLAY_SRC, OVERLAY_DECLARED]
    events = [json.loads(x) for x in audit.splitlines()]
    used = {e.get("media_token_used") for e in events if e["event"] == "media_session"}
    step("audit: no address, key, token or media token; media use and the port mismatch recorded",
         not any(s and s in audit for s in secrets) and used == {True, False}
         and any(e.get("reason") == "endpoint-port-mismatch" for e in events),
         f"{len(events)} lines; media_session media_token_used {sorted(used)}")

    passed = sum(ok for _, ok, _ in results)
    print(f"\n{passed} / {len(results)} PASS")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
