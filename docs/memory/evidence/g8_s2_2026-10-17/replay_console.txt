# G8-S2 replay — `PRIVYHUB_START_RUNG=floor` (open loop on the recorded reports; no claim of improvement)

| run | rules | start rung (source, path) per session | transitions (elapsed s: from→to reason) | reports at each level | back at 7000 | the recorded first acted transition | the floor-started ladder's level then | its decisions within 4 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 (overlay) | off | 4000 (floor, remote), 4000 (floor, remote) | 184: 4000→5000 increase_increase; 502: 4000→5000 increase_increase; 689: 5000→5500 increase_increase | 4000: 180 / 5000: 147 / 5500: 1 | no | none recorded | — | — |
| G4-S1 run 1 (overlay) | on | 4000 (floor, remote), 4000 (floor, remote) | — | 4000: 328 | no | none recorded | — | — |
| G4-S1 run 2 (overlay, then a LAN setup) | off | 4000 (floor, remote), 5000 (floor, lan), 5000 (floor, lan), 5000 (floor, lan) | 214: 4000→5000 increase_increase | 4000: 104 / 5000: 153 | no | none recorded | — | — |
| G4-S1 run 2 (overlay, then a LAN setup) | on | 4000 (floor, remote), 5000 (floor, lan), 5000 (floor, lan), 5000 (floor, lan) | — | 4000: 152 / 5000: 105 | no | none recorded | — | — |
| G8-S1 cell 6 loss-5 on | on | 5000 (floor, lan) | — | 5000: 330 | no | 00:33:38Z 7000→5000 recovery_escalation (today's level then: 7000) | 5000 | [('refused', 'FALLBACK', 'at_floor', 5000), ('refused', 'ROUTINE', 'at_floor', 5000)] |
| G8-S1 cell 7 burst-50x20 off | off | 5000 (floor, lan) | — | 5000: 328 | no | 00:49:35Z 7000→6000 capacity_mild (today's level then: 7000) | 5000 | [('refused', 'ROUTINE', 'at_floor', 5000)] |
| G8-S1 cell 12 delay-150 on | on | 5000 (floor, lan) | — | 5000: 331 | no | 02:06:05Z 7000→6000 wan_rules (today's level then: 7000) | 5000 | no decision within 4 s |

Check: every session's first sample row carries the start rung, at the floor of its path's list -> PASS.

Today's arm (start 7000) is replayed through the same harness; each cell's recorded first acted transition is the live one (`decisions.jsonl`).

