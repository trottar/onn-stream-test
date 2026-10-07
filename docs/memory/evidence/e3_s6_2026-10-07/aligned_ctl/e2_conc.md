# E2-S1 — the CONC question (pre-registered §3, amendment A1)

Baseline: E1-PS1-STREAM (E1-PS1-STREAM/run1), relay thread identified (candidates 1).

## E1-CONC/run1 — 217 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 26.44 (5.58) | 54.49 | 5.02 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 7.72 (0.78) | 7.63 | -0.12 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.08 (0.41) | 12.38 | 29.91 | 0 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 40.81 | 59.62 | 78.43 | 51.16 | 51.58 | 56.01 | 32.37 | 24.75 | 25.31 | 27.78 | 27.77 |
| encoder dup+drop /s | 0.00 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 7.45 | 7.71 | 7.85 | 7.64 | 7.60 | 7.61 | 7.36 | 7.39 | 7.18 | 8.20 | 7.25 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 11.88 | 20.99 | 17.07 | 9.64 | 8.81 | 9.03 | 7.79 | 9.52 | 0.23 | 20.11 | 8.09 |

## E1-CONC/run2 — 222 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 26.44 (5.58) | 55.57 | 5.22 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 7.72 (0.78) | 7.10 | -0.79 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.08 (0.41) | 20.69 | 50.12 | 0 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 44.35 | 73.39 | 68.33 | 45.33 | 58.95 | 45.80 | 34.08 | 39.81 | 42.11 | 42.88 | 29.35 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 7.09 | 7.13 | 7.29 | 7.02 | 7.11 | 7.07 | 7.05 | 6.85 | 7.07 | 6.88 | 6.33 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 15.81 | 28.38 | 30.51 | 19.27 | 17.31 | 14.42 | 9.59 | 13.24 | 13.01 | 6.72 | 8.96 |

