# B178 — addendum after code (three changes to the hashed design, each found on T90's real pictures)

1. **The glyph distance.** The hashed design measured a glyph against a digit's template by the mean |difference| over
   the whole cell. Once glyph parts were joined 8-connected (2, below), the reader learnt without end_P2_2 read its "29"
   as "28": the unseen 9 fell inside 8's threshold. The label stage's own check 4 caught it as a disagreement and would
   have named a right label. That is the guessed digit the queue forbids. **As built:** the distance is **the largest
   3 × 3 local mean of |difference|** (the least over ±1 px shifts). A stroke one glyph has and the other lacks counts
   in full, where a whole-cell mean dilutes it. On T90's own glyphs:
   - the whole-cell mean: same digit ≤ 0.055, two digits ≥ 0.070 (8 / 9), ratio 1.27;
   - the local measure: same digit ≤ 0.342, two digits ≥ 0.696, ratio 2.04.
2. **Glyph parts 8-connected**, not 4: a pixel font's diagonal strokes touch only at corners (the made-up titles' font,
   and many SNES / N64 fonts); 4-connected, such a digit falls apart and is never read.
3. **A digit's threshold floor.** A digit only one save shows has an own spread of 0 (its pictures are the same
   picture), and its threshold would sit at half the nearest other digit. **As built:** each digit's own spread is at
   least **the title's own variation**: the largest own spread among digits two saves or more show. The threshold is
   then halfway from that to the nearest other digit (`_gap`, MIN_GAP, unchanged). It is learnt from the saves, never
   typed.

**The bar, as a consequence:** with the local measure T90's digit `margin_needed` is 0.2794, so the score kind's
`digit margin_needed` cell is held to **`margin_needed_min` (0.0796), today's bar**, not the "> 0" of the hashed design
(section 5). Nothing is lowered.

**T90 with these changes:**
- label PASS;
- learn FAIL on three left-out cells only;
- every digit only one save shows is left unread when that save is left out (1; 3, 8; 9), never read as another.
