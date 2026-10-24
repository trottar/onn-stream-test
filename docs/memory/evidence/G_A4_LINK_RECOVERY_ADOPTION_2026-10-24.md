---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 8ea9f09 (CL-B12 and queue G committed; G-A4 uncommitted beside it; the user commits)
---

# G-A4 — `PRIVYHUB_LINK_RECOVERY=1` ADOPTED: the tenth adopted line; the confirmation window VALID, every row met

**Classification: ADOPTED (the user's decision, 2026-10-24, "Adopt", after CL-B12). The adopted environ is TEN lines.**
- The confirmation window was VALID, with the host gates met: one E1-SNES-STREAM, **no `e3_flag.conf`, no client
  property set**, the ten lines alone, 5 GHz throughout.
- **The stack by the drop-in alone:** `link_recovery_config` (umbrella true) and the six modules' config rows, none
  `ignored`; `e3_state.py` read `link_recovery.stack` all six `implied 1` before, during and after the window.
- **No action without a stall:** 0 `state_saved`, 0 holds, 0 stall rows. Silences ≥ 250 ms **0 / 10 min**, hitch
  seconds **0 / 10 min**.
- **The teardown:** `session_end_bye`, then `state_save_skipped` reason `client_bye` (silence 400.9 ms), no hold.
- `link_recovery_config` reads `implied` [] / `explicit` the six, as in CL-B12: **B's logging defect, not fixed here.**
- Nothing else adopted. Nothing committed.

Task: `handoffs/G-A4_LINK_RECOVERY_ADOPTION_TASK.md`, session A. The patch is session B's
(`patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`, B20). Files: `g_a4_2026-10-24/`.

## 1. Precondition (18:12Z, `check_before.json`)

- **`tools/e3_state.py` ok on nine:** no `e3_flag.conf`, no `e4_constraint.conf`; no game, RetroArch or encoder;
  **APK `20e3e339…563d` CONFIRMED** (the pin `EXPECT_APK`); adb connected.
- **One device paired**, 0 active sessions, no pairing window.
- **Units:** `privyhub-companion` and `privyhub-link-n1` only.
- **HEAD `8ea9f09`**, CL-B12 committed (its record and `cl_b12_2026-10-24/` tracked). `git status --short` printed
  nothing: the prompt and the task file are both tracked in HEAD, unmodified (`git_status_at_start.txt`).
- **The clock: 18:12Z**, outside 04:30-05:30Z.
- **The band: 5 GHz** (5180 MHz, standard 5, RSSI −69).
- **The seven client properties empty:** `restart_guard`, `stall_signal`, `link_notice`, `link_report`, `loss_guard`,
  `wifi_lock`, `opus_decode`.

## 2. The adoption

1. **`git apply -p1`** of the prepared diff (`g_a4.diff`, extracted verbatim from the patch file's diff block).
   `--check` passed first. It touched 4 files, +11 / −4 (`g_a4_applied.diff`; `predecessor_sha256.txt` →
   `after_sha256.txt`):
   - `tools/e1_suite.py`: `LINK_RECOVERY` defined and in `ADOPTED` (**ten**); the preflight's `drop_in_link_recovery`
     and its `ok` term;
   - `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: wording only.
   - **One edit beyond the diff, disclosed (as G-A3):** the placeholder `G-A4 (adopted <date>, the user)` was filled
     with `2026-10-24`.
   - `git diff --check` was clean.
2. **Tests from the tree, green** (`tests.txt`):
   - `e1_suite.py --self-test`: `E1_SUITE_SELF_TEST_OK`;
   - `test_e1_remote`: 21 OK;
   - `test_c3_l4_nft_night`: 33 OK;
   - `tests/link_recovery/test_link_recovery.py`: 7 OK.
3. **The drop-in**, written with the file tool:
   `~/.config/systemd/user/privyhub-companion.service.d/link-recovery.conf` (`link-recovery.conf.copy`):

   ```
   [Service]
   Environment=PRIVYHUB_LINK_RECOVERY=1
   ```

4. **`systemctl --user daemon-reload && systemctl --user restart privyhub-companion`**, a separate command, at
   **18:13:02Z** (active). Outside 04:30-05:30Z.
   - At the restart the recovery log carried `link_recovery_config` and the six config rows
     (`restart_config_rows.jsonl`).
5. **The environ read back TEN lines** (`check_after_restart.json`):
   - `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, `PRIVYHUB_AUDIO_CODEC=opus`, `PRIVYHUB_EPG_GUIDE_INDEX=cached`;
   - **`PRIVYHUB_LINK_RECOVERY=1`**, `PRIVYHUB_LINK_REPORT=1`;
   - `PRIVYHUB_OVERLAY_PROVIDER=tailscale`, `PRIVYHUB_RECOVERY_TRIGGER=v2`, `PRIVYHUB_SESSION_IDENTITY=v2`;
   - `PRIVYHUB_SNES_CAPTURE_FIX=output_rate`, `PRIVYHUB_SNES_CORE=snes9x`.
   - **`--check` ok on ten** (`drop_in_link_recovery` true; APK CONFIRMED). `link_recovery`: umbrella `1`, on, and
     `stack` = `PRIVYHUB_INPUT_HOLD`, `_B6`, `_B8`, `_REWIND`, `PRIVYHUB_STALL_SIGNAL`, `PRIVYHUB_STALL_RESUME`, each
     **`implied 1`**.

## 3. The confirmation window

- **Pre-registration** `g_a4_preregistration.txt`, sha256 **`a89043df…9250`**, hashed at 18:14:20Z, before the run.
  The tools and the reused readers were hashed then too (`tools_at_preregistration_sha256.txt`).
- **The run:** `g_a4_window.py` (G-A3's runner for ten lines, plus a band read every 30 s and one `g_a4_state.py`
  read mid-window) called the suite's own CLI:
  `run --only E1-SNES-STREAM --runs 1 --window 600 --gap 120 --e2 --prereg …`. There was **no `--plan`, no
  `e3_flag.conf` and no `setprop`**, and the pad was not touched.
  - PLAYING at 18:17:24Z, **attempt 2**, 5.2 s (the suite's retry; disclosed). The session ran
    18:17:24.4-18:28:56.8Z (11.54 min); the suite's window was 18:18:54-18:28:54Z.
- **The environ:** ten lines, equal to the new `ADOPTED`, in **58 of 58** reads (every 15 s). After the run: ten
  lines, `flags_absent` true, `--check` ok, the stack all `implied 1` (`window_result.json`).
- **The band:** 29 of 29 reads at 5 GHz, 5180 MHz (`band.jsonl`). Mid-window (18:21:51Z, `state_midwindow.json`):
  the stack all `implied 1`, the seven properties empty. That read's `ok` is false because a game was running, as
  expected during a stream.
- **The reader:** `g_a4_read.py` (G-A3's reader plus the recovery log's link-recovery rows; B6's `measure` and
  UX-R3's `evening` / `counts` exec'd unedited, their sha256s asserted against LINK-R1's pins). Output in
  `record_read.json` and `record_read_console.txt`.
  - **One reader fix, disclosed:** the first run looked back 120 s before `session_started` for the config rows. It
    found none, because the rows are logged at the suite's start (18:14:50Z), 154 s earlier (the 120-s gap plus the
    launch). The look-back was widened to the whole copy span and the reader re-run. The rows were in the copied log
    all along.

**The rows, as hashed:**

| row | read | |
| --- | --- | --- |
| Y1 `link_recovery_config` | umbrella true; `implied` [] / `explicit` the six (B's defect, as CL-B12) | met as stated |
| Y1 the six config rows | `input_hold_config` (hold 250 ms), `input_hold_b6_config` (950 ms), `input_hold_b8_config`, `input_hold_rewind_config` (cap 30) + `input_hold_rewind_cores_config` (mode `state`, slot 9, 400 ms), `stall_signal_config` (threshold 400), `stall_resume_config` (`fast_ready` / `save_from_signal` / `state_save` true); none `ignored` | **met** |
| Y2 host gates | RetroArch 59.999; capture 59.992; dup+drop 0.1 / min; the ladder at 7000 throughout; resyncs 0; 0 client pauses; ten lines in 58 / 58 | **met** |
| Y3 no action without a stall | 0 `state_saved`, 0 holds, 0 stall rows (no stall occurred) | **met** |
| Y4 the link on 5 GHz | silences ≥ 250 ms **0 / 10 min** (0 in 673 s streaming); hitch seconds **0 / 10 min** | stated (G-A3 0.0 / 0.9; CL-B12 0 silences) |
| Y5 teardown | `session_end_bye` 18:28:55.807Z → `state_save_skipped` `client_bye` 18:28:56.643Z (silence 400.9 ms) → `session_ended`; no hold; after: `flags_absent`, ten lines, `--check` ok, the properties empty | **met** |

**Other figures (the suite's window):** rendered 59.94 fps; post-FEC loss 13.8 / min (session 17.4 / min); stale
drops 1.6 / min; ≥ 50 / ≥ 80-ms spikes 23 / 15; max output gap 200 ms; audio underruns 41 (heartbeat 31); host CPU
7.4 %, encoder 27.5 %, RetroArch 8.3 %. RSSI −69 (319 heartbeats) / −70 (27); tx 195 (330); rx 117 (274), 58 (58).
`native_stream_ctrl_gaps.log` holds no row in the session.

## 4. How to turn it off

1. Delete `~/.config/systemd/user/privyhub-companion.service.d/link-recovery.conf`.
2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
3. Take `LINK_RECOVERY` out of `tools/e1_suite.py` `ADOPTED` (reverse `g_a4_applied.diff`); `e3_state.py` then reads
   ok on nine.

The client halves are separate. `20e3e339…` has them on by default; `adb shell setprop debug.privyhub.stall_signal 0` /
`adb shell setprop debug.privyhub.restart_guard 0` turn them off. One part of the host stack can be turned off alone
with its explicit line (`…=0`), which wins over the umbrella.

## 5. Not changed

- `ADOPTED_E3` in `tools/d7_regression.py` / `tools/c3_l4_nft_night.py`: three names, as the patch lists (as G-A1 to
  G-A3).
- **The `link_recovery_config` log defect** (`plugins/games.py` logs a second `apply()`): B's, not fixed here.
- `link_n1_watch.py` (the nightly watch, `privyhub-link-n1`): not touched; it keeps running.
- The patch file `G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md` is kept as it is (nothing renamed or deleted).

## 6. State (18:30Z, `check_end.json`)

- **TEN adopted lines; `--check` ok on ten; APK `20e3e339…` CONFIRMED.** The stack all `implied 1`.
- No `e3_flag.conf`, no game, no RetroArch, no encoder. One device paired. `active_sessions` reads 2: those are the
  client's identity tokens from the window's signed setup (8-h expiry), not streams.
- **Units:** `privyhub-companion` and `privyhub-link-n1` only. This task started no unit.
- The seven client properties empty. The band 5 GHz.
- No sudo, no nft. adb for state reads only (`getprop`, `dumpsys wifi`). No address or identifier in any kept file
  (`redact_check.txt`). Nothing fetched or deleted. Nothing adopted but the tenth line. Nothing committed.
  `logs/g_a4_git_status.txt`.

## 7. Files (`g_a4_2026-10-24/`)

- **The start:** `baseline_head.txt`, `git_status_at_start.txt`, `check_before.json`, `g_a4_state.py` (the state
  reader).
- **The patch:** `g_a4.diff` (as prepared), `g_a4_applied.diff` (as applied), `predecessor_sha256.txt`,
  `after_sha256.txt`, `tests.txt`.
- **The drop-in and the restart:** `link-recovery.conf.copy`, `restart_at.txt`, `restart_config_rows.jsonl`,
  `check_after_restart.json`.
- **The window:**
  - `g_a4_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`, `tools_at_preregistration_sha256.txt`;
  - `g_a4_window.py`, `window_console.txt`, `window_result.json`, `band.jsonl`, `state_midwindow.json`;
  - `runs/` (the suite's run, `logs_run1/` addresses masked);
  - `g_a4_read.py`, `record_read.json`, `record_read_console.txt`.
- `check_end.json`, `redact_check.py` / `.txt`, `manifest.sha256`.
