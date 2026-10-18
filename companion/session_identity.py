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

G3-S3 (`docs/memory/evidence/G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md`):
the setup canon v2 (the audio port and the overlay address signed), the
declared-port binding, a per-session media token, the range server's gate
(`MediaGate`, asking the companion's `/session/media-check` on loopback), and
`diagnostics` as a grantable permission (default on for a paired device).
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs, urlsplit

FLAG_ENV = "PRIVYHUB_SESSION_IDENTITY"
MODE_V2 = "v2"
SESSION_HEADER = "X-PrivyHub-Session"

PERMISSIONS = ("games", "tv", "vod", "diagnostics", "pairing-admin")
# G3-S3: `diagnostics` (the user's own device reporting its health) is on for a
# paired device. A record written since G3-S3 lists it (`permissions_v` 2) and
# can drop it; a record paired before G3-S3 (no `permissions_v`) is granted it.
DEFAULT_PAIRED_PERMISSIONS = ("games", "tv", "vod", "diagnostics")
PERMISSIONS_V = 2
MEDIA_PERMISSION = "vod"
MEDIA_TOKEN_PARAM = "media_token"
MEDIA_CHECK_PATH = "/session/media-check"
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
SETUP_CANON_V2 = "privyhub-session-setup-v2"
# CL-B4: `sig_v` 3 = v2 plus the client's declared audio codecs (G4-W2's `audio_codecs`).
SETUP_CANON_V3 = "privyhub-session-setup-v3"
AUDIO_CODECS_MAX = 8
_AUDIO_CODEC_RE = re.compile(r"[a-z0-9]{1,16}")

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
            "permissions_v": PERMISSIONS_V,
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


def device_permissions(device: Mapping[str, Any]) -> tuple[str, ...]:
    """The record's permissions; a pre-G3-S3 record (no `permissions_v`) also gets `diagnostics`."""
    listed = [p for p in device.get("permissions", []) if p in PERMISSIONS]
    if device.get("permissions_v") is None and "diagnostics" not in listed:
        listed.append("diagnostics")
    return tuple(listed)


def required_permission(path: str) -> str | None:
    if path.startswith("/plugins/games/") or path == "/diagnostics/client-health":
        return "games"
    if (
        path.startswith(("/plugins/tv_state/", "/plugins/epg/", "/plugins/iptv_org/", "/sources/"))
        or path in ("/sources", "/stop")
    ):
        return "tv"
    if path == "/status" or path.startswith("/diagnostics/"):
        return "diagnostics"     # G3-S3: grantable, default on for a paired device
    return None


@dataclass
class Session:
    client_id: str
    expires_at: float
    media_host: str | None = None
    video_port: int | None = None
    permissions: tuple[str, ...] = ()
    # G3-S3
    audio_port: int | None = None
    overlay_host: str | None = None
    media_token: str | None = None
    media_audited: tuple[bool, ...] = ()

    def target_for(self, routing: str, classify: Callable[[str], str]) -> str | None:
        """The declared address whose class matches the request's routing class."""
        want = ROUTING_LAN if routing == ROUTING_LOCAL else routing
        for host in (self.media_host, self.overlay_host):
            if host and classify(host) == want:
                return host
        return self.media_host


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
            sess.permissions = device_permissions(device)
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
                mismatch = self._port_mismatch(sess, parse_qs(query, keep_blank_values=True))
                if mismatch is not None:
                    return self._refuse(403, "endpoint-port-mismatch", "session_refused", routing,
                                        client_id=sess.client_id, path=path, port_kind=mismatch)
            return Decision(True, kind="session", client_id=sess.client_id,
                            media_host=sess.target_for(routing, self.classifier.classify))

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

    @staticmethod
    def _port_mismatch(sess: Session, query: dict[str, list[str]]) -> str | None:
        """G3-S3: the stream-start ports must be the signed ones. None = bound."""
        ports = query.get("port") or []
        if len(ports) != 1 or not ports[0].isdigit() or int(ports[0]) != sess.video_port:
            return "video"
        for name, signed in (("audio_port", sess.audio_port), ("controller_port", None)):
            if name in query:
                values = query[name]
                if (signed is None or len(values) != 1 or not values[0].isdigit()
                        or int(values[0]) != signed):
                    return name.split("_", 1)[0]
        return None

    # ---- the range server's check (G3-S3) ------------------------------------------

    def _session_by_media_token(self, media_token: str) -> str | None:
        with self._lock:
            for token, sess in self._tokens.items():
                if sess.media_token and hmac.compare_digest(sess.media_token.encode(), media_token.encode()):
                    return token
        return None

    def _media_check(self, method: str, body: dict[str, Any] | None, routing: str) -> tuple[int, dict[str, Any]]:
        """`POST /session/media-check` from the range server (loopback only)."""
        body = body if isinstance(body, dict) else {}
        forwarded = body.get("routing")
        fwd = forwarded if forwarded in (ROUTING_LAN, ROUTING_OVERLAY, ROUTING_UNKNOWN) else ROUTING_UNKNOWN
        path = urlsplit(str(body.get("path") or "/")).path[:256]

        def refused(status: int, reason: str, event: str = "media_refused", at: str = fwd, **f: Any):
            self._refuse(status, reason, event, at, path=path, **f)
            return status, {"ok": False, "error": "session refused", "reason": reason}

        if routing != ROUTING_LOCAL:
            return refused(403, "host-local-only", at=routing)
        if method != "POST":
            return 405, {"ok": False, "error": "POST only"}
        if self.mode != MODE_V2:
            return refused(401, "identity-flag-unknown")

        token = str(body.get("token") or "").strip() or None
        media_token = str(body.get("media_token") or "").strip() or None
        used_media_token = token is None and media_token is not None
        if used_media_token:
            token = self._session_by_media_token(media_token)
            if token is None:
                return refused(401, "media-token-unknown", media_token_used=True)
        if token is None:
            if fwd == ROUTING_LAN:
                if self.settings.legacy_unpaired_lan():
                    return 200, {"ok": True, "kind": "legacy", "client_id": LEGACY_CLIENT}
                return refused(401, "legacy-disabled", "legacy_refused")
            reason = "legacy-overlay" if fwd == ROUTING_OVERLAY else "legacy-unknown-network"
            return refused(401, reason, "legacy_refused")

        sess, refusal = self._session_for(token, fwd, path)
        if refusal is not None:
            return refusal.status, {"ok": False, "error": "session refused", "reason": refusal.reason}
        assert sess is not None
        if sess.client_id != LEGACY_CLIENT and MEDIA_PERMISSION not in sess.permissions:
            return refused(403, "permission-denied", "permission_denied", client_id=sess.client_id,
                           permission=MEDIA_PERMISSION, media_token_used=used_media_token)
        with self._lock:
            first = used_media_token not in sess.media_audited
            if first:
                sess.media_audited = sess.media_audited + (used_media_token,)
        if first:
            self.audit.write("media_session", client_id=sess.client_id, token_ref=token_ref(token),
                             media_token_used=used_media_token, path=path, **self._evidence(fwd))
        kind = "legacy" if sess.client_id == LEGACY_CLIENT else "session"
        return 200, {"ok": True, "kind": kind, "client_id": sess.client_id}

    # ---- /session/* ------------------------------------------------------------

    def session_route(self, method: str, path: str, body: dict[str, Any] | None,
                      token: str | None, source: str) -> tuple[int, dict[str, Any]]:
        routing = self.classifier.classify(source)

        def refused(status: int, reason: str, event: str = "session_refused", **f: Any):
            self._refuse(status, reason, event, routing, path=path, **f)
            return status, {"ok": False, "error": "session refused", "reason": reason}

        if path == MEDIA_CHECK_PATH:
            return self._media_check(method, body, routing)

        if self.mode != MODE_V2 and not (routing == ROUTING_LOCAL and path == "/session/status"):
            return refused(401, "identity-flag-unknown")

        if path == "/session/status":
            if method != "GET":
                return 405, {"ok": False, "error": "GET only"}
            if routing != ROUTING_LOCAL:
                return refused(403, "host-local-only")
            with self._lock:
                now = self._clock()
                live = [s for s in self._tokens.values() if s.expires_at > now]
                active = len(live)
                window = self._pairing is not None and self._pairing.expires_at > now
                # G3-S3: each live session's permission set and whether a media
                # token is live (a boolean; never the token).
                sessions = [{
                    "client_id": s.client_id,
                    "kind": "legacy" if s.client_id == LEGACY_CLIENT else "session",
                    "permissions": list(s.permissions),
                    "media_token_live": bool(s.media_token),
                    "expires_in_s": int(s.expires_at - now),
                } for s in live]
            return 200, {
                "ok": True, "mode": self.mode, "paired_devices": self.devices.count(),
                "active_sessions": active, "legacy_unpaired_lan": self.settings.legacy_unpaired_lan(),
                "pairing_window_open": window,
                "permissions_known": list(PERMISSIONS),
                "default_paired_permissions": list(DEFAULT_PAIRED_PERMISSIONS),
                "sessions": sessions,
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
        # G3-S3: `sig_v` 2 signs the audio port and the overlay address too.
        v2 = body.get("sig_v") == 2 and not isinstance(body.get("sig_v"), bool)
        # CL-B4: `sig_v` 3 signs v2's fields and the declared audio codecs (required).
        v3 = body.get("sig_v") == 3 and not isinstance(body.get("sig_v"), bool)
        audio_raw = body.get("audio_port") if (v2 or v3) else None
        overlay_raw = str(body.get("overlay_host") or "") if (v2 or v3) else ""

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

        codecs_raw = body.get("audio_codecs") if v3 else None
        if v3 and not (isinstance(codecs_raw, list) and 1 <= len(codecs_raw) <= AUDIO_CODECS_MAX
                       and all(isinstance(c, str) and _AUDIO_CODEC_RE.fullmatch(c) for c in codecs_raw)):
            return refused(403, "audio-codecs-invalid", client_id=device_id)
        if v3:
            canonical = "\n".join([SETUP_CANON_V3, device_id, nonce, media_host, str(port_raw),
                                   "" if audio_raw is None else str(audio_raw), overlay_raw,
                                   ",".join(codecs_raw)])
        elif v2:
            canonical = "\n".join([SETUP_CANON_V2, device_id, nonce, media_host, str(port_raw),
                                   "" if audio_raw is None else str(audio_raw), overlay_raw])
        else:
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
        audio_port: int | None = None
        if audio_raw is not None:
            if isinstance(audio_raw, bool) or not isinstance(audio_raw, int) or not (1024 <= audio_raw <= 65535):
                return refused(403, "endpoint-invalid", client_id=device_id)
            audio_port = audio_raw
        overlay_host: str | None = None
        if overlay_raw:
            try:
                ov = ipaddress.ip_address(overlay_raw)
            except ValueError:
                return refused(403, "endpoint-invalid", client_id=device_id)
            if ov.version != 4 or self.classifier.classify(str(ov)) != ROUTING_OVERLAY:
                return refused(403, "endpoint-invalid", client_id=device_id)
            overlay_host = str(ov)
        want = ROUTING_LAN if routing == ROUTING_LOCAL else routing
        declared = [self.classifier.classify(str(host))]
        if overlay_host:
            declared.append(ROUTING_OVERLAY)
        if want not in declared:
            return refused(403, "endpoint-class-mismatch", client_id=device_id)

        permissions = device_permissions(device)
        media_token = secrets.token_urlsafe(24)
        token = self._issue_token(Session(device_id, self._clock() + TOKEN_TTL_S,
                                          media_host=str(host), video_port=port, permissions=permissions,
                                          audio_port=audio_port, overlay_host=overlay_host,
                                          media_token=media_token))
        extra: dict[str, Any] = {"audio_codecs": ",".join(codecs_raw)} if v3 else {}
        self.audit.write("token_issued", client_id=device_id, token_ref=token_ref(token),
                         expires_in_s=int(TOKEN_TTL_S), permissions=",".join(permissions),
                         sig_v=3 if v3 else 2 if v2 else 1, overlay_declared=overlay_host is not None,
                         media_token_issued=True, **extra, **self._evidence(routing))
        return 200, {"ok": True, "token": token, "expires_in_s": int(TOKEN_TTL_S),
                     "client_id": device_id, "permissions": list(permissions),
                     "media_token": media_token}

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


class MediaGate:
    """G3-S3: the range server's gate (a separate process; the tokens live in
    the companion). Loopback → allowed; the LAN without a token → today's
    legacy path (if `legacy_unpaired_lan`); anything else → the companion's
    `/session/media-check` on loopback decides and audits. The media token
    is never logged: the range server's own log lines mask it."""

    def __init__(
        self,
        mode: str,
        config_dir: Path,
        audit_path: Path,
        control_port: int = 8765,
        classifier: RoutingClassifier | None = None,
        transport: Callable[[str, bytes], tuple[int, bytes]] | None = None,
        wall: Callable[[], float] = time.time,
    ) -> None:
        self.mode = mode
        self.settings = Settings(config_dir / "session_identity.json")
        self.audit = AuditLog(audit_path, wall=wall)
        self.classifier = classifier or RoutingClassifier()
        loopback = str(ipaddress.ip_address(0x7F000001))
        self.check_url = f"http://{loopback}:{int(control_port)}{MEDIA_CHECK_PATH}"
        self._transport = transport or self._post

    @staticmethod
    def _post(url: str, body: bytes) -> tuple[int, bytes]:
        import urllib.error
        import urllib.request
        req = urllib.request.Request(url, data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status, resp.read(BODY_MAX_BYTES)
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(BODY_MAX_BYTES)

    def decide(self, source: str, request_path: str, header_token: str | None) -> tuple[int, dict[str, Any]] | None:
        """None = serve the request as today; else (status, refusal body)."""
        routing = self.classifier.classify(source)
        if routing == ROUTING_LOCAL:
            return None
        split = urlsplit(request_path)
        media_token = ((parse_qs(split.query).get(MEDIA_TOKEN_PARAM) or [""])[0]).strip() or None
        token = (header_token or "").strip() or None
        if (token is None and media_token is None and routing == ROUTING_LAN
                and self.mode == MODE_V2 and self.settings.legacy_unpaired_lan()):
            return None
        body = {"routing": routing, "path": split.path}
        if token is not None:
            body["token"] = token
        elif media_token is not None:
            body["media_token"] = media_token
        try:
            status, raw = self._transport(self.check_url, json.dumps(body).encode("utf-8"))
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            self.audit.write("media_refused", reason="identity-unavailable", path=split.path[:256],
                             media_token_used=token is None and media_token is not None,
                             routing_evidence=routing, host_local=False)
            return 503, {"ok": False, "error": "session refused", "reason": "identity-unavailable"}
        if status == 200 and isinstance(payload, dict) and payload.get("ok") is True:
            return None
        reason = payload.get("reason") if isinstance(payload, dict) else None
        return (status if status in (401, 403) else 503), {
            "ok": False, "error": "session refused", "reason": str(reason or "identity-unavailable")}

    @staticmethod
    def mask(text: str) -> str:
        """The request line with the media token's value masked."""
        if MEDIA_TOKEN_PARAM + "=" not in text:
            return text
        out, rest = [], text
        key = MEDIA_TOKEN_PARAM + "="
        while key in rest:
            head, _, tail = rest.partition(key)
            end = min([i for i in (tail.find("&"), tail.find(" "), tail.find("#")) if i >= 0] or [len(tail)])
            out.append(head + key + "<redacted>")
            rest = tail[end:]
        return "".join(out) + rest

    def refuse(self, handler: Any) -> bool:
        """True when the gate answered the request (a refusal)."""
        decision = self.decide(str(handler.client_address[0]), handler.path,
                               handler.headers.get(SESSION_HEADER))
        if decision is None:
            return False
        status, payload = decision
        data = json.dumps(payload, indent=2).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        if handler.command != "HEAD":
            handler.wfile.write(data)
        return True


def media_gate_from_environ(environ: Mapping[str, str], project_root: Path) -> MediaGate | None:
    raw = environ.get(FLAG_ENV)
    if raw is None or not raw.strip():
        return None
    return MediaGate(
        mode=raw.strip().lower(),
        config_dir=Path.home() / ".config" / "privyhub",
        audit_path=Path(project_root) / "logs" / "session_audit.jsonl",
    )


def gate_from_environ(environ: Mapping[str, str], project_root: Path) -> SessionGate | None:
    raw = environ.get(FLAG_ENV)
    if raw is None or not raw.strip():
        return None
    return SessionGate(
        mode=raw.strip().lower(),
        config_dir=Path.home() / ".config" / "privyhub",
        audit_path=Path(project_root) / "logs" / "session_audit.jsonl",
    )
