---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: efa4240 (G-A3 and CL-B10 PART 1 committed; this record and PART 2's files uncommitted beside it)
---

# CL-B10 — the state path and stall resume (cells 2, 3), the restart guard (cell 1), the notice (cell 4): MEASURED, 4 / 4 valid; `da09e154…` CONFIRMED

**Classification: MEASURED. All four cells were playing and valid, with the host gates met.**

By CL-B7 §6's rule, the candidate APK **`da09e154…6cf` stays and is CONFIRMED.** The pin moved, and `--check` is ok on
nine lines. Limits on that are in §6.

**The rows:**
- **Cell 2 (`@both`, state path):**
  - 5 of 5 blackouts gave a silence save at 0.40-0.41 s, a `state` load, and **net 24** by B9's row (B's number);
  - no second pause, no extra session;
  - **the resume came ≤ 1 heartbeat after the return in 4 of 5.** The fourth came 2.13 s after.
- **Cell 3 (`@down`, stall resume):**
  - 5 of 5 gave a stall save, the pause at 423-430 ms, a resume via `client_ready_stall` with the load, **net 9**,
    `stall_end_late`, and no second pause;
  - **but blackout 5 had one `encoder_restart`** (the row says none). The picture was held 5.3-7.2 s for a 4-s dark
    span.
- **Cell 1 (the restart guard): NOT MET.**
  - The Home press was found: a 5.3-s controller silence, then the client's own stream restart.
  - **No old report and no `session_ended` came before the new start.**
  - The new report's `restart_cause` is **null**.
  - The new session had **2,418 audio underruns in 28 s** (~85 / s, the storm B11 was built against).
- **Cell 4 (the notice):**
  - **The client raised it at once on 2.4 GHz:** `link_notice_shown` reason 1 `band_2_4_ghz` on the session's first
    heartbeat, and `link_notice=1` in all 275 heartbeats on 2412 MHz.
  - **"Shown" is NOT YET GATED.** The user's word on what was on screen is the gate, and the user's stage-3 message
    carried none (§4).
  - Cleared on the first heartbeat of the session the client started after the switch back.
- **The A/B LINK-R1 could not make, in the same hour, on the same game and onn:**

  | band | silences ≥ 250 ms / 10 min | hitch s / 10 min |
  | --- | --- | --- |
  | **2.4 GHz** | **168.1** | **149.2** |
  | **5 GHz** | **0.0** (cell 1's playing spans and cell 4 after the switch) | 0.0 / 9.3 |

  The user, on 2.4 GHz: "It's running like absolute shit right now". After the switch: "Switched to 5 with no issues and
  plays significantly better".

**The pre-registered reading:** cells 2 and 3 each missed one row in one blackout. So **the hold / state / stall stack
goes back to B with the rows.** It is not yet a candidate for the user's adoption call. Its costs as measured: 24 frames
per two-way drop, a save per stall plus saves at sub-second gate stalls, and the picture frozen 3.5-7.2 s per 4-s drop.
The guard goes back to B. The notice works as built, pending the user's word.

Nothing adopted. Nothing committed.

Tasks: `handoffs/G-A3_AND_CL-B10_TASK.md` PART 1 §2 and PART 2; `handoffs/CL-B10_PART2_ATTENDED_TASK.md` (three stages).
Launch: `CL_B10_LAUNCH_2026-10-23.md`. Files: `cl_b10_2026-10-23/`.

## 0. How it ran

- **PART 1 (detached):**
  - `privyhub-cl-b10` ran cells 2 and 3 from 18:42:13Z and closed "all 2 cells done" at 19:11:04Z;
  - pre-registration `49b7267e…2d06` (hashed before the install).
- **PART 2 (attended):**
  - `privyhub-cl-b10-p2` (`cl_b10_p2_driver.py`, one cell per launch) ran cell 1 at 03:32:35-03:46:53Z and cell 4 at
    03:51:04-04:09:38Z (2026-10-24);
  - pre-registration `2d883c91…0495`, hashed 03:32:34Z, before cell 1.
  - The driver is PART 1's, plus:
    - one cell per launch;
    - the cap at launch + 40 min;
    - the band read every 10 s (`runs/<cell>/band.jsonl`);
    - the watch rule: no cell that could still run at 04:30Z;
    - **the status text and log tag corrected** to `~/privyhub_cl_b10/STOP` / `cl_b10_p2`;
    - the properties read, not cleared.
    - The diff is `cl_b10_p2_driver_vs_cl_b10.diff`.
- **Every cell:**
  - E1-SNES-STREAM (snes9x), the nine adopted lines plus the cell's drop-in;
  - the drop-in read back at the stream and under load: 16 lines for cells 2 / 3, 10 for cells 1 / 4;
  - removed at the teardown; `flags_absent` true; nine lines after;
  - the properties `restart_guard` / `stall_signal` / `link_notice` = 1 before and after;
  - `link_report` = 1 (from LINK-R1).
- **The stage-3 reader:** `cl_b10_p2_read.py` (`p2_record_read.json`, `p2_record_read_console.txt`). B6's `measure`
  and UX-R3's `evening` / `counts` are exec'd unedited, asserted against LINK-R1's pins. It computes the named spans
  and the per-blackout rows from the recovery logs. The driver's rows are in `cells.jsonl`.
- **The instructions, disclosed.** Stage 1's reply gave the Home minute without saying what the user would see or do
  after. The user (verbatim, after the Home press): "These are terrible instructions. I went home and returned to game,
  it never paused from what I can see. Now what you're so unclear this is shit". Later replies said what to expect at
  each step.

## 1. Validity and the gates

| cell | band | drop-in | started | PLAYING (attempt) | window | environ stream / load | validity | RetroArch / capture / dup+drop | rendered | post-FEC loss / min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 5 GHz | `blackout-4s@both` + the six stack flags | 18:42:13Z | 18:44:35 (1) | 600 | 16 / 16 | valid | 59.999 / 59.996 / 0.1 | 57.93 | 1,620 (the blackouts) |
| 3 | 5 GHz | `blackout-4s@down` + the same | 18:56:39Z | 18:59:02 (1) | 600 | 16 / 16 | valid | 59.999 / 59.997 / 0.1 | 57.87 | 1,610 (the blackouts) |
| 1 | 5 GHz | `none@post-fec,seed=1` | 03:32:35Z | 03:35:04 (1) | 600 | 10 / 10 | valid | 59.999 / 60.006 / 0.0 | 59.50 | 11.6 |
| 4 | 2.4 → 5 GHz | `none@post-fec,seed=1` | 03:51:04Z | 03:54:46 (2) | 780 | 10 / 10 | valid | 59.999 / 59.997 / 0.077 | 59.515 | 96.26 |

- **The shim's dark spans:** 5 in cell 2 (`uplink_dropped` 9,120), 5 in cell 3 (uplink 0, as `@down`).
- **Cells 1 and 4 are not invalidated by the Home press or the band switch,** nor by the client sessions those caused
  (pre-registered).
- **Cell 4's suite reached PLAYING on its second launch attempt**, as BENCH-R3's A did. The client's first stream (from
  03:53:26Z) carried the first heartbeats and the notice row.

## 2. Cell 2 — the state path under `blackout-4s@both`, per blackout

| pause at (UTC) | the save (kind, after onset) | pause age ms | release | net (B9's row) | frames restored | via | packets back → resume ms | held ms | 2nd pause / extra session |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18:46:15.846 | silence, 400.8 | 954 | `state`, `LOAD_STATE_SLOT 9` | **24** | 34 | `hold_return_stall` | 1,318 | 4,422 | none |
| 18:48:15.862 | silence, 405.2 | 953 | `state` | **24** | 34 | `hold_return_stall` | 427 | 3,528 | none |
| 18:50:15.865 | silence, 400.8 | 950 | `state` | **24** | 35 | `hold_return_stall` | 1,286 | 4,382 | none |
| 18:52:15.866 | silence, 406.8 | 951 | `state` | **24** | 35 | `hold_return_stall` | **2,130** | 5,235 | none |
| 18:54:15.869 | silence, 405.6 | 958 | `state` | **24** | 35 | `hold_return_stall` | 976 | 4,084 | none |

**The rows:**

| row | result |
| --- | --- |
| `state_saved` kind silence ~0.40 s in | **met 5 / 5** (400.8-406.8 ms) |
| `input_release` method `state` at the resume, playing after | **met 5 / 5** (`stall_gate_after_return` 3-46 ms after; `client_ready_after_hold`; `stall_end_late`) |
| net ≈ 24 | **met 5 / 5** by B9's row |
| the resume ≤ 1 heartbeat after the return | **4 / 5**: the heartbeat comes every ~2.0 s, and blackout 4's 2,130 ms is just over |
| no second `desync_pause`, no `session_started` | **met** (5 pauses, 1 session) |

- **`--net`:** `unattended_frames.py --net` read 239.1 core-running frames, ~47.8 per blackout, the same as plain. As in
  BENCH-R3, the reader credits only releases carrying `rewound_frames`, not `state` releases. So B9's row (24) is the
  net, and the reader's 47.8 is the gross before the restore (34-35 restored).
- **Also:**
  - **4 extra `state_saved` kind stall** at 150-163 ms gate stalls, outside the blackouts (18:44:57, 18:46:05 and two
    at the session's end 18:56:07). That is a save per sub-second stall, stated as a cost.
  - Silences ≥ 250 ms: 4.44 / 10 min, all 5 the blackouts.

## 3. Cell 3 — the stall resume under `blackout-4s@down`, per blackout

| pause at (UTC) | the save (kind, after onset) | the pause after the client's last frame | handover v2 held ms | release | net | via | recovering ms | encoder restart | 2nd pause |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19:00:57.042 | stall, 150.5 | **430 ms** | 5,006 | `state` | **9** | `client_ready_stall` | 6,399 | 0 | none |
| 19:02:57.045 | stall, 155.1 | **426** | 5,062 | `state` | **9** | `client_ready_stall` | 6,404 | 0 | none |
| 19:04:57.048 | stall, 156.2 | **429** | 5,098 | `state` | **9** | `client_ready_stall` | 5,342 | 0 | none |
| 19:06:57.049 | stall, 154.1 | **426** | 5,159 | `state` | **9** | `client_ready_stall` | 5,782 | 0 | none |
| 19:08:57.051 | stall, 150.5 | **423** | 5,225 | `state` | **9** | `client_ready_stall` | 7,207 | **1** (19:09:03.267, last output 3,980 ms) | none |

**The rows:**

| row | result |
| --- | --- |
| `state_saved` kind stall | **met 5 / 5** |
| the pause 400-460 ms after the client's last frame | **met 5 / 5** (423-430) |
| no `encoder_restart` | **NOT MET: 1 in blackout 5** (v2's handover at 5.2 s, then one restart before the client's ready at 19:09:04.1) |
| no `recovery_escalation` | **met** (0) |
| one `resumed via client_ready_stall` with the load | **met 5 / 5** |
| net ≈ 9-12 | **met** (9 in all 5) |
| `client_ready_after_stall`, `stall_end_late` | **met 5 / 5** |
| no second pause | **met** |

- **The cost seen:** each 4-s dark span held the picture **5.3-7.2 s**. B12 holds v2's restart until the pause is 5 s
  old, and the client's ready came after that each time.
- 0 uplink silences (as `@down`).

## 4. Cell 1 — the restart guard (5 GHz) and cell 4 — the notice (2.4 GHz → 5 GHz)

### Cell 1: the Home press, as the logs carry it

| UTC | row |
| --- | --- |
| 03:35:03.259 | `session_started` (PLAYING 03:35:04) |
| ~03:38:37.6 | the controller goes silent: the Home press (the pause's age 5,263 ms at 03:38:42.912) |
| 03:38:42.912 | `desync_pause` trigger `controller_silence` |
| 03:38:43.687 | `client_stream_restart` (the client's own restart on return) |
| 03:38:46.463 | `resumed` via `controller_return` (recovering 3,543 ms, packets back → resume 2,251 ms) |
| 03:38:50.765 | `session_started` (the new client session), **with no `session_ended` before it** |
| 03:39:12.155 | `session_ended`: the user's back-out ("I continued to play the I paused by backing out") |
| 03:41:48.983 → 03:42:21.100 | a further session, the user's re-entry (36 s, 11 underruns), then `session_ended` |

**The client's reports** (`logs/games/decoder_sessions/`):
- **No report for the first session** (03:35:03 to the Home press).
- The 03:39:12.129Z report is the new session's: 28.4 s, **`restart_cause` null**, **audio underruns 2,418**.
- The 03:42:21Z report: 36 s, underruns 11.

**B11's rows:**

| row | result |
| --- | --- |
| the Home press found | **met** (the 5.3-s silence, the client's own restart) |
| the old report + `session_ended` before the new start | **NOT MET** (no old report; the only `session_ended` came at the back-out) |
| `restart_cause.away_ms` ≈ 5,000 | **NOT MET** (`restart_cause` absent) |
| the new session's underruns ≈ the others' (not ~170 / s) | **NOT MET**: ~85 / s (2,418 in 28 s; the re-entry session 11 in 36 s) |
| `link_notice=0` throughout, no row | **met** (131 heartbeats, all 0) |

- **What the logs cannot say:** why the guard's path did not run. `restart_guard` read `1` before and after the cell,
  and the APK was `da09e154…`. Back to B with these rows.
- **On screen, the return looked seamless:** the client restarted within ~6 s. The user's line: "I went home and
  returned to game, it never paused from what I can see".
- **Silences and hitches on 5 GHz:** 0 / 0 over the playing spans (195 + 1 + 12 streaming s by B6's edge rule).
  LINK-R1 read 0 / 0; G-A3 read 0 / 0.9.

### Cell 4: the notice and the band

**The band per 10 s** (`runs/4_snes_24ghz_notice/band.jsonl`, 106 reads):
- **2412 MHz, 802.11n, from 03:51:04Z** (RSSI −67…−69; tx 6-162).
- **5180 MHz from 04:04:45Z** (RSSI −70 at the first read).
- 77 reads at 2.4 GHz, 29 at 5 GHz.

**The rows:**
- **`link_notice_shown`** 03:53:26.888Z, heartbeat_sequence 1, `reasons` 1, `reason_names` `["band_2_4_ghz"]`, at
  2412 MHz / −67 dBm / tx 6.
  - This is the client's first heartbeat. The host's state read `ENDED` there because the suite's first launch attempt
    was still settling. PLAYING came at 03:54:46.
  - `link_notice=1` was in all 294 heartbeats at 2412 MHz.
- **The switch-back** (the user's hand, 00:04 Eastern as asked):
  - the controller went silent ~04:04:29.9Z; `desync_pause` `controller_silence` 04:04:35.1;
  - the band read 5 GHz 04:04:45.5; `client_stream_restart` 04:04:54.4;
  - **`link_notice_cleared` 04:04:54.8Z** (heartbeat_sequence 1 of the new client session, `previous_reasons` 1);
  - `resumed` via `controller_return` 04:04:59.5 (recovering 24,333 ms); `session_started` 04:05:01.2;
  - `session_ended` 04:09:18.0 (the window's end).
- **The clear came 9.3 s after the first 5-GHz band read.** It arrived with the new session's first heartbeat, not
  after B14's "30 s good". That path was not exercised, because the switch restarted the client's stream.
- The 03:53-04:09 client report: 263 s, underruns 351.

**"Shown", the user's word as the gate:**
- The user's stage-3 message read, in full: "Stage 3". **It carried no word on the notice.**
- So **"shown" is NOT YET GATED.** The row and the heartbeats say the client raised it; whether it was on screen
  bottom-left, and with which words, is the user's to say. It can be added to this record as one line.
- **The user's word (2026-10-24, verbatim): "I saw that box".** The gate is **MET**: B14's notice was on screen on 2.4 GHz.

### The same-hour A/B (`p2_record_read.json`)

| span | streaming s | silences ≥ 250 ms | per 10 min | max ms | hitch s | per 10 min | longest | heartbeats: freq / notice |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cell 1, 5 GHz, before Home (03:35:03-03:38:37) | 195 | 0 | **0.0** | — | 0 | **0.0** | 0 | 5180 ×105 / 0 |
| cell 1, after the return (03:38:50-03:39:12) | 1 | 0 | 0.0 | — | 0 | 0.0 | 0 | 5180 ×10 / 0 |
| cell 1, the re-entry (03:41:48-03:42:21) | 12 | 0 | 0.0 | — | 0 | 0.0 | 0 | 5180 ×16 / 0 |
| **cell 4, 2.4 GHz (03:54:46-04:04:29)** | 564 | **158** | **168.1** | 2,511 | **145** | **149.2** | 6 | 2412 ×275 / 1 |
| **cell 4, 5 GHz after the switch (04:05:01-04:09:18)** | 237 | 0 | **0.0** | — | 4 | **9.3** | 1 | 5180 ×126 / 0 |

- **On 2.4 GHz** the silences ran **168 per 10 min**. That is ~7.5× BENCH-R3 C's 22.4, which was 2.4 GHz on an earlier
  day. Hitch seconds ran 149 per 10 min, against 0-9 on 5 GHz minutes apart.
- **The user's words, verbatim:**
  - stage 2, during 2.4 GHz: "It's running like absolute shit right now";
  - after the switch: "Switched to 5 with no issues and plays significantly better".

## 5. The reading, as pre-registered

- **Cells 2 and 3:** each met every row but one, in one blackout:
  - cell 2's resume was 2.13 s after the return in blackout 4 (≤ 1 heartbeat ≈ 2.0 s);
  - cell 3 had one `encoder_restart` in blackout 5.
  - **Not "both meet their rows," so the stack goes back to B with these rows. It is not yet a candidate.**
  - **The costs measured,** for B and the user's later call:
    - 24 frames per two-way drop, restored to the save at 0.40 s;
    - a save per stall, including 150-ms gate stalls (4 extra in cell 2);
    - the picture frozen 3.5-5.2 s (`@both`) and 5.3-7.2 s (`@down`) per 4-s drop.
- **The guard (cell 1): back to B.** No old report, no `session_ended` before the new start, no `restart_cause`, and
  the underrun storm (~85 / s) after the self-restart.
- **The notice (cell 4):** the client raised it on 2.4 GHz at the first heartbeat (reason 1) and cleared it on 5 GHz.
  **"Shown" awaits the user's word.** The 30-s clear path is not exercised.
- **The band, settled in the same hour:** on 5 GHz there were 0 silences in every span. On 2.4 GHz there were 168 per
  10 min and 149 hitch s per 10 min, and the user's words match.

## 6. The CONFIRMED rule (CL-B7 §6)

- **All four cells (2, 3, 1, 4) were valid** (§1). The flag-absent host behaviour read as today in cells 1 and 4,
  which carried only the `none` impairment line.
- **Not exercised, disclosed:** no cell ran with the client properties empty. So the property-empty client behaviour
  and B13's one intended difference (the link keys present with `link_report` empty) were not run on the onn here.
  - They rest on B's proofs: client added-lines only for B11 / B14, and B13's two stated lines. That is the same
    by-construction ground CL-B7 §6 cites from CL-B7P §2.
  - The user's next play with the properties empty is the first live read, and the heartbeats will show whether the
    link keys arrive.
- **The rule as written gives CONFIRMED:** `da09e154…6cf` stays on the onn.
- **The pin moved where CL-B7 §6 moves it** (`cl_b10_pin.diff`, `pin_predecessors/`, `pin_predecessor_sha256.txt`,
  `pin_after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK`;
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`;
  - its test (`test_the_preflight_expects_the_cl_b10_apk`).
- **Tests** (`pin_tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK.
  `git diff --check` was clean.
- **`--check` ok on nine, APK CONFIRMED** (`check_end.json`, 04:10:14Z).
- **The APKs, nothing deleted (gitignored):**
  - `PrivyHub/app/build/cl_b10_installed/app-debug.apk` (`da09e154…`);
  - `PrivyHub/app/build/cl_b10_preserved/app-debug.apk` (`bf5114a2…`, the previous CONFIRMED one).

## 7. State at the end (04:10Z, before the nightly watch's 04:30Z)

- **The band read 5 GHz** (5180 MHz, 802.11ac, RSSI −68, tx 292 / rx 117).
- **The properties cleared and read back empty** (`adb_reads/p2_stage3_properties.txt`): `restart_guard`,
  `stall_signal`, `link_notice`, and **`link_report` too**. `wifi_lock`, `loss_guard` and `opus_decode` were empty.
  - With `da09e154…`, `link_report` empty means the client sends the link keys by default.
- **Nine lines,** no `e3_flag.conf`, `flags_absent` true, `--check` ok, APK CONFIRMED.
- **The onn: `da09e154…`, paired** (`client_end.json`: identity v2, the device secret, the id in the hub's store, 1
  device). Session status: 1 paired, 0 active.
- **Units:** the companion and `privyhub-link-n1`. Both CL-B10 units are closed and collected. No adb after 04:10:22Z,
  so none ran in the watch's hour.
- No sudo, no nft. The Opal was untouched; both band switches were the user's hand. adb was used for the install
  (PART 1), the named `setprop`s and state reads only.
- No address or identifier in any kept file (`redact_check.txt`). Nothing fetched or deleted. Nothing adopted.
  Nothing committed. `logs/cl_b10_git_status.txt`.

## 8. Files (`cl_b10_2026-10-23/`, `manifest.sha256` over all of it)

- **PART 1:** the launch record's files; `cells.jsonl` (rows 2, 3, 1, 4); `cl_b10_state.json`; `runs/2_…`, `runs/3_…`.
- **PART 2:**
  - `cl_b10_p2_preregistration.txt` / `.sha256`, `p2_preregistration_hashed_at.txt`,
    `p2_tools_at_preregistration_sha256.txt`;
  - `cl_b10_p2_driver.py`, `cl_b10_p2_suite_call.py`, `cl_b10_p2_driver_vs_cl_b10.diff`;
  - `p2_check_before_cell1.json` / `_cell4.json`, `p2_units_before_cell1.txt`, `p2_cell{1,4}_launched_at.txt` /
    `_launch_console.txt`, `cl_b10_p2_state.json`;
  - `runs/1_snes_5ghz_restart_guard/`, `runs/4_snes_24ghz_notice/` (each with `band.jsonl`).
- **Stage 3:**
  - `adb_reads/p2_stage3_properties.txt`, `p2_check_stage3.json`;
  - `cl_b10_p2_read.py`, `p2_record_read.json`, `p2_record_read_console.txt`;
  - the pin: `cl_b10_pin.diff`, `pin_predecessors/`, `pin_*_sha256.txt`, `pin_tests.txt`;
  - `check_end.json`, `client_end.json`, `session_status_end.json`;
  - `redact_check.txt`.
