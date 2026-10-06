# E2-S1 — the CONC question (pre-registered §3, amendment A1)

Baseline: E1-PS1-STREAM (E1-PS1-STREAM/run1), relay thread identified (candidates 1).

## E1-CONC/run1 — 208 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 26.82 (5.43) | 55.24 | 5.23 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 7.78 (0.87) | 8.45 | 0.77 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.55 (2.24) | 26.26 | 11.47 | 0 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 40.46 | 57.17 | 78.37 | 60.21 | 52.08 | 54.24 | 31.61 | 29.69 | 31.30 | 30.95 | 33.80 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 7.65 | 8.21 | 8.90 | 8.83 | 8.51 | 8.38 | 8.01 | 7.98 | 7.45 | 7.90 | 7.80 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 34.20 | 64.67 | 43.10 | 6.47 | 9.52 | 7.47 | 20.50 | 23.21 | 21.00 | 20.86 | 18.61 |

## E1-CONC/run2 — 214 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 26.82 (5.43) | 54.80 | 5.15 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 7.78 (0.87) | 8.17 | 0.45 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.55 (2.24) | 26.00 | 11.35 | 0 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 44.90 | 66.93 | 72.84 | 48.80 | 57.20 | 44.02 | 33.80 | 35.93 | 44.51 | 38.90 | 24.25 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 6.92 | 8.74 | 8.61 | 8.23 | 8.03 | 7.99 | 7.42 | 7.15 | 7.14 | 8.20 | 6.50 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 34.98 | 61.03 | 39.36 | 9.13 | 8.56 | 8.13 | 21.33 | 26.47 | 23.87 | 29.37 | 31.86 |

