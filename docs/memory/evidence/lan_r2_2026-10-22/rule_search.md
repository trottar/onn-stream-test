# LAN-R2 — the rule search: LAN-R1's T 4 K 2 AND a second term (`lan_r2_analysis.py`)

Base (LAN-R1, one signal): cells 1-4 episodes {'BENCH-R1 01_loss-1_plain': 20, 'BENCH-R1 02_loss-1_lan_rule': 10, 'BENCH-R1 03_loss-5_lan_rule': 4, 'BENCH-R1 04_burst-50x20_lan_rule': 27}; clean windows 0; Sunday first 05:03:05.

| second term | p | cell 1 | cell 2 | cell 3 | cell 4 | clean windows | last night clean (false minutes) | Sunday first | Sunday minutes | passes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| uplink silences >= G ms in the window >= N | 250/1 | 9 | 7 | 8 | 25 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 250/2 | 1 | 3 | 14 | 16 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 250/3 | 0 | 1 | 10 | 14 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 300/1 | 8 | 4 | 9 | 19 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 300/2 | 0 | 2 | 13 | 16 | 0 | — | 05:06:07 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 300/3 | 0 | 0 | 4 | 6 | 0 | — | 05:06:07 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 400/1 | 5 | 1 | 4 | 13 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 400/2 | 0 | 0 | 7 | 9 | 0 | — | 05:06:07 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 400/3 | 0 | 0 | 2 | 2 | 0 | — | 05:06:55 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 500/1 | 1 | 1 | 5 | 9 | 0 | — | 05:06:07 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 500/2 | 0 | 0 | 2 | 3 | 0 | — | 05:06:09 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 500/3 | 0 | 0 | 0 | 2 | 0 | — | 05:06:55 | 05:06, 05:07, 05:10, 05:21 |  |
| uplink silences >= G ms in the window >= N | 600/1 | 0 | 0 | 1 | 7 | 0 | — | 05:06:07 | 05:06, 05:07, 05:10, 05:20, 05:21 |  |
| uplink silences >= G ms in the window >= N | 600/2 | 0 | 0 | 0 | 0 | 0 | — | 05:06:55 | 05:06, 05:07, 05:21 |  |
| uplink silences >= G ms in the window >= N | 600/3 | 0 | 0 | 0 | 0 | 0 | — | 05:06:59 | 05:06, 05:07, 05:21 |  |
| uplink silences >= G ms in the window >= N | 800/1 | 0 | 0 | 0 | 3 | 0 | — | 05:06:07 | 05:06, 05:07, 05:10, 05:21 |  |
| uplink silences >= G ms in the window >= N | 800/2 | 0 | 0 | 0 | 0 | 0 | — | 05:21:40 | 05:21 |  |
| uplink silences >= G ms in the window >= N | 800/3 | 0 | 0 | 0 | 0 | 0 | — | — | — |  |
| client output gap max in the window >= X ms | 150 | 1 | 0 | 0 | 0 | 0 | — | 05:10:52 | 05:10, 05:11 |  |
| client output gap max in the window >= X ms | 200 | 1 | 0 | 0 | 0 | 0 | — | 05:10:52 | 05:10, 05:11 |  |
| client output gap max in the window >= X ms | 250 | 1 | 0 | 0 | 0 | 0 | — | — | — |  |
| client output gap max in the window >= X ms | 300 | 1 | 0 | 0 | 0 | 0 | — | — | — |  |
| client output gap max in the window >= X ms | 400 | 1 | 0 | 0 | 0 | 0 | — | — | — |  |
| client output gap max in the window >= X ms | 600 | 1 | 0 | 0 | 0 | 0 | — | — | — |  |
| client output gap max in the window >= X ms | 1000 | 0 | 0 | 0 | 0 | 0 | — | — | — |  |
| audio arrival gap max in the window >= Y ms | 80 | 19 | 9 | 7 | 27 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| audio arrival gap max in the window >= Y ms | 100 | 15 | 4 | 8 | 27 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| audio arrival gap max in the window >= Y ms | 150 | 12 | 3 | 6 | 26 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| audio arrival gap max in the window >= Y ms | 200 | 10 | 0 | 8 | 13 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| audio arrival gap max in the window >= Y ms | 300 | 6 | 0 | 0 | 2 | 0 | — | 05:06:07 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| audio arrival gap max in the window >= Y ms | 500 | 1 | 0 | 0 | 0 | 0 | — | 05:10:55 | 05:10, 05:11, 05:20, 05:21 |  |
| one report holds >= Z of the window's unrec | 2 | 20 | 10 | 4 | 27 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| one report holds >= Z of the window's unrec | 3 | 16 | 5 | 4 | 27 | 0 | — | 05:03:05 | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| one report holds >= Z of the window's unrec | 4 | 10 | 2 | 4 | 20 | 0 | — | 05:06:55 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| one report holds >= Z of the window's unrec | 6 | 7 | 2 | 4 | 19 | 0 | — | 05:06:55 | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 |  |
| one report holds >= Z of the window's unrec | 8 | 4 | 0 | 4 | 10 | 0 | — | 05:10:55 | 05:10, 05:11, 05:20, 05:21 |  |
