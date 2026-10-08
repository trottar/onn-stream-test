# E2-S1 — the CONC question (pre-registered §3, amendment A1)

Baseline: E1-PS1-STREAM (E1-PS1-STREAM/run1), relay thread identified (candidates 1).

## E1-CONC/run1 — 72 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 24.54 (2.89) | 35.47 | 3.78 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 8.15 (0.83) | 8.03 | -0.15 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.15 (0.90) | 1.09 | 1.05 | 0 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 38.09 | 72.21 | 71.65 | 27.92 | 25.85 | 26.11 | 25.93 | 33.88 | 27.54 | 25.83 | 26.59 |
| encoder dup+drop /s | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |
| relay thread CPU % | 8.19 | 8.25 | 8.51 | 8.21 | 7.79 | 7.76 | 7.89 | 7.97 | 7.88 | 7.81 | 7.90 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 1.97 | 3.88 | 3.62 | 0.82 | 0.44 | 0.51 | 0.21 | 0.39 | 0.37 | 0.41 | 2.00 |

## E1-CONC/run2 — 72 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 24.54 (2.89) | 35.30 | 3.72 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 8.15 (0.83) | 7.90 | -0.3 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.15 (0.90) | 0.91 | 0.84 | 1 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 33.17 | 61.93 | 78.54 | 41.56 | 26.16 | 25.55 | 25.28 | 30.03 | 30.08 | 26.39 | 27.01 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 7.90 | 8.17 | 8.08 | 8.04 | 7.74 | 7.75 | 7.88 | 7.83 | 7.96 | 7.65 | 8.00 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 1.04 | 3.57 | 3.31 | 1.30 | 0.06 | 0.04 | 0.04 | 0.89 | 0.95 | 0.88 | 0.06 |

