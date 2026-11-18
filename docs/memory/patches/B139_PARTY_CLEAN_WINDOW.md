---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: c1a66bc9 (this repo)
---

# B139 — a party mini game's title launched with RetroArch's on-screen text off (PRIVYHUB_PARTY=1)

**Result:** `evidence/B139_PARTY_CLEAN_WINDOW_2026-11-17.md`.

- **Files:** `companion/games/emulator_manager.py` (`_party_session_settings`, class default `None`; read by
  `_prepare_retroarch_session_config`, which then replaces any assignment of its keys and appends them),
  `companion/party_minigame.py` (`PARTY_SESSION_SETTINGS` = `video_font_enable = "false"`,
  `menu_show_load_content_animation = "false"`, set around the layer's own launch only; `PARTY_LABEL_MASK = False`),
  `tests/b139_party_clean_window/` (new), `tests/b114_party_minigame_hang/b114_scenario.py` (each launch's config read by
  the fake; the users' launch's config kept in `today` / `cheat` / `nopress`), `tests/b137_party_no_press/test_b137.py`
  (its label test for B139's rule); `evidence/b139_2026-11-17/b139.diff` (applies on `c1a66bc9`).
- **Switch:** `PRIVYHUB_PARTY=1` (with `PRIVYHUB_H7=1`): only a launch made by `party-minigame-start` carries the keys;
  either flag absent → today; the users' launches byte for byte today with the flags set.
- **Rollback:** `git apply -R` b141.diff, b140.diff, then b139.diff (B137's order and mask back).
