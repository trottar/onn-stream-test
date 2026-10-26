---
memory_schema: 1
as_of: 2026-10-26
baseline_commit: 06c565e
---

# B24 — `PRIVYHUB_RESTART_FAST_UNLOCK=1`: the fast restart's ready at the new encoder's check

**Result: SETTLED + BUILT; `tests/restart_fast_unlock` 10 green, B22's 13 unedited and green, every `tests/` suite
green; absent = the adopted G-A5 worker (proven); no client change, no APK; no live run.** Record:
`evidence/B24_RESTART_FAST_UNLOCK_2026-10-26.md`. Diff: `evidence/b24_2026-10-26/b24.diff`. Nothing committed.

- **Settled:**
  - return 1's 2,088-ms old-audio stop is the capture's 2-s SIGTERM wait expiring;
  - the ready needs only the new encoder's check and `prepare`;
  - the old encoder's flushed frames were forwarded because the relay was stopped after its exit.
- **Built** (`companion/restart_fast_unlock.py`, `RestartFastUnlock(RestartFast)`; inside `PRIVYHUB_RESTART_FAST=1`):
  - the old audio's stop first, beside a capture watchdog (SIGKILL at 300 ms);
  - **the relay stopped before the old encoder's SIGTERM**; SIGKILL after a 100-ms grace; the capture target selected
    during it;
  - the new encoder, `prepare`, today's 0.75-s check;
  - **the lock released: the ready answers.** The old audio's stop is joined and logged after it
    (`restart_fast_audio_stop`, `restart_fast_audio_stop_ms`), then the new audio (`restart_fast_audio`).
- **Files:** `companion/restart_fast_unlock.py` (new), `companion/plugins/games.py` (+10 lines),
  `tests/restart_fast_unlock/` (new).
- **Rollback:** remove the line (the adopted G-A5 worker), or revert the files above.
