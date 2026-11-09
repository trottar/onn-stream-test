---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9e77af1e
---

# B65 — the N64 first start that never got ready: the cause the link + the onn's latched gate (fixed in B67); an N64 load only into a core answering PAUSED (inside PRIVYHUB_N64=1)

**Result: see `evidence/B65_N64_CONTINUE_LOAD_2026-11-09.md` (tests, mutations, proof).**

- **Apply:** `git apply evidence/b65_2026-11-09/b65.diff`. The four diffs go in order b65, b66, b67, b68, each
  against the previous snapshot; they are applied to the tree, uncommitted.
- **Live:** at the next companion restart.
- **Rollback:** reverse the diffs in the order b68, b67, b66, b65 (`diff_check.txt`).
