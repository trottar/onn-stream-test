# B181-B184 — design, written before any code (queue BH)

The `score` kind only, plus B182's give-up (party layer, both bench flags) and B184's template line and anchor.
Nothing per game in code; no bar in `BARS` lowered; `winner` / `places`, T88's and T89's rules unchanged.

## 0. Settled from T90's four end saves

The pictures session A's learn made, copied read only to a scratch off the repo. The picture source was not run.

- **One font at one size.**
  - The line score's quarter / overtime cells and the FINAL column are both 16 px tall (640 × 480), 8-9 px wide, on
    the same row as that side's final.
  - The same digit, a quarter against the FINAL, is at most 0.418 apart (B178's local measure). Two different digits
    are at least 0.685 apart over every labelled glyph.
- **The columns sit at fixed places.** Q1-Q4 at the same x in every save; OT1 only in the overtime save (blank in the
  others); OT2 blank in all four.
- **Digits across the whole line score** (my readings; glyphs, saves showing it):
  - 0 (14, 4), 2 (12, 4), 9 (7, 3), 5 (2, 2);
  - 7 (9, but 1 save), 1 (1, 1), 3 (1, 1), 8 (1, 1);
  - **4 and 6 never.**
- **Prediction:** T90 cannot pass on its six saves under the every-digit rule. Its line will ask for a match showing 1,
  3, 4, 6, 7 or 8.

## B181 — every digit, from the line score

- **The readings.** Each side's value is either the final alone (`15`, as B178) or the line score:
  `9+2+2+2+_+_=15` (the cells left to right, `_` a blank cell, then `=` the final). Sides are joined by `-`, P1 first;
  two readings per save, from `.1` and `.2`, as B178:
  `end_P1=9+2+2+2+_+_=15-0+0+2+0+_+_=2,9+2+2+2+_+_=15-0+0+2+0+_+_=2`. **The FINAL is still the result** (the role
  check, the sidecar, the hub). A title whose screen has only the final keeps B178's form. All saves of a title give
  the same number of cells per side, or none.
- **The checks:** B178's four, now over every number (the two readings the same in every cell; the role; the places
  found; read back by a reader learnt without that save, every number), plus **the sum**: a side's non-blank cells add
  up to its final, else that save is named ("P<k>'s cells add up to <s>, not its final <f>").
- **The learner (spec version 4, the `score` block grows `columns`):** the label class carries the cells
  (`end_s9+2+2+2+_+_=15-…`).
  - **The finals' places as B178.**
  - **Each column's place, per side, left to right, on its final's line:**
    - candidates are clusters (anchor within 4 px) of strings on that line, left of the final, of the final's
      polarity and ink radius;
    - valid when, in every save, the cluster has a string with the labelled number of digits where the cell is
      labelled, and none where it is blank;
    - **refused when two of its glyphs labelled with different digits are nearer than the finals' digit
      `margin_needed`** (a column separator: the same glyph whatever the label);
    - then the most glyphs the finals' own reader reads as labelled; then nearest the place the other columns' spacing
      predicts; then the leftmost after the previous column.
    - A column blank in every save has no place. A labelled column with no valid place → not found, the saves where
      the place that holds in the most saves breaks named.
  - **The templates** from every glyph of every labelled number, thresholds and margin as B178.
  - **The hub reads the finals only.** The columns are read at learn and label for the checks.
- **learn's cells:** B178's, with **left out: <role> over every number** (the finals ended as labelled within 2.0 s,
  and every labelled cell read exactly at its column by the spec learnt without that save). A new cell, **"every digit
  0-9 read by a reader learnt without each save that shows it"**: each digit shown by at least two saves (then the
  left-out cells read it). Missing digits are named.
- **The line:** "One more save: a match either player won whose line score or final score shows <digits> (a quarter or
  a final with a <d>, …)" — the roles for each winner as B178. The cap as today.
- **A title with only the final:** the same rule over its finals. Each save shows 2-4 digits (two sides, 1-2 digits
  each), and every digit must be shown by two saves: 20 digit-sightings at the very least, so **5 end saves at the
  very best**. A title whose finals never reach some digit (scores that stay under 4, say) **can never pass**. At four
  saves per player (8 end saves) the cap's line says the final score cannot be learnt this way.

## B182 — an unread final screen given up at once (`PRIVYHUB_H7=1`; the party layer needs both flags)

- **The reader:** a version-4 read whose screen is the final screen but whose number is not read gives
  `{"class": "unknown", "end_unread": true}`.
- **The watch** (`h7_minigame._run`) counts such reads in a row. At K (the spec's own K) it sets the watch's state to
  `unreadable`, writes one row `final_unreadable` (no number), and stops reading.
- **The party layer:** a watch `unreadable` → `given_up`, why "the final screen was seen and a number on it was not
  read" — the board's own given-up path, no scores, no winner. The `minigame_given_up` row carries that why only.
- Versions 2 / 3 never give `end_unread` → today. The flags absent → today.

## B183 — the last look

- **Before label's PASS** (every other check met), the stage writes `label/digits.png`: one row per digit read, every
  glyph of every labelled number in it (its crop from the picture, ×2), numbered 1… under each. `label.json` keeps
  which save each tile came from.
- **The session answers:** `look=all` (every tile in every row is that row's digit), or `look=<d>:<tiles>` naming the
  tiles that are not (e.g. `look=9:1.2.5`).
- **A cell, "the last look: every glyph is the digit it was read as".** Met only by a `look=all` given for these exact
  readings; a reading changed → the look again. Named tiles → their saves named to read again ("<role> (a glyph read as
  <d> is not one, at the last look)").
- **The systematic misread of BG's table** (every 4 read as 9) puts 4-shapes in the 9 row. The session sees it and
  names the tiles → caught.

## B184 — the template and the anchor

- **`ADD_GAME_PROMPT_TEMPLATE.txt`:** "You never judge a picture" becomes "You never judge a picture — except the
  label stage's readings and its last look, each checked by the tool". The sha256 before and after recorded.
- **learn's anchor for a final screen** (end saves): **the first picture held still 3 s after the load** — the first
  picture from which every picture over the next 3.0 s is near it (B140's measure) and the run reaches 3.0 s past it.
  None → B167's anchor (the frame most of the run stays near), as today.
  - Begin / other: today's.
  - The same anchor in B176's same-picture check and the label stage's two pictures.
- **T88's and T89's numbers unchanged:** their kept specs are never learnt again here. Their kept saves' runs read the
  same by `learn --check` (read only).

## Proof

- **Made-up titles:** a line score that sums; a misread breaking a sum; a title with only finals; all ten digits
  needed (FAIL naming them, then PASS); a column separator refused; the last look catching the systematic misread;
  B182 in B114's harness (an unseen digit, the screen moving on after it); the anchor (a final screen held 4 s inside
  a longer later screen).
- **T90:** I label every line-score number through the label stage, look at the digit sheet myself, and report label
  and learn as they fall.
- **Mutations:** the sum check skipped; a pass with a digit unlearnt; the give-up waiting; the look skipped.
- B178's and the earlier add-game suites green.
