# B50 — `PRIVYHUB_PS2` absent = today, hunk by hunk

| hunk (`b50.diff`) | without the line |
| --- | --- |
| `companion/ps2_session.py` (the face names, vsync / mailbox, the card slots, `wait_audio`, PINE-late, `ensure_memcards`) | imported only under `PRIVYHUB_PS2=1` (B49's guards in `plugins/games.py` and `emulator_manager.py`, unchanged); B49's `Hooks.test_absent_is_today` / `Launch.test_absent_is_todays_refusal_and_nothing_written` still pass |
| `companion/ps2_memcard.py` (new) | imported only inside `ps2_session.ensure_memcards`, called only from `_launch_pcsx2` |
| `emulator_manager.py` (`ensure_memcards`, the `PS2 memcards:` line, `self._ps2.wait_audio`) | all inside `_launch_pcsx2`, reachable only with `_ps2` set (the flag) |
| `tools/trip_log_keeper.py` `GAME_LOG` | also accepts `<date>-<time>-ps2.log`, a file only a PS2 launch writes; for every other name the match is as before (`trip_log_keeper`, `diag_keeper` suites as the baseline) |
| `tools/diag_read.py` | a `-ps2.log` launch, a `ps2_session` row and `system: "ps2"` exist only for PS2 sessions; a log with none of them reads as before (`diag_read` suite as the baseline; `Keeper.test_a_ps2_session_is_labelled_ps2_and_a_ps1_one_as_before`: the PS1 row has no `system` key) |
| `tools/diag_check.py` | the seventh line only when the newest `sessions.jsonl` row is PS2; else today's six (`diag_check` suite as the baseline; `test_diag_check_prints_a_seventh_line_only_for_a_ps2_newest_row`) |
| `tools/ps2_p2_window.py`, `tests/ps2_session/test_b50.py` (new) | run by nothing in the service |
| `tests/ps2_session/test_ps2_session.py` | B49's binding and vsync expectations moved to B50's meaning (disclosed); the launch test's fake session got a fake clock and a fake sink-input (A's wait no longer calls the real `pactl`: 91 s → 1.4 s) |
