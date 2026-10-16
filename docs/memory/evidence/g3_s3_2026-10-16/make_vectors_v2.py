#!/usr/bin/env python3
"""G3-S3: the v2 setup vectors, made and verified by the host's own code.

For each case the canonical input is built from `session_identity.SETUP_CANON_V2`,
signed, and then **accepted by `SessionGate._setup` in process** (a device record
with the vector's id and key written into a temporary store; the vector's nonce
issued). The host bodies come from a gate run in process, serialised as the
companion's `_send_json` does (`json.dumps(indent=2)`). Addresses are integers,
built on each side; no address literal is written.

    python3 docs/memory/evidence/g3_s3_2026-10-16/make_vectors_v2.py <out.json>
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests" / "session_identity"))

from common import KEY_HEX, LAN_SRC, LOCAL_SRC, OVERLAY_SRC, make_gate, pair, si  # noqa: E402

CASES = [
    {"name": "lan-no-overlay", "device_id": "dev-0123456789abcdef", "nonce": "fixture-nonce-v2-1",
     "media_host": "0xC0A86439", "video_port": 48100, "audio_port": 48101, "overlay_host": None,
     "source": "lan"},
    {"name": "lan-with-overlay", "device_id": "dev-0123456789abcdef", "nonce": "fixture-nonce-v2-2",
     "media_host": "0xC0A86439", "video_port": 48100, "audio_port": 48101, "overlay_host": "0x64401235",
     "source": "lan"},
    {"name": "overlay-only", "device_id": "dev-fedcba9876543210", "nonce": "Zz-09_fixture-v2",
     "media_host": "0x64401235", "video_port": 50000, "audio_port": 50001, "overlay_host": "0x64401235",
     "source": "overlay"},
]


def ip(hexint: str | None) -> str:
    return "" if hexint is None else str(ipaddress.ip_address(int(hexint, 16)))


def main() -> None:
    out = Path(sys.argv[1])
    vectors = []
    for case in CASES:
        media, overlay = ip(case["media_host"]), ip(case["overlay_host"])
        canonical = "\n".join([si.SETUP_CANON_V2, case["device_id"], case["nonce"], media,
                               str(case["video_port"]), str(case["audio_port"]), overlay])
        sig = hmac.new(bytes.fromhex(KEY_HEX), canonical.encode(), hashlib.sha256).hexdigest()
        # the host accepts it
        g = make_gate()
        store = g.devices._file.path
        store.parent.mkdir(parents=True, exist_ok=True)
        store.write_text(json.dumps({"version": 1, "devices": [{
            "device_id": case["device_id"], "display_name": "fixture", "key_hex": KEY_HEX,
            "paired_at": "2026-10-16T00:00:00Z", "permissions": list(si.DEFAULT_PAIRED_PERMISSIONS),
            "permissions_v": 2}]}))
        g._nonces[case["nonce"]] = si._Nonce(g._clock() + 60)
        body = {"device_id": case["device_id"], "nonce": case["nonce"], "media_host": media,
                "video_port": case["video_port"], "audio_port": case["audio_port"], "sig_v": 2, "sig": sig}
        if overlay:
            body["overlay_host"] = overlay
        source = {"lan": LAN_SRC, "overlay": OVERLAY_SRC}[case["source"]]
        status, resp = g._setup(body, g.classifier.classify(source),
                                lambda st, reason, *a, **k: (st, {"reason": reason}))
        assert status == 200, (case["name"], resp)
        vectors.append({**case, "key_hex": KEY_HEX, "sig_v": 2,
                        "canonical_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                        "canonical_bytes": len(canonical.encode()), "sig": sig, "host_accepted": True})

    g = make_gate()
    dev = pair(g)
    _, n = g.session_route("POST", "/session/nonce", {}, None, LAN_SRC)
    from test_g3s3 import setup_v2, media_check
    st, ok = setup_v2(g, dev)
    st_mm = g.authorize("POST", "/plugins/games/native-stream-start", "port=1", ok["token"], LAN_SRC)
    bodies = {
        "setup_ok_v2": json.dumps({**ok, "token": "fixture-token", "media_token": "fixture-media-token",
                                   "client_id": "dev-0123456789abcdef"}, indent=2),
        "port_mismatch": json.dumps({"ok": False, "error": "session refused", "reason": st_mm.reason}, indent=2),
        "media_token_unknown": json.dumps(media_check(g, "overlay", media_token="x")[1], indent=2),
        "diagnostics_denied": json.dumps({"ok": False, "error": "session refused", "reason": "permission-denied"}, indent=2),
    }
    paths = ["/status", "/diagnostics/health", "/diagnostics/bundle", "/diagnostics/self-test",
             "/diagnostics/stream-telemetry", "/diagnostics/client-health", "/plugins/tv_state/state",
             "/plugins/epg/guide", "/plugins/epg/prefetch", "/plugins/iptv_org/channels", "/sources",
             "/plugins/games/launch", "/vod/x.mp4", "/session/nonce"]
    out.write_text(json.dumps({
        "setup_canon_v2": si.SETUP_CANON_V2,
        "vectors": vectors,
        "host_bodies": bodies,
        "permission_map": {p: si.required_permission(p) for p in paths},
        "default_paired_permissions": list(si.DEFAULT_PAIRED_PERMISSIONS),
        "media_permission": si.MEDIA_PERMISSION,
        "media_token_param": si.MEDIA_TOKEN_PARAM,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
