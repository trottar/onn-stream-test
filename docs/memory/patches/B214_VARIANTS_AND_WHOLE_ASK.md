---
memory_schema: 1
as_of: 2026-11-24
baseline_commit: 689207fc (this repo)
---

# B214-B217 — the once rule's variants, plan's whole ask, register on three saves (queue BQ)

**Result:** `evidence/B214_VARIANTS_AND_WHOLE_ASK_2026-11-24.md`.

- **Files:**
  - `tools/party_steps.py`: `test_variants` (valid only when cut as one glyph with >= `SYN_OWN` of its ink pasted; up
    to `VARIANT_DRAWS` 24 draws, `VARIANTS_NEEDED` 8), two random streams (templates / tests), `_once_rule` needs
    eight and records what they read as; `score_gates` / `letters_gates` (train's gates 1-3, nothing written) called by
    `plan` and `train`.
  - `tools/party_add_game.py`: `new_path`; register's "kept states present" on the new path needs begin, other, one
    ending; register keeps the binding's `survey`.
  - Tests: `tests/b214_variants/` (new); `tests/b208_survey/test_b208.py` (two assertions to B214 / B215: eight
    variants, plan's counted / not counted rows); `tests/b181_every_digit/line_capture.py`, `test_b181.py`,
    `tests/b185_overtime/test_b185.py` back to `ef8a0ce5` plus a first line.
  - The diff: `evidence/b214_2026-11-24/b214.diff`.
- **Switch:** none beyond BP's — the new path is entered by `survey` or by a score / letters title the old learn never
  learnt. Nothing in `BARS` changed; `companion/` unchanged.
- **Rollback:** `git apply -R evidence/b214_2026-11-24/b214.diff`.
