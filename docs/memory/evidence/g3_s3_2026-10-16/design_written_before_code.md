# G3-S3 — the design, written before any G3-S3 code

Every change below is behind the existing flags: the host's
`PRIVYHUB_SESSION_IDENTITY=v2` (absent: `session_identity` is never imported,
and the range server never imports it either) and the client's `identity_v2`
(off: no new call, no new header, no new field, today's bytes).

## What the survey found (before the code)

- **Hub discovery today is a setting, not discovery.** The client reads one
  hand-entered "companion host" (`companion_host` in `privyhub_prefs`) in
  `MainActivity`, `TvEpgRepository`, `TvStateSyncClient`, and passes it to
  `NativeStreamActivity` / `DiagnosticsActivity` as an intent extra. There is
  no mDNS / NSD lookup. "Hub host" therefore overrides that setting.
- **The range server** (`companion/range_server.py`, port 8000) is a child
  process of the companion (`Popen`, environment inherited). It serves the
  VOD library (`/vod/…`), the generated live HLS, and the game artwork. It
  holds no session state: the tokens live in the companion's memory.
- **The client's player** is Media3 ExoPlayer over `DefaultHttpDataSource`,
  which **can send request headers** (it already sends `Referer` for some
  sources). The same player also plays third-party IPTV URLs, so a header
  must be scoped to the hub's media URLs only. Artwork is fetched with
  `HttpURLConnection` (headers possible).
- `native-stream-start` already compares `?port=` with the signed
  `video_port` (G3-S1). The audio and controller ports are fixed constants on
  both sides; no call names them today. The client declares `audio_port`
  unsigned, and the host ignores it (CL-B2 §6).
- TV-sync (`/plugins/tv_state/*`) and EPG (`/plugins/epg/*`) already map to
  `tv`; the client sends no token on them, so over the overlay they would be
  refused `legacy-overlay`. `/status` and `/diagnostics/*` map to
  `diagnostics`, which is not grantable (`permission-unknown`).

## Host

1. **Setup canon v2** (`privyhub-session-setup-v2`): a body with
   `"sig_v": 2` is verified over `v2 \n device_id \n nonce \n media_host \n
   video_port \n audio_port \n overlay_host` (an absent field is the empty
   string). Without `sig_v` the v1 canon is verified as today (the CL-B2
   APK keeps working); `audio_port` / `overlay_host` are then ignored, as
   today.
2. **The declared-port binding.** The session stores the signed
   `video_port` and (v2) `audio_port`. `native-stream-start` with a token:
   `port` must equal the signed `video_port` (as today), missing or
   duplicated → mismatch; if the call names `audio_port` or `controller_port`
   it must equal the signed value (no signed value → mismatch). Refusal: 403
   `endpoint-port-mismatch`, audited (`session_refused`, with
   `port_kind`). Legacy LAN: unchanged.
3. **The overlay address.** A v2 setup may declare `overlay_host` (IPv4, in
   the overlay class, else `endpoint-invalid`). The media target is the
   declared address **whose class matches the request's routing class**:
   an overlay source streams to `overlay_host` (or to `media_host` if that
   is overlay-class), a LAN source to `media_host`. The class rule of G3-S1
   is otherwise unchanged (`endpoint-class-mismatch`).
4. **The media token.** Issued with every session token (`media_token` in
   the setup response; random, 24 bytes), bound to the session's client id,
   expiring and revoked with it (`/session/end`, device revocation). Never
   logged: the audit records `media_token_used: true|false`, never the value.
5. **The range server's gate.** Only when the flag is set does
   `range_server.py` build a gate (the import inside that `if`; absent →
   today's handler, byte for byte). Per request:
   - loopback → allowed (the hub's own tools);
   - LAN with no token → allowed if `legacy_unpaired_lan` (today), not
     audited one by one (as G3-S1's legacy calls); else 401 `legacy-disabled`;
   - anything else (a token header or `media_token` query on any network;
     overlay / unknown without either) → the range server asks the
     companion on loopback, `POST /session/media-check {routing, path,
     token | media_token}` (host-local only). The companion decides with the
     same session table: `token-unknown` / `token-expired` /
     `device-revoked` / `media-token-unknown`, the `vod` permission
     (`permission-denied`), overlay / unknown without a token →
     `legacy-overlay` / `legacy-unknown-network`, an unknown flag value →
     `identity-flag-unknown`. Refusals are audited
     (`media_refused`); the first accepted use of each token is audited
     once (`media_session`, with `media_token_used`).
   - the companion unreachable → 503 `identity-unavailable`, audited by
     the range server itself.
   - The range server's own request log masks the `media_token` value
     under the flag (`media_token=<redacted>`).
6. **Diagnostics.** `diagnostics` becomes a grantable permission. A new
   pairing's record lists `games, tv, vod, diagnostics` and carries
   `"permissions_v": 2`. A record without `permissions_v` (paired before
   G3-S3, e.g. CL-B2's) is granted `diagnostics` implicitly ("default on for
   a paired device"); revoking it = writing the record's list without it and
   `"permissions_v": 2`. `/status` and `/diagnostics/*` (but
   `/diagnostics/client-health` → `games`) need it.
7. **TV-sync and EPG:** already `tv`; the change is the client sending the
   token. Over the overlay with no token: `legacy-overlay`, as today.
8. **`/session/status`** (host-local) adds `permissions_known`,
   `default_paired_permissions`, and `sessions`: per live session its
   client id, kind, permissions, `media_token_live` (a boolean) and the
   seconds left. No address, no token, no media token.
9. New reason codes: `media-token-unknown`, `identity-unavailable`, and the
   media-check's own `host-local-only`; each audited where it fires.

## Client (behind `identity_v2`)

1. **"Hub host"** in Settings, under the identity checkbox: empty = today
   (the companion host). Set and the setting on: every call (catalogue,
   games, sources, the stream, TV-sync, EPG, diagnostics, media, artwork)
   goes to it. One function decides (`PrivyHubIdentity.effectiveHost`);
   the settings field still shows the stored companion host.
2. **The setup** signs v2 (`sig_v: 2`) with `audio_port` and, when present,
   `overlay_host`: the IPv4 address of a local interface in the overlay
   block (the Tailscale interface), found by enumerating interfaces (no
   packet sent).
3. **The token on every audited call:** the existing hooks, plus
   `TvStateSyncClient`, `TvEpgRepository`, `DiagnosticsActivity` (`/status`,
   `/diagnostics/*` now under `diagnostics`), the player's requests to the
   hub's media port (a Media3 `ResolvingDataSource` that adds the header
   only when the URI's host and port are the hub's media endpoint; never on
   a third-party URL), and the artwork fetch. The player uses the
   **header**; the media token is stored, and offered as `media_token=` for
   a player that cannot set headers (none in this APK).
4. Refusals: the host's reason code shown (toast, settings line), one retry
   on `token-unknown` / `token-expired`, as G3-S2. The player's 401 cannot be
   retried inside one load; the next load sets up afresh.
5. No address, token or hub host in any log line the change adds; the
   player's "Opening media" line logs the URL with the host replaced by a
   12-hex hash under the setting.

## Verification

Host unit tests for every new accept / refuse case; G3-S1's handler replay
extended (range server: the baseline's handler from `git show HEAD`, flag
absent, byte for byte, plus TV / EPG / diagnostics requests on the
companion); the G1 / G3 / G5 suites; client unit tests (v2 vectors made with
the host's code); the G3-S2 handshake harness extended (v2 setup, overlay
host, the port mismatch, TV / EPG / diagnostics tokens, the range server
over the overlay with the header and with the media token); the debug APK
built and hashed, not installed; the redactor.
