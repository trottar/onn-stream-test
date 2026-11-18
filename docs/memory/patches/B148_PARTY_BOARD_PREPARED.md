---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 1052fe82 (this repo) + B147's diff
---

# B148 — the board prepared before its launch (PRIVYHUB_PARTY=1)

**Result:** `evidence/B148_PARTY_BOARD_PREPARED_2026-11-18.md`.

- **Files:** companion/party_session.py (IMPORT_LIMIT_S, import_needed, _board_running, prepare), companion/games/emulator_manager.py (_launch_party calls prepare), tests/b148_party_board_prepared/ (new); `evidence/b148_2026-11-18/b148.diff`.
- **Switch:** behind `PRIVYHUB_PARTY=1`; absent = today (the users' own sessions byte for byte with the flag set).
- **Rollback:** `git apply -R evidence/b148_2026-11-18/b148.diff` (later items' diffs first).
