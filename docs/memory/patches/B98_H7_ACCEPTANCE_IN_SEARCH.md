---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: 6cb4663b
---

# B98 — H7's search: the acceptance rule in the search itself (tools only; the companion unchanged)

**Result:** `evidence/B98_H7_ACCEPTANCE_IN_SEARCH_2026-11-11.md`.

- **Files:** `tools/h7_rule_search.py`, `tests/h7_rule_search/test_h7_rule_search.py`,
  `tests/h7_rule_search/test_b98_acceptance.py` (new); `evidence/b98_2026-11-11/b98.diff` (applies on `6cb4663b`).
- **Changed meaning:** `decided` needs an accepted answer (template a or b, a hinted family, or a hinted set h); (b2)
  and (c) answers are listed under `not_accepted`. New keys: `accepted`, `not_accepted`, `ranking_pick`,
  `ranking_pick_count`. `--accept-loose` = B97's output.
- **Live:** nothing runs it on its own.
- **Rollback:** `git apply -R b98.diff`.
