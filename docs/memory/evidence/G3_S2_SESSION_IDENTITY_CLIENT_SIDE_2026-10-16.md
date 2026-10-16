---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (plus last night's uncommitted G1-S1 / G3-S1 work)
---

# G3-S2 — session identity, client side

**Classification: BUILT behind the client setting `identity_v2` (default
off = today's requests, byte for byte); verified by unit tests and an
in-process handshake against G3-S1's host logic; the debug APK built;
NOT INSTALLED; NOT ADOPTED.** The release APK was not built (§5).

- Task: `handoffs/G3-S2_SESSION_IDENTITY_CLIENT_SIDE_TASK.md`, session B
  (`_cowork_prompt_b.txt`).
- **Baseline `3107fb5`** (`git log --oneline -1` at the start). The tree
  carried G1-S1 / G3-S1 uncommitted, untouched here
  (`g3_s2_2026-10-16/git_status_at_start.txt`). The client tree was clean
  at HEAD.
- The link watch may be running. This session did not restart the
  companion, start a stream or a game, run adb or touch the onn, or touch
  `~/privyhub_link_watch/` or `e4_s4d_2026-10-15/`.

## 1. What the client does (against G3-S1 as written)

| piece | the client (APK) | G3-S1 host |
| --- | --- | --- |
| setting | `identity_v2` in `privyhub_settings`, **default off**. Off: `decorate` returns before touching the connection or building the session; no nonce, no header, no declared endpoint, no store read | — |
| device secret | 32 random bytes (`SecureRandom`), hex, in `files/identity/device_secret` (app-private, owner-only); never logged | holds the key (HMAC) |
| pairing | Settings → "Pair with hub…": the 6-digit code and a device name → `POST /session/pair {code, device_name, key}`. Stores the device id, name and permissions the host returned, and shows them. "Re-pair (new key)" replaces the secret, **only** on that explicit action | the window opened on the hub's loopback (below); 120 s; ≤ 5 tries |
| setup | `POST /session/nonce` → `POST /session/setup {device_id, nonce, media_host, video_port, audio_port, sig}`. `sig` = HMAC-SHA256(key, `privyhub-session-setup-v1\n` + device_id + `\n` + nonce + `\n` + media_host + `\n` + video_port), byte for byte G3-S1's | verifies; issues an 8-h token |
| declared endpoints | `media_host` = the local address of the route to the hub (a UDP `connect`, which sends nothing); `video_port` 48100 (signed); `audio_port` 48101 (declared, unsigned) | reads `media_host` + `video_port`; **ignores** `audio_port` |
| token | in memory; refreshed when < 10 min remain; `X-PrivyHub-Session` on every control call whose path needs a permission the host granted (`/plugins/games/*` and `/diagnostics/client-health` → games; tv paths → tv). **Not** on `/status` or `/diagnostics/*` (the host would answer `permission-unknown`): those stay on the LAN legacy path | `required_permission` (the client mirrors it; unit-tested against the host's map) |
| refusal | 401 / 403 with a reason code. `token-unknown` / `token-expired` → one fresh setup and **one** retry. Anything else, or a second refusal → the code is shown (a toast "PrivyHub session refused: <reason>"; the call's error text "Session refused (<status>): <reason>"; the settings line "Last refusal"). A refused setup fails closed (the call is not made) with a 30-s cooldown, so there is no retry storm | reason codes |
| host flag off | `/session/nonce` → 404: the client goes on **without** a header (today's request) and rechecks after 60 s | — |
| unpaired, setting on | no header: the host's legacy LAN path, as today | `legacy-lan` |
| logs | `PrivyHubIdentity` lines carry states and reason codes only: no address, secret, token or host name (unit-tested) | — |

**Where the hooks are.** `MainActivity.httpGet` / `httpPost` (the
catalogue, games and sources calls) and `NativeStreamActivity.httpPost` /
`httpPostBody` / `httpPostJson` (`native-stream-start` / `-stop` / `-ready` /
`-desync` / `-heartbeat`, `/diagnostics/client-health`, the decoder report). These cover every call in the audit's client
list: `launch`, `native-stream-start`, `recovery-resume`, and the
in-session calls. Not hooked: the TV / EPG repositories, `TvStateSyncClient`
and `DiagnosticsActivity`. They keep today's requests and so take the
legacy LAN path under the host flag; over the overlay they would be
refused. That is G3-S3's to decide.

**Opening the pairing window on the hub** (the user, on the hub, while the
host flag is on):
`curl -s -X POST http://localhost:8765/session/pairing/open` prints
`{"ok": true, "code": "NNNNNN", "expires_in_s": 120}`. Enter the code on the
onn within 2 minutes.

**Two deviations from the task's wording, both forced by G3-S1's host as
written:**

1. **"Never sent — only HMACs of it."** The secret is sent **once**, in the
   pairing body on the LAN. G3-S1 verifies HMAC-SHA256 and must hold the key,
   because the stdlib offers no public-key signatures and nothing could be
   fetched. After pairing, only HMACs travel. A public-key scheme would remove
   this; it needs a host change first.
2. **"A stable client_id derived from it as the host does."** The host does
   not derive it: it **assigns** `dev-` + 16 hex at pairing. The client
   stores and uses that.

The task's "the interface addresses it currently holds" also became one
address (`media_host`): G3-S1's setup reads one host. More would be
ignored, unsigned.

## 2. The test vectors — the two sides agree on the bytes

`g3_s2_2026-10-16/make_vectors.py` made `setup_vectors.json` with **G3-S1's
own code**: `tests/session_identity/common.sign`, `SETUP_CANON`, and a
`SessionGate` run in process for the host's response bodies
(`json.dumps(indent=2)`, as `_send_json` writes them):

- **3 setup vectors**: a text host; a LAN IPv4; an overlay IPv4 with port
  50000. The addresses are given as integers and built on each side, so the
  file holds no address literal.
- **9 host bodies**: `pair_ok`, `pair_closed`, `nonce_ok`, `setup_ok`,
  `setup_nonce_unknown`, `legacy_overlay`, `permission_unknown`,
  `token_expired`, and a host-flag-off 404.
- **The permission map** for 12 paths.

The file was copied **unchanged** into
`PrivyHub/app/src/test/resources/g3_s2/setup_vectors.json`; both copies are
sha256 `2c14bb47…`.

## 3. Verification

**Client unit tests** (`sh ./gradlew --offline :app:testDebugUnitTest`,
`unit_tests.log`, `unit_tests_summary.txt`): **30 / 30**. The 11 existing
tests still pass, and there are 19 new:

| suite | tests | what |
| --- | --- | --- |
| `SessionProtocolTest` | 6 | the constants = the host's; **the HMAC input (sha256 and byte length) and the signature match all 3 vectors**; the setup body's fields and order; the pairing body's escaping; the permission map = the host's; the 9 host bodies parse (nonce, token, TTL, permissions, device id, reason codes) |
| `IdentitySessionTest` | 11 | off = no call, no header, no store read; on and unpaired = legacy; pairing sends the key once and stores the pairing; a bad code is refused; re-pair replaces the secret only when asked; the header by permission, the declared `media_host` / `video_port` / `audio_port`, token reuse; **refresh before expiry**; **one retry on `token-expired`, then shown**; `permission-denied` shown, not retried; **a refused setup fails closed with a cooldown (no storm)**; a host without the identity layer (404) still works; **no secret, token, address or host name in any log line** |
| `WireRequestTest` | 2 | the raw request on a loopback socket, built field by field as `MainActivity.httpPost` builds it: **off = today's bytes exactly** (and the session is never built); on and paired = the same bytes plus one `X-PrivyHub-Session` line |

**The handshake harness** (`handshake_harness.py` → `handshake_output.txt`):
**18 / 18 PASS**. The client side is a line-for-line Python port of
`SessionProtocol.kt` / `IdentitySession.kt`, first checked against the 3
vectors. The host side is G3-S1's `SessionGate`, unchanged. The steps:

- pair, with the window opened on the hub's loopback;
- nonce and signed setup, with the declared endpoints;
- a replayed setup → `nonce-replayed`;
- a call with the token → the plugin target is **the declared host**, not
  the source;
- no header on `/status`;
- refresh inside the margin;
- expiry → `token-expired` → one retry → allowed;
- wrong key → `bad-signature`;
- a LAN source declaring an overlay host → `endpoint-class-mismatch`;
- no token over the overlay → `legacy-overlay`;
- a forged token → `token-unknown`, no fallback;
- unpaired → legacy LAN;
- the host's audit: no address, key or token.

**Run 1 read 17 / 18** (`handshake_output_run1.txt`). The harness sent the
replayed setup *after* moving the clock past the 8-h expiry. By then the
host had purged the spent nonce, so it answered `nonce-unknown` (refused, but
not the reason the step expected). The step was moved to straight after the
setup and the harness re-run: 18 / 18. The protocol did not change.

## 4. The debug APK (`apk_sha256.txt`, `build_debug.log`)

- `sh ./gradlew --offline :app:assembleDebug` → **`77011eefa538fb965e46ad1f25ddac99036e1d77557ba7b7a677dc5947807d9d`**,
  **9,808,513 bytes**. Built after the last source edit. **Not installed.**
- **The CONFIRMED APK's build output was preserved first.**
  `app/build/outputs/apk/debug/app-debug.apk` was `de072762…835e` (the
  CONFIRMED APK, `tools/c3_l4_nft_night.py`). It was copied to
  `PrivyHub/app/build/g3_s2_preserved/` (gitignored) before this build
  overwrote it. The onn still runs `de072762…`; the watch's preflight is
  unaffected.

## 5. The release APK: not built (the user's decision)

`sh ./gradlew --offline :app:assembleRelease` failed
(`build_release.log`): `com.android.tools.lint:lint-gradle:32.3.2` is not in
the offline cache. The session stopped and reported it. **The user,
2026-10-16: "Skip the release APK. The debug APK is the one CL-B2 installs,
as CL-B1 did."** Nothing was fetched, and lint was not skipped.

## 6. For the user — CL-B2 (not done here)

1. **After the watch is stopped or ends** (its cap is 2026-10-20T04:00Z):
   install the debug APK `77011eef…` as the CONFIRMED one (`adb install -r`,
   as CL-B1 did). Update the pinned hashes: `ADOPTED_APK_SHA256` in
   `tools/c3_l4_nft_night.py` (and its test), and `EXPECT_APK` in
   `tools/e1_suite.py`.
2. With the client setting off, a short regression shows today's
   behaviour.
3. **The host flag on** (`PRIVYHUB_SESSION_IDENTITY=v2`, a drop-in). On the
   hub, open the pairing window (`curl … /session/pairing/open`). On the onn,
   turn "Use paired identity (identity v2)" on in Settings, then "Pair with
   hub…" and enter the code. **By hand, on the LAN.**
4. **The live smoke of G3, end to end, on the LAN:**
   - launch and stream;
   - `logs/session_audit.jsonl` shows `pairing_ok` and `token_issued`, and
     no `legacy_setup` for the paired client;
   - the stream reaches the declared host.

   Only then any remote test.

Not adopted; the client setting is off by default; the host flag is absent.

## 7. Files; disclosures

- **`g3_s2_2026-10-16/`:**
  - `baseline_commit.txt`, `git_status_at_start.txt`,
    `predecessor_sha256.txt`, `after_sha256.txt`, `g3_s2.diff` (the two
    activities' diffs, then the new files);
  - `make_vectors.py`, `setup_vectors.json`;
  - `baseline_unit_tests.log`, `unit_tests.log`, `unit_tests_summary.txt`;
  - `handshake_harness.py`, `handshake_output_run1.txt`,
    `handshake_output.txt`;
  - `build_debug.log`, `build_release.log`, `apk_sha256.txt`;
  - `redact_check.txt`, `manifest.sha256`.
- **Patch record:** `patches/G3-S2_SESSION_IDENTITY_CLIENT_SIDE.md`
  (`PATCH_INDEX.md` not updated: not session B's file).
- **Left in place:** `make_vectors.py` and the harness ran G3-S1's
  `make_gate`, which leaves its temporary stores under the system temp
  directory. Gradle wrote its build outputs and caches (gitignored). Nothing
  was deleted.
- **The redactor** (`redact_check.txt`): 22 files OK, 0 HIT, over this
  directory, the record, the patch, `REMOTE_TRUST.md`, ROADMAP and the
  vectors resource. The checker reads no `.kt` files, but every Kotlin line
  this task added is in `g3_s2.diff`, which it read.
- No sudo, no nft, the Opal untouched, nothing fetched, nothing installed,
  no adb. Git status: `logs/g3_s2_git_status.txt`.
