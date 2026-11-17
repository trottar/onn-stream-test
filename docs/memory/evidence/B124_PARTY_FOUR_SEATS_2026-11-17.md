---
memory_schema: 1
as_of: 2026-11-17
status: BUILT (session B, queue AR) — four seats on the board, and who plays what, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1 for the mini game): the board's start answers four players and four ports (also while a mini game sets it aside), its launch environment carries PRIVYPARTY_ON_HUB=1; party-minigame-start takes four seats (seat → port in the order given) and refuses seats that do not fit the title; my board script plays the hub's two-player titles for two players (a duel) and its four-player ones for four (a round's end), MAX_PLAYERS 4; its check PASS (40). The board's rules call the mini game with every player at a round's end and with the two at a duel; its picker would still pick its button-mash game every other time — one line for the PC side, given here, not written. Tests through the real HTTP server: 6, 3 runs. Either flag absent → today. Nothing adopted; nothing committed in either repo. No title, game id, path or picture in this record
---

# B124 — four seats on the board, and who plays what (2026-11-17)

**Baseline:** HEAD `cb16e0c8` + B122 + B123; the board's repo at `f1adc44` (the user's commit of B116), clean before.
**Design** hashed 01:35:14Z before B124's code (`b124_2026-11-17/design.sha256`); no amendment.

## Four pads for the board

- **The onn's join takes up to the host's ports** (`ports_set.players` in `native-stream-start`'s answer) and its
  prompt the title's `players` (`player_count.for_start`): for the board both were 2 (no plan, no `max_players`).
  **Built:** while the board is the session — **or a mini game has set it aside** — both answer **4**, `"source":
  "party"` (`players_session.ports_set`, `player_count.for_start`; reached only when the party module is loaded, i.e.
  with `PRIVYHUB_PARTY=1`). So a RESUME during a duel still takes all four pads (the hub routes the two seats).
- **The board's own lobby** (read, `input/controls.gd`): joins up to `MAX_PLAYERS` 4 on `PAD_COUNT` 4 pads ("hold any
  button for half a second"), pad0-pad3 = the hub's P1-P4 — **nothing there is the PC side's**.
- **The board's launch environment** carries **`PRIVYPARTY_ON_HUB=1`** (`party_session.launch_env`) — the word the PC
  side's one line below keys on.

## Four seats in the mini-game session

`party-minigame-start?…&seats=a,b,c,d` → the route for four ports (seat → port in the order given, the others dropped
— B110's route, already n-wide), the result's scores in the seats' order (B123's places form), every hand-over, the
stop, Home / RESUME / END and the 2-s rule as B114 / B115 made them. **A four-player title with two seats, or a
two-player one with four → 400 "this mini game takes n different seats, 1-4"** (today's check, now tested both ways).

## Who plays what

- **My `minigames/hub_minigame.gd`** (+3 / −1): `MAX_PLAYERS` 4 (`MIN_PLAYERS` 2). `play(players)` already asks the hub
  for the titles whose `players` equal the count — **two → its two-player titles, four → its four-player ones** (seeded
  as before); three, or none for that count → the seam's draw with one line ("no mini game on the hub for 3 players").
  **My check** (+24 / −3): four players with their pads in another order → the hub's four-player game, seats 3,1,4,2,
  its scores back; two → the two-player game; three → a draw, nothing started; offered for two to four.
  **"HUB MINIGAME CHECK: PASS (40 assertions)"** (was 34; `check_run.txt`); against an outside hub 26.
- **The board's rules** (read): every round ends with `_play_minigame()` → `minigame.play(every player)` — **four with
  four people**; a duel (`duel()`, from the duel space and the sword item) → `minigame.play([the two])`. **The picker**
  (`game/minigame_picker.gd`) keeps a shuffled bag per player count of every mini game that fits — for two and for
  four: the board's own button-mash (1-4) and the hub's — **so the hub's game would come only every other time**.
- **The one line the user's plan needs (the PC side's; not written here)** — in `game/minigame_picker.gd`, `play()`,
  right after `var id := next_id(players.size())`, add:

  ```gdscript
  	if OS.get_environment("PRIVYPARTY_ON_HUB") == "1" and Registry.minigames().has("hub") and players.size() in [2, 4]:
  		id = "hub"  # on the hub: a duel plays its two-player game, a round's end its four-player one
  ```

  (`next_id` still draws first, so the seeded bag stays in step; on the PC the word is absent: nothing changes; with
  three players the picker as before.)

## Tests (`tests/b124_party_four_seats/test_b124.py`, 6; 3 runs in `tests_x3.txt`)

B114's harness (B108's stand-in board, the stream stub with its own lock, the onn's client thread, status / result /
native-stream-status every 0.1 s, the adopted lines on) with **two mini games in the rules folder**: the fixture's PS1
title (B103's two-player spec and sidecar) and **the fixture's N64 title with a real version-3 spec and the places
sidecar `{"players": 4}`**: the board's start answers **4 players / 4 ports, source party**; the launch word `1`; the
list [2, 4]; **refused**: the four-player title with seats 1,2 and the two-player one with 1,2,3,4; **four back to back
— two-player (1,2), four-player (3,1,4,2) with Home / RESUME, two-player (2,1), four-player (1,2,3,4)**: the routes
{1→1, 2→2}, **{3→1, 1→2, 4→3, 2→4}**, {2→1, 1→2}, {1→1 … 4→4} and cleared after; the four-player ends read as places
[2, 1, 4, 3] → **scores [3, 4, 1, 2] in the seats' order**, the two-player ends [1, 0] / [0, 1] with no `places` key;
**RESUME during the four-player game answers 4 / 4**; every hand-over two planned switches, no recovery act, no key to
the board, the board's picture back, the title gone; no escalation or step; every route < 2 s while a mini game is on.
**Each flag absent → today:** B114's flag test now also compares a title's start with the prompt (players, ports) with
HEAD's code — the same (2 ports) in all four flag combinations. Other suites green (`tests_x3.txt`); **B111's test**
(this repo's run of my check) updated: the fake hub's two-and-four list and four-player result, PASS 40 / 26, ten end
calls.

## The board's two files (new hashes) and the commit line for the user

- `minigames/hub_minigame.gd` — sha256 `e246478bdab5b0ad580031ba302e5ca89a54f5529e6c8b74ebbd18a8d6dd4fb4` (was `4706a28b…`)
- `checks/hub_minigame_check.gd` — sha256 `b016167da754916fc9993dee8fdcebe44a249ac286740d793b2db6b25279c10c` (was `c09036b7…`)
- Copies in `b124_2026-11-17/board_files/`, the diff `b124_board.diff` (applies on `f1adc44`); the board's repo after:
  exactly these two ` M` lines, `.godot/` ignored as before (`board_repo_after.txt`).
- **The user, in the board's repo:** `git add minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m
  "Hub mini game: four players get the hub's four-player games, two its two-player ones, with its check"` — and, for
  the plan, the PC side's one line above in `game/minigame_picker.gd`.

## Files

`companion/players_session.py`, `companion/player_count.py`, `companion/party_session.py`,
`tests/b124_party_four_seats/test_b124.py`, `tests/b114_party_minigame_hang/` (the harness's `four` mode and extra
arguments; the flag test's ports), `tests/b111_party_board/test_b111.py`; the board's two files; `b124_2026-11-17/`:
the design and its hash, `b124.diff` (applies after `b123.diff`), `b124_board.diff`, `board_files/`, `board_*`,
`check_run.txt`, `scripts/run_all.sh`, `tests_x3.txt`, `snapshot_at.txt`, `sha256_before_after.txt`, redact / title
checks, `manifest.sha256`; `patches/B124_PARTY_FOUR_SEATS.md`.
