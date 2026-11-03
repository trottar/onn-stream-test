# B32-host — flag absent = today: PROVEN

- **`PRIVYHUB_STEP_IN_PLACE` absent / empty / `0` / junk:** a fresh process imports no `step_in_place` and
  `native_stream.STEP_IN_PLACE` is None (`TheFlag.test_nothing_imported_without_the_line`, five values); the actuator
  entry then calls today's `diagnostic_c3_validated_bitrate_transition` (`test_the_actuator_entry_absent_is_todays…`).
- **AST** (`proof_flag_absent.py`, `proof_flag_absent_output.txt`): each of the three edited modules with B32's guarded
  additions taken out equals its predecessor's AST (`predecessors/`, the base bytes), and differs before stripping
  (the edit is real):
  - `native_stream.py`: the `STEP_IN_PLACE = None` / guarded import, and the one `if STEP_IN_PLACE is not None` in the
    non-sized branch of `adaptive_level_transition`;
  - `adaptive_bitrate_live.py`: the one `**({...} if … "in_place" in video else {})` entry of the `transition_done` row
    — today's actuator never returns `in_place`, so it adds no key; the row key for key and value for value as the
    predecessor's (`TheLadderRow.test_todays_payload_gives_todays_row`; and the same row printed from the base and the
    copy, identical);
  - `remote_umbrella.py`: `cap_on_umbrella_ladder` / `_cap_import_obj` and the `if self.cap_on_umbrella_ladder` in
    `__init__`, the one `if` in `_in_force`, and `_to_lan`'s `… if self.cap_on_umbrella_ladder else None` (None without
    an explicit cap) — so without an explicit `PRIVYHUB_REMOTE_RUNG_CAP` beside the umbrella, or with an explicit
    ladder line, B28 byte for byte (`tests/remote_umbrella` unedited, green).
- **The relay** (`native_fec_relay.py`) is not edited: the splice wraps the relay *instance's* `_handle_rtp` only at the
  first in-place step, and idle it returns every packet unchanged (`TheSplice.test_idle_is_pass_through_byte_for_byte`).
