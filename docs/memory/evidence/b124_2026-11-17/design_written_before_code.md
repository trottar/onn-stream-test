# B124 — design, written before code (hashed before the first edit for B124)

Baseline HEAD `cb16e0c8` + B122 + B123. Companion changes behind `PRIVYHUB_PARTY=1` (and `PRIVYHUB_H7=1` for the mini
game); either absent → today byte for byte through the real routes. The board's repo: only my two files.

## Four pads for the board

- **The onn's join takes up to the host's ports** (`ports_set.players` in `native-stream-start`'s answer, H7-C1's
  `onn_offers.md`), and the title's `players` (`player_count.for_start`) sets the prompt. For the board both are 2
  today (no plan, no `max_players`). **Built:** while the board is the session — or a mini game has set it aside — both
  answer **4** (`"source": "party"`; reached only when a party session exists, i.e. with `PRIVYHUB_PARTY=1`). During a
  mini game the board's four, so a RESUME in a duel still takes all four pads (the hub routes the seats).
- **The board's own lobby** (read from its code): `input/controls.gd` joins up to `MAX_PLAYERS` 4 on `PAD_COUNT` 4
  pads ("hold any button for half a second"), devices pad0-pad3 = the hub's P1-P4 — **nothing there is the PC side's.**

## Four seats in the mini-game session

`party-minigame-start?…&seats=a,b,c,d` → the route for four ports (seat → port in the order given; the others
dropped) — B110's route is already n-wide; the result's scores in the seats' order (B123); every hand-over, the stop,
Home / RESUME / END and the 2-s rule as B114 / B115 made them. **A four-player title with two seats, or a two-player
one with four → refused plainly** ("this mini game takes n different seats, 1-4" — today's check, kept and tested).

## Who plays what

- **My `minigames/hub_minigame.gd`:** `MAX_PLAYERS` 4 (`MIN_PLAYERS` 2); `play(players)` already asks the hub for the
  titles whose `players` equal the count — two → its two-player titles, four → its four-player ones (seeded as now);
  three or none → the seam's draw with one line ("no mini game on the hub for N players"). My check updated (four
  players, four seats, a three-player draw; its PASS line).
- **The board's rules** (read): each round ends with `_play_minigame()` → `minigame.play(every player)` (four with four
  people), and `duel()` → `minigame.play([the two])` (the duel space, the sword item). **The picker**
  (`game/minigame_picker.gd`) keeps a shuffled bag per player count of every mini game that fits: for two and for four,
  the board's own button-mash (1-4) and the hub's — **so the hub's game comes up only every other time**. The user's
  plan needs one line in that file (the PC side's, not written here), keyed on a word the hub's launch now sets in the
  board's environment: **`PRIVYPARTY_ON_HUB=1`** (`party_session.launch_env`, only with `PRIVYHUB_PARTY=1`).

## Tests (`tests/b124_party_four_seats/`, B110 / B114's harness with B108's stand-in board, the real HTTP server)

The board's start answers four ports and four players; the board's launch environment carries the word; four seats
routed (seat → port, others dropped) and a four-player end → scores in the seats' order; a two-player title with four
seats and the reverse refused; three back to back (two-player, four-player, two-player) with B114's concurrent calls,
every hand-over planned (B115); each flag absent → today; the other suites green.
