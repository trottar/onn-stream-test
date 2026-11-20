---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: 6d4a6c44 (this repo)
---

# B172 — the solo mark ends at close

**Result:** in `evidence/B171_ADD_GAME_MORE_SAVES_2026-11-20.md` (§B172).

- **Files:** `tools/party_add_game.py` (`end_solo_mark`: close — and register, the first stage of a use — end the
  title's `solo_mark.json`, `files_before.json`, `saves_before.json`, the tool's own files in its add_game folder);
  `tests/b171_more_saves/test_b172.py` (new). In `evidence/b171_2026-11-20/b171_b172.diff` with B171.
- **Switch:** none — the tool.
- **Rollback:** with B171's diff.
