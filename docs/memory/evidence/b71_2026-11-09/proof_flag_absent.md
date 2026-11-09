# B71 — a one-disc session (and the off switches) = today, hunk by hunk (`b71.diff`)

**Host, default on.** A session is "multi-disc" only for a RetroArch PS1 launch of an `.m3u` with more than one disc
line. **For every other launch `_disc_session` stays `None`, and none of the new keys, rows or lines appears.** That
covers a `.cue` / `.chd`, a one-disc `.m3u`, any other system, PCSX2, Dolphin, and `PRIVYHUB_DISC_SWAP=0`. With
`PRIVYHUB_DISC_SWAP=0`, the `disc-swap` action is today's unknown-action error.

Tests: `test_not_a_multi_disc_session`, `test_status_keys_only_on_a_multi_disc_session`, `test_launch_ports_row`
(today's row without the keys), `test_heartbeat_copies_only_when_present`, `test_the_action_and_its_row` (the knob),
`test_load_makes_the_disc_unknown` (no session → the payload untouched). Mutation M4 (the one-disc guard removed) is
caught.

**Client, default on. `debug.privyhub.disc_change=0`, an old host, or a one-disc game: no CHANGE DISC button ever
becomes visible.** `readDiscState` returns null; `DiscChange.showEntry` is false (`B71DiscChangeTest`; M1 caught). The
bar's state line has no disc line.

| file | hunk | on a one-disc session / with the off switch |
| --- | --- | --- |
| `companion/disc_swap.py` | new | imported, but `session_for` returns None, so nothing else in it runs |
| `games/emulator_manager.py` | `import disc_swap as _disc_swap` | an import (default on: no flag to gate it) |
| | class defaults `_disc_session`, `_disc_tail`, `_disc_event` | attributes, None |
| | `status()`: `return {...}` → `payload = {...}`, the keys under `if active and self._disc_session is not None`, `return payload` | the same dict returned |
| | `launch()`: `_disc_session = None`, `_disc_tail = None` before any kind's branch | attributes set to None |
| | after the RetroArch Popen: `session_for(content_path, system)` | None |
| | every session-end reset: `self._disc_session = None   # B71` beside `_network_cmd_port = None` | an attribute set to None |
| | new `_disc_refresh`, `_disc_game_log`, `disc_swap`, `disc_after_load` | `disc_swap` raises "This game has one disc" (only reachable through the new action); `disc_after_load` returns its payload untouched |
| `games/native_stream_heartbeat.py` | `"discs", "disc"` in the copied fields | copied only when the plugin set them (a multi-disc session) |
| `plugins/games.py` | `import disc_swap as _disc_swap` | an import |
| | the `disc-swap` action under `_disc_swap.enabled()` | knob `0` → falls through to today's "Unknown Games plugin POST action" |
| | LOAD: `payload = self._emulator.disc_after_load(payload)` | the payload unchanged |
| | `launch_ports`: `discs` / `disc` only when the payload has `discs` | today's row |
| | heartbeat: `discs` / `disc` only when `_disc_session` is a dict | not set |
| `MainActivity.kt` | the import; `gameDiscButton`, `gameSessionDiscs`, `discChangeOn` | fields |
| | the button made (`GONE` by `createGameSessionActionButton`) and added to the bar between LOAD and END | a GONE child takes no space: the bar is today's |
| | `showGameSessionBanner(…, discs = readDiscState(json))` at the four calls | null → `gameSessionDiscs` null |
| | `clearGameSessionBanner`, `hideNowPlaying`, `showMediaNowPlayingControls`, `stopGameOnCompanion` | the button kept GONE / disabled |
| | `showGameSessionBannerUi`: visible only if `showEntry` | GONE |
| | `gameSessionStreamStatusText`: `discLine` | empty: today's text |
| | new `readDiscState`, `showDiscChooser`, `requestDiscSwap` | reached only from the visible button |
| `DiscChange.kt`, the tests | new | — |

**A one-disc PS1 session's start response, `status`, SAVE / LOAD replies, heartbeat rows and `launch_ports` row are
byte for byte today's.** On a multi-disc session they gain `discs` / `disc`, and the action and its `disc_swap` row
and game-log line exist.
