# B51 — `PRIVYHUB_PS2` absent = today, hunk by hunk

| hunk (`b51.diff`) | without the line |
| --- | --- |
| `EmulatorManager.save_state` / `load_state` branch | `self._launch_kind == "pcsx2"` is set only by `_launch_pcsx2`, reachable only with `_ps2` (the flag); `None` otherwise (class default and `__init__`), so the RetroArch bodies run exactly as before. `Ps1Untouched.test_a_retroarch_session_never_takes_the_pine_branch` checks this, and the whole host regression matches the baseline copy |
| `EmulatorManager._pcsx2_save_state` / `_pcsx2_load_state` (new) | called only from that branch |
| `ps2_session.py` (the PINE constants, `pine_call`, `state_files`, the `Session` additions, `pcsx2_log_path`) | imported only under the flag (B49's guards, unchanged) |
| `plugins/games.py`, the `ps2_session` row's `savestates: "pine"` | inside B49's `_ps2_session is not None and _ps2_session.active(...)` guard |
| `tests/ps2_session/test_ps2_session.py` | B49 / B50 expectations moved to B51's meaning (disclosed): the row's key, the two button refusals, the launch test's save message |

Two things kept as B49 left them: the recovery paths' refusals (`save_recovery_state`'s skip, `load_recovery_state*`,
`copy_recovery_state_to_slot`), and the `ps2_mode` skips of the hold rewind / slot-9 save / stall-resume load.
