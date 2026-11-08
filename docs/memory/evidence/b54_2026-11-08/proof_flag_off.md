# B54 — `0` / `off` (client) and no request (host) = the CONFIRMED build's / today's behaviour, hunk by hunk

`b54.diff` against the baseline copy (`0eb115d9`; the code as `68386b32`): 17 files, 53 hunks. Each hunk of a
pre-existing production file is classified below; new files are reached only through the hunks shown.

## Client (`debug.privyhub.player_prompt` `0` / `off` → `playerPrompt == null`, as in `cfe0211c…`)

| file | hunks | why `0` is the CONFIRMED build's |
| --- | --- | --- |
| `PlayerPrompt.kt` | 10 | the class is only built when the flag is on (`NativeStreamActivity.playerPrompt` lazy: `PlayerPromptFlag.fromSystem()` false → null). `PlayerPromptFlag.parse` is unchanged (`!= "0" && != "off"`). |
| `PlayerChoiceStoreAndroid.kt` | 2 | constructed only inside the same lazy (and `MainActivity`'s suffix, behind the flag). |
| `NativeStreamActivity.kt` | 10 | (1) the self-restart's start query: inside `if (playerPrompt != null …)`; (2) the report: inside `playerPrompt?.let`; (3) `promptJoinedQuery()` returns `""` when `playerPrompt` is null (the heartbeat's former `promptChosenQuery()` did the same); (4) `promptTick` + `startRelaunch`: posted only when `playerPrompt != null` (unchanged guard at `onCreate`), and `startRelaunch` returns at `playerPrompt ?: return`; (5) the key hook: inside `playerPrompt?.let`; (6) the removed hat hook was inside `playerPrompt?.let` (a no-op at `0`); (7)-(8) the overlay's and the gate's `relaunchActive` branches: `relaunchActive` is only set by `startRelaunch` → false at `0`; (9) the constant `RELAUNCH_READ_TIMEOUT_MS`: used only by `startRelaunch`; (10) the heartbeat comment. |
| `MainActivity.kt` | 3 | `playersChosenLaunchSuffix`: `PlayerPromptFlag.fromSystem()` false → `""` (unchanged first branch); two comments. |
| `NativeControllerSender.kt` | 1 | a comment. |

So at `0`: no prompt object, no view, no `players_joined` / `players_chosen` / `pad_claims` key, no report key, no
relaunch — the CONFIRMED build's `0`. (B46's absent = ON stands: absent / empty / junk = hold-to-join.)

## Host (no `players_joined`, no `native-stream-relaunch-ports` → today)

| file | hunks | why no key is today |
| --- | --- | --- |
| `plugins/games.py` | 5 | (1) the launch: `if "players_joined" in query` is new; B46's `if "players_chosen" in query` became its `elif` — identical without the new key; `joined_source` stays False, so (2) the `source` rewrite after the launch never runs; (3)-(4) the start / heartbeat: `players_joined` passed to `SlotsLog` only `if "players_joined" in query`; (5) the new action `native-stream-relaunch-ports` is reached only by that request. |
| `pad_slots.py` | 6 | docstring; `parse_joined` / `_joined_extra` new (unused without the key); `last_joined` init None; `start` / `heartbeat` take `players_joined=None`: `with_chosen(slots, None)` returns `slots` unchanged, `_joined_extra(None)` is `{}`, and the change test's added term `None != None` is False — B46's rows byte for byte (tested: `test_without_the_key_the_rows_are_b46s`). |
| `players_session.py` | 4 | docstring; `parse_joined` / `ports_for_joined` new; `plan(…, source="launch")` — the default is B46's literal; `ports_set` also accepts `join` / `relaunch`, which only B54's paths write. |
| `games/native_stream_heartbeat.py` | 1 | `join` / `players_joined` copied only when present in the values (only B54's path puts them there). |
| `games/emulator_manager.py` | 3 | `RELAUNCH_STATE_SUFFIX` (a constant); `save_relaunch_state` (new; called only by `relaunch_ports.run`); `load_recovery_state_running(source=None)`: `source if source is not None else self._recovery_state_path_for_active()` — with no argument, today's call exactly (tested: `test_no_source_is_todays_recovery_path`). |

Tests: the B46 host tests run unchanged and green in the B54 copy (13), plus their temp-dir clean-up import (test
hygiene; disclosed).

**Result: PROVEN** — every hunk is either behind `playerPrompt != null` / the B54 query keys, a new file reached only
from them, a default argument equal to today's value, or a comment / docstring.
