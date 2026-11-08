---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 6fcd2f23
---

# B62 — the N64 layout: ○ = C-right, △ = C-up by a verified core remap; the per-title n64_layout; the layout as the details label (inside PRIVYHUB_N64=1)

**Result: SETTLED + BUILT; tests and mutations in `evidence/B62_N64_MAPPING_2026-11-08.md` §2.**

- **Apply:** `git apply evidence/b62_2026-11-08/b62.diff` — the four diffs in order b61, b62, b63, b64 (each
  against the previous snapshot); applied to the tree, uncommitted.
- **Live:** at the next companion restart (HOME-8 stage 1); no new environment line, nothing to adopt.
- **Rollback:** reverse the diffs in the order b64, b63, b62, b61 (`diff_check.txt`).
