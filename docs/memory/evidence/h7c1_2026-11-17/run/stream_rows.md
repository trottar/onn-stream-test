# The stream during H7-C1 (the bitrate log's samples, the client's heartbeats, the recovery log; marks in `pre/log_marks.txt`)

Three stream sessions — the launch (00:33:46-00:35:10Z), after SAVE 1's RESUME (00:35:21-00:38:17Z), after SAVE 2's
RESUME (00:38:36-00:46:51Z); each ended only by the users' Home (`session_end_bye` / `session_ended`) and the END.

| | H7-C1 (T89, four pads) | PP-H3b's sitting (the board and T88, two pads) |
| --- | --- | --- |
| frames a second (bitrate samples, median) | **59.8** (377 samples; 0.0 only at each session's first sample, `resync`; 17.9 once at 00:35:52Z, 49.7 / 49.9 twice) | 59.7 (412) |
| the level | **7000 throughout**; `escalation_armed` false in every sample; no `transition`; the state REFERENCE ↔ PRESSURE only | 7000 throughout |
| lost packets (sum of `lost_packets_delta`) | **113** (the heartbeats: 3 / 33 / 77 per session; FEC unrecoverable groups 1 / 5 / 8; no resync; audio lost 3) | 57 |
| the client's output gap (samples, max) | 73 ms | — |
| the Wi-Fi | RSSI −69 dBm | — |

**The recovery log** (33 rows from its mark): `launch_ports` 1, `pad_slots` 14, `session_started` / `session_end_bye`
/ `session_ended` / `state_save_skipped` 3 each, `state_reply` 2, `remote_config` 3, `input_hold_skipped_paused` 1 —
**no `client_stall`, `desync_pause`, `stall_handover_v2`, `encoder_restart`, `resumed`, `gave_up_saved`**;
`launch_orphaned` 2 → 2.

**The four seats:** `launch_ports` four ports (`--device=1:1` … `4:1`, `players` 4; its `players_joined` "3" — the onn's
count when it asked); `pad_slots` count 4 in each session — 00:33:56.8Z; after SAVE 1's RESUME P1-P3 by 00:35:30Z and
**P4 only at 00:37:12.7Z** (during M1); after SAVE 2's RESUME 00:38:48.6Z.
