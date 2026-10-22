---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 43a8df6
---

# BENCH-R2 — the lock, the hold, the stall signal: INSTALLED and LAUNCHED (detached)

**Classification: the candidate APK `cb0935c8…1080` INSTALLED (paired), and the driver LAUNCHED and RUNNING** as the
systemd --user unit `privyhub-bench-r2`, from 2026-10-22T14:09:00Z. Cell a1 (the lock A/B, no lock) passed its preflight and was **PLAYING** at the 7000 start when this session exited. The record is a later task: "write
BENCH-R2's record from the driver's files" (`evidence/BENCH_R2_LOCK_HOLD_STALL_CELLS_2026-10-23.md`). Measurement only.
Nothing adopted, nothing committed.

Task: `handoffs/BENCH-R2_LOCK_HOLD_STALL_CELLS_TASK.md` §2 (the install and the launch), session A.
- **Baseline `43a8df6`** (`baseline_head.txt`): queue C, ML-R1 and BENCH-R1's record, committed by the user.
- The tree was clean but for the prompt and the task file. `git_status_at_start.txt` also lists `bench_r2_2026-10-22/`,
  created a moment before it was written.
- **The flag names, property names, profile strings and the APK hash are session B's** (`SESSION_B_DONE_2026-10-22C.md`
  items 8-9; the B5 / B6 / B7 / B1b / LAN-R2 records).

## 1. Precondition (14:02-14:04Z)

- **`tools/e3_state.py --check`: ok** (`check_before.json`).
  - eight adopted lines; no `e3_flag.conf`, no `e4_constraint.conf`;
  - no game, no RetroArch, no encoder;
  - **APK `93d29b4a…` CONFIRMED;**
  - `adb` true without a reconnect, the endpoint never printed.
- **One device paired** (`session_status_before.json`; counts only). One session-identity session was active (the
  paired client), not a game.
- **The three properties read empty:** `debug.privyhub.wifi_lock`, `stall_signal`, `link_report`.
- **No `privyhub-*` unit but the companion** (`units_before.txt`).
- **Code under test = HEAD:** `git diff HEAD -- companion tools` was empty.

## 2. Pre-registration (before the install)

- **`bench_r2_preregistration.txt`**, sha256 **`45046008…e2fc`** (`bench_r2_preregistration.sha256`), hashed at
  **14:04:37Z** (`preregistration_hashed_at.txt`), before the install and before the first cell.
- **It states, as the task does:**
  - the fifteen cells with their shim lines, flags, properties and workloads;
  - the validity rule, now with the properties read back empty at teardown;
  - the four gates; what is reported per cell, with the comparison rows (BENCH-R1 cells 1-8);
  - the six expectations written beforehand; the reading; the CONFIRMED rule.
- **Decided in it, disclosed here:**
  - **The workload.** The task's table marks only the f rows as SNES. So a1-e3 run the PS1 fixture (E1-PS1-STREAM), f1 / f2
    run E1-SNES-STREAM (snes9x), and f3 / f4 the PS1 fixture (Beetle PSX HW).
    - Consequence: **b1 / b2 / c1 exercise rewind on Beetle PSX HW.** Their holds are where PSX HW's rewind answer
      (`rewound_frames` or `rewind_failed`) will show, with f4 and RetroArch's own log.
  - **`PRIVYHUB_WAN_TELEMETRY=1`** stays as the base line of every drop-in (BENCH-R1's scaffolding; telemetry only).
  - **The suite's `apk` field reads `MISMATCH`** while the candidate is on the onn, because its `EXPECT_APK` is still
    `93d29b4a…`. Expected; the pin moves only by the CONFIRMED rule.
- **The cap:** `CAP_UTC: 2026-10-22T20:00:00Z`, the planned 15:00Z launch + 5 h.
  - **Disclosed:** the launch came 51 min early, so the cap is the real launch + 5 h 51 min.
  - Fifteen cells take ~3.6 h, so the cap does not bind.

## 3. The install (14:04-14:05Z)

- **The candidate's hash matches B's pin.** `/tmp/b_q22c_scratch/b7_apk/app-debug.apk` read sha256
  **`cb0935c8cadd5ee65a3f52f390d0994899de27ebaa5c207b547e57185e761080`**, equal to B's pin (`candidate_apk_sha256.txt`).
  The `/tmp` copy was present, so no rebuild was needed.
- **The signer is the same as the CONFIRMED APK's.** `apksigner verify --print-certs`; the certificate digests were
  compared, not printed (`signer_check.txt`).
- **Preserved, nothing deleted** (both gitignored):
  - the CONFIRMED `93d29b4a…` → `PrivyHub/app/build/bench_r2_preserved/app-debug.apk`;
  - the candidate → `PrivyHub/app/build/bench_r2_installed/app-debug.apk`.
- **`adb install -r`: `Success`** (`install.log`, `install_at.txt`).
- **The device reads `cb0935c8…`. Paired:**
  - identity v2, the device secret present, the client's id in the hub's store (1 device);
  - read with CL-B4's reader: booleans, counts and key names only (`client_before_install.json`,
    `client_after_install.json`).
- **The three properties read empty after the install** (`properties_after_install.txt`).

## 4. The driver

**`bench_r2_driver.py`**, built from `bench_r1_driver.py`'s scaffolding.

**Kept:**
- the status line and heartbeat, history, STOP (`~/privyhub_bench_r2/STOP`), the busy skip, the cap;
- the suite call; the crash handler;
- the readings beside a run, the encoder read-back;
- the applied check (G8-S1's tolerances and B1's blackout spans);
- the per-run log copies (heartbeat, control gaps, recovery, frame sizes, ladder), B2's reader;
- `no_play` as an outcome; the profile-not-applied repeat; the state stop.

**Changed:**
- **The fifteen cells**, in the pre-registered order: a1 a2 a3 d1 d2 b1 b2 c1 e1 e2 e3 f1 f2 f3 f4.
- **The workload per cell**, passed to `bench_r2_suite_call.py`. That is BENCH-R1's wrapper with the workload id as a
  4th argument; it refuses anything but E1-PS1-STREAM / E1-SNES-STREAM and still refuses to run unless the
  pre-registration matches its hash.
- **The properties per cell:**
  - `adb shell setprop` before the suite, which then force-stops the app and starts a new stream activity; the
    activity reads each property as a lazy value;
  - read back with `getprop`;
  - after the cell all three are set empty and read back.
  - A cell that does not read back empty ends the driver.
  - The three are read at the start and cleared at the close.
- **Added to each row:**
  - RetroArch's CPU % and RSS, the host's available memory (the summary's `procs.retroarch.*` / `mem.available_mb`);
  - B2's reader with `--net` beside the plain count; the property read-backs.
- **The readers:** `tools/unattended_frames.py --net` ran on BENCH-R1 cell 6's copies. With no rewind rows there, it read
  the same as the plain count (B4 §7).

**`--dry` on b1's flags and properties** (14:07:01-14:08:39Z; `dry_run/`, `dry_run_console.txt`):
- b1's drop-in was written (six lines) and the companion restarted; the environ read **14** lines (eight + six), all
  present;
- the properties were set and read back: `wifi_lock=low_latency`, `stall_signal=1`, `link_report` empty;
- 30 s later the drop-in was removed and the companion restarted: `flags_absent` true, adopted8 ok;
- the properties were cleared and all three read back empty;
- no stream ran.

**`tools_at_preregistration_sha256.txt`:**

| file | sha256 |
| --- | --- |
| `impairment.py` | `6db4712a…` |
| `input_hold.py` | `22ddf955…` |
| `hold_tuning.py` (B6) | `f90527d5…` |
| `hold_rewind.py` (B4) | `594c7d5b…` |
| `games/link_drop_recovery.py` | `a1d51460…` |
| `lan_loss_rule.py` | `3d8b0182…` |
| `stall_signal.py` (B7) | `2b418522…` |
| `native_session_io.py` | `9b233a80…` |
| `native_stream.py` | `59c9ba27…` |
| `adaptive_bitrate_live.py` | `dffbacd2…` |
| `tools/e1_suite.py` | `e72c7985…` |
| `tools/unattended_frames.py` | `d30a7e6b…` |
| the driver | `73035125…` |
| the wrapper | `94e45b8c…` |
| the journal reader, E4-S5D's analysis | `d0b892e6…`, `41cbb0c3…` |
| `ux_r3_seconds.py`, B6's `gap_distribution.py` | `e9b2b3f7…`, `a93d2f57…` |

**The launch** (14:09:00Z; `launched_at.txt`, `launch_console.txt`):
- `systemd-run --user --unit=privyhub-bench-r2 --collect -p WorkingDirectory=<repo> /usr/bin/python3 -B …/bench_r2_driver.py`;
  it printed "Running as unit: privyhub-bench-r2.service" (the invocation id masked).
- **Just before it, `--check` read `ok False` only because the APK reads `MISMATCH`**, as pre-registered.
  - Its preflight was ok: eight lines, no `e3_flag.conf`, no game, no RetroArch, no encoder
    (`check_before_launch.json`).
  - The driver's own state read uses that preflight.

## 5. The first cell (`first_cell_preflight.txt`)

**a1, no lock: the preflight passed and the cell was PLAYING.** This is a confirmation at 14:12Z, not a result; the
record reads the cell.
- **The properties:** set as pre-registered (none) and read back. All three were empty.
- The suite passed its preflight (it refuses to continue otherwise), wrote the drop-in and restarted the companion.
- **PLAYING** on suite attempt 1 in **4.1 s** (14:11:25Z).
- **The environ: 10 lines.** That is the eight adopted lines, all present, plus `PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1`
  and `PRIVYHUB_WAN_TELEMETRY=1`.
- **The encoder** (read back 14:11:24Z, masked): `-b:v 7000k -maxrate 7000k -bufsize 7000k`. The stream poll reads
  7000 at 1280×720: **the 7000 start**.
- **The shim is live:** `none`, post-fec, seed 1. At t_s 23 it read 958 packets in the second, 0 dropped of any kind.
- **The unit:** active (running) (`unit_status_after_launch.txt`).

## 6. For the user

- **Status:** `cat ~/privyhub_bench_r2/status.txt`. The heartbeat is at most 5 min old.
- **Expected end:** about 17:50Z, fifteen cells of ~14.5 min each.
- **The TV and the onn stay on and idle; the pad untouched.** Nobody plays. A game started by hand is waited out (busy).
- **To stop early:**
  1. `touch ~/privyhub_bench_r2/STOP`;
  2. wait for `EXITED (the stop file)` (≤ 15 min).

  The cells done so far stand. The driver clears the three properties at its close.
- **On the onn now:** the candidate `cb0935c8…`. The CONFIRMED decision is the record's: by the pre-registered rule it
  stays, or `93d29b4a…` (preserved) is reinstalled.
- **The record when it ends:** "write BENCH-R2's record from the driver's files". It covers:
  - the per-cell tables; the uplink-silence count and distribution per cell;
  - the per-blackout tables against BENCH-R1;
  - the rewind CPU / RSS per core, PSX HW's answer;
  - the reading applied; the CONFIRMED decision.

## 7. Files

- **`bench_r2_2026-10-22/`:**
  - the start: `baseline_head.txt`, `git_status_at_start.txt`, `check_before.json`, `session_status_before.json`,
    `units_before.txt`;
  - the pre-registration: `bench_r2_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`;
  - the install: `candidate_apk_sha256.txt`, `signer_check.txt`, `client_before_install.json`, `install_at.txt`,
    `install.log`, `client_after_install.json`, `properties_after_install.txt`;
  - the code: `bench_r2_driver.py`, `bench_r2_suite_call.py`, `tools_at_preregistration_sha256.txt`;
  - the dry run: `dry_run/`, `dry_run_console.txt`;
  - the launch: `check_before_launch.json`, `launched_at.txt`, `launch_console.txt`, `unit_status_after_launch.txt`,
    `first_cell_preflight.txt`;
  - `redact_check.txt`: 45 files OK at the launch. One HIT, a1's `title.txt`, is the core's version string, OK
    (benign) on the re-check, as BENCH-R1's.
  - The driver keeps writing `runs/`, `cells.jsonl` and `bench_r2_state.json` until it ends.
- **`logs/bench_r2_launch_git_status.txt`.**
- **Not done:** no sudo, no nft, no Opal access.
- **adb:** the install, the pre-registered `setprop`s, and state reads only.
- **Not written:** no address, token or identifier.
- **Nothing** fetched, deleted, adopted or committed.
