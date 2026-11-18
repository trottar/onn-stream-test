# PP-H4 the cells (pre-registered, `preregistration.md` d2d7bb1f…)

| cell | read | met |
| --- | --- | --- |
| part 1 | (a)-(f): hub 97, step25 108, step26 117, step27 56, step8 210; no `board_import`; T88 end_P1 [1, 0]; T89 practice by time 90.001 s, then places [1, 2, 3, 4] / scores [4, 3, 2, 1] / seats [3, 1, 4, 2]; files before = after | met |
| self-proof S | two switches, both read: sound 1.4 s / 1.4 s after T, rises 0, lost 0 | met |
| J | the board's game after the relaunch: `4 players`; the first mini game's `minigame_start` players 4, seats [1, 2, 3, 4] from the four pads (the onn's `pad_slots` P1-P4, all `sony`). The first start (19:2xZ) had 2 players / 20 rounds — the onn saw two pads; stopped before any mini game (END, all four pads on, relaunched) | met (after the relaunch; disclosed) |
| D | two duels (T88): each `cards 1, chose 0`, players 2, ready, PAUSED, no reload; end_P1 [1, 0] seats 3,2 and 4,1; the board's lines the same | met |
| X | two rounds' ends (T89): each one card, players 4, ready, PAUSED, no reload; places [1, 4, 3, 2] / [4, 3, 2, 1], scores = places_to_scores; the board's lines the same seats | met |
| PR | 5 practices (T89 2, T88 3): the band in exactly those 5 encoder argv lines; all `"by": "select_button"`; no `minigame_ended` inside; `load screen again` 5; `after_practice` ready before each next go | met |
| S | 18 switches, all read, none listed: sound 0.0-2.0 s after each, rises ≤ 6 a row | met |
| L | per mini game in order: cards, (practice, load screen again) × n, start, scores; 10 gos (`practice` [F, T, F, T, F, T, T, F, T, F] from the self-proof on) match the board's lines | met |
| C | 7 `minigame_launch` (2 in part 1, 5 after) all `cheat` / `profile_matches`; 13 `watching` `"begin": "setup"`; the two keys `"false"` read after part 1's two launches and after the last launch (the file each launch rewrites, last written 19:41:10Z) — **not read separately at the four middle launches** | met as read (the gap disclosed) |
| F | PAUSED every second from every watch row to its go: 4/4, 5/5, 1/1, 7/7, 4/4, 36/36, 13/13, 2/2, 3/3 (+ part 1 18/18, 11/11, 13/13; self-proof 3/3); no `minigame_reloaded` anywhere | met |
| H | Home / RESUME asked once after round's end 1: taken after X2 (board paused 19:34:42Z, resumed 19:35:13Z, the board back, the pads as they were); a second, the users' own, inside D2 (`home`, `resume_start`, `resume_ready`), the duel finished | met |
| E | END: the board paused, F10, exit 0 (0.36 s); `status` inactive; nothing running | met |
| U | 228 files, 227 before = after; **T89's setup's in-game save changed** (recorded, not a cell); no `.state8` | met |
| B148 | three board launches (part 1, 19:19Z, 19:25Z): no `board_import` row at any (the test 0) | as expected |

**MET** — every cell, part 1 and the self-proof's S, with C's keys read at three of seven launches (disclosed).
