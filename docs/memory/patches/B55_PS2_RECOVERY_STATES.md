---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 0eb115d9
---

# B55 — PS2 recovery through PINE states: the slot-9 save, the hold's return, the stall resume, the give-up save

**Result: SETTLED + BUILT; `tests/ps2_session` 93 green ×3; 8 mutations caught; absent = today PROVEN.** Record:
`evidence/B55_PS2_RECOVERY_STATES_2026-11-08.md`.

- **Files:** `companion/rewind_cores.py`, `companion/hold_rewind.py`, `companion/ps2_session.py`,
  `companion/games/emulator_manager.py`, `companion/games/link_drop_recovery.py`, `companion/plugins/games.py`,
  `tests/ps2_session/test_b55.py` (new), `tests/ps2_session/test_ps2_session.py` (three B49 tests moved, disclosed).
- **Apply:** `git apply evidence/b55_2026-11-08/b55.diff` (or queue T's combined diff, applied to the tree).
- **Live:** at the next companion restart, inside the adopted `PRIVYHUB_PS2=1`.
- **Rollback:** reverse it (B49 / B51's skips return).
