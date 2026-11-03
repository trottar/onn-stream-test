---
memory_schema: 1
as_of: 2026-11-02
baseline_commit: e0155d1c
---

# B40 — a hub-side VOD drop for the bench (`PRIVYHUB_VOD_DROP_TEST=1`, per run, never adopted)

**Result: BUILT. `tests/vod_drop_test` 14 green ×3; B35's `tests/vod_log` 9 green (one filter line); every suite as the
baseline; 3 mutations caught; absent = today PROVEN; no live run.**
- Record: `evidence/B40_VOD_DROP_TEST_2026-11-02.md`.
- Diff: `evidence/b40_2026-11-02/b40.diff`.
- Nothing committed.

**What it does:**
- **The control** is a file, not a signal. A `SIGUSR1` would kill a range server running without the flag, and
  nothing records its pid.
  - A appends a line to `<repo>/runtime/vod_drop_test.trigger`. The range server's thread sees the change of
    (mtime, size) within 250 ms. The signature at start is the baseline.
  - Each append drops once. The file is never removed.
- **The drop:** every `/vod/` connection streaming a body is reset with `SO_LINGER {1,0}` + a Linux
  `connect(AF_UNSPEC)`, a real RST. B35's row reads `client_reset`, and the player's read fails with a connection
  reset.
- **The row:** `vod_drop_injected` (`trigger`, `dropped`, opaque `ids`, `how`) into `logs/vod_drop_test.jsonl`, and
  into `logs/vod_range.jsonl` with B35's log.

**Files:**
- `companion/vod_drop_test.py` (new);
- `companion/range_server.py` (+15: `VOD_DROP_TEST = None` and one guarded block after B35's);
- `tests/vod_drop_test/` (new);
- `tests/vod_log/test_vod_log.py` (B35's: one filter line for B40's two nodes).

**Apply:** `git apply evidence/b40_2026-11-02/b40.diff` from the repo root. It acts only with
`PRIVYHUB_VOD_DROP_TEST=1` in the companion's environment at its start (a bench drop-in, then a restart).

**Use** (HOME-2's C5'): `mkdir -p runtime && date -u +%FT%TZ >> runtime/vod_drop_test.trigger` while the movie plays.

**Rollback:** no line (today's). Or `git apply -R` the diff.
