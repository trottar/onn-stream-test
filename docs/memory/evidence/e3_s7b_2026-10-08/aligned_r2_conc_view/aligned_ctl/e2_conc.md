# E2-S1 — the CONC question (pre-registered §3, amendment A1)

Baseline: E1-PS1-STREAM (E1-PS1-STREAM/run1), relay thread identified (candidates 1).

## E1-CONC/run1 — 217 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 25.60 (6.76) | 55.34 | 4.4 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 8.23 (0.82) | 8.49 | 0.31 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.33 (2.30) | 7.83 | 3.26 | 0 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 41.10 | 74.85 | 73.30 | 48.47 | 59.77 | 42.10 | 31.98 | 27.21 | 26.86 | 32.26 | 27.60 |
| encoder dup+drop /s | 0.00 | 0.00 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 8.33 | 8.74 | 8.70 | 8.56 | 8.41 | 8.37 | 8.20 | 8.12 | 8.00 | 7.87 | 7.88 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 8.61 | 12.74 | 10.52 | 7.45 | 6.09 | 4.98 | 5.61 | 3.05 | 0.15 | 4.52 | 9.27 |

## E1-CONC/run2 — 220 grab bodies in the window; relay thread identified

| signal | baseline mean (sd) | mean in grab bodies | magnitude (baseline sd) | first rise (s after grab start) |
| --- | --- | --- | --- | --- |
| busiest core % | 25.60 (6.76) | 55.18 | 4.38 | 0 |
| encoder dup+drop /s | 0.00 (0.04) | 0.00 | 0.0 | never |
| relay thread CPU % | 8.23 (0.82) | 8.62 | 0.47 | never |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 (0.00) | 0.00 | 0.0 | never |
| lost packets /s (heartbeat) | 0.33 (2.30) | 4.66 | 1.88 | 1 |

**Most:** busiest; **first:** busiest.

Aligned on the grab start (mean across grabs, by offset in s):

| offset s | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % | 40.85 | 61.19 | 77.69 | 52.60 | 55.45 | 51.47 | 27.67 | 25.17 | 27.85 | 30.14 | 24.55 |
| encoder dup+drop /s | 0.00 | 0.01 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relay thread CPU % | 8.37 | 8.78 | 8.94 | 8.70 | 8.46 | 8.57 | 8.13 | 8.02 | 8.46 | 8.17 | 8.50 |
| eno1 tx drops /s (qdisc+softnet+if) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lost packets /s (heartbeat) | 3.92 | 7.45 | 7.47 | 4.52 | 2.86 | 2.44 | 2.41 | 1.26 | 0.25 | 5.47 | 0.25 |

