---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 0f4b551
---

# B8 — the hold / stall ownership at the return behind `PRIVYHUB_INPUT_HOLD_B8`

**Result: BUILT; 14 tests (fake core, fake client, B4's real rewinder on a fake NCI); B2 / B4 / B6 / B7 suites
unchanged and green; flag absent = BENCH-R2's files (AST, 4 / 4); NOT ADOPTED; no live run.** Record:
`evidence/B8_HOLD_STALL_OWNERSHIP_2026-10-22.md`. Nothing committed.

- **With the hold + B6 + the stall signal** (BENCH-R2 b1's stack):
  - a stall's handover carries the hold's pending rewind: requested = pre-hold frames + the client's frames before
    the silence (`input_hold_carry`);
  - the first fresh heartbeat after the return resumes (`resumed via hold_return_stall`), without the client's gate
    or a second stall;
  - a gate `ready` that lands first resumes with the same rewind (`client_ready_hold`, in the ready action, before
    its own resume);
  - gate-bit stalls over fresh output after the resume are ignored; the late `stall_end` is `stall_end_late`;
  - B4's cap default 72 (B6's 62 + 10).
- **Files:** `companion/hold_ownership.py` (new), `games/link_drop_recovery.py` +14, `stall_signal.py` +11,
  `hold_rewind.py` +7, `plugins/games.py` +12, `tests/input_hold_b8/` (new).
- **Validation performed:** the tests (3 runs), the regression set from the /tmp copy, the AST proof, `git diff
  --check`, the redact check.
- **Rollback:** unset `PRIVYHUB_INPUT_HOLD_B8` (the module is then never imported); or revert the five files and
  remove the new module and test directory.
