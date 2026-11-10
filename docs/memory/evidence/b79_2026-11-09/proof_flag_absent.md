# B79 — `PRIVYHUB_GC_CHEATS=0` (and a plain launch) = today, hunk by hunk (`b79.diff`)

Reached only inside `PRIVYHUB_GAMECUBE=1` (`_gc` loaded).

| file | hunk | knob 0 / plain launch |
| --- | --- | --- |
| `companion/gc_cheats.py` | new | imported only on the paths below |
| `companion/gamecube_session.py` | `dolphin_ini(cheats=False)`, `config_files(…, cheats=False)`, `write_config(…, cheats=False)` | False → `EnableCheats = False`, today's bytes (`test_dolphin_ini_default_is_todays_bytes`) |
| `games/emulator_manager.py` | `launch()`'s GameCube branch | knob 0 or no cheat argument → `self._launch_dolphin(game, players_chosen)`, today's call |
| | `_launch_dolphin(…, cheat_source_index=None, …)`; `gc_cheat_pick` | None → no user file, today's `write_config` call (B77's), no `GC cheats` line, no `gc_cheats` key (`test_a_plain_launch_is_today`) |
| | `cheat_catalog` / `cheat_profiles`: `_ext_cheat_catalog` first | non-GameCube titles and the knob 0 → None → today's code (`test_knob_zero_is_today`) |
| | new `_gc_cheat_catalog`, `_gc_cheat_pick` | reached only from the above |

The catalog sent to the onn never carries the disc id (`_`-keys stripped; `test_the_onns_shape`).
