# E3-R1 probe — what the trigger saw (2026-10-08)

Measurement before the change, on the adopted state (live, the guide index, Snes9x), no flag. Two parts:
- **the timelines** (`e3_r1_timelines.py` → `timelines.json`): per second, ±60 s around every recorded `desync_pause` — the
  five suite runs' false pauses (seven events), three of the same type outside the suite (10-05), and every real drop
  (R3b/R3d's nft outages N05, N3, N15, N15b, N150, E30; R3's 09-20 substitute outages F05, F3, F15, F150);
- **the idle probe** (`e3_r1_idle_probe.py` → `idle_probe/`, `idle_stats.json`): a PS1 stream PLAYING, nobody at the
  controller, 10 min (03:46:17-03:56:17Z), the controller-packet age the recovery monitor reads polled at 4 Hz
  (`recovery.last_client_seen_ms`; no new hook), the 1-s sampler, the client's heartbeats.

Sources per timeline: the run's 1-s sampler (`eno1` rx packets/s = the client→host direction, ~460/s of it the
controller channel; tx = the stream), the heartbeats (2 s; arrival delay against the client's own `elapsed_ms`; the
client's `last_output_age_ms`; its lost-packet total), the C2 telemetry, the ladder's decisions, the recovery log.
The controller channel's silence per second is estimated from rx against the run's median; nothing finer exists in
the records (the receive loop logs no packet times).

## The summaries

| id | kind | trigger, age ms | fault s; fired after s | then (s, event) | ctrl silent s est (-3..+3); rx pps -3..+4 | hb arrival gap max s; delay max s | client out age max ms (+/-6 s); next hb |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E2-1080P-r1 | false | controller_silence, 1002.5 | None; None | 120.4 gave_up_saved | 1.84; [458.0, 488.0, 256.0, 15.0, 1031.0, 258.0, 707.0, 489.0] | None; None | None; None |
| S1-control | false | client_output_silence, 1149.0 | None; None | 2.8 resumed | 0.27; [462.0, 466.0, 468.0, 356.0, 465.0, 566.0, 446.0, 561.0] | 3; 0.97 | 1669; 0 |
| S1-CONC-r1a | false | client_output_silence, 1011.0 | None; None | 9.5 encoder_restart; 18.3 resumed; 21.0 desync_pause (controller_silence); 141.4 gave_up_saved | 0.08; [532.0, 544.0, 510.0, 556.0, 579.0, 440.0, 468.0, 515.0] | 4; 1.13 | 3198; 636 |
| S1-CONC-r1b | false | controller_silence, 1003.2 | None; None | 120.4 gave_up_saved | 1.17; [457.0, 543.0, 393.0, 18.0, 641.0, 978.0, 985.0, 458.0] | 4; 2.0 | 761; 26 |
| S1-CONC-r2a | false | controller_silence, 1002.1 | None; None | 14.9 encoder_restart; 32.2 resumed; 118.4 desync_pause (client_output_silence); 143.2 resumed | 0.91; [415.0, 404.0, 1117.0, 544.0, 605.0, 797.0, 163.0, 809.0] | 4; 2.19 | 931; 144 |
| S1-CONC-r2b | false | client_output_silence, 1206.0 | None; None | 24.8 resumed | 0.35; [877.0, 978.0, 866.0, 440.0, 413.0, 767.0, 390.0, 752.0] | 3; 1.81 | 703; 149 |
| A2-PS1-r1 | false | controller_silence, 1003.6 | None; None | 120.3 gave_up_saved | 3.15; [266.0, 48.0, 931.0, 71.0, 6.0, 1410.0, 452.0, 451.0] | 5; 3.13 | 174; 174 |
| out-10-05-0401 | false-outside | client_output_silence, 1237.0 | None; None | 1.0 resumed; 77.3 desync_pause (client_output_silence); 80.6 encoder_restart; 93.9 resumed; 167.9 session_ended | None; None | None; None | None; None |
| out-10-05-0402 | false-outside | client_output_silence, 1353.0 | None; None | 3.2 encoder_restart; 16.6 resumed; 90.6 session_ended | None; None | None; None | None; None |
| out-10-05-1514 | false-outside | controller_silence, 1002.6 | None; None | 0.5 session_ended | None; None | None; None | None; None |
| R3b-N3 | real | client_output_silence, 1132.0 | 3.06; 1.27 | 3.6 resumed; 25.8 session_ended | None; None | 3; 0.0 | 2166; 23 |
| R3b-N15 | real | client_output_silence, 1281.0 | 15.06; 1.42 | 4.2 encoder_restart; 17.4 resumed; 49.8 session_ended | None; None | 3; -0.0 | 6417; 4367 |
| R3b-N15b | real | client_output_silence, 1147.0 | 15.07; 1.28 | 4.2 encoder_restart; 17.4 resumed; 83.5 session_ended | None; None | 3; 0.01 | 6271; 4228 |
| R3b-N150 | real | client_output_silence, 1300.0 | 150.07; 1.44 | 3.1 encoder_restart; 15.8 encoder_restart; 38.0 encoder_restart; 70.7 encoder_restart; 103.4 encoder_restart | None; None | 3; 0.01 | 7459; 3358 |
| R3b-E30 | real | client_output_silence, 1235.0 | None; 1.36 | 4.2 encoder_restart; 16.9 encoder_restart; 39.1 encoder_restart; 71.8 encoder_restart; 104.5 encoder_restart | None; None | 3; 0.03 | 6351; 4311 |
| R3b-N05 | real-nofire | None, None | 0.56; None | 24.3 session_ended | None; None | 2; 0.01 | 18; 5 |
| R3-F05 | real-nofire | None, None | 0.75; None | 22.1 session_ended; 75.4 desync_pause (client_output_silence); 78.7 encoder_restart; 80.6 resumed; 103.2 session_ended | None; None | 2; 0.03 | 158; 15 |
| R3-F3 | real | client_output_silence, 1095.0 | 3.09; 1.3 | 3.3 encoder_restart; 5.2 resumed; 27.7 session_ended; 84.4 desync_pause (client_output_silence); 98.0 encoder_restart | None; None | 2; 0.05 | 1614; 0 |
| R3-F15 | real | client_output_silence, 1492.0 | 15.25; 1.73 | 13.6 encoder_restart; 23.6 encoder_restart; 43.6 encoder_restart; 44.4 session_ended; 98.3 desync_pause (client_output_silence) | None; None | 2; 0.02 | 7112; 3030 |
| R3-F150 | real | client_output_silence, 1418.0 | 154.6; 1.62 | 14.2 encoder_restart; 24.2 encoder_restart; 44.2 encoder_restart; 74.2 encoder_restart; 104.2 encoder_restart | None; None | 3; 0.94 | 6511; 2440 |

## The idle probe

- **The client keeps sending controller packets with no input: yes** — 460.0 packets/s median (interval
  ~2.17 ms), minimum 417.0/s, no second below half the median in 600 s.
- **Controller-packet age** (2,400 reads at 4 Hz): median 3.0 ms, p95 10, p99 28, max **295 ms**;
  1 read over 250 ms, none over 500 or 1,000.
- **The client's output age** (heartbeats): median 9.0 ms, p95 42, max **144 ms**; none over 1,000.
- Heartbeat arrival gaps: median 2.01 s, max 2.23 s. The state stayed PLAYING throughout.

## What the timelines show

**The four `controller_silence` pauses** (E2-1080P r1, S1-CONC r1b, S1-CONC r2a, A2 r1) each sit on a **client→host
stall**: the controller packets dip (to 6-48/s in the worst second) for ~1-3 s, then arrive in a catch-up burst
(931-1,410/s) — packets queued on the onn and delivered late; the heartbeats posted in the same seconds arrive 2-3 s
late. The host→client stream is untouched (tx steady), and the **client's output stayed fresh** (the next heartbeat's
`last_output_age_ms` 26-174 ms): the client never stopped playing. Because the client never saw an output stall, it
never ran its re-entry gate, and the host's recovery has no other way back: **three of the four sat 120 s and gave up
and saved** (E2, S1-CONC r1b, A2: `gave_up_saved`, then `PAUSED_SAVED` to the end of the window); S1-CONC r2a came back
only because a later client-side stall ran the gate (resumed +32 s).

**The three false `client_output_silence` pauses** (S1 control, S1-CONC r1a, S1-CONC r2b; all on 10-06, before the
index removed the per-grab parse) are the **client's own detector** seeing a real output stall of 1.0-3.2 s (output age
1,149 / 3,198 / 1,206 ms, with loss bursts of 600-1,800 packets). Each resumed through the gate as designed (+2.8 s,
+18.3 s, +24.8 s). They are indistinguishable from R3's shortest real drops at every signal the host has: R3b N3
(3.06 s) and R3 F3 (3.09 s) post the same trigger at the same age (1,132 / 1,095 ms) and their next heartbeat shows the
output back (23 / 0 ms), exactly as S1 control's does (0 ms). Only the heartbeats' arrival delay differs (0.6-1.8 s in
the S1 events, ≤ 0.05 s in N3/F3), which is the S1-era host load, not the link, and one real drop (F150) reached 0.94 s.

**The real drops**: every one was triggered by the client (`client_output_silence`, 1,095-1,492 ms, +1.27 to +1.73 s
after the fault began); the host's controller trigger never fired on a real drop (the nft rule and the substitute
stop only host→client traffic — R3's "unexercised" note). N05 / F05 (0.5-0.75 s) did not fire.

## The reading (the task's rule)

- **(b) — no.** Idle, the controller age never grows: 460 packets/s with no input, max age 295 ms in 10 min.
- **(c) — no.** The fired ages (1,002-1,004 ms) agree with the neighbouring seconds: the packets really were absent
  for over a second in every case (the rx dips and the late heartbeats).
- **(a) — yes, for the controller trigger.** Every controller false pause sits on a client→host loss/delay burst
  longer than the 1-s threshold (est. 1.2-3.2 s; the longest, A2's, with heartbeats 3.1 s late), while the real
  drops (3-150 s) exceed it by a margin and do not use this trigger at all.
- **For the client trigger, no length separates false from real**: the false output stalls reach 3.2 s, the real
  drops start at 3.06 s; the detector is the client's (the APK), not the host's. The change below leaves it alone, and
  the replay bar's "fires on none of the five" cannot hold for the three runs whose pause was the client's (stated
  before the replay, in the pre-registration).

## The timelines around the events (−8 to +10 s; the full ±60 s in `timelines.json`)

**A2-PS1-r1** (false; 2026-10-07T23:00:07.545Z; trigger controller_silence, age 1003.6 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | 455.0 | 0.0 | 1456.6 |  |  |
| -7 | 450.0 | 0.01 | 1448.1 | 83; 0.01; 6; 137 |  |
| -6 | 460.0 | 0.0 | 1437.5 |  |  |
| -5 | 438.0 | 0.04 | 1457.2 | 84; 0.01; 3; 159 |  |
| -4 | 463.0 | 0.0 | 1464.0 |  |  |
| -3 | 266.0 | 0.42 | 1437.7 |  |  |
| -2 | 48.0 | 0.89 | 1444.8 |  |  |
| -1 | 931.0 | 0.0 | 1420.6 |  |  |
| 0 | 71.0 | 0.84 | 1430.4 | 85; 3.13; 13; 210 | desync_pause (controller_silence) |
| 1 | 6.0 | 0.99 | 1288.7 | 86; 0.73; 174; 397 |  |
| 2 | 1410.0 | 0.0 | 1450.1 | 87; 0.02; 12; 496 |  |
| 3 | 452.0 | 0.01 | 1449.2 |  |  |
| 4 | 451.0 | 0.01 | 1447.8 | 88; 0.01; 6; 496 |  |
| 5 | 452.0 | 0.01 | 1446.0 |  |  |
| 6 | 450.0 | 0.01 | 1447.8 | 89; -0.0; 3; 496 |  |
| 7 | 446.0 | 0.02 | 1445.8 |  |  |
| 8 | 473.0 | 0.0 | 1452.7 | 90; -0.01; 7; 496 |  |
| 9 | 451.0 | 0.01 | 1445.8 |  |  |
| 10 | 463.0 | 0.0 | 1447.9 | 91; 0.03; 8; 498 |  |

**E2-1080P-r1** (false; 2026-10-05T23:50:31.718Z; trigger controller_silence, age 1002.5 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | 458.0 | 0.0 | 2237.0 |  |  |
| -7 | 447.0 | 0.02 | 2405.2 |  |  |
| -6 | 455.0 | 0.0 | 2292.2 |  |  |
| -5 | 367.0 | 0.19 | 2269.7 |  |  |
| -4 | 548.0 | 0.0 | 2292.8 |  |  |
| -3 | 458.0 | 0.0 | 2311.2 |  |  |
| -2 | 488.0 | 0.0 | 2254.8 |  |  |
| -1 | 256.0 | 0.44 | 2290.3 |  |  |
| 0 | 15.0 | 0.97 | 2081.7 |  | desync_pause (controller_silence) |
| 1 | 1031.0 | 0.0 | 2167.0 |  |  |
| 2 | 258.0 | 0.43 | 2282.5 |  |  |
| 3 | 707.0 | 0.0 | 2224.1 |  |  |
| 4 | 489.0 | 0.0 | 2240.2 |  |  |
| 5 | 455.0 | 0.0 | 2263.2 |  |  |
| 6 | 460.0 | 0.0 | 2259.6 |  |  |
| 7 | 450.0 | 0.01 | 2254.8 |  |  |
| 8 | 461.0 | 0.0 | 2260.4 |  |  |
| 9 | 446.0 | 0.02 | 2258.0 |  |  |
| 10 | 461.0 | 0.0 | 2263.2 |  |  |

**S1-CONC-r1b** (false; 2026-10-06T03:50:24.116Z; trigger controller_silence, age 1003.2 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | 442.0 | 0.07 | 1289.9 |  |  |
| -7 | 359.0 | 0.24 | 1290.4 | 139; 0.91; 12874; 19123 |  |
| -6 | 72.0 | 0.85 | 1316.0 |  |  |
| -5 | 1142.0 | 0.0 | 1316.6 | 140; 0.9; 761; 20290 |  |
| -4 | 455.0 | 0.04 | 1078.5 | 141; 0.0; 6; 20760 |  |
| -3 | 457.0 | 0.04 | 1305.2 |  | resumed |
| -2 | 543.0 | 0.0 | 1503.5 |  |  |
| -1 | 393.0 | 0.17 | 1339.7 |  |  |
| 0 | 18.0 | 0.96 | 1142.2 | 142; 2.0; 30; 20776 | desync_pause (controller_silence) |
| 1 | 641.0 | 0.0 | 1314.5 | 143; -0.01; 26; 21025 |  |
| 2 | 978.0 | 0.0 | 1316.6 |  |  |
| 3 | 985.0 | 0.0 | 1311.8 | 144; -0.01; 4; 21025 |  |
| 4 | 458.0 | 0.03 | 1237.3 |  |  |
| 5 | 457.0 | 0.04 | 1142.8 | 145; -0.01; 8; 21182 |  |
| 6 | 458.0 | 0.03 | 1300.3 |  |  |
| 7 | 488.0 | 0.0 | 1305.1 | 146; 0.04; 2; 21185 |  |
| 8 | 594.0 | 0.0 | 1288.1 |  |  |
| 9 | 579.0 | 0.0 | 1319.2 | 147; -0.01; 38; 21187 |  |
| 10 | 579.0 | 0.0 | 1343.4 |  |  |

**S1-CONC-r2a** (false; 2026-10-06T04:22:51.591Z; trigger controller_silence, age 1002.1 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | 573.0 | 0.0 | 1353.5 |  |  |
| -7 | 405.0 | 0.14 | 1148.8 | 387; 0.48; 38; 24929 |  |
| -6 | 536.0 | 0.0 | 1311.8 |  |  |
| -5 | 489.0 | 0.0 | 1338.1 |  |  |
| -4 | 464.0 | 0.01 | 1095.1 | 388; 1.49; 1; 25009 |  |
| -3 | 415.0 | 0.12 | 1376.5 |  |  |
| -2 | 404.0 | 0.14 | 1317.7 |  |  |
| -1 | 1117.0 | 0.0 | 1355.0 |  |  |
| 0 | 544.0 | 0.0 | 1289.9 | 389; 2.19; 931; 25599 | desync_pause (controller_silence) |
| 1 | 605.0 | 0.0 | 871.8 | 390; 0.56; 144; 26650 |  |
| 2 | 797.0 | 0.0 | 1455.5 |  |  |
| 3 | 163.0 | 0.65 | 1317.7 | 391; 1.34; 267; 27084 |  |
| 4 | 809.0 | 0.0 | 1324.3 |  |  |
| 5 | 570.0 | 0.0 | 1327.0 | 392; 0.49; 63; 27138 |  |
| 6 | 538.0 | 0.0 | 1330.3 |  |  |
| 7 | 631.0 | 0.0 | 1321.1 | 393; 0.7; 54; 27209 |  |
| 8 | 437.0 | 0.07 | 1090.9 |  |  |
| 9 | 492.0 | 0.0 | 1317.3 | 394; 1.07; 262; 27328 |  |
| 10 | 469.0 | 0.0 | 1325.3 |  |  |

**S1-control** (false; 2026-10-06T03:30:38.177Z; trigger client_output_silence, age 1149.0 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | 95.0 | 0.79 | 1466.3 | 277; 1.05; 2; 751 |  |
| -7 | 837.0 | 0.0 | 1436.0 |  |  |
| -6 | 487.0 | 0.0 | 1494.0 | 278; 0.71; 149; 873 |  |
| -5 | 472.0 | 0.0 | 1218.8 |  |  |
| -4 | 474.0 | 0.0 | 1450.9 | 279; 0.44; 32; 1147 |  |
| -3 | 462.0 | 0.0 | 1450.0 | 280; 0.33; 10; 2039 |  |
| -2 | 466.0 | 0.0 | 1448.3 |  |  |
| -1 | 468.0 | 0.0 | 1451.1 |  |  |
| 0 | 356.0 | 0.23 | 1451.3 | 281; 0.97; 1669; 3109 | desync_pause (client_output_silence) |
| 1 | 465.0 | 0.0 | 1617.9 | 282; 0.0; 0; 3717 |  |
| 2 | 566.0 | 0.0 | 1417.8 |  | resumed |
| 3 | 446.0 | 0.04 | 1483.3 | 283; 0.02; 5; 3717 |  |
| 4 | 561.0 | 0.0 | 1810.7 |  |  |
| 5 | 477.0 | 0.0 | 1444.6 | 284; 0.01; 12; 3717 |  |
| 6 | 474.0 | 0.0 | 1514.2 |  |  |
| 7 | 473.0 | 0.0 | 1369.4 | 285; -0.0; 57; 3717 |  |
| 8 | 478.0 | 0.0 | 1474.7 |  |  |
| 9 | 464.0 | 0.0 | 1476.5 | 286; 0.0; 12; 3717 |  |
| 10 | 476.0 | 0.0 | 1438.1 |  |  |

**S1-CONC-r1a** (false; 2026-10-06T03:50:03.115Z; trigger client_output_silence, age 1011.0 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | 474.0 | 0.0 | 1295.0 |  |  |
| -7 | 417.0 | 0.12 | 1278.7 | 131; 0.16; 42; 11047 |  |
| -6 | 463.0 | 0.02 | 1326.5 |  |  |
| -5 | 470.0 | 0.01 | 1284.7 |  |  |
| -4 | 512.0 | 0.0 | 1322.9 | 132; 0.74; 69; 11108 |  |
| -3 | 532.0 | 0.0 | 1307.3 |  |  |
| -2 | 544.0 | 0.0 | 1326.4 | 133; 0.7; 48; 11244 |  |
| -1 | 510.0 | 0.0 | 1309.2 | 134; 0.59; 1010; 11846 |  |
| 0 | 556.0 | 0.0 | 1265.8 |  | desync_pause (client_output_silence) |
| 1 | 579.0 | 0.0 | 867.3 |  |  |
| 2 | 440.0 | 0.07 | 1696.3 | 135; 1.06; 636; 12696 |  |
| 3 | 468.0 | 0.01 | 1304.1 |  |  |
| 4 | 515.0 | 0.0 | 1324.6 |  |  |
| 5 | 424.0 | 0.11 | 1265.9 | 136; 1.13; 3198; 14477 |  |
| 6 | 494.0 | 0.0 | 1300.5 |  |  |
| 7 | 490.0 | 0.0 | 1118.4 |  |  |
| 8 | 393.0 | 0.17 | 1317.9 | 137; 1.86; 5742; 15711 |  |
| 9 | 502.0 | 0.0 | 1101.2 |  | encoder_restart |
| 10 | 1107.0 | 0.0 | 1339.8 |  |  |

**S1-CONC-r2b** (false; 2026-10-06T04:24:49.995Z; trigger client_output_silence, age 1206.0 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | 577.0 | 0.0 | 1506.2 | 444; -0.0; 8; 32812 |  |
| -7 | 575.0 | 0.0 | 1068.2 |  |  |
| -6 | 469.0 | 0.0 | 1365.7 | 445; -0.01; 10; 32949 |  |
| -5 | 448.0 | 0.04 | 1310.9 |  |  |
| -4 | 968.0 | 0.0 | 1395.8 | 446; -0.0; 16; 32951 |  |
| -3 | 877.0 | 0.0 | 1361.5 |  |  |
| -2 | 978.0 | 0.0 | 1256.5 |  |  |
| -1 | 866.0 | 0.0 | 1426.5 | 447; 1.75; 703; 33155 |  |
| 0 | 440.0 | 0.06 | 1343.0 |  | desync_pause (client_output_silence) |
| 1 | 413.0 | 0.12 | 1302.0 | 448; 0.57; 149; 33282 |  |
| 2 | 767.0 | 0.0 | 1323.2 |  |  |
| 3 | 390.0 | 0.17 | 1288.1 |  |  |
| 4 | 752.0 | 0.0 | 1300.0 | 449; 1.81; 76; 33566 |  |
| 5 | 225.0 | 0.52 | 1289.7 |  |  |
| 6 | 74.0 | 0.84 | 1289.1 |  |  |
| 7 | 983.0 | 0.0 | 793.0 | 450; 2.72; 17; 34169 |  |
| 8 | 732.0 | 0.0 | 1625.4 | 451; 0.17; 36; 34645 |  |
| 9 | 395.0 | 0.16 | 1294.0 |  |  |
| 10 | 482.0 | 0.0 | 1308.1 |  |  |

**R3b-N3** (real; 2026-09-22T15:17:49.103Z; trigger client_output_silence, age 1132.0 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | — | — | — | 13; 0.0; 74; 4 |  |
| -7 | — | — | — |  |  |
| -6 | — | — | — | 14; 0.0; 9; 4 |  |
| -5 | — | — | — |  |  |
| -4 | — | — | — | 15; -0.0; 28; 9 |  |
| -3 | — | — | — |  |  |
| -2 | — | — | — | 16; -0.01; 123; 9 |  |
| -1 | — | — | — |  |  |
| 0 | — | — | — | 17; -0.0; 2166; 9 | desync_pause (client_output_silence) |
| 1 | — | — | — |  |  |
| 2 | — | — | — | 18; -0.0; 23; 2345 |  |
| 3 | — | — | — |  | resumed |
| 4 | — | — | — |  |  |
| 5 | — | — | — | 19; -0.01; 45; 2348 |  |
| 6 | — | — | — |  |  |
| 7 | — | — | — | 20; -0.01; 44; 2348 |  |
| 8 | — | — | — |  |  |
| 9 | — | — | — | 21; 0.02; 10; 2348 |  |
| 10 | — | — | — |  |  |

**R3-F3** (real; 2026-09-20T20:04:15.658Z; trigger client_output_silence, age 1095.0 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | — | — | — | 14; -0.0; 5; None |  |
| -7 | — | — | — |  |  |
| -6 | — | — | — | 15; 0.01; 14; None |  |
| -5 | — | — | — |  |  |
| -4 | — | — | — | 16; 0.03; 7; None |  |
| -3 | — | — | — |  |  |
| -2 | — | — | — | 17; 0.05; 2; None |  |
| -1 | — | — | — |  |  |
| 0 | — | — | — | 18; -0.01; 1614; None | desync_pause (client_output_silence) |
| 1 | — | — | — |  |  |
| 2 | — | — | — | 19; 0.03; 0; None |  |
| 3 | — | — | — |  | encoder_restart |
| 4 | — | — | — | 20; 0.0; 9; None |  |
| 5 | — | — | — |  | resumed |
| 6 | — | — | — | 21; -0.01; 2; None |  |
| 7 | — | — | — |  |  |
| 8 | — | — | — | 22; 0.01; 15; None |  |
| 9 | — | — | — |  |  |
| 10 | — | — | — | 23; -0.01; 22; None |  |

**R3b-N15** (real; 2026-09-22T15:19:22.181Z; trigger client_output_silence, age 1281.0 ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | — | — | — | 13; 0.0; 12; 9 |  |
| -7 | — | — | — |  |  |
| -6 | — | — | — | 14; -0.0; 5; 9 |  |
| -5 | — | — | — |  |  |
| -4 | — | — | — | 15; -0.0; 0; 9 |  |
| -3 | — | — | — |  |  |
| -2 | — | — | — | 16; -0.01; 272; 9 |  |
| -1 | — | — | — |  |  |
| 0 | — | — | — | 17; 0.0; 2317; 9 | desync_pause (client_output_silence) |
| 1 | — | — | — |  |  |
| 2 | — | — | — | 18; -0.01; 4367; 9 |  |
| 3 | — | — | — |  |  |
| 4 | — | — | — |  | encoder_restart |
| 5 | — | — | — | 19; -0.01; 6417; 9 |  |
| 6 | — | — | — |  |  |
| 7 | — | — | — | 20; -0.0; 8456; 9 |  |
| 8 | — | — | — |  |  |
| 9 | — | — | — | 21; 0.0; 10509; 9 |  |
| 10 | — | — | — |  |  |

**R3b-N05** (real-nofire; 2026-09-23T05:54:39.767663Z; trigger None, age None ms)

| s | client→host pkt/s | ctrl silent (est) | host→client kB/s | heartbeat (seq; arrival delay s; client output age ms; lost total) | recovery |
| --- | --- | --- | --- | --- | --- |
| -8 | — | — | — | 12; 0.0; 6; 5 |  |
| -7 | — | — | — |  |  |
| -6 | — | — | — | 13; -0.01; 16; 5 |  |
| -5 | — | — | — |  |  |
| -4 | — | — | — | 14; -0.0; 2; 5 |  |
| -3 | — | — | — |  |  |
| -2 | — | — | — | 15; -0.01; 18; 5 |  |
| -1 | — | — | — |  |  |
| 0 | — | — | — | 16; -0.0; 4; 459 |  |
| 1 | — | — | — |  |  |
| 2 | — | — | — | 17; -0.01; 5; 464 |  |
| 3 | — | — | — |  |  |
| 4 | — | — | — | 18; 0.0; 11; 464 |  |
| 5 | — | — | — |  |  |
| 6 | — | — | — | 19; 0.01; 8; 464 |  |
| 7 | — | — | — |  |  |
| 8 | — | — | — | 20; 0.03; 7; 464 |  |
| 9 | — | — | — |  |  |
| 10 | — | — | — | 21; -0.01; 17; 464 |  |
