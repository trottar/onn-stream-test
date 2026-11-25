# SESSION B — done, 2026-11-24 BR (QUEUE_2026-11-24BR: B219 a once-seen symbol's threshold, B220 T92 and T90 once; read line 00:26:17Z (2026-11-25), limit 01:11:17Z)

**Finished:** 00:34Z, inside the limit; nothing left undone.

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; queue BQ and session A's T92 page committed (`4af23eb4`).

**Rules kept:**
- No title started. No stream, no restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive; nothing deleted.
- **T92's real folder only read** (copied to scratch as it stands). Your slots not touched.
- **Nothing in `BARS` changed; the once rule's gate not changed. T88-T91's rules: sha256 before = after.**
- No title, id, team or character name or path in any record (four checks, plus the screen-words check kept off the
  repo). No picture in git.
- Nothing adopted; nothing committed.

## B219 — NOT BUILT, by the queue's own condition

**Why each valid test variant was not read (nothing changed):**

| title | symbol | variant | nearest | distance | threshold | margin | needed | failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T92 | 6 | 3 | 5 | 0.8572 | 0.5223 | 0.0097 | 0.1968 | threshold + margin |
| T92 | 6 | 6 | 5 | 0.8462 | 0.5223 | 0.0285 | 0.1968 | threshold + margin |
| T90 | 8 | 1 | 8 | 0.5292 | 0.5432 | 0.2190 | 0.2345 | margin |
| T90 | 8 | 4 | 8 | 0.5423 | 0.5432 | 0.2033 | 0.2345 | margin |
| T90 | 8 | 7 | 8 | 0.5392 | 0.5432 | 0.2116 | 0.2345 | margin |
| T90 | 8 | 8 | 8 | 0.5601 | 0.5432 | 0.1961 | 0.2345 | threshold + margin |

- **Five of six failed on the margin, so per item 2 nothing was changed.** Separable failed for none.
- **T92's two "?" 6s are not really the glyph:** each cut is about 62 px wide around a 35 px 6. The pasted 6 joined
  leftover ink, yet passed B214's 85 % own-ink share (86.6 %, 86.4 %).
- **T90's 8 misses are genuine:** read as 8, but with a margin a little under the title's.

**The seed** (today's code; reported, never a gate):
- T92's 6 is refused under all five seeds.
- T90's 8 is counted under two of five; its 9 under two of five.
- **T92's 6 was counted in BQ for more than the seed:** the sixth save (03-01) moved T92's `margin_needed` from
  0.1039 to 0.1968.

## B220 — T92 and T90, plan then train, once each (scratch)

| | T92 | T90 |
| --- | --- | --- |
| plan's last line | "Still needed: a final score with a 6 in it (either player)." | "Still needed: a final score with a 6 in it and a final score with a 7 in it and a final score with a 8 in it (either player; one match may show more than one)." |
| train | FAIL (23 cells); last line the same as plan's | FAIL (22 cells); last line the same as plan's |

Every cell is in the reply and in `evidence/b219_2026-11-24/b220/`. Nothing was changed after.

## Tests

- No code changed, so no new tests and no mutations.
- b208 9 OK, b214 10 OK, b210 9 OK, once.
- `git diff --stat` on `tools/`, `companion/` and `tests/` is empty, so the old path's suites were not run (the stat
  is in `logs/b219_git_status.txt`).

## What I would change (not done — the queue is the task)

1. **A valid variant should be the glyph's own size.** Its cut box should be the pasted glyph's box within a pixel or
   two, not just 85 % own ink. That would throw away T92's two 62-px cuts and redraw them; on today's numbers the six
   others all read as 6.
2. **A once-seen digit's margin should not hang on the other digits' real margins.** `margin_needed` is half the least
   margin among every real glyph, so one more save of another digit can raise it (T92: 0.1039 → 0.1968) and refuse a
   digit that passed before. A once-seen digit could be held to the margin its own real glyph shows against the others.
   That is a rule change, for a queue to state first.
3. **The seed should not decide a verdict.** T90's 8 and 9 flip across seeds. Testing more than eight variants would
   make the verdict steadier (for example "all but at most one of 16, the misses never another digit"), but that
   changes the once rule's gate, which this queue froze.

**Checks:** redaction, titles, ids, T90-T92's names: FAILS 0 each; screen words (kept off the repo): FAILS 0;
T88-T91's rules sha256 before = after.

## Files

- **Record:** `evidence/B219_ONCE_THRESHOLD_2026-11-24.md` + `b219_2026-11-24/`.
- **Patch:** `patches/B219_ONCE_THRESHOLD.md` (no code).
- **Docs:** `docs/KNOWN_ISSUES.md` (one line).
- **Logs:** `logs/b219_git_status.txt`, `handoffs/SESSION_B_STATUS.txt`, this file.

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
