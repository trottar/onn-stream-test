# B185-B187 — design, written before any code (queue BI)

The `score` kind's label and learn stages only (`tools/party_add_game.py`, `tools/h7_endscreen.py`). Nothing per game
in code; no bar in `BARS` lowered; `winner` / `places`, T88's and T89's rules unchanged; the hub's reader unchanged
(it reads the finals only, B181). The sum check, the two readings and the last look stay as they are.

## 0. Settled from T90's five end saves (`t90_spread.txt`, `scripts/t90_spread.py`)

The label stage's first picture of each save (the hub's capture, 640 x 480, a glyph 16 px tall), my readings, B178's
local measure:

- **Every digit two saves show, within one save against across saves:** within at most 0.418 (mean 0.299, 48 pairs),
  across at most 0.401 (mean 0.260, 182 pairs). Across is **0.017 below** within at the most, 0.040 below on the mean.
  Per digit: 0 within 0.336 / across 0.374; 2 within 0.418 / across 0.357; 9 within 0.366 / across 0.401 (1, 3, 5, 8
  have one glyph per save: across only, 0.251-0.335).
- **Two pictures of one save:** the same glyph exactly the same (0.000, 59 glyphs) — the capture is the emulator's
  own output.
- **Two different digits:** at least 0.656 apart.
- **The digits only one save shows:** 7 (end_P1_2, 9 glyphs, within at most 0.343), 6 (end_P2_3, 3 glyphs, 0.333),
  4 (end_P2_3, 2 glyphs, 0.259). Each glyph against the mean of its save's other glyphs of that digit: 0.228-0.327;
  against the nearest other digit's template: 0.664-0.811.

**So the numbers support B186:** a fixed font, drawn the same in every match (across no larger than within). The
margin, from these numbers: **ACROSS_MARGIN = 0.05** — a title's across-save spread may be at most its within-save
spread + 0.05. T90 sits 0.067 inside it; 0.05 is under half of T90's room between the same digit (at most 0.418) and
two digits (at least 0.656), 0.119, so a title within it still has a one-save digit's glyphs nearer their own template
than any other digit's.

## B185 — a column only one save fills (overtime)

- **The learner** (`_find_columns`, unchanged in rule): a column's place is learnt from every save that fills it; one
  save is enough (its cell's string on the final's line, between its neighbours); a column blank in every save has no
  place. Every save still gives every side the same number of cells (`_` for a blank) — the form, not which cells are
  filled.
- **The left-out reading** (`_read_all`): a column with no place in the reader learnt without the save — no other save
  fills it — reads `*` ("no other save fills this column"), never `_`. **`_judge(want, got, only)`** replaces
  `_compare`: a `*` cell labelled blank is the same; a `*` cell labelled with a number is **"shown only here"**
  (`P<k> column <c>`), never a misread. A `?` glyph whose labelled digit no other save shows is "shown only here" as
  today. Anything else read otherwise is contradicted, as today.
- **label's read-back cell:** met when every number reads back, but for cells and digits shown only here; those are
  recorded under "shown only here" (`{"end_P1_2": {"digits": ["7"], "columns": ["P1 column 5", "P2 column 5"]}}`),
  never named to read again, never sent to the user.
- **learn's left-out cell:** a column shown only here does not fail it (recorded); digits as B186.
- **A save whose rows add up to its finals is never refused for which columns it fills.**
- **The hub:** unchanged — it reads the finals only (B181). An overtime match's final screen has its FINAL column at
  the same place; the hub reads its finals as any other's (learn's "<role>: ended as itself" cell for the overtime
  save).

## B186 — a digit only one save shows

- **A digit counts as learnt** (learn's every-digit cell) when **either** two saves show it (today) **or**:
  1. one save shows it at least twice (glyphs, over its whole line score); and
  2. **each of those glyphs is read back as it** by a template learnt without that glyph — from the other saves'
     glyphs (every digit) and that save's own other glyphs of that digit only, never the glyph under test (by its
     place, in every picture of the save); thresholds and margin by B178's own rule (`_digit_stats`); and
  3. **the title's across-save spread is within the bar:** over every digit two saves show, on each save's first
     labelled picture, the largest distance between two glyphs of one digit from two saves is at most the largest
     within one save + ACROSS_MARGIN (0.05). No digit shown twice within one save and by two saves → not measured →
     not met (today's rule then).
- **learn's left-out cell for a save** reads every number with the reader learnt without it; a glyph it does not read
  whose digit only this save shows (and which 1-3 hold) is read with the save's own other glyphs of that digit (2.),
  never with the glyph under test. When the save's final holds such a digit, the reader learnt without it cannot end
  on it: its finals and cells are then read at their places on the save's first labelled picture, and the time to end
  is the full reader's own "<role>: ended within" cell (recorded).
- **The cell's read:** `{"shown by fewer than two saves": [...], "learnt from one save": {"7": "9 glyphs, each read
  back", ...}, "across-save spread": [across, within, bar]}`; met when no digit is short.
- **What still gets through:** a digit only one save shows, labelled as another digit that also only it shows, in
  every glyph, in cells whose sums still add up and finals the other saves' reader cannot check — the last look is
  then the only guard (the session sees the row's glyphs side by side). A one-save digit drawn differently in other
  matches (a colour, a highlight) is caught only through the across-save spread of the title's other digits.
- **The hub's reader** is learnt from every save as today, so it holds that digit's template.

## B187 — the ask to the user

- **Counted per save, per reason** (`named_for`, each count up only when the session gave that save's reading again):
  `readings` (its two readings differ), `sum` (a side's cells do not add up to its final), `read back` (a reader learnt
  without it reads a number as another), `look`.
- **The user is asked only when** `readings` or `sum` reaches 2 for the same save. **Never** for a missing sample —
  a column or digit no other save shows is never named (B185, B186). A `read back` named twice is not asked of the
  user: its line says the save's reading and the other saves' reader still differ at those cells, and to take that
  line back to the chat (Cowork). No save is asked to be replaced.
- **The ask, at run time** (printed; the verdict's recorded line has the final left out): "Ask the user about the
  match P1 won 35-28 in overtime, saved at 6:31 pm to slot 2: P1's row — each quarter, overtime and the final —
  (and/or P2's) as its final stats screen shows them. YOU, now: ask Cowork to show you the picture of that match; then
  reply with its scores." — then the session's command `label <code> <role>=<the whole line score with the user's
  numbers>,user`.
  - **The match:** the player who won, its final as the session read it (`35-28`, or `35-28 (or 35-23)` when the two
    readings differ), "in overtime" when it fills a column some other save leaves blank, and when and where it was
    saved: register `--collect` keeps each role's slot and the slot file's time in the binding (off the repo); a save
    kept earlier gives "kept at <the kept copy's time>". The hub's clock, 12-hour.
  - **The cells in doubt:** the readings' differing cells, or the side whose sum fails — named by column (Q1-Q4, OT1,
    OT2 for six cells; "cell <c>" otherwise) and the final.
  - **The user's answer in the line score's own form:** on a title whose saves carry cells, a `,user` answer without
    the cells is refused (Usage: "the user's answer is the line score's own form …").
- **The picture:** the ask copies the one picture in doubt (`label/<role>.1.png`) to `logs/add_game_ask/<code>_<role>.png`
  in this repo (git-ignored: `logs/`); only that one. **`close` removes `logs/add_game_ask/<code>_*.png`.**

## B188 — the task's words

`handoffs/ADD_GAME_TASK.md`: after learn's every-digit line, how many digits are still short and that learn may ask
once more after this match — never that one match is enough; the ask line as B187; the overtime rule as B185. The
template unchanged (sha256 before and after).

## Tests (made-up titles, `tests/b185_overtime/`), mutations

- `Overtime`: one save fills OT1 → label PASS, its cell "shown only here"; learn's left-out not failed by it; two
  overtime saves → the column learnt (a place in the spec); a filled OT cell breaking the sum still caught.
- `OneSave`: a digit one save shows three times → learnt (learn PASS); shown once → short; the across-save bar met.
- `Ask`: two readings differing twice → the ask with the match, the cells, the picture in `logs/add_game_ask/`;
  a final alone refused; a read-back contradiction twice → never the user; close removes the picture.
- Mutations: a one-save column refused; a digit shown once counted; the user asked for a missing sample (a shown-only
  -here save named); the user asked for a read-back contradiction; a final alone taken.
