# B77 — `PRIVYHUB_PROFILES_EXT=0` (and the Default profile) = today, hunk by hunk (`b77.diff`)

Reached only inside `PRIVYHUB_PS2=1` / `PRIVYHUB_GAMECUBE=1` (the launches exist only there).

| file | hunk | knob 0 / Default profile |
| --- | --- | --- |
| `companion/profile_layouts.py` | new, pure | imported only by `_ext_profile_layouts` |
| `companion/ps2_session.py` | `pad_sections(…, bindings=None)`, `settings_for(…, bindings=None)` | None → `DS2_BINDINGS` (`test_the_default_text_is_todays_bytes`; B49-B57's suites green) |
| `companion/gamecube_session.py` | `gcpad_ini(layouts=None)`, `config_files(gcpad_layouts=None)`, `write_config(…, gcpad_layouts=None)` | None → `PAD_LAYOUT` (same test; B69 / B72's suites green) |
| `games/emulator_manager.py` | new `_ext_profile_layouts` | knob 0 → `(None, "")`: no profile read, no log line |
| | `_launch_pcsx2`: `settings_for(…, profile_tables)`; the log line `if profile_line` | None / "" → today's ini and log (`test_knob_zero_ignores_the_swap`: the ini equal to the knob-0 launch's) |
| | `_launch_dolphin`: `write_config(user, profile_tables)` only when not None; the log line | today's `write_config(user)` call and log (`test_default_is_todays_bytes_and_knob_zero`) |

**The Default profile with the knob on:** the tables are None (`is_default`), so the files are today's bytes; the only
difference is one game-log line `PS2 input profile: default overrides=0` / `GC input profile: …` (disclosed: the
knob is default-on, so this line appears on every PS2 / GameCube launch; `0` removes it). A profile equal to the
editor's identity is also default (`test_default_profile_is_todays_bytes`). An unusable profile → today's layout and
a log line (`test_an_unusable_profile_is_todays_layout_and_logged`); the launch is never refused for it.
