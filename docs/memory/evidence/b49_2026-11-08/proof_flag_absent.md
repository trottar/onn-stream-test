# B49 — `PRIVYHUB_PS2` absent = today, hunk by hunk

| hunk (`b49.diff`) | without the line |
| --- | --- |
| `plugins/games.py` module import | `_ps2_session = None`; `ps2_session` never imported (`Hooks.test_absent_is_today`: `ps2_imported` false) |
| `GamesPlugin.__init__` | `SYSTEMS` stays the class dict (no `ps2` key) |
| `_scan`'s `ps2` branch | guarded by `_ps2_session is not None`: never reached; the scan is today's (same entries, test) |
| `native-stream-start` `ps2_mode` / `ps2_session` row | guarded by `_ps2_session is not None`: no key, no row (`Rows.test_a_retroarch_session_and_the_flag_absent_are_today`) |
| the heartbeat's `ps2_mode` | guarded the same: no key in the row (same test) |
| `native_stream_heartbeat.py` copy list | copies `ps2_mode` only if the handler set it (never, absent) |
| `emulator_manager.py` module import | `_ps2 = None` (`em_ps2` false) |
| `EmulatorManager.launch` branch | `_ps2 is not None and system == "ps2"`: never; a `ps2` title gets today's refusal (`Launch.test_absent_is_todays_refusal_and_nothing_written`: `EmulatorError`, no Popen, no `data/games/ps2/`) |
| `_controller_profile_catalog` | guarded by `_ps2 is not None`: today's `EmulatorError` for a system with no profile (test) |
| `pause` / `resume` / `stop` / the six save-state methods | `self._launch_kind == "pcsx2"`: only `_launch_pcsx2` sets it (unreachable), so `None` (class default and `__init__`) = today |
| `_refresh_process` / the stop reset | two attributes reset to `None` (no behaviour) |
| `hold_rewind.Rewinder.rewind`, `rewind_cores.Cores.save` | `getattr(emulator, "_launch_kind", None) == "pcsx2"`: never; today's paths (`rewind_needs_loss`, `input_hold_rewind`, `stall_owner` suites as the baseline) |
| `link_drop_recovery._give_up_and_save` | adds keys only when the save returns `skipped: ps2_mode` (only the PCSX2 path); a RetroArch row is today's (`SaveStatesOff.test_the_give_up_row`) |
| `players_session` (`ps2` in `MULTITAP_SYSTEMS`, the `ps2` branch) | reached only for a title whose system is `ps2`, which no list holds without the line |
| `tools/ps2_p2_frames.py`, `tests/ps2_session/` | new files, run by nothing in the service |

**`0`** reads as absent (`enabled` is `== "1"`). The flag is read at import, so it takes effect at a companion restart,
as every line does.
