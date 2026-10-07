# E2-S1 — the CONC question (pre-registered §3, amendment A1)

Baseline: E1-PS1-STREAM (E1-PS1-STREAM/run1), relay thread identified (candidates 1).

## E1-CONC/run1 — 230 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 25.36 (6.21) | 56.36 | 4.99 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | -0.02 | never |
| relay thread CPU % | 7.70 (0.79) | 8.85 | 1.45 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.05 (0.30) | 21.22 | 70.54 | 0 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 41.96 | 75.47 | 67.00 | 45.14 | 57.12 | 45.68 | 36.58 | 46.03 | 31.60 | 21.65 | 26.40 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 8.73 | 8.94 | 9.02 | 8.79 | 8.82 | 8.70 | 8.71 | 9.06 | 8.40 | 9.00 | 8.00 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 16.28 | 26.93 | 28.65 | 19.76 | 14.94 | 16.06 | 18.40 | 14.35 | 18.81 | 0.00 | 0.00 |

