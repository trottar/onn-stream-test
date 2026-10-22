# LAN-R2 replay: through the real controller (LAN-R1's harness), offline, read-only

## 1. Flag absent

| span | client sessions | samples | recorded events | reproduced | HEAD vs tree |
| --- | ---: | ---: | ---: | --- | --- |
| UX-R1 Sunday (2026-10-20) | 41 | 1709 | 505 | exact | identical (2256) |
| UX-R2 last night (2026-10-21) | 12 | 1180 | 318 | exact | identical (1510) |
| BENCH-R1 01_loss-1_plain | 1 | 335 | 120 | exact | identical (456) |
| BENCH-R1 02_loss-1_lan_rule | 1 | 344 | 32 | 281 MISMATCH | identical (363) |
| BENCH-R1 03_loss-5_lan_rule | 1 | 344 | 58 | 222 MISMATCH | identical (364) |
| BENCH-R1 04_burst-50x20_lan_rule | 2 | 346 | 57 | 226 MISMATCH | identical (367) |

### 1b. Cells 2-4 ran with `PRIVYHUB_LAN_LOSS_RULE=1` live: their recorded run through LAN-R1's rule

| span | samples | recorded events | reproduced |
| --- | ---: | ---: | --- |
| BENCH-R1 02_loss-1_lan_rule | 344 | 32 | 1 mismatch |
| BENCH-R1 03_loss-5_lan_rule | 344 | 58 | 191 mismatch |
| BENCH-R1 04_burst-50x20_lan_rule | 346 | 57 | 195 mismatch |

## 2. `=1` (LAN-R1: unrec T 4 K 2)

| span | kind | sessions | asks | first ask | taken (rung path) | refused | the ladder's own transitions |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| UX-R1 Sunday (2026-10-20) | evening | 41 | 7 | 05:03:05 | 05:03:05 7000->6000; 05:06:07 6000->5500; 05:10:48 5500->5000; 05:20:52 7000->6000 | refused:hold_down 3 | — |
| UX-R2 last night (2026-10-21) | evening | 12 | 2 | 05:12:50 | — | refused:guard 2 | — |
| CL-B5 A pcm | clean | 1 | 0 | — | — | — | — |
| CL-B5 B opus | clean | 1 | 0 | — | — | — | — |
| CL-B5 L opus | clean | 1 | 0 | — | — | — | — |
| CL-B6 1 opus | clean | 1 | 0 | — | — | — | — |
| CL-B6 2 pcm | clean | 1 | 0 | — | — | — | — |
| CL-B7 pcm | clean | 1 | 0 | — | — | — | — |
| CL-B7 opus today | clean | 1 | 0 | — | — | — | — |
| CL-B7 opus lean | clean | 1 | 0 | — | — | — | — |
| G4-S3 (remote, 4000; no LAN part) | clean_remote | 5 | 0 | — | — | — | — |
| G8-S1 03 loss-1 off | g8 | 2 | 6 | 20:46:14 | 20:46:14 7000->6000; 20:49:21 6000->5500; 20:51:40 5500->5000 | refused:hold_down 3 | — |
| G8-S1 04 loss-1 on | g8 | 2 | 7 | 20:59:52 | 21:01:28 7000->6000; 21:05:45 6000->5500; 21:08:02 5500->5000 | refused:guard 1, refused:hold_down 3 | — |
| G8-S1 05 loss-5 off | g8 | 2 | 15 | 21:14:17 | 21:14:58 7000->6000; 21:17:04 6000->5500; 21:19:11 5500->5000 | refused:guard 2, refused:hold_down 10 | — |
| G8-S1 06 loss-5 on | g8 | 2 | 2 | 00:32:18 | — | refused:guard 2 | 00:33:38 7000->5000 recovery_escalation |
| G8-S1 07 burst-50x20 off | g8 | 2 | 5 | 00:48:56 | 00:49:33 7000->6000; 00:52:44 6000->5500 | refused:guard 1, refused:hold_down 2 | — |
| G8-S1 08 burst-50x20 on | g8 | 2 | 0 | — | — | — | — |
| G8-S1 21 delay-50+loss-1 off | g8 | 2 | 13 | 04:04:32 | 04:05:38 7000->6000; 04:07:43 6000->5500; 04:09:49 5500->5000 | refused:guard 2, refused:hold_down 8 | — |
| G8-S1 22 delay-50+loss-1 on | g8 | 2 | 10 | 04:18:48 | 04:19:56 7000->6000; 04:22:49 6000->5500; 04:25:22 5500->5000 | refused:guard 2, refused:hold_down 5 | — |
| BENCH-R1 01_loss-1_plain | cell | 1 | 9 | 02:34:48 | 02:35:14 7000->6000; 02:39:15 6000->5500; 02:41:39 5500->5000 | refused:guard 1, refused:hold_down 5 | — |
| BENCH-R1 02_loss-1_lan_rule | cell | 1 | 6 | 02:49:37 | 02:50:17 7000->6000; 02:53:30 6000->5500; 02:56:59 5500->5000 | refused:guard 1, refused:hold_down 2 | — |
| BENCH-R1 03_loss-5_lan_rule | cell | 1 | 15 | 03:03:34 | 03:04:14 7000->6000; 03:06:21 6000->5500; 03:08:28 5500->5000 | refused:guard 2, refused:hold_down 10 | — |
| BENCH-R1 04_burst-50x20_lan_rule | cell | 2 | 15 | 03:18:03 | 03:18:44 7000->6000; 03:20:56 6000->5500; 03:23:07 5500->5000 | refused:guard 2, refused:hold_down 10 | — |

## 2. `=bidir` (LAN-R2: unrec T 4 K 2 AND >= 2 uplink silences >= 400 ms in each window)

| span | kind | sessions | asks | first ask | taken (rung path) | refused | the ladder's own transitions |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| UX-R1 Sunday (2026-10-20) | evening | 41 | 6 | 05:06:09 | 05:06:09 7000->6000; 05:10:52 6000->5500; 05:20:52 7000->6000 | refused:hold_down 3 | — |
| UX-R2 last night (2026-10-21) | evening | 12 | 0 | — | — | — | — |
| CL-B5 A pcm | clean | 1 | 0 | — | — | — | — |
| CL-B5 B opus | clean | 1 | 0 | — | — | — | — |
| CL-B5 L opus | clean | 1 | 0 | — | — | — | — |
| CL-B6 1 opus | clean | 1 | 0 | — | — | — | — |
| CL-B6 2 pcm | clean | 1 | 0 | — | — | — | — |
| CL-B7 pcm | clean | 1 | 0 | — | — | — | — |
| CL-B7 opus today | clean | 1 | 0 | — | — | — | — |
| CL-B7 opus lean | clean | 1 | 0 | — | — | — | — |
| G4-S3 (remote, 4000; no LAN part) | clean_remote | 5 | 0 | — | — | — | — |
| G8-S1 03 loss-1 off | g8 | 2 | 0 | — | — | — | — |
| G8-S1 04 loss-1 on | g8 | 2 | 0 | — | — | — | — |
| G8-S1 05 loss-5 off | g8 | 2 | 0 | — | — | — | — |
| G8-S1 06 loss-5 on | g8 | 2 | 0 | — | — | — | 00:33:38 7000->5000 recovery_escalation |
| G8-S1 07 burst-50x20 off | g8 | 2 | 4 | 00:48:56 | 00:49:33 7000->6000; 00:52:44 6000->5500 | refused:guard 1, refused:hold_down 1 | — |
| G8-S1 08 burst-50x20 on | g8 | 2 | 0 | — | — | — | — |
| G8-S1 21 delay-50+loss-1 off | g8 | 2 | 0 | — | — | — | — |
| G8-S1 22 delay-50+loss-1 on | g8 | 2 | 0 | — | — | — | — |
| BENCH-R1 01_loss-1_plain | cell | 1 | 0 | — | — | — | — |
| BENCH-R1 02_loss-1_lan_rule | cell | 1 | 0 | — | — | — | — |
| BENCH-R1 03_loss-5_lan_rule | cell | 1 | 0 | — | — | — | 03:09:02 7000->6000 capacity_mild; 03:12:15 6000->5500 capacity_mild |
| BENCH-R1 04_burst-50x20_lan_rule | cell | 2 | 0 | — | — | — | 03:26:45 7000->6000 capacity_mild |

## 3. The false-trigger table (asks; must be 0)

| span | `=1` | `=bidir` |
| --- | ---: | ---: |
| CL-B5 A pcm | 0 | 0 |
| CL-B5 B opus | 0 | 0 |
| CL-B5 L opus | 0 | 0 |
| CL-B6 1 opus | 0 | 0 |
| CL-B6 2 pcm | 0 | 0 |
| CL-B7 pcm | 0 | 0 |
| CL-B7 opus today | 0 | 0 |
| CL-B7 opus lean | 0 | 0 |
| G4-S3 (remote, 4000; no LAN part) | 0 | 0 |
| BENCH-R1 01_loss-1_plain | 9 | 0 |
| BENCH-R1 02_loss-1_lan_rule | 6 | 0 |

Shown, not counted as false (random / burst downlink loss at 5 % and 50x20; the ladder may act there): BENCH-R1 03_loss-5_lan_rule: `=1` 15, `=bidir` 0; BENCH-R1 04_burst-50x20_lan_rule: `=1` 15, `=bidir` 0

**Sunday:** `=1` first ask 05:03:05 (taken: 05:03:05 7000->6000; 05:06:07 6000->5500; 05:10:48 5500->5000; 05:20:52 7000->6000); `=bidir` first ask 05:06:09 (taken: 05:06:09 7000->6000; 05:10:52 6000->5500; 05:20:52 7000->6000).
