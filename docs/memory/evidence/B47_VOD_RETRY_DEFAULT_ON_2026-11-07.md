---
memory_schema: 1
as_of: 2026-11-07
baseline_commit: ea40a93f (the tree clean; B47 built in /tmp/b_q07o_b47, integrated by queue O's coordinator)
---

# B47 — the movie retry on by default, and HOME-3's two VOD cosmetics

**Classification: BUILT.** The client is on by default (`debug.privyhub.vod_retry` absent = on, `0` / `off` = today),
the G-A13 client half. The host half lives inside the adopted `PRIVYHUB_VOD_LOG=1`.
- **Tests:** JVM 4 new (`VodRetryDefaultOnTest`) and `VodRetryTest.theFlag` moved; the whole JVM suite 223 / 223 in the
  item's copy (228 / 228 integrated). Host `tests/vod_log` 12 → 16, green ×3; `vod_drop_test` 21 OK with one
  structural assertion moved (disclosed); every host suite as the baseline copy.
- **Mutations:** 3 caught:
  - B35's hide-at-the-row-only → 2 JVM fail;
  - the flag back to `== "1"` → 2 JVM fail;
  - `flush_open` not marking the boxes flushed → 1 host fail.
- **Proof:** `0` / `off` = `8ba4d996…`'s absent (`b47_2026-11-07/proof_flag_off.md`).
- NOT installed; no live run; nothing committed.

Design `b47_2026-11-07/design_written_before_code.md`, sha256 `63b1e12b…0d89`, hashed **18:28:12Z, before any B47
code**.

## 1. Built (`b47.diff`, 8 files)

- **The default:** `VodRetryFlag.parse` is on unless `0` / `off`, and a failed read is on. `MainActivity`'s
  construction (`wanted(flag, isLive)`) is unchanged, so live TV never gets the retry.
- **Cosmetic 1, "reconnecting…" cleared at every resume.**
  - **The cause was not found.** The rows show `vod_resumed` written, so `hideMark` ran. Which step left a view on
    screen is not visible in them.
  - **The fix makes the clear unconditional and complete:**
    - `onReady` always cancels a scheduled attempt and hides the mark (also with no open episode);
    - the `vod_resumed` row is written as before, once per episode;
    - `showMark` runs only while the episode is open;
    - `VodRetryAndroid` tags the mark and removes **every** tagged view from the overlay, now and again on the next
      main-loop turn; `show()` first sweeps any stale one.
  - The test models HOME-3 (a): the player's own reconnect reaches READY while attempt 4 is still scheduled. The mark
    is hidden, nothing stays scheduled, and there is no seek back.
- **Cosmetic 2, the range row at a companion restart.**
  - **The cause:** a restart sends SIGTERM to the cgroup. The range server died on Python's default action, so the open
    request's `finally` (its row) never ran.
  - `RangeLog` now keeps the open requests. `flush_open("shutdown")` writes each one with `closed: "shutdown"` and its
    bytes so far, and marks it flushed, so a request that finishes afterwards writes no second row.
  - `range_server.py`, inside the existing `PRIVYHUB_VOD_LOG=1` block, installs a SIGTERM handler: flush, then
    `SystemExit(0)`. Without the line there is no handler (today).
- **Files:**
  - `VodRetry.kt`, `VodRetryAndroid.kt`;
  - `VodRetryDefaultOnTest.kt` (new), `VodRetryTest.kt` (the flag case moved);
  - `companion/vod_log.py`, `companion/range_server.py`;
  - `tests/vod_log/test_vod_log_b47.py` (new), `tests/vod_drop_test/test_vod_drop_test.py` (one assertion moved:
    B40's structural check now also allows the changed `PRIVYHUB_VOD_LOG` block; B40's own two nodes are checked as
    before).

## 2. Tests

**JVM:**
- absent / empty / junk → the controller is built; `0` / `off` / live → none;
- a `reset` episode → READY with an attempt pending → the mark is gone, nothing is scheduled, no late seek, a later
  READY writes no row;
- a READY with no episode → no row, the mark hidden;
- after `cancel`, nothing is shown or hidden.

**Host:**
- a slow client holding a request, then `flush_open` → one row: `shutdown`, 206, the range, the bytes so far, no name;
  the request then reset → no second row;
- nothing open → no row; a closed request is `complete` as before;
- **a real range-server process** (a copy in a temp tree, so its log is the temp tree's):
  - with `PRIVYHUB_VOD_LOG=1`, a request open, SIGTERM → exit 0 and the `shutdown` row on disk;
  - without the line → exit −15 and no `logs/` (today).

## 3. Live

- **On the onn:** from this APK, a movie with no property set retries by itself (B35 + B43).
- **On the hub, after the next companion restart:** with the fifteenth line already set, a request open at a later
  restart gets its `shutdown` row. Nothing else changes; the adopted lines are untouched.

## 4. Files

`b47_2026-11-07/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `.sha256` + `design_hashed_at.txt`;
- `predecessors/` + `predecessor_sha256.txt`, `after_sha256.txt`;
- `b47.diff`;
- `proof_flag_off.md`;
- `tests_jvm.txt`, `tests_vod_log_x3.txt`, `tests_mutations.txt`, `tests_host_b47.txt`;
- `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B47_VOD_RETRY_DEFAULT_ON.md`.
