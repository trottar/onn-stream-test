# B84 — `debug.privyhub.cheat_picker=0` = today's dialog, hunk by hunk (`b84.diff`)

| file | hunk | the property `0` / `off` |
| --- | --- | --- |
| `streaming/CheatPicker.kt` | new | `CheatPicker.fromSystem()` → `parse("0")` / `parse("off")` = false (`theProperty`) |
| `MainActivity.kt` | `showGameCheatEntryDialog`: `if (CheatPicker.fromSystem()) { showCheatPickerScreen(…); return }`, placed after today's two early checks and before today's dialog | false → the function continues into today's code, unchanged line for line |
| | `showCheatPickerScreen` (new) | never called |
| `B84CheatPickerTest.kt` | new | — |

Nothing else in the client changes; the launch call, the profile label and the hub's API are today's. The APK tree's
only source differences from the baseline that rebuilds `de6682db…` byte for byte are B84's and B86's files
(`b86_2026-11-10/apk_source_diff.txt`).
