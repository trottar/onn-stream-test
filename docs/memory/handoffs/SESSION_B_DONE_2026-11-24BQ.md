# SESSION B — done, 2026-11-24 BQ (QUEUE_2026-11-24BQ: B214 the once rule's variants, B215 plan's whole ask, B216 register on three saves, B217 the old path's two suites, B218 T90 and T92 once; read line 20:11:56Z, limit 21:26:56Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; queue BP committed (`689207fc`).

**Finished:** 20:48Z, inside the limit (21:26:56Z); nothing left undone.

**Rules kept:**
- No title started. No stream, no restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive; nothing deleted.
- **Your slots and T92's real folder were not touched.** B218 ran on a fresh scratch copy; the picture source was
  pointed at nothing.
- **Nothing in `BARS` changed. T88-T91's rules: sha256 before = after** (23 files).
- No title, id, team or character name or path in any record (four checks, plus the screen-words check kept off the
  repo). No picture in git; the app and the board's repo not touched.
- Nothing adopted; nothing committed.

## B214 — the once rule's variants: BUILT

- **A test variant counts only when it is the glyph that was pasted:** the cut finds exactly one glyph, and at least
  0.85 (`SYN_OWN`) of its ink is pasted ink.
- An invalid one is thrown away and the next drawn, up to 24 draws. **Eight valid are needed;** fewer → not counted,
  "variants could not be made".
- **The test variants are never in the templates:** a separate random stream.
- The rule otherwise unchanged.

## B215 — plan's last line is the whole ask: BUILT

plan runs train's gates itself (nothing written). Its last line names everything train would ask for, and **train's
last line is the same sentence** (tested on three made-up titles, and on T90 and T92 below).

## B216 — register on three saves: BUILT

- **New path** (a survey, or a score / letters title the old learn never learnt): register PASSes on begin, other and
  one ending. Further endings come when plan asks.
- **Old path** (T90 / T91, winner / places): two saves per ending, as before.
- **Fixed along the way:** register now keeps the survey. BP's register would have dropped it on a later `--collect`.

## B217 — the old path's two suites: BUILT

B181 and B185 are back on exactly their pre-BP noise, with a first line saying so. The per-picture noise stays for the
new path's suites.

## B218 — T90 and T92, once each (scratch)

| | T90 | T92 |
| --- | --- | --- |
| survey / label / plan | PASS / PASS / PASS (BP's answers; the same regions) | PASS / PASS / PASS |
| plan's list | 3 4 9 seen once; 8 not counted; 6 7 never | 4 6 seen once; 3 not counted; 1 never |
| train | FAIL (22 cells) | FAIL (21 cells) |
| endings read right | 4 of 5 | 4 of 5 |

**Still refused, and what their variants read as:**
- **T90's 8:** 8 valid variants in 8 draws. 4 read as 8, 4 not read ("?"); none as another digit.
- **T92's 3:** 8 valid in 10 draws (2 thrown away by the cut rule). 6 read as 3, 2 not read; none as another digit.

Every cell is in the reply and in `evidence/b214_2026-11-24/b218/`. Nothing was changed after these runs.

## Tests

- **New tests:** `b214_variants`, 10 tests, three runs OK.
- **Mutations: 5 of 5 caught.**
- **The every-time suites, once, all at once, each to its end:**
  - OK: B157, B171, B175, B178, **B181**, **B185** (29.7 min), B198, B200, B204, B210.
  - **B208: 2 failures on its run.** Two of BP's own assertions, written for exactly what this queue changes (two
    variants; plan's plain "once" rows). Brought to B214 / B215, then 9 OK.
- **Checks:** redaction, titles, ids, T90-T92's names: FAILS 0 each; screen words (kept off the repo): FAILS 0.
  `b214.diff` applies on `689207fc`.

## Files

- **Code:** `tools/party_steps.py`, `tools/party_add_game.py`.
- **Tests:**
  - `tests/b214_variants/` (new);
  - `tests/b208_survey/test_b208.py` (two assertions);
  - `tests/b181_every_digit/line_capture.py`, `test_b181.py`, `tests/b185_overtime/test_b185.py` (pre-BP, plus a
    first line).
- **Record:** `evidence/B214_VARIANTS_AND_WHOLE_ASK_2026-11-24.md` + `b214_2026-11-24/`.
- **Patch:** `patches/B214_VARIANTS_AND_WHOLE_ASK.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line).
- **Logs:** `logs/b214_git_status.txt`, `handoffs/SESSION_B_STATUS.txt`, this file.

## What I would change (not done — the queue is the task)

1. **A once-seen digit's own threshold is the remaining gap.** Every valid variant of T90's 8 and T92's 3 was either
   read right or not read; none was read as another digit. The threshold of a digit learnt from one save comes from
   that save's glyphs only, so shifted copies of the same glyph fall just outside it. Setting a once-seen digit's
   threshold from its own valid variants (still never in the templates) would likely count both. That is a rule
   change, for a queue to state first.
2. **Plan takes as long as train's gates** (T92 about 8 s; a letters title about 75 s: five learns). Fine for now. If
   letters titles grow, plan could keep its gates' result for train to reuse when the inputs are the same.
3. **The new-path test in register reads the rules folder's sidecar** to tell the old learn's titles apart. An explicit
   `"path"` field in the binding, written by survey and by learn, would say it without looking.

## B213's command list, as it now stands

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
