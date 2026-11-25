---
memory_schema: 1
as_of: 2026-11-25
baseline_commit: 2d8a8345 (this repo)
---

# B221 — a valid test variant is the glyph's own size (queue BS)

**Result:** `evidence/B221_VARIANT_SIZE_2026-11-25.md`.

- **Files:**
  - `tools/party_steps.py`: `VARIANT_SIZE_TOL` = 2; `test_variants` throws away a test variant whose cut box's width or
    height is more than 2 px off the pasted glyph's (B214's two conditions as they were).
  - Tests: `tests/b221_variant_size/` (new).
  - The diff: `evidence/b221_2026-11-25/b221.diff`.
- **Switch:** none — test variants only; templates, the once rule's gate, `BARS`, `companion/` unchanged.
- **Rollback:** `git apply -R evidence/b221_2026-11-25/b221.diff`.
