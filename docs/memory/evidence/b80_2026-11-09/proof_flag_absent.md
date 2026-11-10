# B80 — `PRIVYHUB_PS2_PATCHES=0` / `debug.privyhub.ps2_patches=0` (and a title without a record) = today (`b80.diff`)

Host reached only inside `PRIVYHUB_PS2=1`.

| file | hunk | knob 0 / no record |
| --- | --- | --- |
| `companion/ps2_patches.py` | new | imported only on the paths below |
| `games/emulator_manager.py` | `_ps2_patch_offer`, `ps2_patches`, `set_ps2_patches` | knob 0 → None / refused |
| | `_ps2_game_settings` (called in `_launch_pcsx2` after the ini) | knob 0 → `[]`; the title's ids unknown or no toggle record → `[]`: nothing written, no line (`test_no_record_or_knob_zero_or_unknown_ids_is_today`) |
| | the log lines loop | empty |
| `plugins/games.py` | `details`: `ps2_patches` only for a PS2 title with an offer | absent (`test_details_key_only_with_a_patch`) |
| | action `ps2-patches` | only reached when the onn's new entry posts it |
| `companion/gc_cheats.py` | `read_bundled(…, run=None)` → `run or subprocess.run` | **B79's code, fixed here** (disclosed): the default was bound at definition; same behaviour, now patchable |
| client `Ps2Patches.kt` | new | — |
| client `MainActivity.kt` | `jsonStrings`; `showGameLaunchModeDialog(…, ps2PatchesAvailable = [], …)`; `showGameExtrasMenu` built by `Ps2Patches.extrasItems` | no `ps2_patches` in the details (every title but a PS2 one with a bundled patch) → `["Cheats", "Mods"]` (+ B74's entry for a set): today's list and order (`extrasListIsTodaysWithoutPatches`); the property 0 → no entry |
| | new `showPs2PatchesDialog` | only from the new entry |

The launch's query is unchanged: the hub reads the remembered toggles.
