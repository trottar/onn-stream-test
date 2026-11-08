---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 6fcd2f23
---

# B61 — the N64 Home-hold freeze: no state save into a running N64 core; the silent-port storm bounded (inside PRIVYHUB_N64=1)

**Result: SETTLED + BUILT; tests and mutations in `evidence/B61_N64_HOLD_FREEZE_2026-11-08.md` §2.**

- **Apply:** `git apply evidence/b61_2026-11-08/b61.diff` — the four diffs in order b61, b62, b63, b64 (each
  against the previous snapshot); applied to the tree, uncommitted.
- **Live:** at the next companion restart (HOME-8 stage 1); no new environment line, nothing to adopt.
- **Rollback:** reverse the diffs in the order b64, b63, b62, b61 (`diff_check.txt`).
