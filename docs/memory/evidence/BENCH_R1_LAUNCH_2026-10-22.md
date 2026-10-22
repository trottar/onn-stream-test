---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: b909735
---

# BENCH-R1 — the loss cells and the blackout cells, the hold off and on: LAUNCHED (detached)

**Classification: LAUNCHED and RUNNING.** The driver runs as the systemd --user unit `privyhub-bench-r1`, from
2026-10-22T02:31:50Z. Cell 1 of 8 passed its preflight and was **PLAYING** at the 7000 start when this session exited. The record is a later task: "write BENCH-R1's record from the driver's
files" (`evidence/BENCH_R1_BLACKOUT_AND_LOSS_CELLS_2026-10-22.md`). Measurement only. Nothing adopted, nothing
committed.

Task: `handoffs/BENCH-R1_BLACKOUT_AND_LOSS_CELLS_TASK.md` §2 (the launch only), session A. **Baseline `b909735`**
(`baseline_head.txt`).
- The user committed session B's queue as `b909735`. Its message repeats `aa884a3`'s UX-R3 / LAN-R1 text. The content
  is B's queue: B1-B3, the records, and this task file. Disclosed, not changed.
- The tree was clean, the prompt and the task file included (both were committed). `git_status_at_start.txt` lists
  only `bench_r1_2026-10-22/`, which was created a moment before it was written.
- The flag names and profile strings are session B's (`SESSION_B_DONE_2026-10-22.md` item 8, the B1 / B2 records):
  - `blackout-4s@both,every=120s,seed=1` and `blackout-4s@down,every=120s,seed=1`, with no `@post-fec`;
  - cell 8 is `none@post-fec,seed=1`.
- **B2 was built,** so cells 6 and 8 run with `PRIVYHUB_INPUT_HOLD=250`.

## 1. Precondition (02:26-02:31Z)

- **`tools/e3_state.py --check`: ok** (`check_before.json`; again before the launch, `check_before_launch.json`).
  - eight adopted lines; no `e3_flag.conf`, no `e4_constraint.conf`;
  - no game, no RetroArch, no encoder;
  - APK CONFIRMED;
  - `adb` true without a reconnect. adb was only read; the endpoint was not printed.
- **One device paired, 0 sessions** (`session_status_before.json`; counts only).
- **No `privyhub-*` unit but the companion** (`units_before.txt`). The eight drop-ins were listed.
- **Code under test = HEAD:** `git diff HEAD -- companion tools` was empty.

## 2. The driver

**`bench_r1_driver.py`**, built from `g8_s5_driver.py`'s scaffolding.

**Kept:**
- the log; the atomic state and status files; the status line after every run, with a 5-min heartbeat;
- `history.csv`; the STOP file (`~/privyhub_bench_r1/STOP`); the busy skip (10 min × 3); the cap;
- the suite call with its timeout and SIGINT; the crash handler; `--dry`;
- the readings beside a run: the stream poll, the flags at stream time and under load, `wan`, the encoder command
  read back and masked;
- the ladder's reading, the journal reader, the host gates;
- `no_play` as an outcome; the profile-not-applied repeat; the state stop.

**The cells (task order), each E1-PS1-STREAM `--e2 --window 600`, a 120-s gap, a 7000 start (no
`PRIVYHUB_START_RUNG`), the suite launching the title:**

| # | `PRIVYHUB_IMPAIRMENT=` | other flags | environ lines |
| --- | --- | --- | ---: |
| 1 | `loss-1@post-fec,seed=1` | — | 10 |
| 2 | `loss-1@post-fec,seed=1` | `PRIVYHUB_LAN_LOSS_RULE=1` | 11 |
| 3 | `loss-5@post-fec,seed=1` | `PRIVYHUB_LAN_LOSS_RULE=1` | 11 |
| 4 | `burst-50x20@post-fec,seed=1` | `PRIVYHUB_LAN_LOSS_RULE=1` | 11 |
| 5 | `blackout-4s@both,every=120s,seed=1` | — | 10 |
| 6 | `blackout-4s@both,every=120s,seed=1` | `PRIVYHUB_INPUT_HOLD=250` | 11 |
| 7 | `blackout-4s@down,every=120s,seed=1` | — | 10 |
| 8 | `none@post-fec,seed=1` | `PRIVYHUB_INPUT_HOLD=250` | 11 |

- **Every drop-in also carries `PRIVYHUB_WAN_TELEMETRY=1`.** That is the scaffolding's base line, as in G8-S1's cells,
  so cell 1 is G8-S1's row again. It is telemetry only, and the WAN rules are off. The LAN loss rule reads the
  client-health telemetry, not this flag. Disclosed in the pre-registration.

**Changed from G8-S5:**
- **The applied check:**
  - G8-S1's tolerances for `none` / `loss-1` / `loss-5` / `burst-50x20`.
  - B1's blackout: dark spans of 3-6 s on the shim's 1-s lines, their starts 117-123 s apart within a stream start,
    no drop but `dropped_blackout`, `uplink_dropped` > 0 on `@both` and 0 on `@down`.
- **The logs copied per run (they rotate)** into `runs/<cell>/logs_run<n>/`, under their own names:
  - `native_stream_heartbeat.log`, `native_stream_ctrl_gaps.log`, `native_stream_recovery.log`,
    `native_frame_sizes.jsonl`, `adaptive_bitrate_shadow.jsonl`;
  - each from the live file and its newest `stream_log_archive/*.1`, over the run's span, de-duplicated, addresses
    masked;
  - so B2's reader (`tools/unattended_frames.py --logs`) and UX-R3's hitch script read them directly.
- **Added to each row:**
  - the recovery rows by event, with `desync_pause` by trigger and `resumed` by `via`, and `held_ms`;
  - the control gaps ≥ 250 / ≥ 1,000 ms;
  - the `lan_loss_rule` rows;
  - the shim's `dropped_blackout`, `uplink_dropped` and dark spans;
  - B2's reader over the run's span (`unattended_run<n>.json`). The record reads it again, per blackout.

**`bench_r1_suite_call.py`** is G8-S5's wrapper with only the pre-registration's name changed. It calls
`tools/e1_suite.py`'s `run_suite`, unedited, and refuses to run unless the pre-registration matches its hash.

**The readers were checked before the dry run** (read-only; output in `/tmp/bench_r1_readertest`, not deleted):
- G8-S1's shim lines read applied: cell 01 (`none`), 03 (`loss-1`, 0.991 %), 05 (`loss-5`, 4.985 %) and 07
  (`burst-50x20`, 35 bursts against 35 expected).
- A synthetic blackout series read applied: spans 120 s apart. The same series checked as `@down` was refused, as its
  uplink drops require.
- The log copy and B2's reader over last night's 04:50-05:00Z read the death's 967-ms gap, 8 gaps in 4 episodes, and
  99.5 unattended frames over 600 streaming seconds.

**`--dry` on cell 6's flags** (02:29:16-02:30:54Z; `dry_run/`, `dry_run_console.txt`):
- cell 6's drop-in was written (three lines) and the companion restarted;
- the environ read **11** lines (eight + three), all present;
- 30 s later the drop-in was removed and the companion restarted: `flags_absent` true, adopted8 ok;
- no stream ran.

## 3. Pre-registration and launch

- **`bench_r1_preregistration.txt`**, sha256 **`d7de4da0…e41d`** (`bench_r1_preregistration.sha256`), hashed at
  **02:31:42Z** (`preregistration_hashed_at.txt`), before the first cell.
- **It states, as the task does:**
  - the cells, the validity rule and the gates;
  - what is reported per cell, with the comparison rows (G8-S1 §2c's 03 / 05 / 07; UX-R3's death);
  - the seven expectations written beforehand;
  - the reading.
- **The cap:** `CAP_UTC: 2026-10-22T05:40:00Z`. That is the planned launch, 02:40Z, + 3 h.
  - **Disclosed:** the launch came 8 min before the planned time, so the cap is the real launch + 3 h 8 min.
  - Eight cells take about 2 h, so the cap does not bind.
- **`tools_at_preregistration_sha256.txt`:**

  | file | sha256 |
  | --- | --- |
  | `impairment.py` | `6db4712a…` |
  | `lan_loss_rule.py` | `7ce249c9…` |
  | `input_hold.py` | `877c701d…` |
  | `adaptive_bitrate_live.py` | `dffbacd2…` |
  | `games/link_drop_recovery.py` (recovery v2) | `e35a5a0c…` |
  | `native_session_io.py` | `9e6f6b61…` |
  | `native_stream.py` | `59c9ba27…` |
  | `tools/e1_suite.py` | `e72c7985…` |
  | `tools/unattended_frames.py` | `c18e4554…` |
  | the driver | `1db9dc17…` |
  | the wrapper | `8a77eb20…` |
  | the journal reader | `d0b892e6…` |
  | E4-S5D's analysis | `41cbb0c3…` |
  | `ux_r3_seconds.py` (the hitch definition) | `e9b2b3f7…` |

- **The launch** (02:31:50Z; `launched_at.txt`, `launch_console.txt`) came after a fresh `--check` ok:
  `systemd-run --user --unit=privyhub-bench-r1 --collect -p WorkingDirectory=<repo> /usr/bin/python3 -B …/bench_r1_driver.py`.
  - It printed "Running as unit: privyhub-bench-r1.service"; the invocation id is masked.

## 4. The first cell (`first_cell_preflight.txt`)

**01 loss-1, plain: the preflight passed, and the cell was PLAYING.** This is a confirmation at 02:34:50Z, not a
result. The record reads the cell.
- The suite passed its preflight (it refuses to continue otherwise), wrote the drop-in and restarted the companion.
- **PLAYING** on suite attempt 1 in **10.2 s** (02:34:21Z).
- **The environ: 10 lines.** That is the eight adopted lines, all present, plus `PRIVYHUB_IMPAIRMENT=loss-1@post-fec,seed=1`
  and `PRIVYHUB_WAN_TELEMETRY=1`. There is no `PRIVYHUB_START_RUNG`.
- **The encoder** (read back 02:34:13Z, masked): `-b:v 7000k -maxrate 7000k -bufsize 7000k`, no `-rc_mode`.
- The stream poll reads `bitrate_kbps` 7000 at 1280×720: **the 7000 start**.
- **The shim is live:** `loss-1`, post-fec, seed 1. At t_s 26 it read 960 packets in the second, 10 `dropped_loss`, and 0
  blackout / uplink drops.
- **The unit:** `systemctl --user status privyhub-bench-r1` reads active (running) (`unit_status_after_launch.txt`).

## 5. For the user

- **Status:** `cat ~/privyhub_bench_r1/status.txt`. The heartbeat is at most 5 min old.
- **Expected end:** about 04:30Z, eight cells of about 14-15 min each.
- **To stop early:**
  1. `touch ~/privyhub_bench_r1/STOP`;
  2. wait for `EXITED (the stop file)` (≤ 15 min).

  The cells done so far stand.
- **The TV and the onn stay on and idle on the LAN.** Nobody plays. A game started by hand is waited out (busy).
- **The record when it ends:** "write BENCH-R1's record from the driver's files". It covers:
  - the per-cell tables; the hitch seconds by UX-R3's script; the unattended frames per blackout by B2's reader;
  - the reading applied;
  - `KNOWN_ISSUES.md`, the ROADMAP lines and `CURRENT.md`'s Next Action.

## 6. Files

- **`bench_r1_2026-10-22/`:**
  - the start: `baseline_head.txt`, `git_status_at_start.txt`, `check_before.json`, `session_status_before.json`,
    `units_before.txt`;
  - the code: `bench_r1_driver.py`, `bench_r1_suite_call.py`;
  - the dry run: `dry_run/`, `dry_run_console.txt`;
  - the pre-registration: `bench_r1_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`,
    `tools_at_preregistration_sha256.txt`;
  - the launch: `check_before_launch.json`, `launched_at.txt`, `launch_console.txt`, `unit_status_after_launch.txt`,
    `first_cell_preflight.txt`;
  - `redact_check.txt`: 39 files OK at the launch. One HIT, cell 1's `title.txt`, is the core's version string
    (`Beetle PSX HW <version>`), OK (benign) on the re-check, as G8-S5's.
  - The driver keeps writing `runs/`, `cells.jsonl` and `bench_r1_state.json` until it ends.
- **`logs/bench_r1_launch_git_status.txt`.**
- **Not done:** no sudo, no nft, no Opal access, adb only read.
- **Not written:** no address, token or identifier.
- **Nothing** fetched, deleted, adopted or committed.
