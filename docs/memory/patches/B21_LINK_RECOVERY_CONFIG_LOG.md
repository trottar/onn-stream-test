---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 13ccff5
---

# B21 — the `link_recovery_config` row reports the import-time `apply()`

**Result: BUILT; `tests/link_recovery` 16 green; absent proven (AST); no live run.** Record:
`evidence/B21_LINK_RECOVERY_CONFIG_LOG_2026-10-24.md`. Diff: `evidence/b21_2026-10-24/b21.diff`. Nothing committed.

- **The fault (CL-B12 §1):** the row logged a third `apply(os.environ)` at the plugin's wire, after
  `emulator_manager`'s import-time one had set the six, so it read `implied` [] / `explicit` the six.
- **Built:**
  - `companion/link_recovery.py`: `_FIRST` keeps the process's first `apply` result. New `config_row(environ)`
    returns it with `at` `import` and `reapply` (what a re-application would add now; `[]` = nothing new). It writes
    nothing.
  - `companion/plugins/games.py`: the row calls `config_row`; the second `apply` is removed.
- **The row under G-A4's drop-in (after the next companion restart):** `umbrella` true, `implied` the six, `explicit`
  {}, `at` `import`, `reapply` [].
- **Absent:** `link_recovery` not imported, no row (unchanged).
- **Files:** `companion/link_recovery.py`, `companion/plugins/games.py`, `tests/link_recovery/test_config_row.py`
  (new).
- **Rollback:** revert the two companion files (the behaviour does not change; only the row's fields).
