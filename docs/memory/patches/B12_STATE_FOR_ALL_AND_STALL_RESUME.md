---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c (+ B11 uncommitted)
---

# B12 — `PRIVYHUB_INPUT_HOLD_REWIND=1` = `state` for every core; `PRIVYHUB_STALL_RESUME=1`

**Result: BUILT; 10 tests (a loopback fake core, a fake client); every hold / stall suite green (B9's three `1` lines
moved to `rewind`, disclosed); AST proof for four files; NOT ADOPTED; no live run.** Record:
`evidence/B12_STATE_FOR_ALL_AND_STALL_RESUME_2026-10-23.md`. Nothing committed.

- `1` → `state` (no rewind keys for any core); `rewind` → B9's allow-list; `all` / `state` unchanged. Cost per save:
  snes9x 0.8 MB, bsnes 0.3 MB, PS1 16.8 MB; ack 4-11 ms after the send on PS1 (BENCH-R3 D).
- `PRIVYHUB_STALL_RESUME=1` (with the stall signal): a save at the first stall of an episode (`state`); a stall-owned
  pause resumes once, with that load, at `stall_end` or the client's gate `ready` (`client_ready_stall`), the late
  `stall_end` a no-op; v2's encoder restart held off until the pause is 5 s old, then v2 owns it once
  (`stall_handover_v2`).
- **Files:** `companion/stall_owner.py` (new), `rewind_cores.py` +15 −9, `hold_rewind.py` +5 −2, `stall_signal.py` +8,
  `games/link_drop_recovery.py` +6, `plugins/games.py` +11, `tests/stall_owner/` (new),
  `tests/rewind_cores/test_rewind_cores.py` (3 lines).
- **Validation performed:** the tests (3 runs), the regression set from the /tmp copy, the AST proof, `git diff
  --check`, the redact check.
- **Rollback:** `PRIVYHUB_INPUT_HOLD_REWIND=rewind` restores B9's `1`; unset `PRIVYHUB_STALL_RESUME`; or revert the
  files and remove the new module and test directory.
