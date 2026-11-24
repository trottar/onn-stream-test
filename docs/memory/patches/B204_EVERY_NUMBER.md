---
memory_schema: 1
as_of: 2026-11-24
baseline_commit: 2b4afeab (this repo)
---

# B204 — every number on a score title's final screen; another size of the score's font counted when the numbers say so

**Result:** `evidence/B204_EVERY_NUMBER_2026-11-24.md`.

- **Files:**
  - `tools/party_add_game.py`:
    - `SIDE` (a side's stats rows after `:`);
    - `Row`, `_periods` (new); `_sides` / `_text` / `_score_class` carry the stats rows;
    - the sum check and the ask's sum over the period cells only;
    - `_culprit` keeps a side's period count;
    - the label line names the stats rows.
  - `tools/h7_endscreen.py`:
    - `_one_font`, `SIZES_PER_DIGIT` (new): another size counted when every one-digit pair across sizes is nearer
      than every two-digit pair (`score.sizes`);
    - `_centre`, `_nearest_own` (new): an off-line column is its nearest final's side;
    - `_choose_offline` searched depth first over as many candidates as the side has columns.
  - `docs/memory/handoffs/ADD_GAME_TASK.md`: §2 (read every number, the stats table after `:`) and the status line.
    The template unchanged.
  - Tests: `tests/b204_every_number/` (new: `test_b204.py`); `tests/b200_drawn_places/test_b200.py` (`Drawn`'s and
    `Counted`'s assertions: one font at two sizes now counted — disclosed).
  - The diff: `evidence/b204_2026-11-24/b204.diff`.
- **Switch:** none. A reading without `:` is today's text. A title whose columns are all on the final's line (T90) is
  unchanged. No bar in `BARS` lowered; `companion/` unchanged; the running companion reads the reader after its next
  start.
- **Rollback:** `git apply -R evidence/b204_2026-11-24/b204.diff`.
