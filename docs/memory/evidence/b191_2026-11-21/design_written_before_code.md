# B191 / B192 — design, written before code (queue BJ)

Predecessors (HEAD `13646e06`): `tools/h7_endscreen.py` 50266447…, `tools/party_add_game.py` 9865fb78…,
`companion/party_minigame.py` 06059c6f…, `handoffs/ADD_GAME_TASK.md` ed4b017c…, the template aadccb04… (unchanged).
Settled first (B190, `t91_settle.txt`); prototyped on T91's own pictures off the repo before this was written; the
prototype is not adopted, the code below is written fresh into the tools.

## The user's rule, nothing per game in code

The title's data names **the word** (given at register, `--word`, kept in the binding and the spec) and **where each
player's letters sit** (learnt from the labelled saves). At the screen after a match each player's corner is read as
letters; **the player whose letters spell the whole word has lost and the other player has won**. Neither or both
spelled, or a corner not read, is **no result** — never a guess.

## B191 — the `letters` kind

**register** `--result letters --word <WORD>` (A-Z, 2-12 letters; refused otherwise). Players: **2 only**. Four
players are refused with a plain line: in a four-player match the player who spelled the word lost, but which of the
other three won is not on that screen — winner-only would then name a winner the game never showed. What the hub
could honestly report is "port k lost" (the other three tied); the board has no such result, so it is not built.
Roles as `winner` (begin, other, end_P1, end_P1_2, end_P2, end_P2_2; more of an ending as B171); **end_Pk = port k won
= the other player spelled the word**. The binding keeps `"word"`; the sidecar `{"players": 2, "result": "letters"}`.
`--word` is refused for any other result kind.

**label** (as the score kind's label stage): the tool puts two pictures of each end save in `label/`; the session
reads each player's corner: `label <code> <role>=<P1>/<P2>,<P1>/<P2>` — each side the letters it shows left to right,
the game's not-yet marks as `-`, `_` when the corner shows nothing. The tool checks, per save:
1. the two readings the same;
2. each side fits the word: as long as the word, each place its letter or `-` (or `_`);
3. **the role agreeing**: end_Pk — the other side spells the whole word, side k does not;
4. the letters at one place in every save (the learner below finds both corners);
5. read back by a reader learnt **without that save** (B192's training included), its letters exactly;
6. **the last look**: `label/letters.png`, a row per letter (`-` too), every glyph read as that letter, numbered;
   `look=all`, or `look=<letter>:<tile numbers>` for the ones that are not.
A named save → "Read again: …" (both pictures); named twice for the same reason → back to the chat (never the user,
never another match). No ask-the-user path for letters: the session reads letters as well as the user.

**learn**: spec **version 5** from every labelled save. Cells (bars never lower than today's):
- spec usable; both corners' places found;
- B192's training: every held-out synthetic picture read (`synthetic_held_wrong_max` 0, a new bar: the training's
  own; it can fail learn, it never counts toward a pass);
- `begin: recognised within` <= 8.0 s and `begin: never ended`; `other: never ended`;
- each end save `ended as itself` / `ended within` <= 2.0 s (its own pictures, as replayed today);
- **a moving screen never ended**: each end save's own picture moved 8 px every read (a real picture, transformed;
  no synthetic letters) — never ends;
- **left out**: each end save, a spec learnt **without it** (training included): its pictures end as its role within
  2.0 s and never another, its letters read exactly;
- B176's "no two saves of one ending the same picture", as today.
Any not met → one plain line naming the save and why. More saves are asked only when a corner or a letter cannot be
learnt without a save (B171's own bound of four per ending); the line says first whether synthetic training could
cover it (it cannot make a letter no save shows, nor a corner no save shows clean).

**The begin (B190)**: the user's own start serves. It is recognised by **its own still picture**: B122's one-screen
learner on the begin's pictures against the mid-match save's and the end saves' (the pixels it shares with them left
out), every picture with B137's top-right box (200 × 70) painted black first, at learn and at every read, so the hub's
paused read ("Paused." masked) and an unpaused read are the same picture.

**The reader (hub)** `ReaderLetters`, per picture:
1. the start test (above) → `start`;
2. else each corner read (below) → spelled = the side is the word exactly;
3. both sides read: exactly one spelled → `end_P<the other>`; none → `other`; both → `unknown` ("both spelled");
4. a side not read: the other spelled → `unknown` with `end_unread` (B182's give-up after K such reads: no result);
   else `other`;
5. **a moving screen**: B140's measure against the previous read's picture (64 × 48 grey, >= 20 % of the cells moved
   by > 16 levels); a moving read of the same end class as the read before → `unknown`. So K = 3 agreeing end reads
   (B102's `Ended`, unchanged) need reads 2 and 3 still: the end is never taken on a moving screen, and is said as
   soon as today (2 s at one read a second).
Output carries `letters` (each side as read, null when not read). The companion's watcher needs no change (class,
distances, margin, `end_unread` as today).

**The hub's listing** (`party_minigame`, only with `PRIVYHUB_PARTY=1` as all of it): a sidecar `"result": "letters"`
with a version-5 spec whose end classes are exactly end_P1..end_Pn → B158's winner entry (one-hot scores, winner_of).
Absent → today; any other shape → not listed. The running companion loads the new reader only at its next start.

## Reading a corner (learnt, no hand-drawn boxes)

All at 640 × 480 RGB of the game's area (B104's bar cut).
- **The cut (where the letters' pixels are)**, per labelled end save and player, two cues:
  (a) **the pixels the same across saves**: another labelled save showing that player's same letters whose picture is
  different (fewer than half its pixels within 12 levels) — the pixels within 12 levels in both;
  (b) **a plain corner**: a corner where at least half the pixels sit within 48 levels of its commonest colour —
  the pixels not near that colour.
  Both minus the end screens' fixed pixels (the same in every labelled end save) and minus dark pixels (R+G+B < 150,
  the letters' shadow, which dark backgrounds share).
- **The place**: in each player's corners (P1 the left third, P2 the right third; top and bottom thirds), strings of
  glyphs (parts on one line, parts overlapping in x one glyph) with as many glyphs as that side shows; the place the
  one found in the most saves (centres within 8 px); two places found equally often → not found. The box: the
  string's centre ± (word length × the widest glyph + gaps)/2 + 8 px; its line ± the tallest glyph.
- **The colours** per player: chromaticity (r, g of r+g+b; 32 × 32 bins; R+G+B >= 90): a colour is the letters' when
  it is at least 0.2 % of the letters' pixels and at least `ratio` × as common among them as among every background
  pixel seen (every picture of the title outside the boxes, and B192's patch pixels).
- **The glyphs**: the letters' colours in the box; parts >= 6 px; parts overlapping in x one glyph; a glyph under 40 %
  of the smallest labelled glyph is dropped (a speck). The count must be the word's length (or 0 for `_` when a save
  shows it), else not read.
- **A letter**: the glyph's pixels in a 36 × 40 window on its centre (no resizing: one font size); each letter's
  template the mean of its labelled glyphs aligned (shared by the players: one font); distance the mean |difference|,
  least over ± 3 px; threshold halfway from its own spread to the nearest other letter's glyph (separable only with a
  gap >= 0.05); margin_needed half the least margin seen. The letter must be the word's letter at its place or `-`;
  anything else → not read.

## B192 — synthetic pictures to train, never to prove

- **Made**: from each labelled real end save, its letters' pixels (the colour model's pixels inside each read glyph)
  are cut out; the box's background is replaced by a patch cut from one of the title's own pictures (the begin, the
  mid-match save, the other end saves) at a random place and scale (1.0-1.4), never overlapping a letters box or the
  end screens' fixed text, and never a patch that itself holds a letter-sized shape in a player's letters' colours (the
  game's other text: a corner never shows it); the letters' pixels put back at their place moved by up to ± 2 px.
  The seed from the saves' own pictures and readings: the same saves always give the same set.
- **Trained**: held-out pictures made first (8 per end save), never trained on; then rounds (at most 4), each adding
  16 training pictures per end save: the colour model from the real saves' and every training picture's letter and
  background pixels, the templates and thresholds from real and training glyphs, the ratio the first of 5 / 10 / 20 /
  40 that reads every real save and **every held-out picture**. The counts, the rounds and the seconds recorded.
- **Proof stays real**: every gate of B191 reads the real saves only (left-out included); a synthetic picture is never
  read by a gate and never counts toward a pass.
- **What synthetic training cannot fix**, and how learn says so:
  - a letter no real save shows (it has no pixels to paste): label / learn name it ("shown by no save");
  - a background whose colours are the letters' own (the game's text of that colour behind a corner, or a colour that
    hides the text): training does not reach every held-out picture → learn FAIL, the line says which player's
    letters and that more saves of the same backgrounds would not help; at the hub such a match is no result;
  - a corner the real saves never show clean (no other save with that player's same letters over a different picture,
    and no plain corner): learn cannot find it; only a save can.

## Tests (made-up titles only) and mutations

- A made-up title: two players' letters in two colours from a made-up font in the top corners, every match's
  background different; the begin and the mid-match screen with the same background and different middle text.
  B102's whole-screen `winner` learner fails on it; the letters kind passes register → label → learn, its gates read
  on the real saves, left-out included.
- Label refusals: readings differ; a side not fitting the word; the role not agreeing.
- The reader: neither spelled → other, never ended; both → unknown; a corner not read with the other spelled →
  unknown + end_unread; a moving screen never ends; the begin with the corner black → start.
- The hub's listing: `letters` with a version-5 spec listed as a winner entry; a version-2 spec under `letters` not.
- Mutations (each must be caught): **(M1)** the left-out gate reads a synthetic picture of the left-out save instead of
  the save; **(M2)** the colour model takes every colour (a background read as a letter); **(M3)** neither spelled →
  the side with fewer letters wins (a guess).
- Temp dirs removed by every test.

## Not changed

`winner` / `places` / `score`, T88's, T89's and T90's rules; no bar in `BARS` lowered (one added); the companion's
watcher (`h7_minigame.py`); the app; the template.
