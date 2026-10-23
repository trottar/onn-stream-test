---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 9fd73c7
---

# BENCH-R3 — the stack on SNES, the loss guard, the link: INSTALLED and LAUNCHED (detached)

**Classification: the candidate APK `bf5114a2…cf73` (B5 + B7 + B10) is INSTALLED and paired. The driver was LAUNCHED
at 2026-10-22T20:22:11Z and is RUNNING** as the systemd --user unit `privyhub-bench-r3`. When this session exited,
cell A (SNES, blackout `@both`, the whole stack) had passed its preflight and was **PLAYING** at the 7000 start, with
**the link report's keys in every one of its first 21 heartbeats**. The record is a later task: "write BENCH-R3's
record from the driver's files" (`evidence/BENCH_R3_SNES_STACK_AND_LOSS_GUARD_2026-10-23.md`). Measurement only.
Nothing adopted, nothing committed.

Task: `handoffs/BENCH-R3_SNES_STACK_AND_LOSS_GUARD_TASK.md` §2 (the install and the launch), session A.
- **Baseline `9fd73c7`** (`baseline_head.txt`): queue D (B8, B9, B10), committed by the user.
  - An earlier attempt this session stopped at the precondition: queue D was still uncommitted. Nothing was run then.
- The tree was clean at the start; `git_status_at_start.txt` lists only `bench_r3_2026-10-22/`, created a moment before
  the file was written.
- **The flag names, property names, profile strings, APK hash and expected rows are session B's**
  (`SESSION_B_DONE_2026-10-22D.md` items 5-9; the B8 / B9 / B10 records).

## 1. Precondition (20:16Z)

- **`tools/e3_state.py --check`: ok** (`check_before.json`).
  - eight adopted lines; no `e3_flag.conf`, no `e4_constraint.conf`;
  - no game, no RetroArch, no encoder;
  - **APK `cb0935c8…` CONFIRMED;**
  - `adb` true without a reconnect, the endpoint never printed.
- **One device paired** (`session_status_before.json`; counts only). No active session.
- **The properties read empty:** `debug.privyhub.wifi_lock`, `stall_signal`, `link_report`, `loss_guard`, and
  `opus_decode` (read only).
- **No `privyhub-*` unit but the companion** (`units_before.txt`).
- **Code under test = HEAD:** `git diff HEAD -- companion tools` was empty at the launch.

## 2. Pre-registration (before the install)

- **`bench_r3_preregistration.txt`**, sha256 **`620a0ade…5290`** (`bench_r3_preregistration.sha256`), hashed at
  **20:19:39Z** (`preregistration_hashed_at.txt`), before the install and before the first cell.
- **It states, as the task does:**
  - the six cells with their fixtures, shim lines, flags and properties;
  - the expected rows (B's items 6-9);
  - the validity rule and the four gates;
  - what is reported per cell;
  - the expectations written beforehand, including the link's coincidence question;
  - the reading;
  - the CONFIRMED rule.
- **Decided in it, disclosed here:**
  - **`PRIVYHUB_SNES_CORE=snes9x` is adopted line 3** (`snes-core.conf`). It is in every environ and is not repeated
    in the drop-in; repeating it would duplicate the line.
  - **`PRIVYHUB_WAN_TELEMETRY=1` stays as every drop-in's base line.** This is BENCH-R1 / R2's scaffolding and is
    telemetry only. It keeps the cells comparable with BENCH-R2's b1 / b2 / c1 / d2.
  - **The suite's `apk` field reads `MISMATCH`** while the candidate is on the onn, because `EXPECT_APK` is still
    `cb0935c8…`. This is expected; the pin moves only by the CONFIRMED rule.
- **The cap:** `CAP_UTC: 2026-10-22T23:35:00Z`, the planned 20:35Z launch + 3 h.
  - **Disclosed:** the launch came 13 min early, so the cap is the real launch + 3 h 13 min.
  - Six cells take ~1.5 h, so the cap does not bind.

## 3. The install (20:19Z)

- **The candidate's hash matches B's pin.** `/tmp/b_q22d_scratch/b10_apk/app-debug.apk` read sha256
  **`bf5114a2d257f1246374b05e3d79b24f0382afe1c66b2c6acb3a37fa6e58cf73`** (`candidate_apk_sha256.txt`). The `/tmp` copy
  was present, so no rebuild was needed.
- **The signer is the same as the CONFIRMED APK's.** `apksigner verify --print-certs` was run and the certificate
  digests compared, not printed; `apksigner verify` OK (`signer_check.txt`).
- **Preserved, nothing deleted** (both gitignored):
  - the CONFIRMED `cb0935c8…` → `PrivyHub/app/build/bench_r3_preserved/app-debug.apk`;
  - the candidate → `PrivyHub/app/build/bench_r3_installed/app-debug.apk`.
- **`adb install -r`: `Success`** (`install.log`, `install_at.txt`).
- **The device reads `bf5114a2…`. Paired:**
  - identity v2, the device secret present, the client's id in the hub's store (1 device);
  - read with CL-B4's reader: booleans, counts and key names only (`client_before_install.json`,
    `client_after_install.json`).
- **Every property read empty after the install** (`properties_after_install.txt`).

## 4. The driver

**`bench_r3_driver.py`**, built from `bench_r2_driver.py`'s scaffolding. Everything was kept: the status line and
heartbeat, history, STOP, the busy skip, the cap, the suite call, the crash handler, the readings beside a run, the
applied check, the per-run log copies, B2's reader with `--net`, `no_play` as an outcome, the profile-not-applied
repeat, the state stop, and the properties set before / cleared after and read back.

**`bench_r3_suite_call.py`** is R2's wrapper with only the pre-registration name changed. It still refuses to run unless
the pre-registration matches its hash.

**Changed:**
- **The six cells**, in the pre-registered order A, B, C, D, E-off, E-on.
  - A-C: E1-SNES-STREAM on snes9x, with the whole stack (`INPUT_HOLD=1`, `_B6=1`, `_B8=1`, `_REWIND=1`,
    `STALL_SIGNAL=1`) and `LINK_REPORT=1`; properties `stall_signal=1`, `link_report=1`.
  - D: E1-PS1-STREAM (Beetle PSX HW), the stack with `INPUT_HOLD_REWIND=state`; the same properties.
  - E-off / E-on: E1-PS1-STREAM, `loss-1@post-fec,seed=1`, `LOSS_GUARD=1` + `LINK_REPORT=1`, the hold flags absent;
    properties `loss_guard=count` then `=1`, with `link_report=1`.
- **Four properties** (`wifi_lock`, `stall_signal`, `link_report`, `loss_guard`). All four are set empty and read back
  after each cell and at the close; `wifi_lock` is never set.
- **The Opal's O1 station view.** B's copy (`e4_s4d_2026-10-15`) of `o1_opal_sample.sh`, `o1_redact.py` and
  `o1_parse.py`, copied byte for byte (sha256 equal), samples every 300 s on `wlan1`.
  - It was started before cell A and is stopped after E-on by its own `.stop` file, then waited out.
  - It is read-only on the Opal; every byte goes through `o1_redact.py` inside the script before it is written.
- **Added to each row:**
  - the link report's per-heartbeat keys (rows carrying them, RSSI / tx / rx summaries, frequencies, standard);
  - the loss guard's heartbeat counters (E);
  - the silences ≥ 250 ms per 10 min, with B6's `gap_distribution.py` bins and 10-s edge rule;
  - the Opal rounds inside the cell;
  - RetroArch's own log lines on state / slot / rewind, scrubbed (D's "Loaded state from slot #9").
- The new readers ran on BENCH-R2 b1's copied logs before the launch (read-only). They read 0 link rows, as R2's record
  says, and its silences.

**`--dry` on cell A's flags and properties** (20:19:58-20:21:35Z; `dry_run/`, `dry_run_console.txt`):
- A's drop-in was written (eight lines) and the companion restarted; the environ read **16** lines (eight + eight),
  all present;
- the properties were set and read back: `stall_signal=1`, `link_report=1`, the others empty;
- the Opal sampler ran three 10-s rounds (read-only) and exited on its stop file;
- the drop-in was removed and the companion restarted: `flags_absent` true, adopted8 ok;
- all four properties were cleared and read back empty;
- no stream ran.

**`tools_at_preregistration_sha256.txt`:** 27 files.
- The companion modules: `impairment.py`, `input_hold.py`, `hold_tuning.py`, `hold_rewind.py`, `hold_ownership.py`,
  `rewind_cores.py`, `stall_signal.py`, `keyframe_request.py`, `games/link_drop_recovery.py`,
  `games/native_stream_heartbeat.py`, `diagnostics/client_feedback.py`, `diagnostics/stream_telemetry.py`,
  `native_session_io.py`, `native_stream.py`, `plugins/games.py`.
- The tools: `tools/e1_suite.py`, `e3_state.py`, `unattended_frames.py`, B6's `gap_distribution.py`, the journal
  reader, E4-S5D's analysis, CL-B4's client reader.
- This run's files: the driver, the wrapper, the Opal sampler and its two scripts.

**The launch** (20:22:11Z; `launched_at.txt`, `launch_console.txt`):
- `systemd-run --user --unit=privyhub-bench-r3 --collect -p WorkingDirectory=<repo> /usr/bin/python3 -B …/bench_r3_driver.py`;
  it printed "Running as unit: privyhub-bench-r3.service".
  - The invocation ID printed on the console was masked in `launch_console.txt` after the fact; my first mask pattern
    missed it.
- **Just before it, `--check` read `ok False` only because the APK reads `MISMATCH`**, as pre-registered.
  - Its preflight was ok: eight lines, no `e3_flag.conf`, no game, no RetroArch, no encoder
    (`check_before_launch.json`).

## 5. The first cell (`first_cell_preflight.txt`)

**A (SNES, blackout `@both`, the stack): the preflight passed and the cell was PLAYING.** This is a confirmation at
20:25Z, not a result; the record reads the cell.
- **The properties:** `stall_signal=1` and `link_report=1` were set and read back; `wifi_lock` and `loss_guard` are
  empty.
- **PLAYING** on suite attempt 2 in **4.1 s** (20:24:46Z). Attempt 1's failure file is written at the run's end; the
  record reads it.
- **The environ: 16 lines.** That is the eight adopted lines, all present, plus A's eight.
- **The encoder:** `-b:v 7000k -maxrate 7000k -bufsize 7000k`. The stream poll reads 7000 at 1280×720: **the 7000 start**.
- **The shim is live:** blackout-4s, post-fec, seed 1. At t_s 58 it read 967 packets in the second, 0 dropped; the
  first dark span is due at ~120 s.
- **The link report's keys are present.** All 21 heartbeats from 20:24:40Z to 20:25:11Z carry the five `link_*` keys:
  - RSSI −66 / −67 dBm;
  - tx 108-162 Mbps, rx 108-216 Mbps;
  - **2412 MHz (2.4 GHz, channel 1), Wi-Fi standard 4 (802.11n)**.
- **The Opal's `wlan1` (5 GHz, channel 36) lists no associated station.** That held in the dry run's three rounds and
  in round 0 of the run.
  - The onn's link is on 2412 MHz, the channel of the Opal's `wlan0` (2.4 GHz, channel 1). The pre-registered
    sampler reads `wlan1` only.
  - So **the Opal's station rows for the onn will be empty in this run**; its airtime / utilization rows for `wlan1`
    are still kept.
  - The pre-registered interface was kept, not changed mid-run. O1 (2026-09-21) found the client on the 5 GHz
    interface.
  - This bears on the link question; the record carries it to the next task.
- **The unit:** active (running) (`unit_status_after_launch.txt`).

## 6. For the user

- **Status:** `cat ~/privyhub_bench_r3/status.txt`. The heartbeat is at most 5 min old.
- **Expected end:** about 21:55Z, six cells of ~14.5 min each.
- **The TV and the onn stay on and idle; the pad untouched.** Nobody plays. A game started by hand is waited out
  (busy).
  - If you watch E-off / E-on (about 21:20-21:50Z), your one line on each (corrupted picture vs stutter) is recorded
    verbatim. Otherwise "no watch".
- **To stop early:**
  1. `touch ~/privyhub_bench_r3/STOP`;
  2. wait for `EXITED (the stop file)` (≤ 15 min).

  The cells done so far stand. The driver stops the Opal sampler and clears the four properties at its close.
- **On the onn now:** the candidate `bf5114a2…`. The CONFIRMED decision is the record's: by the pre-registered rule it
  stays, or `cb0935c8…` (preserved) is reinstalled.
- **The record when it ends:** "write BENCH-R3's record from the driver's files".

## 7. Files

- **`bench_r3_2026-10-22/`:**
  - the start: `baseline_head.txt`, `git_status_at_start.txt`, `check_before.json`, `session_status_before.json`,
    `units_before.txt`;
  - the pre-registration: `bench_r3_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`;
  - the install: `candidate_apk_sha256.txt`, `signer_check.txt`, `client_before_install.json`, `install_at.txt`,
    `install.log`, `client_after_install.json`, `properties_after_install.txt`;
  - the code: `bench_r3_driver.py`, `bench_r3_suite_call.py`, `o1_opal_sample.sh`, `o1_redact.py`, `o1_parse.py`,
    `tools_at_preregistration_sha256.txt`;
  - the dry run: `dry_run/` (with `dry_run/opal/`), `dry_run_console.txt`;
  - the launch: `check_before_launch.json`, `launched_at.txt`, `launch_console.txt`, `unit_status_after_launch.txt`,
    `first_cell_preflight.txt`;
  - `redact_check.txt`.
  - The driver keeps writing `runs/`, `opal/`, `cells.jsonl` and `bench_r3_state.json` until it ends.
- **`logs/bench_r3_launch_git_status.txt`.**
- **Not done:** no sudo, no nft. The Opal was only read, by the O1 sampler.
- **adb:** the install, the pre-registered `setprop`s, and state reads only.
- **Not written:** no address, token or identifier.
- **Nothing** fetched, deleted, adopted or committed.
