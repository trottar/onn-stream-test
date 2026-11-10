# B81 — `PRIVYHUB_CHEAT_DROPINS=0` (and no file in the folders) = today, hunk by hunk (`b81.diff`)

| file | hunk | knob 0 / no file |
| --- | --- | --- |
| `companion/cheat_dropins.py` | new | imported only on the paths below |
| `games/emulator_manager.py` | `_cheat_catalog_unlocked` → the old body renamed `_cheat_catalog_base_unlocked` (unchanged) + the wrapper | knob 0 or no user `.cht` → the base, today's dict (`test_no_user_file_is_todays_dict`); a missing manifest still raises as today with the knob 0 (`test_no_manifest_still_lists_the_users`) |
| | `_dropin_folders_once` in `cheat_catalog` / `cheat_profiles` | knob 0 → nothing made (`test_created_empty_once_and_not_with_the_knob_off`) |
| | `_ext_cheat_catalog`: the PS2 branch; `_ps2_dropins_on`, `_ps2_cheat_catalog`, `_ps2_cheat_pick` | knob 0 (or B80's knob 0) → None → today's code |
| | `launch()`'s PS2 branch | knob 0 or no cheat argument → `self._launch_pcsx2(game, players_chosen)`, today's call |
| | `_launch_pcsx2(…, cheat_source_index=None, …)` | None → nothing staged, B80's call with `cheat_extra=None` (`test_knob_zero_is_today`, `test_a_plain_launch_without_a_written_file_is_today`) |
| | `_ps2_game_settings`: rewrite a file it wrote before | only when the file carries B80's marker line, i.e. after a B80 / B81 write; knob 0 → today's B80 rule |
| `companion/ps2_patches.py` | `wrote_before` | — |
| `docs/CHEATS.md` | new | — |

**Deviation from the hashed design (disclosed):** the design put the folder creation in the games plugin's
constructor. Other suites import `plugins.games` through the package, which constructs the plugin, so the tree's own
`data/` would get the folders during test runs. The folders are made instead at the first Cheats list a companion
process serves (the onn's Extras → Cheats on any title), still empty, still only with the knob on.
