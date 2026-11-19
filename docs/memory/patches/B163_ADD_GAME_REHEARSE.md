---
memory_schema: 1
as_of: 2026-11-19
baseline_commit: 58497ab8 (this repo)
---

# B163 — rehearse: learn's whole real path on a title already added

**Result:** `evidence/B163_ADD_GAME_REHEARSE_2026-11-19.md`.

- **Files:** `tools/party_add_game.py` (`rehearse`: `kept_source`, `rehearse_roles`, `_read_run`, `_capture_run`,
  `_rules_shas`, `_rehearse_in`, `cmd_rehearse`; the stage list and usage); `tests/b163_rehearse/` (new);
  `handoffs/ADD_GAME_TASK.md` §0. In `evidence/b162_2026-11-19/b162_b163.diff` with B162 (one file holds both).
- **Switch:** none needed — a new command; no companion change. It writes only into a scratch tree under the title's
  add_game folder (removed at its end) and its own verdict and page; the real rules folder is only read (its every
  file's sha256 before = after is a cell).
- **Rollback:** with B162's diff (above).
