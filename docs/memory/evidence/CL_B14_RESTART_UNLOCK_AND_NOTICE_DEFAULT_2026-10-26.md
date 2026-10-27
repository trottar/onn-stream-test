---
memory_schema: 1
as_of: 2026-10-27
baseline_commit: 44558c9 (queue I committed; "Queue I done (B24, B25); CL-B14 handoff"; this record, its dir and the pin uncommitted beside it)
---

# CL-B14 — the unlocked fast restart at four Home returns, with the notice on by default: MEASURED, valid, every row met at every return; `fcd924c2…` CONFIRMED

**Classification: MEASURED.** One attended Home cell, valid, on 5 GHz with every client property EMPTY (no `setprop`
was run). **R1-R7 met at all four returns.** By CL-B7 §6's rule, B25's APK **`fcd924c2…9b96` is CONFIRMED** and the
pin moved; `e3_state` is ok on eleven.

**The rows, in short (PRIVYHUB_RESTART_FAST_UNLOCK=1 on the eleven lines):**
- **The picture back 1.86 / 1.60 / 1.15 / 1.27 s** after the new activity (one clock; ≤ 2.0). CL-B13 cell 1 (the G-A5
  worker): 3.12 / 1.74 / 2.00 / 1.76.
- **The lock released at the check:** `unlocked_ms` − `checked_ms` 0.0 ms at every return.
- **The old encoder's last picture frame** at +0.005 / +0.003 / −0.011 / −0.003 s after the entry (CL-B13's method);
  a bound that needs no fps assumption: ≤ +0.19 / +0.22 / +0.06 / +0.12 s. CL-B13: +0.08 / +0.17 / +0.35 / +0.39.
- **The old audio after the ready:** its stop ran 150 / 201 / 405 / 402 ms. **At returns 3 and 4 the audio capture was
  SIGKILLed at the 300-ms bound** (`capture_returncode` −9): twice the case that took 2.1 s in CL-B13's return 1. The new
  audio started every time; first intervals 0 / 1 / 0 / 0 underruns.
- **The notice (B25), with no property:** 319 / 319 heartbeats carry `link_notice` = 0 on 5180 MHz; no
  `link_notice_shown` row; every report `link_notice_shown` 0.
- **On 5 GHz:** 0 silences ≥ 250 ms and 0 hitch seconds in all five client sessions.

**For B, disclosed (not a row as pre-registered):** at each return the relay logged one 8-byte, single-packet,
unmarked "frame" within 1 ms of the old encoder's exit (`released_ms`), 100-140 ms after the relay's stop. It was absent
in CL-B13. It is not a picture frame. The rows cannot say whether it reached the onn (§2).

**The reading, as pre-registered:** every row at every return → **G-A7 is the user's question** (§5). Nothing adopted.
Nothing committed.

**The user's line, verbatim:** "The returns ran as expected".

Task: `handoffs/CL-B14_RESTART_UNLOCK_AND_NOTICE_DEFAULT_TASK.md`, session A. B's strings: `SESSION_B_DONE_2026-10-26I.md`
items 2-5; B24, B25. Methods: CL-B13 §2. Files: `cl_b14_2026-10-26/`.

## 0. How it ran

- **Precondition (2026-10-26 15:21-15:22Z):**
  - **the band read first:** 5180 MHz, 5 GHz, RSSI −69 (`adb_reads/wifi_first_read.json`);
  - `check_at_start.json`: eleven lines, `--check` ok (`e3_check_at_start.txt`), APK `6bddafc0…` CONFIRMED, no game;
    no `e3_flag.conf`;
  - one device, paired (`client_before_install.json`, booleans and counts); the client on the LAN (the newest
    `token_issued` lan);
  - units: the companion and `privyhub-link-n1` only;
  - HEAD `44558c9`, the tree clean (`git_status_at_start.txt`, taken before this dir was made); the clock 15:21Z.
- **The pre-registration** `cl_b14_preregistration.txt`, sha256 **`bf938c78…1077`**, hashed at **15:24:02Z, before the
  install**. `tools_at_preregistration_sha256.txt` hashes the driver, the wrapper, `e1_suite`, `e3_state`,
  `unattended_frames`, `link_recovery`, `restart_fast`, `restart_fast_unlock`, `link_notice`, `plugins/games.py` and the
  two readers.
- **The install (15:24Z):**
  - **`6bddafc0…` preserved** at `PrivyHub/app/build/cl_b13_installed/` (untouched);
  - B25's copy `/tmp/b_q26i25_scratch/apk/app-debug.apk` (named in `b25_2026-10-26/apk_sha256.txt`) copied to
    `PrivyHub/app/build/cl_b14_installed/` (gitignored): **`fcd924c2…9b96`, 9,638,234 B** (`apk_sha256.txt`);
  - the signer the same as `6bddafc0…`'s (digests compared, not printed); `apksigner verify` OK (`signer_check.txt`);
  - **`adb install -r` `Success`** (`install.log`); read back `fcd924c2…`, **paired** (`client_after_install.json`);
  - the seven properties empty before and after (`adb_reads/properties*.txt`);
  - `e3_state` `ok` false only by APK `MISMATCH` (the preflight ok on eleven; `check_after_install.json`).
- **The driver** `cl_b14_driver.py`, from `cl_b13_driver.py` (`cl_b14_driver_vs_cl_b13.diff`, 142 lines): one cell;
  `config_rows()` (the two config rows from the recovery log after the restart); this task's names; `adopted11`.
  `cl_b14_suite_call.py` is CL-B13's wrapper with the pre-registration name changed.
- **The dry run** `privyhub-cl-b14-dry --dry` (15:24:49-15:26:30Z, `dry_run/`): 13 lines; **`restart_fast_config` 0.75 /
  2.0 and `restart_fast_unlock_config` `kill_grace_s` 0.1, `capture_bound_s` 0.3, `audio_join_cap_s` 10,
  `startup_check_s` 0.75**; the properties empty both ways; `flags_absent` true; `adopted11 ok`.
- **Attempt 1** (`privyhub-cl-b14`, 2026-10-26 15:26:43Z; PLAYING 15:29:18Z on the suite's attempt 2; closed 15:41:23Z,
  valid):
  - **No Home press:** one client session (15:29:17.733-15:40:50.873Z) and no `restart_fast` row;
  - the user: "We may need to redo that, it was not obvious I needed to interact". The words told were the task's;
    they did not say plainly enough that the presses were the user's to make;
  - its files renamed `*_attempt1*` (`runs/…_attempt1_no_presses/`, `cell_attempt1_note.txt`, `cl_b14_state_attempt1.json`).
    Nothing deleted. Its R7: 344 / 344 heartbeats `link_notice` 0 on 5180 MHz, no notice row.
- **The relaunch** on the user's "Go" (2026-10-27): the state re-read at 17:49:52Z (`check_before_relaunch.json`,
  `client_before_relaunch.json`: 5180 MHz, eleven lines, no game, properties empty, `fcd924c2…` paired, the two units).
  `privyhub-cl-b14` 17:50:05Z; **PLAYING 17:52:33Z** (attempt 1, 8.1 s); the user told the task's words with the times
  (13:54 / 13:56 / 13:58 / 14:00, play to 14:02 EDT) and, after them, the plain steps. **Four returns:** 17:54:21,
  17:56:36, 17:58:35, 18:01:10Z. Closed 18:04:26Z "all 1 cells done".
- **The reader** `cl_b14_read.py` (`record_read.json`, `record_read_console.txt`): CL-B13's reader's first 147 lines and
  its `REP` / `RK` / `jtime` unedited (B6's `measure`, UX-R3's `evening` / `counts`, pin-asserted), plus `returns14()`,
  the capture with the kill pairs left out, and the per-session spans.
- **The events read:** one `adb logcat -b events -d` at 18:04:36Z (`adb_reads/logcat_events_cell.txt`,
  `cl_b14_events_read.py` = CL-B13's reader, unedited but its comment line). The journal at µs precision:
  `journal_precise_cell.txt` (the start / ready / stop lines and the report lines; addresses and ports masked).

## 1. Validity and the gates

| | drop-in | PLAYING | environ at stream / under load | validity | RetroArch / capture / dup+drop | rendered | post-FEC loss / min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| attempt 1 (no press) | `none` + `RESTART_FAST_UNLOCK` | 15:29:18 (2) | 13 / 13 | valid | 59.999 / 59.996 / 0.0 | — | — |
| **the cell** | `none` + `RESTART_FAST_UNLOCK` | 17:52:33 (1) | **13 / 13** | **valid** | 59.999 / **59.894** / 0.0 | 59.88 | 9.45 |

- **The capture 59.894 is the Home restarts' own sample pairs, as CL-B13 §1 (59.899).** Two of the sampler's per-second
  encoder pairs span an old encoder's kill. **With them left out: 59.995.** The pre-registration (§4) says the cell is
  not invalidated by the Home presses, and that these pairs are read with them left out. **Valid, disclosed.**
- The shim's `none` applied (0 drops); `flags_absent` true after; eleven lines; the seven properties empty before and
  after; 5180 MHz in every band read and every heartbeat; the client's class lan at the stream.
- The teardown: `session_end_bye` 18:04:05.291, `session_ended` .494, `state_save_skipped` `state_ended` (401.2 ms).

## 2. The four returns (B item 4; CL-B13 §2's methods)

Times are UTC on the host's clock. "Entry" is the start's `session_ended`. The new activity on one clock is
`startSession` (heartbeat 1's arrival less its `elapsed_ms`) less `create_to_start_ms`. The worker's own ms are from
its t0, which read 3.9-4.9 ms after the entry.

| row | return 1 (menu) | return 2 (recents / tile) | return 3 (menu) | return 4 (recents / tile) |
| --- | --- | --- | --- | --- |
| entry (`session_ended`) | 17:54:21.812 | 17:56:36.764 | 17:58:35.628 | 18:01:10.286 |
| `restart_fast` `response_ms` / after the entry | 6.5 / 10 ms | 7.3 / 11 | 6.4 / 11 | 7.8 / 12 |
| new activity → entry (one clock) | 0.383 s | 0.139 | 0.088 | 0.124 |
| **R1 the picture back (one clock)** | **1.86 s** | **1.60** | **1.15** | **1.27** |
| R1 from the events read (the onn's clock) / **the offset** | 2.52 / **+0.65 s** | 2.39 / **+0.79** | 1.94 / **+0.79** | 2.05 / **+0.77** |
| **R2 the old encoder's last frame after the entry** (method) | **+0.005 s** (50 frames) | **+0.003** (47) | **−0.011** (38) | **−0.003** (18) |
| R2 the bound (no fps assumption) | ≤ +0.188 (the second's end) | ≤ +0.218 (the relay's stop) | ≤ +0.055 (the relay's stop) | ≤ +0.115 (the relay's stop) |
| `restart_fast_done` relay_stopped / released / spawned / checked / unlocked ms | 500.5 / 602.4 / 603.8 / 1,355.1 / 1,355.1 | 214.3 / 353.9 / 355.4 / 1,106.8 / 1,106.8 | 50.0 / 189.0 / 190.6 / 942.3 / 942.3 | 109.8 / 248.7 / 250.6 / 1,002.1 / 1,002.1 |
| **R3 `unlocked_ms` − `checked_ms`** | **0.0** | **0.0** | **0.0** | **0.0** |
| **R4 seconds after the switch with two relay rows** | **none** | **none** | **none** | **none** |
| **R5** `session_ended` → old report → `session_started` | **met** (old report +549 ms after the response) | **met** (+1,222 ms; `report_wait_ms` 301) | **met** (+124) | **met** (+160) |
| `session_started` | 17:54:23.289 | 17:56:38.225 | 17:58:36.693 | 18:01:11.437 |
| **R6** `restart_fast_audio_stop` ms / returncode / killed at bound | 150.3 / 255 / false | 200.6 / 255 / false | **405.2 / −9 / true** | **401.7 / −9 / true** |
| R6 `restart_fast_audio` started / `new_audio_ms` / after `session_started` | true / 1,601 / +0.13 s | true / 1,350 / −0.11 | true / 1,186 / +0.13 | true / 1,265 / +0.12 |
| **R6 the first 2-s interval after `session_started`** (underruns) | **0** | **1** | **0** | **0** |
| R6 `restart_fast_released_by` / `_response_to_release_ms` / `_gate_resets` | `fast` / 791 / 0 | `fast` / 1,036 / 0 | `fast` / 683 / 0 | `fast` / 680 / 0 |
| R6 `restart_cause` | `via_start`, host ended, `create_to_start_ms` 246, `recreate` | the same, 99 | the same, 88 | the same, 97 |
| R6 `restart_fast_failed` | 0 | 0 | 0 | 0 |
| **R7** the report's `link_notice_shown` | **0** | **0** | **0** | **0** |
| the path (the events read) | new `MainActivity` → new `NativeStreamActivity` (`recreate`) | the same | the same | the same |

| row (B item 4) | CL-B13 cell 1 (G-A5's worker) | **CL-B14** |
| --- | --- | --- |
| R1 the picture back ≤ 2.0 s | 3.12 / 1.74 / 2.00 / 1.76 | **met 4 / 4** (1.15-1.86) |
| R2 the old encoder's last frame ≤ entry + 0.3 s | +0.075 / +0.168 / +0.351 / +0.388 | **met 4 / 4** (−0.011 to +0.005; bound ≤ +0.22) |
| R3 `unlocked_ms` − `checked_ms` ≤ 20 | — (the lock held to `done`, 1.6-2.4 s) | **met 4 / 4** (0.0) |
| R4 no second with both encoders' frames after the kill | — | **met 4 / 4** |
| R5 the order | met | **met 4 / 4** |
| R6 the audio rows; first interval ≤ 15; `fast`, `via_start`, no failed | 0 / 0 / 1 / 0 | **met 4 / 4** (0 / 1 / 0 / 0) |
| R7 `link_notice` 0 in every heartbeat, no `link_notice_shown` | — (B14's flag absent = off) | **met** (319 / 319; 0 rows) |
| the path | `recreate` ×4 | **`recreate` ×4**; surface / process not produced |

- **R1's margin:** B's note expected ~0.02 s at a ~0.55-s new activity → entry. The largest here was return 1's 0.383 s,
  with 0.14 s of margin (1.86 s). The offset (one clock − the onn's) read **+0.65 to +0.79 s** at the four returns
  (CL-B13: −0.06 to +0.33). The events column alone would read 1.94-2.52 s. The row is on the one clock, as
  pre-registered.
- **R2, the method:** as CL-B13, the old encoder's row for the entry's second, at 60 fps from the second's start (the
  per-second log has no per-frame times). The bound beside it: the old encoder has no picture row in the next second,
  so its frames ended before that second began; the relay was stopped at the time shown in any case. The old encoder's
  picture frames ended at the entry itself at all four. (In CL-B13 they ran on until the kill.)
- **The 8-byte packet (for B):** in the switch second of every return, the relay logged one 1-packet, 8-byte, unmarked
  "frame" (`frames` 1, `packets` 1, `payload_bytes` 8, `unmarked_frames` 1). Its time is 0.1-0.7 ms before `released_ms`
  (the old encoder's exit): +0.606 / +0.358 / +0.193 / +0.253 s after the entry, and 100-140 ms after the relay's stop.
  - **It was not seen in CL-B13 cell 1.** It is not a picture frame (mean frame 9.7 kB).
  - Its source (likely the old encoder's last packet at exit) and whether it was forwarded to the onn (the relay was
    stopped, and the new relay starts ~1 ms after `released_ms`) are not in the rows.
  - **Not counted in R2 or R4**, which are about picture frames by the pre-registered method. If it were counted as the
    old encoder's last frame, R2 would read +0.61 / +0.36 at returns 1-2 (over 0.3).
- **`relay_stopped_ms` 500.5 at return 1** (214 / 50 / 110 at the others). Before the relay's stop come the audio stop's
  thread start, the capture watchdog's start and `m._host_telemetry.stop()`. B's "`released_ms` ≈ 100-150" held as
  `released` − `relay_stopped` (102-140 ms), not from t0 (189-602 ms). Not a row; for B.
- **R6, returns 3 and 4:** the old audio capture did not exit on SIGTERM within 300 ms and was SIGKILLed at the bound
  (−9). Under G-A5's worker each would have waited up to 2 s inside the lock (CL-B13's return 1). The ready did not wait
  on it.
- **Return 2's old report** came 1,222 ms after the start's response (124-549 at the others;
  `restart_fast_report_wait_ms` 301), still 226 ms before `session_started`.
- The diagnostics page's line ("Link notice: none shown") was **not read.** It needs the page open on the onn, and no
  `setprop` or UI step was taken for it.

## 3. On 5 GHz (B6's edge rule, UX-R3's reader; each client session to its Home silence)

| span | streaming s | silences ≥ 250 ms / 10 min | hitch s / 10 min |
| --- | --- | --- | --- |
| **CL-B14 sessions 1-5** | 74 / 103 / 86 / 123 / 154 | **0.0 / 0.0 / 0.0 / 0.0 / 0.0** | **0.0 ×5** |
| CL-B13 cell 1 sessions 1 / 2 / 5 | 195 / 133 / 204 | 0.0 / 0.0 / 0.0 | 0.0 / 3.9 / 5.4 |
| G-A5 window | 672 | 0.89 | 6.1 |

- The whole cell (589 s, the Home silences inside it): 4 silences, the longest 15.1 s (a Home press), and 0 hitch
  seconds. 5180 MHz in 319 / 319 heartbeats, RSSI median −69.
- **R7 across the whole cell: met.** `link_notice` 0 in every heartbeat of both attempts (319 + 344); no
  `link_notice_shown` / `_cleared` row; the five reports `link_notice_shown` 0.

## 4. The CONFIRMED rule (CL-B7 §6)

- **At the close (18:04:48Z, `check_end_before_rule.json`):** the properties empty; the drop-in removed; eleven lines;
  no `e3_flag.conf`; `flags_absent` true; the client on the LAN (the newest `token_issued` lan); 5180 MHz
  (`adb_reads/*stage2*`); `fcd924c2…` paired (`client_end.json`); the two units only (`units_end.txt`).
- **The cell valid** (§1). **The behaviours as today where no flag was set:** no client property was set. The notice's
  one intended difference held (armed by default, 0 on 5 GHz, never shown). The rest read as CL-B13 cell 1:
  - the restart guard: every return `via_start`, with the guard's end in the start;
  - the link report: every heartbeat carries the link keys;
  - at each Home press, the stack's silence save at 401-404 ms, then the input hold at 953-955 ms and its handover
    (CL-B13: 952-954 ms);
  - 0 stall pauses (CL-B13 cell 1 had one).
- **The rule gives CONFIRMED:** `fcd924c2…9b96` stays on the onn.
- **The pin moved** (`cl_b14_pin.diff`, `pin_predecessors/`, `pin_predecessor_sha256.txt`, `pin_after_sha256.txt`):
  `tools/e1_suite.py` `EXPECT_APK`; `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`; its test, now
  `test_the_preflight_expects_the_cl_b14_apk`.
- **Tests** (`pin_tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK; `git
  diff --check` clean.
- **`e3_state --check` ok on eleven, APK CONFIRMED** (`check_end.json`).
- **The APKs, nothing deleted (gitignored):** `PrivyHub/app/build/cl_b14_installed/app-debug.apk` (`fcd924c2…`, on the
  onn); `PrivyHub/app/build/cl_b13_installed/app-debug.apk` (`6bddafc0…`, the previous CONFIRMED one).
- **The notice is now on by default in the CONFIRMED APK.** On 2.4 GHz it shows at the first tick. Off:
  `setprop debug.privyhub.link_notice 0`.

## 5. The reading, as pre-registered

- **Every row R1-R7 met at every return → G-A7, the user's question, in B's words:** "Adopt
  `PRIVYHUB_RESTART_FAST_UNLOCK=1` as the twelfth line? It lets the game resume at the new picture's check, ~1.2-2.0 s
  after a Home return, without waiting for the old session's audio teardown."
  - **Measured:** the picture back 1.15-1.86 s at four returns (G-A5 alone, CL-B13: 1.74-3.12). The lock was released at
    the check, and the old encoder's picture frames stopped at the entry.
  - **The cost:** the old audio capture SIGKILLed if still alive 300 ms after its stop began (two of four returns here);
    the old encoder SIGKILLed 100 ms after its SIGTERM; the new audio starting just after the ready (−0.11 to +0.13 s
    from `session_started`; the client waits up to 3 s for it, with no underrun counted); the relay stopped before the
    old encoder's exit.
  - **For B beside it, not blocking as pre-registered:** the 8-byte packet at the old encoder's exit, and
    `relay_stopped_ms` 500 once.
  - **Off:** remove the line (the drop-in) and restart the companion. The restart is then G-A5's worker (CL-B13 cell 1).
- **G-A7 is NOT applied here.** B prepared no G-A7 patch. A would write it in G-A5's applied form on the user's say-so.
- **Not exercised:** the surface / process return paths; 2.4 GHz (the notice's shown path).

## 6. State at the end (~18:10Z)

- **ELEVEN lines; `--check` ok; APK `fcd924c2…9b96` CONFIRMED** on the onn, paired, 5180 MHz; the seven properties
  empty. No `e3_flag.conf`, no game. Units: the companion and `privyhub-link-n1`. Every CL-B14 unit closed and
  collected.
- No sudo, no nft. The Opal was untouched. **No `setprop`.** adb was used for the install, state reads and the one events
  read.
- No address or identifier in any kept file (`redact_check.txt`). Nothing fetched. Nothing deleted (attempt 1's files
  renamed). Nothing adopted. Nothing committed. `logs/cl_b14_git_status.txt`.
- **The user's messages, verbatim** (`user_lines.txt`):
  1. "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
  2. "Stage 2" (after attempt 1 had closed with no press)
  3. "We may need to redo that, it was not obvious I needed to interact"
  4. "Go"
  5. "Stage 2"
  6. "The returns ran as expected"

## 7. Files (`cl_b14_2026-10-26/`, `manifest.sha256` over all of it)

- **The start and the install:** `baseline_head.txt`, `git_status_at_start.txt`, `check_at_start.json`,
  `e3_check_at_start.txt`, `client_before_install.json`, `adb_reads/wifi_first_read.json`, `adb_reads/properties*.txt`,
  `cl_b14_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`, `tools_at_preregistration_sha256.txt`,
  `apk_sha256.txt`, `signer_check.txt`, `install_at.txt`, `install.log`, `client_after_install.json`,
  `check_after_install.json`.
- **The driver:** `cl_b14_driver.py`, `cl_b14_driver_vs_cl_b13.diff`, `cl_b14_suite_call.py`, `dry_run/`.
- **The cell:** `cells.jsonl` (attempt 1, the cell), `cl_b14_state_attempt1.json`, `cl_b14_state.json`,
  `cell_attempt1_note.txt`, `cell_*launched_at*`, `cell_*playing_at*`, `check_before_relaunch.json`,
  `client_before_relaunch.json`, `units_before_cell.txt`, `runs/` (each with `band.jsonl`, `logs_run1/`, the journal,
  the mid-cell e3 read).
- **Stage 2:** `cl_b14_read.py`, `record_read.json`, `record_read_console.txt`, `journal_precise_cell.txt`,
  `adb_reads/logcat_events_cell.txt`, `cl_b14_events_read.py`; the pin (`cl_b14_pin.diff`, `pin_predecessors/`,
  `pin_*_sha256.txt`, `pin_tests.txt`); `check_end_before_rule.json`, `check_end.json`, `client_end.json`,
  `units_end.txt`, `adb_reads/*stage2*`; `user_lines.txt`, `redact_check.py`, `redact_check.txt`.
