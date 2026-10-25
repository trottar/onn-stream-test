---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 13ccff5 (+ B21)
---

# B22 — `PRIVYHUB_RESTART_FAST=1`: a guarded restart's start answered before the old teardown; the client's release at the new stream's first fresh frame

**Result: SETTLED + BUILT; host `tests/restart_fast` 13 green; JVM 146 / 146; absent proven; APK `6bddafc0…a927`
pinned, NOT installed; no live run.** Record: `evidence/B22_RESTART_FAST_2026-10-24.md`. Diff:
`evidence/b22_2026-10-24/b22.diff`. Nothing committed.

- **Settled:**
  - the host's 2.0-2.2 s = the old audio's teardown before the encoder's kill (~0.78 s) + the new encoder (~0.45 s)
    + a fixed 0.75-s check and the new audio (~0.85 s);
  - the client's 8.8 / 4.2 s = the start-up gate's baseline + 6 clean 500-ms ticks (≥ ~3.5-4 s), press 1 reset at
    least once. The picture itself was back ~1.3-2.0 s after `startSession`.
- **Host** (`companion/restart_fast.py`, the flag): for `guard_end=1` on Linux with an old encoder running:
  - the response is a `status()` snapshot + `restart_fast` armed, sent once a worker holds the manager's lock;
  - the worker kills the old encoder first, stops the old audio beside the new encoder, starts the new encoder as
    today's start does, runs today's 0.75-s check (≥ once), then `prepare` and the new audio;
  - the ready's `status()` waits on the lock;
  - rows `restart_fast_config` / `restart_fast` / `restart_fast_done` / `restart_fast_failed`.
- **Client** (inside `restart_guard`, armed only by the key):
  - a 50-ms tick releases at the first fresh frame after the SSRC switch, once the old report's post is done (cap
    1 s); today's gate stays the fallback;
  - the rebuilt audio receiver starts at the ready's return;
  - report keys `restart_fast_*` (incl. the gate's resets and their reason).
- **Absent:** no host flag → today's start, no key → the client as `20e3e339…`; `restart_guard 0` → no guard.
- **Files:** `companion/restart_fast.py` (new), `companion/plugins/games.py`, `tests/restart_fast/` (new);
  `RestartFast.kt` (new), `NativeStreamActivity.kt`, `RestartFastTest.kt` (new).
- **Rollback:** remove the host line (today's start); or keep `20e3e339…` on the onn; or revert the files above.
