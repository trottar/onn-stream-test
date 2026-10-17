---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 0093b7c
---

# G8-S3 — the cap cells with the start rung (record)

**Classification: MEASURED; 3 of 3 cells valid.**

- **Cells 1 and 2 (cap-6000) reached PLAYING at the 5000 start:** 9.1 s and 7.1 s, both on the suite's first
  attempt. Host gates met in both.
- **Cell 3 (cap-4500): `no_play`, as predicted.**
- **Cell 2 did not hold to the window's end.** At 18:04:16Z, 417 s into the window, a client pause
  (`client_output_silence`) began. Recovery v2 made 5 encoder restarts, then gave up and saved the game at 18:06:16Z.
  Cell 1 held the whole window with no pause.
- **The 5000 rung's live wire rate under the shim:** mean 6,039 kbit/s, close to G8-S2's bench of 6.10-6.14 Mbit/s and
  not above it. The tail drop was 6.75 % against the bench's 1.8-2.4 %. On the mean, the extra drop is unexplained. The
  term that differs from the bench is the spread of frame sizes and per-second rates (§3).

Measurement only. Nothing adopted, nothing committed. The driver was not relaunched.

- **Task:** `handoffs/G8-S3_RECORD_TASK.md`, session A.
- **Pre-registration:** `handoffs/G8-S3_CAP_CELLS_START_RUNG_TASK.md` §1, as hashed in
  `g8_s3_2026-10-17/g8_s3_preregistration.txt`. Its sha256 is `e3f0675a…20d7`, re-read unchanged at this record.
- **Launch:** `G8_S3_LAUNCH_2026-10-17.md`.
- **Counterparts:** `G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` §5, cells 17-19.
- **Bench:** `G8_S2_START_RUNG_2026-10-17.md` §3.
- **The reading:** `g8_s3_2026-10-17/g8_s3_record_read.py` → `record_read.json`, `record_read_console.txt`.
- **HEAD `0093b7c`**, the code under test.

## 1. The end and the state

- **The driver** (`final_status.txt`, `driver.log`, `history.csv`, copied from `~/privyhub_g8_s3/`) closed itself
  "all 3 cells done" at 18:21:36Z. The cells ran 17:38:38-18:21:36Z.
- **The unit** `privyhub-g8-s3` is collected (`unit_status_at_record.txt`: not found).
- **At this record** (18:51Z):
  - `--check` ok on the seven adopted lines (`check_record.json`);
  - no `e3_flag.conf`, no game, adb connected (read only);
  - one device paired, 0 sessions (`session_status_record.json`).
- **The tree** (`git_status_at_record_start.txt`): committed through G8-S2. Beside it, uncommitted: the launch's files,
  the two task files and `_cowork_prompt.txt`.

## 2. The cells (the pre-registered reported set)

**Flags:**
- Every drop-in was present under load: 10 environ lines in cells 1 and 3, and 11 in cell 2 (seven plus three or four).
- `flags_absent` was true after every cell, after each of cell 3's three attempts, and in each final state.
- The shim's cap check held in all three cells: output at most 6,013.3 / 4,509.7 kbit/s, no random, burst or reorder
  drop, `send_errors` 0.

| | 1 · cap-6000, rules off | 2 · cap-6000, rules on | 3 · cap-4500, rules off |
| --- | --- | --- | --- |
| outcome / validity | **playing** / valid | **playing** / valid | **no_play** / valid |
| PLAYING (suite attempt, client launch, s) | 1, 2, **9.1 s** | 1, 1, **7.1 s** | none in 3 attempts (6 client sessions) |
| start rung, first row with `start_rung` (ladder log) | **5000, `floor`**, requested `floor`, list 5000/5500/6000/7000, `lan`, 17:41:08Z | the same, 17:55:41Z (one row; the 5 encoder-only restarts wrote none) | the same on all 6 client sessions' rows, 18:10:10-18:20:18Z |
| wire rung (status / encoder `-b:v`) | 5000 / `5000k` in every poll | 5000 / `5000k` | 5000 / `5000k` |
| rung path; acted transitions | **5000; none** | **5000; none** | 5000; none |
| ladder refusals | `at_floor` ROUTINE 15, FALLBACK 1 | `at_floor` ROUTINE 11, FALLBACK 4 | `at_floor` FALLBACK 6 |
| rules' suggestions, by rule id | — (off) | **R5.1 `no_step_up` 255** (240 `none`, 15 `refused:at_floor`); **R1.2 `no_step_up` 73**; **R1.1 `hold` 17** | — (off) |
| post-FEC loss /min | 2,378.7 | 3,244.6 | — (no window) |
| FEC recovered / unrecoverable (last heartbeat) | 806 / 517 | 746 / 719 | 48-78 / 87-111 per session |
| rendered fps | **53.08** | **36.65** | — (19-32 frames per session) |
| stale /min; resyncs (heartbeat / report) | 2.99; 3 / 5 | 2.74; 13 / 8 | —; 0-2 per session |
| client pauses; recovery rows | 0; 0 | **1** (`client_output_silence` 18:04:16Z) → 5 `encoder_restart` → `gave_up_saved` 18:06:16Z | — |
| max output gap ms (report) | 492 | **185,954** | 21,000-47,758 |
| `wan` class (last); windows | capacity-limited; lossy 48, capacity-limited 18, starved 2 | latency-limited; lossy 36, capacity-limited 30, starved 2, latency-limited 1 | latency-limited; latency-limited 2, starved 1 |
| shim in / out packets | 505,346 / 472,268 | 500,946 / 457,706 | 233,226 / 168,213 (6 starts) |
| dropped_queue (fraction); queue max | 33,078 (6.55 %); 76 | 43,207 (8.63 %); 75 | **64,745 (27.76 %)**; 55 |
| host gates: RetroArch, capture, dup+drop | **met**: 59.999, 59.987, 0.10/min | **met**: 59.999, 60.041, 0.10/min | not evaluable (no window) |
| host CPU; companion | 11.88 %; 28.3 % of a core | 12.26 %; 28.6 % | — |

**Notes on the table:**
- **Why no transition was expected, from the code:**
  - On the LAN the active list is `LAN_LIST = (5000, 5500, 6000, 7000)` (`companion/start_rung.py`, equal to
    `adaptive_bitrate.LADDER_KBPS`), so 5000 is its lowest rung.
  - A down-step at that level is refused: `if direction == "down" and target >= self.level_kbps: reason = "at_floor"`
    (`adaptive_bitrate_live.py`).
  - An up-step needs R5.1's increase rule: 85 of the last 90 reports clean (fps ≥ 57, queue ≤ 1, gap ≤ 150). Cells 1-2
    never reached it: their sample states were RECOVERY_PROBATION 265 / 194, PRESSURE 82 / 64, HOLD_DOWN 0 / 88.
  - So the ladder could only hold, and every refusal reads `at_floor`.
- **The loss figures:**
  - Post-FEC loss and rendered are the window's heartbeat figures.
  - The shim's fraction covers its whole stream: warm-up, window and teardown. The window-only fractions are in §3.
- **Cell 3's suite attempts:** the driver's `suite_attempts` field reads 2 because it counts only the
  `summary_failed_attempt*.json` files. The third attempt is `summary.json` (FAILED, `flags_absent` true). It made
  3 attempts and 6 client sessions (§5).

## 3. The live wire rate at 5000 against the bench, term by term

**The sources:**
- **The shim's per-second bytes and packets in** (`impairment_run1.jsonl`).
- **The FEC relay's own per-second frame log** (`logs/games/native_frame_sizes.jsonl`, read only):
  - the H.264 RTP payload bytes (no RTP header, no parity), the RTP data packets, frames, and the largest and mean frame
    per second;
  - matched second by second to the shim by packet count (alignment score 0.03-0.04).
- **The encoder's log** (`logs/games/native_video_alpha.log`, read only): the cumulative bitrate and muxing overhead.

**`encoder.jsonl` holds no bitrate.** The sampler keeps only frame / fps / dup / drop / speed. The encoder's actual
output is therefore read from the relay's payload bytes, and it is cross-checked against the encoder's own log.

**The terms (code):**
- **Each data datagram** is a 12-B RTP header plus its payload; ffmpeg's `pkt_size=1200` makes the payload at most
  1,188 B.
- **Each XOR parity datagram** is a 23-B `FEC_HEADER` plus the group's largest payload. A group holds up to 8 data
  packets and closes at each frame's end.
- **Audio is not on the shim.** It is built only inside `NativeVideoFecRelay`. The audio term on the capped hop is 0.

**The window, per second** (cell 1: 600 s; cell 2: 600 s, and its 417 s before the pause):

| term | bench (G8-S2, 5000) | cell 1 | cell 2 (window) | cell 2 (before the pause) |
| --- | --- | --- | --- | --- |
| H.264 payload kbit/s: mean / median / p95 / max | synthetic: 10,439 B × 60 = 5,010, flat; recorded starts: CBR-scaled per-second aggregates, re-timed evenly | **5,012.1** / 5,011.4 / **5,943.8** / 7,886.2 | 4,997.8 / 4,999.7 / 5,709.1 / 7,945.6 | 5,010.9 / 5,005.0 / 5,955.4 / 7,945.6 |
| share of seconds with payload > 5000 | — | **52.3 %** | 49.8 % | 51.3 % |
| RTP header kbit/s | — | 58.5 (609.1 data pkts/s) | 58.1 | 58.4 |
| parity kbit/s (shim bytes − payload − RTP header) | — | **968.4** | 971.7 | 971.6 |
| parity packets / s; per data packet; per frame | nominal 8+1: 0.125 per data packet | 108.6; **0.178**; 1.81 | 108.7; 0.180; 1.81 | 108.8; 0.179; 1.81 |
| parity bytes per parity packet | ≤ 23 + 1,188 = 1,211 | 1,114.9 | 1,117.5 | 1,116.0 |
| frames / s; data packets per frame (mean) | 60; ~9 | 60.0; 10.15 | 59.92; 10.10 | 60.0; 10.14 |
| largest frame in a second: median / max (bytes) | 10,439 (synthetic, every frame) | **40,325 / 89,248** | 57,306 / 89,157 | 41,269 / 89,157 |
| **shim input kbit/s: mean / median / p95 / max** | **6,103-6,137 (steady)** | **6,039.0** / 6,034.2 / 6,988.6 / 9,422.1 | 6,027.6 / 6,033.1 / 7,012.6 / 9,008.6 | 6,041.0 / 6,039.7 / 7,283.1 / 9,008.6 |
| share of seconds with input > 6000 | — | **54.7 %** | 63.0 % | 54.9 % |
| **tail-dropped fraction** | **1.8-2.4 %** | **6.75 %** | 9.18 % | 7.07 % |
| drop in seconds over / at-or-under the cap | — | 8.19 % / 4.80 % (69.8 % of the drops in seconds over) | 10.91 % / 5.90 % (77.8 %) | 9.00 % / 4.37 % (74.2 %) |
| per-second drop fraction: median / p95 | — | 3.48 % / 23.35 % | 9.27 % / 20.19 % | 3.36 % / 23.96 % |

**Read plainly:**
- **The encoder at the 5000 target:**
  - The window's mean payload is 5,012 kbit/s, and 52 % of seconds are above 5000 (p95 5,944, max 7,886).
  - The encoder's own log agrees on the mean: the session's cumulative 5,069.5 kbit/s includes its 1.263 % RTP muxing
    overhead, which leaves ≈ 5,006 kbit/s of video (cell 1).
- **Parity** runs 1.81 per frame, that is 0.178 per data packet, not 0.125. Most frames carry 9-11 data packets, which
  makes two groups and two parity datagrams.
- **The three terms** — payload 5,012 + header 58.5 + parity 968 — sum to the shim's 6,039 kbit/s. That holds by
  construction: parity is the remainder.
  - The parity term's two independent checks are consistent with the code's structure: 1,115 B per parity packet, just
    under the 1,211-B maximum, and 1.81 per frame.
  - No byte remainder is left over that the code does not account for.
- **Against the bench:**
  - **The mean wire rate does not exceed the bench.** It is 6,039 against 6,103-6,137, about 1-2 % lower.
  - Over the window the mean is 0.65 % above the cap. A flat stream at that mean would lose about 0.65 %.
  - The measured drop is 6.75 %. **About 6 points of the drop are unexplained by the mean terms.**
- **The term that differs from the bench is the spread:**
  - Per second, the payload ranges up to 7.9 Mbit/s and the input up to 9.4 Mbit/s.
  - 70 % of the drops fall in the 55 % of seconds whose input is over the cap.
  - The largest frame in a typical second is 40 KB, against the bench's flat 10.4 KB. The worst is 89 KB, more than the
    queue's 75 KB (100 ms of the cap).
  - G8-S2's synthetic source had none of this spread, and its recorded starts were re-timed evenly within each second.
- **Not shown by these files:** packet timing within a second. Both logs are 1-s aggregates. The files therefore cannot
  separate a burst at an I-frame from any other cause inside the second. No mechanism is chosen.

## 4. Cell 1 against cell 2 (rules off vs on): side by side, no cause chosen

| | cell 1 (off) | cell 2 (on) |
| --- | --- | --- |
| PLAYING | 9.1 s (client launch 2) | 7.1 s (client launch 1) |
| post-FEC loss /min (window) | 2,378.7 | 3,244.6 |
| rendered fps (window) | 53.08 | 36.65 |
| last `wan` class | capacity-limited | latency-limited (windows: capacity-limited 30, lossy 36) |
| the rules' rows | none (off) | R5.1 `no_step_up` 255, R1.2 `no_step_up` 73, R1.1 `hold` 17. Every one is a no-increase or hold suggestion. **None asked for a step down.** 15 were refused `at_floor` and the rest acted on nothing. |
| ladder | held 5000; no transition | held 5000; no transition; 5 `ssrc_change` (the restarts), 1 `escalation_armed`, blackout 15 samples, HOLD_DOWN 88 samples |
| client pause / recovery | none | 18:04:16Z `client_output_silence` → 5 encoder-only restarts at 5000 (C3-F1 lines in the encoder log, first RTP resume 408-682 ms) → `gave_up_saved` 18:06:16Z; max output gap 185,954 ms |
| **encoder output (payload), before cell 2's pause** | mean 5,012.1, p95 5,943.8, 52.3 % > 5000 | mean 5,010.9, p95 5,955.4, 51.3 % > 5000 |
| **shim input before the pause** | mean 6,039.0, 54.7 % > cap | mean 6,041.0, 54.9 % > cap |
| **tail drop before the pause** | 6.75 % (whole window) | 7.07 % |
| tail drop, whole window / whole stream | 6.75 % / 6.55 % | 9.18 % / 8.63 % |

- **Until 18:04:16Z the encoder's output and the shim's input were the same in the two cells,** to within 0.1 % on the
  mean. The drop was 7.07 % against 6.75 %.
- **The difference in the whole-window figures** comes with the pause and its five restarts, 18:04:16-18:06:16Z, and
  the last minute of the window after it. Over the whole window, cell 2's drop came to 9.18 %. Its largest
  frames per second were larger (median 57 KB against 41 KB before the pause), and its rendered fps and loss/min are
  window averages that include the 120-s silence.
- **The rules were on in cell 2. Every suggestion they made was a hold or no-increase. The ladder acted on none.**
  - Whether the rules had any effect on the stream is not shown by these files.
  - Cell 1 vs cell 2 is one run each. It is stated, not judged.

## 5. Cell 3 (`cap-4500` at 5000): the G8-S1 §5 reading

**The suite's attempts** (`summary_failed_attempt1/2.json`, `summary.json`):
- All three ended with "stream did not reach PLAYING: {'ok': False, 'recovery': 'ENDED'}".
- There were 6 client sessions, two launches per attempt, as in G8-S1.
- No window and no `recovery.jsonl` row; the ladder logged `at_floor` FALLBACK 6.

**The client's end-of-session report per attempt:**

| attempt | duration ms | rendered | lost packets | max output gap ms | resyncs | audio underruns |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 49,974 | 19 | 5,592 | 47,758 | 1 | 5,218 |
| 2 | 49,424 | 26 | 5,773 | 21,000 | 1 | 5,731 |
| 3 | 50,430 | 26 | 5,904 | 22,798 | 1 | 4,543 |

**The client's heartbeats** (the companion's journal, `companion_journal_run1.txt`, masked), per session at the last
heartbeat:
- `rendered_frames` 19-32;
- `rx_packets` 22,815-23,628, `lost_packets` 5,368-5,816 (23-25 %);
- `forward_gap_events` 2,701-2,857;
- FEC recovered 48-78, unrecoverable groups 87-111;
- `last_output_age_ms` 46,719 / 46,005 / 1,601 / 1,650 / 1,587 / 3,809.

**The shim's counters per stream start:**
- 6 starts of 48-60 s;
- steady input 6,103-6,295 kbit/s (median 6,194-6,233);
- output pinned at the cap (max 4,507-4,510 kbit/s);
- steady drop 27.0-28.4 %, queue max 54-55;
- in total, **64,745 of 233,226 packets dropped = 27.76 %**.

**The prediction held.** G8-S2's bench gave 28.9-29.9 % at 5000 under cap-4500, and `no_play` was expected; this cell
measured 27.76 % and `no_play`.

## 6. Against G8-S1's cells 17-19 (the same profiles at a 7000 start)

| | 17 cap-6000 off @7000 | **1 cap-6000 off @5000** | 18 cap-6000 on @7000 | **2 cap-6000 on @5000** | 19 cap-4500 off @7000 | **3 cap-4500 off @5000** |
| --- | --- | --- | --- | --- | --- | --- |
| PLAYING | none (3 attempts) | **9.1 s** | none (3) | **7.1 s** | none (3) | none (3) |
| shim steady input kbit/s | 8,252-8,259 | 6,039 mean (window) | 8,044-8,253 | 6,028 (window) | 8,252-8,259 | 6,103-6,295 |
| dropped fraction (shim, all starts) | 27.85 % | **6.55 %** (window 6.75 %) | 26.79 % | **8.63 %** (window 9.18 %) | 44.28 % | **27.76 %** |
| rendered | 20-25 frames per session | **53.08 fps** | 16-22 frames | **36.65 fps** | 11-14 frames | 19-32 frames per session |
| `wan` class | capacity-limited | capacity-limited | capacity-limited | latency-limited | capacity-limited | latency-limited |

## 7. What the files say about "settling under a cap"

- At the LAN floor the ladder has nowhere to go. Down is refused `at_floor` (§2), and up needs R5.1's clean reports,
  which a lossy capped link never gave.
- **Cell 1:** the stream stayed up for the whole 600-s window at 5000 under cap-6000, with no pause. It ran at
  2,379 loss/min post-FEC and 53.1 fps rendered, with a max output gap of 492 ms.
- **Cell 2:** the same start and the same cap. It held for 417 s, then went silent on the client. Recovery gave up
  after 5 restarts.
- **What did not happen:** the ladder never climbed back above the cap in either cell. The pre-registered "the climb
  will push it above the cap again" did not arise.
- **Whether a 53-fps, 2,400-loss/min stream is playable** is the user's judgement, not this record's.

## 8. Files; disclosures

- **`g8_s3_2026-10-17/`, added by the record:**
  - the driver's files: `final_status.txt`, `history.csv`, `driver.log`;
  - the state: `check_record.json`, `session_status_record.json`, `unit_status_at_record.txt`, `record_head.txt`,
    `git_status_at_record_start.txt`;
  - the reading: `g8_s3_record_read.py`, `record_read.json`, `record_read_console.txt`;
  - `validity.json`, `manifest.sha256`, and `redact_check.txt` (replaced, over the whole directory, `.pyc` excluded).
- **The driver's own files** are unchanged: `cells.jsonl`, `g8_s3_state.json`, `runs/`.
- **`logs/g8_s3_record_git_status.txt`.**
- **Read only, not copied:** `logs/games/native_frame_sizes.jsonl` and `logs/games/native_video_alpha.log`. Only numbers
  were taken. The latter's text holds addresses, none of which was written.
- **The encoder's argv banner** prints `encoder=7000 kbps` and the profile's 7000/7000 in every session, while its
  output line and SDP read 5000 kb/s. That is a label in the banner, stated, not changed.
- **Not written:** no address, token or identifier; the game's state-file name is not reproduced.
- **Not done:** no sudo, no nft, no Opal access.
- **Nothing** fetched, deleted, adopted or committed.
