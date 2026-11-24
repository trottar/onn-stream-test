# B205 — design, written before any code (queue BO; a 60-minute limit from 17:10:03Z)

**Why:** after BN, T92's reader learnt without end_P2 reads its big 3 right but only after 14.0 s (bar 2.0 s). Its only
other 3 is a small glyph (end_P1's stats "13") on the stats table's plain box, while the big 3 sits on the moving
stadium. The template has never seen a 3 over that background or at that size.

## B205 — synthetic training for the score kind (B192's way, for digits)

In `h7_endscreen.learn_scores`, after the places, the columns and the size decision (B204), with the real labelled
glyphs gathered:

1. **The real glyphs to paste:** every labelled glyph on each save's first labelled picture, at its place — its crop
   (the place's rows, the glyph's columns, 2 px around) and its ink (the place's own polarity and radius), keyed by
   its group and drawn digit.
2. **The sizes the title draws:** the heights of the places in that group (T92's finals group: 57 px finals and the
   15-17 px cells and stats it counts).
3. **One synthetic glyph:** a real glyph of that key, its crop and ink scaled to one of those heights, its ink pixels
   pasted over a patch of the same size cut from one of the title's own end pictures at a random place, moved by up
   to 1 px; then `glyph_cell` as for a real glyph.
4. **Fixed seed** from the saves (`letters_seed`'s way: the pictures and the labels). **Held out first:**
   `SYN_DIGIT_HELD` = 6 per key. **Then rounds:** `SYN_DIGIT_PER_ROUND` = 12 per key, at most `SYN_DIGIT_ROUNDS` = 4,
   until every held-out one is read as its digit by B178's rule (nearest template of its group, within its threshold,
   the margin needed).
5. **Training only.**
   - The templates are the mean of the real glyphs and the synthetic ones.
   - Every gate is measured on the real glyphs alone: each digit's own spread and foreign distance, its threshold,
     separable, the margin needed, the glyph counts, `saves_showing`. The real glyphs are measured against those
     templates.
   - A synthetic glyph never counts toward a cell. No digit is made that no real labelled glyph shows.
   - The read-back, the left-out saves, the replays and the every-digit cell read real pictures only, as before.
6. **The record:** `score.trained` holds the held-out count, the trained count, the rounds, the held-out read, the
   seconds and the seed.

`_digit_stats(cells, shown, train=None)`: the templates from cells + train, every measure from cells alone.

## Tests (fast) and the mutation

`tests/b205_synthetic_digits/`:
- `_digit_stats` with training cells: the templates move, but every gate equals the real glyphs measured against those
  templates (a far synthetic outlier never widens a digit's own spread);
- `synthetic_digits` is deterministic for one seed, makes glyphs of the asked heights' keys only, and never makes a
  digit no real glyph shows.

**Mutation:** the synthetic glyphs counted in the gates (merged into the cells before the measures) — caught.

## Then

`learn T92` on its six kept saves as BN left them (no register, no label: the kept saves and slots untouched). Every
cell as it falls; `left out: end_P2`'s seconds against 2.0.
