# B178 — the `score` result kind: design, written before any code (queue BG)

Behind `PRIVYHUB_H7=1` / `PRIVYHUB_PARTY=1` (the companion modules that read it are imported only with them); either
absent → today, byte for byte. On the vision path only: the picture of the final screen. No emulator memory, no RAM
read, no per-game code. Nothing here names a title; the same code for every title of this kind.

## 0. Settled from T90's six kept saves (the pictures session A's learn made; read only, copied to a scratch)

Measured with a prototype in a scratch folder off the repo (numbers only; no picture kept).

- **Where each side's score sits — twice, at the same places every match:** a large number under each side's emblem
  (P1 on the left, P2 on the right, centred in a coloured triangle), and the FINAL column of the line-score table at
  the bottom (P1's row above P2's). The four end saves put each at the same place within 1-2 px; the numbers are centred
  (one digit and two digits share a centre).
- **How big:** the window is 640 × 525 at the hub's capture; the large numbers are about 36-39 px tall there (18 px at
  the learner's 320 × 240), the FINAL column's 16 px at 640 × 480. Digits seen in the four end saves: 0 1 2 3 5 8 9;
  never 4, 6, 7. Shown in only one save: 1, 3, 8, 9.
- **What else changes between matches:** the two emblems and team names, every stat line (time of possession, yards
  …), the quarter-by-quarter line scores. The frame, the headings and the row labels stay.
- **Held still:** each end save's final screen is pixel-still (mean |difference| 0.0 grey) for 6.5-9.5 s after its
  load, then a loading screen (91 grey from it), then another screen. T88's end screen holds the same way; the score
  read needs K = 3 agreeing reads at one a second, so ~3 s of the 6.5-9.5 s.
- **What the digits demand of a reader (prototype, 640 × 480, the FINAL column):** the same digit in two saves differs
  by up to 0.055 (mean |difference| of the normalised glyph cell); the closest two different digits (8 / 9) 0.070
  apart; 0 / 9 0.104. A reader learnt without a save left every digit that only that save showed unread (never another
  digit): 1 at 0.196 (its nearest template's bar 0.083), 3 at 0.135 (0.073), 8 at 0.070 (0.052), 9 at 0.070 (0.058).
- **No OCR reader is on the hub** (no tesseract, no python OCR package; numpy, PIL, scipy, sklearn are). One would be
  a package to install (e.g. Debian `tesseract-ocr`): not proposed, not installed. **The reader is learnt from the
  title's own glyphs**, PIL + numpy only.

## 1. The learner: spec version 4 (`tools/h7_endscreen.py`, a new path; versions 2 / 3 unchanged)

**Labels** (the learner's labels file, as today): an end class named `end_s<a>-<b>[-<c>-<d>]` — the numbers each side
shows on that save's final screen, P1 first (two to four sides). When every end class is of this form the learner
writes version 4; any other labels → version 2 / 3 exactly as today; mixed → refused.

**The screen** — as version 3: one screen class `end` (every score class merged), `start`, `other`; each screen's own
mask, reference and threshold (`_learn_one_screen`, unchanged). The final screen is recognised as itself only; the
begin and the mid-match save are its foreign pictures; K agreeing reads; an end only after the start was seen / loaded.

**The score places** (learnt, never typed):
1. Every end save's first labelled picture, its game area at 640 × 480 (`SCORE_SIZE`, BILINEAR).
2. Ink: a pixel brighter (or darker) than its local mean (a box of radius R) by more than 12 % of the picture's own
   2nd-98th percentile spread (at least 8 grey). Both polarities, R in (8, 16) px.
3. Strings: connected components ≥ 10 px tall, no wider than 1.5 × their height; grouped left to right while their top
   and bottom agree within 2 px and the gap is at most max(4, 0.6 × height); parts overlapping in x merged into one glyph.
4. Side k's place: a string with as many glyphs as side k's number has digits, **in every end save**, at one place —
   its top and bottom within 2 px and its centre (or left edge, or right edge: the alignment) within 4 px. Among the
   places that hold in every save: the least spread, then the tallest, then the first by polarity, R, x. Side k's place
   must not overlap an earlier side's. Learnt: polarity, R, the line's top / bottom (medians), its x extent, the
   alignment.
5. Not found for a side → the spec is not usable; the report names the saves where the best place breaks (the place
   that holds in the most saves; the others named).

**How a number is read there** (the same at learn, replay and on the hub):
- The place's box (its x extent padded by one glyph cell width, its rows padded by half a line); ink as learnt; glyph =
  components whose top and bottom are the line's within 2 px, parts overlapping in x merged; left to right; the gaps at
  most max(4, 0.6 × height) (else unreadable).
- Each glyph's cell: its crop over the line's rows, normalised by its own 5th / 95th percentiles (inverted for dark
  ink: tone and background do not matter), resized to 24 px tall keeping its width (BOX), centred in a 26 × 22 cell.
- Distance to a digit's template: mean |difference| over the cell, the least over ±1 px shifts.
- **A digit is read only when** its template is separable, the glyph is within that digit's threshold, and the next
  template is at least `margin_needed` further. **Any glyph not read → the number is not read → the screen reads
  `unknown`.** Never the nearest digit by itself.
- Templates: each digit's mean cell over every labelled glyph of it (both sides pooled when their line heights agree
  within 2 px; else per side). Each digit's threshold halfway between its own worst and the nearest other digit's
  glyph (`_gap` with MIN_GAP, as version 2's classes); `margin_needed` = SAFETY × the least margin a labelled glyph
  showed. A digit never labelled has no template: it can never be read.
- **Deterministic:** fixed sizes and orders, no randomness, no training loop; the same pictures and labels give the
  same spec, and the same picture the same reading.

**A read (version 4):** the screen as version 3; on `end`: every side's number → `{"class": "end", "scores": [..]}`;
any side not read → `unknown` (scores null). **`Ended` (version 4):** K agreeing reads of the class and the whole
`scores` → ended, `ended.scores`. `score_scores` (held-out): per labelled end class — read exactly, read as other
numbers, unknown, other; `other_read_as_screen`.

## 2. The label stage (`tools/party_add_game.py label <code>`)

- **`label <code>`** (register PASS for these saves needed): makes the pictures if needed (the same picture source as
  learn), then writes, in the title's add_game folder `label/` (off the repo), for every end save **two pictures of its
  final screen two ticks apart** (`<role>_1.png`, `<role>_2.png`: the screen that stays — learn's own anchor — and the
  picture two ticks later still on it) and, once the score places are known from an earlier reading, **the crop of
  each side's number** ×4 (`<role>_P1.png`, `<role>_P2.png`). Its last line: what to read and the command.
- **The session reads them with its own vision** and passes `label <code> end_P1=<P1>-<P2>,<P1>-<P2> …` — the first
  reading from `_1`, the second from `_2`. The user's numbers, when asked: `<role>=<P1>-<P2>,user` (one reading).
- **The checks (cells, every end save):**
  1. **the two readings the same**;
  2. **the role agrees**: `end_P<k>`'s reading has P<k> strictly ahead (no draw role; a draw is not a save to label);
  3. **the scores found at one place in every save** (section 1's place search on the labels; a save whose number of
     digits does not fit where the others are is named);
  4. **read back by a reader learnt without it**: the spec learnt from every other end save (learn's own call) reads
     this save's pictures — met when it ends with exactly the labelled numbers, **or** it does not read them for want of
     a digit no other save shows (named, recorded; learn's line asks for it). Read as other numbers → not met.
- **The line** (one): a save not read → "Read the final score of …"; a check not met → "Read <role> again …" (its
  crops named when there are some); **a save named a second time after the session read it again → "Ask the user for
  <role>'s two numbers …"**; the user's numbers not met → "<role> cannot be read as the user says: collect it again
  from another match". Kept in `label.json` in the title's add_game folder: each save's readings, its state's sha256,
  how often it was named (reset when the save changes).
- **How far the checks catch a misread label** (proved on made-up titles): a digit misread as another digit some other
  save shows → check 4 (the other saves' templates disagree); misread once of two → check 1; the sides swapped or a
  digit dropped → checks 2 / 3; the same misread twice on a digit no other save shows → **not caught by the label
  stage** — but learn cannot pass with it: its left-out cell needs that digit in another save, where a right reading
  of the same glyph then disagrees with the wrong one. **What gets through:** the same wrong digit read for the same
  glyph in every save that shows it, consistently, twice each — a systematic misread of one glyph shape; the role check
  catches it only if it changes the winner.

## 3. learn, rehearse, bench, solo, close with `--result score`

- **register `--result score`**: the same roles as `winner` (begin, other, end_P1, end_P1_2, end_P2, end_P2_2; up to
  four per ending); the result-kind cell's bar `["winner", "places", "score"]`.
- **learn** needs label's PASS for these saves and readings (its inputs carry the readings). Labels: each end save's
  class `end_s<its numbers>`. **Cells:** spec usable; the score places found; every digit separable; digit
  margin_needed (see 5); held-out frames read as other numbers 0; held-out frames unknown share ≤ 0.105; other read as
  a screen 0; begin never ended, recognised ≤ 8 s; other never ended; **each end save ended with its own numbers
  within 2.0 s**; no two saves of one ending the same picture (B176); **left out: <role>** — the spec learnt without
  that save (learn's own call) replays it: ended with exactly its numbers within 2.0 s and never other numbers (B175's
  cell, for numbers). Recorded (never a cell): the digits learnt from two saves or more, from one, never.
- **The line for one more save:** a left-out save not read for want of a digit → "One more save: a match either player
  won whose final score shows <digits> (either side) …; collect it as end_P<the winner>_<n> (end_P1_3 or end_P2_3 …),
  label <code> again, then learn <code> again." Other cells → B171's line (an ending's next save). At four saves of
  both endings → the cap's line. The bars the same every time.
- **The sidecar** `{"players": n, "result": "score"}` (+ the setup). **rehearse** carries it: its scratch gets the
  title's `label.json` and a label PASS for those readings, as it writes register's. **bench**: each end save ends
  with class `end`, its labelled numbers as the scores and the winner seat. **solo --read --winner <seat|draw>**.
  **close** unchanged.
- **The least labelled end saves:** every digit an end save shows must be shown by another end save (the left-out
  cell); the register minimum (two wins each, four end saves) passes only when the four numbers share their digits;
  T90's four do not (1, 3, 8, 9 once each) → at least one more, at most one per missing digit.

## 4. The hub (`companion/party_minigame.py`, `companion/h7_minigame.py`)

- `h7_minigame` (H7 only): feeds `Ended` a read's `scores` when it has them (else `places`, as today); keeps
  `ended.scores` in the watch and its `ended` row. Versions 2 / 3: no `scores` key → today.
- `party_minigame` (both flags): a sidecar `"result": "score"` with a version-4 spec of n sides (2-4) → listed; at
  `ended` the reader's numbers, port by port, **passed through as the real numbers** (`scores`), `"winner"` = the seat
  of the one side strictly ahead, **null on a tie**. A read without n whole numbers → given up ("an end the scores do
  not name"). Unreadable → `unknown` → the 30-s unknown rule as today; never a guess.
- **Why the real numbers:** the board pays by places (`_places_from`: a place = how many score strictly more; equal
  scores share the better place). Real numbers give the board the true order — for four players a full order (1/0 would
  pay three losers as tied seconds, B158's oddity) — and a tie is a tie. **A tie, read only:** two players `[14, 14]`
  → places `[0, 0]` → `minigame_payout[0]` to both (`[10, 10]` by default) and no mini game won ("a mini game everyone
  drew is nobody's win"); the board's own draw (a given up mini game: all zeros) pays the same. **For the PC side:** a
  draw pays every player the winner's coins; if that is not meant, the board needs a draw row (e.g. the second place's
  coins for all, or nothing) — the hub cannot say it through the scores.

## 5. Bars

- No bar in `BARS` lowered or changed; `winner` / `places` and T88's / T89's rules unchanged.
- The final screen: T88's bars (recognised within 8 s, ended within 2 s, other / begin never ended, other read as a
  screen 0, held-out unknown share ≤ 0.105, read as another 0).
- **The digit margin is a new measure**: `margin_needed_min` (0.0796) is a margin between whole end screens / place
  glyphs (T88 / T89); T90's own 8 / 9 are 0.070 apart in a whole glyph cell, so that number would refuse T90's digits
  whatever the saves. The score kind's digit reading is held by the left-out cells (every digit of every save read
  exactly by a reader that never saw that save) and by its learnt thresholds; its `digit margin_needed` cell needs a
  learnt value (> 0) and is reported. Said plainly in the record; Cowork's call if it wants a fixed floor.

## 6. Proof

- **Made-up titles** (tests): a score screen whose two numbers vary by match (and a non-end screen showing a score
  during play), a tie, a digit never seen, the begin / the mid-match / a moving screen, sides with different digit
  counts; the label checks each failing on purpose; learn PASS / FAIL with its line; the hub: listed, ended with real
  numbers and the winner seat, a tie → winner null, unreadable → no result; the flags absent → today.
- **T90's six kept saves** in a scratch (the tool's env places; the real rules folder, the tool's T90 folder and the
  user's slots only read): the score places found on the real pictures; **I label the four end saves myself through
  the label stage**, reading its pictures with my own vision; the checks applied; learn's verdict reported as it falls,
  every cell. The picture source is not needed (session A's pictures exist): if it is, it runs headless only after
  `status` and `native-stream-status` show nothing running and no client, disclosed.
- **Mutations caught:** a score read from a spec that saw the save (left-out still among the sources); a tie taken as a
  win (the hub's winner on equal numbers); an unread digit guessed (the nearest template taken); the role check
  skipped; one reading accepted where two disagree. B157-B176's suites green.
