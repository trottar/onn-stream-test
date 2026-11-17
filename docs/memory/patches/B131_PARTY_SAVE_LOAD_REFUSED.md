---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: 1fc0ced0 (this repo)
---

# B131 — the onn's SAVE / LOAD during a hub mini game (PRIVYHUB_PARTY=1)

**Result:** `evidence/B131_PARTY_SAVE_LOAD_REFUSED_2026-11-17.md` (with the correction to B127's item 6: today's
manager already refuses SAVE / LOAD while the board is set aside — nothing reached the users' setups).

- **Files:** `companion/plugins/games.py` (`handle_post_request`: `save-state` / `load-state` asked of the party layer
  first), `companion/party_minigame.py` (`state_refusal`: while a mini game is `starting` / `playing` → 400 "not during
  a mini game: nothing was saved" / "… loaded", one `minigame_state_refused` row), `tests/b131_party_save_load/` (new),
  `tests/b114_party_minigame_hang/b114_scenario.py` (the `cheat` mode's `saveload` and `cheat_today`'s
  `board_saveload` options; without them the modes are as before); `evidence/b131_2026-11-17/b131.diff`.
- **Switch:** `PRIVYHUB_PARTY=1`; absent → today. Outside a starting / playing mini game → today's answers.
- **Rollback:** `git apply -R` the diff.
