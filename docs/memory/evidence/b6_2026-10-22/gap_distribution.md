# B6 — every uplink silence >= 250 ms on file: the distribution, and H

From the control-gap logs (E3-R2's, one row per client->host silence > 250 ms) in the evidence copies, read-only (`gap_distribution.py` -> `gap_distribution.json`). Per 10 min = over seconds with frames on the host. 10 s at every session start / end excluded (start-up, teardown). **Clean sessions (chosen before computing, the queue's list): BENCH-R1 cells 1 and 8; UX-R2's evening less the death, the two user pauses and session edges.** The CL-B5/6/7 windows have no gap log (it exists only since E3-R2). Everything else is shown, not used.

| session | clean | streaming s | gaps >= 250 | per 10 min | 250-300 ms | 300-400 ms | 400-500 ms | 500-600 ms | 600-800 ms | 800-1000 ms | 1000-1500 ms | 1500-inf ms | longest ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BENCH-R1 01_loss-1_plain | **yes** | 671 | 11 | 9.84 | 4 (3.58) | 4 (3.58) | 2 (1.79) | 1 (0.89) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 517 |
| BENCH-R1 08_none_hold | **yes** | 671 | 18 | 16.1 | 7 (6.26) | 6 (5.37) | 2 (1.79) | 0 (0.0) | 0 (0.0) | 2 (1.79) | 1 (0.89) | 0 (0.0) | 1336 |
| BENCH-R1 02_loss-1_lan_rule | no | 672 | 22 | 19.64 | 8 (7.14) | 11 (9.82) | 0 (0.0) | 1 (0.89) | 0 (0.0) | 2 (1.79) | 0 (0.0) | 0 (0.0) | 989 |
| BENCH-R1 03_loss-5_lan_rule | no | 673 | 41 | 36.55 | 17 (15.16) | 13 (11.59) | 5 (4.46) | 5 (4.46) | 1 (0.89) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 647 |
| BENCH-R1 04_burst-50x20_lan_rule | no | 672 | 79 | 70.54 | 29 (25.89) | 27 (24.11) | 10 (8.93) | 6 (5.36) | 2 (1.79) | 3 (2.68) | 2 (1.79) | 0 (0.0) | 1429 |
| BENCH-R1 05_blackout-both_plain (outside blackouts) | no | 617 | 132 | 128.36 | 39 (37.93) | 38 (36.95) | 22 (21.39) | 11 (10.7) | 11 (10.7) | 5 (4.86) | 5 (4.86) | 1 (0.97) | 1742 |
| BENCH-R1 06_blackout-both_hold (outside blackouts) | no | 618 | 31 | 30.1 | 9 (8.74) | 6 (5.83) | 6 (5.83) | 7 (6.8) | 3 (2.91) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 667 |
| BENCH-R1 07_blackout-down_plain (outside blackouts) | no | 617 | 6 | 5.83 | 1 (0.97) | 4 (3.89) | 1 (0.97) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 412 |
| UX-R2 clean minutes (04:42-05:27Z less the death, the two user pauses, session edges) | **yes** | 2204 | 13 | 3.54 | 7 (1.91) | 5 (1.36) | 0 (0.0) | 0 (0.0) | 1 (0.27) | 0 (0.0) | 0 (0.0) | 0 (0.0) | 669 |
| UX-R1 whole evening (Sunday, 04:19-05:23Z) | no | 3011 | 256 | 51.01 | 73 (14.55) | 76 (15.14) | 39 (7.77) | 31 (6.18) | 20 (3.99) | 9 (1.79) | 6 (1.2) | 2 (0.4) | 3232 |

Cells: count (per 10 min).

**Gaps >= H per 10 min, the clean sessions (cell 1 / cell 8 / UX-R2), max, pooled:**

| H ms | cell 1 | cell 8 | UX-R2 clean | max | pooled |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 250 | 9.84 | 16.1 | 3.54 | 16.1 | 7.11 |
| 300 | 6.26 | 9.84 | 1.63 | 9.84 | 4.06 |
| 350 | 5.37 | 6.26 | 0.82 | 6.26 | 2.71 |
| 400 | 2.68 | 4.47 | 0.27 | 4.47 | 1.52 |
| 450 | 2.68 | 4.47 | 0.27 | 4.47 | 1.52 |
| 500 | 0.89 | 2.68 | 0.27 | 2.68 | 0.85 |
| 550 | 0.0 | 2.68 | 0.27 | 2.68 | 0.68 |
| 600 | 0.0 | 2.68 | 0.27 | 2.68 | 0.68 |
| 650 | 0.0 | 2.68 | 0.27 | 2.68 | 0.68 |
| 700 | 0.0 | 2.68 | 0.0 | 2.68 | 0.51 |
| 750 | 0.0 | 2.68 | 0.0 | 2.68 | 0.51 |
| 800 | 0.0 | 2.68 | 0.0 | 2.68 | 0.51 |
| 850 | 0.0 | 1.79 | 0.0 | 1.79 | 0.34 |
| 900 | 0.0 | 1.79 | 0.0 | 1.79 | 0.34 |
| 950 | 0.0 | 0.89 | 0.0 | 0.89 | 0.17 |
| 1000 | 0.0 | 0.89 | 0.0 | 0.89 | 0.17 |
| 1050 | 0.0 | 0.89 | 0.0 | 0.89 | 0.17 |
| 1100 | 0.0 | 0.89 | 0.0 | 0.89 | 0.17 |
| 1150 | 0.0 | 0.89 | 0.0 | 0.89 | 0.17 |
| 1200 | 0.0 | 0.89 | 0.0 | 0.89 | 0.17 |
| 1250 | 0.0 | 0.89 | 0.0 | 0.89 | 0.17 |
| 1500 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 1750 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2000 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

**H chosen = 950 ms**: the smallest value (50-ms grid) with <= 1 gap >= H per 10 min on each clean session. (Pooled over the three, the rule would give 500 ms.)

**The death's five gaps (967 / 546 / 442 / 350 / 342 ms): H = 950 holds 1 of them (967)**; each is held from H to its end.

| Sunday window | gaps >= 250 | gaps >= H | longest ms | silent ms in gaps >= H / all |
| --- | ---: | ---: | ---: | ---: |
| Sunday step 04:56-05:05 | 34 | 0 | 623 | 0 / 12023 |
| Sunday burst 05:06 | 51 | 3 | 1296 | 3422 / 24364 |
| Sunday burst 05:10-05:11 | 48 | 3 | 1733 | 3873 / 21119 |
| Sunday burst 05:20-05:21 | 79 | 4 | 3232 | 6803 / 37516 |
