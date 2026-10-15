# E4-S1 — the known-good reference for this host on the adopted state, 2026-10-09; no floor and no lower-tier claim.

The ROADMAP's four-row form (heaviest = the highest host-CPU row other than the contended one: E1-PS1-1080P). E2 (2026-10-06, before E3's adoptions) in brackets.

| workload | row | host CPU % (p95) | busiest core p95 % | PrivyHub CPU (% of one core) | PrivyHub PSS MB | socket W | Tctl °C | stream |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| idle | IDLE | 1.2 (1.8) [E2 0.9] | 3.0 [E2 3.0] | ~0 = 0.0 [E2 0.0] | companion 26 + range_server 14 = 40 [E2 40] | 5.3 [E2 4.7] | 34 [E2 33] | — |
| streaming | PS1-STREAM | 10.9 (12.9) [E2 11.7] | 29.9 [E2 28.7] | companion 25.0 + retroarch 33.5 + encoder 36.0 = 94.6 [E2 94.3] | companion 38 + retroarch 230 + encoder 72 + range_server 14 = 354 [E2 355] | 20.1 [E2 20.4] | 61 [E2 60] | 59.53 fps, loss 169.2/min [E2 59.81 fps, 32.3/min] |
| contended | CONC | 21.4 (29.4) [E2 20.5 / 21.9] | 64.7 [E2 63.4 / 65.7] | companion 26.0 + retroarch 35.8 + encoder 35.2 + epg 75.4 = 172.4 [E2 184.2 / 191.3] | companion 47 + retroarch 230 + encoder 72 + epg 493 + range_server 14 = 856 [E2 971 / 991] | 25.7 [E2 25.9 / 25.3] | 68 [E2 70 / 70] | 58.46 fps, loss 812.9/min [E2 56.53 / 56.57 fps, 1,622 / 1,602/min] |
| heaviest | PS1-1080P | 15.3 (17.1) [E2 13.8] | 27.8 [E2 28.3] | companion 29.1 + retroarch 36.5 + encoder 73.0 = 138.6 [E2 126.2] | companion 39 + retroarch 234 + encoder 74 + range_server 14 = 362 [E2 369] | 22.0 [E2 20.6] | 64 [E2 62] | 59.63 fps, loss 101.9/min [E2 59.87 fps, 22.6/min] |

Every row:

| row | host CPU % (p95) | busiest core p95 | PrivyHub CPU total | PrivyHub PSS MB | socket W | Tctl | rendered fps | loss/min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IDLE | 1.2 (1.8) | 3.0 | 0.0 | 40 | 5.3 | 34 | — | — |
| PS1-LOCAL | 5.3 (6.8) | 23.8 | 33.1 | 293 | 14.5 | 51 | — | — |
| PS1-STREAM | 10.9 (12.9) | 29.9 | 94.6 | 354 | 20.1 | 61 | 59.53 | 169.2 |
| PS1-1080P | 15.3 (17.1) | 27.8 | 138.6 | 362 | 22.0 | 64 | 59.63 | 101.9 |
| META | 10.8 (17.3) | 58.6 | 74.2 | 535 | 15.8 | 59 | — | — |
| VOD | 1.2 (1.7) | 3.0 | 0.1 | 42 | 4.9 | 33 | — | — |
| SNES-STREAM | 7.4 (8.8) | 16.5 | 60.1 | 230 | 15.2 | 49 | 58.74 | 54.0 |
| CONC | 21.4 (29.4) | 64.7 | 172.4 | 856 | 25.7 | 68 | 58.46 | 812.9 |
