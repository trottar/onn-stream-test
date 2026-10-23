**A_snes_blackout_both_stack**

| # | start (UTC) / return | hold s (age ms) | carry pre / stall | handover s (held ms) | resume (via, s after return; hb between) | the rewind / release row | stall_end_late ms (gate stalls ignored) | picture after (1st advance s, fps 10 s) | unattended core-running / --net | link before → after (RSSI, tx/rx) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b1 | 20:26:13.204 / 26:17.396 (4.19 s) | 1.06 (966.2) | 59 / 0 | 4.23 (3261) | client_ready_hold +2.57; 2 | rewind_failed(hold_return_stall) req 59 rew 59 PAUSED after | 325 (6) | 1.79, 59.4 | 48.4 / 48.4 | -67, 162/108 → -67, 162/162 |
| b2 | 20:28:13.388 / 28:17.391 (4.0 s) | 1.04 (951.3) | 59 / 0 | 4.03 (3078) | client_ready_hold +2.49; 1 | rewind_failed(hold_return_stall) req 59 rew 59 PAUSED after | 377 (7) | 0.76, 59.9 | 47.5 / 47.5 | -67, 162/108 → -67, 135/108 |
| b3 | 20:30:13.356 / 30:17.399 (4.04 s) | 1.04 (951.5) | 59 / 0 | 4.08 (3128) | hold_return_stall +3.13; 1 | rewind_failed(client_ready_hold) req 59 rew 59 PAUSED after | 399 (7) | 0.93, 60.2 | 47.6 / 47.6 | -68, 121/108 → -68, 108/108 |
| b4 | 20:32:13.374 / 32:17.395 (4.02 s) | 1.06 (957.0) | 60 / 0 | 4.06 (3102) | client_ready_hold +2.06; 1 | rewind_failed(hold_return_stall) req 60 rew 60 PAUSED after | 505 (7) | 0.77, 59.2 | 48.7 / 48.7 | -67, 108/81 → -67, 121/216 |
| b5 | 20:34:13.386 / 34:17.404 (4.02 s) | 1.05 (950.2) | 59 / 0 | 4.02 (3072) | client_ready_hold +2.72; 1 | rewind_failed(hold_return_stall) req 59 rew 59 PAUSED after | 489 (7) | 0.81, 59.6 | 48.0 / 48.0 | -67, 121/108 → -67, 121/108 |
| b6 | 20:36:13.385 / 36:17.410 (4.03 s) | 1.06 (953.2) | 59 / 0 | 4.03 (3072) | none (session ended)  | rewind_failed(stall_quiet) req 59 rew 59 PAUSED after | None (None) | None, None | 48.4 / 48.4 | -68, 108/108 → -68, 108/162 |

**D_ps1_blackout_both_state**

| # | start (UTC) / return | hold s (age ms) | carry pre / stall | handover s (held ms) | resume (via, s after return; hb between) | the rewind / release row | stall_end_late ms (gate stalls ignored) | picture after (1st advance s, fps 10 s) | unattended core-running / --net | link before → after (RSSI, tx/rx) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b1 | 21:09:48.216 / 09:52.222 (4.01 s) | 1.08 (986.1) | 61 / 0 | 4.05 (3068) | hold_return_stall +2.69; 1 | input_release(hold_return_stall) restored 36 net 24 LOAD_STATE_SLOT 9 | 3388 (59) | 0.79, 59.5 | 49.7 / 49.7 | -68, 108/81 → -68, 121/108 |
| b2 | 21:11:48.218 / 11:52.225 (4.01 s) | 1.05 (950.7) | 59 / 0 | 4.05 (3099) | hold_return_stall +2.81; 1 | input_release(hold_return_stall) restored 34 net 24 LOAD_STATE_SLOT 9 | 3075 (51) | 0.98, 60.7 | 48.1 / 48.1 | -68, 121/108 → -68, 121/162 |
| b3 | 21:13:48.209 / 13:52.224 (4.01 s) | 1.06 (955.8) | 59 / 0 | 4.01 (3059) | hold_return_stall +1.93; 1 | input_release(hold_return_stall) restored 35 net 24 LOAD_STATE_SLOT 9 | None (None) | 1.08, 59.4 | 48.4 / 48.4 | -69, 135/121 → -69, 121/108 |
| b4 | 21:15:48.163 / 15:52.220 (4.06 s) | 1.06 (961.9) | 59 / 0 | 4.09 (3124) | hold_return_stall +1.55; 1 | input_release(hold_return_stall) restored 35 net 24 LOAD_STATE_SLOT 9 | 1842 (32) | 1.7, 60.6 | 48.5 / 48.5 | -68, 121/81 → -69, 121/108 |
| b5 | 21:17:48.152 / 17:52.219 (4.07 s) | 1.05 (955.7) | 59 / 0 | 4.11 (3149) | hold_return_stall +0.92; 1 | input_release(hold_return_stall) restored 35 net 24 LOAD_STATE_SLOT 9 | 2464 (40) | 2.03, 56.5 | 48.1 / 48.1 | -68, 121/108 → -68, 135/108 |

**B_snes_blackout_down_stack** (the start = the client's last frame before the dark span, from its own ≥ 3-s output gaps; the return = start + 4.0 s)

| # | start (UTC) | stall pause age ms (s after the start) | encoder restart | resumes (via, s after return) | the second pause (in-gate) and its rewind | picture after the last resume (1st advance s, fps 10 s) | unattended core-running | link before → after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b1 | 20:41:08.492 | 428.0 (0.49) | 1 | recovery +2.52, stall_end +2.82 | 1 pause; input_release(stall_end) req 2 rew 2 PLAYING after | 1.12, 60.2 | 5.8 | -67, 108/162 → -67, 108/108 |
| b2 | 20:43:08.488 | 428.0 (0.39) | 0 | recovery +3.29, stall_end +3.85 | 1 pause; input_release(stall_end) req 3 rew 3 PLAYING after | 0.81, 59.7 | 0.0 | -68, 121/81 → -69, 108/40 |
| b3 | 20:45:08.488 | 420.0 (0.39) | 1 | recovery +1.93, stall_end +2.36 | 1 pause; input_release(stall_end) req 3 rew 3 PLAYING after | 0.94, 59.9 | 0.0 | -68, 108/108 → -68, 121/108 |
| b4 | 20:47:08.486 | 426.0 (0.48) | 1 | recovery +4.07, stall_end +4.68 | 1 pause; input_release(stall_end) req 3 rew 3 PLAYING after | 1.29, 58.5 | 0.0 | -69, 121/81 → -69, 121/81 |
| b5 | 20:49:08.491 | 484.0 (0.55) | 0 | recovery +2.16, stall_end +2.86 | 1 pause; rewind_failed(stall_end) req 2 rew 2 PAUSED after | 1.71, 58.5 | 0.8 | -68, 108/108 → -68, 121/81 |

