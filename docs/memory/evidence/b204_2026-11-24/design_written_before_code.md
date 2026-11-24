# B204 / B205 — design, written before any code (queue BN; a 90-minute limit from 00:39:51Z)

## Settled first (T92's kept pictures, read only; no picture source run)

Each end save's first picture; every glyph of the finals (F, 57 px), the 1ST period cells (C, 15 px) and the six stats
rows SHOOT..PK (S, 15-17 px), labelled by my reading as drawn; each glyph scaled to one height (`glyph_cell`), B186's
measure (`cell_dists`). Glyphs: F 0 ×10, 2 ×3, 3/4/5 ×1; C the same; S 0 ×93, 1 ×2, 3 ×1.

| pair | min | max |
| --- | --- | --- |
| one digit, one size (F / C / S) | 0.003 | 0.492 |
| one digit, C and S | 0.040 | 0.500 |
| **one digit, C or S and F** | 0.415 | **0.652** |
| two digits, one size | 0.830 | 0.986 |
| **two digits, any two sizes** | **0.834** | 0.993 |

**C and S are one font (the small one); scaled to the finals' height they are the finals' digits:** every same-digit
pair across sizes (≤ 0.652) is below every two-digit pair (≥ 0.830) — a gap of 0.178. They are not the same pixels
(0.652 > the finals' own 0.309), so they count as samples of their digit, not as copies.

## B204 — every number on the final screen; another size counted when the numbers say so

1. **The reading names every number** (party_add_game): a side is `[<period cells>=]<final>[:<stat>.<stat>…]`
   (`_` a blank), e.g. `02+_+_+_+_=02:13.00.00.00.01.00`. Only the final is the result; the period cells add up to
   it (the sum check, as today); the stats have no sum. For the learner every stat is one more column of its side
   (found like an off-line period cell, B200), so the read-back, the last look and the every-digit count cover it.
   A reading without `:` is today's text.
2. **Another size counted** (h7_endscreen `learn_scores`): when the finals share one group and some off-line columns
   are another size, the title's own numbers decide: their glyphs join the finals' group only when every pair of one
   digit across the two sizes is nearer than every pair of two digits (any sizes) — on the glyphs both sizes show.
   Else their own group, as B200 (teaching no final's digit). The decision and its two numbers are in the spec
   (`score.sizes`). T92: 0.652 < 0.830 → counted. A title whose small font is another face stays apart.
3. **What guards a misread stat** (no sum): the two readings the same; the read-back by a reader learnt without that
   save (every stat a column it reads); the last look (every stat glyph on label/digits.png). A stat misread as a digit
   the other saves do not show is caught only by the last look — as a one-save period cell today.
4. The label line names the stats: "… then ':' and each stats row's number, top to bottom, joined by '.'".

## B205 — synthetic training for the score kind (only if the limit leaves time)

B192's way for digits: every labelled real glyph pasted into new numbers (random digits 0..N) over patches of the
title's own end pictures, fixed seed from the saves, held-out synthetic pictures made first and read before training
stops; training only — the templates, never a cell. If not built inside the limit, said so.

## Tests (fast; three runs) and mutations

`tests/b204_every_number/`: the reading with stats parsed and written back; the sum over period cells only; a stat
counted as a column; the size decision on made-up glyph cells (one font at two sizes → counted; two faces → apart).
Mutations: the stats added into the sum; the size decision forced apart; the size decision forced together.
