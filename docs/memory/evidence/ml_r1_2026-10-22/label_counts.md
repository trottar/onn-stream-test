# ML-R1 label counts (rows = seconds after each session's first 15 s)

| set | sessions | rows | hitch seconds | rate | pos k=1 | pos k=2 | pos k=3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| heldout_bench5 | 1 | 682 | 185 | 0.2713 | 0.2702 | 0.4000 | 0.5052 |
| heldout_ux_r1 | 15 | 3140 | 241 | 0.0768 | 0.0771 | 0.1042 | 0.1231 |
| heldout_ux_r2 | 6 | 2280 | 36 | 0.0158 | 0.0150 | 0.0256 | 0.0349 |
| train | 98 | 43683 | 4861 | 0.1113 | 0.1112 | 0.1881 | 0.2239 |
| clean refs, training side | | 5488 | 388 | | | | |
| clean refs, held-out side | | 2205 | 31 | | | | |

Per session: `inventory.json` (seconds) and `label_counts_sessions.json`.
