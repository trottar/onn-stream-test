---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 65186c66
---

# B53 — PCSX2's log per launch (`-logfile`), 30 days, copied by the keeper, counted by diag_read

**Result: SETTLED + BUILT; tests green ×3; 5 mutations caught; absent = today PROVEN.** Record:
`evidence/B53_PCSX2_LOG_PER_LAUNCH_2026-11-08.md`.

- **Files:** `companion/ps2_session.py`, `companion/games/emulator_manager.py`, `tools/trip_log_keeper.py`,
  `tools/diag_keeper.py`, `tools/diag_read.py`, `tests/ps2_session/test_b53.py` (new), `tests/ps2_session/_tmp_cleanup.py`
  (new), and the four test modules' import of it.
- **Apply:** `git apply evidence/b53_2026-11-08/b53.diff` on top of B52 (or `queue_s_combined.diff`; applied).
- **Live:** the launch side at the next companion restart; the keeper side at the next `privyhub-diag` restart.
- **Rollback:** reverse it.
