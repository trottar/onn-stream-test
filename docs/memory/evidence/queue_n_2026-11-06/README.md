# Queue N (2026-11-06) — the integration (session B's coordinator)

- `started_at.txt`, `baseline_head.txt` (795d80d4, the tree clean), `git_status_at_start.txt`, `units_at_start.txt` (the
  companion and `privyhub-diag` only), `units_before_apply.txt`, `applied_to_tree_at.txt`.
- **Baselines** (`/tmp/b_q06n_base`):
  - `tests_regression_queue_n_baseline.txt`: 43 / 43 `tests/` suites OK; the four `tools/` tests fail in a copy as at
    every baseline;
  - `jvm_baseline_*`: 195 / 195.
- **The merge** (`/tmp/b_q06n_all`): `b41.diff`, `b42.diff` (`jvm_b41b42_console.txt`, 211 / 211), `b43.diff` applied
  cleanly in that order.
  - `tests_regression_after_queue_n.txt`: the baseline's outcomes plus `player_prompt` (11); `vod_drop_test` 21,
    `vod_log` 12; all OK;
  - `jvm_all_console.txt`, `jvm_integrated_junit.txt`: 219 / 219.
- **`queue_n_combined.diff`:** applied to the tree (`git apply --check` first). The tree's four dirs then equal the merged
  copy (build outputs aside); `git diff --check` clean; the changed `.py` compile; `after_sha256.txt`.
- **The APK** (`apk_sha256.txt`, `apk_build_console.txt`, `apk_rebuild_console.txt`, `jvm_apk_copy_junit.txt` 208 / 208):
  `8ba4d996…605f`, pinned at `PrivyHub/app/build/queue_n_built/`, NOT installed.
- `redact_check.py` / `.txt`, `manifest.sha256`.
