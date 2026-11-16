# The 25 checks on the hub (headless, from the board game's repo root; Godot 4.7.2-stable; 2026-11-16T16:06:02Z-2026-11-16T16:15:45Z)

The import step once first: exit 0, 3.9 s. Then each script in `checks/` in order (step0-step24). Load = the hub's 1-minute load before / after.

| step | PASS line | assertions | exit | seconds | load before / after |
| --- | --- | --- | --- | --- | --- |
| step0 | `STEP 0 CHECK: PASS` | — (the line gives none) | 0 | 3.8 | 0.42 / 0.47 |
| step1 | `STEP 1 CHECK: PASS (399 assertions)` | 399 | 0 | 0.5 | 0.47 / 0.47 |
| step2 | `STEP 2 CHECK: PASS (667 assertions)` | 667 | 0 | 3.3 | 0.47 / 0.51 |
| step3 | `STEP 3 CHECK: PASS (512 assertions)` | 512 | 0 | 3.4 | 0.51 / 0.51 |
| step4 | `STEP 4 CHECK: PASS (786 assertions)` | 786 | 0 | 4.7 | 0.51 / 0.63 |
| step5 | `STEP 5 CHECK: PASS (82 assertions)` | 82 | 0 | 3.2 | 0.63 / 0.66 |
| step6 | `STEP 6 CHECK: PASS (192 assertions)` | 192 | 0 | 3.3 | 0.66 / 0.66 |
| step7 | `STEP 7 CHECK: PASS (248 assertions)` | 248 | 0 | 10.1 | 0.66 / 0.63 |
| step8 | `STEP 8 CHECK: PASS (199 assertions)` | 199 | 0 | 5.4 | 0.63 / 0.84 |
| step9 | `STEP 9 CHECK: PASS (107 assertions)` | 107 | 0 | 7.7 | 0.84 / 0.85 |
| step10 | `STEP 10 CHECK: PASS (52 assertions)` | 52 | 0 | 6.9 | 0.85 / 0.86 |
| step11 | `STEP 11 CHECK: PASS (192 assertions)` | 192 | 0 | 23.3 | 0.86 / 0.81 |
| step12 | `STEP 12 CHECK: PASS (64 assertions)` | 64 | 0 | 118.6 | 0.81 / 0.22 |
| step13 | `STEP 13 CHECK: PASS (80 assertions)` | 80 | 0 | 3.8 | 0.22 / 0.20 |
| step14 | `STEP 14 CHECK: PASS (128 assertions)` | 128 | 0 | 13.0 | 0.20 / 0.17 |
| step15 | `STEP 15 CHECK: PASS (121 assertions)` | 121 | 0 | 33.3 | 0.17 / 0.25 |
| step16 | `STEP 16 CHECK: PASS (107 assertions)` | 107 | 0 | 5.4 | 0.25 / 0.31 |
| step17 | `STEP 17 CHECK: PASS (142 assertions)` | 142 | 0 | 3.4 | 0.31 / 0.37 |
| step18 | `STEP 18 CHECK: PASS (146 assertions)` | 146 | 0 | 27.4 | 0.37 / 0.32 |
| step19 | `STEP 19 CHECK: FAIL (1 of 125 assertions)` | 1 failed of 125 | 1 | 0.8 | 0.32 / 0.32 |
| step20 | `STEP 20 CHECK: PASS (121 assertions)` | 121 | 0 | 28.0 | 0.32 / 0.37 |
| step21 | `STEP 21 CHECK: PASS (110 assertions)` | 110 | 0 | 79.6 | 0.37 / 0.24 |
| step22 | `STEP 22 CHECK: PASS (90 assertions)` | 90 | 0 | 74.5 | 0.24 / 0.24 |
| step23 | `STEP 23 CHECK: PASS (50 assertions)` | 50 | 0 | 6.3 | 0.24 / 0.22 |
| step24 | `STEP 24 CHECK: PASS (51 assertions)` | 51 | 0 | 102.2 | 0.22 / 0.16 |

**24 of 25 PASS with exit 0**; the 25 scripts' time 9.5 min (with the import 9.6 min).

**Step 19 failed** — one of 125 assertions: `FAIL: the picture wraps round a part's front; its back carries the edges on: Hips has a front, sides and a back` (`step19_failure_output.txt`, the whole output). Run again twice after the set (extra reads, not counted): the same single failure both times, exit 1 — **deterministic on the hub**. The assertion counts the corners of the body's Hips piece whose surface faces front, side and back (more than four of each, `checks/step19_round_bodies.gd` `_wrapped_round`); on the hub one of the three counts is four or fewer. The hand-back says all 25 pass on the PC — what differs between the PC and the hub here (the imported body model built fresh on the hub, floating-point limits at a threshold) is not settled; nothing in the repo was edited to look.
