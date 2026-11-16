# The stream's rows (the adaptive bitrate's rows after the mark 5,554; the recovery log's after 2,199)

Three onn sessions in the sitting, each started and ended by the onn as a normal game's (the 2-4-sample sessions between
them are the stream's start-up handshakes — the first sample before the first picture):

| session (renderer) | from-to (UTC) | samples | fps median | lowest | < 55 | < 50 | lost packets | PRESSURE | acted | level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| run 1 to Home (Compatibility) | 17:47:59-17:50:24 | 73 | **59.8** | 53.8 | 1 | 0 | 5 (one sample) | 3 | 0 | 7,000 |
| run 1 after RESUME (Compatibility) | 17:50:52-17:52:19 | 44 | **59.8** | 55.9 | 0 | 0 | 0 | 1 | 0 | 7,000 |
| run 2 (Mobile) | 17:53:06-17:54:22 | 39 | **59.6** | 57.6 | 0 | 0 | 0 | 0 | 0 | 7,000 |

- **No stall, no recovery row** (the recovery log: `launch_ports`, `remote_config` (the LAN), `pad_slots`,
  `party_session` (`party_mode` true), `session_started`, then at each end `session_end_bye`, `session_ended`,
  `state_save_skipped` (the session over — nothing saved for the board), once `input_hold_skipped_paused`); **no new
  `launch_orphaned` (2 → 2)**; max output gap 38 ms.
- **The bitrate never acted** (7,000 throughout); PRESSURE in 4 of 156 play samples (~0.8 a minute; H7-V4's normal PS1
  session ~1.6 a minute); 5 packets lost in ~5 min of play (H7-V4: 47 in ~8.5 min). The board's busy textures and
  drifting mist did not move the bitrate.
- **Sound (AU):** the stream's audio packets sent grew every second of the play — +14,501 (run 1 to Home), +8,700
  (after RESUME), +7,601 (Mobile), never falling; one sound stream with the board's pid at each launch (`audio` row
  `sink_input` true).
- **The joins** (the recovery log's `pad_slots`): run 1 — both pads joined 5.1 s after the stream's start (17:47:54.5 →
  17:47:59.6); after RESUME the onn's join line came back and both re-joined (P1 at 2.5 s, P2 at 4.5 s after the
  session's start — the onn clears its slot map at every unpause, as for any game); run 2 — both joined 4.6 s after the
  start. After RESUME the user's line says each pad moved its own figure.
