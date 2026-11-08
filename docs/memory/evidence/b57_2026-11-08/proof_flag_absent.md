# B57 — `PRIVYHUB_PS2` absent = today byte for byte, hunk by hunk; PS1 (RetroArch) untouched

`b57_code.diff` against the baseline copy (`d618a20a`): 5 files. Without the flag `emulator_manager._ps2` is None,
`_launch_pcsx2` is never reached (B49's refusal), so `_launch_kind` is never `"pcsx2"` and no session is PS2: `kind`
in `relaunch_ports.run` is `"retroarch"` for every session.

| file | hunk | why absent is today |
| --- | --- | --- |
| `ps2_session.py` | `RELAUNCH_SLOT = 7` | the module is imported only with the flag (B49); the name is read only by the two PCSX2 methods below. |
| `games/emulator_manager.py` | `save_relaunch_state` | B54's `if self._launch_kind == "pcsx2"` keeps its test; only its body changed (B54's `PS2_NO_STATES` refusal → `_pcsx2_save_relaunch_state`). The RetroArch body is unchanged. |
| `games/emulator_manager.py` | `load_recovery_state_running` | B55's `if self._launch_kind == "pcsx2"` keeps its test; `source is None` → B55's call exactly (no argument); a `source` → the slot-7 load. The RetroArch body is unchanged. |
| `games/emulator_manager.py` | `_pcsx2_save_relaunch_state` (new); `_pcsx2_load_recovery_state_running(relaunch_source=None)` | called only from those two PCSX2 branches. With `relaunch_source` None the method is B55's: slot 8, the recovery source, the same log text (`PS2 recovery load: …`), the same errors (the static / fault error now also carries `ps2_picture`, an attribute nobody read before). |
| `relaunch_ports.py` | the save | `kind == "retroarch"` → B54's code unchanged (a failure = refused, nothing touched); the `else` (PCSX2 only) → the slot-7 save. |
| `relaunch_ports.py` | the launch | B54's inline launch moved into `launch_ports(name, ports)`: for `"launch"` the same step names (`launch`, `launch_previous`), the same row fields (`fallback`, `launch_error`, `ok`, `total_ms`, `ended`), the same `end_game_session`, the same error text. |
| `relaunch_ports.py` | the load | `state_path is not None and kind == "pcsx2"` → B57's branch; `elif state_path is not None` → B54's resume / settle / load / pause unchanged; `else` unchanged. |
| `relaunch_ports.py` | the response | `reason` added to the copied keys; only PS2 rows set `reason` (B54 set it only on PS2 too), so a RetroArch response is unchanged. |
| `tests/relaunch_ports/test_relaunch_ports.py` | the PS2 test | moved to B57's meaning (disclosed): a failed PS2 save gives B54's recorded restart (`ps2_relaunch_save_failed`). Every RetroArch test is unchanged and green. |

- **PS1 untouched:** B54's RetroArch tests (the order pause / save / stream stop / stop / launch(4) / resume / settle /
  load / pause / stream start, the 7600-ms fake-timed total, the rows, the refusals, the previous-ports fallback, both
  launches failing, the failed load) unchanged and green in the B57 copy.
- **Absent:** `test_b57.Unchanged.test_absent_no_ps2_session_exists` (with `_ps2` None a manager has no launch kind and
  its relaunch save is B54's own path); `test_the_source_less_running_load_is_b55s_slot_8`; B49-B55's absent tests in
  `tests/ps2_session` (93) green.
- **Every host suite** in the B57 copy equals the baseline copy except `tests/relaunch_ports` (10 → 19 tests);
  the same six `tools/` tests fail in both, identically (`tests_host_baseline.txt`, `tests_host_b57.txt`).

**Result: PROVEN.**
