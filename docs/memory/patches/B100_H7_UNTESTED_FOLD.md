---
memory_schema: 1
as_of: 2026-11-12
baseline_commit: 33d8d2cf
---

# B100 — H7's search: a fold that could not be tested does not count as passed (tools only)

**Result:** `evidence/B100_H7_UNTESTED_FOLD_2026-11-12.md`.

- **Files:** `tools/h7_rule_search.py`, `tests/h7_rule_search/test_b100_untested_fold.py` (new);
  `evidence/b100_2026-11-12/b100.diff` (applies on `33d8d2cf`).
- **Changed meaning:** a template with a fold "not testable" (over a cap) reads at most "weak" (`folds_not_tested`,
  `not_tested` on the fold row).
- **Rollback:** `git apply -R b100.diff`.
