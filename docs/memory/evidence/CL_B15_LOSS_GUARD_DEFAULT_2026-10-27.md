---
memory_schema: 1
as_of: 2026-10-28
baseline_commit: 4a78783 (queue J committed; this record, its dir, the launch record and the pin uncommitted beside it)
---

# CL-B15 — the loss guard on by default, on the bench: MEASURED, 2 / 2 cells valid; L1-L3 NOT MET (one 685-ms hold timed out); `8b0fbb74…` CONFIRMED

**Classification: MEASURED. Cells L and C were playing and valid,** on 5 GHz, with every client property EMPTY (no
`setprop` was run). By CL-B7 §6's rule, B27's APK **`8b0fbb74…3f4e` is CONFIRMED** and the pin moved; `e3_state` is ok
on twelve.

**The rows, in short:**
- **Cell L (1 % loss + `PRIVYHUB_LOSS_GUARD=1`):**
  - the guard on with no property (`loss_guard_mode` `guard`), and the host side as built (`NoRuntimeIdr`, 12
    `keyframe_requests` rows, `forced` 0, received 319 of 320 sent);
  - **NOT MET:** one hold ran **685 ms**, past the 600-ms cap. It **timed out** (`loss_guard_timeouts` 1), and **7
    corrupted frames were shown** (held 2,478 of 2,485). Every other minute held every frame;
  - **9 holds ran long enough (406-433 ms) to trip the adopted stall stack.** The client's stall signal fired, and the
    host paused, saved and resumed 2-3 frames back (`client_stall` → `stall_end`). BENCH-R3 E ran without the stack,
    so this interaction is new.
- **Cell C (clean, no flag):** the guard on by default held 295 = 295 frames in 38 short freezes (max 268 ms), 0
  timeouts. There was no host guard row, no save, no hold and no stall pause. One 258-ms silence; hitch 3.5 s / 10 min.
- **The cost, plain:**
  - **with 1 % loss:** about **28 freezes a minute, ~0.13 s each** on average (7.7 frames), the longest 0.69 s; about
    one a minute long enough to trip a stall pause;
  - **on this clean LAN:** about **3 freezes a minute, ~0.13 s each**, the longest 0.27 s.
- **Not read:** the host controller's `bad_packets` (the L5 clause and C2). The driver did not sample the controller
  status, and each teardown's restart reset it (§4).

**The reading, as pre-registered:** L1-L3 not met → **back to B with the rows.** G-A8 is not a candidate as read; the
question stands in B's words (§6). Nothing adopted. Nothing committed.

**B26** (the relay-stop fix inside the adopted `PRIVYHUB_RESTART_FAST_UNLOCK=1`) **is live** from this task's first
companion restart (the dry run's, 2026-10-28T01:30:37Z). Disclosed; not a row (no Home press here).

Task: `handoffs/CL-B15_LOSS_GUARD_DEFAULT_TASK.md`, session A. B's strings: `SESSION_B_DONE_2026-10-27J.md` items 3-6;
B27, B26, B10; BENCH-R3 §1 / §5. Launch: `CL_B15_LAUNCH_2026-10-27.md`. Files: `cl_b15_2026-10-27/`.

## 0. How it ran

- **The pre-registration** `cl_b15_preregistration.txt` (`f38f2e18…75a6`) was hashed at 01:30:15Z, before the install
  (the launch record §2).
- **The unit** `privyhub-cl-b15`, 01:32:26-02:01:09Z, "all 2 cells done":
  - **cell L** 01:32:27-01:46:51Z, PLAYING 01:34:58Z (attempt 1, 10.1 s), the session 01:34:57.8-01:46:30.7Z (11.55 min);
  - **cell C** 01:46:52-02:01:08Z, PLAYING attempt 1 (4.1 s), the session 01:49:14.5-02:00:47.8Z (11.56 min).
- **Every cell:**
  - E1-PS1-STREAM (Beetle PSX HW), window 600, gap 120;
  - the drop-in read back at the stream and under load (14 / 13) and removed at the teardown; `flags_absent` true;
    twelve lines after;
  - the seven properties empty before and after; 5180 MHz in 85 / 85 band reads per cell; the client's class lan.
- **The reader** `cl_b15_read.py` (`record_read.json`, `record_read_console.txt`):
  - CL-B14's reader's first 160 lines unedited (B6's `measure`, UX-R3's `evening` / `counts`, pin-asserted; `span()`);
  - plus `cell_read()`: the report's guard keys and AU drops; the heartbeats' guard counters per UTC minute; the host's
    `keyframe_requests` rows per minute; the recovery log's rows.
- **Disclosed:**
  - the precondition read `active_sessions` 1 with no game;
  - BENCH-R3 E-on's silences read 54.5 / 10 min in its record and 55.2 in B's note. Both are quoted;
  - the redactor's two hits are the PS1 core's four-part version in each cell's RetroArch window title (`title.txt`),
    not an address.

## 1. Validity and the gates

| cell | drop-in | PLAYING | environ at stream / under load | the shim (applied) | validity | RetroArch / capture / dup+drop | rendered (report) | post-FEC loss / min (window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L | `loss-1` + `LOSS_GUARD` | 01:34:58 (1) | 14 / 14 | `loss-1`: 0.99 % (6,664 of 672,744); no other drop | **valid** | 59.999 / 60.047 / 0.1 | 55.75 | 63.7 |
| C | `none` | 01:49:14 (1) | 13 / 13 | `none`: 0 drops | **valid** | 59.999 / 60.047 / 0.1 | 59.43 | 14.2 |

## 2. Cell L — the guard with the host flag (B item 5)

| row | read | BENCH-R3 E-on (2.4 GHz, `loss_guard=1` by property) | |
| --- | --- | --- | --- |
| **L0** the default is on | `loss_guard_mode` `guard`, no property set | (property) | **met** |
| **L1** every corrupted frame held | report: held **2,478** / counter **2,485**; heartbeats: equal in every minute but **01:41** (238 / 231; the 2-s interval ending 01:41:43.9: +34 / +27) | 3,010 / 3,010 | **NOT MET** (7 frames shown) |
| **L2** timeouts 0 | **1** | 0 | **NOT MET** |
| **L3** max wait ≤ 600 ms (0.5 s expected) | **685 ms** | 501 | **NOT MET** |
| **L4** the counter per minute; AU drops | 165-272 per full minute (below); video `dropped_frames` 404, `sequence_gap_au_drops` 379, `incomplete_au_drops` 27, `non_idr_aus_dropped_waiting_for_idr` 11; decoder `dropped_frames` 7 | 151-357; 464 / 448 / 26; 0 | stated |
| **L5** the host side | `loss_guard_config` `ignored` false, `NoRuntimeIdr`, 500 ms; 12 `keyframe_requests` rows, **`forced` 0** throughout, the reason "no runtime IDR path …"; final **received 319 ≤ sent 320** (acted 278, rate-limited 41); **the controller's `bad_packets` NOT READ** (§4) | received 376 of 394, forced 0 | **met on what was read** |
| **L6** the cost | hitch **37.2 s / 10 min** (longest run 2 s); silences ≥ 250 ms **0**; rendered **55.75 fps**; max output gap **659 ms** | 125.7 / 54.5 (55.2) / 55.19 / 597 | stated |

**Per minute (heartbeat deltas, UTC; the host's `keyframe_requests` deltas for the minute ending at the row):**

| minute | counter | held | unheld | episodes (freezes) | post-FEC lost | rendered | kf received / acted / rate-limited / forced |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01:35 | 215 | 215 | 0 | 32 | 67 | 3,389 | 27 / 25 / 2 / 0 |
| 01:36 | 256 | 256 | 0 | 34 | 95 | 3,337 | 34 / 31 / 3 / 0 |
| 01:37 | 253 | 253 | 0 | 39 | 90 | 3,229 | 40 / 31 / 9 / 0 |
| 01:38 | 208 | 208 | 0 | 28 | 68 | 3,407 | 26 / 24 / 2 / 0 |
| 01:39 | 165 | 165 | 0 | 16 | 34 | 3,348 | 22 / 18 / 4 / 0 |
| 01:40 | 272 | 272 | 0 | 30 | 84 | 3,216 | 28 / 23 / 5 / 0 |
| **01:41** | **238** | **231** | **7** | 29 | 76 | 3,375 | 24 / 24 / 0 / 0 |
| 01:42 | 220 | 220 | 0 | 26 | 53 | 3,395 | 30 / 27 / 3 / 0 |
| 01:43 | 170 | 170 | 0 | 21 | 71 | 3,445 | 22 / 20 / 2 / 0 |
| 01:44 | 185 | 185 | 0 | 21 | 41 | 3,295 | 24 / 17 / 7 / 0 |
| 01:45 | 188 | 188 | 0 | 23 | 70 | 3,430 | 17 / 15 / 2 / 0 |
| (01:34, 01:46 partial) | 5; 65 | 5; 65 | 0; 0 | 1; 12 | | | 25 / 23 / 2 / 0 (01:46:34) |

- The heartbeats carry `frames_after_dropped_reference`, `loss_guard_frames_held` and `loss_guard_episodes` only.
  `loss_guard_timeouts` and `loss_guard_max_wait_ms` are in the report alone, so the 685-ms hold is placed by its
  unheld frames: the interval ending 01:41:43.9Z.
- **The guard and the stall stack (new; not a pre-registered row).** Under the twelve lines, the adopted stall signal
  fires when the picture is ~400 ms old. **Nine guard holds crossed it:**
  - 01:37:02, 01:40:17, 01:40:18, 01:40:51, 01:41:33, **01:41:42**, 01:42:38, 01:43:15, 01:45:55Z;
  - each: `state_saved` `stall` at 406-433 ms → `client_stall` → `desync_pause` → `input_release` `stall_end`
    (2-3 frames restored) → `resumed` 49-184 ms after the pause (149-284 ms after the save);
  - 01:41:42 is the timed-out hold's interval.
  - BENCH-R3 E ran with the hold / stall flags absent, so it never showed this. Cell C had none.

**The cost, plain (from the report, 11.55 min):**
- **320 freezes, 27.7 a minute** (16-39 per full minute), one every ~2 s.
- **2,478 frames held, 7.7 per freeze ≈ 0.13 s** on average; the longest **0.69 s** (it timed out and showed 7
  corrupted frames).
- **9 freezes (~0.8 a minute) ran past 0.4 s** and drew a stall pause and a 2-3-frame rewind on the host.
- What it buys: no frame drawn from a lost reference but those 7. In BENCH-R3 E-off, the counter (frames that would
  have shown corruption) ran 308-718 per minute.

## 3. Cell C — clean, no flag (the absent-key path)

| row | read | G-A7's window (SNES, the same twelve lines) | |
| --- | --- | --- | --- |
| **C1** the absent-key path | `loss_guard_mode` `guard`; held **295 = 295**; timeouts **0**; max wait 268 ms; 38 episodes, `keyframe_requests_sent` 38; **no `loss_guard_config`, no `keyframe_requests` row** | — | **met** |
| **C2** the requests without the host flag | **NOT READ:** the controller's `bad_packets` was not sampled (§4) | — | not read |
| **C3** today's behaviours | silences ≥ 250 ms **0.89 / 10 min** (one, 258 ms); hitch **3.5 s / 10 min** (longest run 1 s); `link_notice` 0 in 341 / 341 heartbeats; 0 `state_saved`, 0 holds, 0 stall rows; the teardown `session_end_bye` → `state_save_skipped` `client_bye` (401.0 ms) → `session_ended` | 0.0 / 2.6; `link_notice` 0; 0 / 0; the bye → `client_bye` | **met but for the one 258-ms silence** (G-A5's window read the same 0.89) |

- **The guard on the clean LAN** (the house's own loss: 157 packets lost after FEC in 11.6 min): **38 freezes, 3.3 a
  minute, 7.8 frames ≈ 0.13 s each, the longest 0.27 s.** Rendered 59.43 fps; max output gap 351 ms. With no host flag
  the heartbeats carry no guard fields (B27: the host records them only with the flag), so C has no per-minute table.

## 4. Not read: the controller's `bad_packets`

- L5's clause ("the controller's `bad_packets` not rising with the requests") and C2 need the host controller's
  `bad_packets` (`native_session_io`'s controller status).
- The driver (CL-B14's) kept the stream poll's video fields only. The suite's `status_poll.jsonl` and `telemetry.jsonl`
  do not carry it; no log, journal or report does. Each cell's teardown restart reset the counter.
- **So neither row is read.** B27's design says each `PHK1` without the flag is one `bad_packets`. That is untested
  here. For a re-read: sample the controller status per minute in the driver.

## 5. The CONFIRMED rule (CL-B7 §6)

- **At the close (02:18:59Z, `check_end_before_rule.json`):** the properties empty; the drop-in removed; twelve lines;
  no `e3_flag.conf`; `flags_absent` true in both cells; the client on the LAN; 5180 MHz (`adb_reads/*part2*`);
  `8b0fbb74…` paired (`client_end.json`); the two units only (`units_end.txt`).
- **Both cells valid** (§1). **The behaviours as today where no flag was set** (cell C): no notice, no host guard row,
  no save, hold or stall, and the same teardown. **The guard's intended difference:** on with no property, holding
  295 frames there. Cell L's misses are rows, which the pre-registration says do not block it.
- **The rule gives CONFIRMED:** `8b0fbb74…3f4e` stays on the onn.
- **The pin moved** (`cl_b15_pin.diff`, `pin_predecessors/`, `pin_predecessor_sha256.txt`, `pin_after_sha256.txt`):
  `tools/e1_suite.py` `EXPECT_APK`; `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`; its test, now
  `test_the_preflight_expects_the_cl_b15_apk`.
- **Tests** (`pin_tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK; `git
  diff --check` clean.
- **`e3_state --check` ok on twelve, APK CONFIRMED** (`check_end.json`).
- **The APKs, nothing deleted (gitignored):** `PrivyHub/app/build/cl_b15_installed/app-debug.apk` (`8b0fbb74…`, on the
  onn); `PrivyHub/app/build/cl_b14_installed/app-debug.apk` (`fcd924c2…`, the previous CONFIRMED one).
- **The guard is now on by default on the onn.** Off: `adb shell setprop debug.privyhub.loss_guard 0` (B10's absent),
  or `fcd924c2…` back from `cl_b14_installed/`. `count` counts without holding.

## 6. The reading, as pre-registered

- **L1-L3 not met → back to B with the rows:**
  - one hold ran 685 ms past the 600-ms cap, timed out and showed 7 frames;
  - **for B:** why the cap fired 85 ms late; and the guard's holds ≥ ~0.4 s now trip the adopted stall stack (9 in
    11.5 min at 1 % loss). Should the guard's hold and the stall signal know of each other?
  - L5 was met on what was read; its `bad_packets` clause and C2 were not read.
- **G-A8, the user's question in B's words, not a candidate as read:** "Adopt `PRIVYHUB_LOSS_GUARD=1` as the
  thirteenth line? It forces nothing. It lets the host count the onn's keyframe requests and log the loss guard's
  numbers. The guard itself is already on in the onn's app."
  - The guard's own off switch: `setprop debug.privyhub.loss_guard 0`, or the previous APK.
  - B's prepared patch `patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md` was NOT applied.
- **Next B item after these rows:** the remote umbrella (queue K).

## 7. State at the end (~02:25Z)

- **TWELVE lines; `--check` ok; APK `8b0fbb74…3f4e` CONFIRMED** on the onn, paired, on the LAN, 5180 MHz; the seven
  properties empty. No `e3_flag.conf`, no game. Units: the companion and `privyhub-link-n1`. Every CL-B15 unit closed and
  collected.
- No sudo, no nft. The Opal was untouched. **No `setprop`.** adb was used for the install and state reads.
- No address or identifier in any kept file (`redact_check.txt`; its two HITs, one per cell's `title.txt`, are the core version, noted). Nothing fetched. Nothing deleted.
  Nothing adopted. Nothing committed. `logs/cl_b15_git_status.txt`.
- **The user's messages, verbatim** (`user_lines.txt`):
  1. "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
  2. "Code is done"

## 8. Files (`cl_b15_2026-10-27/`, `manifest.sha256` over all of it)

- **The start, the install, the launch:** see the launch record §2.
- **The cells:** `cells.jsonl`, `cl_b15_state.json`, `cell_L_playing_at.txt`, `cell_L_config_rows.jsonl`, `runs/` (each
  with `band.jsonl`, `logs_run1/`, the journal, the mid-cell e3 read).
- **Part 2:** `cl_b15_read.py`, `record_read.json`, `record_read_console.txt`; the pin (`cl_b15_pin.diff`,
  `pin_predecessors/`, `pin_*_sha256.txt`, `pin_tests.txt`); `check_end_before_rule.json`, `check_end.json`,
  `client_end.json`, `units_end.txt`, `adb_reads/*part2*`; `user_lines.txt`, `redact_check.py`, `redact_check.txt`.
