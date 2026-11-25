# SESSION B — done, 2026-11-25 BS (QUEUE_2026-11-25BS: B221 a valid test variant is the glyph's own size, B222 T92 and T90 once; read line 00:47:57Z, limit 01:17:57Z)

**Finished:** 00:55Z, inside the limit; nothing left undone.

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; queue BR committed (`2d8a8345`).

**Rules kept:**
- No title started. No stream, no restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive; nothing deleted.
- **T92's real folder only read** (copied to scratch as it stands). Your slots not touched.
- **Nothing in `BARS` changed; the once rule's gate not changed. T88-T91's rules: sha256 before = after.**
- No title, id, team or character name or path in any record (four checks, plus the screen-words check kept off the
  repo). No picture in git.
- Nothing adopted; nothing committed.

## B221 — BUILT

- **A test variant is valid only when its cut box is within 2 px of the pasted glyph's width and height,** besides
  B214's two conditions. Otherwise it is thrown away and the next drawn (24 draws at most, 8 valid needed).
- **Test variants only;** the templates and everything else are unchanged.

**The templates' synthetic glyphs that would fail the same size rule** (reported, nothing changed):

| title | symbol: would fail / cut |
| --- | --- |
| T92 | 0: 33 / 112 · 1: 1 / 8 · 2: 9 / 24 · 3: 5 / 16 · 4: 1 / 8 · 5: 5 / 16 · 6: 4 / 8 — **58 of 192** |
| T90 | **0 of 136** (every symbol) |

## B222 — T92 and T90, plan then train, once each (scratch)

| | T92 | T90 |
| --- | --- | --- |
| plan's last line | **"Nothing more is needed."** | "Still needed: a final score with a 6 in it and a final score with a 7 in it and a final score with a 8 in it (either player; one match may show more than one)." |
| train | **PASS (23 cells)** | FAIL (22 cells); last line the same as plan's |
| once-seen | 1: 9 draws, 8 valid, 8 read as 1 · 4: 9 / 8 / 8 as 4 · **6: 13 / 8 / 8 as 6** — all seen once | 3, 4, 9: 8 / 8 / all as themselves · 8: 8 / 8 / 4 as 8, 4 "?" (margin; not this queue) |

Every cell is in the reply and in `evidence/b221_2026-11-25/b222/`. T92's spec went to the scratch rules folder only:
**the real T92 has no train PASS until session A runs train.**

## Tests

- **New tests:** `b221_variant_size`, 5 tests, three runs OK.
- **Mutation:** the size condition removed — caught.
- b208 9 OK, b214 10 OK, b210 9 OK, once.
- The diff touches only `tools/party_steps.py` and `tests/`, so the old path's suites were not run (the stat is in the
  log).

## What I would change (not done — the queue is the task)

1. **The templates have the same joined cuts.** On T92, 58 of 192 synthetic template glyphs are about 60 px wide for a
   35 px digit: the background keeps part of the other digit in a two-digit region. Applying the same size rule to the
   templates' glyphs would keep the templates to the glyph's own shape. It would change T92's templates and thresholds,
   so a queue should state it, and T92 be run again after.
2. **Erase the region more thoroughly before pasting** (the whole region, not only the ink the radius sees). That would
   stop the joins at their source for both streams.
3. **T90's 8** (margin) and **the seed** stay open, as BR reported.

**Checks:** redaction, titles, ids, T90-T92's names: FAILS 0 each; screen words (kept off the repo): FAILS 0;
`b221.diff` applies on `2d8a8345`; T88-T91's rules sha256 before = after.

## Files

- **Code:** `tools/party_steps.py`.
- **Tests:** `tests/b221_variant_size/` (new).
- **Record:** `evidence/B221_VARIANT_SIZE_2026-11-25.md` + `b221_2026-11-25/`.
- **Patch:** `patches/B221_VARIANT_SIZE.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line).
- **Logs:** `logs/b221_git_status.txt`, `handoffs/SESSION_B_STATUS.txt`, this file.

## The command list, as it now stands (unchanged since BQ)

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
