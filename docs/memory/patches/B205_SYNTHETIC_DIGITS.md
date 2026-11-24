---
memory_schema: 1
as_of: 2026-11-24
baseline_commit: 9dc4cc10 (this repo)
---

# B205 — synthetic training for the score kind (templates only)

**Result:** `evidence/B205_SYNTHETIC_DIGITS_2026-11-24.md`.

- **Files:**
  - `tools/h7_endscreen.py`:
    - `_digit_stats(cells, shown, train=None)`: the templates from the real and synthetic glyphs, the synthetic ones
      at most as many as the real; every measure of the real alone;
    - `real_glyphs`, `synthetic_digits`, `_held_read`, `train_digits` (new);
    - `SYN_DIGIT_HELD` / `_PER_ROUND` / `_ROUNDS`;
    - `learn_scores` trains after the size decision and records `score.trained`.
  - Tests: `tests/b205_synthetic_digits/` (new: `test_b205.py`).
  - The diff: `evidence/b205_2026-11-24/b205.diff`.
- **Switch:** none — every score spec learnt from now on trains its templates. No gate counts a synthetic glyph; no
  bar in `BARS` lowered; `companion/` unchanged. The running companion reads the reader after its next start.
- **Rollback:** `git apply -R evidence/b205_2026-11-24/b205.diff`.
