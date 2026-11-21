# B191 / B192 — addendum, written after code (what changed from the hashed design, and why)

The design (`design_written_before_code.md`, sha256 47b982e3…, 16:30:33Z) stands but for these, each found by the
made-up title's tests or by T91's leave-one-out runs; none lowers a bar, none touches `winner` / `places` / `score`.

1. **The cut no longer drops "the end screens' fixed pixels".** A pixel the same in every end save is not only fixed
   text: where two saves' different letters overlap in one colour (a W's stroke over a not-yet mark) it is a letter's
   pixel, and dropping it cut letters in two. Instead a **found string is fixed text when its cut pixels stay the same
   (>= 90 %) in a save the session read other letters for that player in** — letters change with the reading; the
   `PLAYER 1` header does not (T91 without end_P1_2: the header, merged into three wide glyphs, had tied the letters).
2. **Glyphs when reading a corner**: parts overlapping in x are one glyph (as designed); **when that is not the word's
   length, parts touching in x (a gap <= 1 px) are joined too**, taken only if that gives the word's length. A thin
   join can be lost to the colour cut; a font's letters stand further apart (T91: 3 px and more). The corner search
   keeps the overlap rule only (there the cut's shadows would join letters).
3. **Training glyphs**: a synthetic glyph teaches a letter's shape only when at least 85 % of it is the pasted letter
   (a background speck joined to it teaches nothing), and only when a reader learnt from the real saves alone already
   reads it as that letter by distance. One corrupted paste had made T91's W "not separable" without end_P1. The
   held-out pictures still judge every glyph.
4. **The moving-screen gate** reads each end save's corners as they are with **the rest of the picture taken in turn
   from the title's other saves** (all real pixels), not its own scene panned 32 px: a pan of a plain screen changes
   nothing, so it was not a moving screen. **The reader's moving test is in colour** (the largest channel, B140's 16
   levels / 20 % of 64 × 48 cells): two scenes of one grey level are still two scenes.
5. **The reader reads the letters first**: a picture where a player's letters spell the word is never the begin; with
   none spelled, the start test as designed. (The made-up begin's small mask matched one end background.)
6. The synthetic pictures are made from **one picture of each end save** (the label stage's second is the same
   picture: it doubled the time and added nothing); both pictures are read as real checks.
