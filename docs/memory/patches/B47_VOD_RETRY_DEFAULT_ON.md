---
memory_schema: 1
as_of: 2026-11-07
baseline_commit: ea40a93f
---

# B47 — the movie retry on by default (`vod_retry` absent = on; `0` / `off` today), the mark cleared, the shutdown row

**Result: BUILT; JVM 4 new, 223 / 223 in the item's copy, 228 / 228 integrated; host 4 new (`vod_log` 16); 3 mutations
caught; `0` / `off` = `8ba4d996…`'s absent PROVEN; the host part inside the adopted `PRIVYHUB_VOD_LOG=1` (G-A13); no
live run.** Record: `evidence/B47_VOD_RETRY_DEFAULT_ON_2026-11-07.md`. Nothing committed.

- **Built:**
  - `VodRetryFlag` on unless `0` / `off`;
  - at every READY the "reconnecting…" mark is cleared and a scheduled attempt dropped, and every tagged mark is swept
    from the overlay (HOME-3 C5'' (a));
  - `RangeLog.flush_open` plus a SIGTERM handler in the range server's `PRIVYHUB_VOD_LOG` block: a request open at a
    companion restart gets `closed: "shutdown"`, and never a second row.
- **Files:**
  - `vod/VodRetry.kt`, `vod/VodRetryAndroid.kt`;
  - `VodRetryDefaultOnTest.kt` (new), `VodRetryTest.kt` (the flag case moved, disclosed);
  - `companion/vod_log.py`, `companion/range_server.py`;
  - `tests/vod_log/test_vod_log_b47.py` (new), `tests/vod_drop_test/test_vod_drop_test.py` (one structural assertion
    moved, disclosed).
- **Apply:** `git apply evidence/b47_2026-11-07/b47.diff` (integrated by `queue_o_combined.diff`).
- **Rollback:** on the onn, `setprop debug.privyhub.vod_retry 0`; on the hub the shutdown row goes with the fifteenth
  line (`vod-log.conf`); or reverse `b47.diff`.
