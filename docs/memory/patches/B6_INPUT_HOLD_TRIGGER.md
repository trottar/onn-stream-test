---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7
---

# B6 — the hold's trigger, cap rule and resume behind `PRIVYHUB_INPUT_HOLD_B6=1`

**Result: the distribution READ (H = 950 ms); BUILT, 16 tests, B2 / B4 tests unchanged and green; NOT ADOPTED; no
live run.** Record: `evidence/B6_INPUT_HOLD_TRIGGER_2026-10-22.md`. Nothing committed.

- **H = 950:** the smallest H with ≤ 1 silence ≥ H per 10 min on each clean session (cells 1, 8, UX-R2). Cell 8's
  idle tail (800-1,336 ms) sets it. It catches 1 of the death's 5 gaps.
- **Under the flag** (with `PRIVYHUB_INPUT_HOLD` valid):
  - `1` / `on` → 950;
  - B4's rewind cap default is max(30, round(H / 16.7) + 5): 62, with the buffer 51 MiB snes9x / 1,025 MiB PSX;
  - the cap counts released holds only and disarms for 10 s;
  - (R1) a hold v2's `controller_silence` took over resumes at the first fresh heartbeat after the return
    (`hold_return`, B4's rewind first);
  - (R2) a client-trigger handover is left to the client's black-overlay gate;
  - (R3) a client ready within 20 s of a hold resume ends that recovery (no `session_started`, no ladder reset).
- **Files:** `companion/hold_tuning.py` (new), `input_hold.py` +6, `hold_rewind.py` +4, `games/link_drop_recovery.py`
  +18, `plugins/games.py` +8; `tests/input_hold_b6/test_input_hold_b6.py` (new).
- **Validation performed:**
  - B6 16, B2 19, B4 22 and the regression set;
  - the whole-module AST proof (4 identical);
  - `git diff --check` clean;
  - the redact check.
- **Next (A, BENCH-R2):** `@both` with hold + B6 + rewind (one hold, one release, net ≈ 0, then the client's overlay);
  `none` with everything on (false holds ≤ 1 / 10 min); the distribution re-run with B5's lock cell.
