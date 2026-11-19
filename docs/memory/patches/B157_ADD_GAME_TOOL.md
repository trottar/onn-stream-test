---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 3a9de095 (this repo) + B158
---

# B157 — the add-a-game tool

**Result:** `evidence/B157_ADD_GAME_TOOL_2026-11-18.md`.

- **Files:** `tools/party_add_game.py`, `tools/party_add_game_capture.py` (new); `tests/b157_add_game/` (new: the
  tests, the made-up picture source, the harness mode); `tests/b114_party_minigame_hang/b114_scenario.py` (the `b157`
  mode's two lines); `handoffs/ADD_GAME_TASK.md`, `handoffs/ADD_GAME_PROMPT_TEMPLATE.txt` (new);
  `evidence/b157_2026-11-18/b157.diff`.
- **Switch:** no companion change; a title the tool adds is listed only with `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1`.
- **Rollback:** `git apply -R evidence/b157_2026-11-18/b157.diff`; a title's rules files written by learn are named in
  its binding (off the repo).
