---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: de3c9d0 (queue G committed; this record and its files uncommitted beside it)
---

# CL-B12 — the client defaults, the umbrella, both Home returns: MEASURED, 3 / 3 valid; `20e3e339…` CONFIRMED

**Classification: MEASURED. All three cells were playing and valid, with the host gates met.**
- **Every client property was EMPTY throughout. No `setprop` was run.**
- Every host drop-in was the impairment line plus **`PRIVYHUB_LINK_RECOVERY=1` alone** (11 lines at the stream).
- By CL-B7 §6's rule, B's APK **`20e3e339…563d` stays and is CONFIRMED**. The pin moved, and `--check` is ok on nine.

**The rows:**
- **Cells 2 / 3 (the stack via the umbrella, the client's defaults): every behaviour row met.**
  - In 11 of 11 blackouts the resume came via the client's ready **108-349 ms after the return**; 0 `encoder_restart`,
    0 `stall_handover_v2`. Net 24 / 26. The picture was held 4.11-4.35 s per 4-s drop.
  - **0 `state_saved` outside the blackouts** (CL-B11: 1 per cell).
  - At each teardown: the `bye`, then `state_save_skipped` reason `client_bye` at ~401 ms, and no hold.
  - `stall_signal_ms` 150 and one `fast_ready_release` per blackout, **with no property set**.
  - **Not met as written: the `link_recovery_config` row.** It reads `implied` [] / `explicit` the six, where B's row is
    `implied` the six / `explicit` {}. This is a logging defect: `plugins/games.py` logs a second `apply()` after the
    import-time one. The six were implied: the environ held the umbrella only, and `e3_state.py` read all `implied 1`.
- **Cell 1 (B17's guard order, two Home presses): every row met at both returns but one interval.**
  - No separate `native-stream-stop`. The `session_ended` row was logged by the start (`guard_end=1`), and the old
    report came 56-70 ms after the start's response.
  - `restart_cause` `flush` `via_start`, `host_ended_session` true, **`create_to_start_ms` 280 and 96**, trigger
    `recreate` both times.
  - The first interval after each new `session_started` had 0 underruns.
  - **Not met:** one interval of **30** underruns in press 1's new session, at its end. That is the heartbeat after
    press 2's Home (the activity paused 1.3 s before), not a return.
  - **Both returns took the new-instance path.** The "direct" return (the tile / recents) also went through
    `MainActivity` (the events reads), so `surface` / `process` was not exercised.
- **On 5 GHz:** 0 silences in every span (CL-B11 cell 1: 4.4-5.6 / 10 min). Hitch s 3.9-9.9 / 10 min.

**The reading, as pre-registered ("every row met → candidates for G-A4; else back to B with the rows"):** two rows
were not met as written: the config row's `implied` / `explicit` (a log line), and the one 30-underrun interval at
press 2's Home. **So the stack and the guard go back to B with those two rows.** Every behaviour row of the stack was
met, and every return row of the guard. The costs (§5) are what the user's G-A4 question rests on.

**The user's line, verbatim:** "Each home and return behaved as expected and ran well."

Nothing adopted (G-A4 is a later prompt). Nothing committed.

Task: `handoffs/CL-B12_DEFAULTS_AND_UMBRELLA_TASK.md` (PART 1, PART 2, stage 3), session A. B's strings:
`SESSION_B_DONE_2026-10-24G.md` items 4-9; B17-B20. Launch: `CL_B12_LAUNCH_2026-10-24.md`. Files:
`cl_b12_2026-10-24/`.

## 0. How it ran

- **The pre-registration** `cl_b12_preregistration.txt` (`b377b34e…1966`) was hashed at 16:37:32Z, before the
  install. It was checked again before cell 1 (OK).
- **PART 1:** `privyhub-cl-b12` ran cells 2 and 3 from 16:39:44Z and closed "all 2 cells done" at 17:08:35Z.
- **PART 2:** `privyhub-cl-b12-p2` (`--cell 1`) ran 17:09:48-17:24:04Z and closed "all 1 cells done".
- **Every cell:**
  - E1-SNES-STREAM (snes9x); the nine lines + `PRIVYHUB_IMPAIRMENT=<spec>` + `PRIVYHUB_LINK_RECOVERY=1`;
  - read back at the stream and under load: 11 / 11;
  - `tools/e3_state.py` mid-cell: `link_recovery.stack` all six `implied 1`, environ 11;
  - removed at the teardown; `flags_absent` true; nine lines after;
  - **the seven properties empty before and after**;
  - the band every 10 s: 5180 MHz in all 255 reads.
- **The stage-3 reader:** `cl_b12_read.py` (`record_read.json`, `record_read_console.txt`). It is CL-B11's reader
  (B6's `measure`, UX-R3's `evening` / `counts`, unedited, pin-asserted), plus the teardown rows, the config rows, and
  cell 1's per-session underruns (the sessions split where `elapsed_ms` resets).
- **The two events reads** (`adb_reads/p2_logcat_events_press{1,2}.txt`, `cl_b12_events_read.py`): one dump per press,
  each kept to its press's window. **Disclosed:** both were taken at 17:22:30Z, after the second press. The ring
  buffer held both (7,852 lines from 06:31 EDT).
- **Disclosed:**
  - Cell 2 reached PLAYING on the suite's second launch attempt. The first got no stream within the launcher's wait,
    and no failure summary was written. As a result its window held **6 blackouts**, not 5.
  - Cell 1's teardown raced: the suite's `POST /plugins/games/stop` (13:23:44 EDT) landed just before the client's
    `native-stream-stop`, which got **503**. The skip reason read `state_ended` there (§4).

## 1. Validity and the gates

| cell | drop-in | started | PLAYING (attempt) | environ stream / load / mid-cell e3 | validity | RetroArch / capture / dup+drop | rendered | post-FEC loss / min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | `blackout-4s@both` + umbrella | 16:39:45Z | 16:42:24 (2) | 11 / 11 / 11 | valid | 59.999 / 59.996 / 0.1 | 57.88 | 1,620 (the blackouts) |
| 3 | `blackout-4s@down` + umbrella | 16:54:16Z | 16:56:40 (1) | 11 / 11 / 11 | valid | 59.999 / 59.994 / 0.1 | 57.86 | 1,638 (the blackouts) |
| 1 | `none@post-fec,seed=1` + umbrella | 17:09:49Z | 17:12:12 (1) | 11 / 11 / 11 | valid | 59.999 / 59.948 / 0.0 | 59.57 | 28.8 |

- **The dark spans:** cell 2 had 6, each 5 lines, 120 s apart, `uplink_dropped` 10,927. Cell 3 had 5, uplink 0. Cell
  1 dropped nothing.
- **The config rows**, in all three cells:
  - `link_recovery_config` (see below);
  - then `input_hold_config` hold 250, `input_hold_b6_config` 950, `input_hold_b8_config`, `input_hold_rewind_config`,
    **`input_hold_rewind_cores_config` mode `state`**, **`stall_signal_config` threshold 400**, and
    **`stall_resume_config` `fast_ready` / `save_from_signal` true**, `v2_newest_s` 0.3.
- **`link_recovery_config`** reads `umbrella` true, `implied` [], `explicit` {the six: "1"}.
  - `plugins/games.py:34` applies the umbrella at import, which sets the six into `os.environ`. Line 201 logs a second
    `apply(os.environ)`, which then finds them present and reports them as explicit.
  - **The behaviour is the umbrella's:** the service environ held no individual line.
  - **Row NOT MET as written; a one-line fix for B** (log the import-time result).

## 2. Cell 2 — `blackout-4s@both` under the umbrella, per blackout

| pause at (UTC) | the save (kind, after onset) | pause age ms | packets back | via | **resume after the return ms** | held s | release, net |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16:43:48.019 | silence, 404.4 | 955 | 16:43:50.979 | `client_ready_hold` | **306** | 4.32 | `state`, **24** |
| 16:45:48.021 | silence, 400.8 | 959 | 16:45:50.980 | `client_ready_hold` | **291** | 4.30 | `state`, **24** |
| 16:47:48.023 | silence, 403.2 | 954 | 16:47:50.981 | `client_ready_hold` | **275** | 4.28 | `state`, **24** |
| 16:49:48.026 | silence, 405.2 | 953 | 16:49:50.983 | `client_ready_hold` | **324** | 4.33 | `state`, **24** |
| 16:51:48.030 | silence, 406.9 | 952 | 16:51:50.984 | `client_ready_hold` | **259** | 4.27 | `state`, **24** |
| 16:53:48.030 | silence, 401.9 | 953 | 16:53:50.980 | `client_ready_hold` | **349** | 4.35 | `state`, **24** |

| row (B items 6-7) | CL-B11 | **CL-B12** |
| --- | --- | --- |
| `link_recovery_config` implied the six / explicit {} | — (no umbrella) | **NOT MET as written** (implied [] / explicit the six: the log's second `apply`; behaviour the umbrella's) |
| the module configs (`stall_signal_config` 400, rewind mode `state`, `fast_ready` / `save_from_signal`) | met | **met** |
| silence save ~0.40 s; hold ~950 ms | 401.8-407.8; 951-959 | **met 6 / 6** (400.8-406.9; 952-959) |
| **resumed via `client_ready_hold` ≤ 1.0 s after the packets return** | 146-458 ms | **met 6 / 6: 259-349 ms** |
| `state`, net 24; no second pause | met | **met 6 / 6** (6 pauses, 1 session) |
| **zero `state_saved` outside the blackouts** | NOT MET (1, the session's end) | **met (0)** |
| the teardown: `session_end_bye`, then `state_save_skipped` `client_bye` (~400 ms), no hold | — | **met:** bye 16:53:55.451; skip `client_bye` at 401.0 ms (56.257); `session_ended` 56.388; `input_hold_skipped_paused` (no pause) |
| the report `stall_signal_ms` 150, no property set | (property 1) | **met** (150; 497 stalls sent) |
| the report `fast_ready_releases` 5 | 5 | **met per blackout: 6 for 6** (the 5 assumed five blackouts in the window; disclosed) |

## 3. Cell 3 — `blackout-4s@down` under the umbrella, per blackout

| pause at (UTC) | the save (kind, after onset) | save before the pause | the downlink back | via | **resume after the return ms** | held s | net | restart / v2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16:58:34.050 | stall, 429.1 | 104 ms | 16:58:37.621 | `client_ready_stall` | **161** | 4.16 | **26** | 0 / 0 |
| 17:00:34.053 | stall, 432.1 | 105 ms | 17:00:37.621 | `client_ready_stall` | **181** | 4.18 | **26** | 0 / 0 |
| 17:02:34.054 | stall, 440.1 | 104 ms | 17:02:37.614 | `client_ready_stall` | **156** | 4.16 | **26** | 0 / 0 |
| 17:04:34.055 | stall, 432.1 | 104 ms | 17:04:37.623 | `client_ready_stall` | **182** | 4.18 | **26** | 0 / 0 |
| 17:06:34.108 | stall, 425.1 | 104 ms | 17:06:37.683 | `client_ready_stall` | **108** | 4.11 | **26** | 0 / 0 |

| row | CL-B11 | **CL-B12** |
| --- | --- | --- |
| `link_recovery_config` / the module configs | — / met | **NOT MET as written / met** (as cell 2) |
| the stall save at ~430 ms, before the pause | 429-433, 103-106 ms before | **met 5 / 5** (425-440; 104-105 ms before) |
| **resumed via `client_ready_stall` ≤ 1.0 s after the downlink returns** | 133-248 ms | **met 5 / 5: 108-182 ms** |
| 0 `encoder_restart`, 0 `stall_handover_v2` | 0 / 0 | **met** (0 / 0; 0 `recovery_escalation`) |
| net 24-26; no second pause | 26 | **met** (26; 5 pauses, 1 session) |
| **zero saves outside the blackouts** | NOT MET (1) | **met (0)** |
| the teardown bye | — | **met:** bye 17:08:11.827; skip `client_bye` 401.3 ms (12.493); `session_ended` 12.718; `input_hold_skipped_paused` |
| the report `stall_signal_ms` 150 / `fast_ready_releases` 5, no property | (property 1) / 5 | **met** (150 / 5) |

- Held 4.11-4.18 s from the client's last frame to the resume (CL-B11 4.13-4.25; CL-B10 5.3-7.2). Underruns ≤ 3 per
  interval. Cell 2 ≤ 13.

## 4. Cell 1 — two Home presses, 5 GHz, under the umbrella

**The two presses** (UTC; the events rows are the onn's EDT + 4 h):

| row | **press 1 (the menu)** | **press 2 ("direct": the tile / recents)** |
| --- | --- | --- |
| `NativeStreamActivity` paused / stopped (events) | 17:15:09.827 / 12.697 | 17:18:01.236 / 03.302 |
| the controller silent from | 17:15:13.191 | 17:18:03.769 |
| **the hold's silence save** (after onset) | 17:15:13.598 (401.8 ms) | 17:18:04.183 (400.9 ms) |
| **the hold's pause** (`input_hold`, age) | 17:15:14.235 (953 ms) | 17:18:04.822 (952 ms) |
| `input_hold_handover` → `controller_silence` (age) | 17:15:18.455 (5,264) | 17:18:09.034 (5,265) |
| `MainActivity` created (events) | 17:15:23.051 | 17:18:24.231 |
| **a new `NativeStreamActivity` created** (events; no `am_proc_*`, no destroy) | 17:15:27.809 | 17:18:28.927 |
| the controller back (`hold_return_armed` via `input_release`) | 17:15:28.650 | 17:18:29.584 |
| **`session_ended`, logged by the start's entry** (`native-stream-start?…&guard_end=1`) | 17:15:28.813 | 17:18:29.620 |
| **a separate `native-stream-stop`** | **none** | **none** |
| the start's response (journal) | 17:15:31.004 | 17:18:31.619 |
| **the old report received** | 17:15:31.073 (+70 ms after the response) | 17:18:31.675 (+56 ms) |
| `session_started` (the new ready) | 17:15:39.786 | 17:18:35.773 |
| **`restart_cause`** (the new session's report) | `flush` `via_start`, `host_ended_session` true, `stop_posted` false, `old_report_posted` true, **`create_to_start_ms` 280**, `away_ms` 16,559, **trigger `recreate`** | the same, **`create_to_start_ms` 96**, `away_ms` 26,269, **trigger `recreate`** |
| underruns: the first interval after `session_started` / the session's max / its sum | **0** / **30** (17:18:02.494, the last heartbeat: press 2's Home) / 39 | **0** / 2 / 13 |

| row (B item 8) | CL-B11 | **CL-B12, press 1** | **CL-B12, press 2** |
| --- | --- | --- | --- |
| the hold's pause (~950 ms) with a silence save | — (no hold in cell 1) | **met** | **met** |
| **no separate `native-stream-stop`** | a stop, ~2.3 s inside | **met** | **met** |
| `session_ended` logged by the start request | logged by the stop | **met** | **met** |
| the old report within ~1 s after | before the stop | **met** (70 ms after the start's response; 2.26 s after its entry, the host's teardown inside the start, as B17 states) | **met** (56 ms; 2.06 s) |
| `restart_cause` `flush` `via_start`, `host_ended_session` true | (B15's fields) | **met** | **met** |
| **`create_to_start_ms` ≤ 1,000** | — (the start ~4.4 s after the new activity) | **met: 280** | **met: 96** |
| trigger `recreate` (menu) / `surface` or `process` (direct) | `recreate` | **met: `recreate`** | **`recreate`** — the events read shows the new-instance path, so the trigger names it. **The direct (surface / process) path was not produced:** the tile / recents return also went through `MainActivity` |
| **the first 2-s interval after the new `session_started` ≤ 15** | 221 before the restart | **met (0)** | **met (0)** |
| **no interval of the new client session above 15** | — | **NOT MET: 1 (30)**, the interval in which press 2's Home paused the activity — not a return | **met (max 2)** |
| the game resumes from the hold's pause (no state loaded) | — | **met** (no `input_release` load; the user: "behaved as expected") | **met** |
| one `logcat -b events -d` read names the path | met | **met** (new instance, live process) | **met** (new instance, live process) |

- **The picture back:** from the new activity to `session_started`, 12.0 s (press 1) and 6.8 s (press 2). CL-B11 was
  7.9 s.
  - The host's start ran 2.19 / 2.00 s (entry → response), the encoder's teardown, as B17 stated.
  - Press 1's frames rendered from ~31.5 s (93 frames at the 31.521 heartbeat). Its ready came 8.8 s after the start's
    response, against 4.2 s at press 2: a difference for B to read.
- **The teardown:**
  - `session_end_bye` 17:23:43.518; the report 43.666; `session_ended` 43.718;
  - `state_save_skipped` reason **`state_ended`** (43.937, silence 401.5 ms); **no save, no hold**.
  - The suite's `games/stop` reached the host before the client's `native-stream-stop` (503), so the session was
    already ENDED at the 400-ms mark. Cells 2 and 3 read `client_bye`.
- **On 5 GHz** (B6's edge rule; UX-R3's reader):

  | span | streaming s | silences ≥ 250 ms / 10 min | hitch s / 10 min |
  | --- | --- | --- | --- |
  | session 1 (17:12:12 → press 1) | 161 | **0.0** | 9.9 |
  | session 2 (press 1 → press 2) | 124 | **0.0** | 4.1 |
  | session 3 (press 2 → the end) | 288 | **0.0** | 3.9 |
  | CL-B11 cell 1 | 213 / 414 | 5.63 / 4.35 | 12.9 / 6.9 |
  | CL-B10 cell 1 | 208 | 0.0 | 0.0 |

  5180 MHz in all 313 heartbeats; post-FEC loss 28.8 / min (CL-B11 38.7).
- **The user's line, verbatim:** "Each home and return behaved as expected and ran well."

## 5. The reading, as pre-registered

- **Not every row met → back to B with two rows:**
  1. **`link_recovery_config`** reads `implied` [] / `explicit` the six, in all three cells. It should log the
     import-time `apply`'s result (`plugins/games.py:201`). A log line; the behaviour is the umbrella's.
  2. **Cell 1, press 1's new session: one interval of 30 underruns**, at press 2's Home (the activity pausing), against
     "no interval of the new client session above 15". Every return interval was 0-1.
- **Not exercised:** the direct return to the old instance (`surface`), and the process-death path (`process`). Both
  returns in this cell were new instances in the live process.
- **The costs measured, for the user's G-A4 question:**
  - **Per 4-s drop:** the picture held 4.11-4.35 s (≤ 0.35 s past the drop's end), 24 (`@both`) / 26 (`@down`)
    frames restored to the save.
  - **Saves:** one per real stall, **none at a session's end** (B18).
  - **At a Home return:** the old report and the start's bookkeeping. The start went out 96-280 ms after the new
    activity; the host's ~2-s encoder teardown runs inside it; the picture was ready 6.8-12.0 s after the new activity.
  - **The client's halves** are on by default with this APK (no property). `debug.privyhub.stall_signal 0` /
    `restart_guard 0` turn them off.
- **Against CL-B11:**
  - resume after the return 133-458 → **108-349 ms**;
  - held 4.13-4.47 → **4.11-4.35 s**;
  - saves outside 1 per cell → **0**;
  - the guard's 221-underrun interval before the restart → **0 after each new start**, and the separate stop's
    ~2.3 s → **none**;
  - silences on 5 GHz 4.4-5.6 → **0 / 10 min**.

## 6. The CONFIRMED rule (CL-B7 §6)

- **All three cells (2, 3, 1) were valid** (§1).
- **The property-empty client was exercised in every cell** (all seven empty). B19's defaults acted: `stall_signal_ms`
  150 in every report, `restart_cause` written with no property.
- **The flag-absent host was not run, disclosed beforehand:** every cell carried the umbrella. It rests on B20's proof
  (AST: absent → nothing imported or read) and on CL-B11 cell 1's host behaviour with no stack line.
- **The rule gives CONFIRMED:** `20e3e339…563d` stays on the onn.
- **The pin moved** (`cl_b12_pin.diff`, `pin_predecessors/`, `pin_predecessor_sha256.txt`, `pin_after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK`;
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`;
  - its test, now `test_the_preflight_expects_the_cl_b12_apk`.
- **Tests** (`pin_tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK; `git
  diff --check` clean.
- **B's prepared G-A4 tools diff** (`b20_2026-10-24/ga4_tools.diff`): `git apply --check -p1` **OK on the pinned
  tree** (checked, not applied).
- **`--check` ok on nine, APK CONFIRMED** (`check_end.json`).
- **The APKs, nothing deleted (gitignored):**
  - `PrivyHub/app/build/cl_b12_installed/app-debug.apk` (`20e3e339…`, on the onn);
  - `PrivyHub/app/build/cl_b11_installed/app-debug.apk` (`e2db0aa0…`, the previous CONFIRMED one).

## 7. State at the end (~17:30Z)

- **The band 5 GHz** (5180 MHz, RSSI −69; `adb_reads/p2_wifi_stage3.json`).
- **The seven properties read back empty** (`adb_reads/p2_stage3_properties.txt`). None was ever set in this task.
- **The drop-in removed; nine lines;** no `e3_flag.conf`; `flags_absent` true in all three cells; `--check` ok, APK
  CONFIRMED.
- **The onn: `20e3e339…`, paired** (`client_end.json`).
- **Units:** the companion and `privyhub-link-n1`. Both CL-B12 units are closed and collected.
- No sudo, no nft. The Opal was untouched. **No `setprop`.** adb was used for the install, state reads and the two
  events reads.
- No address or identifier in any kept file (`redact_check.txt`). Nothing fetched or deleted. **Nothing adopted:
  G-A4 is the user's say-so, a later prompt.** Nothing committed. `logs/cl_b12_git_status.txt`.

## 8. Files (`cl_b12_2026-10-24/`, `manifest.sha256` over all of it)

- **PART 1:** the launch record's files (`CL_B12_LAUNCH_2026-10-24.md` §6); `cells.jsonl` (rows 2, 3, 1);
  `cl_b12_state.json`; `runs/2_…`, `runs/3_…` (each with `band.jsonl` and `e3_state_midcell_run1.json`).
- **PART 2:**
  - `adb_reads/p2_wifi_before_cell1.json`, `adb_reads/p2_properties_before_cell1.txt`, `p2_check_before_cell1.json`,
    `p2_client_before_cell1.json`, `p2_units_before_cell1.txt`;
  - `p2_cell1_launched_at.txt` / `_launch_console.txt`, `p2_cell1_playing_at.txt`, `cl_b12_p2_state.json`;
  - `runs/1_snes_5ghz_two_home_presses/`.
- **Stage 3:**
  - `adb_reads/p2_logcat_events_press1.txt` / `_press2.txt`, `cl_b12_events_read.py`;
  - `adb_reads/p2_stage3_properties.txt`, `adb_reads/p2_wifi_stage3.json`, `p2_check_stage3.json`;
  - `cl_b12_read.py`, `record_read.json`, `record_read_console.txt`;
  - the pin: `cl_b12_pin.diff`, `pin_predecessors/`, `pin_*_sha256.txt`, `pin_tests.txt`;
  - `check_end.json`, `client_end.json`, `units_end.txt`;
  - `redact_check.txt`.
