# §2 The threshold search (T per 10-s window of 5 evaluated reports; K consecutive windows)

Clean minutes of last night by the stated definition: 31 of 43 (04:43, 04:44, 04:45, 04:46, 04:47, 04:48, 04:49, 04:50, 04:51, 04:52, 04:53, 04:55, 04:56, 04:57, 04:58, 04:59, 05:00, 05:01, 05:02, 05:03, 05:04, 05:05, 05:06, 05:13, 05:18, 05:19, 05:20, 05:21, 05:23, 05:24, 05:25).

## Per-window distributions (sum over 5 evaluated reports)

| span | metric | windows | median | p90 | p99 | max |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| UX-R1 Sunday (2026-10-20) | lost | 330 | 4 | 17 | 186 | 2156 |
| UX-R1 Sunday (2026-10-20) | unrec | 330 | 1 | 3 | 12 | 33 |
| UX-R2 last night (2026-10-21) | lost | 233 | 4 | 14 | 53 | 89 |
| UX-R2 last night (2026-10-21) | unrec | 233 | 1 | 3 | 6 | 8 |
| CL-B5 A pcm | lost | 59 | 0 | 10 | 15 | 16 |
| CL-B5 A pcm | unrec | 59 | 0 | 2 | 2 | 3 |
| CL-B5 B opus | lost | 59 | 2 | 8 | 98 | 103 |
| CL-B5 B opus | unrec | 59 | 1 | 2 | 3 | 3 |
| CL-B5 L opus | lost | 59 | 0 | 8 | 115 | 253 |
| CL-B5 L opus | unrec | 59 | 0 | 2 | 3 | 3 |
| CL-B6 1 opus | lost | 59 | 0 | 6 | 12 | 14 |
| CL-B6 1 opus | unrec | 59 | 0 | 1 | 2 | 3 |
| CL-B6 2 pcm | lost | 59 | 3 | 12 | 98 | 124 |
| CL-B6 2 pcm | unrec | 59 | 1 | 2 | 3 | 3 |
| CL-B7 pcm | lost | 59 | 0 | 7 | 14 | 18 |
| CL-B7 pcm | unrec | 59 | 0 | 1 | 2 | 2 |
| CL-B7 opus today | lost | 59 | 2 | 11 | 21 | 75 |
| CL-B7 opus today | unrec | 59 | 0 | 2 | 3 | 4 |
| CL-B7 opus lean | lost | 59 | 1 | 11 | 129 | 150 |
| CL-B7 opus lean | unrec | 59 | 0 | 2 | 3 | 3 |
| G4-S3 (remote, 4000; no LAN part) | lost | 56 | 0 | 0 | 0 | 2 |
| G4-S3 (remote, 4000; no LAN part) | unrec | 56 | 0 | 0 | 0 | 1 |

## Does any (T, K) fire on Sunday before 05:06 with 0 false triggers?

- (T, K) pairs with 0 false triggers in every clean window and a Sunday firing: 71
- of those, firing on Sunday between 04:51 and 05:06:00: **2**
- lost: the pre-05:06 firing with the fewest false triggers is T 5 K 5 (first 2026-10-20T04:45:09.820Z): 4 false triggers ({'CL-B6 2 pcm': 1}, last night's clean minutes ['04:59', '05:03', '05:06'])
- unrec: the pre-05:06 firing with the fewest false triggers is T 3 K 3 (first 2026-10-20T05:01:38.823Z): 0 false triggers ({}, last night's clean minutes [])

## The zero-false-trigger pairs, earliest Sunday firing first (top 25)

| metric | T | K | Sunday first fire | Sunday fire minutes | last night fire minutes (none clean) |
| --- | ---: | ---: | --- | --- | --- |
| lost | 10 | 5 | 2026-10-20T04:45:23.906Z | 04:45, 05:06, 05:07, 05:21 | — |
| unrec | 3 | 3 | 2026-10-20T05:01:38.823Z | 05:01, 05:10, 05:11, 05:13, 05:21 | — |
| unrec | 4 | 2 | 2026-10-20T05:03:05.138Z | 05:03, 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 | — |
| lost | 25 | 3 | 2026-10-20T05:06:17.982Z | 05:06, 05:07, 05:10, 05:11, 05:21 | — |
| lost | 20 | 3 | 2026-10-20T05:06:17.982Z | 05:06, 05:07, 05:10, 05:11, 05:21 | — |
| lost | 15 | 3 | 2026-10-20T05:06:17.982Z | 05:06, 05:07, 05:10, 05:11, 05:21 | — |
| lost | 25 | 4 | 2026-10-20T05:06:35.062Z | 05:06, 05:07, 05:21 | — |
| lost | 20 | 4 | 2026-10-20T05:06:35.062Z | 05:06, 05:07, 05:21 | — |
| lost | 15 | 4 | 2026-10-20T05:06:35.062Z | 05:06, 05:07, 05:10, 05:21 | — |
| lost | 5 | 9 | 2026-10-20T05:06:39.219Z | 05:06, 05:07, 05:11 | — |
| lost | 25 | 5 | 2026-10-20T05:06:53.759Z | 05:06, 05:07, 05:21 | — |
| lost | 20 | 5 | 2026-10-20T05:06:53.759Z | 05:06, 05:07, 05:21 | — |
| lost | 15 | 5 | 2026-10-20T05:06:53.759Z | 05:06, 05:07, 05:21 | — |
| unrec | 10 | 1 | 2026-10-20T05:06:53.759Z | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 | — |
| lost | 150 | 2 | 2026-10-20T05:06:55.010Z | 05:06, 05:10, 05:21 | — |
| unrec | 15 | 1 | 2026-10-20T05:06:55.010Z | 05:06, 05:10, 05:11, 05:20, 05:21 | — |
| unrec | 8 | 2 | 2026-10-20T05:06:57.005Z | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 | — |
| unrec | 6 | 2 | 2026-10-20T05:06:57.005Z | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 | — |
| unrec | 5 | 2 | 2026-10-20T05:06:57.005Z | 05:06, 05:07, 05:10, 05:11, 05:20, 05:21 | — |
| lost | 5 | 10 | 2026-10-20T05:06:57.005Z | 05:06, 05:07 | — |
| lost | 50 | 3 | 2026-10-20T05:06:59.039Z | 05:06, 05:11, 05:21 | — |
| lost | 40 | 3 | 2026-10-20T05:06:59.039Z | 05:06, 05:07, 05:11, 05:21 | — |
| lost | 30 | 3 | 2026-10-20T05:06:59.039Z | 05:06, 05:07, 05:11, 05:21 | — |
| lost | 25 | 6 | 2026-10-20T05:07:03.029Z | 05:07, 05:21 | — |
| lost | 20 | 6 | 2026-10-20T05:07:03.029Z | 05:07, 05:21 | — |

## The false-trigger table at the chosen pair (unrec T 4 K 2) and its neighbours

Firing episodes per window (0 required); last night: the clean minutes it fired in.

| window | unrec T3 K1 | unrec T3 K2 | unrec T3 K3 | unrec T4 K1 | unrec T4 K2 | unrec T4 K3 | unrec T5 K1 | unrec T5 K2 | unrec T5 K3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CL-B5 A pcm | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| CL-B5 B opus | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| CL-B5 L opus | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CL-B6 1 opus | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| CL-B6 2 pcm | 5 | 1 | 0 | 3 | 0 | 0 | 1 | 0 | 0 |
| CL-B7 pcm | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CL-B7 opus today | 3 | 0 | 0 | 2 | 0 | 0 | 1 | 0 | 0 |
| CL-B7 opus lean | 6 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| G4-S3 (remote, 4000; no LAN part) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| last night's clean minutes | 04:51, 04:52, 04:55, 04:56, 04:57, 04:58, 04:59, 05:00, 05:01, 05:02, 05:03, 05:04, 05:05, 05:06, 05:18, 05:19, 05:20, 05:21 | 04:55, 04:56, 05:03, 05:05 | 0 | 04:52, 04:55, 04:58, 04:59, 05:02, 05:03, 05:05, 05:06, 05:19, 05:20 | 0 | 0 | 04:55, 05:19 | 0 | 0 |
| Sunday: first fire | 04:23:43 | 04:45:11 | 05:01:38 | 04:23:49 | 05:03:05 | 05:11:00 | 04:57:15 | 05:06:57 | 05:11:00 |

## G8-S1's shim cells (7000 start), under the chosen pair; the recorded rung path from the record

| cell | evaluated reports | post-FEC lost / unrec (sum) | fires (first; minutes) |
| --- | ---: | --- | --- |
| G8-S1 03 loss-1 off | 347 | 537 / 201 (joined 347/348) | 20:46:14; 20:46, 20:47, 20:49, 20:50, 20:51, 20:54, 20:55, 20:56 |
| G8-S1 04 loss-1 on | 346 | 755 / 212 (joined 346/347) | 21:01:28; 21:01, 21:02, 21:03, 21:05, 21:07, 21:08, 21:09, 21:10 |
| G8-S1 05 loss-5 off | 346 | 9394 / 3570 (joined 346/347) | 21:14:54; 21:14, 21:15, 21:16, 21:17, 21:18, 21:19, 21:20, 21:21, 21:22, 21:23, 21:24, 21:25 |
| G8-S1 06 loss-5 on | 324 | 38562 / 2639 (joined 333/337) | 00:33:26; 00:33, 00:34, 00:35, 00:36, 00:37, 00:38, 00:39, 00:40, 00:41, 00:42, 00:43 |
| G8-S1 07 burst-50x20 off | 327 | 9609 / 168 (joined 323/331) | 00:48:56; 00:48, 00:49, 00:50, 00:51, 00:52 |
| G8-S1 08 burst-50x20 on | 346 | 1712 / 53 (joined 345/346) | none |
| G8-S1 21 delay-50+loss-1 off | 348 | 1357 / 318 (joined 347/348) | 04:05:08; 04:05, 04:06, 04:07, 04:08, 04:09, 04:10, 04:11, 04:12, 04:13, 04:14, 04:15 |
| G8-S1 22 delay-50+loss-1 on | 346 | 1875 / 277 (joined 346/347) | 04:19:56; 04:19, 04:20, 04:21, 04:22, 04:24, 04:25, 04:26, 04:27, 04:28, 04:29 |
