---
memory_schema: 1
as_of: 2026-11-21
baseline_commit: e215bae5 (this repo)
---

# B196-B197 — close names what changed before it ends the befores; solo's real-match switches

**Result:** `evidence/B195_CLOSE_NAMES_SOLO_SWITCHES_2026-11-21.md`.

- **Files:**
  - `tools/party_add_game.py`: `SLOT_FILE`, `HUB_SLOTS`, `LEFT_OUT`, `file_kind`, `_sha_of`, `files_changed` (new);
    `files_digest` (root and kind per file, the hub's slots 8 and 9 and their pictures left out); bench's and close's
    file cells (the list); close writes its verdict before `end_solo_mark`; `BARS["real_switches_read"]` (added),
    `BARS["switches_read_min"]` now the planned count's; solo's real-match cell and its listed note (the role);
    `solo_lines` (wait on the load screen).
  - `docs/memory/handoffs/ADD_GAME_TASK.md`: solo's and close's bullets.
  - Tests: `tests/b195_close_solo/` (new); `tests/b162_solo_safe/test_b162.py` (five places, disclosed).
  - The diff: `evidence/b195_2026-11-21/b195.diff`.
- **Switch:** the add-a-game tool's bench, solo and close only (nothing on the hub's path; the companion unchanged).
  No bar in `BARS` lowered.
- **Rollback:** `git apply -R evidence/b195_2026-11-21/b195.diff`.
