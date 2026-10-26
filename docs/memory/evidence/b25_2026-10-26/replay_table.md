# B25 replay — B14's rule over every heartbeat with the link keys since G-A3 (from replay_output.json)

Rule: 2.4 GHz at once; RSSI <= -72 dBm held 10 s; tx <= 54 Mbps held 10 s; cleared after 30 s good; once a session unless the band changes; ticked every 500 ms on the host's clock, each heartbeat's reading held until the next.

| set | start (UTC) | heartbeats | band | RSSI min / median | tx min | lowest RSSI / tx held 10 s | length s | would show | reason | at s | shown for s | client's own bits (replay disagreements) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G-A3 | 2026-10-23T18:27Z | 348 | 5 | -69 / -68.0 | 130 | -69 / 195 | 698 | no | — | — | 0.0 | — |
| CL-B10 c1 | 2026-10-24T03:34Z | 110 | 5 | -68 / -68.0 | 195 | -68 / 260 | 222 | no | — | — | 0.0 | [0] (0) |
| CL-B10 c1 | 2026-10-24T03:38Z | 14 | 5 | -68 / -68.0 | 195 | -68 / 260 | 26 | no | — | — | 0.0 | [0] (0) |
| CL-B10 c1 | 2026-10-24T03:41Z | 18 | 5 | -67 / -67.0 | 234 | -67 / 260 | 35 | no | — | — | 0.0 | [0] (0) |
| CL-B10 c2 | 2026-10-23T18:44Z | 337 | 5 | -68 / -67 | 130 | -68 / 195 | 696 | no | — | — | 0.0 | [0] (0) |
| CL-B10 c3 | 2026-10-23T18:58Z | 346 | 5 | -68 / -68.0 | 175 | -68 / 195 | 696 | no | — | — | 0.0 | [0] (0) |
| CL-B10 c4 | 2026-10-24T03:53Z | 15 | 2.4 | -69 / -68 | 6 | -69 / 9 | 45 | **YES** | band 2.4 GHz | 0.0 | 44.8 | [1] (0) |
| CL-B10 c4 | 2026-10-24T03:54Z | 3 | 2.4 | -68 / -68 | 6 | None / None | 3 | **YES** | band 2.4 GHz | 0.0 | 3.1 | [1] (0) |
| CL-B10 c4 | 2026-10-24T03:54Z | 276 | 2.4 | -69 / -68.0 | 6 | -69 / 27 | 583 | **YES** | band 2.4 GHz | 0.0 | 582.7 | [1] (0) |
| CL-B10 c4 | 2026-10-24T04:04Z | 130 | 5 | -69 / -69.0 | 175 | -69 / 195 | 262 | no | — | — | 0.0 | [0] (0) |
| CL-B11 c1 | 2026-10-24T15:21Z | 118 | 5 | -68 / -67.0 | 130 | -68 / 195 | 236 | no | — | — | 0.0 | — |
| CL-B11 c1 | 2026-10-24T15:26Z | 220 | 5 | -69 / -68.0 | 130 | -68 / 195 | 440 | no | — | — | 0.0 | — |
| CL-B11 c2 | 2026-10-24T10:35Z | 339 | 5 | -67 / -66 | 234 | -67 / 260 | 698 | no | — | — | 0.0 | — |
| CL-B11 c3 | 2026-10-24T10:49Z | 347 | 5 | -67 / -67 | 260 | -67 / 260 | 696 | no | — | — | 0.0 | — |
| CL-B12 c1 | 2026-10-24T17:12Z | 92 | 5 | -69 / -69.0 | 130 | -69 / 195 | 184 | no | — | — | 0.0 | — |
| CL-B12 c1 | 2026-10-24T17:15Z | 77 | 5 | -70 / -69 | 130 | -70 / 195 | 153 | no | — | — | 0.0 | — |
| CL-B12 c1 | 2026-10-24T17:18Z | 156 | 5 | -69 / -69.0 | 97 | -69 / 195 | 312 | no | — | — | 0.0 | — |
| CL-B12 c2 | 2026-10-24T16:42Z | 335 | 5 | -70 / -69 | 117 | -69 / 130 | 696 | no | — | — | 0.0 | — |
| CL-B12 c3 | 2026-10-24T16:56Z | 347 | 5 | -69 / -69 | 130 | -69 / 195 | 696 | no | — | — | 0.0 | — |
| G-A4 | 2026-10-24T18:17Z | 348 | 5 | -70 / -69.0 | 130 | -70 / 195 | 698 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T19:24Z | 27 | 5 | -53 / -53 | 866 | -53 / 866 | 53 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T19:25Z | 45 | 5 | -52 / -52 | 780 | -52 / 866 | 88 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T19:27Z | 20 | 5 | -54 / -52.0 | 866 | -53 / 866 | 38 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T19:28Z | 188 | 5 | -52 / -52.0 | 650 | -52 / 780 | 376 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T19:35Z | 28 | 5 | -52 / -52.0 | 780 | -52 / 866 | 55 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T19:47Z | 217 | 5 | -57 / -56 | 468 | -56 / 520 | 435 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T19:55Z | 160 | 5 | -58 / -56.0 | 520 | -56 / 585 | 320 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T20:04Z | 269 | 5 | -59 / -56 | 585 | -56 / 650 | 538 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T20:14Z | 85 | 5 | -58 / -56 | 585 | -56 / 650 | 169 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T20:21Z | 1238 | 5 | -57 / -56.0 | 585 | -56 / 650 | 2484 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T21:02Z | 54 | 5 | -56 / -56.0 | 650 | -56 / 650 | 107 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-24T21:04Z | 1112 | 5 | -59 / -58.0 | 585 | -59 / 650 | 2241 | no | — | — | 0.0 | — |
| G4-S4 | 2026-10-25T01:20Z | 207 | 5 | -57 / -55 | 351 | -55 / 390 | 415 | no | — | — | 0.0 | — |
| CL-B13 c1a | 2026-10-25T22:01Z | 347 | 5 | -70 / -67 | 97 | -69 / 195 | 696 | no | — | — | 0.0 | — |
| CL-B13 c1 | 2026-10-25T22:39Z | 109 | 5 | -69 / -69 | 195 | -69 / 195 | 218 | no | — | — | 0.0 | — |
| CL-B13 c1 | 2026-10-25T22:43Z | 78 | 5 | -69 / -69.0 | 195 | -69 / 260 | 155 | no | — | — | 0.0 | — |
| CL-B13 c1 | 2026-10-25T22:46Z | 10 | 5 | -69 / -69.0 | 195 | -69 / 234 | 18 | no | — | — | 0.0 | — |
| CL-B13 c1 | 2026-10-25T22:47Z | 9 | 5 | -69 / -69 | 195 | -69 / 195 | 16 | no | — | — | 0.0 | — |
| CL-B13 c1 | 2026-10-25T22:47Z | 112 | 5 | -69 / -69.0 | 175 | -69 / 195 | 223 | no | — | — | 0.0 | — |
| CL-B13 c2 | 2026-10-25T22:54Z | 106 | 5 | -69 / -69.0 | 195 | -69 / 195 | 212 | no | — | — | 0.0 | — |
| CL-B13 c2 | 2026-10-25T22:58Z | 82 | 5 | -69 / -69.0 | 175 | -69 / 195 | 163 | no | — | — | 0.0 | — |
| CL-B13 c2 | 2026-10-25T23:01Z | 143 | 5 | -69 / -69 | 175 | -69 / 195 | 286 | no | — | — | 0.0 | — |
| CL-B13 c3a | 2026-10-25T23:12Z | 336 | 5 | -70 / -69.0 | 130 | -69 / 195 | 697 | no | — | — | 0.0 | — |
| CL-B13 c3b | 2026-10-25T23:27Z | 347 | 5 | -69 / -69 | 130 | -69 / 195 | 696 | no | — | — | 0.0 | — |
| G-A5 | 2026-10-26T03:10Z | 347 | 5 | -70 / -69 | 65 | -70 / 195 | 697 | no | — | — | 0.0 | — |

Gate: {"sessions": 45, "sessions_24": 3, "sessions_24_shown": 3, "sessions_24_not_shown": [], "sessions_5": 42, "sessions_5_shown": []}

5-GHz floors: {"rssi_lowest_held_10s": -70, "rssi_threshold_quiet": -71, "tx_lowest_held_10s": 130, "tx_threshold_quiet": 129}

The live log (supplement): 16 sessions, every one already held in an evidence file (0 added).

## Before G-A3, reference only (outside the gate)

| set | start (UTC) | heartbeats | band | RSSI min / median | tx min | lowest RSSI / tx held 10 s | length s | would show | reason | at s | shown for s | client's own bits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LINK-R1 (ref) | 2026-10-23T15:52Z | 346 | 5 | -69 / -68.0 | 130 | -69 / 195 | 694 | no | — | — | 0.0 | — |
| BENCH-R3 (ref) | 2026-10-22T20:24Z | 335 | 2.4 | -69 / -67 | 81 | -69 / 108 | 697 | **YES** | band 2.4 GHz | 0.0 | 696.8 | — |
| BENCH-R3 (ref) | 2026-10-22T20:39Z | 347 | 2.4 | -70 / -68 | 27 | -69 / 54 | 697 | **YES** | band 2.4 GHz | 0.0 | 696.6 | — |
| BENCH-R3 (ref) | 2026-10-22T20:53Z | 343 | 2.4 | -69 / -68 | 40 | -69 / 81 | 696 | **YES** | band 2.4 GHz | 0.0 | 696.2 | — |
| BENCH-R3 (ref) | 2026-10-22T21:08Z | 256 | 2.4 | -69 / -68.0 | 81 | -69 / 108 | 537 | **YES** | band 2.4 GHz | 0.0 | 537.5 | — |
| BENCH-R3 (ref) | 2026-10-22T21:17Z | 76 | 2.4 | -69 / -69.0 | 54 | -69 / 108 | 157 | **YES** | band 2.4 GHz | 0.0 | 157.1 | — |
| BENCH-R3 (ref) | 2026-10-22T21:19Z | 2 | 2.4 | -69 / -69.0 | 121 | None / None | 1 | **YES** | band 2.4 GHz | 0.0 | 0.9 | — |
| BENCH-R3 (ref) | 2026-10-22T21:22Z | 136 | 2.4 | -69 / -68.0 | 81 | -68 / 108 | 282 | **YES** | band 2.4 GHz | 0.0 | 281.5 | — |
| BENCH-R3 (ref) | 2026-10-22T21:27Z | 22 | 2.4 | -69 / -68.0 | 81 | -68 / 121 | 42 | **YES** | band 2.4 GHz | 0.0 | 42.4 | — |
| BENCH-R3 (ref) | 2026-10-22T21:27Z | 93 | 2.4 | -69 / -68 | 81 | -69 / 108 | 187 | **YES** | band 2.4 GHz | 0.0 | 187.2 | — |
| BENCH-R3 (ref) | 2026-10-22T21:31Z | 93 | 2.4 | -69 / -68 | 81 | -69 / 121 | 187 | **YES** | band 2.4 GHz | 0.0 | 187.4 | — |
| BENCH-R3 (ref) | 2026-10-22T21:37Z | 348 | 2.4 | -69 / -68.0 | 27 | -68 / 54 | 701 | **YES** | band 2.4 GHz | 0.0 | 700.7 | — |
| UX-R4 (ref) | 2026-10-22T20:24Z | 335 | 2.4 | -69 / -67 | 81 | -69 / 108 | 697 | **YES** | band 2.4 GHz | 0.0 | 696.8 | — |
| UX-R4 (ref) | 2026-10-22T20:39Z | 347 | 2.4 | -70 / -68 | 27 | -69 / 54 | 697 | **YES** | band 2.4 GHz | 0.0 | 696.6 | — |
| UX-R4 (ref) | 2026-10-22T20:53Z | 343 | 2.4 | -69 / -68 | 40 | -69 / 81 | 696 | **YES** | band 2.4 GHz | 0.0 | 696.2 | — |
| UX-R4 (ref) | 2026-10-22T21:08Z | 256 | 2.4 | -69 / -68.0 | 81 | -69 / 108 | 537 | **YES** | band 2.4 GHz | 0.0 | 537.5 | — |
| UX-R4 (ref) | 2026-10-22T21:17Z | 76 | 2.4 | -69 / -69.0 | 54 | -69 / 108 | 157 | **YES** | band 2.4 GHz | 0.0 | 157.1 | — |
| UX-R4 (ref) | 2026-10-22T21:19Z | 2 | 2.4 | -69 / -69.0 | 121 | None / None | 1 | **YES** | band 2.4 GHz | 0.0 | 0.9 | — |
| UX-R4 (ref) | 2026-10-22T21:22Z | 136 | 2.4 | -69 / -68.0 | 81 | -68 / 108 | 282 | **YES** | band 2.4 GHz | 0.0 | 281.5 | — |
| UX-R4 (ref) | 2026-10-22T21:27Z | 22 | 2.4 | -69 / -68.0 | 81 | -68 / 121 | 42 | **YES** | band 2.4 GHz | 0.0 | 42.4 | — |
| UX-R4 (ref) | 2026-10-22T21:27Z | 93 | 2.4 | -69 / -68 | 81 | -69 / 108 | 187 | **YES** | band 2.4 GHz | 0.0 | 187.2 | — |
| UX-R4 (ref) | 2026-10-22T21:31Z | 93 | 2.4 | -69 / -68 | 81 | -69 / 121 | 187 | **YES** | band 2.4 GHz | 0.0 | 187.4 | — |
| UX-R4 (ref) | 2026-10-22T21:37Z | 348 | 2.4 | -69 / -68.0 | 27 | -68 / 54 | 701 | **YES** | band 2.4 GHz | 0.0 | 700.7 | — |

(UX-R4's copy is BENCH-R3's same evening: the same 11 sessions.)

## Inputs

- G-A3: `docs/memory/evidence/g_a3_2026-10-23/runs/logs_run1/native_stream_heartbeat.log` 348 rows, sha256 `fd4c867a37ee8a23…`
- CL-B10 c1: `docs/memory/evidence/cl_b10_2026-10-23/runs/1_snes_5ghz_restart_guard/logs_run1/native_stream_heartbeat.log` 142 rows, sha256 `932909030db6d62e…`
- CL-B10 c2: `docs/memory/evidence/cl_b10_2026-10-23/runs/2_snes_blackout_both_state_stall/logs_run1/native_stream_heartbeat.log` 337 rows, sha256 `b9f8205404158263…`
- CL-B10 c3: `docs/memory/evidence/cl_b10_2026-10-23/runs/3_snes_blackout_down_state_stall/logs_run1/native_stream_heartbeat.log` 346 rows, sha256 `232f81cef671b802…`
- CL-B10 c4: `docs/memory/evidence/cl_b10_2026-10-23/runs/4_snes_24ghz_notice/logs_run1/native_stream_heartbeat.log` 424 rows, sha256 `08c852c75d6ecc39…`
- CL-B11 c1: `docs/memory/evidence/cl_b11_2026-10-24/runs/1_snes_5ghz_restart_guard_all_paths/logs_run1/native_stream_heartbeat.log` 338 rows, sha256 `d4c0f54e0daff601…`
- CL-B11 c2: `docs/memory/evidence/cl_b11_2026-10-24/runs/2_snes_blackout_both_fast_ready/logs_run1/native_stream_heartbeat.log` 339 rows, sha256 `0f8d190998224500…`
- CL-B11 c3: `docs/memory/evidence/cl_b11_2026-10-24/runs/3_snes_blackout_down_fast_ready/logs_run1/native_stream_heartbeat.log` 347 rows, sha256 `858f13fabff36bca…`
- CL-B12 c1: `docs/memory/evidence/cl_b12_2026-10-24/runs/1_snes_5ghz_two_home_presses/logs_run1/native_stream_heartbeat.log` 325 rows, sha256 `28f31bf05f6eff22…`
- CL-B12 c2: `docs/memory/evidence/cl_b12_2026-10-24/runs/2_snes_blackout_both_umbrella/logs_run1/native_stream_heartbeat.log` 335 rows, sha256 `c0eb059f65219966…`
- CL-B12 c3: `docs/memory/evidence/cl_b12_2026-10-24/runs/3_snes_blackout_down_umbrella/logs_run1/native_stream_heartbeat.log` 347 rows, sha256 `1b1cd1186578711c…`
- G-A4: `docs/memory/evidence/g_a4_2026-10-24/runs/logs_run1/native_stream_heartbeat.log` 348 rows, sha256 `2584ccf66c9bc7cb…`
- G4-S4: `docs/memory/evidence/g4_s4_2026-10-24/copies/logs/games/native_stream_heartbeat.log` 3650 rows, sha256 `f722b45f8651c0cc…`
- CL-B13 c1a: `docs/memory/evidence/cl_b13_2026-10-25/runs/1_snes_home_presses_restart_fast_attempt1_no_presses/logs_run1/native_stream_heartbeat.log` 347 rows, sha256 `e36b6de94114018c…`
- CL-B13 c1: `docs/memory/evidence/cl_b13_2026-10-25/runs/1_snes_home_presses_restart_fast/logs_run1/native_stream_heartbeat.log` 318 rows, sha256 `ebf602a30ebb7913…`
- CL-B13 c2: `docs/memory/evidence/cl_b13_2026-10-25/runs/2_snes_home_presses_no_flag/logs_run1/native_stream_heartbeat.log` 331 rows, sha256 `5b04e6975082b1d5…`
- CL-B13 c3a: `docs/memory/evidence/cl_b13_2026-10-25/runs/3a_snes_blackout_both_wan/logs_run1/native_stream_heartbeat.log` 336 rows, sha256 `430fbaf9faa3d814…`
- CL-B13 c3b: `docs/memory/evidence/cl_b13_2026-10-25/runs/3b_snes_blackout_down_wan/logs_run1/native_stream_heartbeat.log` 347 rows, sha256 `974c6bbd8729cdbd…`
- G-A5: `docs/memory/evidence/g_a5_2026-10-26/runs/logs_run1/native_stream_heartbeat.log` 347 rows, sha256 `5f16610314108c38…`
- LINK-R1 (ref): `docs/memory/evidence/link_r1_2026-10-23/runs/logs_run1/native_stream_heartbeat.log` 346 rows, sha256 `6ae11a8aace422d3…` (reference)
- BENCH-R3 (ref): `docs/memory/evidence/bench_r3_2026-10-22/record/logs_whole_run/native_stream_heartbeat.log` 2051 rows, sha256 `1b0e88a5469e4460…` (reference)
- UX-R4 (ref): `docs/memory/evidence/ux_r4_2026-10-23/session/logs/games/native_stream_heartbeat.log` 4105 rows, sha256 `797467bda89f7b43…` (reference)
- live (supplement): `logs/games/native_stream_heartbeat.log` 4455 rows, sha256 `064d500eab6755f5…`
