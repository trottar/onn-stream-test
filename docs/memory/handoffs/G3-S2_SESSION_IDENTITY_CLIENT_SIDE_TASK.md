---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G3-S2, session B: the CLIENT side of G3 — the Android client holds a device key, pairs once with the code the host shows, signs its session setup with the host's nonce, carries the session token on control calls, declares its own endpoints, and fails closed with the host's reason code. Built and tested against G3-S1's host logic; the APK is NOT installed on the onn in this task (that is CL-B2, the user's say-so, and it conflicts with the running watch). Nothing adopted; nothing committed
---

# G3-S2 — session identity, client side

**Contract to implement** (G3-S1's design, `companion/session_identity.py`
as written, not as the task imagined it — read the code and its tests
first): the pairing window and one-time code; the nonce endpoint; the
HMAC-signed setup; the 8-h token and its header (`X-PrivyHub-Session`);
declared endpoints in the setup body; the reason codes on refusal; the
legacy path (so an unpaired client still works on the home LAN with the
host flag on, and today's behaviour is unchanged with the host flag off).

Read first: `evidence/G3_S1_SESSION_IDENTITY_HOST_SIDE_2026-10-15.md` §1
(the design) and `g3_s1_2026-10-15/g3_s1.diff`; `companion/session_identity.py`
and `tests/session_identity/`; `docs/REMOTE_TRUST.md`; the Android client
(the module CL-B1 built; its session-setup, launch, native-stream-start
and heartbeat calls — the audit in `g1_s1_2026-10-15/source_address_audit.md`
lists them); `CL_B1_APK_ADOPTION_2026-09-30.md` (how an APK becomes the
CONFIRMED one; **not done here**).

## 1. The client change (behind a client setting, default off)

- **Device identity:** a random 32-byte secret generated on first run,
  kept in app-private storage (Android Keystore-backed if the existing
  code has a pattern for it; else app-private file, mode 0600), never
  logged, never sent — only HMACs of it. A stable `client_id` derived
  from it as the host does.
- **Pairing screen:** enter the code the host shows (the host opens the
  window by its own local action — the record says which command); on
  success store the pairing; show the device's display name and
  permissions the host returned. Re-pairing replaces the secret only on
  explicit user action.
- **Session setup:** fetch the nonce, sign the setup (the exact HMAC
  input G3-S1 defines, byte for byte), include **declared endpoints**:
  the client's listening ports for video, audio and controller return
  traffic and the interface addresses it currently holds (the host
  picks; the client declares). Store the token; send it as
  `X-PrivyHub-Session` on every control call the audit lists; refresh
  before expiry; on `401`/refusal show the host's reason code on screen
  (no silent retry storm: one retry, then a visible state).
- **Setting:** `identity_v2` in the client's settings, **default off =
  today's requests byte for byte** (no nonce fetch, no header, no
  declared endpoints). On: the above. A paired client with the setting
  on and the host flag off still works (the host ignores the extras —
  G3-S1's replay shows that).
- **No address in any log line** the client writes.

## 2. Verification (no onn install, no stream)

- Unit tests in the client module: the HMAC input matches G3-S1's test
  vectors (copy the vectors from `tests/session_identity/` — the two
  sides must agree on the bytes); setup body shape; header presence by
  setting; refusal handling.
- **Cross-check against the host in-process:** a small Python harness
  (`g3_s2_<date>/handshake_harness.py`) that runs G3-S1's host logic and
  the client's HMAC/body construction (ported in the harness from the
  same vectors) through pair → nonce → setup → token → call → expiry →
  refused cases, and prints each step's verdict. The real client code is
  exercised by its own unit tests; the harness proves the protocol
  bytes agree.
- Build the APK (debug and the release flavour CL-B1 used); record its
  sha256 and size; **do not install it** (`adb install` is CL-B2; the
  watch's preflight checks the CONFIRMED APK's hash and would mark every
  probe). If the build needs a dependency that is not cached, stop and
  say so (nothing fetched).

## 3. The record

`evidence/G3_S2_SESSION_IDENTITY_CLIENT_SIDE_<date>.md` + `g3_s2_<date>/`
(the diff, test output, the harness output, the APK hashes,
`redact_check.txt`, `manifest.sha256`); `docs/REMOTE_TRUST.md` (the
client's part of the identity model); `docs/ROADMAP.md` §G3 status;
`patches/G3-S2_…md`; `logs/g3_s2_git_status.txt`. **Listed for the
user:** CL-B2 (install the APK as the CONFIRMED one — after the watch
is stopped or ends; the state check's hash updated; a pairing done by
hand on the LAN; then the live smoke of G3 end to end on the LAN before
any remote test). Nothing adopted; the client setting off by default;
the host flag absent; `SESSION_B_DONE_2026-10-16.md` (ten lines).
