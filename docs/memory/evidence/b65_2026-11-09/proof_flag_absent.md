# B65 — absent = today (`PRIVYHUB_N64` absent, or any non-N64 session), hunk by hunk

- **`emulator_manager.load_state`:** the new check runs only `if getattr(self, "_n64_core", None)`; B61's
  `_n64_core` is set only by an N64 launch (flag-gated), so `n64_status_ms` stays None, no extra `GET_STATUS` is sent,
  and `_n64_continue_event` is never set. The load request and everything after it are today's.
- **`_n64_confirm_paused_for_load`:** new, reached only from that branch. **`_n64_continue_event`:** a new attribute,
  None.
- **`plugins/games.py`'s `load-state`:** sets the attribute to None, calls today's `load_state`, and writes a row only
  if the attribute is a dict (never without an N64 session). The return / raise is unchanged.
- **Shown:** `test_ps1_as_today` (no `GET_STATUS` before the load, no event), `test_a_fresh_manager`; every host suite
  in the after-B65 copy reads as the baseline plus the new suite (`tests_host_b65.txt`).
