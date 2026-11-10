# B78 — absent `PRIVYHUB_N64` / `PRIVYHUB_N64_CHEATS=0` = today, hunk by hunk (`b78.diff`)

| file | hunk | absent / 0 |
| --- | --- | --- |
| `companion/games/cheat_importer.py` | `EXTRA_SYSTEM_SPECS` import; `N64_CHEATS_ENV`; `cheat_system_specs` | `SYSTEM_SPECS`'s four (`test_n64_only_with_the_flag`) |
| | `prepare_system` reads `cheat_system_specs()` | the same refusal "Unsupported game system" for n64 (`test_knob_zero_is_todays_refusal`) |
| `tools/update_game_cheats.py` | the import; the choices | the four |
| `games/emulator_manager.py` | `N64_CHEAT_CORE_LIBRARY_NAME`, `_cheat_core_library_name` | the class table's value; n64 → None without `_n64` (absent `PRIVYHUB_N64`) or with the knob 0 (`test_library_name`) |
| | `_prepare_cheat_runtime` uses it | the same "No validated RetroArch cheat library name" refusal (`test_without_the_flag_the_launch_prep_refuses`) |

**Disclosed (today's behaviour, kept with the knob 0):** once N64 titles have metadata records (after B76's fetch),
today's cheat tool run with `PRIVYHUB_N64=1` in its environment stops on the first N64 title with "Unsupported game
system: n64". With B78 on it does not. Without `PRIVYHUB_N64` in the tool's environment no N64 title is scanned.
