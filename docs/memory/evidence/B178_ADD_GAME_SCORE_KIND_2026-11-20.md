---
memory_schema: 1
as_of: 2026-11-20
status: BUILT (B178 the `score` result kind, behind PRIVYHUB_H7=1 / PRIVYHUB_PARTY=1, either absent = today; B179 the task stops at the questions for a kind the tool lacks) — the labels read by the session from the pictures, every reading checked by the tool; T90's four end saves labelled by me through the label stage: label PASS, learn FAIL on three left-out cells (1, 3, 8, 9 each shown by one save only), its line asks one more match showing any of them; no bar lowered; nothing adopted; nothing committed
---

# B178 — the `score` result kind: each side's number read on the final screen

Queue: `handoffs/QUEUE_2026-11-20BG.md` §B178, §B179. The directory is `b178_2026-11-20/`:
- the design + `.sha256` (hashed 2026-11-20T19:37:59Z, before any code), and three addenda after code, each hashed;
- `t90/` (T90's label and learn pages as the tool wrote them in the scratch, `settle.txt`);
- `table.txt` (how far the checks catch a misread label); the tests; the mutations; the checks;
- `b178.diff` (applies on `b243dd63`); `manifest.sha256`.

Patch: `patches/B178_ADD_GAME_SCORE_KIND.md`.

## Settled from T90's six kept saves

The pictures came from session A's learn, already in the tool's T90 folder. They were copied, read only, to a scratch
off the repo, and that copy was removed after the record. **The picture source was not run:** no title was started
and no capture was made, because the six saves' pictures already existed for these exact saves. Numbers:
`t90/settle.txt`.

- **Where each side's score sits — twice, at the same places every match:**
  - a large number under each side's emblem, P1 left and P2 right, centred in a coloured triangle;
  - the FINAL column of the line-score table at the bottom, P1's row above P2's.
  - Across the four end saves each sits within 1-2 px of the same place; the numbers are centred.
- **How big, at the hub's capture** (the window 640 × 525; the reader's picture 640 × 480):
  - the large numbers 36 px tall;
  - the FINAL column 16 px (8 px at the old 320 × 240).
- **What else changes between matches:** the emblems, the team names, every stat line and the quarter-by-quarter line
  scores. The frame, the headings and the row labels stay.
- **Held still:** every end save's final screen is pixel-still (0.0 grey) for 6.5-9.0 s after its load, then a
  loading screen, then the game moves on. T88's end screen holds the same way.
- **The reader takes the FINAL column for both sides** (16 px, pooled). P2's large number never holds at one place:
  its second digit touches the red panel's edge highlight in the ink map. Choosing the sides together (addendum 2)
  puts both in the column.

## The design (hashed), and three addenda after code

- **The learner, spec version 4** (`tools/h7_endscreen.py`, a new path; versions 2 and 3 unchanged):
  - **The screen** as version 3: `start`, `end` (every score label merged), `other`.
  - **Each side's place**, learnt from the labelled saves:
    - a string with as many glyphs as that side's number has digits, in every save, at one place;
    - the sides chosen together: a line height they share, then how well the readings agree, then the tallest.
  - **How a number is read there:**
    - glyphs are 8-connected parts sitting on the place's line;
    - each glyph's cell is normalised by its own percentiles;
    - its distance to a digit's template is **the largest 3 × 3 local difference**;
    - a digit is read only within that digit's threshold **and** with the margin over the next digit;
    - any glyph not read → the screen reads `unknown`. A digit is never read by nearness alone, and one never
      labelled has no template.
  - **No package:** no OCR reader is on the hub (no tesseract, no OCR module); one would be the Debian package
    `tesseract-ocr`, not proposed. PIL + numpy only.
  - **Deterministic:** fixed sizes and orders, no randomness, no training loop. The same saves and labels give the
    same spec; the same picture gives the same reading.
- **Addendum 1:**
  - the local difference replaces the whole-cell mean (with the mean, an unseen 9 was read as 8);
  - parts are 8-connected (pixel fonts' diagonals);
  - each digit's own spread is at least the title's own variation;
  - with these, the digit `margin_needed` is held to **`margin_needed_min` (0.0796), today's bar**. T90's is 0.2794.
- **Addendum 2:** the sides chosen together (a shared line height, then the readings' agreement: 0.007 right against
  0.496 swapped on a made-up title); one entry per distinct place.
- **Addendum 3:** the label stage's line names the save a reader contradicts, the one whose correction clears the
  others when several are, and an unread save only when nothing else is named.

## The label stage — the one picture the session reads

- **`label <code>`** puts two pictures of every end save's final screen, two ticks apart, in the title's add_game
  folder `label/`, off the repo: `<role>.1.png`, `<role>.2.png`. Once the places are known, it also puts each side's
  number cut out at 4×: `<role>.P1.png`, `<role>.P2.png`.
- **The session reads them** and passes `label <code> end_P1=15-2,15-2 …`, the first reading from `.1` and the
  second from `.2`. **The user types nothing in the normal case.**
- **The tool's checks, one cell each:**
  1. the two readings the same;
  2. the role's player ahead;
  3. the numbers at one place in every save;
  4. read back by a reader learnt without that save — met when it ends with exactly those numbers, or does not read
     them for want of a digit no other save shows (named, recorded).
- **Its line** names the save to read again (with its crops). **The same save named again after the session read it
  again → "Ask the user for <role>'s numbers"**, answered with `<role>=<a>-<b>,user`. The user's numbers that still do
  not fit → collect that save again from another match.

**How far the checks catch a misread label** (`table.txt`; made-up titles through the tool):

| a misread label | caught by | the line |
| --- | --- | --- |
| one of the two readings misread | check 1 | that save, "its two readings differ" |
| a digit misread as one other saves show (24-14 for 21-14), twice | check 4 | that save, "reads it as 21-14" |
| a digit misread as one no save shows (21-17), twice | check 4 | that save, "reads it as 21-14" |
| the sides swapped (14-21 for 21-14) | check 2 | that save, "P1 is not ahead in it" |
| a digit dropped (42-2 for 42-12) | check 3 | that save, "P2's number does not fit …" |
| a digit only this save shows misread (16-2 for 15-2; T90's shape), twice | **not by the label stage**; learn cannot pass (its left-out cell); once one more save shows a 1, check 4 | that save, "reads it as 15-2" |
| **one glyph misread the same way in every save that shows it, twice each** (every 4 read as 9) | **nothing** — label PASS, learn PASS | — |

**Plainly:**
- Every misread that is random, or that leaves a save disagreeing with what the other saves teach, is caught, and
  the line names that save alone.
- A misread on a digit only one save shows waits until another save shows that digit; learn cannot pass before then.
- **What gets through is a systematic misread of one glyph shape, repeated identically in every save and both
  readings.** The role check catches it only when it changes the winner. On the hub it would turn every such digit
  into the wrong one, with consistent wrong numbers, and the winner wrong only when that flips who is ahead.

## learn, the hub, the gates

- **`register --result score`**: the same roles and rounds as `winner`.
- **learn** needs label's PASS for these saves and readings. Its cells:
  - spec usable; the score places found; every digit separable;
  - digit margin_needed ≥ 0.0796;
  - held-out frames read as other numbers 0; held-out unknown share ≤ 0.105; other read as a screen 0;
  - begin never ended, recognised ≤ 8 s; other never ended;
  - each end save ended as itself (its numbers) within 2.0 s;
  - no two saves the same picture;
  - **left out: <role>** for every end save.
  - Recorded, never a cell: the digits shown by two saves or more, by one, by none.
  - The sidecar `{"players": n, "result": "score"}`.
- **Its line:** "One more save: a match either player won whose final score shows <digits> (either side's number; the
  more of them the better) … --collect <role>=<slot> with the role of the player who won (end_P1_3 if P1 won,
  end_P2_3 if P2 won), label <code> and learn <code> again." Otherwise B171's line, and the cap as today.
- **The least labelled end saves:** every digit an end save shows must be shown by another end save.
  - **4 end saves** (register's minimum, two wins each) pass when their final scores share their digits.
  - Each digit shown by only one save needs one more save that shows it. One match can show several: T90's missing
    1, 3, 8, 9 all fit in one score such as 39-18.
  - In practice 5-6 end saves; at most the cap, 4 per player.
- **The hub** (`companion/h7_minigame.py`, `companion/party_minigame.py`, both flags):
  - at the final screen, K = 3 agreeing reads of every number;
  - `ended` carries **the real numbers** port by port, `winner` the seat of the side strictly ahead, **null on a
    tie**;
  - an unreadable final screen is `unknown`: no result, never a guess. It is given up by the 30-s unknown rule as
    today, or, when the screen moves on sooner (T90's holds 6.5-9 s), by the 900-s play limit, or the user's end.
- **Why the real numbers:** the board pays by places (`_places_from`: a place is how many score strictly more).
  - Real numbers give the true order; for four players a full order, where 1/0 pays three losers as tied seconds.
  - **A tie, read only:** `[14, 14]` → places `[0, 0]` → `[10, 10]`, and no mini game won. The board's own draw (a
    given-up mini game) pays the same.
  - **For the PC side:** a draw pays every player the winner's coins. If that is not meant, the board needs its own
    draw row (the second place's coins for all, or nothing); the hub cannot say it through the scores.
- **No bar lowered.** `winner` and `places`, T88's and T89's rules unchanged. The final screen keeps T88's bars.

## T90's learn with my labels (through the label stage, as the session will)

I opened the label stage's eight pictures and read each. The readings, the same from both pictures each:
- end_P1 **15-2**;
- end_P1_2 **35-28**;
- end_P2 **0-22**;
- end_P2_2 **0-29**.

**label: PASS (14 cells).** Read back without itself:
- end_P2 read exactly 0-22;
- the other three not read for a digit only they show: 1; 3, 8; 9. Recorded, not named.

**learn: FAIL (20 of 23 cells met)** — `t90/learn.md`:
- **met:**
  - spec usable; the places found; every digit separable; digit margin_needed 0.2794 ≥ 0.0796;
  - held-out read as other numbers 0; unknown share 0.0; other read as a screen 0;
  - begin never ended, recognised at 0.0 s; other never ended;
  - end_P1 15-2 in 1.5 s, end_P1_2 35-28 in 2.0 s, end_P2 0-22 in 2.0 s, end_P2_2 0-29 in 2.0 s;
  - no two saves the same picture;
  - **left out: end_P2** (0-22 in 2.0 s).
- **not met:** left out: end_P1, end_P1_2, end_P2_2 — each not read. Each digit only that save shows stayed unread,
  never guessed: 1 at 0.767 against a bar of 0.435; 3 at 0.790 against 0.471; 8 at 0.719 against 0.456; 9 at 0.719
  against 0.459. A digit read is 0.000-0.251 from its own template.
- **Its line:** "One more save: a match either player won whose final score shows 1, 3, 8 or 9 (either side's number;
  the more of them the better) — … (end_P1_3 if P1 won, end_P2_3 if P2 won), label T90 and learn T90 again."
- Digits shown by two saves or more: 0, 2, 5; by one: 1, 3, 8, 9; **never: 4, 6, 7.**

**Disclosed:**
- **register's PASS for `--result score` was written in the scratch** as rehearse's scratch writes it. The binding was
  session A's, its result set to `score`; no library call, since the user's words are never written.
- The real rules folder, the tool's T90 folder and the user's slots were only read.
- The scratch's rules folder stayed empty: a FAIL writes nothing.

## Tests (`tests/b178_score_kind/`, 23), mutations, suites

**B178's suite, 23 tests** (`test_b178.py`):
- **`Learn`:**
  - title A (four end saves sharing their digits): label first lists the eight pictures; label PASS; learn PASS with
    every save read by a spec without it; the sidecar `{"players": 2, "result": "score"}`; a version-4 spec;
  - T90's shape: label PASS with "shown only here", learn FAIL naming 1, 3, 8 or 9 and both next roles; then 39-18
    added → PASS;
  - learn refused without label.
- **`Reads`:**
  - a tie read as both numbers;
  - 17-3 (7 and 3 never learnt) only `unknown`, never ended;
  - never ended on: the middle of a match with a score bug, the middle of a match, the numbers moved four pixels;
  - the final screen ended with its numbers and the loading screen after it `other`;
  - the begin `start`.
- **`LabelChecks`:** two readings differ → read again → named twice → ask the user → the user's numbers PASS; the role
  and swapped sides; a digit misread as one other saves show (the three right saves not named); a digit dropped; the
  user's numbers that do not fit; a misread on a digit only one save shows (caught once another save shows it, that
  save alone named); a systematic misread passes (the residual).
- **`Hub`** (B114's harness, its new `b178` mode, the real companion and routes):
  - the tool's whole path PASS: register `--result score` → label → learn → **bench** (every end save ended with class
    `end`, its labelled numbers and its winner) → close;
  - no run-time name written or printed;
  - the hub's endings: `[21, 14]` winner 1 with seats 1,2 and winner **2** with seats 2,1; the tie `[14, 14]` winner
    **null**, its ended row the same; unreadable → given up by the unknown rule, no ended row;
  - a `score` sidecar with `scores` or another player count not listed;
  - the hub's own rules folder's every sha256 before = after.
- **`SoloDraw`:** `solo --read --winner draw` PASS on a tie; a seat named on a tie FAIL.
- **`TodayUnchanged`:** with the flags absent, B114's `today` routes are the same bytes on HEAD's code (`git archive`
  of `b243dd63`, read only) and mine.

**Three runs on the final code: 23 OK each** (269.8 / 270.3 / 270.6 s; temp dirs left 0). Before the label stage's
culprit rule (addendum 3) and the learner's docstring paragraph, the first copy ran 22 tests three times, OK
(237-240 s).

**Mutations, 5 of 5 caught by B178's own suite** (`tests_mutations.txt`, each in a copy of the final code; temp dirs
left 0):
- a score read from a spec that saw the save (the left-out save still among the sources) → `Learn`;
- a tie taken as a win → `Hub`;
- an unread digit guessed (the nearest template taken) → `Reads`;
- the role check skipped → `LabelChecks`;
- one reading accepted where two disagree → `LabelChecks`.

**The earlier suites, green** (`tests_x3.txt`):
- B175 9, B171 10, B163 7, B157 17, B162 17, B167 9, B169 5;
- and the suites of the files touched: B158 6, B102 16, B122 12, B103 13, B124 6.
- Again on the final code: B157 17, B163 7, B175 9, B171 10.
- Temp dirs left 0.

**Test files:** `tests/b178_score_kind/` (new). `tests/b114_party_minigame_hang/b114_scenario.py`: one `b178` mode
(two lines, beside `b157`'s and `b162`'s, disclosed). No other test changed.

## Checks

- **The diff:** `b178.diff` applies on a clean export of `b243dd63`, every file byte for byte the tree (8 of 8);
  `git diff --check` clean (`apply_check.txt`). The final tests ran on a copy byte for byte the tree.
- **No title, game id, setup id, serial, path or address** in any file this queue wrote. Queue BF's three checks,
  reused unchanged: `redact_check.txt`, `id_check.txt`, `title_check.txt`. They ran after every file was written,
  SESSION_B_DONE included.
- **No picture in git:** the label pictures, crops and T90's picture copies stayed in the scratch off the repo, and
  were removed with it after the record, with the two /tmp work copies. `manifest.sha256` lists this directory.
- **The template:** `ADD_GAME_PROMPT_TEMPLATE.txt` sha256 `4ba6a99a…` before = after (`b179_template_sha256.txt`).
- **Read only:** the real rules folder (its sha256 before = after in `Hub`), the tool's T90 folder, the users' slots,
  the kept H7 folders.
- **Nothing run that a hard rule forbids:** no stream, no companion or keeper restart, no flag set on the hub, no
  adb, no sudo, nothing fetched or installed. The picture source never ran: no title started.
