# B62 — absent = today (`PRIVYHUB_N64` absent; any non-N64 system), hunk by hunk

- **`n64_session.py`:** new functions, imported only with the flag (B59: the module itself is never imported without
  it).
- **`emulator_manager.py`:**
  - the label branch: `if _n64 is not None and system_id == _n64.SYSTEM_ID` → else `"Core default"`, as today (PS2's
    label unchanged);
  - the remap write sits inside B59's `if n64_launch` block; the log line inside `if n64_launch and …`; the payload
    keys inside the N64 payload;
  - `_n64_layout`: new, called only from those branches;
  - the input-cfg lines: `*([...] if _n64 is not None and system_id == "n64" else [])` → `[]` otherwise, so the file
    is byte for byte.
- **`tools/n64_core_check.py`:** `--remap` / `--config-dir` are new options; without them the output is today's.
- **Shown:** `tests/b62_n64_mapping` `test_absent_and_other_systems` (no flag → no `.rmp`, today's refusal; SNES with
  and without the flag → no `.rmp`, no lines, today's label). B59's `test_another_systems_launch_is_byte_for_byte_with_the_flag`
  still green. Every host suite as the baseline (`tests_host_b62.txt`).
