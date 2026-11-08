---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 85c51c91
---

# B50 — the PS2 fixes from H3-P2 (inside `PRIVYHUB_PS2=1`)

**Result: SETTLED + BUILT; `tests/ps2_session` 55 (×3, 1.6 s); 6 mutations caught; absent = today PROVEN; NOT
ADOPTED; PCSX2 not started; no live run.** Record: `evidence/B50_PS2_FIXES_2026-11-08.md`. Applied to the tree,
uncommitted.

- **Built:**
  - A's audio wait kept and made testable, plus a ≤ 1-s wait for PINE's first answer before a SIGSTOP;
  - formatted memory cards (`companion/ps2_memcard.py`, only for an absent or all-`0xFF` card);
  - a tear-free present (`VsyncEnable = true`, mailbox allowed);
  - PCSX2 2.8.2's SDL3 face-button names;
  - the keeper labelling PS2 sessions (`diag_read`, `diag_check`, `trip_log_keeper`);
  - `tools/ps2_p2_window.py`.
- **Files:**
  - `companion/ps2_session.py`, `companion/ps2_memcard.py` (new), `companion/games/emulator_manager.py`;
  - `tools/diag_read.py`, `tools/diag_check.py`, `tools/trip_log_keeper.py`, `tools/ps2_p2_window.py` (new);
  - `tests/ps2_session/test_ps2_session.py`, `tests/ps2_session/test_b50.py` (new).
- **Apply:** `git apply evidence/b50_2026-11-08/b50.diff` (already applied, uncommitted).
- **Live** at the next companion restart with `PRIVYHUB_PS2=1`.
- **Rollback:** reverse `b50.diff`. A card the companion formatted stays formatted (that is PCSX2's normal state).
