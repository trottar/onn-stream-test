---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 3a9de095 (this repo)
---

# B158 — winner-only results (PRIVYHUB_PARTY=1, PRIVYHUB_H7=1)

**Result:** `evidence/B158_WINNER_ONLY_2026-11-18.md`.

- **Files:** `companion/party_minigame.py` (`_winner_entry`; `_entries` takes a sidecar's `"result": "winner"`; the
  `ended` row and the result carry `"winner"`; the docstring's B158 line), `tests/b114_party_minigame_hang/
  b114_scenario.py` (the `winner158` mode), `tests/b158_winner_only/` (new); `evidence/b158_2026-11-18/b158.diff`.
- **Switch:** the party layer exists only with both flags; a sidecar without `result` is today's.
- **Rollback:** `git apply -R evidence/b158_2026-11-18/b158.diff` (after B157's, if applied).
