# The stream's rows over the sitting (00:03:29Z mark → 00:28:46Z), against two sessions without reads

| | H7-L1 (a read every second) | T88, 2026-11-11 20:16-20:26Z (no reads; the user's mid-fight saves) | HOME-12V 07:50-08:30Z (no reads) |
| --- | --- | --- | --- |
| adaptive bitrate samples (~2 s each) | 146 (~4.9 min streamed) | 45 (~1.5 min) | 263 (~8.8 min) |
| the bitrate acted / its level | **0** / 7,000 throughout | 0 / 7,000 | 0 / 7,000 |
| PRESSURE entries (each back to REFERENCE in ~2 s) | 12 — **2.5 a minute** | 8 — 5.3 a minute | 20 — 2.3 a minute |
| frames a second, median | **59.8** | 59.8 | 59.8 |
| samples under 50 fps | 2: 4.1 at 0.5 s into a session (its start), 31.6 at 13 s into the first (reset) session | 0 | 1: 11.0 at 0.5 s into a session |
| lost packets (sum of deltas) | 213 | 1,090 | 27 |

**The recovery log** (79 new rows): session starts / ends, pad slots, launch ports, the configs at the companion's
start — **no stall, hold, rewind or recovery row** (the only hold row: `input_hold_skipped_paused` at 00:11:50Z, the
first session's end, a skip), **`launch_orphaned` 0** (the whole log). No recovery row exists for a read's time to fall on.

**The reads** (`h7_reads.jsonl`, 442 rows over both sessions): **442 ok, 0 errors**; `read_ms` **median 38.2, p95 42.3,
worst 53.4**. The watcher's answers (1,349): 442 reads, 906 "not running" (no game), **1 "the game is busy (a save or a
load); not read"** (00:11:07Z, during the first launch — no read sent, not logged), 0 "not in time", 0 cached.

**Read as:** the stream's rows over the sitting are those of a normal session — no bitrate change, the same frame rate,
the PRESSURE flips at the rate of a session without reads, no stall, no orphan. **The reads did not disturb the stream.**
