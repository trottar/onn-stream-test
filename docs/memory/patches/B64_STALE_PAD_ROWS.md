---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 6fcd2f23
---

# B64 — the stale pre-session pad_slots rows tagged stale: true (host logging only)

**Result: SETTLED + BUILT; tests and mutations in `evidence/B64_STALE_PAD_ROWS_2026-11-08.md` §2.**

- **Apply:** `git apply evidence/b64_2026-11-08/b64.diff` — the four diffs in order b61, b62, b63, b64 (each
  against the previous snapshot); applied to the tree, uncommitted.
- **Live:** at the next companion restart (HOME-8 stage 1); no new environment line, nothing to adopt.
- **Rollback:** reverse the diffs in the order b64, b63, b62, b61 (`diff_check.txt`).
