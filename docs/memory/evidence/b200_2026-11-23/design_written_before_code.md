# B200 / B201 / B202 — design, written before any code (queue BM)

## Settled first (T92's kept pictures, read only; no title started for it)

The run's own pictures are still in the title's add_game folder (off the repo): `pictures/<role>/` (the picture source's
run of each kept save, made at the first run) and `label/<role>.1.png`, `.2.png`. Read only; probes ran on a copy in my
scratch, off the repo. No picture source was needed for this.

- **Where things sit (the score picture, 640 x 480):** each side's final is a big number either side of a small box
  (P1's at x 185-260, P2's at x 408-485, rows 82-139, 57 px tall); the box holds a cell per period for each side, one
  row per period (1ST, 2ND, 1EX, 2EX, PK), P1's cells at x 290-313, P2's at x 362-384, the 1ST row at rows 80-95 (15 px
  tall) — **above the finals' line and a quarter of their height, not on it**. Under the box, a stats table (shots,
  offside, fouls, FK, CK, PK, keep %) per side.
- **Every number is drawn with two digits, a leading 0:** the finals (02, 00, 05, 04, 03), the 1ST cells (the same as
  the finals: the users stop at half), the stats table (13, 00, 01); a blank period cell is "--".
- **The same shape in every save:** the box's frame, the period headings (1ST, 2ND, 1EX, 2EX, PK — the "1" and "2"
  there are digit-like), the "--" blanks (too flat to be a glyph: under SCORE_HMIN), the stats headings, the buttons
  under the table, and **the hollow inside each final's leading 0** (every final's first glyph is a 0).
- **Why P2's first cell could not be placed (reproduced on the copy):** told single numbers (2, 0, 5 …), the finder
  looked for one glyph at one place in every save. The one-glyph shape there in every save was **the dark hollow inside
  each final's leading 0** (`pol -1`, 16 px wide): it took the hollow inside P2's leading 0 for P1's final and the one
  inside P1's for P2's. B181 then looked for each side's cells on that line: P1's "cell 1" became the other hollow;
  P2's cell — two glyphs in the box above that line — had no one-glyph place on it in three saves.
- **The finals' background moves:** in 6-8 of each save's ~20 pictures one final's glyph merges into the stadium
  behind it (1-3 s at a time); the cells in the box read in every picture. The first 3 s of every save read both
  finals whole, so the hub's 3 agreeing reads end before it (recorded, not changed).
- **Measured, the same-shape margin (`cell_dists`, each save's first labelled picture):**
  | place | glyphs labelled alike, farthest | glyphs labelled differently, nearest |
  | --- | --- | --- |
  | T92's finals, read as drawn | 0.327 | 0.925 |
  | T92's 1ST cells, read as drawn | 0.492 | 0.830 |
  | T90's finals (its kept places) | 0.342 | 0.719 |
  | the hollows of T92's leading 0s, single numbers | 0.134 | **0.034** |

## B200 — numbers as drawn; a place whose shapes the labels do not explain never taken

**1. A number as drawn (`h7_endscreen.Drawn`, an `int` whose `str` is its glyphs).**
- `Drawn("03")`: value 3 for every check (the role's player ahead, the cells adding up, `--max-score`, the hub's
  result); `str()` "03": its glyphs, "0" and "3", for every glyph count and every glyph's label. JSON writes the value.
- `score_numbers` / `score_cells` return `Drawn`; the learner's saves carry them, so a place holds as many glyphs as the
  number is drawn with and each glyph is labelled by its drawn digit (the leading 0 is a learnt 0).
- `party_add_game`: `_sides` returns `Drawn`; `_text` keeps each number as given (today: `str(int(x))`, which dropped a
  leading 0); `_digits_of` counts every drawn digit (a leading 0 shows a 0); `_mend` / `_fill` build `Drawn`. A reading
  without leading zeros is byte for byte today's canonical text, so T90's and T91's inputs and verdicts stay as they
  are. A title that pads and one that does not both work: the reading is what the screen shows.
- The label stage's reading line adds: "each number as drawn, leading zeros included (a drawn 03 is 03, not 3)"; its
  "Read again" line adds the same when the reason is a place.
- The hub: `read_scores` already reads a place's glyphs and takes `int` of them ("03" → 3). Unchanged.

**2. Same shape, never taken (BL item 1) — `h7_endscreen._shapes_explained`.** For a candidate place (a side's final
or a column) and the saves' labels: every glyph's cell at the place on each save's first labelled picture, labelled by
its drawn digit. **The place is refused when the nearest two glyphs labelled with different digits are no farther apart
than the farther of (the farthest two labelled alike, `SCORE_SAME_SHAPE` = 0.5).** 0.5: above every alike spread
measured on a real title (0.492), below every different-digit distance measured (0.719); the hollow's 0.034 is far
under it. Not a bar in `BARS` (none is lowered); the place cell still decides.
- Finals: each side's candidates (`_find_place`) are filtered by it before `_choose_places`; a side left with none is
  "not found", its saves named as today (label's place cell, "P<k>'s number does not fit …").
- Columns: B181's on-line search keeps its own separator check and adds this one; a valid on-line place is kept as
  today, so T90's columns stay as they are.

**3. Columns off the final's line (where T92's cells sit).** When B181 finds no valid place for a filled column on
the final's line, the column is looked for anywhere on the picture, as a final is: a string with as many glyphs as the
cell is drawn with, at one place in every save that fills it (`_find_place` over those saves), its shapes explained
(2), overlapping no final and no column already placed, and holding no number in a save whose cell is blank. Of
several, the one whose glyphs fit their labels best (`_agreement`'s mean distance), then `_find_place`'s own order.
- Its glyphs' templates: the final's group when its height is the final's within SCORE_TOL; else their own group
  ("c:" for every off-line column of one height, within SCORE_TOL; else "c<side>:"), as B178 keeps sides of another
  height apart.
- **A column in another group teaches no final's digit:** learn's every-digit cell (and B186's one-save rule) counts
  the digits of the finals and of the columns in a final's group only — the hub reads finals, and a digit learnt only
  in the small cells' font would not read a final. The other columns still check every reading (read back, the last
  look). For T92 the cells equal the finals, so the count is the same either way.

**Tests (made-up screens, `tests/b200_drawn_places/`):** a final screen like T92's (two-digit padded finals beside a
box of small padded period cells, a stats table of "00"s, headings, a hollow 0 in every final): read as drawn → the
places and the 1ST cells found, label and learn's place cells met; read as single numbers → the hollow refused (the
place cell not met, never the hollow taken); a panel shaped like a digit beside single-digit finals (B198's disclosed
case) → the panel never taken; a title that does not pad → as today. T90's and T91's label and learn re-run on copies
of their kept saves and readings (scratch, off the repo): every verdict and cell the same as committed. **Mutations:**
the same-shape rule skipped (the hollow taken); a drawn number read by its value (`str(int)`: the place not found);
the off-line search skipped (P2's cell not placed); off-line digits counted for the finals.

## B201 — `--find`

**Why:** the hub's library applies `q` only with `view=search`; the tool sent `system` and `q` with no view, so the hub
answered the system's whole list (72) and ignored the words. The tool's "exact" pick then matched only a name equal to
the library's whole name (region suffix and all).

**The design:** the tool asks for the system's list (`system=<s>`, paged with `offset` / `limit` until `total`) and
matches the user's words itself — case, punctuation and spacing ignored (`'` dropped, other punctuation a space):
1. the whole name equal → that title;
2. else the name without its bracketed parts ("(USA)", "[!]", "(Disc 1)") equal;
3. else every word the user gave found in the name.
The first rule with any match decides: one title → found; several → refused, "<n> titles match …", and when n <= 6
their names are printed **to stderr, for the chat only, marked never to be written** (the guard still checks every line
on stdout and in every file); none → "no title of the system matches those words". The words and every name are
added to the guard. Tests with a stub library (both orders of pages; region suffix; a part of a name; two regions →
candidates on stderr, nothing in the verdict files); the mutation (the words ignored: every title answered) caught.

## B202 — the user's saves asked only through register (ADD_GAME_TASK.md; the template unchanged)

- §1: **never ask the user to make a save before register has said it is missing.** Run `register` with round 1's
  collects first (slots 1-3 as the user keeps them: select screen, mid-match, the final after a P1 win); only a
  "missing" cell (or a refusal "slot <n> is empty") leads to a line to the user, naming exactly what is missing.
- §1: for `score` and `letters` titles, no "other teams / other characters" line (the user's rule: the reader looks at
  the numbers or letters only; B192's synthetic training gives `letters` its backgrounds). Their lines say "another
  match". The "same match saved twice" check stays for them — two saves of one match show the same glyphs once, not
  twice — and is told apart by the whole held screen (the numbers, the stats, the moving background differ from match
  to match), never by the teams. Its line to the user asks for another match, never other teams.
- §1: the highest score asked once; a later change by the user taken without argument: the next register run (no
  `--collect` needed) passes the new N; label (no new readings) and learn run again; the session says one line.
- The template unchanged (sha256 before = after).

## B203 — T92 from its six kept saves

`register T92 … --result score --max-score 5` (no `--collect`), `label T92` (its pictures: reused while the kept states
are unchanged — the picture source runs only if they are not), my own readings of the four end saves through the label
stage, as drawn, the last look, `learn T92` — every verdict as it falls. Scratch-free: the real stages, as session A
would run them; the title's add_game folder is the tool's own.
