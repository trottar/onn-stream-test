# H7-C2 — every load: its load line, the pictures it covers, the grid in words (no names)

Each load by hand into scratch slot 8 of the setup's own `states/<core>/` (`LOAD_STATE_SLOT 8` answered, RetroArch's
"Loading state" line naming the scratch, the scratch removed; N64: `GET_STATUS` PAUSED at the load). The stretch runs
from the load line to the next load (or the stop). "Unlocked" = the select screen's portrait grid full, no "?" box;
"locked" = "?" boxes in the grid (as T88's live run in H7-V2 and its kept end screens in H7-V1 showed, and T89's
select screen in H7-C1).

## T88 (run `runtime/h7_frames/t88_c2_20261117T024815Z/`, 141 pictures)

| load | load line (UTC) | pictures | the screen | the grid |
| --- | --- | --- | --- | --- |
| the users' cheat slot 1 | 02:49:02.140 | 41 (`f000001`-`f000041`) | the versus select screen, tally 00 – 00 | **unlocked** (3 × 7 portraits, no "?") |
| kept end P1 | 02:49:42.330 | 40 (`f000042`-`f000081`) | the versus select screen, tally 01 – 00 | **unlocked** — the same state pictured in H7-V1 (normal setup) showed the **locked** grid |
| kept end P2 | 02:50:22.413 | 40 (`f000082`-`f000121`) | the versus select screen, tally 00 – 01 | **unlocked** (was locked in H7-V1) |
| kept mid-fight (player 1 ahead) | 02:51:02.498 | 20 (`f000122`-`f000141`) | a fight in progress | — (no grid) |

## T89 (run `runtime/h7_frames/t89_c2_20261117T024815Z/`, 102 pictures)

| load | load line (UTC) | pictures | the screen | the grid |
| --- | --- | --- | --- | --- |
| the users' cheat slot 1 | 02:51:37.714 (PAUSED; released after) | 41 (`f000001`-`f000041`) | the four-player select screen, Stock 1, four human slots | **unlocked** (2 × 6 portraits, no "?") |
| kept results_1 | 02:52:18.214 (PAUSE_TOGGLE → PAUSED; PLAYING after) | 41 (`f000042`-`f000082`) | the results screen, the Place row 1 2 3 4 | — (no grid) |
| kept begin | 02:52:59.095 (PAUSE_TOGGLE → PAUSED; PLAYING after) | 20 (`f000083`-`f000102`) | the four-player select screen, Stock 1 | **locked** — "?" boxes in the grid through the whole stretch, **even under the cheat setup** |

**The key question:** T88's kept locked end states show **the unlocked grid** once loaded under T88's cheat setup (from
the first picture to the last of each stretch); T89's kept begin (made in the normal setup) **stays locked** under T89's
cheat setup for its 20 s. The users' cheat slot 1 of each title shows the unlocked grid.
