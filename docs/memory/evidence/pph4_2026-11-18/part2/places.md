# Each mini game: the hub's row first, the board's credit, the users' words

| # | title | seats (ports 1..n) | the hub's `minigame_ended` | the board's line | the users |
| --- | --- | --- | --- | --- | --- |
| X1 | T89 | 1,2,3,4 | `end`, places [1, 4, 3, 2], scores [4, 1, 2, 3] | `scores [4, 1, 2, 3] for seats 1,2,3,4` | "P1" |
| X2 | T89 | 1,2,3,4 | `end`, places [4, 3, 2, 1], scores [1, 2, 3, 4] | `scores [1, 2, 3, 4] for seats 1,2,3,4` | "P4" |
| D1 | T88 | 3,2 (P3 started it) | `end_P1`, [1, 0] | `scores [1, 0] for seats 3,2` | "P3 won" |
| D2 | T88 | 4,1 (P4 started it) | `end_P1`, [1, 0] | `scores [1, 0] for seats 4,1` | "P4 won" |

Every one agrees. The users gave the winner, not T89's whole Place row or the board's payout; the payout is the board's
`scores` (places_to_scores [4, 3, 2, 1]). No character was said to be locked.
