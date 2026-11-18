---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 1052fe82 (this repo) + B147's and B148's diffs; the board's repo 32d5329
---

# B149 — a practice that came and went unseen (my board file)

**Result:** `evidence/B149_PARTY_UNSEEN_PRACTICE_2026-11-18.md`.

- **This repo:** `tests/b111_party_board/test_b111.py` (its fake hub's `hunseen`, the counts 97 / 68, the new line);
  `evidence/b149_2026-11-18/b149.diff`.
- **The board's repo (my two files, uncommitted there):** `minigames/hub_minigame.gd` (the practices count; the load
  screen again for an unseen practice; the `load screen again` line), `checks/hub_minigame_check.gd` (PASS 97);
  `evidence/b149_2026-11-18/b149_board.diff` (against `32d5329`).
- **Switch:** only with a stage that has the screens (a stage without them plays as before); the hub's answer unchanged.
- **Rollback:** `git apply -R evidence/b149_2026-11-18/b149.diff`; in the board's repo `git checkout --
  minigames/hub_minigame.gd checks/hub_minigame_check.gd`.
