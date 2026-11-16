# The 25 checks on the hub again (the board's HEAD changed: d774402d; headless, from its root; Godot 4.7.2-stable; 2026-11-16T17:35:44Z-2026-11-16T17:45:22Z)

The import step once first: exit 0, 2.8 s. Then each script in checks/ in order (step0-step24), exactly as PP-H1. Load = the hub's 1-minute load before / after.

| step | PASS line | assertions | exit | seconds | load before / after |
| --- | --- | --- | --- | --- | --- |
| step0 | STEP 0 CHECK: PASS | — (the line gives none) | 0 | 3.8 | 0.31 / 0.52 |
| step1 | STEP 1 CHECK: PASS (399 assertions) | 399 | 0 | 0.5 | 0.52 / 0.52 |
| step2 | STEP 2 CHECK: PASS (667 assertions) | 667 | 0 | 3.3 | 0.52 / 0.52 |
| step3 | STEP 3 CHECK: PASS (512 assertions) | 512 | 0 | 3.3 | 0.52 / 0.56 |
| step4 | STEP 4 CHECK: PASS (786 assertions) | 786 | 0 | 4.7 | 0.56 / 0.60 |
| step5 | STEP 5 CHECK: PASS (82 assertions) | 82 | 0 | 3.2 | 0.60 / 0.63 |
| step6 | STEP 6 CHECK: PASS (192 assertions) | 192 | 0 | 3.4 | 0.63 / 0.63 |
| step7 | STEP 7 CHECK: PASS (248 assertions) | 248 | 0 | 10.1 | 0.63 / 0.76 |
| step8 | STEP 8 CHECK: PASS (199 assertions) | 199 | 0 | 5.4 | 0.76 / 0.94 |
| step9 | STEP 9 CHECK: PASS (107 assertions) | 107 | 0 | 7.8 | 0.94 / 1.02 |
| step10 | STEP 10 CHECK: PASS (52 assertions) | 52 | 0 | 6.9 | 1.02 / 1.02 |
| step11 | STEP 11 CHECK: PASS (192 assertions) | 192 | 0 | 23.3 | 1.02 / 0.94 |
| step12 | STEP 12 CHECK: PASS (64 assertions) | 64 | 0 | 118.5 | 0.94 / 0.24 |
| step13 | STEP 13 CHECK: PASS (80 assertions) | 80 | 0 | 3.8 | 0.24 / 0.24 |
| step14 | STEP 14 CHECK: PASS (128 assertions) | 128 | 0 | 13.0 | 0.24 / 0.34 |
| step15 | STEP 15 CHECK: PASS (121 assertions) | 121 | 0 | 33.3 | 0.34 / 0.35 |
| step16 | STEP 16 CHECK: PASS (107 assertions) | 107 | 0 | 5.3 | 0.35 / 0.40 |
| step17 | STEP 17 CHECK: PASS (142 assertions) | 142 | 0 | 3.4 | 0.40 / 0.40 |
| step18 | STEP 18 CHECK: PASS (146 assertions) | 146 | 0 | 27.4 | 0.40 / 0.51 |
| step19 | STEP 19 CHECK: PASS (130 assertions) | 130 | 0 | 0.8 | 0.51 / 0.51 |
| step20 | STEP 20 CHECK: PASS (121 assertions) | 121 | 0 | 28.0 | 0.51 / 0.38 |
| step21 | STEP 21 CHECK: PASS (110 assertions) | 110 | 0 | 78.8 | 0.38 / 0.21 |
| step22 | STEP 22 CHECK: PASS (90 assertions) | 90 | 0 | 74.6 | 0.21 / 0.13 |
| step23 | STEP 23 CHECK: PASS (50 assertions) | 50 | 0 | 6.3 | 0.13 / 0.27 |
| step24 | STEP 24 CHECK: PASS (51 assertions) | 51 | 0 | 102.2 | 0.27 / 0.15 |

**C: 25 of 25 PASS with exit 0**; the 25 scripts' time 9.5 min. Step 19 (PP-H1's one failure, now 130 assertions) passes after the PC side's change to the check (one commit since PP-H1, checks/step19_round_bodies.gd only). The board repo's git status --short empty before and after.
