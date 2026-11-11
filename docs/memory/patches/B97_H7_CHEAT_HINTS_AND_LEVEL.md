---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: 2e30c1cf
---

# B97 — H7's search: hints from the game's own cheat list; template (b2) (tools only; the companion unchanged)

**Result:** `evidence/B97_H7_CHEAT_HINTS_AND_LEVEL_2026-11-11.md`.

- **Files:** `tools/h7_cheat_hints.py` (new), `tools/h7_rule_search.py` (`--hints FILE`, template b2, hinted sets as
  template h), `tests/h7_rule_search/` (`fixtures.cht`, `test_h7_cheat_hints.py` new, `test_h7_rule_search.py`);
  `evidence/b97_2026-11-11/b97.diff` (applies after `b96.diff`).
- **Never written anywhere:** a cheat's description (used at run time only).
- **Live:** nothing runs it on its own; A's H7-P2 runs it with T88's cached cheat list.
- **Rollback:** `git apply -R b97.diff`.
