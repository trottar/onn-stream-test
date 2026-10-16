---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e
---

# G3-S3 — hardening, and the hub-host setting

**Classification: BUILT behind the existing flags (the host's
`PRIVYHUB_SESSION_IDENTITY=v2`, the client's `identity_v2`; absent / off =
today, byte for byte); verified by host unit tests, the extended
flag-absent replay, the G1 / G3 / G5 suites, client unit tests and the
extended handshake harness; the debug APK built and hashed; NOT INSTALLED;
NOT ADOPTED; nothing committed.**

- **The APK: `59f736d29b96700253a178efa5efd0cd8846858a89d32848a0994586712bf65f`**,
  9,810,323 bytes (`sh ./gradlew --offline :app:assembleDebug`;
  `g3_s3_2026-10-16/apk_sha256.txt`). No uncached dependency was needed.
- Task: `handoffs/G3-S3_HARDENING_AND_HUB_HOST_TASK.md`, session B
  (`_cowork_prompt_b.txt`). **Baseline `92e388e`** (`git log --oneline -1` at
  the start). The tree held only the two prompt files and the task / G-A1
  handoffs untracked (`g3_s3_2026-10-16/git_status_at_start.txt`).
- The companion runs on the five adopted lines with no flag; it was not
  restarted. No stream, no game, no adb, no install.

## 1. The design (written before the code)

`g3_s3_2026-10-16/design_written_before_code.md`, sha256 `f03a42a7…eb66`,
hashed at 16:30:25Z before the first G3-S3 code edit
(`design_written_before_code.sha256`). What the survey found:

- **There is no hub discovery today.** The client reads one hand-entered
  companion host (`companion_host`) and hands it to the stream and
  diagnostics screens. "Hub host" therefore overrides that setting.
- **The range server** (port 8000) is a child process of the companion, with
  the companion's environment. It serves VOD (`/vod/…`), the live HLS output
  and the game artwork, and it holds no session state.
- **The client's player can send headers.** It is Media3 ExoPlayer over
  `DefaultHttpDataSource`, which already sends `Referer` for some sources.
  The same player also plays third-party IPTV URLs, so the header is scoped
  to the hub's media endpoint. Artwork is an `HttpURLConnection` (headers
  possible).
- `native-stream-start` already compared `port` with the signed
  `video_port`. The audio and controller ports are constants on both sides,
  and no call names them today. The client declared `audio_port` unsigned,
  and the host ignored it.
- TV-sync and EPG already mapped to `tv`. `/status` and `/diagnostics/*`
  mapped to a `diagnostics` permission that could not be granted.

## 2. What was built

### Host (`companion/session_identity.py`, `companion/range_server.py`; `privyhub_service.py` unchanged)

| piece | behaviour under `v2` | reason codes (audited) |
| --- | --- | --- |
| setup canon v2 | `sig_v: 2` signs `v2 / device_id / nonce / media_host / video_port / audio_port / overlay_host`. Without `sig_v`, the v1 canon as before: the CL-B2 APK still sets up, and its `audio_port` is still ignored | `bad-signature`, `endpoint-invalid` (audio port outside 1024-65535; an `overlay_host` that is not an overlay-class IPv4) |
| declared-port binding | a token's `native-stream-start` must name exactly one `port` equal to the signed `video_port`. A named `audio_port` must equal the signed one. A named `controller_port` has no signed value and is refused. The legacy LAN path is unchanged | `endpoint-port-mismatch` (403), audited with `port_kind` video / audio / controller |
| the media target | the declared address **whose class matches the request's routing class**: an overlay source gets `overlay_host`, a LAN source `media_host`. At least one declared address must match the source's class | `endpoint-class-mismatch` |
| media token | issued with every session token (`media_token` in the setup response), bound to the device, expiring and revoked with the session; never logged | `media-token-unknown` |
| the range server's gate | built only under the flag (the import inside the `if`). Loopback → served. LAN with no credential → served as today (if `legacy_unpaired_lan`). Anything else (a header or `?media_token=` on any network; overlay / unknown with neither) → the range server asks the companion, `POST /session/media-check {routing, path, token or media_token}` on loopback. The companion checks the session, then `vod`. A presented credential that fails is refused; it never falls back to legacy | `legacy-overlay`, `legacy-unknown-network`, `legacy-disabled`, `token-unknown`, `token-expired`, `device-revoked`, `media-token-unknown`, `permission-denied` (`vod`), `host-local-only` (a non-loopback media-check), `identity-flag-unknown`, `identity-unavailable` (the companion unreachable: 503, audited by the range server) |
| range server's own log | under the flag, the request line's `media_token=` value becomes `<redacted>` | — |
| audit of media use | refusals every time. The **first accepted use of each token** is audited once (`media_session`, with `media_token_used` true / false), not per range request | — |
| `diagnostics` | grantable; **default on for a paired device**. A new pairing record lists `games, tv, vod, diagnostics` with `permissions_v: 2`. A record paired before G3-S3 (no `permissions_v`, e.g. CL-B2's) gets it implicitly. Revocation: drop it from the list (and, on an old record, add `"permissions_v": 2`), no restart. `/diagnostics/client-health` stays `games` | `permission-denied` (`diagnostics`) |
| TV-sync / EPG | already `tv`; the change is the client sending the token. Over the overlay with no token: refused as before | `legacy-overlay` |
| status document | `/session/status` (hub loopback) adds `permissions_known`, `default_paired_permissions`, and per live session: `client_id`, `kind`, `permissions`, **`media_token_live` (a boolean)** and `expires_in_s`. No address, token or media token | — |

### Client (`identity_v2`; off = today's requests)

| piece | what it does |
| --- | --- |
| **Hub host** | a Settings field under the identity checkbox (`hub_host`, empty = today). With the setting on and a value set, `getCompanionHost()` returns it: catalogue, games, sources, the stream screen and diagnostics (intent extras), TV-sync, EPG, media and artwork all go there. The field beside it still shows the stored companion host; pairing still uses that (LAN) host. Changing the hub host drops the session |
| setup | v2 (`sig_v` 2), `audio_port` signed, plus `overlay_host`: the IPv4 address of an up, non-loopback interface in the overlay block (the Tailscale app's tunnel), found by listing interfaces (nothing sent). Declared only when present and in the block |
| the token on every audited call | the G3-S2 hooks, plus `TvStateSyncClient` (GET / POST), `TvEpgRepository` (guide, prefetch), `DiagnosticsActivity` (`/diagnostics/*`; now under `diagnostics`). Then the player's requests to the hub's media endpoint (`identity/MediaDataSource.kt`: a Media3 `ResolvingDataSource` that adds the header only when the URI's host and port are the hub's media endpoint, never to an IPTV URL) and the artwork fetch |
| `diagnostics` | treated as granted to a paired device until the host's grant says otherwise. The host's grant is then stored as the pairing's permission list |
| refusals | the host's reason code shown (toast, settings line, call error text). `token-unknown` / `token-expired` get one fresh setup and one retry (TV-sync, EPG, diagnostics as G3-S2's calls). A port mismatch or a permission refusal is shown, not retried |
| logs | the lines G3-S3 adds carry states and booleans (`overlay_declared=`). The player's "Opening media" line logs the URL with its host replaced by `h-` + 12 hex under the setting |

**Which the client's player can do (the task's question):** Media3 can set
headers. So the player sends `X-PrivyHub-Session`, scoped to the hub's media
endpoint. The media token is received and held (`mediaTokenFor`); the query
form is for a header-less player, and this APK has none. The host accepts
both, and the harness exercises both.

## 3. Verification

**Host unit tests** (`tests_output.txt`):
`python3 -m unittest discover -s tests/session_identity -v` → **80 OK**:

- G3-S1's 38;
- `test_g3s3.py`, 38 new tests:
  - v2 accepted, with a media token; v1 still accepted;
  - a tampered audio port or overlay address → `bad-signature`, and so is a
    v1 signature sent as v2;
  - an invalid audio port or overlay address;
  - the overlay target chosen off-site, the LAN target at home;
  - the port binding: bound; seven mismatch forms with `port_kind`; a v1
    session naming an audio port; legacy unchanged;
  - diagnostics: default on, a pre-G3-S3 record, revoked at next use,
    `client-health` stays `games`, the overlay without a token;
  - TV / EPG with a token over the overlay, without one, `tv` revoked;
  - the media-check: host-local only; the header, audited once; the media
    token; forged / swapped / ended / expired; bound to the device; `vod`;
    no credentials on each network; a legacy token never over the overlay;
    an unknown flag value; the path audited without its query;
  - the status document;
  - `MediaGate`: the loopback URL, no call for loopback / LAN legacy, the
    overlay, a LAN token checked, the companion unreachable, the mask, the
    flag absent;
  - the audit: no address, token or media token;
- `test_range_replay.py`, 3 new tests (below);
- one new handler-replay test: TV / EPG / diagnostics over the overlay with
  the token (and without → `legacy-overlay`), the port mismatch over HTTP,
  and the declared overlay target.

**The flag-absent replay, extended:**

- **The range server** (`replay_range_server.md`). HEAD's `range_server.py`
  (`fixtures/range_server_predecessor.py.txt`) and the edited one were
  loaded as modules. Each was fed the same raw requests over a fixture media
  tree:
  - VOD full, `bytes=0-1023`, `bytes=70000-`, `bytes=-500` and an
    unsatisfiable range;
  - HEAD, the live playlist, artwork, a missing file, a traversal, and a
    directory listing;
  - a `?media_token=` request.

  Each request came from a LAN, a loopback and an overlay source. **36 / 36
  responses identical, and the log lines identical.** With the gate set:
  - LAN and loopback identical to the baseline, apart from one case: a LAN
    request with an unissued media token is refused `media-token-unknown`
    (no fallback, by design);
  - the overlay without a token → 401 `legacy-overlay` (and HEAD with no
    body);
  - with the header or the media token → **the baseline's 206 bytes**;
  - a forged media token → `media-token-unknown`;
  - the log masks the value.
- **The companion** (`replay_companion.md`). G3-S1's handler replay gained
  six requests: TV-sync, EPG guide, EPG prefetch, `/sources`,
  `/diagnostics/health` and `/diagnostics/stream-telemetry`. All are 200
  through stubs (checked: not identical errors). **26 / 26 identical with the
  flag absent**, as are the access-log lines. `privyhub_service.py` itself is
  unchanged (sha256 `ddfaf5fa…` before and after).
- **Mutation check** (`mutation_check.py` → `mutation_check.txt`): each
  mutation was made in a temp copy, never in the tree. All nine were caught:
  - the port binding off;
  - any media token accepted;
  - the overlay served without a token;
  - `vod` not checked;
  - the v2 canon without the audio port;
  - `diagnostics` not implied;
  - the overlay target not chosen;
  - the log mask off;
  - the gate's import unguarded.

  The last was missed at first: the glue test only checked for an `if`. It
  was tightened to require the flag in the condition (disclosed).

**The G1 / G3 / G5 suites:** `tests/overlay` 17 OK, `tests/wan_telemetry`
18 OK (`tests_regression_g1_g5.txt`); G3 is the 80 above.

**Client unit tests** (`sh ./gradlew --offline :app:testDebugUnitTest --rerun`,
`unit_tests.log`, `unit_tests_summary.txt`): **44 / 44**. That is G3-S2's 30
plus 14 new:

- **`SessionProtocolV2Test` (6):**
  - the constants equal the host's;
  - the v2 canon (sha256 and byte length) and signature match three
    vectors that **the host's `_setup` accepted in process**
    (`make_vectors_v2.py`; `setup_vectors_v2.json`, sha256 `a0e9cfdf…`,
    copied unchanged to `app/src/test/resources/g3_s3/`);
  - the body's field order; the overlay block;
  - the permission map equals the host's (14 paths);
  - the host bodies parse.
- **`IdentitySessionTest` (+8):**
  - v2 signed, the overlay address declared only when present and in the
    block, no address in a log line;
  - diagnostics when the host grants it, stored;
  - TV / EPG carry the token;
  - the media header and media token, and none when off;
  - no media header without `vod`;
  - a port mismatch shown, not retried;
  - the hub-host rule and **the hub-only media rule** (an IPTV host, a
    look-alike host, the control port: no header);
  - the URL log hash.

  G3-S2's fake host was taught the v2 canon. Five G3-S2 tests had failed
  only because it verified v1; they pass unchanged now. `WireRequestTest`
  (off = today's bytes) is unchanged and passes.

**The handshake harness** (`handshake_harness.py` → `handshake_output.txt`):
**24 / 24 PASS**. The client side is a Python port of the G3-S3 Kotlin
(checked first against the 3 v2 vectors). The host side is the edited
`SessionGate`, its `MediaGate` and the edited range server's handler, all in
process. The steps:

1. pair on the LAN;
2. a LAN v2 setup and the declared LAN target;
3. an overlay setup with the overlay address, and the overlay target;
4. **the port mismatch refused, shown, not retried**;
5. the signed audio port;
6. TV-sync GET / POST, EPG guide / prefetch, `/status` and diagnostics
   health over the overlay: with the token allowed, without it
   `legacy-overlay`;
7. the range server over the overlay: no token → 401; **the header → the
   baseline's 206 bytes**; **the media token → the same bytes, the log
   masked**; forged → `media-token-unknown`;
8. the range server on the LAN: no token gives today's bytes; artwork with
   the header;
9. expiry → one fresh setup and one retry;
10. diagnostics revoked → `permission-denied`, shown;
11. the status document;
12. the audit: no address, key, token or media token; `media_session` with
    `media_token_used` true and false; the port mismatch recorded.

**The debug APK** (`build_debug.log`, `apk_sha256.txt`): built after the last
source edit (0 source files newer). The new strings are in the dex. **Not
installed.** First, the build output it overwrote (`77011eef…`, the
CONFIRMED APK) was copied to `PrivyHub/app/build/g3_s3_preserved/`
(gitignored). The onn still runs `77011eef…`.

**The redactor** (`redact_check.txt`): **35 files OK, 0 HIT**, over this
record, the directory, the patch, `REMOTE_TRUST.md`, ROADMAP, the vectors
resource, the session-identity tests, the status / DONE files and the git
status log. The first pass hit `g3_s3.diff` once: the fixture copy of HEAD's
range server holds its bind-all default, which matches the IPv4 pattern. The
diff now references that fixture by source and hash
(`git show 92e388e:companion/range_server.py`, verified verbatim) rather than
inlining it. The checker reads no `.kt` files, but every Kotlin line this
task added is in `g3_s3.diff`, which it read.

## 4. For the user (not done here)

**CL-B3: install this APK, then a LAN smoke.** Session A's
`handoffs/G-A1_ADOPTION_AND_CL-B3_TASK.md` carries it.

- **Install** `59f736d2…` with `adb install -r`, as CL-B1 / CL-B2 did.
  Re-pairing is not needed: `-r` keeps the app's data, so
  `files/identity/device_secret` and the pairing prefs persist. **If the
  client shows "not paired" after the install, they did not persist: say
  so.** Then re-open the pairing window and pair again. Update the pinned
  hashes after install.
- **The host must run this tree's `session_identity.py`.** A restart under
  the flag loads it. This APK signs v2, so a host still running G3-S1's
  module would refuse it `bad-signature` (it fails closed).
- **Leave "Hub host" empty at home.** If it is set to the tailnet name while
  the onn runs Tailscale at home, the session is overlay-class and streams
  over the tunnel.
- **What to look for:**
  - A 10-min LAN PS1-STREAM with the flag and the setting on: the audit
    shows `token_issued` with `sig_v: 2`, no `legacy_setup` for the paired
    client, and no `endpoint-port-mismatch`. The client's first setup
    stores `diagnostics` in its pairing.
  - **The range server: a VOD play.** The audit shows one `media_session`
    (`media_token_used: false`, the header, `routing_evidence: lan`), and
    the play reaches the client.
  - `/session/status` lists the session's permissions and
    `media_token_live: true`.

**Then G4-S1, off-site** (`handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md`).
Before leaving, set "Hub host" to the hub's tailnet name. Off-site, the
session should read overlay-class, stream to the onn's overlay address, and
serve TV-sync, EPG, diagnostics and VOD with the token. The G4-P1 blockers
that are not software remain:

- the overlay provider flag on the companion (G-A1 adopts it);
- the Tailscale app on the onn;
- the hub's firewall on the tailnet interface, which is still unverified.

**Notes for those runs:**

- Under the flag, every range request that carries a token makes one
  loopback `POST /session/media-check`. That is one companion access-log
  line per range request (ExoPlayer: one per open or seek; HLS: one per
  segment and playlist reload).
- A 401 from the range server reaches the player as a playback error, not
  as a reason-coded toast; the next load sets up afresh. A refused *setup*
  is shown as a reason-coded toast.
- At most one media check is in flight per range request, with a 2-s
  timeout. If the companion is unreachable, the range server refuses
  (`identity-unavailable`); it does not serve.

## 5. Files; disclosures

- **`g3_s3_2026-10-16/`:**
  - `baseline_commit.txt`, `git_status_at_start.txt`,
    `predecessor_sha256.txt`, `after_sha256.txt`;
  - `design_written_before_code.md` / `.sha256`;
  - `g3_s3.diff` (the modified files against HEAD, then the new ones; the
    range-server fixture by hash);
  - `tests_output.txt`, `tests_regression_g1_g5.txt`, `replay_range_server.md`,
    `replay_companion.md`, `sample_session_audit.jsonl` (the tests' 269 audit
    lines);
  - `mutation_check.py` / `.txt`;
  - `make_vectors_v2.py`, `setup_vectors_v2.json`;
  - `unit_tests.log`, `unit_tests_summary.txt`;
  - `handshake_harness.py`, `handshake_output.txt`;
  - `build_debug.log`, `apk_sha256.txt`;
  - `redact_check.txt`, `manifest.sha256`.
- Patch record: `patches/G3-S3_HARDENING_AND_HUB_HOST.md`. `PATCH_INDEX.md`
  was not updated (not session B's file). `CURRENT.md`, `CURRENT_HANDOFF.md`
  and `KNOWN_ISSUES.md` were not written.
- **Test expectations changed, disclosed:**
  - Three G3-S1 expectations assumed `diagnostics` could not be granted: a
    new record's permission list; `/status` and `/diagnostics/health` →
    `permission-unknown`; `/status` with a token → 403 over HTTP. They now
    read: the list with `diagnostics` and `permissions_v`; `permission-denied`
    for a record without it; 200.
  - In G3-S3's own range replay, the first run expected the LAN request
    with an unissued `?media_token=` to be served as today. By design it is
    refused (a failing credential never falls back), so that one case is
    asserted as refused.
  - Five G3-S2 client tests failed until the fake host verified v2. The
    tests themselves are unchanged.
- **Two stray shell fragments, disclosed:**
  - A `sed -i … /dev/null` rode along on one command. It refused ("not a
    regular file"); `/dev/null` was checked straight after: still the
    root-owned character device.
  - An `rm -f` named a temp file in this directory that never existed. It
    deleted nothing.
  - Separately, `sample_session_audit.jsonl` was regenerated once, replacing
    this session's own first copy.
- **The status file:** step 4's status line was folded into step 5's.
- **Left in place:** the tests' temporary stores and fixture trees under the
  system temp directory (`g3_s1_tests_*`, `g3_s3_range_*`, `g3_s3_mut_*`),
  `__pycache__/`, and Gradle's outputs and caches (all gitignored). The
  build output `app-debug.apk` is now G3-S3's. The CONFIRMED APK's copy is
  in `app/build/g3_s3_preserved/`.
- Not touched: `~/.config/privyhub/` (the paired-device store, the
  settings), `logs/session_audit.jsonl`, `privyhub_service.py`, and the
  running companion.
- No sudo, no nft, the Opal untouched, nothing fetched, nothing installed,
  no adb. Git status: `logs/g3_s3_git_status.txt`.
