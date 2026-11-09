# B66 — the default proof (tools and one added row; no flag)

- **`diag_read`:**
  - `hitch_s`, `hitch_by` and `hitch_s_per_10min` are computed exactly as before; B36's own test still reads 4 /
    8.0 on its fixture;
  - the new keys (`hold_resume_s`, `hitch_s_bar`, `hitch_s_bar_per_10min`) and the two table columns are additions;
  - a session with no hold resume reads `hold_resume_s 0`, so the bar equals today's number;
  - the per-second view adds `h` only to a hitch second inside a hold's resume window.
- **`diag_check`:** a row without the new keys prints today's PS2 line byte for byte; an N64 row gains a line (none
  before); PS1 / SNES: none, as today.
- **`launch_ports`:**
  - one added recovery row after a successful launch;
  - `_log_launch_ports` never raises (a failed row cannot fail a launch);
  - `_last_device_args` is a new attribute; no other row or response changes.
- **Shown:** `tests/diag_read` 11, `tests/diag_check` 4 and `tests/diag_keeper` 13 green, unchanged;
  `test_today_without_a_hold_resume`; `test_a_failed_launch_writes_none`; every host suite as the baseline plus the
  new ones (`tests_host_b66.txt`).
