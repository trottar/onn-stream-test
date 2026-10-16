---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (plus G1-S1 / G3-S1, uncommitted)
durable_memory_updated: true
---

# G3-S2: session identity, client side (behind the client setting `identity_v2`)

## Purpose

The Android client's half of G3: pair once with the hub's code, sign the
session setup with the hub's nonce, declare its media endpoint, carry the
token on its control calls, and show the hub's reason code on refusal.
Record: `evidence/G3_S2_SESSION_IDENTITY_CLIENT_SIDE_2026-10-16.md`.

## Change

- **New** `PrivyHub/app/src/main/java/identity/`:
  - `SessionProtocol.kt`: the exact HMAC input, the bodies, the permission
    map, a small JSON reader;
  - `IdentitySession.kt`: pairing, setup, refresh, one retry, fail closed,
    `decorateConnection`;
  - `AndroidIdentity.kt`: the setting, the app-private secret, the pairing
    prefs, the HTTP transport, the route lookup, the refusal toast.
- **`MainActivity.kt`** (predecessor `2e31feb4…`, after `d096ac98…`):
  `httpGet` / `httpPost` are decorated, with one retry on a token refusal
  and the reason code as the message. Settings gains the toggle, the
  identity status line and "Pair with hub…" (the code entry, "Re-pair (new
  key)").
- **`streaming/NativeStreamActivity.kt`** (predecessor `e76c234b…`, after
  `2b8c0374…`): `httpPost` / `httpPostBody` / `httpPostJson` decorated, the
  same way.
- **New tests:** `app/src/test/java/identity/` (`SessionProtocolTest`,
  `IdentitySessionTest`, `WireRequestTest`, `MiniJson`), and
  `app/src/test/resources/g3_s2/setup_vectors.json` (made by G3-S1's own
  code).
- **The setting off = today's requests, byte for byte** (`WireRequestTest`).

## Validation

- `sh ./gradlew --offline :app:testDebugUnitTest` → 30 / 30 (19 new).
- The handshake harness against G3-S1's host logic → 18 / 18.
- `:app:assembleDebug` (offline) → `77011eef…7d9d`, 9,808,513 bytes. **Not
  installed** (CL-B2).
- The release APK was not built: `lint-gradle 32.3.2` is not cached offline,
  and the user skipped it ("The debug APK is the one CL-B2 installs").

## Rollback

Keep the setting off (the default). The CONFIRMED APK `de072762…` stays on
the onn; its build output is preserved in `PrivyHub/app/build/g3_s2_preserved/`.
