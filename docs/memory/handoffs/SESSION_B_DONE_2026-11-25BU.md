# SESSION B — done, 2026-11-25 BU (QUEUE_2026-11-25BU: B224 the templates' synthetic glyphs valid as test variants are, B225 T92 and T90 once; read line 07:24:11Z, limit 08:04:11Z)

**Finished:** 07:36Z, inside the limit; nothing left undone.

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty (queue BU committed, `c7750afc`).

**Rules kept:**
- No title started. No stream, no restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive; nothing deleted. Earlier scratch runs were set aside by renaming them under `~/b208_scratch/bu/`.
- **T92's real folder and its rules only read:** the rules folder (27 files) and the real T92 folder have sha256
  before = after. Every run used a scratch copy. Your slots were not touched.
- Nothing in `BARS` or any gate changed.

## B224 — BUILT

- The score path's template stream keeps a synthetic glyph only when it is valid as a test variant is: one glyph,
  at least `SYN_OWN` of its cut ink pasted, and its cut box within 2 px of the pasted glyph's size.
- It is the same code (`paste_cut`), used by both streams. A draw that fails is redrawn from the same stream up to 24
  draws; fewer valid are recorded.
- A title with no draw thrown away is byte for byte as before. The letters spec is byte for byte as before (tested).
- Departure from the hashed design: the record's "not cut" key was kept (always 0 now), because `b214_variants` reads
  it. The record says so.

## B225 — scratch, once each

- **T92:** plan "Nothing more is needed."; train **PASS (23 cells)**. Only `margin_needed` differs from BS's run:
  0.2548, against 0.1968. 88 template draws were thrown away and redrawn, 192 made, no glyph short. 1, 4 and 6 are seen
  once, with the same rows as BS.
- **T90:** plan's and train's cells equal BS's, cell for cell (train FAIL, 22 cells, still 6, 7, 8). None of its
  template draws was thrown away.
- Session A does not retrain the real T92 unless Cowork says so.

## Tests

- New tests `tests/b224_template_validity/`: 7 tests, OK in all three runs.
- Mutation (the size condition removed from the template stream): caught.
- `b208_survey`, `b214_variants`, `b221_variant_size` and `b223_bench_numbers`: OK.
- Only `tools/party_steps.py` changed outside `tests/`, so the old path's suites were not run.
- The checks (redact, title, id, code): FAILS 0.

Record: `evidence/B224_TEMPLATE_VALIDITY_2026-11-25.md`. Patch: `patches/B224_TEMPLATE_VALIDITY.md`.

## The command list as it now stands (unchanged)

```
python3 tools/party_add_game.py register <code> --players 2 --system <ps1|n64|snes> --result <score|letters> [--word <WORD>] [--max-score <N>] --find "<the user's words>" --setup none --collect begin=1 --collect other=2 --collect end_P1=3
  PASS: register <code>: PASS (<n> cells)            [the new path: begin, other, one ending]
  asks: register: REFUSED — <n> titles match          [the whole name as the library lists it]

python3 tools/party_add_game.py survey <code>
  last line: survey <code>: look at survey/boxes.png (<n> numbered boxes, a grid every 40 px) — answer: survey <code> <kind> <P1: a box number or x0,y0,x1,y1> <P2: a box number or x0,y0,x1,y1>
python3 tools/party_add_game.py survey <code> score <P1 box|x0,y0,x1,y1> <P2 box|x0,y0,x1,y1>
python3 tools/party_add_game.py survey <code> letters <WORD> <P1 box|x0,y0,x1,y1> <P2 box|x0,y0,x1,y1>
  last line: survey <code>: look at survey/regions.png — answer survey <code> ok, or survey <code> again P<k>
python3 tools/party_add_game.py survey <code> ok
  PASS: survey <code>: PASS (5 cells)
  asks: survey <code>: mark P<k> again — survey <code> P<k> <a box number or x0,y0,x1,y1>

python3 tools/party_add_game.py label <code>
  last line: label <code>: read the regions on label pictures regions/<role>.1.png and .2.png — label <code> end_P1=<reading>,<reading>
python3 tools/party_add_game.py label <code> end_P1=<P1>-<P2>,<P1>-<P2>          [letters: end_P1=<P1>/<P2>,<P1>/<P2>]
  last line: label <code>: look at regions/look.png — label <code> look=all, or look=<symbol>:<i> for a glyph in the wrong row
python3 tools/party_add_game.py label <code> look=all
  PASS: label <code>: PASS (<n> cells)
  asks: label <code>: read again: <role>

python3 tools/party_add_game.py plan <code>
  PASS: Nothing more is needed.
  asks: Still needed: a final score with a <d> in it (either player).      [several: "… and a final score with a <e> in it (either player; one match may show more than one)."]
        [the whole ask — never seen, or seen once and not counted; the user's match saved to slot 2 or 3, then:
         register <code> … --collect end_P<the winner>_<n>=<slot>, label <code> end_P<the winner>_<n>=…, label <code> look=all, plan <code>]

python3 tools/party_add_game.py train <code>
  PASS: Nothing more is needed.            [after: train <code>: PASS (<n> cells)]
  asks: the same line as plan's

python3 tools/party_add_game.py bench <code>
  PASS: bench <code>: PASS (<n> cells)
python3 tools/party_add_game.py solo <code>
  last line: solo <code>: WAITING — after the user's reply: solo <code> --read --winner <seat>
python3 tools/party_add_game.py solo <code> --read --winner <seat|draw>
  PASS: solo <code>: PASS (<n> cells)
python3 tools/party_add_game.py close <code>
  PASS: close <code>: PASS (3 cells)
```
