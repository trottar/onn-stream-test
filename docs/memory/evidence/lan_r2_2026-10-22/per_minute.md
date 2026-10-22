# LAN-R2 — per-minute signals, random loss against Sunday (`lan_r2_analysis.py`)

Per group of minutes (the means / medians of per-minute values). `up` = uplink silences >= 250 ms (the host's control-gap log); `out gap` = the client's output gap (ladder sample); `audio gap` = the client's audio arrival gap (heartbeat window); `unrec max/report` = the most FEC-unrecoverable groups in one 2-s report.

| group | minutes | unrec / min | unrec max / report | up / min | min with up >= 400 | out gap max (median) | min out gap >= 400 | audio gap max (median) | min audio gap >= 150 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BENCH-R1 01_loss-1_plain | 12 | 24.17 | 14 | 0.67 | 3 | 47 | 1 | 192 | 7 |
| BENCH-R1 02_loss-1_lan_rule | 13 | 14.69 | 6 | 1.69 | 2 | 50 | 0 | 115 | 4 |
| BENCH-R1 03_loss-5_lan_rule | 12 | 270.67 | 19 | 3.92 | 5 | 69 | 0 | 223 | 8 |
| BENCH-R1 04_burst-50x20_lan_rule | 13 | 61.15 | 26 | 6.15 | 9 | 61 | 0 | 214 | 13 |
| Sunday step 04:56-05:05 | 10 | 8.3 | 3 | 3.8 | 7 | 68 | 0 | 187 | 6 |
| Sunday bursts (05:06, 05:09-05:11, 05:20-05:21) | 6 | 36.33 | 14 | 23.83 | 6 | 88 | 0 | 831 | 6 |
| Sunday clean minutes (LAN-R1's definition) | 34 | 5.85 | 3 | 1.41 | 7 | 63 | 0 | 122 | 10 |
| Last night clean minutes | 31 | 5.87 | 3 | 0.26 | 0 | 58 | 0 | 128 | 9 |
| CL-B5 A pcm | 11 | 2.82 | 2 | 5.73 | 4 | 40 | 0 | 106 | 1 |
| CL-B5 B opus | 11 | 4.18 | 2 | 6.73 | 9 | 41 | 0 | 102 | 0 |
| CL-B5 L opus | 11 | 2.73 | 3 | 7.27 | 9 | 46 | 0 | 134 | 4 |
| CL-B6 1 opus | 11 | 2.18 | 1 | 7.91 | 9 | 54 | 0 | 112 | 2 |
| CL-B6 2 pcm | 11 | 4.55 | 2 | 1.64 | 2 | 54 | 0 | 122 | 4 |
| CL-B7 pcm | 11 | 2.09 | 2 | 3.45 | 5 | 39 | 0 | 99 | 4 |
| CL-B7 opus today | 11 | 3.91 | 2 | 0.45 | 1 | 36 | 0 | 138 | 3 |
| CL-B7 opus lean | 10 | 4.3 | 3 | 0.3 | 0 | 46 | 0 | 113 | 0 |
| G4-S3 (remote, 4000; no LAN part) | 10 | 0.1 | 1 | 0.0 | 0 | 25 | 0 | 55 | 1 |

Coverage (samples / joined to a heartbeat): UX-R1 Sunday (2026-10-20): 1709/1686; UX-R2 last night (2026-10-21): 1180/1172; CL-B5 A pcm: 298/298; CL-B5 B opus: 299/299; CL-B5 L opus: 299/299; CL-B6 1 opus: 298/298; CL-B6 2 pcm: 299/299; CL-B7 pcm: 299/299; CL-B7 opus today: 298/298; CL-B7 opus lean: 299/299; G4-S3 (remote, 4000; no LAN part): 287/285; BENCH-R1 01_loss-1_plain: 335/331; BENCH-R1 02_loss-1_lan_rule: 344/344; BENCH-R1 03_loss-5_lan_rule: 344/343; BENCH-R1 04_burst-50x20_lan_rule: 343/341
