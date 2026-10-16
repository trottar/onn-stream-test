---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e
durable_memory_updated: true
---

# G3-S3: hardening and the hub host (behind `PRIVYHUB_SESSION_IDENTITY=v2` / `identity_v2`)

## Purpose

What G4-P1 and CL-B2 found between the LAN-verified identity model and a real
off-site session: the stream-start ports bound to the signed ones, the range
server gated over the overlay, TV-sync / EPG / diagnostics with a token, and a
"Hub host" setting so the client can reach the hub off-site. Record:
`evidence/G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md`.

## Change

- **`companion/session_identity.py`** (predecessor and after in
  `evidence/g3_s3_2026-10-16/predecessor_sha256.txt` / `after_sha256.txt`):
  setup canon v2 (`sig_v` 2: the audio port and the overlay address signed;
  v1 still accepted); the media target chosen by the request's routing class;
  the port binding (`_port_mismatch`, `port_kind` audited); the media token;
  `/session/media-check` (loopback only); `diagnostics` grantable and default
  on (`permissions_v` 2; pre-G3-S3 records granted it implicitly); the status
  document's `permissions_known`, `default_paired_permissions` and `sessions`;
  `MediaGate` and `media_gate_from_environ` for the range server.
- **`companion/range_server.py`**: the gate built only under the flag (the
  import inside the `if`); `do_GET` / `do_HEAD` ask it first; `log_message`
  masks the media token under the flag. Absent: byte for byte today
  (replayed).
- **`companion/privyhub_service.py`: unchanged** (the range server inherits
  the companion's environment; `/session/media-check` is a `/session/*`
  route the existing intercept already answers).
- **Client** (`PrivyHub/app/src/main/java/`): `identity/SessionProtocol.kt`
  (v2 canon and body, the overlay block, `effectiveHost`, `isHubMediaUrl`,
  `urlForLog`); `identity/IdentitySession.kt` (v2 setup with the overlay
  address, `mediaHeaderFor` / `mediaTokenFor`, `diagnostics` implied, the
  host's grant stored); `identity/AndroidIdentity.kt` (`hub_host`,
  `effectiveHost`, the overlay interface lookup, `mediaHeader`,
  `decorateMedia`, `urlForLog`); **new** `identity/MediaDataSource.kt` (a
  Media3 `ResolvingDataSource` adding the header to the hub's media URLs
  only); `MainActivity.kt` (the Hub host field; `getCompanionHost()` →
  effective host, `getStoredCompanionHost()` for the field; the player's
  factory under the setting; artwork decorated; the "Opening media" line
  hashed under the setting); `TvStateSyncClient.kt`, `TvEpgRepository.kt`,
  `diagnostics/DiagnosticsActivity.kt` (decorated, one retry, the reason
  code).
- **Tests:** `tests/session_identity/test_g3s3.py` (new, 38),
  `test_range_replay.py` (new, 3) + `fixtures/range_server_predecessor.py.txt`
  (HEAD's range server); `test_handler_replay.py` extended (TV / EPG /
  diagnostics rows, one new test); three G3-S1 expectations updated for
  `diagnostics` (disclosed in the record). Client: `IdentitySessionTest`
  (+8, the fake host verifies v2), `SessionProtocolV2Test` (new, 6),
  `resources/g3_s3/setup_vectors_v2.json` (made and accepted by the host).

## Validation

- `python3 -m unittest discover -s tests/session_identity` → 80 OK;
  `tests/overlay` 17 OK; `tests/wan_telemetry` 18 OK; mutation check 9/9
  caught.
- `sh ./gradlew --offline :app:testDebugUnitTest --rerun` → 44 / 44.
- The handshake harness → 24 / 24.
- `sh ./gradlew --offline :app:assembleDebug` → `59f736d2…bf65f`, 9,810,323
  bytes, **not installed**. The CONFIRMED APK's build output (`77011eef…`)
  was copied to `PrivyHub/app/build/g3_s3_preserved/` first.
- `git diff --check` clean; the redactor over the record, this patch, the
  directory, `REMOTE_TRUST.md`, ROADMAP and the vectors resource.

## Result

BUILT behind the flags; NOT INSTALLED; NOT ADOPTED; nothing committed.
`PATCH_INDEX.md` not updated (not session B's file).
