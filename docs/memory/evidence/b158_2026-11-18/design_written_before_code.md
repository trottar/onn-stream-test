# B158 — winner-only results (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18BB.md` §B158. Baseline `3a9de095`. Behind `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1` (the
party layer exists only with both); absent = today byte for byte; a sidecar without the new key = today.

## Settled — which endings the reader tells apart today, as data (no code per game)

1. **One whole-screen class per winner** (T88's shape): yes. The labels name the classes; the learner finds the part
   of the picture that differs between them by itself (the outcome mask); the sidecar's `scores` maps each class to
   the seats' scores. Already works for four players (`end_P1`…`end_P4`, one-hot rows): `_entries` takes n ≤ 4.
2. **A row of places on a results screen** (T89's shape, spec version 3): yes, learnt from labels `end_r<places>`; one
   horizontal row of n cells, port 1 leftmost, every place shown in every column in the sources. **Not:** ties shown on
   the screen (a read that is not a permutation is `unknown`, and the mini game is given up after 30 s).
3. **A class per player's own part of a split screen:** not as parts — there is no region per class. It works as (1)
   when every ending is one whole-screen class (the learnt mask sits on the parts that differ): fine for winner-only,
   too many classes for a full order.
4. **A winner known only from numbers or text** (a score, a time): no. The reader recognises pictures, not digits; the
   older memory rule (`<id>.json`) is never used by the party layer.

**For the user, choosing a game's mode:** a screen that shows who won the same way each time → `winner`; a results
screen with each player's place in a fixed row → `places` (or `winner` read from the same row); a winner shown only as
a number, or split screens where a full order is wanted → not yet.

## The design

The sidecar `<id>.party.json` gets an optional **`"result": "winner"`**. Absent → today (`scores` or
`places_to_scores` as now). Present and not `"winner"` → the title is not listed (as any malformed sidecar).

- **With a version-2 spec:** the end classes must be exactly `end_P1` … `end_Pn` (n = `players`), and the sidecar has
  no `scores`; class `end_Pk` → port k won. The entry's scores are built from it (1 for port k, 0 for the rest), so
  the read, the hold and the rest run as today.
- **With a version-3 spec:** no `scores` and no `places_to_scores` in the sidecar; the scores are `[1, 0, …, 0]` by
  place (place 1 → 1, the rest 0) — the read as today (a whole row of places, no ties).
- **The `minigame_ended` row and the result** carry **`"winner": <the seat>`** (the board's seat number of the port
  that won, from the seats given) beside `class`, `scores` (1 for that seat, 0 for the rest) and, for version 3,
  `places`. Only for a `winner` title; every other title's rows and answers are today's.
- T88 and T89 are not touched (their sidecars have no `result`).

## The board's side (read only)

`hub_minigame.gd` passes the scores through; `rules/game.gd` turns scores into places (`_places_from`: a player's
place is the number of players with a strictly higher score, ties share the better place) and pays
`minigame_payout[place]`, `[10, 5, 2, 0]` by default. **Scores [1, 0, 0, 0] → places [0, 1, 1, 1] → coins
[10, 5, 5, 5]**: the three tied losers each take second place's 5 (25 coins to losers, against 7 for a full order).
**For the PC side** (not changed here): a winner-only result wants its own payout — the tied last taking the worst
place, or a winner-only row such as `[10, 0, 0, 0]`; the hub cannot say "tied last" through the scores alone.

## Tests (`tests/b158_winner_only/`, B114's harness, the real HTTP server)

A made-up two-player title and a made-up four-player one (B124's places fixtures) with `"result": "winner"`: the
two-player end P1 → scores [1, 0], `winner` = the first seat; end P2 with seats 2,1 → scores [1, 0] and the winner
seat 2… (the scores in the seats' order); the four-player row 2143 with seats 3,1,4,2 → the seat whose port read place
1 wins, scores one-hot; a sidecar with `result` and `scores` both → not listed; `result` another word → not listed.
T88's and T89's own kept numbers unchanged (their sidecars and specs' sha256 read before and after the tests, which
never touch them). The flags absent → B114's `today` routes the same on HEAD and mine; B124's suite unchanged.
