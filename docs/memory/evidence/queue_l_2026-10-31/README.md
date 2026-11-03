# Queue L (2026-10-31) — the integration (session B's coordinator)

- `started_at.txt`, `baseline_head.txt` (1904fe8), `git_status_at_start.txt`, `units_at_start.txt` (the companion and
  `privyhub-trip-log` only), `units_before_apply.txt`, `applied_to_tree_at.txt`.
- **Baselines** (`/tmp/b_q31l_base`, the tree's four dirs at the start):
  - `tests_regression_queue_l_baseline.txt`: 33 / 33 `tests/` suites OK; the four `tools/` tests fail in a copy as at
    every baseline;
  - `jvm_baseline_console.txt`, `jvm_baseline_junit.txt`: 161 / 161.
- **The merge** (`/tmp/b_q31l_all`): `b32_client.diff`, `host/b32_host.diff`, `b33.diff` applied cleanly. `b34.diff`
  had one rejected hunk (`merge_b34_rejected_hunk.rej`): the report key and the heartbeat query line sit on the same
  lines as B32's. The coordinator put B34's two blocks right after B32's, with the text unchanged. `b35.diff` and
  `b36.diff` (regenerated after the B36 §5 fix) applied cleanly.
  - `tests_regression_all1.txt` (B32-B35) and `tests_regression_after_queue_l.txt` (B32-B36): the baseline's outcomes
    line for line plus 8 new suites, all OK;
  - `jvm_all1_console.txt`, `jvm_integrated_junit.txt`: 184 / 184.
- **`queue_l_combined.diff`:** the tree at 1904fe8 → the merged tree; `git apply --check` then `git apply` on the tree;
  the tree's four dirs then equal `/tmp/b_q31l_all` (build outputs aside). `git diff --check` clean; every changed
  `.py` compiles.
  - `after_sha256_client.txt`, `after_sha256_host.txt`.
- **The APK** (`apk_sha256.txt`, `apk_build_console.txt`, `apk_rebuild_console.txt`, `jvm_apk_copy_junit.txt` 173 / 173):
  - built in `/tmp/b_q31l_apk`: the base with B29 then B27 reversed (byte-equal to their recorded predecessors), plus
    this diff;
  - `554ccf61…9902`, pinned at `PrivyHub/app/build/queue_l_built/`, NOT installed.
- `redact_check.py` / `.txt`, `manifest.sha256`.
