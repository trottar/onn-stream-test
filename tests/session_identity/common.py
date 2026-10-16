"""G3-S1 test helpers: addresses built from integers (never written), a gate on
temporary stores, and the audit collection the record's redactor check reads."""

from __future__ import annotations

import atexit
import hashlib
import hmac
import ipaddress
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import session_identity as si  # noqa: E402

# In-memory only. No address literal appears in any test file or output.
LAN_NET = ipaddress.ip_network((0xC0A86400, 24))
LAN_SRC = str(LAN_NET[23])
LAN_DECLARED = str(LAN_NET[57])
OVERLAY_SRC = str(si.OVERLAY_NETWORKS[0][0x1234])
OVERLAY_DECLARED = str(si.OVERLAY_NETWORKS[0][0x1235])
UNKNOWN_SRC = str(ipaddress.ip_address(0xC6336405))
LOCAL_SRC = str(ipaddress.ip_address(0x7F000001))
ALL_ADDRESSES = (LAN_SRC, LAN_DECLARED, OVERLAY_SRC, OVERLAY_DECLARED, UNKNOWN_SRC)

KEY_HEX = hashlib.sha256(b"g3-s1 fixture device key").hexdigest() * 2   # 64 bytes

_TMP = Path(tempfile.mkdtemp(prefix="g3_s1_tests_"))
_AUDITS: list[Path] = []


class Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def make_gate(mode: str = "v2", clock: Clock | None = None) -> si.SessionGate:
    d = Path(tempfile.mkdtemp(dir=_TMP))
    audit = d / "logs" / "session_audit.jsonl"
    _AUDITS.append(audit)
    clock = clock or Clock()
    return si.SessionGate(
        mode=mode,
        config_dir=d / "config",
        audit_path=audit,
        classifier=si.RoutingClassifier(lan_reader=lambda: [LAN_NET], clock=clock),
        clock=clock,
        wall=lambda: 1_792_000_000.0,
    )


def sign(device_id: str, nonce: str, media_host: str, port, key_hex: str = KEY_HEX) -> str:
    canon = "\n".join([si.SETUP_CANON, device_id, nonce, media_host, str(port)])
    return hmac.new(bytes.fromhex(key_hex), canon.encode(), hashlib.sha256).hexdigest()


def pair(gate: si.SessionGate, source: str = LAN_SRC, name: str = "onn-fixture") -> str:
    status, opened = gate.session_route("POST", "/session/pairing/open", {}, None, LOCAL_SRC)
    assert status == 200, opened
    status, paired = gate.session_route(
        "POST", "/session/pair", {"code": opened["code"], "device_name": name, "key": KEY_HEX}, None, source)
    assert status == 200, paired
    return paired["device_id"]


def setup(gate: si.SessionGate, device_id: str, source: str = LAN_SRC, media_host: str = LAN_DECLARED,
          port=50000, key_hex: str = KEY_HEX):
    _, n = gate.session_route("POST", "/session/nonce", {}, None, source)
    body = {"device_id": device_id, "nonce": n["nonce"], "media_host": media_host, "video_port": port,
            "sig": sign(device_id, n["nonce"], media_host, port, key_hex)}
    return gate.session_route("POST", "/session/setup", body, None, source), body


def audit_lines(gate: si.SessionGate) -> list[dict]:
    if not gate.audit.path.exists():
        return []
    return [json.loads(line) for line in gate.audit.path.read_text().splitlines()]


def _collect() -> None:
    out = os.environ.get("G3_S1_AUDIT_OUT")
    if out:
        with open(out, "a", encoding="utf-8") as handle:
            for path in _AUDITS:
                if path.exists():
                    handle.write(path.read_text())


atexit.register(_collect)
