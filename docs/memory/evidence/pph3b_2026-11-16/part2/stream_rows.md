# PP-H3b part 2 — the hand-overs (party rows, the bitrate log's `ssrc_change` rows, the onn's own decoder-session logs and heartbeats)

The onn's stream session stood from 21:58:21Z to the user's Home in M3 (22:08:04Z), and again from RESUME (22:08:11Z) to
END (22:12:08Z); every switch was inside a session. The client's times are its decoder log's `elapsed_ms` placed on the
hub's clock from its heartbeats (the session's start = min(received − elapsed), ±a few ms). "Held frame" = the client's
`output_gap_ms` before its first frame of the new stream (`slow_events`); "row start" = the `minigame_stream` row's time
minus its `seconds`.

| mini game | way | row start | `seconds` (host) | planned / switched | the client's SSRC change | first IDR (ms after) | first new frame | **held frame on the onn** | row start → first new frame | the window's stalls / stall ends / desyncs not taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | in | 22:00:04.661 | 1.718 | true / true | 22:00:05.533 | 4 | 22:00:05.562 | **0.455 s** | 0.90 s | 6 / 1 / 0 (open 4.72 s) |
| M1 | back | 22:01:46.640 | 1.819 | true / true | 22:01:47.621 | 21 | 22:01:47.665 | **0.569 s** | 1.03 s | 8 / 1 / 0 (4.82 s) |
| M2 | in | 22:04:31.013 | **3.548** | true / true | 22:04:33.723 | 4 | 22:04:33.748 | **0.573 s** | 2.74 s | 8 / 1 / 0 (6.55 s) |
| M2 | back | 22:06:14.506 | **3.635** | true / true | 22:06:17.311 | 21 | 22:06:17.354 | **0.529 s** | 2.85 s | 7 / 1 / 0 (6.63 s) |
| M3 | in | 22:07:04.835 | 1.855 | true / true | 22:07:05.848 | 4 | 22:07:05.872 | **0.531 s** | 1.04 s | 7 / 1 / 0 (4.85 s) |
| M3 | back | 22:08:57.236 | 1.986 | true / true | 22:08:58.400 | 28 | 22:08:58.448 | **0.572 s** | 1.21 s | 8 / 1 / 0 (4.98 s) |
| M4 | in | 22:11:57.970 | 1.867 | true / true | 22:11:59.006 | 7 | 22:11:59.032 | **0.584 s** | 1.06 s | 8 / 1 / 0 (4.87 s) |
| M4 | back | — (END) | — | — | — | — | — | — | — | — |

- **From `ended` to the board's first frame** (the user's view of the hand-back): M1 22:01:45.514 → 22:01:47.665 =
  **2.15 s**; M2 22:06:13.872 → 22:06:17.354 = **3.48 s**; M3 22:08:55.814 → 22:08:58.448 = **2.63 s**.
- **The bitrate log:** seven `ssrc_change` rows `source` "minigame_switch" (`blackout_reports` 3 each); the level 7000
  in every row; `escalation_armed` false in every sample; **no `escalation_armed` / `transition` row**; the state
  REFERENCE ↔ PRESSURE / HOLD_DOWN (blackout) only, no step.
- **What the client reported:** two decoder-session logs (one per stream session): `surface_hold` losses 0, held 0,
  restarted 0, decoders built 1; `stream_discontinuities` = the seven SSRC changes, `jump_packets` 0; every first IDR
  complete, no rejected IDR, no dropped AU; stall datagrams sent 36 + 16 (`stall_signal_ms` 150), all inside the
  planned windows (no `client_stall` row); fps 59-62 in the heartbeats across every switch.
- **Why M2's switches took 3.5-3.6 s and the others 1.7-2.0 s:** not read (no row says); recorded.
