G5-S2 replay over the four named runs (whole sessions from the live log)

## 1-2. Flag absent

| run | session reports | recorded decision / state events | 1. recorded reproduced | 2. controller HEAD vs edited (rows) |
| --- | --- | --- | --- | --- |
| e4_s4b run3 (lossy) | 639 | 98 | exact | identical (738 rows) |
| e4_s4b run2 (cleanest) | 643 | 136 | exact | identical (780 rows) |
| cl_b3 run1 (today's best link) | 343 | 70 | exact | identical (414 rows) |
| e4_s4 E1-CONC_flag run1 (grab bursts) | 636 | 99 | exact | identical (738 rows) |

-> flag absent: PASS

## 3. Flag present (`WanAdaptation.feed`), open loop; no claim of improvement

### LAN (as recorded)

| run | ticks with a suggestion | by rule | ladder decisions changed | blocked increases | forced step-downs (taken / refused) | R5 let the rung back | remote floor would engage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| e4_s4b run3 (lossy) | 213 | R1.2 82, R2.1 6, R3.1 10, R5.1 115 | 1 | 34 | 1 / 1 | no | no |
| e4_s4b run2 (cleanest) | 0 | — | 0 | 0 | 0 / 0 | n/a (never below the reference) | no |
| cl_b3 run1 (today's best link) | 0 | — | 0 | 0 | 0 / 0 | n/a (never below the reference) | no |
| e4_s4 E1-CONC_flag run1 (grab bursts) | 247 | R1.1 5, R1.2 86, R3.1 5, R5.1 151 | 1 | 1 | 0 / 1 | no | no |

### read as remote

| run | ticks with a suggestion | by rule | ladder decisions changed | blocked increases | forced step-downs (taken / refused) | R5 let the rung back | remote floor would engage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| e4_s4b run3 (lossy) | 213 | R1.2 82, R2.1 6, R3.1 10, R5.1 115 | 1 | 34 | 1 / 1 | no | no |
| e4_s4b run2 (cleanest) | 0 | — | 0 | 0 | 0 / 0 | n/a (never below the reference) | no |
| cl_b3 run1 (today's best link) | 0 | — | 0 | 0 | 0 / 0 | n/a (never below the reference) | no |
| e4_s4 E1-CONC_flag run1 (grab bursts) | 247 | R1.1 5, R1.2 86, R3.1 5, R5.1 151 | 1 | 1 | 0 / 1 | no | no |

R4: FEC switch: not implemented; the fixed 8+1 stays (C4-M1); no suggestion is FEC-related.
