---
memory_schema: 1
as_of: 2026-11-23
baseline_commit: ec6d8ea9 (this repo)
---

# B200-B202 — a score title's numbers as drawn, same-shape places never taken, cells off the final's line; `--find` as the user says it; the user's saves asked only through register

**Result:** `evidence/B200_DRAWN_PLACES_FIND_2026-11-23.md`.

- **Files:**
  - `tools/h7_endscreen.py`:
    - `Drawn` (new): a number's value and its glyphs as drawn;
    - `score_numbers`, `score_cells`, `read_scores`, `read_columns` and `EndedScore` return or keep it;
    - `_shape_cells`, `_shapes_explained`, `SCORE_SAME_SHAPE` (new): a place whose shapes the labels do not
      explain is never taken;
    - `_find_place` takes an `ok` filter;
    - `_offline_column`, `_before`, `_choose_offline` (new): line-score columns off the final's line, a side's
      chosen together in drawn order;
    - `_find_columns`: the shape rule, a place overlapping one taken skipped, the off-line fallback;
    - `learn_scores`: the finals filtered, the off-line columns' groups;
    - the reader's templates by exact group;
    - the docstring.
  - `tools/party_add_game.py`:
    - `_drawn` (new); `_sides` / `_text` keep a number as drawn; `_digits_of` counts drawn digits;
    - `_counted_digits` (new): a column of another size teaches no final's digit;
    - `_mend` / `_fill` / `_read_all` as drawn; `_culprit`: a final read blank keeps its label; `_one_save_digits`
      over the finals' group;
    - the label lines' "as drawn" words;
    - `--find`: `_plain`, `_base`, `_library`, `_match_title` (new), `_find_title`, `FIND_NAMED`;
    - `_endscreen` adds the tools folder to the path once;
    - the docstring.
  - `docs/memory/handoffs/ADD_GAME_TASK.md`:
    - the status line;
    - §1: `--find`'s words, register first, no "other teams / characters" for score and letters, the same match
      twice, the highest score's change;
    - §2: read as drawn.

    The template unchanged.
  - Tests: `tests/b200_drawn_places/` (new: `test_b200.py`, `pad_capture.py`); `tests/b201_find/` (new:
    `test_b201.py`); `tests/b198_max_score/test_b198.py` (`Limit`'s assertion: the place cell or the read-back,
    never a PASS — disclosed).
  - The diff: `evidence/b200_2026-11-23/b200.diff`.
- **Switch:** none — a reading without a leading zero is today's text and T90's / T91's label and learn verdicts are
  the same (T91's file but for its recorded training time). No bar in `BARS` lowered; `companion/` unchanged. The running companion reads the changed
  reader only after its next start (session A's bench restarts it).
- **Rollback:** `git apply -R evidence/b200_2026-11-23/b200.diff`.
