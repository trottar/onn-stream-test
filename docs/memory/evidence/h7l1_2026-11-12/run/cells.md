# The cells (the read at that second: the watcher's rows while paused at the user's line; L4 the leader at the knockout)

| cell | the user's line (verbatim) | the read at that second (P1, P2, leader, paused) | met |
| --- | --- | --- | --- |
| L0 | — (no Continue offered; "None of that happened it just reset") | — (the plain start read 0 / 0) | **not run** (`L0_not_run.md`) |
| L1 | "Player 1 winning and player 2 at 4/5 health" | 140, 110, P1, paused | **met** |
| L2 | "Both at equal health" | 110, 110, no winner yet (equal), paused | **met** — both below 140 |
| L3 | "Player 1 won round 1" | 110, 80, P1, paused | **met** |
| L4 | "Player 2 won round 2. Player one won overall" | 140, 102, P1 (paused from 00:25:53Z) | **met** — the loser's 102 recorded |
| L5 | "It returns to character selection" | — (a menu) | **not run** (each new round read 140 / 140 → "no winner yet" during play) |
| the stream | — | 442 reads, 0 errors; 1 "busy" during a launch; median 38.2 ms, worst 53.4 ms | **clean** (`stream_rows.md`) |

**MET** — every cell that ran (L1-L4) met and the stream rows clean; L0 and L5 not run.
