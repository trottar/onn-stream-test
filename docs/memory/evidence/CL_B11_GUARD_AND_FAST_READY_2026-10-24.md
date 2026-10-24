---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: e878d68 (queue F committed; this record and its files uncommitted beside it)
---

# CL-B11 — the guard on every path (cell 1), the fast ready (cells 2, 3): MEASURED, 3 / 3 valid; `e2db0aa0…` CONFIRMED

**Classification: MEASURED. All three cells were playing and valid, with the host gates met.** By CL-B7 §6's rule,
B's APK **`e2db0aa0…6b33` stays and is CONFIRMED.** The pin moved, and `--check` is ok on nine lines.

**The rows, in one paragraph each:**
- **Cell 2 (`@both`, fast ready): every row met but one.** In 5 of 5 blackouts:
  - the silence save at 0.40-0.41 s;
  - the hold's pause at 951-959 ms;
  - **`resumed via client_ready_hold` 146-458 ms after the packets return** (CL-B10: `hold_return_stall` 427-2,130);
  - a `state` load, net 24;
  - no second pause.
  - **Not met: one `state_saved` outside the blackouts:** kind silence, 205 ms before `session_ended`, at the
    window's end.
- **Cell 3 (`@down`, fast ready): every row met but the same one.** In 5 of 5 blackouts:
  - the stall save at 429-433 ms, 103-106 ms **before** the pause (pause age 429-433);
  - **`resumed via client_ready_stall` 133-248 ms after the downlink returns;**
  - **0 `encoder_restart`, 0 `stall_handover_v2`**, 0 `recovery_escalation`;
  - net 26; `client_ready_after_stall`; no second pause;
  - `fast_ready_releases` 5.
  - The picture was held **4.13-4.25 s per 4-s drop** (CL-B10 5.3-7.2 s).
  - **Not met:** one silence save, 207 ms before `session_ended`.
- **Cell 1 (the guard): every row met but one interval.**
  - **The old report and `native-stream-stop` came before the new start** (`session_ended` 15:26:02.753, the stop
    15:26:05, the start 15:26:06).
  - `restart_cause` present: trigger **`recreate`**, `away_ms` 21,356, `old_report_posted` / `stop_posted` true.
  - **52 underruns in the new session's 441 s** (CL-B10: 2,418 in 28 s).
  - The event log names the path: **a new stream activity in the same live process.** The old instance was stopped,
    not destroyed, and no process died.
  - **Not met:** one 2-s interval of **221 underruns** in the new instance's first 2.5 s, before the guard's restart
    rebuilt the audio. After it, 0-15 per interval.

**The reading, as pre-registered ("meet every row → candidate; else back to B with the rows"):**
- **The stack goes back to B with one row:** the save at each session's end.
- **The guard goes back to B with one row:** the 221-underrun interval before its restart.
- Both are much narrower than CL-B10's misses. The costs are measured in §5.

**The user's line, verbatim:** "I had to click into the game but seemed to be at same spot".

Nothing adopted. Nothing committed.

Task: `handoffs/CL-B11_GUARD_AND_FAST_READY_TASK.md` (PART 1, PART 2, stage 3), session A. B's strings:
`SESSION_B_DONE_2026-10-24F.md` items 4-9; B15 §0; B16 §3-§4. Launch: `CL_B11_LAUNCH_2026-10-24.md`. Files:
`cl_b11_2026-10-24/`.

## 0. How it ran

- **The pre-registration** `cl_b11_preregistration.txt` (`1b6f14f4…6a98`) was hashed at 10:30:50Z, before the
  install. It covers all three cells. Its hash was checked again before cell 1's launch (OK).
- **PART 1:** `privyhub-cl-b11` ran cells 2 and 3 from 10:33:13Z and closed "all 2 cells done" at 11:01:49Z.
- **PART 2:** `privyhub-cl-b11-p2` (`--cell 1`) ran 15:19:28-15:33:43Z and closed "all 1 cells done".
  - Before it: the band 5 GHz (5180 MHz, RSSI −67), the properties `1 / 1 / empty / empty`, nine lines, paired.
- **Every cell:**
  - E1-SNES-STREAM (snes9x), the nine adopted lines plus the cell's drop-in;
  - read back at the stream and under load: 16 / 16 (cells 2, 3) and 10 / 10 (cell 1);
  - removed at the teardown; `flags_absent` true; nine lines after;
  - `restart_guard` / `stall_signal` = 1 and `link_notice` / `link_report` empty, before and after each cell;
  - the band every 10 s: 5180 MHz in all 254 reads.
- **The stage-3 reader:** `cl_b11_read.py` (`record_read.json`, `record_read_console.txt`). It is CL-B10's, with B6's
  `measure` and UX-R3's `evening` / `counts` exec'd unedited and asserted against LINK-R1's pins. It computes per
  blackout:
  - the return:
    - `@both`: the end of the ≥ 3-s controller gap, the first packet back (the gaps read 4,004-4,013 ms);
    - `@down`: the client's last frame (the pause's `at_utc` − `age_ms`) + 4,000 ms (the shim's 4-s span; its 1-s lines
      read 5 lines per span, 120 s apart).
  - the resume's distance from the return;
  - held = onset → resume;
  - the saves outside `[onset − 0.1 s, return + 2 s]` of every blackout.
- **Disclosed, the stage messages:**
  - The user's line on the Home press came **before** "Stage 3", at 15:26:40Z, mid-cell
    (`p2_user_words_mid_cell1.txt`). Their "Stage 3" (15:26:54Z) carried no line and came before the window's end, so
    stage 3 waited for the unit to close at 15:33:43Z. The line used here is that earlier one.
  - The one `adb logcat -b events -d` read was taken at 15:27:19Z, before the close, while the press was in the ring
    buffer.

## 1. Validity and the gates

| cell | drop-in | started | PLAYING (attempt) | window | environ stream / load | validity | RetroArch / capture / dup+drop | rendered | post-FEC loss / min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | `blackout-4s@both` + the six stack flags | 10:33:14Z | 10:35:42 (1) | 600 | 16 / 16 | valid | 59.999 / 59.996 / 0.1 | 57.90 | 1,622 (the blackouts) |
| 3 | `blackout-4s@down` + the same | 10:47:34Z | 10:49:56 (1) | 600 | 16 / 16 | valid | 59.999 / 59.996 / 0.1 | 57.91 | 1,613 (the blackouts) |
| 1 | `none@post-fec,seed=1` | 15:19:29Z | 15:21:51 (1) | 600 | 10 / 10 | valid | 59.999 / 59.947 / 0.1 | 59.73 | 38.7 |

- **The shim's dark spans:** cell 2 had 5, each 5 lines, 120 s apart, `uplink_dropped` 9,073. Cell 3 had 5 likewise,
  uplink 0, as `@down`. Cell 1 dropped nothing.
- **Cell 1 is not invalidated by the Home press** or the new client session it caused (pre-registered).
- `stall_resume_config` in cells 2 and 3: `fast_ready` true, `save_from_signal` true, `v2_newest_s` 0.3, `v2_ms` 5000.

## 2. Cell 2 — the stack under `blackout-4s@both`, per blackout

| pause at (UTC) | the save (kind, after onset) | pause age ms | packets back | via | **resume after the return ms** | held s | release, net (restored) | 2nd pause |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10:37:16.582 | silence, 405.9 | 959 | 10:37:19.535 | `client_ready_hold` | **399** | 4.40 | `state`, **24** (35) | none |
| 10:39:16.585 | silence, 407.8 | 957 | 10:39:19.540 | `client_ready_hold` | **146** | 4.16 | `state`, **24** (35) | none |
| 10:41:16.587 | silence, 407.0 | 953 | 10:41:19.540 | `client_ready_hold` | **231** | 4.24 | `state`, **24** (35) | none |
| 10:43:16.571 | silence, 401.8 | 951 | 10:43:19.541 | `client_ready_hold` | **399** | 4.41 | `state`, **24** (35) | none |
| 10:45:16.575 | silence, 405.8 | 951 | 10:45:19.532 | `client_ready_hold` | **458** | 4.47 | `state`, **24** (35) | none |

| row (B item 7) | CL-B10 | **CL-B11** |
| --- | --- | --- |
| `stall_resume_config` `fast_ready` / `save_from_signal` / `v2_newest_s` 0.3 | — | **met** |
| `state_saved` kind silence ~0.40 s | 400.8-406.8 | **met 5 / 5** (401.8-407.8) |
| the hold's pause ~950 ms | 950-958 | **met 5 / 5** (951-959) |
| **resumed via `client_ready_hold` ≤ 1.0 s after the packets return** | `hold_return_stall`, 427-2,130 | **met 5 / 5: 146-458 ms** |
| `input_release` method `state`, net ≈ 24 | 24 | **met 5 / 5** (24) |
| no second pause | met | **met** (5 pauses, 1 session) |
| **zero `state_saved` outside the blackouts** | 4 | **NOT MET: 1** (10:47:14.071, kind silence, 400.9 ms, 205 ms before `session_ended` 10:47:14.276) |

- **The save outside:** the window's end. The controller went silent as the stream ended, and the hold's silence save
  fired at 400 ms, before the stop. CL-B10's other three extra saves (the 150-163 ms gate stalls) are gone, as B16
  built.
- At each blackout, `input_hold_handover` (trigger `client_stall`) came at ~4.0 s, then `client_ready_after_hold`,
  `stall_gate_after_return` (5-45 ms) and `stall_end_late`.
- Silences ≥ 250 ms: 4.42 / 10 min, all 5 the blackouts. Audio underruns 55 in 701 s (≤ 14 per 2-s interval).

## 3. Cell 3 — the stack under `blackout-4s@down`, per blackout

| pause at (UTC) | the save (kind, after onset) | the save before the pause | pause after the last frame | the downlink back | via | **resume after the return ms** | held s | release, net | encoder restart / v2 handover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10:51:51.614 | stall, 432.1 | 103 ms | 432 ms | 10:51:55.182 | `client_ready_stall` | **182** | 4.18 | `state`, **26** | 0 / 0 |
| 10:53:51.665 | stall, 433.1 | 103 ms | 433 | 10:53:55.232 | `client_ready_stall` | **183** | 4.18 | `state`, **26** | 0 / 0 |
| 10:55:51.602 | stall, 432.1 | 105 ms | 432 | 10:55:55.170 | `client_ready_stall` | **248** | 4.25 | `state`, **26** | 0 / 0 |
| 10:57:51.637 | stall, 432.1 | 104 ms | 432 | 10:57:55.205 | `client_ready_stall` | **133** | 4.13 | `state`, **26** | 0 / 0 |
| 10:59:51.624 | stall, 429.1 | 106 ms | 429 | 10:59:55.195 | `client_ready_stall` | **144** | 4.14 | `state`, **26** | 0 / 0 |

| row (B item 8) | CL-B10 | **CL-B11** |
| --- | --- | --- |
| one `state_saved` kind stall, `save_after_onset_ms` ≈ 400 (not 150), **before** the pause | 150.5-156.2 | **met 5 / 5** (429.1-433.1; 103-106 ms before) |
| the pause 400-460 ms after the client's last frame | 423-430 | **met 5 / 5** (429-433) |
| **resumed via `client_ready_stall` ≤ 1.0 s after the downlink returns** | recovering 5.3-7.2 s | **met 5 / 5: 133-248 ms** |
| **no `encoder_restart`, no `stall_handover_v2`**, no `recovery_escalation` | 1 restart | **met** (0 / 0 / 0) |
| net ≈ 24 | 9 | **met** (26) |
| `client_ready_after_stall`; no second pause | met | **met 5 / 5** |
| the client report's `fast_ready_releases` 5 | — | **met** (5; `fast_ready_frame_to_post_ms` 0) |
| **zero saves outside the blackouts** | — | **NOT MET: 1** (11:01:29.086, kind silence, 401.0 ms, 207 ms before `session_ended` 11:01:29.293) |

- **The picture held:** 4.13-4.25 s from the client's last frame to the resume, for a 4-s drop. That is ≤ 0.25 s
  past the drop's end; CL-B10 was 5.3-7.2 s, and the pre-registration said ≤ ~1.3 s.
- 0 uplink silences (as `@down`). Underruns 46 in 697 s (≤ 5 per interval). Cell 2's report also read
  `fast_ready_releases` 5.

## 4. Cell 1 — the Home press, 5 GHz

**The timeline** (the host's logs; the event-log rows are the onn's local EDT, here in UTC):

| UTC | row |
| --- | --- |
| 15:21:51.645 | `session_started` (PLAYING 15:21:51) |
| 15:25:42.158 / 44.897 | (events) `NativeStreamActivity` paused / stopped: the Home press |
| 15:25:45.307 | the controller goes silent (gap 16,919 ms to 15:26:02.226) |
| 15:25:50.666 | `desync_pause` trigger `controller_silence` (age 5,264 ms) |
| 15:25:54.201 | (events) `MainActivity` created: the user opening PrivyHub ("I had to click into the game") |
| 15:26:01.629 | (events) **a new `NativeStreamActivity` created**, in the same process (no `am_proc_start`, no `wm_on_destroy_called`) |
| 15:26:02.670 | **`decoder-session-log`: the old session's report** (237.5 s, 74 underruns) |
| 15:26:02.753 | **`session_ended`** |
| 15:26:05 | **`native-stream-stop`** |
| 15:26:06 | **`native-stream-start`** (the new session); `native-stream-ready` 15:26:09; `session_started` 15:26:09.479 |
| 15:33:23 | the window's end: the new session's report (440.8 s), `session_ended`, the stop at 15:33:24 |

**The one events read** (`adb_reads/p2_logcat_events_around_press.txt`; the PrivyHub rows of the `am_*` / `wm_on_*`
tags only — process names, pids and activity class names, no uid, token or other field):
- **No `am_kill` or `am_proc_died` at the press.** The only kill (15:21:34) is the suite's own force-stop before its
  launch.
- So the path is **the second-launch / new-instance path in a live process.** B15 §0 names it ("a second launch from
  the app … while a stopped stream instance stays in the back stack"). CL-B10's press took the process-death path.

| row (B item 6) | CL-B10 | **CL-B11** |
| --- | --- | --- |
| the old report and `native-stream-stop` (`session_ended`) **before** the new `native-stream-start` | NOT MET (neither) | **met** (report 15:26:02.670, `session_ended` 02.753, stop 15:26:05; start 15:26:06) |
| `restart_cause.trigger` (`process` / `surface`) | absent | **met as B15 built it: `recreate`** (B15's value for a new instance in a live process, which the events read confirms; `old_report_posted` / `stop_posted` true, `restarts` 1) |
| `away_ms` ≈ the time away | absent | **met: 21,356** (pause 15:25:42.2 → the new instance 15:26:01.6 = 19.5 s, + its start) |
| the new session's underruns ≈ the others' (0-13 per 2-s interval, not ~85 / s) | NOT MET (2,418 in 28 s) | **after the guard's restart: met** (52 in 441 s; ≤ 15 per interval, as cell 2's 14 and the first session's 14). **NOT MET in one interval:** 221 underruns between the new instance's first heartbeat (15:26:02.7) and the restart (15:26:06), before the audio rebuild |
| one `logcat -b events -d` read names the path | — | **met** (a new activity in the same process) |

- **The 221:** the new instance's receiver heard the host's old stream for ~3.4 s, between its own start and the
  guard's stop / start. Then the rebuild reset the count to 0. That is B11's lateness mechanism, cut from 28 s to one
  interval.
- **On 5 GHz** (B6's edge rule; UX-R3's hitch reader):

  | span | streaming s | silences ≥ 250 ms | per 10 min | max ms | hitch s | per 10 min |
  | --- | --- | --- | --- | --- | --- | --- |
  | before Home (15:21:51-15:25:45) | 213 | 2 | **5.63** | 442 | 5 | **12.9** |
  | after the return (15:26:09-15:33:23) | 414 | 3 | **4.35** | 564 | 5 | **6.9** |
  | CL-B10 cell 1 | 195 + 1 + 12 | 0 | 0.0 | — | 0 | 0.0 |

  Not zero this time, at 5180 MHz in all 331 heartbeats (RSSI −68…−66), and below 1 s each. Post-FEC loss read
  38.7 / min (CL-B10 cell 1: 11.6).
- **The user's line, verbatim:** "I had to click into the game but seemed to be at same spot". Opening PrivyHub's menu
  and choosing the game started a new stream activity; the guard carried the session over. Away ~20 s, not 5.

## 5. The reading, as pre-registered

- **The stack (cells 2, 3): back to B with one row.** Every row was met in all 10 blackouts — the fast ready, the 400-ms
  save, no restart or v2 handover, net 24 / 26 — except one: **a silence save at each session's end** (1 per cell,
  ~205 ms before `session_ended`).
  - **The costs, measured:**
    - 24 (`@both`) / 26 (`@down`) frames per drop, restored to the save;
    - a save per real stall, plus one at each session's end (the 150-ms gate-stall saves are gone);
    - **the picture frozen 4.13-4.47 s per 4-s drop, 0.13-0.46 s past its end** (CL-B10: 3.5-7.2 s).
  - Against CL-B10:
    - resume after the return 427-2,130 ms → **133-458 ms**;
    - held 5.3-7.2 s (`@down`) → **4.13-4.25 s**;
    - saves outside the blackouts 4 → **1 per cell**.
- **The guard (cell 1): back to B with one row.** The old report, the stop, `restart_cause` and `away_ms` were all met
  on the new-instance path. The miss is **one 2-s interval of 221 underruns before the guard's restart**; after it,
  ≈ the others'.
  - **Cost:** a report and a stop posted at each return, the audio rebuilt, one file in `noBackupFilesDir`, and ~3 s
    more before the picture is back.
  - Against CL-B10's three rows (old report / `session_ended` before the start, `restart_cause`, underruns): **not
    met ×3 → met, met, met but one interval.**
  - **Not exercised:** the process-death path (CL-B10's), and the same-instance surface path.

## 6. The CONFIRMED rule (CL-B7 §6)

- **All three cells (2, 3, 1) were valid** (§1).
- **The flag-absent behaviours:** read as today in cell 1, which carried only the `none` line (no
  `stall_resume_config`, no hold rows; one controller-silence pause at the press, as v2 does).
- **Not exercised, disclosed:** no cell ran with the client properties empty. The property-empty client and the
  host-flag-absent fast ready rest on B's proofs (B15: the guard only behind `restart_guard`; B16: `FastReady` only
  inside the host's `stall_resume` key, sent only with B12's owner). That is the same by-construction ground CL-B10 §6
  cited. The user's next play with the properties empty is the first live read.
- **The rule gives CONFIRMED:** `e2db0aa0…6b33` stays on the onn.
- **The pin moved** (`cl_b11_pin.diff`, `pin_predecessors/`, `pin_predecessor_sha256.txt`, `pin_after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK`;
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`;
  - its test, now `test_the_preflight_expects_the_cl_b11_apk`.
- **Tests** (`pin_tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK; `git
  diff --check` clean.
- **`--check` ok on nine, APK CONFIRMED** (`check_end.json`).
- **The APKs, nothing deleted (gitignored):**
  - `PrivyHub/app/build/cl_b11_installed/app-debug.apk` (`e2db0aa0…`, on the onn);
  - `PrivyHub/app/build/cl_b10_installed/app-debug.apk` (`da09e154…`, the previous CONFIRMED one).

## 7. State at the end (~15:40Z)

- **The band 5 GHz** (5180 MHz, standard 5, RSSI −68; `adb_reads/p2_wifi_stage3.json`).
- **The properties cleared and read back empty** (`adb_reads/p2_stage3_properties.txt`): `restart_guard`,
  `stall_signal`, `link_notice`, `link_report`. `wifi_lock`, `loss_guard` and `opus_decode` were empty.
- **Nine lines,** no `e3_flag.conf`, `flags_absent` true, `--check` ok, APK CONFIRMED.
- **The onn: `e2db0aa0…`, paired** (`client_end.json`: identity v2, the device secret, the id in the hub's store, 1
  device).
- **Units:** the companion and `privyhub-link-n1` (sleeping toward 2026-10-25 04:30Z; nights done 1). Both CL-B11
  units are closed and collected.
- No sudo, no nft. The Opal was untouched. adb was used for the install, the named `setprop`s, the one events read and
  state reads only.
- No address or identifier in any kept file (`redact_check.txt`). Nothing fetched or deleted. Nothing adopted.
  Nothing committed. `logs/cl_b11_git_status.txt`.

## 8. Files (`cl_b11_2026-10-24/`, `manifest.sha256` over all of it)

- **PART 1:** the launch record's files (`CL_B11_LAUNCH_2026-10-24.md` §6); `cells.jsonl` (rows 2, 3, 1);
  `cl_b11_state.json`; `runs/2_…`, `runs/3_…`.
- **PART 2:**
  - `adb_reads/p2_wifi_before_cell1.json`, `adb_reads/p2_properties_before_cell1.txt`, `p2_check_before_cell1.json`,
    `p2_client_before_cell1.json`, `p2_units_before_cell1.txt`;
  - `p2_cell1_launched_at.txt` / `_launch_console.txt`, `p2_cell1_playing_at.txt`, `cl_b11_p2_state.json`;
  - `runs/1_snes_5ghz_restart_guard_all_paths/` (with `band.jsonl`);
  - `p2_user_words_mid_cell1.txt`.
- **Stage 3:**
  - `adb_reads/p2_logcat_events_around_press.txt`, `adb_reads/p2_stage3_properties.txt`, `adb_reads/p2_wifi_stage3.json`,
    `p2_check_stage3.json`;
  - `cl_b11_read.py`, `record_read.json`, `record_read_console.txt`;
  - the pin: `cl_b11_pin.diff`, `pin_predecessors/`, `pin_*_sha256.txt`, `pin_tests.txt`;
  - `check_end.json`, `client_end.json`, `units_end.txt`;
  - `redact_check.txt`.
