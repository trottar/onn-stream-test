# G5-S3 — flag absent, byte for byte (in process)

`PRIVYHUB_REMOTE_LADDER` in this process: absent; HEAD from git; temp files under the system temp directory (`g5_s3_absent_*`), left in place.

## 1. The actuator: HEAD vs edited `c3_linux_actuator_probe.py` (flag absent)

- cases (entry x current x target): 200; identical: **200**; differing: 0
- of which the cycle succeeded: 40 (the rest refused, identically)
- cases touching 4000: 46; accepted by the edited module: **0** (refused as at HEAD)

## 2. The games plugin: HEAD vs edited `handle_post_request("native-stream-start")` (flag absent)

| scenario | HEAD | edited | identical |
| --- | --- | --- | --- |
| started | payload, 7 stub calls | payload, 7 stub calls | **yes** |
| inactive | RuntimeError, 3 stub calls | RuntimeError, 3 stub calls | **yes** |
| start_fails | RuntimeError, 6 stub calls | RuntimeError, 6 stub calls | **yes** |

## 3. G5-S2's `replay.py`, unchanged, re-run with the new code present

```
| run | session reports | recorded decision / state events | 1. recorded reproduced | 2. controller HEAD vs edited (rows) |
| e4_s4b run3 (lossy) | 639 | 98 | exact | identical (738 rows) |
| e4_s4b run2 (cleanest) | 643 | 136 | exact | identical (780 rows) |
| cl_b3 run1 (today's best link) | 343 | 70 | exact | identical (414 rows) |
| e4_s4 E1-CONC_flag run1 (grab bursts) | 636 | 99 | exact | identical (738 rows) |
| run | ticks with a suggestion | by rule | ladder decisions changed | blocked increases | forced step-downs (taken / refused) | R5 let the rung back | remote floor would engage |
| run | ticks with a suggestion | by rule | ladder decisions changed | blocked increases | forced step-downs (taken / refused) | R5 let the rung back | remote floor would engage |
```

- flag absent (recorded decisions exact, HEAD vs edited controller identical): **PASS** (exit 0)
- its flag-present tables (`PRIVYHUB_WAN_ADAPTATION`, the edited `wan_adaptation.py`, this flag absent) equal G5-S2's recorded `replay_tables.json`: **yes**

-> flag absent: **PASS**
