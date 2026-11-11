---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: 2e30c1cf
---

# B96 — H7's search: "decided" by held-out states and families (a tool change; the companion unchanged)

**Result:** `evidence/B96_H7_HELD_OUT_AND_FAMILIES_2026-11-11.md`.

- **Files:** `tools/h7_rule_search.py`, `tests/h7_rule_search/fixtures.py`, `tests/h7_rule_search/test_h7_rule_search.py`;
  `evidence/b96_2026-11-11/b96.diff` (applies on `2e30c1cf`).
- **Changed meaning:** `"decided"` is now `"strong"` evidence only (two "end" states per winner seen, two winners or
  more, a family passing every held-out fold); B94's "exactly one candidate" is gone. Template (c) tightened (player
  number or flag values).
- **Live:** nothing runs it on its own; A's H7-P2 runs it on copies of T88's states.
- **Rollback:** `git apply -R b96.diff` (after B97's `b97.diff` is reversed first).
