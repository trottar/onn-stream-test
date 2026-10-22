---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 0f4b551 (+ B8 uncommitted)
---

# B9 — `PRIVYHUB_STALL_SIGNAL=1` = 400 ms; `PRIVYHUB_INPUT_HOLD_REWIND` = `1` (allow-list) / `all` / `state`

**Result: BUILT; 13 tests (a loopback fake core); B2 / B4 / B6 / B7 / B8 green (two disclosed test lines); NOT
ADOPTED; no live run.** Record: `evidence/B9_STALL_THRESHOLD_AND_REWIND_CORES_2026-10-22.md`. Nothing committed.

- `stall_signal.DEFAULT_MS` 150 → 400 (BENCH-R2 d1 2.6 / 10 min at 150, d2 0 at 400); 150 by number. Client unchanged.
- `PRIVYHUB_INPUT_HOLD_REWIND=1`: rewind keys and REWIND only for snes9x / bsnes; another core gets none and a
  `rewind_skipped` row. `all` = B4 for every core. `state`: `SAVE_STATE_SLOT 9` at a 400-ms silence
  (`PRIVYHUB_INPUT_HOLD_STATE_AT_MS`), loaded at the release into a running core (PAUSE_TOGGLE + LOAD_STATE_SLOT 9,
  D-BASE-R3C's paused-load caveat), only for the matching silence and a fresh file.
- **Files:** `companion/rewind_cores.py` (new), `stall_signal.py` +2 −2, `hold_rewind.py` +18, `input_hold.py` +5,
  `tests/rewind_cores/` (new), `tests/stall_signal/test_stall_signal.py` (1 line), `tests/input_hold_rewind/
  test_hold_rewind.py` (3 lines: the per-core test under `all`).
- **Validation performed:** the tests (3 runs), the regression set from the /tmp copy, the AST proof, `git diff
  --check`, the redact check.
- **Rollback:** `PRIVYHUB_STALL_SIGNAL=150` restores B7's threshold; `PRIVYHUB_INPUT_HOLD_REWIND=all` restores B4's
  rewind; or revert the five files and remove the new module and test directory.
