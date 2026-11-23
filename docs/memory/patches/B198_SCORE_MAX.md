---
memory_schema: 1
as_of: 2026-11-23
baseline_commit: 9ea4bea0 (this repo)
---

# B198-B199 — a score title's highest score (`register --max-score N`); the task's question

**Result:** `evidence/B198_SCORE_MAX_2026-11-23.md`.

- **Files:**
  - `tools/party_add_game.py`: `--max-score` parsed (register, score only); register's cell and the binding's
    `max_score`; `register_inputs` gains it only when given; `expected_digits`, `_every_digit_cell` (new); learn's
    every-digit cell over the expected digits only ("not expected" in its read, `recorded`); the spec's
    `score.max_score` and its reuse key; `_score_line` names only expected digits; the docstring.
  - `tools/h7_endscreen.py`: `check_spec` (a version-4 spec's `max_score` a whole number); `ReaderScore.read` (a final
    above it -> `unknown`, `end_unread`, `above_max`).
  - `docs/memory/handoffs/ADD_GAME_TASK.md`: §1's score bullet (B199's two questions, the draw's line, the give-up
    line), §2's learn line, §4's every-digit bullet, the status line. The template unchanged.
  - Tests: `tests/b198_max_score/` (new: `test_b198.py`, `low_capture.py`).
  - The diff: `evidence/b198_2026-11-23/b198.diff`.
- **Switch:** `--max-score` on register (absent = today, byte for byte the same inputs digest, cell name and spec). The
  hub reads `max_score` from the spec only when learn wrote it. No bar in `BARS` lowered; `companion/` unchanged.
- **Rollback:** `git apply -R evidence/b198_2026-11-23/b198.diff`.
