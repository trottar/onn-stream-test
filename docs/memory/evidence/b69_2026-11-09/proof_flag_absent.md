# B69 — absent = today, hunk by hunk (`b69.diff`)

`PRIVYHUB_GAMECUBE` absent (or any value but `1`): `emulator_manager._gc` and `plugins/games._gc_session` stay `None`
and `gamecube_session` is never imported (`tests/gamecube_session` Hooks: `"gamecube_session" in sys.modules` false,
absent and `0` identical, the list / catalog / launch refusal as today, nothing under `data/games/gamecube/` made;
mutation M2 — the import made unconditional — fails that test and the rows test). `_launch_kind` becomes `"dolphin"`
only in `_launch_dolphin`, reached only through `_gc is not None`.

| file | hunk | reached without the flag? |
| --- | --- | --- |
| `companion/gamecube_session.py` | new | never imported |
| `games/emulator_manager.py` | the flag-gated import (`_gc = None` else) | sets `_gc = None` only |
| | `__init__`: `self._gc = None`, `self._gc_helper_sid = None` | two instance attributes, never read on any other path |
| | `_refresh_process`: `if self._launch_kind == "dolphin" and self._gc is not None` | never true; then `self._gc = None` (an attribute already None) |
| | the catalog's `if _gc is not None and …` | `_gc` None: falls through to today's lookup |
| | class defaults `_gc` / `_gc_helper_sid` | attributes only |
| | `launch`: `if _gc is not None and … == "gamecube"` | `_gc` None: today's path (a `gamecube` title refused: no profile) |
| | `_pcsx2_stop` / `stop` reset: `self._gc = None` | an attribute set to None |
| | the new `_launch_dolphin` … `_dolphin_stop` methods | called only from the `dolphin` branches |
| | pause / resume / save / load / recovery save / paused recovery load / relaunch save / running recovery load / copy / stop: `if self._launch_kind == "dolphin"` | never true |
| `games/link_drop_recovery.py` | `**({"gc_states": …} if saved.get("gc_states") else {})` | only `_dolphin_save_recovery_state` returns `gc_states`: the row is today's |
| `games/native_stream_heartbeat.py` | `"gc_mode"` added to the copied fields | copied only when the plugin set it, which needs `_gc_session` |
| `hold_rewind.py` | `if _launch_kind == "dolphin" and not (state mode)` | never true |
| `players_session.py` | `"gamecube"` added to the plan sources | only `gamecube_session.plan()` writes that source |
| `plugins/games.py` | the flag-gated import; `SYSTEMS`, the scan, the heartbeat's `gc_mode`, the start's `gc_mode` + `gc_session` row | each under `_gc_session is not None` |
| `relaunch_ports.py` | `if _launch_kind == "dolphin": raise` | never true |
| `rewind_cores.py` | `RELEASE_SETTLE_GC_S`; the save / release branches `== "dolphin"`; the new `_save_gc` / `_release_gc` / `_verify_gc` | a constant; never true; called only from those branches |
| `tools/trip_log_keeper.py` | `GAME_LOG` + `gamecube`; `DOLPHIN_LOG`; `self.gclogs`; `seen["gc_logs"]`; the copy loop over `data/games/gamecube/logs/` | matches only names a GameCube launch writes. **Disclosed:** the keeper's `seen` gains an empty `gc_logs` set, so its `state.json` carries `"gc_logs": []` after its next restart (B53's `ps2_logs` did the same); nothing else changes with no such folder |
| `tools/diag_keeper.py` | a `gclogs/` tail resumed from `state.json` | only a key the new keeper wrote for a Dolphin log |
| `tools/diag_read.py` | `GC_LOG`, `DOLPHIN_*`, `dolphin_events`, the Logs / Analysis lines, `dolphin_counts`, the row keys, the Markdown section | match only `-gamecube.log` / `-dolphin.log` names and the `gc_session` row; a row gains keys only when `core == "dolphin"`; the section only when such a row exists |
| `tools/diag_check.py` | `"gamecube"` in the last-session systems | only a row with `system: "gamecube"` (written only for a Dolphin session) |
| `tools/gc_frames.py`, `tests/gamecube_session/` | new | a tool run by hand; the suite |

**Every host suite** in the B69 copy reads as in the baseline copy (`tests_host_b69.txt` vs `tests_host_baseline.txt`),
plus `tests/gamecube_session`.
