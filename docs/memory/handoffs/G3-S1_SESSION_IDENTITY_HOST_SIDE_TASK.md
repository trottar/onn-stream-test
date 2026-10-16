---
memory_schema: 1
as_of: 2026-10-15
status: TASK HANDOFF — G3-S1, queue 2026-10-15B item 2: durable client identity, session identity, declared endpoints, fail-closed authorization and an audit log on the HOST side, behind `PRIVYHUB_SESSION_IDENTITY=v2` (absent = today, byte for byte). Today's Android client keeps working under the flag through an explicit, audited "legacy" path, so the host can be adopted before the client changes (G3-S2). Software only; no stream; nothing adopted; nothing committed
---

# G3-S1 — session identity and authorization, host side

**The rule being implemented** (ROADMAP §G3 and the trust boundary):
source address is routing evidence, never identity; overlay membership
is transport, never authorization; session setup fails closed;
permissions are auditable. The audit from G1-S1 §2 lists every place
this touches.

Read first: G1-S1's `source_address_audit.md` and `docs/REMOTE_TRUST.md`;
the companion's session-setup path (`plugins/games.py`,
`native_session_io.py`, the HTTP handlers), how media/controller targets
are chosen today, the Android client's setup request (what it sends: a
device name? nothing?), `D6_R1_…` (the replay suite's requests),
`C1_STATIC_PROFILE_AND_STATUS_PRIVACY_…` (what the status endpoint may
expose).

## 1. The model (one module, `companion/session_identity.py`; the design in the record §1 before the code)

- **Client identity**: a per-device key pair or long random secret,
  created on the client at first run (G3-S2), **paired once on the
  home LAN** through an explicit host action (a pairing window the host
  opens for 2 min; a one-time code shown by the host, entered on the
  client — the host side of this now, the client side in G3-S2). Paired
  devices are stored on the host (`~/.config/privyhub/paired_devices.json`,
  outside git: a device id, a display name, the public key or secret
  hash, paired-at, permissions). No address stored.
- **Session identity**: at session setup the client proves its identity
  (a signed or HMAC'd setup request with a nonce the host issued), and
  the host issues a session token bound to that client id, with an
  expiry; every control call afterwards carries it. Possession of the
  LAN, the travel router or the overlay grants nothing.
- **Declared endpoints**: the client **declares** where it will receive
  video, audio and controller return traffic (addresses and ports, in
  the setup request), and the host uses those — **not** the request's
  source address. The host may still record the source as routing
  evidence in the audit log.
- **Authorization**: per paired device, a small permission set (games,
  tv, vod, pairing-admin; default: games+tv+vod for a paired device,
  nothing for an unpaired one). Unknown device → setup refused with a
  reason code; unknown permission → denied. Fail closed everywhere.
- **Audit log**: `logs/session_audit.jsonl` — one line per setup,
  refusal, token issue/expiry, permission denial, pairing event: time,
  client id (never the key), what, why, and `routing_evidence`
  redacted to "lan"/"overlay"/"unknown" (no address). The redactor must
  pass on it.
- **Legacy path (so today's client keeps working under the flag):** a
  setup request with no identity material is accepted **only if** the
  source is on the home LAN **and** the host's `legacy_unpaired_lan`
  setting is on (default on in v2 for this transition; the record says
  how it is turned off), is given a session token bound to a synthetic
  client id `legacy-lan`, has its endpoints derived from the source
  address **as today**, and is logged as `legacy` in the audit. Over
  the overlay the legacy path is never allowed.

## 2. The flag and the byte-for-byte rule

`PRIVYHUB_SESSION_IDENTITY=v2`; absent = today: no token, no pairing
store read, no audit file written, the status document unchanged. With
it set and no paired device: today's client works via the legacy path
on the LAN; the audit log shows it as such.

## 3. Verification (no stream, no restart)

- `tests/session_identity/`: pairing window open/closed; a signed setup
  accepted; a wrong signature, a replayed nonce, an expired token, an
  unknown device, a denied permission — each refused with its reason
  code; the legacy path on-LAN accepted and audited, off-LAN refused;
  declared endpoints used instead of the source; the flag absent →
  today's code path (the handlers' outputs identical for the replay
  suite's requests, compared byte for byte).
- The D6-R1 replay suite run against an **in-process** companion
  instance with the flag absent and present (if the suite can target a
  non-service instance; else "pending on the stream").
- The redactor over the audit log the tests produced.

## 4. The record

`evidence/G3_S1_SESSION_IDENTITY_HOST_SIDE_<date>.md` + `g3_s1_<date>/`
(the design, the diff, the test output, the replay comparison, a sample
audit log, `redact_check.txt`, `manifest.sha256`); `docs/REMOTE_TRUST.md`
gains the identity model section; `docs/ROADMAP.md` §G3 status;
`patches/G3-S1_…md`; `logs/g3_s1_git_status.txt`. **Listed for the
user:** G3-S2 (the client side: key generation, pairing UI, signed setup,
declared endpoints — an APK change) and the live smoke for session A.
Nothing adopted; the flag absent; then `SESSION_B_DONE_2026-10-15B.md`.
