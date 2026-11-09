# B74 — a one-disc session (and the off switches) = today, hunk by hunk (`b74.diff`)

**Host, default on.** Everything B74 does on the host sits behind B71's knob and B71's multi-disc test
(`disc_swap.session_for`: a RetroArch PS1 `.m3u` with more than one disc line).
- **`PRIVYHUB_DISC_SWAP=0`:**
  - the plugin's `launch` passes no `start_disc`, so the emulator's `launch()` call is today's
    (`test_launch_query` pins the exact kwargs);
  - `details` gets no `discs`;
  - `session_for` is None, so nothing is written (`test_the_relaunch_and_the_knob_write_nothing`).
- **A one-disc game** (a `.cue` / `.chd`, a one-disc `.m3u`, any other system, PCSX2, Dolphin):
  - `_disc_start_prepare` returns None, so no record is read or written, and no `PS1 start disc` line is logged;
  - `_disc_session` stays None, so there are no keys and today's `launch_ports` row;
  - `details` has no `discs` (`test_one_disc_game_untouched`, `test_details_discs_only_on_a_set`,
    `test_launch_ports_row`).
- **B54's relaunch** (`relaunch_ports`, `start_disc` None): no record is written, so RetroArch's own restore is kept
  (`test_the_relaunch_and_the_knob_write_nothing`).

| file | hunk | one disc / knob off |
| --- | --- | --- |
| `companion/disc_swap.py` | constants; `parse_start_disc`, `m3u_entries`, `savefile_dir_from_config`, `ldci_set`, `first_index` | reached only from a multi-disc set's launch |
| `games/emulator_manager.py` | `launch(…, start_disc=None)` | default None |
| | `disc_start = self._disc_start_prepare(…)` before the log | None |
| | `if disc_start is not None:` the `PS1 start disc` line | not written |
| | after the Popen: `launched_disc` / `_launch_line_open` / `start_disc` under `if self._disc_session is not None` | not reached |
| | `_disc_refresh`: `launched_disc` from the first line while the launch line is open | returns at once (no session) |
| | new `_disc_start_prepare` | None |
| | `disc_swap`: `_launch_line_open = False`; `launched_disc` on both events | reachable only on a multi-disc session (else "This game has one disc", as B71) |
| `plugins/games.py` | `launch`: `start_disc` under `_disc_swap.enabled()` | knob 0 → no key: today's call |
| | `launch_ports`: `start_disc` / `launched_disc` only inside B71's `"discs" in payload` and with a B74 session | today's row |
| | `details`: `discs` only under the knob and only when > 1; new `_set_discs` | not set |
| `streaming/DiscSafe.kt` | new | — |
| `MainActivity.kt` | the import; `discSafeOn` | a lazy field |
| | `gameDiscButton` → `showDiscWarningThenChooser()` | the button is never visible on a one-disc game (B71); `disc_safe=0` → `needsWarning` false → B71's `showDiscChooser()` at once |
| | after a change: `afterChangeLine` only with `discSafeOn` | B71's `statusLine` |
| | `showGameLaunchModeDialog(…, json.optInt("discs", 0))` → `showGameExtrasMenu(…, discs)` | `discs` 0 → today's two items (Cheats, Mods) |
| | new `showStartDiscChooser` | reached only from the third item |
| | `launchGameOnCompanion(…, startDisc = null)` → `+ DiscSafe.launchSuffix(null)` = `""` | **today's URL byte for byte** |
| tests | new | — |

**The swap sequence is not changed** (`Swapper` is untouched; `test_the_settled_sequence_unchanged` pins the commands,
no `PAUSE_TOGGLE`, and the 0.4-s spacing). B71's own 21 tests stay green in the same copy.

**Disclosed:** with the knob on, **every library launch of a set** (the old APK included, which sends no `disc`) starts on
disc 1. That is the queue's point (2), live as soon as the companion is restarted, and independent of the APK.
