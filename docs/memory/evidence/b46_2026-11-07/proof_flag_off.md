# B46 — `debug.privyhub.player_prompt=0` (or `off`) = `8ba4d996…`'s absent, hunk by hunk

`PlayerPromptFlag.parse("0")` / `parse("off")` is false (JVM `theFlagIsOnUnlessZeroOrOff`). With it false:

| hunk (`b46.diff`) | why it is today's |
| --- | --- |
| `NativeStreamActivity` `playerPrompt` lazy | `if (PlayerPromptFlag.fromSystem()) … else null` → **null**; `padSlots` then by `pad_slots` alone (B41's OR adds nothing) |
| the start query (`&players_chosen` at a self-restart) | `playerPrompt != null && …` → "" |
| the start response (`onStartResponse`) | `playerPrompt?.` → not called |
| the report (`players_chosen`, `ports_set`) | inside `playerPrompt?.let` → no key |
| `promptChosenQuery()` on the heartbeat | `n = playerPrompt?.chosen` → null → "" |
| `dispatchKeyEvent` chooser intercept | `playerPrompt?.let` → nothing; the Back block before it unchanged |
| `dispatchGenericMotionEvent` hat intercept | `playerPrompt?.let` → nothing |
| `NativeControllerSender` `repeat = event.repeatCount` | inside `if (prompt != null)`; with null the line is `playerForDevice(device)` as today |
| `PadSlots.clearAll` (new) | called only from `PlayerPrompt.onStartResponse` |
| `PlayerChoiceStoreAndroid.kt` (new) | built only in the `playerPrompt` lazy and in `playersChosenLaunchSuffix` behind the flag |
| `MainActivity.playersChosenLaunchSuffix` | `if (!PlayerPromptFlag.fromSystem()) ""` → the launch URL is today's |
| `PlayerPrompt.kt` (rewritten) | no object is built |

Host: without `players_chosen` on the launch, `handle_post` calls `emulator.launch` with today's three keyword arguments
(host test `test_the_launch_passes_the_pick_only_when_present`); `EmulatorManager.launch(players_chosen=None)` →
`players_plan` None → `_device_args` returns today's list (`test_no_pick_is_todays_list`) and
`_prepare_ps1_multitap_options(session_mode=None)` reads the metadata as today (`test_no_pick_and_no_metadata_writes_nothing`);
the stale guard acts only on a title a pick once wrote (its list file never exists until a pick) — `test_the_stale_guard`.
`ports_set` is only inside B41's `player_prompt == "1"` block; without `players_chosen` the `pad_slots` rows are B41's
(`test_without_the_pick_the_rows_are_b41s`); the heartbeat log copies `players_chosen` only when present.

**Absent / empty / junk is now ON (the user's default), not today: disclosed, as B42.** B41's ten `PlayerPromptTest`
cases were replaced by B46's fifteen (the 1-player and "pads already in the map" cases now mean the opposite).
