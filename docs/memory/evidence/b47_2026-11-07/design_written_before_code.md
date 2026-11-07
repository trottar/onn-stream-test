# B47 — the movie retry on by default, and HOME-3's two VOD cosmetics (design, written and hashed before any B47 code)

Queue: `handoffs/QUEUE_2026-11-07O.md` §B47. The user: "Reconnect by default yes" (2026-11-06). The host half is G-A13
(`PRIVYHUB_VOD_LOG=1`, the fifteenth adopted line, 2026-11-07). Baseline `ea40a93f`; built in `/tmp/b_q07o_b47`.

## 1. The default (client)

- `VodRetryFlag.parse`: **absent / empty / junk / `1` = ON; `0` / `off` = OFF** (= `8ba4d996…`'s absent: no
  `VodRetryAndroid`, every `vodRetry?.` call a no-op, today's "Playback error" at once). `read()` failing = ON.
- Only the flag object changes; `MainActivity`'s one construction site (`VodRetryController.wanted(flag, isLive)`)
  is untouched, so live TV never gets a controller.
- **Disclosed (as B42):** `VodRetryTest.theFlagIsOneOnly` (B35) moves to "absent = on"; B43's
  `VodRetryTokenTest` needs no flag change (it builds the controller directly).

## 2. Cosmetic 1: "reconnecting…" cleared on `vod_resumed` in every path

HOME-3 C5'' (a): after a `reset` episode (4 attempts) the movie resumed and `vod_resumed` was written, yet the mark
stayed; after (b)'s `401` episode it cleared. Reading the code, `onReady` → `ui.hideMark()` → `hide()` removes the view
held in `mark`; the rows do not show which step left a view up (a second view added, or the removal missed). **Not
reproduced; the fix makes the clear unconditional and complete:**
- `VodRetryController.onReady`: at READY it **always** calls `ui.hideMark()` (also when no episode is open; idempotent)
  and **cancels any scheduled attempt** (`scheduler.cancel()`), so a late attempt cannot seek back or re-show the mark
  after the resume; the `vod_resumed` row is written exactly as today (once per open episode).
- `showMark` only while the episode is open (`retrying`), never after a resume.
- `VodRetryAndroid.hide()`: removes **every** view tagged as the mark from the player's overlay frame (not only the one
  in `mark`), and the same sweep runs again on the next main-loop turn (`handler.post`), so a view added in the same turn
  is also removed. `show()` tags its view and first sweeps any stale one.

## 3. Cosmetic 2: the range row written when the companion stops with a request open

The row is written in the request's `finally`. A companion restart sends SIGTERM to the whole cgroup; the range server
(a child, `ThreadingHTTPServer`, daemon request threads) dies on Python's default SIGTERM action, so no `finally` runs and
an open request's row is lost (HOME-3 (a)'s resumed `bytes=<P>-` row).
- **`vod_log.RangeLog`** keeps the open requests (their box, `t0`, `m0`, the handler) in a dict under a lock;
  `flush_open(closed="shutdown")` writes one row per open request with `closed: "shutdown"`, its bytes so far and its
  duration, and marks each box flushed so a request that finishes afterwards writes no second row.
- **`range_server.py`**, inside the existing `PRIVYHUB_VOD_LOG=1` block only (absent = today: no handler installed):
  `signal.signal(SIGTERM, …)` → `VOD_LOG.flush_open()`, then `raise SystemExit(0)` in the main thread (the serve loop
  ends; `server_close` as today; the daemon request threads end with the process). The handler class is not touched
  (B35's AST test stands).
- The `vod_range.jsonl` row's shape is today's; `closed` gains the value `shutdown`.

## 4. Tests

- **JVM:** absent / empty / junk / `1` → the flag on and the controller built (`wanted(parse(null), false)`); `0` /
  `off` → no controller; a `reset` episode → resume → the mark hidden and no attempt left scheduled; a READY with no open
  episode hides the mark and writes no row; a late scheduled attempt after a resume does not run.
- **Host (`tests/vod_log`):** a request held open (a slow client) + `flush_open()` → one row `closed: shutdown` with the
  bytes so far; the request then ending writes no second row; with nothing open no row; a real range-server process
  started with `PRIVYHUB_VOD_LOG=1`, a request left open, SIGTERM → the row on disk and the process exited 0; without
  the line SIGTERM → no row, the default action (today).

## 5. Not in B47

Media3's own reconnect timings; the host's drop test; any live-TV path.
