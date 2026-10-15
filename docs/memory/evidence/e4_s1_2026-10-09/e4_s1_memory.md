# E4-S1 — the memory row read by E2 §5 (reported)

| run | PSS before first grab (anon / file) MB | after first grab | window end | growth anon / file share | last-15-min slope (% of level per 15 min) | reading | node PSS per grab, first / last (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1-META/run1 | 26.3 (24.5 / 1.8) | 32.2 (30.4 / 1.8) | 34.1 (32.3 / 1.8) | 99.1 % anon | 4.05 | plateaus | 651.0 / 855.4 |
| E1-CONC/run1 | 35.1 (33.5 / 1.7) | 41.9 (40.2 / 1.7) | 48.8 (47.1 / 1.7) | 100.0 % anon | 5.94 | keeps growing | 650.2 / 633.7 |

- E1-META/run1: companion PSS per minute of the window (MB): [32.6, 32.6, 32.6, 32.6, 32.6, 32.6, 32.6, 32.6, 32.6, 33.1, 33.6, 33.6, 33.6, 33.6, 33.6, 33.6, 33.6, 33.6, 33.6, 33.8, 34.1]
- E1-CONC/run1: companion PSS per minute of the window (MB): [43.1, 43.6, 43.7, 44.4, 45.6, 45.6, 45.7, 46.1, 47.8, 47.8, 47.9, 47.9, 47.9, 48.0, 48.1, 48.1, 48.2, 48.4, 48.6, 48.6, 51.0]
