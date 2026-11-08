# B61 — absent = today (`PRIVYHUB_N64` absent, or any session that is not N64), hunk by hunk

Every new branch keys on `EmulatorManager._n64_core`. It is set only by an N64 launch (`n64_launch`, B59's
flag-gated branch), is `None` in `__init__`, and is reset to `None` at each of the three process resets.

- **`emulator_manager.py`:**
  - the attribute and its resets (no behaviour);
  - `self._n64_core = core_path.name if n64_launch else None`: None for every non-N64 launch;
  - `_capture_slot0_state`: `if getattr(self, "_n64_core", None)` is false otherwise, so `n64_resume_after` stays
    False; the `try / finally` runs today's `SAVE_STATE_SLOT 0` request and nothing after it;
  - `_n64_pause_for_save` / `_n64_resume_after_save`: new methods, called only from that branch.
- **`rewind_cores.py`:** two `if getattr(self.emulator, "_n64_core", None)` guards, false otherwise; the counter and
  two constants. PS1 / SNES saves and releases as today: `tests/rewind_cores` 13 and B61's PS1 tests.
- **`stall_signal.py`:**
  - `n64` is false unless the rewinder's emulator has `_n64_core`;
  - `self._silent` is only ever set by `_n64_silent_failure`, reached only when `n64`, so `silent` is None and the
    back-off check is skipped;
  - the pid check only clears it;
  - a failure takes today's `stall_resume_failed` branch;
  - `resumed` gets `after_silent_fails` only when `_silent` was set.
  - **Shown:** B61's PS1 bound test (43 tries, 43 rows, no `backoff_s`) and the no-rewinder test;
    `tests/stall_signal` 12 and `tests/stall_owner` 10 green.
- **`tests/n64_session`:** the harness reports `_n64_core` (test-only).
- **Every host suite** in the after-B61 copy reads as the baseline, plus `tests/b61_n64_hold` (`tests_host_b61.txt`).
