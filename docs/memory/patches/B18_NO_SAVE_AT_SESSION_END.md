---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d
---

# B18 — no save and no hold at the session's end, inside `PRIVYHUB_INPUT_HOLD_REWIND=1` (+ the client's bye)

**Result: SETTLED + BUILT; host 8 (`tests/session_end`), client 2 (`StallByeTest`), JVM 132 / 132; B8 / B9 / B12 /
B16 green; absent proven; NOT ADOPTED; no live run.** Record: `evidence/B18_NO_SAVE_AT_SESSION_END_2026-10-24.md`.
Nothing committed.

- **Settled:** at each teardown the controller went silent at `surfaceDestroyed`. B9's save fired at 400 ms; the
  client's report (+154-181 ms) and stop (+205-207 ms) came after it. Only the client knows the end in time.
- **Built:**
  - **client:** a finishing activity sends `PHS1` kind 3 (`bye`) three times before its sender stops (≤ 60-ms wait);
  - **host:** `SessionEnd` (B9's module) knows the end from the `bye`, a non-PLAYING state, or the stream's sender
    flat for 250 ms. Then no save (`state_save_skipped`) and no hold (`input_hold_skipped_ending`).
- **Files:** `rewind_cores.py`, `stall_signal.py`, `games/link_drop_recovery.py`, `plugins/games.py`, `StallSignal.kt`,
  `NativeStreamActivity.kt`, `StallByeTest.kt` (new), `tests/session_end/` (new).
- **Rollback:** unset `PRIVYHUB_INPUT_HOLD_REWIND`; or revert the files above.
