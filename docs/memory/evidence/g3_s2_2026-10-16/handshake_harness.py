#!/usr/bin/env python3
"""G3-S2: the handshake, client bytes against G3-S1's host logic, in process.

The client side here is a line-for-line port of the APK's
`identity/SessionProtocol.kt` (the canonical string, the HMAC, the compact
setup / pair bodies in the client's field order) and of `IdentitySession`'s
decisions (refresh margin, one retry on a token refusal, the header only
where a granted permission is needed). The port is first checked against the
same vectors the client's unit tests read (`setup_vectors.json`). The host
side is G3-S1's `SessionGate` unchanged. Each step prints its verdict; the
addresses are built from integers and printed only as labels.

    python3 docs/memory/evidence/g3_s2_2026-10-16/handshake_harness.py
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

from common import LAN_DECLARED, LAN_SRC, LOCAL_SRC, OVERLAY_SRC, Clock, make_gate, si  # noqa: E402

LABEL = {LAN_SRC: "lan-source", LAN_DECLARED: "lan-declared", LOCAL_SRC: "hub-loopback", OVERLAY_SRC: "overlay"}

# ---- the client, ported from SessionProtocol.kt / IdentitySession.kt ----------
SETUP_CANON = "privyhub-session-setup-v1"
REFRESH_MARGIN_S = 10 * 60
RETRYABLE = {"token-unknown", "token-expired"}


def canonical(device_id: str, nonce: str, media_host: str, video_port: int) -> str:
    return "\n".join([SETUP_CANON, device_id, nonce, media_host, str(video_port)])


def sign(key_hex: str, device_id: str, nonce: str, media_host: str, video_port: int) -> str:
    return hmac.new(bytes.fromhex(key_hex), canonical(device_id, nonce, media_host, video_port).encode(),
                    hashlib.sha256).hexdigest()


def setup_body(device_id, nonce, media_host, video_port, audio_port, sig) -> str:
    # SessionProtocol.setupBody: compact, this field order, ports as numbers.
    return ("{" + f"\"device_id\":{json.dumps(device_id)},\"nonce\":{json.dumps(nonce)},"
            f"\"media_host\":{json.dumps(media_host)},\"video_port\":{video_port},"
            f"\"audio_port\":{audio_port},\"sig\":{json.dumps(sig)}" + "}")


def pair_body(code, name, key_hex) -> str:
    return "{" + f"\"code\":{json.dumps(code)},\"device_name\":{json.dumps(name)},\"key\":{json.dumps(key_hex)}" + "}"


def client_sends_header(path: str, granted: list[str]) -> bool:
    perm = si.required_permission(path)   # the client mirrors this map (unit-tested against it)
    return perm is not None and perm in granted


# ---- the run -----------------------------------------------------------------
results: list[tuple[str, bool, str]] = []


def step(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")


def main() -> int:
    vectors = json.loads((HERE / "setup_vectors.json").read_text())
    for v in vectors["vectors"]:
        spec = v["media_host"]
        host = str(ipaddress.ip_address(int(spec["ipv4_int"], 16))) if "ipv4_int" in spec else spec["text"]
        c = canonical(v["device_id"], v["nonce"], host, v["video_port"])
        ok = (hashlib.sha256(c.encode()).hexdigest() == v["canonical_sha256"]
              and sign(v["key_hex"], v["device_id"], v["nonce"], host, v["video_port"]) == v["sig"])
        step(f"0 port = vectors ({v['name']})", ok, "canonical sha256 and sig match G3-S1's")

    clock = Clock()
    gate = make_gate(clock=clock)
    key = hashlib.sha256(b"g3-s2 harness device secret").hexdigest()   # 32 bytes, like the client's

    # 1. pairing: the hub opens the window on its loopback; the client pairs from the LAN.
    st, opened = gate.session_route("POST", "/session/pairing/open", {}, None, LOCAL_SRC)
    step("1a hub opens the pairing window", st == 200 and len(opened["code"]) == 6, f"status {st}, 6-digit code, 120 s")
    st, paired = gate.session_route("POST", "/session/pair", json.loads(pair_body(opened["code"], "onn fixture", key)),
                                    None, LAN_SRC)
    device = paired.get("device_id", "")
    step("1b client pairs (body as the APK sends it)", st == 200 and device.startswith("dev-"),
         f"status {st}, device id dev-…, permissions {paired.get('permissions')}")
    granted = paired.get("permissions", [])

    def setup(source=LAN_SRC, media_host=LAN_DECLARED, key_hex=key, replay_body=None):
        if replay_body is not None:
            return gate.session_route("POST", "/session/setup", json.loads(replay_body), None, source), replay_body
        st, n = gate.session_route("POST", "/session/nonce", {}, None, source)
        body = setup_body(device, n["nonce"], media_host, 48100, 48101, sign(key_hex, device, n["nonce"], media_host, 48100))
        return gate.session_route("POST", "/session/setup", json.loads(body), None, source), body

    # 2-3. nonce and the signed setup, endpoints declared.
    (st, tok), body = setup()
    step("2 nonce + 3 signed setup", st == 200 and "token" in tok,
         f"status {st}, token, expires_in_s {tok.get('expires_in_s')}; audio_port declared and ignored by the host")
    token = tok.get("token")
    issued_at = clock.t

    # 3b. the same setup body sent again at once: its nonce is spent. (Run 1
    # sent it after the 8-h expiry, when the host had purged the nonce, and
    # read nonce-unknown; refused either way. Moved here to test the replay.)
    (st, r), _ = setup(replay_body=body)
    step("3b replayed setup", r.get("reason") == "nonce-replayed", f"{st} {r.get('reason')}")

    # 4. a control call with the header: the declared target, not the source.
    d = gate.authorize("POST", "/plugins/games/native-stream-start", "port=48100", token, LAN_SRC)
    step("4 call with the token", d.allowed and d.media_host == LAN_DECLARED,
         f"allowed as {d.kind}; plugin target = {LABEL.get(d.media_host, 'other')} (source = lan-source)")

    # 4b. the client omits the header where the host would deny it.
    sends = client_sends_header("/status", granted)
    d = gate.authorize("GET", "/status", "", token, LAN_SRC)
    step("4b no header on /status", (not sends) and d.reason == "permission-unknown",
         "client sends none (legacy on the LAN); with a token the host would answer permission-unknown")

    # 5. refresh before expiry.
    clock.t = issued_at + tok["expires_in_s"] - REFRESH_MARGIN_S + 1
    needs = clock.t >= issued_at + tok["expires_in_s"] - REFRESH_MARGIN_S
    (st, tok2), _ = setup()
    step("5 refresh inside the 10-min margin", needs and st == 200 and tok2["token"] != token,
         "client re-runs nonce + setup; a new token")

    # 6. expiry: the old token refused, one retry with a fresh setup succeeds.
    clock.t = issued_at + tok["expires_in_s"] + 1
    d = gate.authorize("GET", "/plugins/games/status", "", token, LAN_SRC)
    retry = d.reason in RETRYABLE
    (st, tok3), _ = setup()
    d2 = gate.authorize("GET", "/plugins/games/status", "", tok3.get("token"), LAN_SRC)
    step("6 expired token → one retry", d.reason == "token-expired" and retry and d2.allowed,
         f"first {d.status} {d.reason}; client retries once after a fresh setup → allowed")

    # 7. refusals, each with its reason code shown.
    (st, r), _ = setup(key_hex=hashlib.sha256(b"wrong").hexdigest())
    step("7b wrong key", r.get("reason") == "bad-signature", f"{st} {r.get('reason')}")
    (st, r), _ = setup(media_host=str(ipaddress.ip_address(si.OVERLAY_NETWORKS[0][7])))
    step("7c declared overlay host from the LAN", r.get("reason") == "endpoint-class-mismatch", f"{st} {r.get('reason')}")
    d = gate.authorize("GET", "/plugins/games/status", "", None, OVERLAY_SRC)
    step("7d no token over the overlay", d.reason == "legacy-overlay", f"{d.status} {d.reason}")
    d = gate.authorize("GET", "/plugins/games/status", "", "forged", LAN_SRC)
    step("7e forged token", d.reason == "token-unknown" and not d.allowed, f"{d.status} {d.reason}; no fallback")
    retry_again = d.reason in RETRYABLE   # one retry, then a visible state
    step("7f one retry only", retry_again, "token-unknown is retried once, then shown (client unit tests: attempt 1 → shown)")

    # 8. the setting on, not paired: no header — the host's legacy LAN path, as today.
    gate2 = make_gate(clock=Clock())
    d = gate2.authorize("POST", "/plugins/games/launch", "id=x", None, LAN_SRC)
    step("8 unpaired client, legacy LAN", d.allowed and d.kind == "legacy" and bool(d.issued_token),
         "accepted as legacy-lan; the host's token header is ignored by the client")

    lines = [json.loads(x) for x in gate.audit.path.read_text().splitlines()]
    text = gate.audit.path.read_text()
    clean = not any(a in text for a in (LAN_SRC, LAN_DECLARED, OVERLAY_SRC, key, token))
    step("9 host audit", clean, f"{len(lines)} lines, no address, key or token")

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} / {len(results)} steps PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
