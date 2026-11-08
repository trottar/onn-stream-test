# B59 — `PRIVYHUB_N64` absent (or any value but `1`) = today, hunk by hunk

`b59_code.diff`, 10 files. The new files (`companion/n64_session.py`, `companion/inplace_library.py`,
`tools/n64_core_check.py`, `tools/n64_frames.py`, `tests/n64_session/`) are never imported by the companion without the
flag. The two tools run only when A runs them; neither changes a file.

**`companion/games/emulator_manager.py`:**
1. **The import:** `_n64 = None` unless the flag reads `1`. Every later hunk tests `_n64 is not None` first.
2. **`_resolve_n64`:** a new method, called only from hunk 5's `n64_launch` branch.
3. **`_controller_profile_catalog`:** `if _n64 is not None and …`. Absent: skipped, and an `n64` game refuses as today
   (no profile). Proven by `Plugin.test_absent_is_today`: the catalog is `EmulatorError`.
4. **`launch`, after `_runtime_details()`:** `n64_launch` is `False` when `_n64` is None, so the runtime is
   today's object, untouched.
5. **`launch`, the content:** `if n64_launch … else` today's `_resolve_game` call, unchanged.
6. **`launch`, the plan / options:** inside `if n64_launch`; `n64_options` stays None otherwise and is read only
   under `n64_launch`.
7. **`launch`, the log lines:** `if n64_launch and …`.
8. **`launch`, the payload key:** `if n64_launch and …`. No `n64_session` key otherwise.

**`companion/plugins/games.py`:**
1. **The import:** `_n64_session = None` unless `1`.
2. **`__init__`:** `SYSTEMS` reassigned only when `_n64_session` is set. Absent: the class dict (or B49's instance
   dict), as today.
3. **`_scan`:** `if _n64_session is not None and …`. With `n64` absent from `SYSTEMS` it is never reached anyway.

**`companion/players_session.py`:** `ports_set` accepts one more plan source, `"n64"`. Only
`n64_session.plan()` makes a plan with that source, and only an N64 launch calls it (flag on). Absent: no session
dict carries `"n64"`, so every branch returns as today.

**`tools/diag_read.py`:** `CORES` gains `"n64"`. It is read only for a game log named `…-game_n64_<hex>.log`. Absent,
no such log exists (an `n64` launch is refused before any log is opened), so every read is today's. This is the one
unconditional line. It is a reader on demand: the keeper (`privyhub-diag`) does not import it and is not restarted.

**Shown by the tests (`tests/n64_session`, fresh interpreters per flag state):**
- **flag absent, `0` and `yes`:**
  - `n64_session` / `inplace_library` not imported;
  - `SYSTEMS` without `n64`; the scan only today's systems; the catalog refuses (`test_absent_is_today`);
- **an `n64` launch absent / `0`:** today's refusal ("No emulator profile configured for system: n64"), no Popen, no
  `.opt` (`test_absent_is_todays_refusal_nothing_written`);
- **a SNES launch with the flag absent and with it on** (the same fake project): the same command, the same
  `privyhub-input.cfg` and `privyhub-session.cfg` (the random command port masked), no `.opt`, no `N64` log line, no
  `n64_session` key, the same `ports_set` (`test_another_systems_launch_is_byte_for_byte_with_the_flag`);
- **`status()` is not touched:** the N64 profile goes only into the launch's runtime copy
  (`test_the_profile_is_injected_into_a_copy`), so with the flag on and no core the runtime does not turn "not
  ready".

**Every host suite** in the B59 copy reads as the baseline copy, plus `tests/n64_session` 28
(`tests_host_baseline.txt`, `tests_host_b59.txt`): the same six `tools/` tests fail in both, identically.
