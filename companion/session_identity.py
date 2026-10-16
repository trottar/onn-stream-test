"""G3-S1: session identity and authorization, host side (ROADMAP §G3).

Behind `PRIVYHUB_SESSION_IDENTITY=v2`. **Absent = today**: the companion
never imports this module, reads no store, writes no audit line and adds no
header. The design is §1 of
`docs/memory/evidence/G3_S1_SESSION_IDENTITY_HOST_SIDE_2026-10-15.md`.

The rule: a request's source address is routing evidence, never identity;
overlay membership is transport, never authorization; setup fails closed;
every decision that matters is audited, with no address in the audit.

- Client identity: a device paired once on the home LAN (a 120-s window the
  host opens, a one-time code), stored in `~/.config/privyhub/paired_devices.json`
  (0600, outside git): id, name, HMAC key, permissions — no address.
- Session identity: a nonce-bound, HMAC-SHA256-signed setup issues a token
  with an expiry; every call carries it (`X-PrivyHub-Session`).
- Declared endpoints: the media host comes from the setup, not the source.
- Authorization: per-device permissions (games, tv, vod, pairing-admin);
  unknown → denied.
- Legacy: today's client (no token) is accepted only from the hub's own LAN
  with `legacy_unpaired_lan` on, as `legacy-lan`, exactly as today; never
  over the overlay. The hub itself (loopback) is `host-local`.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs

FLAG_ENV = "PRIVYHUB_SESSION_IDENTITY"
MODE_V2 = "v2"
SESSION_HEADER = "X-PrivyHub-Session"

PERMISSIONS = ("games", "tv", "vod", "pairing-admin")
DEFAULT_PAIRED_PERMISSIONS = ("games", "tv", "vod")
LEGACY_CLIENT = "legacy-lan"
HOST_LOCAL_CLIENT = "host-local"

PAIRING_WINDOW_S = 120.0
PAIRING_MAX_ATTEMPTS = 5
NONCE_TTL_S = 60.0
NONCE_MAX = 256
TOKEN_TTL_S = 8 * 3600.0
KEY_MIN_HEX = 64          # 32 bytes
KEY_MAX_HEX = 256
BODY_MAX_BYTES = 16_384
SETUP_CANON = "privyhub-session-setup-v1"

# The session-setup actions: a legacy token is issued and audited on these.
SETUP_PATHS = frozenset({
    "/plugins/games/launch",
    "/plugins/games/native-stream-start",
    "/plugins/games/recovery-resume",
    "/plugins/games/recovery-copy",
})

# The overlay's address space, built from integers (no literal in source):
# the shared CGNAT block (Tailscale's IPv4 range) and Tailscale's IPv6 ULA.
OVERLAY_NETWORKS = (
    ipaddress.ip_network((0x64400000, 10)),
    ipaddress.ip_network((0xFD7A115CA1E0 << 80, 48)),
)

ROUTING_LOCAL = "local"
ROUTING_LAN = "lan"
ROUTING_OVERLAY = "overlay"
ROUTING_UNKNOWN = "unknown"


# --------------------------------------------------------------------------
# Routing evidence

def read_onlink_networks(route_path: Path = Path("/proc/net/route")) -> list[ipaddress.IPv4Network]:
    """The hub's own on-link IPv4 subnets (no gateway), overlay interfaces excluded."""
    nets: list[ipaddress.IPv4Network] = []
    try:
        lines = route_path.read_text().splitlines()[1:]
    except OSError:
        return nets
    for line in lines:
        parts = line.split()
        if len(parts) < 8:
            continue
        iface, dest, gateway, mask = parts[0], parts[1], parts[2], parts[7]
        if gateway != "00000000" or dest == "00000000":
            continue
        if iface == "lo" or iface.startswith(("tailscale", "wg")):
            continue
        try:
            d = int.from_bytes(bytes.fromhex(dest), "little")
            m = int.from_bytes(bytes.fromhex(mask), "little")
            nets.append(ipaddress.ip_network((d, bin(m).count("1")), strict=False))
        except ValueError:
            continue
    return nets


class RoutingClassifier:
    REFRESH_S = 60.0

    def __init__(
        self,
        lan_reader: Callable[[], list[Any]] = read_onlink_networks,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._lan_reader = lan_reader
        self._clock = clock
        self._lan: list[Any] = []
        self._read_at: float | None = None
        self._lock = threading.Lock()

    def _lan_networks(self) -> list[Any]:
        with self._lock:
            now = self._clock()
            if self._read_at is None or now - self._read_at >= self.REFRESH_S:
                self._lan = list(self._lan_reader())
                self._read_at = now
            return self._lan

    def classify(self, source: str) -> str:
        try:
            ip = ipaddress.ip_address(str(source).split("%", 1)[0])
        except ValueError:
            return ROUTING_UNKNOWN
        if getattr(ip, "ipv4_mapped", None):
            ip = ip.ipv4_mapped
        if ip.is_loopback:
            return ROUTING_LOCAL
        if any(ip.version == n.version and ip in n for n in OVERLAY_NETWORKS):
            return ROUTING_OVERLAY
        if any(ip.version == n.version and ip in n for n in self._lan_networks()):
            return ROUTING_LAN
        return ROUTING_UNKNOWN


# --------------------------------------------------------------------------
# Stores

def _atomic_write_json(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=2)
        handle.write("\n")
    os.replace(tmp, path)


class _JsonFile:
    """A JSON file re-read when its mtime changes; a broken file reads as `None`."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._mtime: tuple[int, int] | None = None
        self._doc: dict[str, Any] | None = None
        self._missing = True

    def read(self) -> tuple[bool, dict[str, Any] | None]:
        """(present, doc). A present but unreadable file returns (True, None)."""
        try:
            st = self.path.stat()
            mtime = (st.st_mtime_ns, st.st_size)
        except OSError:
            self._mtime, self._doc, self._missing = None, None, True
            return False, None
        if mtime != self._mtime:
            self._mtime, self._missing = mtime, False
            try:
                doc = json.loads(self.path.read_text(encoding="utf-8"))
                self._doc = doc if isinstance(doc, dict) else None
            except (OSError, ValueError):
                self._doc = None
        return True, self._doc


class DeviceStore:
    def __init__(self, path: Path) -> None:
        self._file = _JsonFile(path)

    def _devices(self) -> list[dict[str, Any]]:
        present, doc = self._file.read()
        if not present or doc is None:
            return []  # absent: none paired; broken: fail closed, none trusted
        devices = doc.get("devices")
        return [d for d in devices if isinstance(d, dict)] if isinstance(devices, list) else []

    def get(self, device_id: str) -> dict[str, Any] | None:
        for d in self._devices():
            if d.get("device_id") == device_id:
                return d
        return None

    def count(self) -> int:
        return len(self._devices())

    def add(self, display_name: str, key_hex: str, permissions: tuple[str, ...], paired_at: str) -> dict[str, Any]:
        devices = self._devices()
        device = {
            "device_id": "dev-" + secrets.token_hex(8),
            "display_name": display_name,
            "key_hex": key_hex,
            "paired_at": paired_at,
            "permissions": list(permissions),
        }
        devices.append(device)
        _atomic_write_json(self._file.path, {"version": 1, "devices": devices})
        return device


class Settings:
    def __init__(self, path: Path) -> None:
        self._file = _JsonFile(path)

    def legacy_unpaired_lan(self) -> bool:
        present, doc = self._file.read()
        if not present:
            return True          # the transition default
        if doc is None:
            return False         # a broken settings file fails closed
        value = doc.get("legacy_unpaired_lan", True)
        return value is True


class AuditLog:
    def __init__(self, path: Path, wall: Callable[[], float] = time.time) -> None:
        self.path = path
        self._wall = wall
        self._lock = threading.Lock()

    def write(self, event: str, **fields: Any) -> None:
        line = {
            "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._wall())),
            "event": event,
            **{k: v for k, v in fields.items() if v is not None},
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, sort_keys=True) + "\n")


# --------------------------------------------------------------------------
# The gate

def token_ref(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]


def required_permission(path: str) -> str | None:
    if path.startswith("/plugins/games/") or path == "/diagnostics/client-health":
        return "games"
    if (
        path.startswith(("/plugins/tv_state/", "/plugins/epg/", "/plugins/iptv_org/", "/sources/"))
        or path in ("/sources", "/stop")
    ):
        return "tv"
    if path == "/status" or path.startswith("/diagnostics/"):
        return "diagnostics"     # not grantable in v1: a token session is denied
    return None


@dataclass
class Session:
    client_id: str
    expires_at: float
    media_host: str | None = None
    video_port: int | None = None
    permissions: tuple[str, ...] = ()


@dataclass
class Decision:
    allowed: bool
    status: int = 200
    reason: str | None = None
    kind: str | None = None          # host-local | legacy | session
    client_id: str | None = None
    media_host: str | None = None
    issued_token: str | None = None


@dataclass
class _Pairing:
    code: str
    expires_at: float
    attempts: int = 0


@dataclass
class _Nonce:
    expires_at: float
    used: bool = False


class SessionGate:
    def __init__(
        self,
        mode: str,
        config_dir: Path,
        audit_path: Path,
        classifier: RoutingClassifier | None = None,
        clock: Callable[[], float] = time.monotonic,
        wall: Callable[[], float] = time.time,
    ) -> None:
        self.mode = mode
        self.devices = DeviceStore(config_dir / "paired_devices.json")
        self.settings = Settings(config_dir / "session_identity.json")
        self.audit = AuditLog(audit_path, wall=wall)
        self.classifier = classifier or RoutingClassifier()
        self._clock = clock
        self._wall = wall
        self._lock = threading.RLock()
        self._tokens: dict[str, Session] = {}
        self._nonces: dict[str, _Nonce] = {}
        self._pairing: _Pairing | None = None

    # ---- helpers -----------------------------------------------------------

    def _evidence(self, routing: str) -> dict[str, Any]:
        return {
            "routing_evidence": ROUTING_LAN if routing == ROUTING_LOCAL else routing,
            "host_local": routing == ROUTING_LOCAL,
        }

    def _refuse(self, status: int, reason: str, event: str, routing: str, **fields: Any) -> Decision:
        self.audit.write(event, reason=reason, **self._evidence(routing), **fields)
        return Decision(False, status, reason)

    def _session_for(self, token: str, routing: str, path: str) -> tuple[Session | None, Decision | None]:
        with self._lock:
            sess = self._tokens.get(token)
            if sess is None:
                return None, self._refuse(401, "token-unknown", "session_refused", routing, path=path)
            if self._clock() >= sess.expires_at:
                del self._tokens[token]
                return None, self._refuse(401, "token-expired", "token_expired", routing,
                                          client_id=sess.client_id, token_ref=token_ref(token), path=path)
            if sess.client_id == LEGACY_CLIENT:
                if routing != ROUTING_LAN or not self.settings.legacy_unpaired_lan():
                    reason = "legacy-overlay" if routing == ROUTING_OVERLAY else (
                        "legacy-disabled" if routing == ROUTING_LAN else "legacy-unknown-network")
                    return None, self._refuse(401, reason, "legacy_refused", routing, path=path)
                return sess, None
            device = self.devices.get(sess.client_id)
            if device is None:
                self._tokens = {t: s for t, s in self._tokens.items() if s.client_id != sess.client_id}
                return None, self._refuse(401, "device-revoked", "session_refused", routing,
                                          client_id=sess.client_id, path=path)
            sess.permissions = tuple(p for p in device.get("permissions", []) if p in PERMISSIONS)
            return sess, None

    def _issue_token(self, sess: Session) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            now = self._clock()
            self._tokens = {t: s for t, s in self._tokens.items() if s.expires_at > now}
            self._tokens[token] = sess
        return token

    # ---- authorization of ordinary routes ------------------------------------

    def authorize(self, method: str, path: str, query: str, token: str | None, source: str) -> Decision:
        routing = self.classifier.classify(source)
        if self.mode != MODE_V2:
            if routing == ROUTING_LOCAL:
                return Decision(True, kind="host-local", client_id=HOST_LOCAL_CLIENT)
            return self._refuse(401, "identity-flag-unknown", "session_refused", routing, path=path)

        if token:
            sess, refusal = self._session_for(token, routing, path)
            if refusal is not None:
                return refusal
            assert sess is not None
            if sess.client_id == LEGACY_CLIENT:
                return Decision(True, kind="legacy", client_id=LEGACY_CLIENT)
            permission = required_permission(path)
            if permission is None or permission not in PERMISSIONS:
                return self._refuse(403, "permission-unknown", "permission_denied", routing,
                                    client_id=sess.client_id, path=path, permission=permission)
            if permission not in sess.permissions:
                return self._refuse(403, "permission-denied", "permission_denied", routing,
                                    client_id=sess.client_id, path=path, permission=permission)
            if path == "/plugins/games/native-stream-start":
                port = (parse_qs(query).get("port") or [""])[0]
                if not port.isdigit() or int(port) != sess.video_port:
                    return self._refuse(403, "endpoint-port-mismatch", "session_refused", routing,
                                        client_id=sess.client_id, path=path)
            return Decision(True, kind="session", client_id=sess.client_id, media_host=sess.media_host)

        if routing == ROUTING_LOCAL:
            if path in SETUP_PATHS:
                self.audit.write("host_local_setup", client_id=HOST_LOCAL_CLIENT, path=path,
                                 **self._evidence(routing))
            return Decision(True, kind="host-local", client_id=HOST_LOCAL_CLIENT)
        if routing == ROUTING_LAN:
            if not self.settings.legacy_unpaired_lan():
                return self._refuse(401, "legacy-disabled", "legacy_refused", routing, path=path)
            issued = None
            if path in SETUP_PATHS:
                issued = self._issue_token(Session(LEGACY_CLIENT, self._clock() + TOKEN_TTL_S,
                                                   permissions=DEFAULT_PAIRED_PERMISSIONS))
                self.audit.write("legacy_setup", client_id=LEGACY_CLIENT, path=path,
                                 token_ref=token_ref(issued), **self._evidence(routing))
            return Decision(True, kind="legacy", client_id=LEGACY_CLIENT, issued_token=issued)
        reason = "legacy-overlay" if routing == ROUTING_OVERLAY else "legacy-unknown-network"
        return self._refuse(401, reason, "legacy_refused", routing, path=path)

    # ---- /session/* ------------------------------------------------------------

    def session_route(self, method: str, path: str, body: dict[str, Any] | None,
                      token: str | None, source: str) -> tuple[int, dict[str, Any]]:
        routing = self.classifier.classify(source)

        def refused(status: int, reason: str, event: str = "session_refused", **f: Any):
            self._refuse(status, reason, event, routing, path=path, **f)
            return status, {"ok": False, "error": "session refused", "reason": reason}

        if self.mode != MODE_V2 and not (routing == ROUTING_LOCAL and path == "/session/status"):
            return refused(401, "identity-flag-unknown")

        if path == "/session/status":
            if method != "GET":
                return 405, {"ok": False, "error": "GET only"}
            if routing != ROUTING_LOCAL:
                return refused(403, "host-local-only")
            with self._lock:
                now = self._clock()
                active = sum(1 for s in self._tokens.values() if s.expires_at > now)
                window = self._pairing is not None and self._pairing.expires_at > now
            return 200, {
                "ok": True, "mode": self.mode, "paired_devices": self.devices.count(),
                "active_sessions": active, "legacy_unpaired_lan": self.settings.legacy_unpaired_lan(),
                "pairing_window_open": window,
            }

        if method != "POST":
            return 405, {"ok": False, "error": "POST only"}
        if routing == ROUTING_UNKNOWN:
            return refused(401, "network-unknown")
        body = body if isinstance(body, dict) else {}

        if path in ("/session/pairing/open", "/session/pairing/close"):
            allowed = routing == ROUTING_LOCAL
            if not allowed and token:
                sess, refusal = self._session_for(token, routing, path)
                if refusal is not None:
                    return refusal.status, {"ok": False, "error": "session refused", "reason": refusal.reason}
                allowed = sess is not None and "pairing-admin" in sess.permissions
            if not allowed:
                return refused(403, "pairing-admin-required", "pairing_refused")
            with self._lock:
                if path.endswith("/close"):
                    self._pairing = None
                    self.audit.write("pairing_close", **self._evidence(routing))
                    return 200, {"ok": True, "pairing_window_open": False}
                code = f"{secrets.randbelow(10**6):06d}"
                self._pairing = _Pairing(code, self._clock() + PAIRING_WINDOW_S)
            self.audit.write("pairing_open", window_s=int(PAIRING_WINDOW_S), **self._evidence(routing))
            return 200, {"ok": True, "code": code, "expires_in_s": int(PAIRING_WINDOW_S)}

        if path == "/session/pair":
            if routing not in (ROUTING_LAN, ROUTING_LOCAL):
                return refused(403, "pairing-not-lan", "pairing_refused")
            name = str(body.get("device_name") or "").strip()
            name = "".join(ch for ch in name if ch.isprintable())[:64]
            key = str(body.get("key") or "").strip().lower()
            code = str(body.get("code") or "")
            with self._lock:
                window = self._pairing
                if window is None or self._clock() >= window.expires_at:
                    self._pairing = None
                    return refused(403, "pairing-closed", "pairing_refused")
                window.attempts += 1
                if not hmac.compare_digest(code.encode(), window.code.encode()):
                    if window.attempts >= PAIRING_MAX_ATTEMPTS:
                        self._pairing = None
                        return refused(403, "pairing-attempts-exhausted", "pairing_refused")
                    return refused(403, "pairing-bad-code", "pairing_refused")
                if not name or not (KEY_MIN_HEX <= len(key) <= KEY_MAX_HEX) or any(
                        c not in "0123456789abcdef" for c in key) or len(key) % 2:
                    return refused(400, "pairing-bad-request", "pairing_refused")
                self._pairing = None
                device = self.devices.add(
                    name, key, DEFAULT_PAIRED_PERMISSIONS,
                    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._wall())),
                )
            self.audit.write("pairing_ok", client_id=device["device_id"],
                             permissions=",".join(device["permissions"]), **self._evidence(routing))
            return 200, {"ok": True, "device_id": device["device_id"], "permissions": device["permissions"]}

        if path == "/session/nonce":
            nonce = secrets.token_urlsafe(24)
            with self._lock:
                now = self._clock()
                self._nonces = {n: v for n, v in self._nonces.items() if v.expires_at > now}
                while len(self._nonces) >= NONCE_MAX:
                    self._nonces.pop(next(iter(self._nonces)))
                self._nonces[nonce] = _Nonce(now + NONCE_TTL_S)
            return 200, {"ok": True, "nonce": nonce, "expires_in_s": int(NONCE_TTL_S)}

        if path == "/session/setup":
            return self._setup(body, routing, refused)

        if path == "/session/end":
            if not token:
                return refused(401, "token-missing")
            with self._lock:
                sess = self._tokens.pop(token, None)
            if sess is None:
                return refused(401, "token-unknown")
            self.audit.write("token_end", client_id=sess.client_id, token_ref=token_ref(token),
                             **self._evidence(routing))
            return 200, {"ok": True}

        return 404, {"ok": False, "error": "Not found"}

    def _setup(self, body: dict[str, Any], routing: str, refused) -> tuple[int, dict[str, Any]]:
        device_id = str(body.get("device_id") or "")
        nonce = str(body.get("nonce") or "")
        media_host = str(body.get("media_host") or "")
        port_raw = body.get("video_port")
        sig = str(body.get("sig") or "").lower()

        device = self.devices.get(device_id) if device_id else None
        if device is None:
            return refused(401, "unknown-device")
        with self._lock:
            entry = self._nonces.get(nonce)
            now = self._clock()
            if entry is None:
                return refused(401, "nonce-unknown", client_id=device_id)
            if now >= entry.expires_at:
                self._nonces.pop(nonce, None)
                return refused(401, "nonce-expired", client_id=device_id)
            if entry.used:
                return refused(401, "nonce-replayed", client_id=device_id)
            entry.used = True     # spent whatever the outcome below

        canonical = "\n".join([SETUP_CANON, device_id, nonce, media_host, str(port_raw)])
        try:
            key = bytes.fromhex(str(device.get("key_hex") or ""))
        except ValueError:
            key = b""
        expected = hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest() if key else ""
        if not key or not hmac.compare_digest(sig.encode(), expected.encode()):
            return refused(401, "bad-signature", client_id=device_id)

        try:
            host = ipaddress.ip_address(media_host)
            port = int(port_raw)
        except (ValueError, TypeError):
            return refused(403, "endpoint-invalid", client_id=device_id)
        if (host.version != 4 or host.is_loopback or host.is_unspecified or host.is_multicast
                or not (1024 <= port <= 65535) or isinstance(port_raw, bool)):
            return refused(403, "endpoint-invalid", client_id=device_id)
        declared = self.classifier.classify(str(host))
        if not (declared == routing or (routing == ROUTING_LOCAL and declared == ROUTING_LAN)):
            return refused(403, "endpoint-class-mismatch", client_id=device_id)

        permissions = tuple(p for p in device.get("permissions", []) if p in PERMISSIONS)
        token = self._issue_token(Session(device_id, self._clock() + TOKEN_TTL_S,
                                          media_host=str(host), video_port=port, permissions=permissions))
        self.audit.write("token_issued", client_id=device_id, token_ref=token_ref(token),
                         expires_in_s=int(TOKEN_TTL_S), permissions=",".join(permissions),
                         **self._evidence(routing))
        return 200, {"ok": True, "token": token, "expires_in_s": int(TOKEN_TTL_S),
                     "client_id": device_id, "permissions": list(permissions)}

    # ---- the HTTP glue ------------------------------------------------------------

    def intercept(self, handler: Any, method: str, parsed: Any) -> bool:
        """True when the gate answered (a /session/* route or a refusal)."""
        handler._session_decision = None
        handler._session_headers = []
        source = str(handler.client_address[0])
        token = (handler.headers.get(SESSION_HEADER) or "").strip() or None
        path = parsed.path

        if path.startswith("/session/"):
            body: dict[str, Any] | None = None
            if method == "POST":
                try:
                    length = int(handler.headers.get("Content-Length") or 0)
                except ValueError:
                    length = -1
                if length < 0 or length > BODY_MAX_BYTES:
                    handler._send_json(400, {"ok": False, "error": "session refused", "reason": "bad-request"})
                    return True
                raw = handler.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw.decode("utf-8")) if raw else {}
                except (UnicodeDecodeError, ValueError):
                    handler._send_json(400, {"ok": False, "error": "session refused", "reason": "bad-request"})
                    return True
            status, payload = self.session_route(method, path, body, token, source)
            handler._send_json(status, payload)
            return True

        decision = self.authorize(method, path, parsed.query, token, source)
        if not decision.allowed:
            handler._send_json(decision.status, {"ok": False, "error": "session refused",
                                                 "reason": decision.reason})
            return True
        handler._session_decision = decision
        if decision.issued_token:
            handler._session_headers = [(SESSION_HEADER, decision.issued_token)]
        return False

    @staticmethod
    def client_target(handler: Any) -> str:
        """The declared media host for a token session; else the source (today)."""
        decision = getattr(handler, "_session_decision", None)
        if decision is not None and decision.kind == "session" and decision.media_host:
            return decision.media_host
        return str(handler.client_address[0])


def gate_from_environ(environ: Mapping[str, str], project_root: Path) -> SessionGate | None:
    raw = environ.get(FLAG_ENV)
    if raw is None or not raw.strip():
        return None
    return SessionGate(
        mode=raw.strip().lower(),
        config_dir=Path.home() / ".config" / "privyhub",
        audit_path=Path(project_root) / "logs" / "session_audit.jsonl",
    )
