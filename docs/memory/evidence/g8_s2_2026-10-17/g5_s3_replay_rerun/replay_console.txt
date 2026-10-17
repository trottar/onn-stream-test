# G5-S3 replay — the remote ladder, flag present (open loop on the reports; no claim of improvement)

## 0. Flag absent on G4-S1's sessions (G5-S2's `replay_recorded`, the plain `feed`)

| run | session | first report (UTC) | routing evidence at setup | reports | recorded events | reproduced |
| --- | --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 | 1 | 22:51:00Z | overlay | 144 | 14 | exact |
| G4-S1 run 1 | 2 | 22:56:18Z | overlay | 184 | 8 | exact |
| G4-S1 run 2 | 1 | 23:07:42Z | overlay | 152 | 12 | exact |
| G4-S1 run 2 | 2 | 23:15:21Z | lan | 2 | 0 | exact |
| G4-S1 run 2 | 3 | 23:15:26Z | lan | 3 | 0 | exact |
| G4-S1 run 2 | 4 | 23:15:46Z | lan | 100 | 42 | exact |

## 1. Flag present (`PRIVYHUB_REMOTE_LADDER=1`), G5-S2's rules off and on

| run | path_class | rules | reports | transitions (from→to, reason) | reached 4000 | 4000 refused | min level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 (overlay) | as set up | off | 328 | — | no | — | 7000 |
| G4-S1 run 1 (overlay) | as set up | on | 328 | — | no | — | 7000 |
| G4-S1 run 2 (overlay, then a LAN setup) | as set up | off | 257 | — | no | — | 7000 |
| G4-S1 run 2 (overlay, then a LAN setup) | as set up | on | 257 | — | no | — | 7000 |
| e4_s4b run3 (lossy) | lan (as recorded) | off | 639 | — | no | — | 7000 |
| e4_s4b run3 (lossy) | lan (as recorded) | on | 639 | 7000→6000 wan_rules (R2.1) | no | — | 6000 |
| e4_s4b run3 (lossy) | read as remote (hypothetical) | off | 639 | — | no | — | 7000 |
| e4_s4b run3 (lossy) | read as remote (hypothetical) | on | 639 | 7000→6000 wan_rules (R2.1) | no | — | 6000 |
| e4_s4b run2 (cleanest) | lan (as recorded) | off | 643 | — | no | — | 7000 |
| e4_s4b run2 (cleanest) | lan (as recorded) | on | 643 | — | no | — | 7000 |
| e4_s4b run2 (cleanest) | read as remote (hypothetical) | off | 643 | — | no | — | 7000 |
| e4_s4b run2 (cleanest) | read as remote (hypothetical) | on | 643 | — | no | — | 7000 |
| cl_b3 run1 (today's best link) | lan (as recorded) | off | 343 | — | no | — | 7000 |
| cl_b3 run1 (today's best link) | lan (as recorded) | on | 343 | — | no | — | 7000 |
| cl_b3 run1 (today's best link) | read as remote (hypothetical) | off | 343 | — | no | — | 7000 |
| cl_b3 run1 (today's best link) | read as remote (hypothetical) | on | 343 | — | no | — | 7000 |

Checks over every replay: every row carries `path_class`; nothing below 4000; never 4000 on a `lan` path.

-> PASS

## 2. WAN rules' suggestions per run (rules on)

| run | path_class | ticks with a suggestion | by rule | `floor_4000` ticks |
| --- | --- | --- | --- | --- |
| G4-S1 run 1 (overlay) | as set up | 0 | — | 0 |
| G4-S1 run 2 (overlay, then a LAN setup) | as set up | 0 | — | 0 |
| e4_s4b run3 (lossy) | lan (as recorded) | 213 | R1.2 82, R2.1 6, R3.1 10, R5.1 115 | 0 |
| e4_s4b run3 (lossy) | read as remote (hypothetical) | 213 | R1.2 82, R2.1 6, R3.1 10, R5.1 115 | 0 |
| e4_s4b run2 (cleanest) | lan (as recorded) | 0 | — | 0 |
| e4_s4b run2 (cleanest) | read as remote (hypothetical) | 0 | — | 0 |
| cl_b3 run1 (today's best link) | lan (as recorded) | 0 | — | 0 |
| cl_b3 run1 (today's best link) | read as remote (hypothetical) | 0 | — | 0 |

## 3. Why G4-S1 did not step down: the ladder's evidence windows (sliding, evaluated reports)

| run | session (path) | evaluated reports | median fps | median lost / report | windows | loss >= 50 on >= 3 of 5 | fps < 57 on >= 4 of 5 | both (capacity_mild) | fps < 50 on all 5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 | 1 (remote) | 143 | 59.8 | 0 | 139 | 0 | 0 | 0 | 0 |
| G4-S1 run 1 | 2 (remote) | 184 | 59.8 | 0.0 | 180 | 0 | 0 | 0 | 0 |
| G4-S1 run 2 | 1 (remote) | 152 | 59.8 | 0.0 | 148 | 0 | 0 | 0 | 0 |
| G4-S1 run 2 | 4 (lan) | 100 | 59.7 | 0.0 | 96 | 0 | 3 | 0 | 0 |

A window must meet both clauses for `capacity_mild` (one rung down, the only step that reaches 4000 from 5000); the strict trigger names 5000. G5-S2's R2 / R3 need `latency-limited` / `starved` / `capacity-limited` windows; a `lossy` window alone moves nothing (R4: FEC, not a rung).

## 4. The shape of G4-S1's loss (the run's `telemetry.jsonl`, fresh reports in the window)

| run | fresh reports | lost (sum) | largest single report | when (UTC) | that report: waiting_for_idr / forward gaps | lost without it | per min without it |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 | 282 | 21,463 | 21,407 | 22:56:12.608Z | True / 1 | 56 | 6.0 |
| G4-S1 run 2 | 214 | 2,026 | 1,871 | 23:15:47.645Z | False / 32 | 155 | 21.7 |

Run 1's largest report is the first after the 24.5-s controller-silence pause (22:55:48.9Z → 22:56:13.4Z, G4-S1 §2): the sequence jump across the outage. Run 2's is the first report of the LAN-set-up stream after the toggle. Reported as read; G4-S1's record is not rewritten.

