# G5-S4 replay — the remote rung cap over G4-S1 (open loop on the reports; arithmetic, not results)

## 1. The target per tick

| run | cap | rules | reports on the remote path: at 7000 / 5000 / 4000 | on the LAN path | the move to the cap (session, elapsed) | other transitions | clamps (rows with `source: remote_cap`): moves / blocked increases | max level on the remote path after the move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 (overlay) | 4000 | off | 30 / 0 / 298 | — | 1: 61 s, 7000→4000; 2: 323 s, 7000→4000 | — | 2 / 111 | 4000 |
| G4-S1 run 1 (overlay) | 4000 | on | 30 / 0 / 298 | — | 1: 61 s, 7000→4000; 2: 323 s, 7000→4000 | — | 2 / 0 | 4000 |
| G4-S1 run 1 (overlay) | 5000 | off | 30 / 298 / 0 | — | 1: 61 s, 7000→5000; 2: 323 s, 7000→5000 | — | 2 / 111 | 5000 |
| G4-S1 run 1 (overlay) | 5000 | on | 30 / 298 / 0 | — | 1: 61 s, 7000→5000; 2: 323 s, 7000→5000 | — | 2 / 0 | 5000 |
| G4-S1 run 2 (overlay, then a LAN setup) | 4000 | off | 28 / 0 / 124 | 7000 ×105 | 1: 61 s, 7000→4000 | — | 1 / 32 | 4000 |
| G4-S1 run 2 (overlay, then a LAN setup) | 4000 | on | 28 / 0 / 124 | 7000 ×105 | 1: 61 s, 7000→4000 | — | 1 / 0 | 4000 |
| G4-S1 run 2 (overlay, then a LAN setup) | 5000 | off | 28 / 124 / 0 | 7000 ×105 | 1: 61 s, 7000→5000 | — | 1 / 32 | 5000 |
| G4-S1 run 2 (overlay, then a LAN setup) | 5000 | on | 28 / 124 / 0 | 7000 ×105 | 1: 61 s, 7000→5000 | — | 1 / 0 | 5000 |

Checks: every move is on a remote path; no remote transition above the cap; the LAN path stays at 7000 (no effect).

-> PASS

## 2. The wire rate and the data per hour, as arithmetic

| level | wire rate (Mbit/s) | source | GB / h at that rate | overlay, scaled ×(11.42/8.60) | GB / h | overlay, +(11.42−8.60) | GB / h |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7000 | 8.60 | C5-M3 measured | 3.87 | 11.42 | 5.14 | 11.42 | 5.14 |
| 5000 | 6.20 | L1 estimate (not measured) | 2.79 | 8.23 | 3.70 | 9.02 | 4.06 |
| 4000 | 5.02 | C5-M3 measured | 2.26 | 6.67 | 3.00 | 7.84 | 3.53 |

G4-S1 run 1's measured 11.42 Mbit/s at 7000 is 5.14 GB / h (G4-S1 §9: about 5.1).

### The replayed mix on each run's remote path (time-weighted over the reports, the first minute at 7000 included)

| run | cap | rules | reports on the remote path | share at the cap | implied wire (C5-M3 basis) | GB / h | implied overlay (scaled) | GB / h | implied overlay (added) | GB / h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G4-S1 run 1 (overlay) | 4000 | off | 328 | 91 % | 5.35 | 2.41 | 7.10 | 3.20 | 8.17 | 3.68 |
| G4-S1 run 1 (overlay) | 4000 | on | 328 | 91 % | 5.35 | 2.41 | 7.10 | 3.20 | 8.17 | 3.68 |
| G4-S1 run 1 (overlay) | 5000 | off | 328 | 91 % | 6.42 | 2.89 | 8.52 | 3.84 | 9.24 | 4.16 |
| G4-S1 run 1 (overlay) | 5000 | on | 328 | 91 % | 6.42 | 2.89 | 8.52 | 3.84 | 9.24 | 4.16 |
| G4-S1 run 2 (overlay, then a LAN setup) | 4000 | off | 152 | 82 % | 5.68 | 2.56 | 7.54 | 3.39 | 8.50 | 3.82 |
| G4-S1 run 2 (overlay, then a LAN setup) | 4000 | on | 152 | 82 % | 5.68 | 2.56 | 7.54 | 3.39 | 8.50 | 3.82 |
| G4-S1 run 2 (overlay, then a LAN setup) | 5000 | off | 152 | 82 % | 6.64 | 2.99 | 8.82 | 3.97 | 9.46 | 4.26 |
| G4-S1 run 2 (overlay, then a LAN setup) | 5000 | on | 152 | 82 % | 6.64 | 2.99 | 8.82 | 3.97 | 9.46 | 4.26 |

Arithmetic on recorded inputs at 7000; the reports a capped stream would have produced are not these. The data volume at the cap is for the first off-site run with it to measure (G4-S2); the picture at the cap is the user's judgement.

