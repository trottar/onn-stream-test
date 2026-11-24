# SESSION B — done, 2026-11-24 BP (QUEUE_2026-11-24BP: the front of the add-a-game path rebuilt once — B208 survey, B209 plan and train, B210 the hub keeps what it read, B211 T90 / T91 / T92, B212 housekeeping, B213 the commands; read line 19:16:04Z, limit 22:16:04Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; the audit and T92's second record committed (`86120a3b`, `ef8a0ce5`).

**Rules kept:**
- No stream, no companion or keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive.
- **The picture source did not run:** T90's, T91's and T92's pictures were already on the hub; the scratch runs had it
  pointed at nothing.
- Read only: your setups, slots and in-game saves, the kept H7 folders, the rules folder. **T88-T91's rules: sha256
  before = after** (23 files). Every B211 run was in a scratch copy; the real add_game folders were not written.
- No title, id, team or character name or path in any record (four checks, and one for the screens' team names kept
  off the repo). No picture in git.
- Every companion change behind `PRIVYHUB_PARTY=1`; the app and the board's repo not touched.
- Nothing adopted; nothing committed.
- Deleted: one line-file of my own in scratch (`runs/b124_alone.txt`, a failed comparison's one line) — disclosed.
  Scratch leftovers stay in `$HOME/b208_scratch` (copies of the three titles' saves and pictures, run outputs).
  The diff's apply check ran in a scratch export of HEAD made a git repository there (`git init`, nothing committed).

## B208 — survey: BUILT

- `survey <code>` puts the first ending's final screen in `survey/boxes.png`, off the repo:
  - every string today's segmentation finds, as a numbered box;
  - a grid every 40 px.
- **The session answers once:**
  - `survey <code> score <P1> <P2>` (a box number or `x0,y0,x1,y1`);
  - or `letters <WORD> <P1> <P2>`, or `winner|places` (recorded; the path then goes on as today).
- `survey/regions.png` shows each region x4; the session answers `ok`, or `again P<k>`.
- The regions are kept in the binding. **Nothing searches for them again:** a score's place is the region's own line
  of glyphs, and letters' places are the regions.
- Survey runs once register holds the three saves (register's verdict for them, whatever it says).

## B209 — plan and train: BUILT

- `label` reads the regions only.
- `plan` lists every symbol and how many real pictures show it. Its last line is the ask.
- `train` checks four gates:
  1. A symbol two or more saves show must be read by a reader learnt without its save.
  2. **The once rule:** a symbol one save shows counts when the font is rigid (≥ the bar), all 8 synthetic variants
     are read as itself, and no other glyph is read as it.
  3. A symbol never seen is asked for.
  4. Today's replays.
- **The spec is one the hub's readers already load:** version 4 with `score.places` from the regions, or version 5
  with the regions. **No hub reader change.**

**The measure:** rigidity = 1 − (farthest pair of one symbol's real glyphs) / (nearest pair of two symbols'), over the
symbols two saves show, in the result regions only.

| title | rigidity |
| --- | --- |
| T90 | 0.5693 |
| T91 | 0.1990 |
| **the bar `rigid_min`** | **0.0995** — half the smaller; in `BARS` at 19:27:27Z, before T92 |
| T92 (after) | 0.6465 |

## B210 — the hub keeps what it read: BUILT

With `PRIVYHUB_PARTY=1`, at the end of every score or letters mini game (ended, or given up on the final screen) the
hub keeps:
- the pictures the reader ended on or could not read;
- what it read, the seats and the time;
- under `<add_game home>/<code>/played/<stamp>/`, the newest 200 a title.

Flags absent → nothing.

## B211 — T90, T91, then T92 (scratch)

| | T90 | T91 | T92 |
| --- | --- | --- | --- |
| survey / label / plan | PASS / PASS / PASS | PASS / PASS / PASS | PASS / PASS / PASS |
| plan's last line | Still needed: 6 and 7 | Nothing more is needed. | **Still needed: a final score with a 1 in it (either player).** |
| train | FAIL — 6 7 8 9 | **PASS** | FAIL — 1 3 6 |
| endings read right | 3 of 5 | 4 of 4 | 3 of 5 |

**T92's train cells, as they fell:**
- gate 1: all met;
- margin_needed 0.1039 (bar 0.0796): met;
- every symbol two saves show (0, 2, 5) separable: met;
- gate 2, once rule:
  - 4: **seen once**;
  - 3: not counted (rigid 0.6465, 7 of 8 synthetic variants read as 3, no other glyph read as it);
  - 6: not counted (the same, 7 of 8);
- gate 3: **not met — 1, 3, 6**;
- screens: start 0.1651, end 0.1868;
- begin never ended, recognised at 0.0 s; other never ended;
- ended as itself within 2.0 s:
  - end_P1 02-00 (1.5 s), end_P1_2 05-04 (1.5 s), end_P2_2 00-02 (2.0 s);
  - **end_P2 and end_P2_3: not ended** (a 3 and a 6).

**T92's plan, last line as it stands:** "Still needed: a final score with a 1 in it (either player)."

## B212 — housekeeping: DONE

- **`CURRENT.md`:** as of today; health check structure all true.
- **Your quoted words:**
  - "freaking" in BG, and "hell" in BM, BN and T92's first record, each replaced by "[…]";
  - only those two words occur in the four files.
- **Noise per picture:** the made-up titles' noise is drawn per picture and per save, not by test order.

## Tests

- **New tests, three runs each:**
  - `b208_survey`: 9 tests OK ×3;
  - `b210_keep_result`: 9 tests OK ×3.
  - B210's first run failed one assertion of mine (bench's own endings are kept too); I widened it, then ran three
    times.
- **Mutations: 9 of 9 caught.**
- **The every-time suites, once, all at once, each to its end (B185 included), plus B191 / B103 / B114 / B124:**
  - OK: B103, B114, B157, B171, B175, B178, B191, B198, B200, B204.
  - **B185: 3 failures** (it ran to its end, 24 min).
  - **B181: 1 failure.**
  - B124: 0 tests ran while 12 other suites ran (its harness answer got mixed up); alone, OK on my code and on HEAD's.
- **The four B181 / B185 failures are B212's per-picture noise, not this queue's code.** Each one reproduces on HEAD's
  code with only the new noise files copied in. It is the made-up font's tight thresholds, which BI reported and test
  order had hidden. Assertions unchanged, as the queue says. **After commit these two suites fail** until the made-up
  font, or the old score path's left-out read-back, is looked at.

**Checks:** redaction, titles, ids, T90-T92's names over every file written: FAILS 0 each; the screens' team names
(a check kept off the repo): FAILS 0; `b208.diff` applies on `ef8a0ce5`.

## B213 — the commands (a new two-player title; `<code>` its code)

```
python3 tools/party_add_game.py register <code> --players 2 --system <ps1|n64|snes> --result <score|letters> [--word <WORD>] [--max-score <N>] --find "<the user's words>" --setup none --collect begin=1 --collect other=2 --collect end_P1=3
  last line, three saves: register <code>: FAIL (<n> cells; not met: kept states present, missing)   [expected: survey next]
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
  asks: Still needed: a final score with a <d> in it (either player).
        [the user's match saved to slot 2 or 3, then: register <code> … --collect end_P<the winner>_2=<slot>, label <code> <that role>=…, plan <code>]

python3 tools/party_add_game.py train <code>
  PASS: Nothing more is needed.            [after: train <code>: PASS (<n> cells)]
  asks: Still needed: a final score with a <d> in it … (either player; one match may show more than one).

python3 tools/party_add_game.py bench <code>
  PASS: bench <code>: PASS (<n> cells)
python3 tools/party_add_game.py solo <code>
  last line: solo <code>: WAITING — after the user's reply: solo <code> --read --winner <seat>
python3 tools/party_add_game.py solo <code> --read --winner <seat|draw>
  PASS: solo <code>: PASS (<n> cells)
python3 tools/party_add_game.py close <code>
  PASS: close <code>: PASS (3 cells)
```

`ADD_GAME_TASK.md` has its one RETIRED line (after its front matter, so the memory schema still reads it). The template
is unchanged.

## What I would change (not done — the queue is the task)

1. **Plan's last line is not the whole ask.** Plan names only symbols never seen. Train can then refuse a symbol seen
   once and ask for it: for T92, plan asks for 1, train for 1, 3 and 6. That breaks "nothing else asks". Plan should
   run train's once rule itself, so its line names every symbol train will refuse.
2. **The synthetic cut has a flaw.** One of the 8 variants of each glyph is cut badly (distance ~0.54-0.95 against
   ~0.3). That alone keeps T90's 8 and 9, and T92's 3 and 6, from counting "seen once". A variant should be tested only
   when its cut is the glyph that was pasted (B192's `SYN_OWN` for digits). Not changed after T92 was seen: that would
   be fitting to the title.
3. **Register should need only the three saves on the new path.** Today it FAILs on three saves and names a second save
   of each ending; survey runs anyway, but register's page still asks.
4. **A box that is a whole panel.** When the numbered box holding a number is the panel around it, the region's line
   is the panel's edge (the made-up title). The session then gives a rectangle. Survey could say so when the region's
   line touches its edge.
5. **T90 on the new path needs 6 and 7.** It counts finals only; the old path also counted the line score's cells.
   Whether a title's other places in the same font may count is the user's call.
6. **Bench, solo and close were not run on a surveyed title.** Only bench's requirement changed (train's PASS), so the
   first real title through the new path is its first bench.

## Files

- **Code:**
  - `tools/party_steps.py` (new);
  - `tools/party_add_game.py`, `tools/h7_endscreen.py`;
  - `companion/h7_minigame.py`, `companion/party_minigame.py`.
- **Tests:**
  - `tests/b208_survey/`, `tests/b210_keep_result/` (new);
  - `tests/b114_party_minigame_hang/b114_scenario.py` (the `b210` mode);
  - B212's noise: `tests/b178_score_kind/`, `tests/b181_every_digit/`, `tests/b185_overtime/`, `tests/b198_max_score/`,
    `tests/b200_drawn_places/`.
- **Record:** `evidence/B208_SURVEY_PLAN_TRAIN_2026-11-24.md` + `b208_2026-11-24/`.
- **Patch:** `patches/B208_SURVEY_PLAN_TRAIN.md`.
- **Docs:**
  - `docs/KNOWN_ISSUES.md` (one line), `docs/ROADMAP.md` (one paragraph);
  - `CURRENT.md`, `ADD_GAME_TASK.md` (one line);
  - the four files with your words.
- **Logs:** `logs/b208_git_status.txt`, `handoffs/SESSION_B_STATUS.txt`, this file.
