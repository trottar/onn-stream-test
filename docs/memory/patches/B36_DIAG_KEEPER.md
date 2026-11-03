---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8
---

# B36 — the always-on diagnostics keeper (`privyhub-diag`), `diag_read.py`, `diag_check.py`

**Result: BUILT, new files only.**
- **Tests:** `tests/diag_keeper` 13, `tests/diag_read` 11, `tests/diag_check` 4 green; 5 mutations caught; every host
  suite the baseline's.
- **Dry run over the trip keeper's copies:** TRIP-R2 §1 47 / 48 cells and `sessions.tsv` 900 / 900 cells the same.
- **Absent:** 0 existing files changed, PROVEN. Not installed; nothing committed.
- **Where:** record `evidence/B36_DIAG_KEEPER_2026-10-31.md`; diff `evidence/b36_2026-10-31/b36.diff`.

- **Built:**
  - **`tools/diag_keeper.py`:** B30's keeper made permanent. It writes redacted copies every 5 min into
    `~/privyhub_diag/<UTC date>/`, with the 60-s samples. It resumes after a restart (`state.json`) and has no cap.
  - **Retention, the one deletion:** a `YYYY-MM-DD` dir directly under the root, older than 30 days, removed whole.
  - **The summary:** one `sessions.jsonl` row 90 s after each `session_ended`.
  - **The unit:** `tools/privyhub-diag.service`.
  - **`tools/diag_read.py <range>`:** `last night` / `today` / `YYYY-MM-DD HH:MM..HH:MM` / `trip`. It writes Markdown
    under `evidence/reads/` with:
    - the per-session and per-10-min tables;
    - every restart / rewind / pause with its cause;
    - the ±60-s views.
  - **`tools/diag_check.py`:** the trip check's six lines, the sixth `privyhub-diag`.
- **Unchanged:** `tools/trip_log_keeper.py` (`privyhub-diag` imports it: keep it) and `tools/trip_check.py` (the
  runbook's).
- **Apply:** `git apply docs/memory/evidence/b36_2026-10-31/b36.diff`. Then, at home (A, HOME-1):

  ```
  mkdir -p ~/.config/systemd/user && cp tools/privyhub-diag.service ~/.config/systemd/user/
  systemctl --user daemon-reload && systemctl --user enable --now privyhub-diag
  python3 tools/diag_check.py
  ```

- **Rollback:**
  - `systemctl --user disable --now privyhub-diag`, then remove the unit file;
  - the copies stay in `~/privyhub_diag/` until A removes them;
  - remove the 8 new files.

- **After the merge (record §5):** `diag_read` takes `in_place` from the step's `transition_done` row, where B32-host writes
  it (+8 lines; the fixture likewise). `b36.diff` is regenerated with the fix; `b36_worker_original.diff` is kept beside it.
