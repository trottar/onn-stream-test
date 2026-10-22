# ML-R1 label counts (rows = seconds after each session's first 15 s)

| set | sessions | rows | hitch seconds | rate | pos k=1 | pos k=2 | pos k=3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| heldout_bench8 | 1 | 685 | 29 | 0.0423 | 0.0424 | 0.0805 | 0.1173 |
| train | 1 | 688 | 55 | 0.0799 | 0.0801 | 0.1297 | 0.1591 |
| clean refs, training side | | 688 | 55 | | | | |
| clean refs, held-out side | | 685 | 29 | | | | |

Per session: `inventory.json` (seconds) and `label_counts_sessions.json`.
