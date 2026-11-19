---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: d7a99b62 (this repo) + B153
---

# B155 — the minigame_launch row's "keys_written" (PRIVYHUB_PARTY=1)

**Result:** `evidence/B153_PARTY_SWITCH_LENGTH_2026-11-18.md` §B155.

- **Files:** `companion/party_minigame.py` (`SESSION_CONFIG_NAME`; `_session_config_path`, `_session_config_stamp`,
  `_keys_written`; `launch()` stamps the session config before and reads it back after; the `minigame_launch` row's
  `"keys_written"`), `tests/b114_party_minigame_hang/b114_scenario.py` (the `b155` mode),
  `tests/b155_party_keys_written/` (new); `evidence/b153_2026-11-18/b155.diff` (applies on top of `b153.diff`).
- **Switch:** behind `PRIVYHUB_PARTY=1` (and `PRIVYHUB_H7=1`): the row exists only in a party mini game; the emulator
  manager and the users' launches are unchanged.
- **Rollback:** `git apply -R evidence/b153_2026-11-18/b155.diff`.
