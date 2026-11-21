---
memory_schema: 1
as_of: 2026-11-21
baseline_commit: 45e8ec97 (this repo)
---

# B185-B188 — a column only one save fills; a digit one save shows several times; the ask to the user; the task's words

**Result:** `evidence/B185_OVERTIME_ONE_SAVE_ASK_2026-11-21.md`.

- **Files:**
  - `tools/party_add_game.py`:
    - B185: `NO_PLACE` (`*`, a column the left-out reader has no place for); `_read_all` (a direct read at the places
      when the replay never ends; `direct=True` for the label stage's read-back and learn's left-out cell); `_judge`
      (replaces `_compare`: "shown only here" digits and columns); `_mend` and `_culprit` (a final read in part);
      label's read-back cell and its record.
    - B186: `ACROSS_MARGIN` (0.05); `_one_save_digits`; `_fill`; learn's left-out and every-digit cells.
    - B187: `ASK_REASONS`; per-reason counts (`named_for`); `ask_folder`, `_column_words`, `_when_saved`, `_ask_line`;
      a user's answer refused unless in the line score's own form; the "Stop: … back to the chat" line; register
      `--collect` keeps the slot and the slot file's time in the binding; close removes `logs/add_game_ask/<code>_*.png`.
    - B188: learn's line ends with how many digits are still short and that it may ask once more.
  - `tools/h7_endscreen.py`: `save_glyphs`, `read_glyph_with`, `spread_across_within` (new; nothing existing changed).
  - `docs/memory/handoffs/ADD_GAME_TASK.md`: B188 (the overtime rule, the ask line, learn's every-digit words).
  - Tests: `tests/b185_overtime/` (new). `tests/b178_score_kind/` (the ask's words; the ask folder in the harness's
    temp dir; end_P1's read-back now `?5-2`; the 16-for-15 misread now named at once — disclosed).
    `tests/b181_every_digit/` (the every-digit cell's one key compared — disclosed).
  - The diff: `evidence/b185_2026-11-21/b185.diff`.
- **Switch:** the `score` kind's label and learn stages only (the add-a-game tool; nothing on the hub's path). The
  hub's reader, `winner` / `places`, T88's / T89's rules unchanged. No bar in `BARS` lowered.
- **Rollback:** `git apply -R evidence/b185_2026-11-21/b185.diff`.
