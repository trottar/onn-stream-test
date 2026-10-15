# E4-S1 — the CONC aligned frame (E2 §3 method, amendment A1; reported)

Baseline: E1-PS1-STREAM (E1-PS1-STREAM/run1), relay thread identified (candidates 1).

## E1-CONC/run1 — 214 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 25.24 (6.68) | 53.49 | 4.23 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 7.86 (0.79) | 8.08 | 0.28 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 2.45 (24.09) | 12.99 | 0.44 | never |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 44.87 | 74.91 | 64.35 | 50.95 | 55.44 | 37.61 | 38.04 | 33.59 | 34.52 | 39.14 | 30.44 |
| encoder dup+drop /s | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 8.02 | 8.21 | 8.26 | 8.08 | 8.01 | 7.98 | 7.88 | 8.15 | 7.95 | 7.92 | 7.89 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 10.48 | 18.71 | 18.68 | 14.55 | 11.64 | 7.83 | 6.90 | 6.55 | 4.79 | 9.42 | 7.37 |

