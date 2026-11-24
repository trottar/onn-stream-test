# B214-B218 — the once rule's variants, plan's whole ask, register on three saves (queue BQ; design before code)

Read line 2026-11-24T20:11:56Z; limit 21:26:56Z. Written before any code; sha256 in `design.sha256`. Nothing in
`BARS` changes.

## B214 — the once rule's variants (`tools/party_steps.py`, score kind)

- Two random streams from one seed (`seed_of(readings)`): `default_rng([seed, 0])` makes the **templates'**
  synthetic glyphs (as BP: 8 per real glyph, B205's weighting); `default_rng([seed, 1])` makes the **test
  variants**. A test variant is never in the templates (different draws, never pooled).
- A test variant of a once-seen glyph: BP's paste (the glyph's ink over another end save's erased region, shift
  dx ±3, dy ±1), then it is **valid only when** `place_glyphs` cuts exactly one glyph and at least `SYN_OWN` (0.85,
  `h7_endscreen.SYN_OWN`, B192's) of that glyph's cut ink (the place's ink, inside the cut box) is pasted ink. Not
  valid → thrown away, the next draw from the same stream; at most `VARIANT_DRAWS` = 24 draws a glyph; it stops at
  `VARIANTS_NEEDED` = 8 valid.
- Fewer than 8 valid after 24 draws → the symbol is not counted; its gate-2 cell reads "variants could not be made"
  (it is asked for, as today).
- The rule unchanged: rigidity ≥ `rigid_min`, all 8 valid variants read as itself, no other symbol's real glyph read
  as it.
- Letters (T91's kind): its variants are the glyph's own cell shifted (no paste, no cut), so each is the glyph that was
  pasted by construction; they are drawn from the test stream only and never in the templates (the letters
  templates are B192's own training). 8 needed as above.
- The gate-2 record carries, per once-seen symbol: draws, valid, and what the valid variants read as (counts).

## B215 — plan's last line is the whole ask

- The gates 1-3 of train move into one function per kind (`score_gates`, `letters_gates`) that writes nothing and
  returns the cells, the symbols counted, and **the ask** (never seen ∪ seen once and not counted). `plan` calls it
  after its list and its regions check; its last line is `ask_line(kind, ask)` — one sentence. `train` calls the
  same function and adds the spec, the screens and the replays; its last line is the same `ask_line`.
- plan records the gates' outcome (recorded, never a cell — plan's PASS stays: the page written, the regions hold).
- Test: on every made-up title in `tests/b208_survey` and the new tests, plan's last line = train's last line.

## B216 — register on the new path (`tools/party_add_game.py`)

- **New path** = a `score` or `letters` title whose binding has a survey, or that the old path has not learnt
  (no `learnt` in its binding) and is not `--rules-players`. There `kept states present` needs `begin`, `other` and
  one ending (`end_P<k>` for any k); later endings are any `end_P<k>[_n]`. The cell's bar reads "begin, other, one
  ending (the new path)".
- Old path (a binding learnt by `learn`, T90 / T91; `winner` / `places`; `--rules-players`): `_roles_needed` as today.
- Register keeps the binding's `survey` (and today drops nothing else differently): the old binding's `survey` is
  carried over when its kind is the registered result, so collecting a further ending does not lose the survey.
  (BP's register rebuilt the binding from its arguments: a later `--collect` would have dropped the survey — found
  reading the code for this queue.)
- Tests: three saves of a made-up score title PASS register (its cells); a binding learnt by the old path still needs
  two per ending; a survey kept across a second register.

## B217 — the old path's two suites

`tests/b181_every_digit/` and `tests/b185_overtime/`: their made-up pictures' noise exactly as before BP — their own
copies of the pre-BP noise: `line_capture.py`'s capture and B181's / B185's `put` restored to HEAD `ef8a0ce5`'s text
(the shared `Made.N` counter, B185's reset, one generator per run). B181 imports B178's `score_capture` — B178 stays
on the per-picture noise (a new-path harness for B208's tests); B181 and B185 use only `line_capture` and their own
`put`, so restoring those restores their pictures. The first line of each test file says: "frozen with T90's old score
path: its made-up noise is exactly the pre-BP fixture (queue BQ, B217)". Both run to their end.

## B218 — T90 and T92 once (scratch)

A new scratch copy of each (binding without `survey`, kept saves, pictures; register's verdict copied); `survey` with
BP's answers (T90 boxes 25 33; T92 boxes 10 12), `ok`, `label` with BP's readings, `look=all`, `plan`, `train` —
once each, every cell as it falls, plan's last line word for word. Nothing changed after. A refused symbol: what its
valid variants read as (from the record).

## Tests and mutations

`tests/b214_variants/` (new): a badly cut variant thrown away and redrawn, not counted against the symbol (a made-up
picture where some shifts merge the pasted glyph with a neighbour); fewer than 8 after 24 → not counted with the words;
misread valid variants → still refused; the test stream never in the templates; plan's ask = train's ask; register on
three saves; the old minimum for a learnt binding; the survey kept across register. Mutations: a test variant pooled
into the templates; counted with fewer than 8; the SYN_OWN check removed; plan's ask without gate 2; register's three
saves for a learnt binding.
