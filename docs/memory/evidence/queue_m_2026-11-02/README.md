# Queue M (2026-11-02) — the integration (session B's coordinator)

- `started_at.txt`, `baseline_head.txt` (e0155d1c; A's uncommitted G-A10 `tools/` edits were in the copy and
  untouched), `git_status_at_start.txt`, `units_at_start.txt` (the companion and `privyhub-diag` only),
  `units_before_apply.txt`, `applied_to_tree_at.txt`.
- **Baselines** (`/tmp/b_q02m_base`):
  - `tests_regression_queue_m_baseline.txt`: 41 / 41 `tests/` suites OK; the four `tools/` tests fail in a copy as at
    every baseline;
  - `jvm_baseline_console.txt` / `_junit.txt`: 184 / 184.
- **The merge** (`/tmp/b_q02m_all`): `b38.diff`, `b39.diff`, `b40.diff` applied cleanly in that order.
  - `tests_regression_after_queue_m.txt`: the baseline's outcomes line for line plus 2 new suites, OK;
  - `jvm_all_console.txt`, `jvm_integrated_junit.txt`: 195 / 195.
- **`queue_m_combined.diff`:** applied to the tree (`git apply --check` first). The tree's four dirs then equal the merged
  copy (build outputs aside); `git diff --check` clean; the changed `.py` compile; `after_sha256.txt`.
- **The APK** (`apk_sha256.txt`, `apk_build_console.txt`, `apk_rebuild_console.txt`, `jvm_apk_copy_junit.txt` 184 / 184):
  - built in `/tmp/b_q02m_apk` (B29 then B27 reversed, then this diff);
  - `0132b944…e24f`, pinned at `PrivyHub/app/build/queue_m_built/`, NOT installed.
- `redact_check.py` / `.txt`, `manifest.sha256`.
