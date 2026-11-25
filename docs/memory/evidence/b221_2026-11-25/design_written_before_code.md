# B221 / B222 — a valid test variant is the glyph's own size (queue BS; design before code)

Read line 2026-11-25T00:47:57Z; limit 01:17:57Z. Written before any code; sha256 in `design.sha256`.

## B221 (`tools/party_steps.py`, `test_variants` only)

- One more condition, after B214's two (one glyph cut; >= `SYN_OWN` of its ink pasted): the cut box's width and
  height are each within `VARIANT_SIZE_TOL` = 2 px of the pasted glyph's (its real glyph box `g`: `g[3]-g[1]+1`,
  `g[2]-g[0]+1`). Not → thrown away, the next drawn from the same stream (24 draws at most, 8 valid needed, else
  "variants could not be made"), exactly as B214.
- Nothing else changes: the templates' synthetic glyphs (`synthetic_glyphs`, stream 0), the once rule's gate,
  `BARS`, plan / train, register, letters.
- Reported, nothing changed (`template_sizes.py`, scratch, read only): the templates' synthetic glyphs of T92 and
  T90 that a size check would fail, by symbol — re-made exactly as `score_gates` makes them (stream 0, the same order),
  each cut's box against its real glyph's box.

## B222

Scratch: T92's real folder copied as it stands; T90 from BR's scratch (BQ's answers). plan then train, once each;
every cell; plan's last line; each once-seen symbol's draws, valid variants, what they read as. Nothing changed after.

## Tests

`tests/b221_variant_size/` (new): B214's made-up picture with a bar of the line's height beside the glyph but
touching it (a joined cut wider than the glyph, ink share >= 0.85) on some shifts → those draws thrown away, 8 valid
from the rest, each valid cut within 2 px of the glyph's size; the same background with the size check removed would
accept a wide cut (shown by the cut box recorded); a right-sized variant misread still refuses (`_once_rule`).
Mutation: the size condition removed — caught.
