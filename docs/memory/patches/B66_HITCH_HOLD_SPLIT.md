---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9e77af1e
---

# B66 — UX-R3's hold-resume split (the bar's number hitch_s_bar_per_10min) and the launch_ports row

**Result: see `evidence/B66_HITCH_HOLD_SPLIT_2026-11-09.md` (tests, mutations, proof).**

- **Apply:** `git apply evidence/b66_2026-11-09/b66.diff`. The four diffs go in order b65, b66, b67, b68, each
  against the previous snapshot; they are applied to the tree, uncommitted.
- **Live:** the tools at once; the row at the next companion restart.
- **Rollback:** reverse the diffs in the order b68, b67, b66, b65 (`diff_check.txt`).
