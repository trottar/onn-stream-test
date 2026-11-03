# B36 — absent = today, PROVEN (files)

B36 has no flag: it is new files only, and nothing runs until A installs and starts `privyhub-diag`.

- **Existing files changed by B36: 0** (every file of the copy's companion/ tools/ tests/ PrivyHub/ that exists in
  the base compared byte for byte with `cmp`). `b36.diff` holds 8 `new file` entries and nothing else.
- `tools/trip_log_keeper.py` (the running `privyhub-trip-log`'s code) and `tools/trip_check.py` (the runbook's check) are
  byte for byte the base: `predecessor_sha256.txt` = their lines in `after_sha256.txt` = the tree's.
- **Files under companion/ or PrivyHub/ that name diag_keeper / diag_read / diag_check: 0.** The companion and the
  client never load B36.
- No unit file installed (`tools/privyhub-diag.service` is a file in the tree for A), no `~/privyhub_diag/` created
  (`ls ~/privyhub_diag`: no such directory, after the smoke run, which used a /tmp root).
- Host suites in the copy: the baseline's outcomes line for line plus three new suites OK
  (`tests_regression_after.txt` vs `tests_regression_queue_l_baseline.txt`; the four tools/ tests fail in a copy as at
  every baseline).

Checked 2026-10-31T17:49:42Z.
