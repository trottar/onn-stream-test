# B122 — design, written before code (hashed before the first edit to `tools/h7_endscreen.py`)

Baseline: HEAD `cb16e0c8` (H7-C1 committed with queue AR). The tool is not behind a flag (it is a tool; the hub
imports it only under `PRIVYHUB_H7=1`). **What reads as today:** every spec version 2 and every labels file whose end
classes are not place rows — T88's `end_P1` / `end_P2` — learn and read exactly as today (the same code path; a test
compares T88's spec and its reads before / after).

## What the pictures and a look at the data settled (scratch analysis, numbers only)

- T89's results screen carries the **Place row**: four digits in four columns under the 1P-4P markers (1st in yellow
  with a laurel), over a moving scene (characters, their floating pointers, confetti). At the tool's 160 × 120 a digit
  is ~5 × 8 values — too small; **places are read at the 320 × 240 step** (the same picture the alignment search
  moves), a digit ~10 × 15 values.
- **Per column alone the place cannot be learnt**: in one column a place mostly comes from one match, so "place" and
  "match" (its stage, its characters) are confounded; and two matches can share a stage. **What separates them is the
  row's own structure:** every results picture is a permutation, so at the right column positions every place appears
  in five matches at different columns over different backgrounds. Searched over a row of n equally spaced cells
  (spacing, origin, cell size), the per-pixel ratio of between-place to within-place variance of the matches' mean
  pictures (box-averaged over a cell) peaks sharply at **spacing 40 (of 320), origin (x 131-133, y 54-61)** — 33-57
  against ≤ 2.5 anywhere else — the same in every leave-one-match-out fold.
- With **one template per place pooled across all columns** (each column's cell at its own position, refined ±3 px),
  leave-one-match-out: **every place in four of the five held-out matches read right (no wrong place)**, including
  eight places their column never showed in training (1P 4th; 2P 2nd and 3rd; 3P 1st and 3rd; 4P 1st, 2nd and 3rd);
  in M2 (its results screen 5 s) **the 2P column is unread** — the 3P pointer stands on that "1" all five seconds —
  so the row is `unknown`, never a guess.

## The design (spec version 3; only for place rows)

- **When:** the labels' end classes are all place rows `end_r<d1..dn>` (n = 2-4 ports, the digits a permutation of
  1..n, one n). Else today's version-2 learner, unchanged.
- **The screen and its classes:** today's `learn_arrays` on `start`, **one end class `end`** (every `end_r…` merged)
  and `other` → the screen mask, its threshold, the start / end references, as today. The spec's classes
  `["start", "end"]`, end class `end`.
- **The row (learnt, no boxes):** on the end pictures' **ranks at 320 × 240 against the screen mask** (the mask
  upsampled ×2; B104's tone-independent measure), the matches' mean pictures (one per labelled order); for every
  spacing s (8 … 320 / (n−1)) and cell size (12 × 8, 16 × 12, 20 × 16, 24 × 20): the per-pixel Fisher ratio
  (between-place / within-place variance, each place's values from the columns that showed it), box-averaged → the
  best (spacing, origin, cell). The cell padded by 4; **the glyph mask** = the padded cell's pixels with a Fisher
  ratio > 1. Each column's cell refined ±3 px (two passes: templates, then each column's shift with the least distance
  to its labelled places' templates). **One reference per place** = the mean of every cell (any column) showing it.
- **A place never seen in a column** is read with the pooled reference learnt from the columns that showed it, at that
  column's own position, with a ±1-px search — **the alignment across columns is the row's learnt spacing and each
  column's refined offset**. A place never seen in **any** column cannot be read: learning refuses ("place q is never
  shown: the pictures need a match where someone is q-th").
- **Distances and thresholds:** a cell's distance to a place = the median |rank − reference| over the glyph mask, the
  least over ±1-px shifts. Per place: the threshold halfway between the worst own distance and the best foreign one in
  the training cells; the margin needed = half the smallest margin seen. A place is read only under its threshold and
  with the margin.
- **A read (version 3)** = `{"screen", "class": "end" | "start" | "other" | "unknown", "places": [p1..pn] | null,
  "distances" (the screen's and the classes'), "place_distances": [per column, per place], "margin",
  "place_margins"}`: the screen and its class as today; **for `end`, every column's place — any column unread, or two
  columns with the same place → `class` `unknown`, `places` null (never guessed)**. Version 2's read has no new key.
- **Ended:** K agreeing reads of **the whole row** (the same class and the same places) after the start was seen; for
  version 3 it says `end` with the places.
- **Score / replay:** a version-3 score per labelled order: rows read right / unknown / wrong, places right / unread /
  wrong per port, `other` read as the screen (must be 0), the read's time; `replay` with the places in each `ended`.
- **Spec on disk:** `version` 3, `places` {ports, spacing, cell, offsets, thresholds, margin_needed, frames, …}; the
  arrays file adds `place_mask`, `place_refs`. `load_spec` / `check_spec` take versions 2 and 3 (version 1 refused as
  today).

## The evidence (on the real pictures, numbers only) and the tests

Five folds (each match held out; learnt on the other four): per port places right / unread / wrong, rows unknown,
`other` read as the screen. Learnt from all five → the spec A will use (written outside git, to scratch only — the
rules folder is A's) and its score; one read's time; B104's tone changes on held-out pictures (offsets ±30, gains
0.8-1.2, gammas 0.8-1.25) → 0 readings changed; `replay` K = 3 and 2. T88: its spec learnt as H7-V3 did reads H7-V1's
and H7-V2's pictures exactly as before (the same numbers as B104's record). Tests on synthetic pictures: four
digit-like glyphs under four markers over a moving scene; places learnt from three permutations read a fourth never
seen whole; a place never seen in a column; a duplicated place → `unknown`; a half-drawn row → not `ended`; K; the
two-player tests (B102 / B104's suites) green.

**Five matches enough?** The answer goes in the record from the folds: if every never-seen-in-column case reads right
or unread (never wrong), they are enough for the sitting; the smallest further capture is the order that shows the two
missing pairs (1P 2nd, 3P 4th) directly — e.g. one match with places 2, 1, 4, 3.
