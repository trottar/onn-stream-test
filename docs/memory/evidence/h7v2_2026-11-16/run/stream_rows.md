# The stream's rows over the sitting (the 03:26:05Z mark → the close 03:45:01Z)

| | H7-V2 (two matches, the watcher and the picture keeper) | H7-L2 | HOME-12V 07:50-08:30Z |
| --- | --- | --- | --- |
| adaptive bitrate samples (~2 s each) | 290 (~9.7 min streamed) | 118 | 263 |
| the bitrate acted / its level | **0** / 7,000 throughout | 0 / 7,000 | 0 / 7,000 |
| PRESSURE entries (each back to REFERENCE) | 27 — **2.6 a minute** | 2.3 a minute | 2.3 a minute |
| frames a second, median | **59.7** | 59.8 | 59.8 |
| samples under 50 fps | 8 — **all in the first session 03:31:26-03:31:47Z** (its start, and the onn leaving it: `surface_lost` user_leave) and the two session starts | 0 | 1 |
| lost packets (sum of deltas) | **6,693 — 6,658 of them 03:31:28-03:31:47Z**, in the first session, before any start call (03:32:25Z) or picture (03:32:59Z); **35 over the ~9.5 min after** | 25 | 27 |

- **At the two loads** (03:32:25.6Z, 03:37:55.4Z): no recovery row; PRESSURE entries 1.8 s / 3.9 s **before** each and
  12 s after — the ordinary short flips, not at a load.
- **The recovery log** (50 new rows): the two companion starts' config rows; launch ports, pad slots; the first session
  03:31:24Z (`surface_lost` user_leave 03:31:45Z, `session_end_bye` 03:32:02Z — the onn left it and joined again);
  sessions 03:32:09-03:37:22Z and 03:37:45-03:41:35Z; `state_save_skipped` ×4, `input_hold_skipped_paused` ×1; **no stall,
  hold, rewind or recovery row; `launch_orphaned` 2 before = 2 after (none new).**
- **Read as:** the matches, the watcher and the picture keeper did not disturb the stream. The first session's loss
  burst came before any of them ran and ended with the onn leaving that session (as the user launched); it is recorded,
  not explained.
