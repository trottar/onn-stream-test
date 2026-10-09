# E2-S1 — the CONC question (pre-registered §3, amendment A1)

Baseline: E1-PS1-STREAM (E1-PS1-STREAM/run1), relay thread identified (candidates 1).

## E1-CONC/run1 — 126 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 25.60 (6.76) | 41.88 | 2.41 | 1 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 8.23 (0.82) | 8.27 | 0.04 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.33 (2.30) | 4.97 | 2.02 | 1 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 36.99 | 69.06 | 75.00 | 29.96 | 29.14 | 32.23 | 35.74 | 52.36 | 40.31 | 25.90 | 26.64 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 8.27 | 8.52 | 8.69 | 8.15 | 8.05 | 8.13 | 8.13 | 8.50 | 8.29 | 8.09 | 8.21 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 4.59 | 7.58 | 10.49 | 8.03 | 0.18 | 1.43 | 3.33 | 6.98 | 6.20 | 3.65 | 1.82 |

## E1-CONC/run2 — 125 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 25.60 (6.76) | 41.48 | 2.35 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 8.23 (0.82) | 8.16 | -0.09 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.33 (2.30) | 5.44 | 2.22 | 1 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 46.77 | 76.66 | 57.32 | 25.23 | 31.82 | 29.68 | 41.79 | 53.70 | 34.51 | 24.90 | 28.39 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 8.30 | 8.61 | 8.42 | 7.82 | 8.04 | 8.06 | 8.14 | 8.28 | 8.02 | 8.00 | 8.04 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 4.63 | 14.26 | 16.33 | 6.50 | 0.55 | 1.16 | 2.07 | 4.18 | 5.81 | 0.87 | 0.81 |

