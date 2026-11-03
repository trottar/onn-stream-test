# B35 design (written and hashed before any B35 code) — the movie player retries; the hub logs every range request

Facts (TRIP-R2 §4): the long feature's connection ended client-side ~1 h 50 min in; no further request reached the
range server; the player (`MainActivity.kt:15564-15612`, Media3 `ExoPlayer`, `Player.Listener.onPlayerError`) saved
progress, marked the source "recently failed", showed "Playback error…" and stopped; the hub's range server
(`companion/range_server.py`, a `ThreadingHTTPServer` subprocess of the service, inheriting its environment) logged
only timestamp-less BrokenPipe / ConnectionReset tracebacks. Today there is no Retry button on a playback error (the
only "Retry" in MainActivity is the TV guide dialog's).

## Client — behind `debug.privyhub.vod_retry=1` (exactly `1` after trim; absent / empty / `0` / junk = today)

New file `PrivyHub/app/src/main/java/vod/VodRetry.kt` (package `com.safeiot.privyhub.vod`), pure Kotlin (no Android
type) so the JVM can test it:
- `VodRetryFlag` — `PROPERTY`, `parse(raw)` (`raw?.trim() == "1"`), `read()` (SystemProperties by reflection, any
  failure = off; CL-B7P's convention).
- `VodRetryPolicy` — **backoff 1, 2, 4, 8, 15 s, then 15 s each** (attempts at +1, +3, +7, +15, +30, +45 … s after the
  first error); **bound 150 s** (≥ 2 min) from the episode's first error; an attempt is scheduled only if it starts
  within the bound. **Retryable** = Media3 `ERROR_CODE_TIMEOUT` (1003) and the IO codes 2000 unspecified, 2001
  connection failed, 2002 connection timeout, 2004 bad HTTP status (a token or gate refusal while the link heals);
  not 2003 / 2005 / 2006 / 2007 / 2008 (content type, not found, no permission, cleartext, position out of range) nor
  any decoder / parser / DRM code — those go today's way at once.
- `VodRetryController(policy, player port, scheduler port, clock, rows sink, ui port, mediaId)`:
  - `onError(code, codeName, positionMs): Boolean` — true = handled (retrying; the caller returns before today's
    branch). Within an episode the **position is the first error's** (later failed attempts sit at the seek target).
    A `vod_error` row at the episode's first error; each scheduled attempt a `vod_retry` row (attempt n, delay, the
    elapsed ms); the ui shows the mark. Not retryable or past the bound → false (today's path runs) and, past the
    bound, a `vod_gave_up` row, the mark hidden, and the ui offers **Retry** (new, flag only).
  - the scheduled attempt calls `player.retryAt(positionMs)` (Android: `seekTo(pos)`, `prepare()`,
    `playWhenReady = true` on the same `ExoPlayer` and the same `MediaItem`: a fresh connection with a Range from the
    position).
  - `onReady()` — an open episode closes: `vod_resumed` row (attempts, elapsed ms, position), mark hidden, reset.
  - `manualRetry()` (the Retry button) — a new episode at the saved position, attempt at once.
  - `cancel()` — the pending attempt dropped (the user left playback / a new item).
- Rows (maps): `event`, `media` (12 hex of sha256 of the source id — no title, no path, no URL), `attempt`,
  `position_ms`, `error_code`, `error_name` (Media3's code name, never the message — a message can carry a URL),
  `delay_ms`, `elapsed_ms`, `bound_ms`.

Android glue `vod/VodRetryAndroid.kt`: the Handler scheduler, the mark (a small "reconnecting…" `TextView` added to
`PlayerView.overlayFrameLayout`, top-end, removed when hidden), the Retry `AlertDialog` ("Retry" / "Close"), and the
row poster (a daemon thread, `POST http://<hub>:<control>/diagnostics/vod-client`, JSON, `PrivyHubIdentity.decorate`,
1.5-s timeouts, every failure ignored).

`MainActivity.kt` hunks — each a `vodRetry?.` call on a field that is **null unless the flag reads `1`** and the
playback is not live:
1. a field `private var vodRetry: VodRetryAndroid? = null`;
2. in `playMedia`, after `releasePlayer(...)`: the field built when `!isLive && VodRetryFlag.read()`;
3. in `onPlayerError`, after today's `saveCurrentProgress()` (the save still happens): `if (vodRetry?.onError(...)
   == true) return`; after today's branch (the error text set): `vodRetry?.afterTodaysError()` (offers Retry only when
   the controller gave up);
4. in `onPlaybackStateChanged`, at `STATE_READY`: `vodRetry?.onReady()`;
5. in `releasePlayer`, first: `vodRetry?.cancel(); vodRetry = null`.
Flag absent: the field stays null, every hunk is a null-safe no-op — today's calls in today's order.

## Host — behind `PRIVYHUB_VOD_LOG=1` (exactly `1`; absent / other = today: nothing imported, nothing written)

New `companion/vod_log.py`:
- `opaque_id(request_path)` — 12 hex of sha256 over `privyhub-vod:` + the URL path (the query, which can carry the
  media token, is dropped first). No address, no title, no path in any row.
- `RangeLog(project_root).install(handler_class)` — wraps, on the class, `send_response` (the first status),
  `send_header` (`Content-Length`), `copyfile` (a counting writer around the socket file) and `do_GET` / `do_HEAD`
  (the clock, then one row after the method returns or raises; **the exception re-raised**, so today's traceback still
  reaches the range-server log). Row into `logs/vod_range.jsonl` (rotating, `games.log_rotation.append_line`, 5 MB ×
  3), one per request: `at_utc` (start, ms), `end_utc`, `method`, `id`, `kind` (`vod` / `media`), `range` (the header
  if it is `bytes=N-M`, else `invalid` / absent), `status`, `length`, `bytes`, `duration_ms`, `closed`:
  `complete` (bytes = length, or no body expected: HEAD, 3xx/4xx/5xx → `no_body`), `client_reset`
  (`ConnectionResetError`), `broken_pipe` (`BrokenPipeError`), `error` (any other exception, its class name in
  `error`), `short` (returned with fewer bytes than the length).
- `ClientLog(project_root).accept(payload)` — the client's four rows (`vod_error` / `vod_retry` / `vod_resumed` /
  `vod_gave_up`) whitelisted field by field (ints; `media` 12 hex; `error_name` `[A-Z_]{1,64}`), anything else
  rejected (`ValueError` → 400); one row with `at_utc` into `logs/vod_client.jsonl`.
- `range_server.py`: one guarded block after `RANGE_GATE`'s (`VOD_LOG = None`; with the line, import and
  `VOD_LOG.install(RangeRequestHandler)` after the class). Absent: the class body is not edited at all.
- `privyhub_service.py`: one guarded import block beside G5-S1's (`VOD_CLIENT_LOG = None`), and in `do_POST` one branch
  `if VOD_CLIENT_LOG is not None and request_path == "/diagnostics/vod-client":` before `/diagnostics/client-health`.
  Absent: the branch's test is false before the path is read; the request falls through as today. Identity v2: the
  path is `/diagnostics/…` → the `diagnostics` permission (default on for a paired device), on both sides already.

## Tests
- `tests/vod_log/` (host, loopback only): a real `RangeRequestHandler` subclass with the log installed, a temp root
  with a 1 MiB file under `vod/`:
  - a client reads 100 KiB of `Range: bytes=0-` and resets (SO_LINGER 0) → one row, `client_reset` or `broken_pipe`,
    `bytes` < `length`, the range, a 12-hex id, no path or title or address in the row;
  - a full ranged read → `complete`, `bytes` = `length`, 206; a resume at a position (`bytes=P-`) → `complete`, 206;
  - a missing file → 404 `no_body`; HEAD → `no_body`;
  - `ClientLog`: the four events accepted, junk / unknown keys / a URL in a string rejected;
  - **absent:** a fresh `python3 -c 'import range_server'` without the line: `VOD_LOG` None, `vod_log` not in
    `sys.modules`; the class's AST equal to the base file's; the raw response bytes (Date stripped) of the base and the
    new server for the same request equal; `privyhub_service.py`'s new blocks guarded (AST), no top-level import.
- `PrivyHub/app/src/test/java/vod/VodRetryTest.kt` (JVM, fake clock / scheduler / player): the flag parse; the
  backoff list and the bound; **a fake server that drops the connection at a byte position** (the fake player plays
  from the server until the drop, raises 2001 at that position; the server is back after 10 s) → the attempts at
  +1 / +3 / +7 / +15 s, the 4th resumes **at the drop's position** within the bound, rows `vod_error`, `vod_retry` ×4,
  `vod_resumed`; **the server down** → attempts to the bound, `vod_gave_up` at ≤ 150 s with ≥ 120 s elapsed, false
  returned (today's error path runs), Retry offered; Retry → a new episode at the position; a non-retryable code →
  false at once, no row; `cancel()` drops the pending attempt; **absent** → no controller (flag off or live), so the
  caller's `vodRetry?.` hunks are no-ops.
- Mutations: the backoff's position taken from the failed attempt instead of the first error (the resume test fails);
  the range log's `closed` always `complete` (the drop test fails).

## Not done
No install, no stream, no restart; the live range server keeps its loaded code until A restarts the companion with the
line; nothing adopted.
