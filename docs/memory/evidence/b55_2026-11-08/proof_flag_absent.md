# B55 — `PRIVYHUB_PS2` absent = today byte for byte, hunk by hunk

`b55.diff` against the baseline copy (`0eb115d9`): 8 files, 14 hunks. Without the flag `emulator_manager._ps2` is
None, `_launch_pcsx2` is never reached (B49's refusal), so `_launch_kind` is never `"pcsx2"` and no session is PS2.

| file | hunk | why absent is today |
| --- | --- | --- |
| `ps2_session.py` | constants | the module is imported only with the flag (B49); the names (`PINE_BEHAVIOURS`, `OFF_BEHAVIOURS` now `("rewind",)`, `SCRATCH_SLOT`, `RECOVERY_SLOT`, `RELEASE_SHARE_S`, `VERIFY_RUNNING_S`) are read only by PS2 branches and by the start's `ps2_session` row, itself inside `_ps2_session is not None and _ps2_session.active(...)`. |
| `rewind_cores.py` | `save` | `if _launch_kind == "pcsx2"` (was B49's skip on the same test) → `_save_ps2`; otherwise unchanged. |
| `rewind_cores.py` | `release` | `if _launch_kind == "pcsx2"` → `_release_ps2`, placed after the unchanged B33 / match checks; otherwise unchanged. |
| `rewind_cores.py` | new methods | `_spawn`, `_ps2_folder`, `_save_ps2`, `_release_ps2`, `_verify_ps2`: called only from the two branches above. |
| `hold_rewind.py` | the PS2 test | `_launch_kind == "pcsx2" and not (b9 in state mode)`: False for every RetroArch session, as B49's `_launch_kind == "pcsx2"` was. |
| `games/link_drop_recovery.py` | `gave_up_saved` | `ps2_states` added only when the save's answer carries it (only `_pcsx2_save_recovery_state` does). |
| `games/emulator_manager.py` | `save_recovery_state` / `load_recovery_state_running` / `copy_recovery_state_to_slot` | each B49 `if self._launch_kind == "pcsx2"` keeps its test; only its body changed (a PINE method instead of the skip / refusal). |
| `games/emulator_manager.py` | new methods | `_pcsx2_save_recovery_state`, `_pcsx2_recovery_source`, `_pcsx2_load_recovery_state_running`, `_pcsx2_copy_recovery_state_to_slot`: called only from those branches. |
| `plugins/games.py` | the `ps2_session` row | inside B49's `if _ps2_session is not None and _ps2_session.active(self._emulator)`. |
| `tests/ps2_session/*` | tests | B49's three skip tests moved to B55's meaning (disclosed); `test_b55.py` new. |

The flag-absent tests (B49 / B50 / B51's "absent" and "a RetroArch session never takes the PINE branch", B55's
`RetroArchUntouched`) are green in the B55 copy.

**Result: PROVEN.**
