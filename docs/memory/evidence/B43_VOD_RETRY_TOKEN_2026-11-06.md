---
memory_schema: 1
as_of: 2026-11-06
baseline_commit: 795d80d4 (the tree clean at the start; B43 built in /tmp/b_q06n_b43, uncommitted)
---

# B43 — the movie retry made real: the token refetched on a refusal, a companion restart survived, "lost" only for no answer; B40's drop gains a refusal window

**Classification: SETTLED + BUILT.**
- **Client:** inside `debug.privyhub.vod_retry=1`, no new flag.
- **Host:** inside B40's `PRIVYHUB_VOD_DROP_TEST=1` (per run, never adopted), plus three whitelisted fields in B35's
  client log.
- **Tests:**
  - JVM `VodRetryTokenTest` 8 green, the whole suite 203 / 203 (195 + 8), three runs; B35's `VodRetryTest`
    unedited;
  - host `tests/vod_drop_test` 21 (B40's 14 unedited + 7) and `tests/vod_log` 12 (B35's 9 unedited + 3), three runs;
  - every host suite as the queue-N baseline (only those two counts grew);
  - **4 mutations caught**.
- **Proof:** absent = the CONFIRMED build's behaviour, PROVEN.
- NOT installed; NOT ADOPTED; no live run; nothing committed.

Design `b43_2026-11-06/design_written_before_code.md`, sha256 `47133b3f…334e`, hashed **17:55:21Z, before any B43 code**.
Precondition (the queue's): only the companion and `privyhub-diag` active; `git status --short` empty at the start.

## 0. Settled

- **Where the media token lives.** The movie's requests carry the session header, set per request by a
  `ResolvingDataSource`:
  - the chain is `identity/MediaDataSource.kt` → `PrivyHubIdentity.mediaHeader` → `IdentitySession.mediaHeaderFor`
    → `liveToken`;
  - `liveToken` returns the **cached** token while the onn's own clock says it is not near expiry;
  - the URL carries none.
- **Why B35 kept the dead token (HOME-2 C5' addendum):**
  - a companion restart empties the hub's in-memory session table, so the range-server gate answers that token
    **401**;
  - nothing on the media path drops the cached token. Control calls do: `IdentitySession.onResponse` drops it on a
    401 / 403 and sets up afresh. That is why a fresh start (`POST /sources/<id>/start`) recovered at 17:00:02Z;
  - B35's retry (seek / prepare / play) and its Retry button re-ran the same data source with the same header: 66 +
    24 GETs, all 401.
- **What a 401 is to the player today:** `InvalidResponseCodeException` (401) → `ERROR_CODE_IO_BAD_HTTP_STATUS` (2004).
  B35 treats it as a lost link and gives up with "The connection to the hub was lost." while the hub answers.
- **Media3 1.11.0's own reconnect** (disassembled from the cached aar, read-only:
  `media3_1.11.0_DefaultLoadErrorHandlingPolicy_javap.txt`):
  - **the retry delay** is `min((errorCount − 1) × 1000, 5000)` ms;
  - **never retried:** `ParserException`, `FileNotFoundException`, cleartext refusals, unexpected loader errors and a
    position out of range. **Resets and 401s are retried;**
  - **the minimum retry count** is 3 for a progressive VOD;
  - **progress resets the count** (`ProgressiveMediaPeriod.onLoadError` → `createRetryAction(madeProgress, …)`);
  - **the error surfaces** only through `maybeThrowError`, when the buffer is spent and errorCount > 3.
- **So the player's own reconnect covers any outage the buffer covers.** The VOD load control holds 15-30 s, and the
  loader retries every ≤ 5 s. HOME-2's 12.8-s single reset never surfaced, and B35 never ran.
- **The demonstration: `drop 45`.** That is 30 s (the buffer at most) + 5 s (one loader interval) + 10 s margin.
  - The player surfaces its error at ~30-35 s into the window.
  - B35's attempts at +1 / +2 / +4 / +8 s then straddle the window's end, so the resume comes ≤ 15 s after it.
  - The JVM model shows it: drop at 60 s → surfaced at 90 → attempts at 91, 93, 97, 105 → resumed. A 12-s drop: no
    rows (HOME-2's case).

## 1. Built (`b43_2026-11-06/b43.diff`)

**Client** (`vod/VodRetry.kt`, `vod/VodRetryAndroid.kt`; MainActivity: `{ player }` gains a comma and one argument
follows, `{ getCompanionHost() }`, inside B35's flag-only construction):
- **A reason per error,** read from the cause chain: `401` / `403` (`InvalidResponseCodeException.responseCode`),
  `timeout` (1003 / 2002, or a `SocketTimeoutException`), `refused` (a `ConnectException`), else `reset`
  (`VodRetryPolicy.reasonOf`).
- **A refusal is not a lost hub:**
  - the controller asks the new `Token` port to refetch: `IdentitySession.endSessionLocally()` then
    `mediaHeaderFor(host)`, on a background thread. That is the fresh setup a playback's first media request takes;
  - then the attempt at the saved position: **at once after a successful refetch** (the cause is fixed), after the
    backoff after a failed one (the hub still down);
  - three refusals in a row, each after a refetch, end the episode as **`refused`**. The dialog then reads "The hub
    refused this playback. Press Retry or start the movie again.", never "connection lost", and there are no 150 s
    of futile attempts.
- **"The connection to the hub was lost."** appears only when the 150-s bound runs out on `reset` / `refused` /
  `timeout`. The bound and the backoff are B35's, unchanged.
- **A companion restart is survived:**
  - while the hub is down, `refused` / `reset` follow B35's backoff;
  - the first 401 after it refetches → resumed at the saved position (the first error's, as B35).
- **The Retry button refetches first** (HOME-2: it reused the dead token).
- **Rows:** `vod_error` / `vod_retry` / `vod_gave_up` gain `reason`; a refusal's `vod_retry` gains `token_refetched`
  (bool) and its actual `delay_ms`; `vod_gave_up` gains `kind` (`lost` | `refused`).
- **Identity off** (a legacy LAN, no token): the refetch reports false. A 401 then retries to the bound and ends
  `refused`.

**Host:**
- **`companion/vod_log.py`:** the client whitelist gains `reason` (one of the five), `kind` (one of two) and
  `token_refetched` (a bool). Junk is refused; a B35 row is written as before.
- **`companion/vod_drop_test.py`** (B40's module; `range_server.py` not edited). The appended line `drop <seconds>`
  (0-600; the last non-empty appended line decides):
  - **One reset** of every streaming `/vod/` connection, as B40.
  - **Then the window:** for that many seconds every new `/vod/` request gets an **immediate RST and no HTTP
    response**. `do_GET` / `do_HEAD` are wrapped at install, before the gate, the file and the log; other paths are
    served.
  - **Why an RST, not a 503:**
    - a dead link gives no status. An RST reads `reset` on the onn, as a dropped link does;
    - a 503 is a hub answering (2004, like the refusals B43 treats differently);
    - Media3 retries both, so the player's own reconnect still runs and still gives up only with its buffer spent.
- **Only the appended bytes are read:** opened read-only, from the last seen size, ≤ 4 KiB. The file is still never
  written or removed. A shrunk or new file, a plain line, or `drop 0` = B40's one-shot, its row byte for byte.
- **Rows:**
  - `vod_drop_injected` gains `refuse_s` (only when > 0);
  - `vod_refuse_ended` (`trigger`, `refuse_s`, `vod_refused` = requests refused) closes each window: from the polling
    thread at its end, or first thing at a new trigger;
  - both go to `logs/vod_drop_test.jsonl`, and to `vod_range.jsonl` with B35's log on.

**A refinement of the design, disclosed:** the design said the attempt runs after the refetch but named no delay. The
first JVM run waited out B35's full backoff (15 s) after a successful refetch; the attempt now runs at once after a
successful refetch and keeps the backoff after a failed one.

## 2. Tests (`tests_jvm.txt`, the two JUnit xml, `tests_host_x3.txt`, `tests_regression_after.txt`, `tests_mutations.txt`)

- **JVM, `VodRetryTokenTest`** (a discrete-time simulation: a fake hub, a fake Media3 loader with the settled policy
  and a 30-s buffer, a fake token port):
  - **a companion restart with the movie open:** 12 s of no answer, then 401 → one refetch → `vod_resumed` at the saved
    position in < 30 s;
  - **a 45-s refusal:** the player's own reconnect surfaces once, after its buffer; then `vod_error` → `vod_retry`×n →
    `vod_resumed`; no refetch;
  - **a 12-s refusal:** no rows (the buffer covers it, as HOME-2 saw);
  - **the hub down:** `vod_gave_up` `kind: lost` after the bound;
  - **a refusal persisting after refetches:** `refused` after 3, in < 30 s, never lost;
  - **the Retry button** refetches first, then resumes;
  - **without the token port:** B35's rows as built, and no controller without the flag;
  - **the reason classification.**
- **Host:**
  - **`drop 0.8`** (the 45-s path scaled): the stream reset; two new `/vod/` requests get an RST and no HTTP byte;
    `/live/` is served; `vod_refuse_ended` `vod_refused: 2`; then the resume served 206;
  - **a plain line:** B40's row keys exactly, no window;
  - **`drop 0`** = a plain line;
  - **only appended bytes:** an old `drop 30` before the start never applies;
  - **a new trigger inside a window** closes it first;
  - **a loader retrying through the window** is reset every time, then served after it;
  - **the parse:** last line wins, the cap, junk = 0.
  - **`vod_log`:** the new fields when valid, junk refused, a B35 row as before.
- **Mutations, all caught:**

  | mutation | change | failures |
  | --- | --- | --- |
  | H1 | the window never refuses | 2 |
  | H2 | the whole file read (an old drop line applies) | 3 |
  | C1 | a refusal retried like a reset, no refetch | 2; the restart test reproduces HOME-2: `vod_gave_up` |
  | C2 | every give-up named `lost` | 1 |

- **Every host suite in the copy:** the queue-N baseline's outcomes line for line. Only `vod_drop_test` 14 → 21 and
  `vod_log` 9 → 12 changed; the four `tools/` tests fail in a copy as at every baseline.

## 3. Proof (`proof_flag_absent.py` / `_output.txt` / `.md`): absent = `0132b944…`'s behaviour, PROVEN

- **No `vod_retry` flag:** no controller. The flag's parse and `wanted` are unchanged, and MainActivity's one change
  sits inside the flag-only construction. The identity layer and `range_server.py` are byte-equal.
- **No `PRIVYHUB_VOD_DROP_TEST`:** nothing imported. A plain line = B40 as built.
- **`vod_log` and a B35 client:** its rows as before.

## 4. HOME-3 — C5'' (two parts; restarts outside 04:30-05:30Z, no game running)

**Setup (once):** the host lines for this run only, then restart.
```
printf '[Service]\nEnvironment=PRIVYHUB_VOD_LOG=1\nEnvironment=PRIVYHUB_VOD_DROP_TEST=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b43-vod-drop.conf
systemctl --user daemon-reload && systemctl --user restart privyhub-companion
adb shell setprop debug.privyhub.vod_retry 1
```
**(a) The 45-s drop**, the movie in front, nothing pressed on the onn, playing ≥ 1 min:
```
cd ~/Projects/onn-stream-test && mkdir -p runtime && echo "drop 45" >> runtime/vod_drop_test.trigger
```
- **Pass:**
  - `logs/vod_drop_test.jsonl`: `vod_drop_injected` with `dropped: 1`, `how: rst`, `refuse_s: 45.0`, then
    `vod_refuse_ended` with `vod_refused` ≥ 4 (the player's own reconnects);
  - `logs/vod_client.jsonl`: `vod_error` (`reason: reset`) → `vod_retry` × n (`reason: reset`) → `vod_resumed`, the
    first row ~30-35 s after the injection (the buffer) and the last ≤ 15 s after the window ends;
  - on screen "reconnecting…", then the movie at the error's position, with no "Playback error";
  - `logs/vod_range.jsonl`: the reset request `closed: client_reset`, then `range: bytes=<P>-` 206 after the window.
- **Invalid if** `dropped: 0` (nothing streaming), or no `vod_error` with the window over (the buffer covered it: run
  again with `drop 60`).

**(b) A companion restart with the movie open** (the player in front, playing ≥ 1 min):
```
systemctl --user restart privyhub-companion
```
- **Pass:**
  - "reconnecting…" on screen, then the movie resumes by itself at the position (within ~30 s of the hub being back),
    with no "connection to hub lost" and no Retry pressed;
  - `logs/vod_client.jsonl` holds a `vod_retry` with `reason: "401"` and **`token_refetched: true`**, then
    `vod_resumed`;
  - the hub's range log shows 401s stop after that refetch (`vod_range.jsonl`: `status` 401 then 206).
- **Note:** rows posted while the hub is down are lost (B35 posts once and ignores failures). So the pass rests on the
  rows after the hub is back; the first `vod_error` may be missing.

**Close:**
```
rm ~/.config/systemd/user/privyhub-companion.service.d/b43-vod-drop.conf && systemctl --user daemon-reload && systemctl --user restart privyhub-companion
adb shell setprop debug.privyhub.vod_retry ""
```

## 5. Files

- **`b43_2026-11-06/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `predecessors/` + `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `media3_1.11.0_DefaultLoadErrorHandlingPolicy_javap.txt`;
  - `b43.diff`, `proof_flag_absent.py` / `_output.txt` / `.md`;
  - `tests_jvm.txt`, `TEST-…VodRetryTokenTest.xml`, `TEST-…VodRetryTest.xml`, `tests_host_x3.txt`,
    `tests_regression_after.txt`, `tests_mutations.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `patches/B43_VOD_RETRY_TOKEN.md`.
- **The code** (in the copy, for the coordinator to merge):
  - `companion/vod_drop_test.py`, `companion/vod_log.py`;
  - `vod/VodRetry.kt`, `vod/VodRetryAndroid.kt`, `MainActivity.kt` (+2 lines, 1 changed);
  - `test/vod/VodRetryTokenTest.kt`, `tests/vod_drop_test/test_vod_drop_refuse.py`, `tests/vod_log/test_vod_log_b43.py`
    (new).
- **Left in /tmp:**
  - `b_q06n_b43` (the copy);
  - `b_q06n_b43_scratch/` (`media3/`, the extracted classes; `mut_h1`, `mut_h2`, `mut_c1`, `mut_c2`);
  - `b_q06n_b43_gradle*.txt`.
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched; nothing of A's touched;
  - nothing fetched (the Media3 aar read from the local gradle cache), deleted, adopted or committed.
