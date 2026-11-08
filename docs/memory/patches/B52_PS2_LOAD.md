---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 65186c66
---

# B52 — the PS2 load (MTVU off; the load after the game's ELF; "confirmed" = the picture moving)

**Result: SETTLED + BUILT inside `PRIVYHUB_PS2=1`; tests green ×3; 6 mutations caught; absent = today PROVEN.**
Record: `evidence/B52_PS2_LOAD_2026-11-08.md`.

- **Files:** `companion/ps2_session.py`, `companion/games/emulator_manager.py`, `tests/ps2_session/test_b52.py` (new),
  `test_b51.py`, `test_ps2_session.py`.
- **Apply:** `git apply evidence/b52_2026-11-08/b52.diff` (applied with B53 as `queue_s_combined.diff`).
- **Live:** at the next companion restart with the flag.
- **Rollback:** reverse it (the ini then keeps PCSX2's `vuThread`).
