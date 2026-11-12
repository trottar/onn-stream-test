# The stream's rows over the sitting (06:25:38Z mark → 06:43:41Z), against sessions without contests

| | H7-L2 (two contests, a read every second) | H7-L1 (reads only) | HOME-12V 07:50-08:30Z (neither) |
| --- | --- | --- | --- |
| adaptive bitrate samples (~2 s each) | 118 (~3.9 min streamed) | 146 (~4.9 min) | 263 (~8.8 min) |
| the bitrate acted / its level | **0** / 7,000 throughout | 0 / 7,000 | 0 / 7,000 |
| PRESSURE entries (each back to REFERENCE in ~2 s) | 9 — **2.3 a minute** | 2.5 a minute | 2.3 a minute |
| frames a second, median | **59.8** | 59.8 | 59.8 |
| samples under 50 fps | **0** | 2 (session starts) | 1 (a session start) |
| lost packets (sum of deltas) | 25 | 213 | 27 |

**At the two loads (rows recorded):** the recovery log has no row at either load (06:37:44.978Z, 06:41:09.791Z) — no
stall, hold, rewind or recovery; the bitrate log has one PRESSURE entry 3.0 s and 3.8 s after each load (a sample at
55.8 fps, output gap 6 / 22 ms, no loss, no IDR wait), back to REFERENCE "clean" 2.0 s later — the same short flip it
logs about every 25 s of an ordinary session (9 in the sitting, 7 away from any load).

**The recovery log** (42 new rows): the companion's start configs, session starts / ends, pad slots, launch ports; the
only state / hold rows `state_save_skipped` at the two session ends (06:39:07Z — the user's Home; 06:42:39Z — END) and
`input_hold_skipped_paused` (06:39:08Z); **`launch_orphaned` 0** (the whole log).

**The reads** (`h7_reads.jsonl`, 490 rows, the contests' included): **490 ok, 0 errors**; `read_ms` **median 38.8, p95
45.3, worst 54.8**. The watchers: no "busy", no "not in time".

**The loads as designed:** RetroArch's own line `[State] Loading state "…state8", 16777240 bytes.` at each (the game log;
`load_line_ms` 33.2 and 52.3); the first reads after each 0 / 0 (0.03-0.14 s after); armed when the values filled to
140 / 140 (15.73 s, 11.75 s); 30 samples a second to 30.0 / 30.1 s by the hub's clock.

**Read as:** the stream's rows are those of a normal session. **The contests and the reads did not disturb the stream.**
