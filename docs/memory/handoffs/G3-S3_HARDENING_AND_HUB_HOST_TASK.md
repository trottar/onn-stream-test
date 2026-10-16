---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G3-S3, session B, software only: the four things G4-P1 and CL-B2 found standing between the LAN-verified identity model and a real off-site session. Host: (1) the stream-start port bound to the signed declared port; (2) the range server gated over the overlay; (3) TV-sync, EPG and diagnostics calls gated by permission with the token. Client: (4) a hub-host setting (the tailnet name) so the app can reach the hub off-site, and the token on every call. All behind the existing flags (`PRIVYHUB_SESSION_IDENTITY=v2`, the client's `identity_v2`); absent = today. Built and tested; the APK not installed (CL-B3). Nothing adopted; nothing committed
---

# G3-S3 — hardening, and the hub-host setting

Read first: `CL_B2_…` §2 (the declared-port note), `G4_P1_…` (blockers
and findings 8-9 of `SESSION_B_DONE_2026-10-16B.md`: the range server on
port 8000 ungated over the overlay; TV-sync / EPG / diagnostics carry no
token), `G3_S1_…` §1 (permissions, routing evidence classes),
`g1_s1_2026-10-15/source_address_audit.md` (every call), `G3_S2_…` (the
client's declared endpoints — which interface addresses it declares),
`companion/session_identity.py`, the range server's code (what serves
VOD / media byte ranges, how the client fetches them — a player that
cannot send headers needs a query token), the client's hub discovery
(how it finds the hub today: discovery, a fixed address, both).

## 1. Host (behind `PRIVYHUB_SESSION_IDENTITY=v2`; absent = today)

- **Declared-port binding:** `native-stream-start`'s port must equal the
  session's signed `video_port` (and audio / controller likewise where
  the call names them); mismatch → `403 endpoint-port-mismatch`,
  audited. The legacy LAN path keeps today's behaviour.
- **The range server over the overlay:** requests whose routing
  evidence is `overlay` are refused unless they carry a valid session
  token — as the header, or, for players that cannot set headers, as a
  **per-session media token in the query string**, issued with the
  session token, bound to the client id, expiring with it, never logged
  (the audit records `media_token_used`, not the value). On the LAN:
  today's behaviour (legacy allowed). Say in the record which the
  client's player can do.
- **Permissions for the other calls:** TV-sync and EPG calls require
  the `tv` permission with a token; diagnostics calls require a new
  `diagnostics` permission, **default on for a paired device** (it is
  the user's own device reporting its health), listed in the pairing
  record so it can be revoked. Over the overlay, no token → refused and
  audited (as today's `legacy_refused`); on the LAN, legacy as today.
- **Audit and status:** each new refusal reason code in the audit; the
  session status document lists the permission set and whether a media
  token is live (boolean).

## 2. Client (behind `identity_v2`; off = today's requests byte for byte)

- **Hub host setting:** a field in the app's settings — "Hub host" —
  that overrides discovery: the hub's tailnet name (or any hostname);
  empty = today's discovery. With it set, every call goes to that host;
  the declared endpoints include the client's **overlay interface
  address** (the Tailscale interface) when present, so the host's
  endpoint class is `overlay` off-site and `lan` at home.
- **The token on every call** the audit lists, including TV-sync, EPG,
  diagnostics and the range requests (header, or the media query token
  for the player), with the host's reason codes shown on refusal, one
  retry.
- No address in any client log line; the hub host value is never
  logged (a hash if needed).

## 3. Verification (no onn install, no stream)

- Host unit tests for every new accept / refuse case and the
  flag-absent byte-for-byte handler replay (G3-S1's harness, extended
  with range and TV/EPG/diagnostics requests); the G1/G3/G5 regression
  suites still green.
- Client unit tests; the handshake harness extended to the new calls
  and the port-mismatch refusal; the debug APK built and hashed (no
  release build, as CL-B2).
- The redactor over everything.

## 4. The record

`evidence/G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md` + `g3_s3_…/` (the
diffs, test outputs, the harness output, the APK hash, `redact_check.txt`,
`manifest.sha256`); `docs/REMOTE_TRUST.md` (the media token and the
permission set); ROADMAP §G3; `patches/G3-S3_…md`;
`logs/g3_s3_git_status.txt`. **Listed for the user:** CL-B3 (install
this APK, re-pair is not needed — the device secret persists across
`adb install -r`; say if it does not — a 10-min LAN PS1-STREAM with the
flag and the setting on, the range server exercised by a VOD play), then
G4-S1 off-site. `SESSION_B_DONE_2026-10-16C.md` (ten lines).
