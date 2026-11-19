---
memory_schema: 1
as_of: 2026-11-19
baseline_commit: 58497ab8 (this repo)
---

# B162 — the add-a-game tool's solo, safe for many titles

**Result:** `evidence/B162_ADD_GAME_SOLO_SAFE_2026-11-19.md`.

- **Files:** `companion/party_minigame.py` (`set_only`, the list filter, `NOT_LISTED`), `companion/plugins/games.py`
  (the `party-minigame-only` route, loopback); `tools/party_add_game.py` (solo's setting, its title cell, S's listed
  switches, the in-game saves recorded at close, the pads' words; B163's `rehearse` is in the same file);
  `tests/b162_solo_safe/` (new), `tests/b157_add_game/made_up_hub.py` (new), `tests/b157_add_game/test_b157.py` (its
  solo tests given the made-up hub and a launch log), `tests/b114_party_minigame_hang/b114_scenario.py` (the `b162`
  mode's two lines; the `today` mode calls the new route); `handoffs/ADD_GAME_TASK.md`;
  `evidence/b162_2026-11-19/b162_b163.diff` (B162 and B163 together; applies on `58497ab8`).
- **Switch:** the companion's part is reached only with `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1`; the setting is never
  set but by the tool's `solo` over loopback, kept in memory only (any restart clears it). Either flag absent: HEAD's
  bytes on every route; both set and the setting never set: the users' routes HEAD's bytes.
- **Rollback:** `git apply -R docs/memory/evidence/b162_2026-11-19/b162_b163.diff` (also takes B163's `rehearse` out).
