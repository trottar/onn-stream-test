#!/usr/bin/env python3
"""G3-S2: the setup test vectors, made by G3-S1's own code.

The HMAC input and signature come from `tests/session_identity/common.sign`
(G3-S1's signing helper) and `companion/session_identity.SETUP_CANON`; the
host response bodies come from G3-S1's `SessionGate` run in process and
serialised the way the companion's `_send_json` does (`json.dumps(indent=2)`).
A media host given as `ipv4_int` is built from that integer on both sides;
no address literal is written. Output: one JSON file, copied unchanged into
the client's unit-test resources.

    python3 docs/memory/evidence/g3_s2_2026-10-16/make_vectors.py <out.json>
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests" / "session_identity"))

import common  # noqa: E402  (G3-S1's helpers; puts companion/ on sys.path)
from common import KEY_HEX, LAN_SRC, LOCAL_SRC, OVERLAY_SRC, Clock, make_gate, si  # noqa: E402


def host_of(spec: dict) -> str:
    if "ipv4_int" in spec:
        return str(ipaddress.ip_address(int(spec["ipv4_int"], 16)))
    return spec["text"]


CASES = [
    {"name": "text-host", "device_id": "dev-0123456789abcdef", "nonce": "fixture-nonce-AAAA_bbbb-1",
     "media_host": {"text": "media-host-fixture"}, "video_port": 48100},
    {"name": "lan-ipv4", "device_id": "dev-0123456789abcdef", "nonce": "fixture-nonce-CCCC_dddd-2",
     "media_host": {"ipv4_int": "0xC0A86439"}, "video_port": 48100},
    {"name": "overlay-ipv4-port-50000", "device_id": "dev-fedcba9876543210", "nonce": "Zz-09_fixture",
     "media_host": {"ipv4_int": "0x64401235"}, "video_port": 50000},
]


def main() -> None:
    out = Path(sys.argv[1])
    vectors = []
    for case in CASES:
        host = host_of(case["media_host"])
        canonical = "\n".join([si.SETUP_CANON, case["device_id"], case["nonce"], host, str(case["video_port"])])
        vectors.append({
            **case,
            "key_hex": KEY_HEX,
            "canonical_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "canonical_bytes": len(canonical.encode()),
            "sig": common.sign(case["device_id"], case["nonce"], host, case["video_port"]),
        })

    # Host response bodies, from G3-S1's gate in process.
    clock = Clock()
    gate = make_gate(clock=clock)
    bodies: dict[str, dict] = {}

    def record(name: str, status: int, payload: dict) -> dict:
        bodies[name] = {"status": status, "body": json.dumps(payload, indent=2)}
        return payload

    st, opened = gate.session_route("POST", "/session/pairing/open", {}, None, LOCAL_SRC)
    st, paired = gate.session_route("POST", "/session/pair",
                                    {"code": opened["code"], "device_name": "onn \"fixture\"", "key": KEY_HEX},
                                    None, LAN_SRC)
    record("pair_ok", st, paired)
    record("pair_closed", *gate.session_route("POST", "/session/pair",
                                              {"code": "000000", "device_name": "x", "key": KEY_HEX}, None, LAN_SRC))
    st, nonce = gate.session_route("POST", "/session/nonce", {}, None, LAN_SRC)
    record("nonce_ok", st, nonce)
    (st, setup), _ = common.setup(gate, paired["device_id"])
    record("setup_ok", st, setup)
    st, bad = gate.session_route("POST", "/session/setup",
                                 {"device_id": paired["device_id"], "nonce": "never-issued", "media_host": "x",
                                  "video_port": 48100, "sig": "00"}, None, LAN_SRC)
    record("setup_nonce_unknown", st, bad)
    d = gate.authorize("GET", "/plugins/games/status", "", None, OVERLAY_SRC)
    record("legacy_overlay", d.status, {"ok": False, "error": "session refused", "reason": d.reason})
    d = gate.authorize("GET", "/status", "", setup["token"], LAN_SRC)
    record("permission_unknown", d.status, {"ok": False, "error": "session refused", "reason": d.reason})
    clock.t += si.TOKEN_TTL_S + 1
    d = gate.authorize("GET", "/plugins/games/status", "", setup["token"], LAN_SRC)
    record("token_expired", d.status, {"ok": False, "error": "session refused", "reason": d.reason})
    bodies["host_flag_off_nonce"] = {"status": 404, "body": json.dumps({"ok": False, "error": "Not found"}, indent=2)}

    doc = {
        "generated_by": "docs/memory/evidence/g3_s2_2026-10-16/make_vectors.py (G3-S1's sign() and SessionGate)",
        "setup_canon": si.SETUP_CANON,
        "header": si.SESSION_HEADER,
        "token_ttl_s": int(si.TOKEN_TTL_S),
        "vectors": vectors,
        "host_responses": bodies,
        "permission_paths": {p: si.required_permission(p) for p in (
            "/plugins/games/launch", "/plugins/games/native-stream-start", "/plugins/games/native-stream-heartbeat",
            "/plugins/games/status", "/diagnostics/client-health", "/plugins/epg/guide", "/sources",
            "/sources/x/start", "/stop", "/status", "/diagnostics/health", "/no/such")},
    }
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(vectors)} vectors, {len(bodies)} host responses -> {out.name}")


if __name__ == "__main__":
    main()
