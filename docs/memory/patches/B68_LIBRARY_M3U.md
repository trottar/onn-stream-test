---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9e77af1e
---

# B68 — tools/library_m3u.py: one entry per multi-disc PS1 title (behind PRIVYHUB_IMPORT=1; NOT applied)

**Result: see `evidence/B68_LIBRARY_M3U_2026-11-09.md` (tests, mutations, proof).**

- **Apply:** `git apply evidence/b68_2026-11-09/b68.diff`. The four diffs go in order b65, b66, b67, b68, each
  against the previous snapshot; they are applied to the tree, uncommitted.
- **Live:** only when A runs it with the user's "apply m3u"; undo is its rollback.
- **Rollback:** reverse the diffs in the order b68, b67, b66, b65 (`diff_check.txt`).
