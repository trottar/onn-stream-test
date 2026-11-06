# B43 — the movie retry made real: design, written before any B43 code (2026-11-06)

Queue: `handoffs/QUEUE_2026-11-06N.md` §B43. Facts: `HOME_2_HOLD_PADS_VOD_2026-11-03.md` C5' and `home2_2026-11-03/c5/C5.md`
(the addendum). Base: HEAD 795d80d4, `/tmp/b_q06n_base`; the CONFIRMED client `0132b944…`.

## 0. Settled (from the code and the addendum)

1. **Where the media token lives.** The movie's requests carry the session header, set per request by a
   `ResolvingDataSource` (`identity/MediaDataSource.kt` → `PrivyHubIdentity.mediaHeader` →
   `IdentitySession.mediaHeaderFor` → `liveToken`). `liveToken` returns the **cached** `token` while
   `now < expiresAtMs - REFRESH_MARGIN_MS`, by the onn's own clock. The URL carries no token.
2. **Why B35 kept the dead token.** A companion restart empties the hub's session table (`session_identity`,
   in memory), so the range-server gate answers every request with that token **401**. Nothing on the media path drops
   the cached token. Control calls do: `IdentitySession.onResponse` drops it on a 401 / 403 with a retryable reason and
   sets up afresh. That is why a fresh start (`POST /sources/<id>/start`, a control call) recovered at 17:00:02Z.
   B35's retry (`retryAt` = seek / prepare / play) and its Retry button only re-ran the same data source, so each request
   carried the same dead header: 66 + 24 GETs, all 401.
3. **What a 401 is to the player today:** `HttpDataSource.InvalidResponseCodeException` (`responseCode` 401) →
   `PlaybackException` `ERROR_CODE_IO_BAD_HTTP_STATUS` (2004).
   - B35 counts 2004 as retryable and treats it like a lost link.
   - Its give-up dialog says "The connection to the hub was lost." even though the hub answered every request.
4. **Media3 1.11.0's own reconnect** (disassembled from the cached aar, read-only;
   `media3_1.11.0_DefaultLoadErrorHandlingPolicy_javap.txt`):
   - **The delay:** `getRetryDelayMsFor` = `min((errorCount − 1) × 1000, 5000)` ms, so 0, 1, 2, 3, 4, then 5 s each.
   - **Never retried:** `ParserException`, `FileNotFoundException`, `CleartextNotPermittedException`,
     `UnexpectedLoaderException`, a position out of range. **401 and a connection reset are retried.**
   - **When it surfaces:** `getMinimumLoadableRetryCount` = 3 for a progressive VOD. `ProgressiveMediaPeriod` resets the
     count whenever a load made progress (`createRetryAction(madeProgress, …)`). The loader throws only through
     `maybeThrowError` when errorCount > 3 **and** the player needs data it does not have.
   - **So the player's own reconnect covers any outage shorter than the buffer.** The VOD load control buffers 15-30 s
     (`setBufferDurationsMs(15000, 30000, …)`), and the loader keeps retrying every ≤ 5 s. HOME-2's single reset
     (12.8 s to the reopen) never surfaced, so B35 never ran.
   - **To reach B35, the hub must stay unreachable longer than the buffer can hold** (≤ 30 s) plus one retry interval
     (5 s) plus a margin.
   - **Chosen demonstration: `drop 45`** (30 + 5 + 10 s margin). At 45 s the player has surfaced the error at ~30-35 s
     (errorCount ≥ 4 by then), and B35's attempts at 1 / 2 / 4 / 8 s land on both sides of the window's end, so a
     resume follows within ≤ 15 s of it.

## 1. The client, inside `debug.privyhub.vod_retry=1` (no new flag; absent = `0132b944…` byte for byte)

`VodRetryController` (pure Kotlin) gains:
- **A reason per error,** classified by the Android side from the exception chain and passed in:
  - `401` / `403`: `InvalidResponseCodeException.responseCode`;
  - `timeout`: code 1003 / 2002, or a `SocketTimeoutException` in the chain;
  - `refused`: a `ConnectException` in the chain;
  - `reset`: every other retryable IO error.
- **A refusal (401 / 403) is not a lost hub.**
  - Before the next attempt the controller asks a new `Token.refresh(done)` port to drop the cached token and set up
    afresh: `IdentitySession.endSessionLocally()` then `mediaHeaderFor(host)`, on a background thread. That is the same
    setup path a playback's first media request uses.
  - Only then does `retryAt(position)` run. A refetch that fails (the hub still down) is noted (`token_refetched:
    false`) and the attempt runs anyway: the next error re-classifies.
  - **A refusal that persists:** three consecutive refused attempts, each after a successful refetch, end the episode
    as `refused`. The message is "The hub refused this playback. Press Retry or start the movie again." with Retry,
    **never "connection lost"**, and no 150 s of futile attempts.
- **"Connection to hub lost" only for no response:** the give-up past the 150-s bound keeps B35's message only when
  the episode's last error was `reset` / `refused` / `timeout`. The bound and the backoff are B35's, unchanged.
- **A companion restart is survived:**
  - while the hub is down, `reset` / `refused` retries follow B35's backoff;
  - when it is back, the first `401` triggers the refetch → the new token → the resume at the saved position (the
    episode's first-error position, as B35).
  - A restart longer than the bound gives up as `lost`, as B35.
- **The Retry button** (past the bound) refetches the token first too (HOME-2: it reused the dead one).
- **The rows:**
  - `vod_error` gains `reason`;
  - `vod_retry` gains `reason` (the error that led to this attempt) and, after a refusal, `token_refetched`
    (bool);
  - `vod_gave_up` gains `reason` and `kind` (`lost` | `refused`).
  - The host's `vod_log.ClientLog` whitelist gains `reason` (one of the five), `kind` (one of two) and
    `token_refetched` (bool). A row without them (B35's client) is written as today.
- **The Android side** (`VodRetryAndroid`):
  - classifies; implements `Token` via `PrivyHubIdentity.get(activity)` with the host from a new constructor lambda
    (MainActivity's B35 construction passes `{ getCompanionHost() }`, inside its flag-only branch);
  - posts the result to the main thread;
  - shows the dialog's message by `kind`.
  - **Identity off** (legacy LAN): `refresh` does nothing and reports false; a 401 then ends as `refused` after three
    attempts.

## 2. The host, inside `PRIVYHUB_VOD_DROP_TEST=1` (B40's flag; per run, never adopted)

- **The trigger file's new bytes are read.** B40 compared only (mtime_ns, size).
  - On a change with size > the last seen size, B43 opens the file read-only, seeks to the last seen size and reads
    only the appended bytes (≤ 4 KiB); the file is still never written or removed.
  - The last non-empty line decides: `drop <seconds>` (an integer or decimal, 0-600) gives `refuse_s`; anything else
    (B40's `date` line) gives 0.
  - A shrunk or replaced file gives 0 (as built: one drop).
- **`refuse_s` = 0 is B40 as built:** one reset of every streaming `/vod/` connection and the same row, byte for byte
  (no new key).
- **`refuse_s` > 0:** the same reset, then for `refuse_s` seconds every new `/vod/` request is answered by an
  **immediate RST and no HTTP response**.
  - **How:** B40's `install` also wraps `do_GET` / `do_HEAD`; inside the window a `/vod/` request is reset (B40's
    `reset()`: `SO_LINGER {1,0}` + AF_UNSPEC connect), `close_connection` is set, and nothing else runs (the gate, the
    file, the log all skipped). Other paths are served as today.
  - **Why an RST, not a 503:**
    - A dead link gives the player no HTTP status. An RST surfaces exactly as a dropped link: a `SocketException`
      "Connection reset", which is `reset` in the rows.
    - A 503 is a hub answering. It would read `ERROR_CODE_IO_BAD_HTTP_STATUS` like B43's refusals, and so would test
      the wrong branch.
    - Media3 retries both, so the player's own reconnect still runs and still gives up only when the buffer is gone.
- **The rows:**
  - `vod_drop_injected` gains `refuse_s` (only when > 0);
  - at the window's end (the polling thread) a `vod_refuse_ended` row: `refuse_s`, `vod_refused` (the count of
    requests refused), `trigger`.
  - A new trigger inside a window closes the old window first (its `vod_refuse_ended`), then starts its own.
  - The same two outputs as B40 (`logs/vod_drop_test.jsonl`, and `vod_range.jsonl` when B35's log is on).

## 3. Tests

- **JVM** (`VodRetryTokenTest`, fake clock / scheduler / player / token / server; B35's `VodRetryTest` unedited and
  green):
  - **a companion restart:** resets while the hub is down, then a 401 → refetched (`token_refetched` true) → resumed
    at the saved position; the rows `vod_error` (`reset`) → `vod_retry` × n → `vod_retry` (`401`) → `vod_resumed`;
  - **a 45-s refusal:** a fake Media3 loader (B43's settled policy: 0, 1, 2, 3, 4, 5 … s, surfacing at errorCount > 3
    once a 30-s buffer is spent) gives up first; then `vod_error` → `vod_retry` × n → `vod_resumed` after 45 s;
  - **the hub down:** "lost" after the 150-s bound, `kind` `lost`;
  - **a persistent 401 with a working refetch:** `refused` after three, never "lost";
  - **the Retry button** refetches;
  - **absent:** `wanted(false, …)` = no controller (B35's absent test unchanged).
- **Host** (`tests/vod_drop_test`, B40's 14 unedited):
  - `drop 45` (a short window in the test, e.g. `drop 0.6`) → the current connection reset, every new `/vod/` request
    reset for the window, `/other` served, then served again after it; the rows `refuse_s` / `vod_refuse_ended`
    `vod_refused` n;
  - a plain line → B40's row byte for byte (no `refuse_s`) and no refusal;
  - `drop 0` = a plain line; only the appended bytes are read (an old `drop 30` before the start never applies).
- **`tests/vod_log`** (B35's suite):
  - the new fields accepted when valid, refused when junk;
  - a row without them written as today. B40's filter line stays; the module's AST count is unchanged unless a node is
    added (none is planned: the whitelist constants change in place, disclosed).

## 4. Absent = today

- **Client:** every change sits behind B35's controller, which exists only with the flag. MainActivity's one added
  argument is inside the flag-only construction.
- **Host:** `vod_drop_test.py` is imported only with `PRIVYHUB_VOD_DROP_TEST=1`. `vod_log.py`'s client whitelist only
  widens, for keys no flag-absent client sends. `range_server.py` is not edited.
