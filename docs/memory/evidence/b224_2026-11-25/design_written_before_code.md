# B224 — design, written and hashed before any code (queue BU)

Read line 2026-11-25T07:24:11Z; limit 08:04:11Z. Predecessor (HEAD `c7750afc`):
`tools/party_steps.py` 58ca125956fe92f97e9c5dbe6d7f8feba97a5029749cd87df5734da874881bb5.

## The rule

The score path's template stream (stream 0, `synthetic_glyphs`, called only by `score_gates`) keeps a synthetic glyph
only when it is valid as a test variant is (B214 / B221):
1. it is cut as exactly one glyph;
2. at least `SYN_OWN` of the cut's ink is pasted ink;
3. its cut box is within `VARIANT_SIZE_TOL` px of the pasted glyph's width and height.

## The same code

- A new function `paste_cut(a, g, ink, pix, bg, dx, dy, place, region, size_tol)` holds one draw: the paste, then the
  three conditions in `test_variants`' order. It returns `(cell, None)` for a valid draw, else `(None, why)`.
  `why` is one of "outside the picture", "not one glyph", "not its own size", "not its own ink".
- `test_variants` calls it. Its stream, its draws and its cells are unchanged: the same rng calls in the same order,
  the same checks.
- `synthetic_glyphs` calls it with `size_tol=VARIANT_SIZE_TOL`. A draw that is not valid is thrown away and the next
  one drawn from the same stream, until `per` (`SYN_PER_GLYPH`) are valid or `VARIANT_DRAWS` draws are spent. Fewer
  valid: those that were made, recorded, never an error.
- **A title with no draw thrown away runs the same rng calls in the same order and keeps the same cells, so its
  templates, and so its spec, are byte for byte today's.** Today's `None` cells (outside the picture, or not one
  glyph) are draws thrown away now, so those titles change.

## What train's page records

`synthetic` in `recorded`. "made" stays. "not cut" becomes "thrown away" (the total). New: "by symbol" → {symbol:
{made, thrown away, draws, why: {reason: n}, glyphs short of 8}}.

## Not changed

- The test variants' stream (stream 1), the once rule, gate 1, the margins, `BARS`, every bar and gate.
- The letters path: `letters_gates` / `train_letters` call neither function.
- `party_add_game.py`.

## Tests (tests/b224_template_validity, new, three runs)

1. On B221's made-up 4 with its line: the template stream throws away joined, wider cuts and redraws them. Each kept
   template's cut is the glyph's own size; a draw with the joined cut is never a template.
2. On a background where every draw joins: fewer than `SYN_PER_GLYPH` made (0), recorded with the reason, no
   exception.
3. With no line: the templates are byte for byte today's (HEAD's `synthetic_glyphs`, loaded from git, on the same seed).
4. A made-up score title (b208's FULL), surveyed, labelled, planned: `score_gates`' fit (keys, thresholds, margin_needed,
   refs) is byte for byte HEAD's when nothing was thrown away. If the made-up title does throw some away, the test
   says so, not passes.
5. A made-up letters title: train's spec on my code is byte for byte HEAD's.
6. Train's recorded "synthetic" carries made / thrown away by symbol.

Mutation: the size condition removed from the template stream (`size_tol=VARIANT_SIZE_TOL` in `synthetic_glyphs`'s
call → `size_tol=10 ** 6`). It must be caught by test 1.
