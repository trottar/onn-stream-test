# E2-S1 — the CONC question (pre-registered §3, amendment A1)

Baseline: E1-PS1-STREAM (E1-PS1-STREAM/run1), relay thread identified (candidates 1).

## E1-CONC/run1 — 200 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 25.67 (4.47) | 35.70 | 2.24 | 1 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 7.75 (0.81) | 7.13 | -0.77 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 3.44 (30.31) | 41.86 | 1.27 | 1 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 28.61 | 47.14 | 39.46 | 38.93 | 32.09 | 33.57 | 26.13 | 23.85 | 23.43 | 25.23 | 25.07 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 6.96 | 6.45 | 7.67 | 7.46 | 7.13 | 7.21 | 7.05 | 6.75 | 7.04 | 6.85 | 7.11 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 44.02 | 65.14 | 54.50 | 31.07 | 31.60 | 32.12 | 33.67 | 33.70 | 21.35 | 14.44 | 51.24 |

## E1-CONC/run2 — 203 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 25.67 (4.47) | 36.11 | 2.33 | 1 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | -0.02 | never |
| relay thread CPU % | 7.75 (0.81) | 7.41 | -0.43 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 3.44 (30.31) | 33.51 | 0.99 | never |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 32.48 | 46.02 | 40.17 | 36.51 | 32.83 | 33.52 | 27.75 | 27.81 | 30.43 | 25.86 | 24.87 |
| encoder dup+drop /s | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 6.60 | 7.53 | 7.70 | 7.74 | 7.33 | 7.32 | 7.07 | 6.59 | 6.61 | 6.00 | 7.00 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 37.70 | 55.63 | 48.18 | 25.50 | 24.26 | 23.32 | 24.66 | 23.12 | 28.00 | 8.74 | 1.16 |

