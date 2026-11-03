# B36 dry run against TRIP-R2

## 1. TRIP-R2 §1's restart table, cell for cell

| restart | cell | TRIP-R2 | diag_read | same |
| --- | --- | --- | --- | --- |
| 01:20:44 | session | 14 | 14 | yes |
| 01:20:44 | title | football | PS1 football (Blitz) | yes |
| 01:20:44 | rung before → after | 4000 → 4000 | 4000 → 4000 | yes |
| 01:20:44 | last step-up Δt | 397 s | (none in the session; 397 s earlier) | yes |
| 01:20:44 | client's trigger | surface | surface | yes |
| 01:20:44 | paused ms | 1720 | 1720 | yes |
| 01:20:44 | away ms | 1787 | 1787 | yes |
| 01:20:44 | the seconds before (numbers) | silence 1736 | silences 1736 | yes |
| 03:26:05 | session | 20 | 20 | yes |
| 03:26:05 | title | kart | PS1 kart racer | yes |
| 03:26:05 | rung before → after | 4000 → 4000 | 4000 → 4000 | yes |
| 03:26:05 | last step-up Δt | (none in the session) | (none in the session; 6511 s earlier) | yes |
| 03:26:05 | client's trigger | surface | surface | yes |
| 03:26:05 | paused ms | 4511 | 4511 | yes |
| 03:26:05 | away ms | 8582 | 8582 | yes |
| 03:26:05 | the seconds before (numbers) | silence 7467 | silences 283 / 7467 | yes |
| 04:19:21 | session | 25 | 25 | yes |
| 04:19:21 | title | golf | PS1 golf | yes |
| 04:19:21 | rung before → after | 4000 → 4000 | 4000 → 4000 | yes |
| 04:19:21 | last step-up Δt | (none in the session) | (none in the session; 1956 s earlier) | yes |
| 04:19:21 | client's trigger | surface | surface | yes |
| 04:19:21 | paused ms | 1877 | 1877 | yes |
| 04:19:21 | away ms | 2027 | 2027 | yes |
| 04:19:21 | the seconds before (numbers) | stall 419; silence 1918 | stall 419; silences 1918 | yes |
| 04:30:12 | session | 26 | 26 | yes |
| 04:30:12 | title | golf | PS1 golf | yes |
| 04:30:12 | rung before → after | 6000 → 4000 | 6000 → 4000 | yes |
| 04:30:12 | last step-up Δt | 95 s | 95 s | yes |
| 04:30:12 | client's trigger | surface | surface | yes |
| 04:30:12 | paused ms | 2070 | 2070 | yes |
| 04:30:12 | away ms | 1039 | 1039 | yes |
| 04:30:12 | the seconds before (numbers) | stall 464; gaps 292 / 303 / 495 | stall 464; silences 292 / 303 / 495 | yes |
| 04:34:41 | session | 31, never PLAYING | (none PLAYING) | NO |
| 04:34:41 | title | golf | PS1 golf | yes |
| 04:34:41 | rung before → after | 4000 → 4000 | 4000 → 4000 | yes |
| 04:34:41 | last step-up Δt | 363 s | (none in the session; 363 s earlier) | yes |
| 04:34:41 | client's trigger | surface | surface | yes |
| 04:34:41 | paused ms | 767 | 767 | yes |
| 04:34:41 | away ms | 1188 | 1188 | yes |
| 04:34:41 | the seconds before (numbers) | silence 1190 | silences 1190 | yes |
| 05:19:35 | session | 35 | 35 | yes |
| 05:19:35 | title | brawler | PS1 brawler | yes |
| 05:19:35 | rung before → after | 4000 → 4000 | 4000 → 4000 | yes |
| 05:19:35 | last step-up Δt | (none in the session) | (none in the session; 178 s earlier) | yes |
| 05:19:35 | client's trigger | None | None | yes |
| 05:19:35 | paused ms | None | None | yes |
| 05:19:35 | away ms | None | None | yes |
| 05:19:35 | the seconds before (numbers) | silence 16079 | silences 16079 | yes |

**47 / 48 cells the same; 6 / 6 restart times found.**

## 2. TRIP-R2's sessions.tsv against diag_read's sessions

Sessions: TRIP-R2 36, diag_read 36. Cells compared: 900 (25 columns x 36 sessions); **different: 0**.


## 3. The keeper's chunks joined against TRIP-R2's copies/ (byte prefix)

| log | copies bytes | joined bytes | copies a prefix of joined |
| --- | --- | --- | --- |
| native_stream_recovery.log | 58866 | 58866 | yes |
| adaptive_bitrate_shadow.jsonl | 3381099 | 3381099 | yes |
| native_stream_heartbeat.log | 4905642 | 4905642 | yes |
| native_stream_ctrl_gaps.log | 8817 | 8817 | yes |
| native_frame_sizes.jsonl | 5343380 | 5343380 | yes |
| host_resource_samples.jsonl | 1040992 | 1083689 | yes |
| wan_sessions.jsonl | 82629 | 82629 | yes |
| decoder reports | 36 files | 36 reports | (count) |
