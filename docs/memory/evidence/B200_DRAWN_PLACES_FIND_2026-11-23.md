---
memory_schema: 1
as_of: 2026-11-23
status: BUILT (B200 a score title's numbers read as drawn, leading zeros included; a place whose glyphs are the same shape in saves labelled with different digits never taken; line-score cells off the final's line found where they are; B201 `--find` takes the user's words as said; B202 ADD_GAME_TASK — the user's saves asked only after register names them missing, no "other teams / characters" for score and letters, the highest score's later change taken as said). B203 T92 from its six kept saves: register PASS, label PASS, learn FAIL — one more match showing 1, 3, 4 or 5. Disclosed: the same-shape rule as built differs from the hashed design (below); B203's first label run ran before the last fix. No bar lowered; nothing adopted; nothing committed
---

# B200-B203 — T92's score places, finding a title, never re-asking for saves

Queue: `handoffs/QUEUE_2026-11-23BM.md`. The directory is `b200_2026-11-23/`:
- the design + `.sha256` (hashed 2026-11-23T18:50:00Z, before any code);
- the tests, the mutations, T90's and T91's re-run, the four checks, `scripts/`;
- `b200.diff` (applies on `ec6d8ea9`), `apply_check.txt`, `template_sha256_before.txt` / `template_sha256.txt`,
  `manifest.sha256`.

Patch: `patches/B200_DRAWN_PLACES_FIND.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty; T92's first record
committed (`ec6d8ea9`).

## B200 — settled from T92's pictures

The run's own pictures were still in T92's add_game folder (off the repo): each kept save's run (`pictures/`) and the
eight label pictures. **Read only; no picture source ran for B200 or B203** (the pictures are reused while the kept
states are the same).

- **Where things sit** (the score picture, 640 x 480): each side's final is a big number, 57 px tall, either side of a
  small box (P1's x 185-260, P2's x 408-485, rows 82-139). The box holds a cell per period for each side, one row per
  period (1ST, 2ND, 1EX, 2EX, PK), P1's at x 290-313, P2's at x 362-384, the 1ST row at rows 80-95: **15 px tall,
  above the finals' line, not on it.** Under the box, a stats table per side.
- **Every number is drawn two-digit with a leading 0:** the finals, the 1ST cells (the same as the finals: the users
  stop at half) and the stats table (13, 00, 01). A blank period cell is "--".
- **The same shape in every save:**
  - the box's frame and the period headings (1ST, 2ND, 1EX, 2EX, PK; their "1" and "2" are digit-like);
  - the "--" blanks (too flat to count as a glyph);
  - the stats headings and the buttons;
  - **the hollow inside each final's leading 0.**
- **Why P2's first cell could not be placed** (reproduced on a copy): told single numbers, the finder looked for one
  glyph at one place in every save. It took **the dark hollow inside each final's leading 0** for the finals (the one
  inside P2's 0 for P1's, the one inside P1's for P2's). B181 then looked for each side's cells on that line, where
  P2's cell — two glyphs, in the box above the line — has no one-glyph place.
- **The finals' background moves:** in 6-8 of each save's ~20 pictures one final's glyph merges into the stadium
  behind it, 1-3 s at a time. The cells in the box read in every picture. Every save's first 3 s read both finals
  whole, so the hub's 3 agreeing reads end first (recorded; not changed).
- **Measured** (each save's first labelled picture):

  | place | alike, farthest | different digits, nearest |
  | --- | --- | --- |
  | T92's finals, read as drawn | 0.327 | 0.925 |
  | T92's 1ST cells, read as drawn | 0.492 | 0.830 |
  | T90's finals (its places) | 0.342 | 0.719 |
  | the hollows of T92's leading 0s, single numbers | 0.134 | **0.034** |

## B200 — built

- **A number as drawn** (`h7_endscreen.Drawn`, an `int` whose `str` is its glyphs):
  - "03" is the value 3 for every check (the role's player ahead, the cells adding up, `--max-score`, the hub's
    result) and the glyphs "0" and "3" for every glyph count and label. The leading 0 is a 0 learnt.
  - The readings keep what the session gives; a reading without a leading 0 is byte for byte today's text.
  - The label line says: "each number as drawn, leading zeros included (a drawn 03 is 03, not 3)". Its "Read again"
    line says the same when the reason is a place.
  - The hub reads a place's glyphs and takes their value, as before ("03" → 3).
  - **A title that pads and one that does not both work**: the reading is what the screen shows.
- **Same shape, never taken** (`_shapes_explained`, `SCORE_SAME_SHAPE` = 0.5): the labels must explain a place's
  shapes — the nearest two glyphs labelled with different digits farther apart than the farther of the two
  labelled alike and 0.5. Applied to every final's candidate and every column's.
- **Cells off the final's line:**
  - when B181 finds no valid place on the line, the column is looked for anywhere: one place in every save that
    fills it, as many glyphs as drawn, its shapes explained, overlapping nothing taken, no number where a save's cell
    is blank;
  - a side's off-line columns are chosen together: the periods in drawn order (top to bottom, then left to right)
    first, then the fewest explained only by leaving a save out, then the glyphs' fit;
  - glyphs of another size (T92's 15 px cells beside 57 px finals) get their own template group (`c:`).
- **A column in another group teaches no final's digit:** learn's every-digit cell and B186's one-save rule count the
  finals' digits (and those of columns in a final's group) only, because the hub reads finals.

**Departures from the hashed design (found while building; each disclosed, none lowers a bar):**
1. **The same-shape rule.** As hashed, a single wrong reading (B178's tests: 21 read as 24; 15 as 16) made the place
   itself refused, where B178 names exactly that save through the read-back. As built, the place may also stand with
   one save left out, but only while the others still show different digits there. An off-line candidate that
   stands only that way ranks after any that stands without it. Without the tolerance, B178's two misread tests fail.
   Without the ranking, T92's left-out readers took a stats row (CK: 01 / 00 / 00) or a heading for P1's cell.
2. **The reader's templates by exact group** (`key[:-1] == group`). Before, `key.startswith(group)` let the finals'
   group "" take every key, so the finals were compared against the cells' templates. Same result for every title
   so far: their keys share one group, or use "1:" / "2:".
3. **B181's on-line search skips a place overlapping one already taken.** On a screen whose two finals share one line,
   it took the other side's final for a cell column. T90's finals are on separate lines.
4. `read_scores` / `read_columns` / `EndedScore` keep the read as `Drawn` (the same values).

## B201 — `--find`

- **Why every title answered:** the hub's library applies `q` only with `view=search`. The tool sent `system` and `q`
  with no view, so the library listed all 72 of the system's titles. The old exact pick then matched only the
  library's whole name, region suffix and all.
- **Now:** the tool lists the system's titles (paged by `offset` / `limit` until `total`) and matches the user's words
  itself, ignoring case, spacing and punctuation. It tries, in order:
  1. the whole name;
  2. the name without its bracketed parts;
  3. every word in the name.

  The first rule that matches anything decides. One title is found. Two to six are refused, with their names on
  stderr for the chat only. None, or more than six, is refused with no names.
- **Guarded:** every matched name is guarded (never printed on stdout, never written); a refusal writes nothing.

## B202 — `ADD_GAME_TASK.md` (the template unchanged, `aadccb04…` before and after)

- §1: **never ask the user to make a save before register has said it is missing** — register runs with round 1's
  collects first; only a "missing" cell (or "slot <n> is empty") leads to a line, naming exactly those saves.
- §1: **no "other teams / other characters" for `score` and `letters`** — their lines say "another match" (the
  user's rule, quoted).
- **"The same match saved twice" still makes sense for these kinds.** Two saves of one match show its glyphs once,
  not twice, so they must not count as two. It is told apart by the whole held screen — the numbers, the stats and
  the moving background differ from match to match — never by the teams. Its line now asks for another match,
  nothing about teams.
- **The highest score is asked once.** A later change is taken as said: the next register passes the new N, then
  label and learn run again. One line to the user.
- §1: `--find` takes the user's words as said; candidates are asked in chat only.
- §2: read every number as drawn, leading zeros included.

## B203 — T92 from its six kept saves (no new match, no new save)

Before: `status` and `native-stream-status` showed nothing running (not active, no stream, recovery ENDED) and no
RetroArch process. **The picture source did not run** (pictures reused). The rules folder: sha256 before = after.

| stage (UTC) | verdict | notes |
| --- | --- | --- |
| register T92 … `--max-score 5`, no `--collect` (20:00:33) | **PASS** (9 cells) | the same inputs as the first run; nothing rewritten |
| label, my readings of the four end saves, as drawn (20:00:38) | FAIL (19) | **on the build before departure 1's ranking:** "Read again: end_P2" (its left-out reader had P1's cell on a stats row) |
| — the fix, then: label, end_P2 read again (the same: 02-03) (20:09:48) | FAIL (19) | only the last look not given |
| label `look=all` (20:11:35) | **PASS** (19 cells) | label/digits.png: 0 ×20, 2 ×6, 3 ×2, 4 ×2, 5 ×2 tiles, every tile its row's digit |
| learn T92 (20:13:12) | **FAIL** (24 cells) | not met: left out end_P1_2, left out end_P2, every digit 0-5 |

**My readings** (each save, from `.1` and `.2` separately, the same both times): end_P1 `02+_+_+_+_=02-00+_+_+_+_=00`,
end_P1_2 `05…=05-04…=04`, end_P2 `02…=02-03…=03`, end_P2_2 `00…=00-02…=02`.

**learn's cells met:**
- the places;
- every digit separable;
- margin 0.2473;
- the held-out frames;
- the replays (each end save ended as its own numbers within 2.0 s; the begin and the mid-match never ended);
- no two saves the same picture.

**Not met:** every digit 0-5. Shown by two saves or more: 0 (every save's leading zeros) and 2. Shown by one save:
3, 4 and 5. Never: 1. learn's line asks for one more match showing **1, 3, 4 or 5** (`end_P1_3` / `end_P2_3`); "left
out" end_P1_2 and end_P2 fail only for those digits.

**Does B186's rule cover them?**
- **0:** yes — every save's leading zeros show it.
- **1:** no — no number the session reads shows it. The stats table's 01 and 13 are never read or labelled.
- **3, 4 and 5:** no. Each is in one save, once at the finals' size. Its second showing is the small 1ST cell,
  another size and so another template group. B186 needs one save to show a digit twice at one size.
- **What it takes:** each of 1, 3, 4 and 5 twice in the finals means at least three more matches (two finals each;
  1 needs two). Learn asks one match at a time.

## Tests, mutations

- **B200's suite, 6 tests** (`tests/b200_drawn_places/`; `pad_capture.py` a made-up padded screen like T92's — big
  padded finals with hollow 0s, a box of small padded period cells, digit-like headings, a stats table of 00s):
  - `Drawn`: read as drawn → label and learn PASS, the finals on the finals, the first cells off the line in group
    `c:`;
  - `Single`: read as single numbers → never a PASS, never a leading 0's hollow, learn refused;
  - `Counted`: two periods filled, the cells' 2 in no final → learn names 2 short;
  - `Panel`: B178's screen with single-digit finals → never the panel under the number;
  - `Value` ×2: `Drawn`, and a reading without a leading 0 is today's text.
- **B201's suite, 6 tests** (`tests/b201_find/`; a stub library answering as the companion does, made-up names, 88
  titles over two pages).
- **Three runs each, B178-B198's suites and the suites of the code touched once each:** `tests_runs.txt`.
- **Mutations:** `tests_mutations.txt`.
- **T90 and T91 re-run** on copies (their add_game folders, verdicts and the rules folder copied to my scratch; the
  tree's code; no picture source): `regress.txt`.

**Results:**
- **B200's 6 and B201's 6:** three runs each, all OK.
- **B178-B198's suites and those of the code touched:** once each, all green — B198 11, B178 23, B181 7, B185 9, B191
  14, B195 6, B175 9, B171 10, B157 17 (1 skipped, as before), B163 7, B158 6, B162 17, B169 5, B167 9, B102 16,
  B122 12, B103 13, B124 6. Temp dirs left 0.
- **Mutations, 5 of 5 caught:**
  - the same-shape rule skipped → `Panel` (the panel under the number taken);
  - a drawn number read by its value → `Drawn` (label FAIL, every read-back);
  - the off-line search skipped → `Drawn` (the place cell);
  - off-line digits counted for the finals → `Counted` (learn PASS where 2 is short);
  - the words ignored → `Words` (the library's 88 titles refused).

  Temp dirs left 0.
- **T90:** label PASS 23, learn PASS 27, both verdict files byte for byte the committed ones.
- **T91:** label PASS 19 (byte for byte); learn PASS 20. Every cell is the same; the one difference in the file is the
  recorded synthetic-training time (2.39 s committed, 2.36 s here, wall clock — not a cell).

**One earlier test changed (disclosed):** B198's `Limit` pinned B178's disclosed limit as "label FAIL on the place
cell". With B200 that title's places are now found (on table cells a one-save excuse lets through), and label fails on
the read-back instead — still never a PASS. The assertion now accepts either cell; the never-a-PASS assertion is
unchanged. Reaching that path also showed a latent crash, a final the other saves' reader saw as blank mended to
nothing in `_culprit` (the old code would have raised there too); it now keeps its labelled value.

## Checks

- `b200.diff` applies on a clean export of `ec6d8ea9`, every file byte for byte the tree; `git diff --check`
  clean (`apply_check.txt`).
- **No title, game id, setup id, serial, path or address** in any file this queue wrote: BF's three checks reused
  unchanged (`redact_check.txt`, `id_check.txt`, `title_check.txt`) and one for T92 (`code_check.py`: its binding's
  title, id and file name, loaded and never printed; `code_check.txt`), run after every file was written.
- **No picture in git.** The tests' pictures are made up, in temp dirs the tests remove. The probes' pictures stayed in
  my scratch, off the repo.
- **Read only / untouched:** the rules folder (sha256 before = after), the kept H7 folders, the users' slots, setups
  and in-game saves, the runtime pictures (read; the T92 label stage writes its own label/ pictures and label.json,
  the tool's own files). The app, the companion and the board's repo were not touched.
- **No title started:** no stream, no restart, no adb, no sudo, no nft. **Hub calls:** read-only GETs — the library
  list (once while settling B201, once by register), `status` and `native-stream-status` (once).

## Disclosed

1. The same-shape rule as built differs from the hashed design (departure 1, above), and three more departures
   (2-4).
2. **B203's first label run ran on the build before departure 1's ranking.** Its "Read again: end_P2" came from that
   fault, not from a reading. After the fix I read end_P2 again (the same) and the stage went on. end_P2's
   "named" count went to 3 (2 for place, from the first run, and 1 for read back) — kept in label.json.
3. **Temp dirs left in my scratch, off the repo, not removed by hand (nothing deleted):** two from a suite run I
   stopped, after the work copy changed under it, and one from a second run I stopped after a code change.
   Every complete run left 0.
4. The suite run in `tests_runs.txt` is the one on the final code. Two earlier full runs are not counted: one I
   stopped after a code change, and one completed before the `_culprit` fix and B198's assertion change (all green
   then but B198's `Limit`).
5. **M1 was first pointed at `Single`.** Its runner reported an error there that did not reproduce when run alone,
   where the mutant passed `Single`: that test guards the fail-safe outcome, not the rule. M1 now points at `Panel`,
   which the mutant fails.
6. **What `Single` shows:** on the made-up padded screen read as single numbers, a junk place can stand with one save
   excused (two saves' shapes coincide there by chance). The read-back then fails every save: never a PASS.
