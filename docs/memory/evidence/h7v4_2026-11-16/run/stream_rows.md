# The stream's rows (this sitting: one onn session 15:43:13.980-15:51:48.446Z; the launch's handoff 15:42:59-15:43:13Z)

- **Adaptive bitrate** (287 rows after the mark 5,263): **acted 0; 7,000 kbps throughout**; 261 samples, fps median
  59.5; REFERENCE 247 / PRESSURE 14 (~1.6 a minute; H7-V2 2.6); max output gap 74 ms.
- **Recovery log** (9 rows after the mark 2,166): `launch_ports`, `remote_config` (LAN), `pad_slots` ×2,
  `session_started`, then at the user's END `session_end_bye`, `state_save_skipped` (client_bye), `session_ended`,
  `input_hold_skipped_paused`. **No stall, no recovery row, no `launch_orphaned` (2 → 2).**
- **At the loads and starts** (15:43:25, :29, :35, :39, :45, 15:46:34, 15:48:56): **no loss, no low-fps sample, no
  recovery row** within ±5 s. The watcher's reads and kept pictures (410 in all) left no mark on the rows.
- **Loss:** 47 packets in 7 samples over the ~8.5 min after the start-up (2-16 each, 15:45:18-15:50:29).
- **The first seconds, read on their own** (not a cell): 15:43:03-15:43:13Z, before "ready" and before any start call —
  2 samples under 50 fps (36.3, 46.6) and 514 lost packets (485 + 25 + 4), PRESSURE twice; then clean. H7-V2's first
  session: 6,658 lost packets and 8 low-fps samples over ~21 s. The same kind of start-up burst, much smaller.
- **The game** (status every 10 s, `status_reads.txt`): running and unpaused from "ready" to the user's END; paused only
  at the launch's own stabilisation (15:43:03 / 15:43:13Z, before "ready") and at the user's Home (15:51:53Z). The
  encoder ~42 % of one CPU (median), as a normal session.
- **Clean.**
