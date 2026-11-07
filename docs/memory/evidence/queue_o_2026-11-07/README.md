# Queue O (2026-11-07) — the integration (session B's coordinator)

- `started_at.txt`, `baseline_head.txt` (ea40a93f), `git_status_at_start.txt` (only queue O's own evidence dirs, made a
  moment before), `units_at_start.txt` (the companion and `privyhub-diag` only), `units_before_apply.txt`,
  `applied_to_tree_at.txt`.
- **Baselines** (`/tmp/b_q07o_base`, the tree's companion/ tools/ tests/ PrivyHub/):
  - `tests_regression_queue_o_baseline.txt`: 44 `tests/` suites OK; six `tools/` tests fail in a copy (the same six in
    every copy of this run);
  - the JVM baseline is the tree's 219 (queue N's integrated count).
- **The merge** (`/tmp/b_q07o_all`): `b46.diff`, then `b47.diff`, applied cleanly.
  - `tests_regression_after_queue_o.txt`: the baseline's outcomes plus `players_session` (13); `vod_log` 16, all OK;
  - `jvm_all_console.txt`, `jvm_integrated_junit.txt`: 228 / 228.
- **`queue_o_combined.diff`:** applied to the tree (`git apply --check` first).
  - The tree's changed files equal the merged copy's; `git diff --check` clean; the changed `.py` compile.
  - `after_sha256.txt`; `tests_tree_after_apply.txt` (the six touched suites from the tree).
- **The APK** (`apk_sha256.txt`, `apk_build_console.txt`, `apk_rebuild_console.txt`): `cfe0211c…a65f`, JVM 217 / 217 in
  the APK copy (228 less B27's 4 and B29's 7). Pinned at `PrivyHub/app/build/queue_o_built/`, NOT installed.
- `redact_check.py` / `.txt` (also over the B48 design, the done file, KNOWN_ISSUES and ROADMAP), `manifest.sha256`.
