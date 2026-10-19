---
memory_schema: 1
as_of: 2026-10-19
baseline_commit: 7a1ab60
---

# G8-S5 — the cap cell with the encoder's `tight` rate control (launch and record)

**Classification: MEASURED; 2 of 2 cells valid, host gates met in both. Nothing adopted, nothing committed.**

- **A (control, flag absent) and B (`PRIVYHUB_ENCODER_RC=tight`)** both reached PLAYING under cap-6000 at the 5000
  start and held 5000 (`at_floor`), as G8-S3's cell 1 did.
- **Cell A went silent on the client 235 s into its window.** At 14:53:52Z a `client_output_silence` pause began.
  Recovery made 5 encoder restarts, then gave up and saved the game at 14:55:52Z. The max output gap was 366,811 ms.
  This is the pattern G8-S3's cell 2 showed without the flag. Cell B held its whole window with no pause (max gap
  388 ms).
- **Over the window as run:** rendered **21.00 → 54.74 fps**, post-FEC loss 3,934 → 1,598/min, tail drop 11.19 → 4.50 %.
  A's figures include its ~6-min silence.
- **Paired over the first 235 s of each window (before A's pause):**
  - tail drop **6.52 → 4.43 %** (−32 %);
  - per-second drop p95 **19.68 → 15.75 %** (not halved), max 43.1 → 18.8 %, median 3.21 → 2.42 %;
  - rendered **53.45 → 55.12 fps**; loss 2,286 → 1,534/min;
  - the largest frame **89,248 B in both**.
- **Against G8-S3 cell 1:** A's first 235 s read as G8-S3's cell 1 did (6.52 % against 6.75 % dropped, 53.45 against
  53.08 fps). Today's control matched the earlier run until its pause.
- **The pre-registered reading:** the per-second drop p95 did not halve, so neither "candidate" branch applies. As
  written, the bench's p95 result did not transfer and the item closes as measured. Beside that: the tail drop and the
  loss fell by about a third, and only the control cell paused. That is one run each; no cause is chosen.

- **Task:** `handoffs/G8-S5_CAP_CELL_ENCODER_RC_TIGHT_TASK.md`, session A. Session B (CL-B7P) worked in `android/` /
  `PrivyHub/` in parallel.
- **Pre-registration:** `g8_s5_2026-10-19/g8_s5_preregistration.txt`, sha256 **`4adef199…32f8`**, hashed at
  14:41:47Z, before the first cell. It has the cap written in it: `CAP_UTC: 2026-10-19T16:45:00Z` (launch + 2 h).
- **The reading:** `g8_s5_record_read.py` → `record_read.json`, `record_read_console.txt`;
  `g8_s5_split_heartbeat.py` → `split_heartbeat.json`.
- **Bench:** `G8_S4_ENCODER_RATE_HEADROOM_2026-10-18.md` §3.3. **Counterpart:** `G8_S3_CAP_CELLS_START_RUNG_2026-10-17.md`
  cell 1 and §3.

## 1. Precondition (14:36-14:42Z)

- **`--check` ok on the eight adopted lines** (`check_before.json`). No `e3_flag.conf`, no `e4_constraint.conf`, no
  game, no RetroArch, no encoder; APK CONFIRMED.
  - **adb:** the onn was off adb after G4-S3 (`adb: false` at the first read). It was reconnected by hand with
    `adb connect`, using the endpoint taken from the companion's own recent journal inside one shell command. Nothing
    was printed or written. adb was then used only for state reads.
- **One device paired** (`session_status_before.json`, counts only).
- **No `privyhub-g8-*` / `privyhub-g4-*` unit** (`units_before.txt`); the eight drop-ins listed.
- **HEAD `7a1ab60`** (`baseline_head.txt`), and `git diff HEAD -- companion tools` was empty: the code under test is
  HEAD.
- **The tree** (`git_status_at_start.txt`) carried only the two prompts and the two task files (G8-S5's and CL-B7P's).

## 2. The driver, the dry run, the launch

- **`g8_s5_driver.py`, built from `g8_s3_driver.py`'s scaffolding.**
  - **Kept:** the log, the atomic state and status files, the 5-min heartbeat, `history.csv`, `STOP`, the busy skip,
    the suite call with its timeout and SIGINT, the crash handler, `--dry`, the shim's applied check, `no_play` as an
    outcome, the profile-not-applied repeat, and the state stop.
  - **The cells:** two (A control, B `tight`).
  - **The cap** is read from the pre-registration's `CAP_UTC:` line. If the line is absent, no cell starts.
  - **Three added readings:**
    1. **The encoder's command,** read from `/proc/<pid>/cmdline` 3 s after each new encoder pid. It is masked before
       it is kept (E4-S5B's method: argv[0], device, window, display and sink), and stored as the masked argv, its
       sha256 and the four rate values (`encoder_cmd_run1.jsonl`).
    2. **The relay's per-second frame log** over the run, copied in from the live file and its newest archive
       (`frame_sizes_run1.jsonl`).
    3. **From the summary:** the encoder's % of a core, the max output gap and the audio columns.
  - **One fix:** the ladder's archive path. G8-S3 read `logs/games/archive/`, which does not exist; the rotation
    writes to `stream_log_archive/`. The ladder's log did not rotate during this run. **The frame log did rotate**,
    at ~15:10Z during cell B. The copy read the archive and the live file (700 rows), and B's 600 window seconds all
    matched.
- **`g8_s5_suite_call.py`:** G8-S3's wrapper, with only the pre-registration's name changed. It calls `run_suite`
  (unedited) and refuses to run unless the pre-registration matches its hash.
- **`--dry`** (14:39:38-14:41:15Z; `dry_run/`, `dry_run_console.txt`): cell B's drop-in was written and the companion
  restarted. The environ read **12** lines, all flags present. 30 s later the drop-in was removed: `flags_absent`
  true, adopted8 ok. No stream ran.
- **`tools_at_preregistration_sha256.txt`:**

  | file | sha256 |
  | --- | --- |
  | `encoder_rc.py` | `a3d086a5…` |
  | `start_rung.py` | `92fa69f6…` |
  | `impairment.py` | `1fe14437…` |
  | `adaptive_bitrate_live.py` | `4dbbb540…` |
  | `native_stream.py` | `59c9ba27…` |
  | `tools/e1_suite.py` | `2fc42bfa…` |
  | the driver | `08926c19…` |
  | the wrapper | `5025c9ab…` |
  | G8-S1's journal reader | `d0b892e6…` |
  | E4-S5D's analysis | `41cbb0c3…` |

- **The launch** (14:42:17Z, after a fresh `--check` ok, `check_before_launch.json`):
  `systemd-run --user --unit=privyhub-g8-s5 --collect -p WorkingDirectory=<repo> -E PYTHONDONTWRITEBYTECODE=1
  /usr/bin/python3 -B …/g8_s5_driver.py`. The invocation id is masked (`launch_console.txt`).
- **Cell A's preflight passed** (`first_cell_preflight.txt`): preflight ok (8 lines), and the restart environ read 11.
- **The wait:** the status file was polled every 60 s. The driver closed itself at **15:14:55Z** ("all 2 cells done"),
  33 min after launch. The unit was collected (`unit_status_at_record.txt`: not found).

## 3. The cells

**Flags and validity** (`validity.json`):
- The drop-ins were present at stream time and under load: **11** lines in A, **12** in B.
- `flags_absent` was true after each cell, after A's failed first attempt, and in each final state.
- The shim's cap check held: output at most 6,015.1 / 6,014.4 kbit/s (G8-P1's tolerance is 1.05 × cap). There was no
  random, burst or reorder drop, and `send_errors` was 0.

**The encoder command, read back live** (`record_read.json` → `encoder_cmd`):
- **A:** 7 encoder starts (the two attempts and the 5 recovery restarts), every one with one masked sha256
  `38df744f…`. Each had `-b:v 5000k -maxrate 5000k -bufsize 5000k` and **no `-rc_mode`**: today's options.
- **B:** 1 encoder start, masked sha256 `1842ad94…`, with `-b:v 5000k -maxrate 5000k -bufsize 1250k -rc_mode CBR`.
- **`encoder_rc.apply_to(A's masked argv, "tight", 5000)` equals B's masked argv, byte for byte.** The two differ only
  by the profile's values and the inserted `-rc_mode CBR` pair (41 against 43 args).
- "Byte for byte as today" for A rests on two things: the code under test is HEAD (`git diff` empty), and G8-S4 §3.1
  proved the flag-absent builder identical to its predecessor.

| | **A · control** | **B · tight** | G8-S3 cell 1 (2026-10-17) |
| --- | --- | --- | --- |
| outcome / validity | playing / valid | playing / valid | playing / valid |
| PLAYING (suite attempt, s) | **2** (attempt 1 `no_play`: 49.7 s, 2,371 frames, recovery ENDED), 2.1 s | **1**, 3.0 s | 1 (client launch 2), 9.1 s |
| start rung (ladder log) | 5000, `floor`, list 5000/5500/6000/7000, `lan` | the same | the same |
| rung path; transitions | 5000; none | 5000; none | 5000; none |
| ladder | `at_floor` ROUTINE 5, FALLBACK 1; 5 `ssrc_change`; samples HOLD_DOWN 179, RECOVERY_PROBATION 160, PRESSURE 28 | `at_floor` ROUTINE 13; samples RECOVERY_PROBATION 297, PRESSURE 49 | `at_floor` ROUTINE 15, FALLBACK 1 |
| **shim input kbit/s, window: mean / median / p95 / max; > 6000** | 6,024.5 / 6,038.2 / 6,421.6 / 9,587.7; 72.2 % | 6,026.2 / 6,021.3 / 6,414.5 / **7,204.7**; 53.7 % | 6,039.0 / 6,034.2 / 6,988.6 / 9,422.1; 54.7 % |
| **tail drop: window / whole stream** | 11.19 % / 9.91 % | **4.50 % / 4.38 %** | 6.75 % / 6.55 % |
| **per-second drop, window: median / p95 / max** | 14.01 / 15.46 / 43.11 % | **2.64 / 15.75 / 22.65 %** | 3.48 / 23.35 / — % |
| H.264 payload kbit/s, window: mean / p95 / max | 4,999.5 / 5,398.3 / 7,527.9 | 5,013.7 / **5,332.7 / 5,895.4** | 5,012.1 / 5,943.8 / 7,886.2 |
| largest frame per second: median / max (B) | 87,053 / 89,248 | 41,846 / **89,248** | 40,325 / 89,248 |
| post-FEC loss /min | 3,934.5 | **1,597.7** | 2,378.7 |
| FEC recovered / unrecoverable (last heartbeat) | 504 / 918 | 1,231 / 359 | 806 / 517 |
| **rendered fps** | **21.00** | **54.74** | 53.08 |
| stale /min; resyncs (heartbeat / report) | 1.64; 11 / 6 | 1.98; 0 / 0 | 2.99; 3 / 5 |
| client pauses; recovery | **1**: `client_output_silence` 14:53:52Z → 5 `encoder_restart` → `gave_up_saved` 14:55:52Z | 0 | 0 |
| max output gap ms (report) | **366,811** | 388 | 492 |
| `wan` class (last); windows | capacity-limited; capacity-limited 39, lossy 27, starved 2 | latency-limited; lossy 53, capacity-limited 11, starved 2, latency-limited 1 | capacity-limited; lossy 48, capacity-limited 18, starved 2 |
| host gates: RetroArch, capture, dup+drop | **met**: 59.999, 60.002, 0.0/min | **met**: 59.999, 59.996, 0.1/min | met: 59.999, 59.987, 0.10/min |
| host CPU; companion; **encoder** (% of a core) | 8.68 %; 24.1 %; **38.38 %** | 11.95 %; 24.8 %; **40.40 %** | 11.88 %; 28.3 %; 35.59 % |
| shim CPU (% of a core); queue max | 5.25; 75 | 5.16; 76 | 5.07; 76 |
| *audio (reported, not compared):* underruns report / window; net loss pkts; spikes ≥ 50 ms; ≥ 20 ms /min | 9 / 6; 9; 32; 108.4 | 14 / 14; 11; 41; 278.2 | PCM: 21 / 9; 63; 52; 226.5 |

**Notes on the table:**
- **The "whole stream" fraction** covers the shim's whole run: both of A's attempts, the warm-up, the window and the
  teardown. The window figures are the 600 s matched second by second to the frame log (alignment score 0.034 /
  0.029).
- **A's window after 14:53:52Z:**
  - the client rendered nothing;
  - the stream status read `active` 5000 HOLD_DOWN to the end;
  - the shim kept receiving ~6 Mbit/s, with a per-second drop near 14 % and an ~87-KB largest frame in most seconds.
  These figures fill A's window table. They are reported, not explained.
- **G8-S3 cell 1's per-second drop max** was not computed by G8-S3's reader (its frame log was not copied).
- **The audio columns** are not comparable with G8-S3: it ran PCM, and today runs Opus. Audio is not on the shim
  (§3 of G8-S3).

## 4. Paired before the pause (the first 235.4 s of each window)

`record_read.json` → `wire_first_split_s`; `split_heartbeat.json` (`tools/e1_suite.py`'s own `heartbeat_figures` over
the same span; its whole-window call reproduces the suite's figures).

| | A · control (14:49:57-14:53:52Z) | B · tight (15:04:22-15:08:17Z) | B / A |
| --- | --- | --- | --- |
| H.264 payload kbit/s: mean / median / p95 / max | 5,010.8 / 4,996.8 / 5,757.7 / 7,527.9 | 5,014.0 / 5,012.5 / **5,366.8 / 5,593.6** | p95 0.93, max 0.74 |
| share of seconds with payload > 5000 | 49.2 % | 57.6 % | |
| shim input kbit/s: mean / median / p95 / max | 6,034.9 / 6,027.6 / 7,358.1 / 9,587.7 | 6,024.6 / 6,013.3 / **6,378.1 / 7,204.7** | p95 0.87, max 0.75 |
| share of seconds with input > 6000 | 53.4 % | 52.5 % | |
| **tail-dropped fraction** | **6.52 %** | **4.43 %** | **0.68** |
| drop in seconds over / at-or-under the cap (share of drops in seconds over) | 7.81 % / 4.86 % (67.5 %) | 4.21 % / 4.69 % (51.1 %) | |
| **per-second drop: median / p95 / max** | 3.21 / **19.68** / 43.11 % | 2.42 / **15.75** / 18.83 % | **p95 0.80**, max 0.44 |
| largest frame per second: median / p95 / max (B) | 39,902 / 87,790 / 89,248 | 41,846 / 87,526 / 89,248 | max 1.00 |
| parity per data packet; per frame | 0.178; 1.81 | 0.178; 1.81 | |
| **rendered fps** (heartbeats) | **53.45** | **55.12** | +1.67 fps |
| post-FEC loss /min | 2,285.8 | 1,534.0 | 0.67 |
| resyncs; max last-output age ms | 1; 1,124 | 0; 108 | |

**Read plainly:**
- **`tight` did what G8-S4 built it for, on the encoder's side.** The per-second payload p95 fell 5,758 → 5,367 and the
  max 7,528 → 5,594, and the shim's input max fell 9,588 → 7,205. Those are the bench's direction and about its size
  (G8-S4 at 5000: p95 5,605 → 5,298, max 5,976 → 5,535). The mean did not move (~6,030 at the shim, the cap's level).
- **The drop spread out.** In A, two thirds of the drops fall in the seconds over the cap. In B, the drop is about the
  same in seconds over and under (4.2 / 4.7 %). The tail fraction fell by a third, the per-second max by more than half,
  but **the per-second p95 only by a fifth** (the bench: 17.1 → 8.0 %).
- **The largest frame per second did not change** (89,248 B max in both, against D-BASE-P6a's 90,000 cap). The 250-ms
  buffer did not cap the single-frame burst; the frame cap still sets it.
- **Rendered fps** before the pause: 53.45 → 55.12. Over the window: 21.00 → 54.74, which is A's pause.

## 5. The pre-registered expectations and the reading

| written beforehand | result | |
| --- | --- | --- |
| 1. B's per-second drop p95 at most half of A's | window 15.75 vs 15.46 % (1.02); before the pause 15.75 vs 19.68 % (0.80) | **not met** |
| 2. B's tail drop lower than A's by about a quarter (bench 4.67 → 3.42) | before the pause 6.52 → 4.43 % (−32 %); window 11.19 → 4.50; whole stream 9.91 → 4.38 | **met** |
| 3. B's largest-frame-per-second max well under A's ~89 KB | 89,248 B in both | **not met** |
| 4. whether rendered rises from ~53 (the open question) | before the pause 53.45 → 55.12 fps; window 21.00 → 54.74 (A paused and gave up 235 s in; B held) | stated |
| 5. the encoder's CPU in B within 10 % of A's | 40.40 vs 38.38 % of a core (+5.3 %) | **met** |

**The reading, as written beforehand:**
- "If B's drop p95 halves and rendered rises → a candidate": **does not apply**, because the p95 did not halve.
- "If the drop p95 halves but rendered does not move → smoothness, no frames": **does not apply.**
- "If neither → the bench did not transfer and the item closes as measured": **this is the branch the written reading
  gives.** On the pre-registered measure, the per-second drop p95, the bench's halving did not appear live.

**Stated beside the reading, not substituted for it:**
- The tail drop and the post-FEC loss each fell by about a third, and rendered rose 1.7 fps before the pause.
- The control cell went silent and recovery gave up at 235 s; the `tight` cell held 600 s. G8-S3's flag-absent cell 2
  did the same at 417 s, and its cell 1 held.
- This is one run per arm. Whether `tight` affects how often a capped stream goes silent is not shown by two cells.
- The picture cost, if the user weighs it anyway: G8-S4's −0.45 dB PSNR avg, −2.4 to −3.4 dB on the worst frame.
- Nothing is adopted. Pursuing it further (more paired runs aimed at the silence) is the user's call.

## 6. Files; disclosures

- **`g8_s5_2026-10-19/`:**
  - **the start:** `baseline_head.txt`, `git_status_at_start.txt`, `check_before.json`, `session_status_before.json`,
    `units_before.txt`;
  - **the code:** `g8_s5_driver.py`, `g8_s5_suite_call.py`;
  - **the dry run:** `dry_run/`, `dry_run_console.txt`;
  - **the pre-registration:** `g8_s5_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`,
    `tools_at_preregistration_sha256.txt`;
  - **the launch:** `check_before_launch.json`, `launched_at.txt`, `launch_console.txt`, `first_cell_preflight.txt`,
    `unit_status_after_launch.txt`;
  - **the driver's own files:** `cells.jsonl`, `g8_s5_state.json`, and `runs/`, with both cells' suite outputs, the
    shim's per-second files (`impairment_run1.jsonl`), the relay's frame log over each run (`frame_sizes_run1.jsonl`),
    `encoder_cmd_run1.jsonl`, `ladder_log_run1.jsonl`, `stream_poll_run1.jsonl`, `wan_poll_run1.jsonl` and
    `companion_journal_run1.txt`;
  - **copied from `~/privyhub_g8_s5/`:** `final_status.txt`, `history.csv`, `driver.log`;
  - **the record:** `check_record.json`, `session_status_record.json`, `unit_status_at_record.txt`, `record_head.txt`,
    `git_status_at_record_start.txt`, `g8_s5_record_read.py`, `record_read.json`, `record_read_console.txt`,
    `g8_s5_split_heartbeat.py`, `split_heartbeat.json`, `validity.json`, `redact_check.txt`, `manifest.sha256`.
- **`logs/g8_s5_git_status.txt`.**
- **At the record** (15:15Z):
  - `--check` ok on the eight lines (`check_record.json`);
  - no `e3_flag.conf`, no game, adb connected and only read;
  - one device paired, 0 sessions.
- **Session B, in parallel:** its uncommitted edits appeared in the tree during the run (`PrivyHub/…` Opus decode files,
  `tools/cl_b7_onn_threads.py`, `cl_b7p_2026-10-19/`; `git_status_at_record_start.txt`). None is under `companion/`,
  and none was touched here. The APK read CONFIRMED before and after, so nothing was installed on the onn during the
  unit. Whether session B built during the unit is not shown by these files.
- **The recovery rows** in `runs/` and `record_read.json` carry the game's state-file name, as G8-S3's did. It is not
  reproduced here.
- **Not written:** no address, token or identifier. The adb endpoint was never printed (§1). RetroArch's core version
  in `title.txt` is the only dotted quad in the directory (`redact_check.txt`).
- **One deletion, disclosed:** the `__pycache__/` that `py_compile` created in this directory while the driver was
  being checked was removed seconds later. It was a byte-code cache this session had just made, not data. Nothing else
  was deleted. The record reader's `__pycache__/` remains and is excluded from the manifest.
- **Not done:** no sudo, no nft, no Opal access, nothing fetched, nothing adopted, nothing committed. The eight lines
  only, and no `e3_flag.conf`, at the end.
