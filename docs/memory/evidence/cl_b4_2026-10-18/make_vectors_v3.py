#!/usr/bin/env python3
"""CL-B4: the v3 setup vectors, made and verified by the host's own code (as G3-S3's v2 ones).

Each case: the v3 canonical (`session_identity.SETUP_CANON_V3`), signed; the client's exact body
string (the field order and compact form `SessionProtocol.setupBodyV3` writes); that string parsed
and **accepted by `SessionGate._setup` in process**, with `token_issued` carrying sig_v 3 and the
codecs. Addresses are integers, built on each side; no address literal is written.

    python3 docs/memory/evidence/cl_b4_2026-10-18/make_vectors_v3.py <out.json>
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

from common import KEY_HEX, LAN_SRC, OVERLAY_SRC, audit_lines, make_gate, si  # noqa: E402

CASES = [
    {"name": "lan-no-overlay", "device_id": "dev-0123456789abcdef", "nonce": "fixture-nonce-v3-1",
     "media_host": "0xC0A86439", "video_port": 48100, "audio_port": 48101, "overlay_host": None,
     "audio_codecs": ["opus"], "source": "lan"},
    {"name": "lan-with-overlay", "device_id": "dev-0123456789abcdef", "nonce": "fixture-nonce-v3-2",
     "media_host": "0xC0A86439", "video_port": 48100, "audio_port": 48101, "overlay_host": "0x64401235",
     "audio_codecs": ["opus"], "source": "lan"},
    {"name": "overlay-only", "device_id": "dev-fedcba9876543210", "nonce": "Zz-09_fixture-v3",
     "media_host": "0x64401235", "video_port": 50000, "audio_port": 50001, "overlay_host": "0x64401235",
     "audio_codecs": ["opus"], "source": "overlay"},
]


def ip(hexint):
    return "" if hexint is None else str(ipaddress.ip_address(int(hexint, 16)))


def client_body(case, media, overlay, sig):
    """`SessionProtocol.setupBodyV3`, field for field."""
    s = json.dumps
    return ("{" + '"device_id":' + s(case["device_id"]) + "," + '"nonce":' + s(case["nonce"]) + ","
            + '"media_host":' + s(media) + "," + '"video_port":' + str(case["video_port"]) + ","
            + '"audio_port":' + str(case["audio_port"]) + ","
            + ('"overlay_host":' + s(overlay) + "," if overlay else "")
            + '"audio_codecs":[' + ",".join(s(c) for c in case["audio_codecs"]) + "],"
            + '"sig_v":3,' + '"sig":' + s(sig) + "}")


def main() -> None:
    out = Path(sys.argv[1])
    vectors = []
    for case in CASES:
        media, overlay = ip(case["media_host"]), ip(case["overlay_host"])
        canonical = "\n".join([si.SETUP_CANON_V3, case["device_id"], case["nonce"], media, str(case["video_port"]),
                               str(case["audio_port"]), overlay, ",".join(case["audio_codecs"])])
        sig = hmac.new(bytes.fromhex(KEY_HEX), canonical.encode(), hashlib.sha256).hexdigest()
        g = make_gate()
        store = g.devices._file.path
        store.parent.mkdir(parents=True, exist_ok=True)
        store.write_text(json.dumps({"version": 1, "devices": [{
            "device_id": case["device_id"], "display_name": "fixture", "key_hex": KEY_HEX,
            "paired_at": "2026-10-18T00:00:00Z", "permissions": list(si.DEFAULT_PAIRED_PERMISSIONS),
            "permissions_v": 2}]}))
        g._nonces[case["nonce"]] = si._Nonce(g._clock() + 60)
        body_text = client_body(case, media, overlay, sig)
        source = {"lan": LAN_SRC, "overlay": OVERLAY_SRC}[case["source"]]
        status, resp = g._setup(json.loads(body_text), g.classifier.classify(source),
                                lambda st, reason, *a, **k: (st, {"reason": reason}))
        assert status == 200, (case["name"], resp)
        row = [a for a in audit_lines(g) if a["event"] == "token_issued"][-1]
        assert (row["sig_v"], row["audio_codecs"]) == (3, "opus"), row
        vectors.append({**case, "key_hex": KEY_HEX, "sig_v": 3,
                        "canonical_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                        "canonical_bytes": len(canonical.encode()), "sig": sig,
                        "body_sha256": hashlib.sha256(body_text.encode()).hexdigest(),
                        "host_accepted": True})
    out.write_text(json.dumps({"setup_canon_v3": si.SETUP_CANON_V3, "vectors": vectors}, indent=2) + "\n")


if __name__ == "__main__":
    main()
