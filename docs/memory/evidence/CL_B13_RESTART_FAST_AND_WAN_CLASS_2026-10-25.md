---
memory_schema: 1
as_of: 2026-10-25
baseline_commit: 7a1e0de (queue H committed; this record, its dir and the pin uncommitted beside it)
---

# CL-B13 — the fast restart at Home, the same without it, the remote class on the bench: MEASURED, 4 / 4 cells valid; `6bddafc0…` CONFIRMED

**Classification: MEASURED. Cells 1, 2, 3a and 3b were playing and valid.** Every client property was EMPTY
throughout, and no `setprop` was run. By CL-B7 §6's rule, B's APK **`6bddafc0…a927` is CONFIRMED** and the pin moved;
`e3_state` is ok on ten.

**The rows, in short:**
- **Cell 1, `PRIVYHUB_RESTART_FAST=1`, four Home returns.**
  - Met:
    - the host answered every guarded start in **6.6-8.6 ms**, 11-13 ms after `session_ended`;
    - the release was `fast` every time;
    - the first interval after each new start had 0-1 underruns;
    - no `restart_fast_failed`.
  - **The picture was back 1.74-2.00 s after the new activity at returns 2-4,** against 7.52 / 6.73 s without the flag
    (cell 2) and CL-B12's 12.0 / 6.8.
  - **Not met, three rows:**
    - **return 1's picture back 3.12 s** (≤ 3.0). The old audio's stop took 2.21 s in the worker, and the ready
      waits on the lock;
    - **returns 3 and 4: the old encoder's last frame at entry + 0.35 / + 0.39 s** (≤ 0.3);
    - the capture gate in this run (59.899 against 60 ± 0.1). That is the Home restarts' own sample pairs (§1), and it
      does not invalidate the cell.
- **Cell 2, no flag: every row met.** No `restart_fast*` row or key. CL-B12's order, `create_to_start_ms` 274 / 81, the
  picture back 7.52 / 6.73 s.
- **Cell 3a, `@both` on the overlay (direct), `PRIVYHUB_LINK_RECOVERY_WAN=1`.**
  - Met: the class rows (`remote-unknown` `pending` → `remote-direct` 450 / 200 in 271 ms), and the first two
    blackouts held at age 453-458 ms after a ~404-ms save.
  - **Not met:** **one false hold at 23:18:07Z** (age 451 ms, no drop). **The guard tripped** as designed (the
    `WHY_GUARD` row; the session back to 950 / 400). There was also one false **stall pause** at 207 ms (23:13:12Z).
- **Cell 3b, `@down` on the overlay: every row met.**
  - Each stall pause came at 208-214 ms after the client's last frame, with the stall save 103-105 ms before it.
  - Resumed via `client_ready_stall` 41-212 ms after the return; 0 `encoder_restart`, 0 `stall_handover_v2`.
  - 0 pauses outside the blackouts; no `WHY_GUARD`.

**The reading, as pre-registered:**
- **G-A5 (`PRIVYHUB_RESTART_FAST=1`): not every row of cell 1 met → back to B with the three rows.** The behaviour it
  targets is there: 1.7-2.0 s at three of four returns, against 6.7-7.5 without it.
- **G-A6 (`PRIVYHUB_LINK_RECOVERY_WAN=1`): 3a's false hold → back to B.** The guard did its job (one false hold, then
  950). But the onn on the home Wi-Fi through the overlay is the LAN's radio path under a direct label, and B23's
  replay already showed that the LAN holds falsely at 450.

**The user's lines, verbatim:** "It returned fine" (cell 1); "Stage 3. Returned fine" (cell 2). All the messages are in
§7.

Nothing adopted. Nothing committed.

Task: `handoffs/CL-B13_RESTART_FAST_AND_WAN_CLASS_TASK.md` (stages 1-4), session A. B's strings:
`SESSION_B_DONE_2026-10-24H.md` items 4-10; B21-B23. Launch: `CL_B13_LAUNCH_2026-10-25.md`. Files:
`cl_b13_2026-10-25/`.

## 0. How it ran

- **The pre-registration** `cl_b13_preregistration.txt` (`19536f2b…5e19`) was hashed at 21:57:17Z, before the install.
- **Cell 1:**
  - **attempt 1** (21:59-22:14Z) played with no Home press. The user's message came after it had closed. Its files
    were renamed `*_attempt1*` (nothing deleted);
  - **the relaunch:** `privyhub-cl-b13-c1` 22:37:29-22:51:46Z, PLAYING 22:39:54Z.
- **Cell 2:** `privyhub-cl-b13-c2` 22:52:15-23:06:35Z, PLAYING 22:54:43Z.
- **Cell 3:** `privyhub-cl-b13` 23:10:39-23:39:34Z, "all 2 cells done": 3a PLAYING 23:13:04Z, 3b PLAYING 23:27:31Z.
- **Every cell:**
  - E1-SNES-STREAM (snes9x), window 600;
  - the drop-in read back at the stream (12 / 11 / 12 / 12) and removed at the teardown; `flags_absent` true; ten
    lines after;
  - the seven properties empty before and after;
  - 5180 MHz in every band read;
  - the client's class at each stream: lan (cells 1, 2), overlay (3a, 3b).
- **The reader** `cl_b13_read.py` (`record_read.json`, `record_read_console.txt`):
  - CL-B12's reader (its pinned `measure` / `evening` / `counts` and its `blackouts` / `sessions_underruns`,
    unedited);
  - plus `returns()` (the recovery log, the start's response and the report's arrival from the journal at µs
    precision (`journal_precise_cell{1,2,3}.txt`, addresses masked), heartbeat 1, the reports, the relay's frame log,
    the events read);
  - and `wan_rows()`.
- **The events reads:** one per attended cell, each taken right after its cell (`adb_reads/logcat_events_cell{1,2}.txt`,
  CL-B12's reader).
- **Disclosed:**
  - the user made **four** returns in cell 1, not two (22:43:48, 22:46:47, 22:47:10, 22:47:40Z). All four are read;
  - the first `git status` was taken after this dir was made;
  - a `__pycache__/` made by `py_compile` was removed (the launch record §2).

## 1. Validity and the gates

| cell | drop-in | PLAYING (attempt) | environ at stream | validity | RetroArch / capture / dup+drop | rendered | post-FEC loss / min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 (relaunch) | `none` + `RESTART_FAST` | 22:39:54 (1) | 12 | valid | 59.999 / **59.899** / 0.0 | 59.59 | 20.3 |
| 2 | `none` | 22:54:43 (1) | 11 | valid | 59.999 / 59.948 / 0.0 | 59.64 | 49.9 |
| 3a | `blackout-4s@both` + `LINK_RECOVERY_WAN` | 23:13:04 (1) | 12 | valid | 59.999 / 59.996 / 0.1 | 57.63 | 1,650 (the blackouts) |
| 3b | `blackout-4s@down` + `LINK_RECOVERY_WAN` | 23:27:31 (1) | 12 | valid | 59.999 / 59.997 / 0.1 | 57.80 | 1,613 (the blackouts) |

- **Cell 1's capture 59.899 is 0.001 under the gate's 59.9.** The cause is in the sampler's per-second encoder pairs:
  - the pair spanning each old encoder's kill holds 31 frames (that encoder killed mid-second) and is counted as a
    full second;
  - cell 1 had two such pairs, at 22:43:48.9 and 22:47:12.0 (its four returns); cell 2 had one;
  - with them left out, both cells read 59.996;
  - attempt 1, with no press, read 59.998.
  - The pre-registration (§6) says the Home cells "are not invalidated by the Home presses or the client sessions they
    cause". **So the cell is valid, with this disclosed.**
- **The dark spans:** 5 in 3a (the controller gaps ≥ 3 s, 120 s apart, `uplink_dropped` 8,876); 5 in 3b (uplink 0).
- **The class at the stream:** cells 1 and 2 `routing_evidence` lan; 3a and 3b overlay. The overlay check (23:10Z):
  connected, **direct**, 2 devices online.

## 2. Cell 1 — `PRIVYHUB_RESTART_FAST=1`, the Home returns (B item 7)

Times are UTC on the host's clock. "Entry" is the start's `session_ended`. The new activity on one clock is
`startSession` (heartbeat 1's arrival less its `elapsed_ms`) less `create_to_start_ms`.

| row | return 1 (the menu) | return 2 | return 3 | return 4 |
| --- | --- | --- | --- | --- |
| `session_ended` (the start's entry) | 22:43:48.258 | 22:46:47.349 | 22:47:10.632 | 22:47:40.229 |
| **(a) `restart_fast` `response_ms` / after `session_ended`** | **8.6 / 13 ms** | **7.4 / 12** | **6.7 / 11** | **6.6 / 12** |
| (b) the start's response (journal) → the old report | +275 ms | +318 | +121 | +83 |
| (b) `restart_fast_done` released / spawned / audio stopped / checked / done ms | 123 / 556 / **2,210** / 2,210 / 2,438 | 221 / 576 / 576 / 1,328 / 1,558 | 471 / 824 / 824 / 1,576 / 1,807 | 421 / 762 / 769 / 1,521 / 1,750 |
| **(c) the old encoder's last frame after the entry** (the relay's per-second rows) | **+0.075 s** | **+0.168** | **+0.351** | **+0.388** |
| (d) `restart_fast_released_by` / `_response_to_release_ms` / `_gate_resets` (last) | `fast` / 573 / 0 | `fast` / 632 / 1 (`fps`) | `fast` / 980 / 1 (`no_new_frame`) | `fast` / 935 / 0 |
| (d) `restart_cause` | `via_start`, host ended, `create_to_start_ms` 284, `recreate` | the same, 78 | the same, 80 | the same, 73 |
| `session_started` | 22:43:50.826 | 22:46:49.030 | 22:47:12.548 | 22:47:42.096 |
| **(e) the picture back: new activity → `session_started`, one clock** | **3.12 s** | **1.74** | **2.00** | **1.76** |
| (e) the same from the events read (the onn's clock) / the offset | 3.06 / −0.06 s | 1.90 / +0.16 | 2.14 / +0.14 | 2.10 / +0.33 |
| **(f) the first 2-s interval after `session_started`** (underruns) | **0** | **0** | **1** | **0** |
| (g) `restart_fast_failed` | 0 | 0 | 0 | 0 |
| (h) the path (events read) | new `MainActivity` → new `NativeStreamActivity` (`recreate`) | the same | the same | the same |

| row | CL-B12 cell 1 (no flag) | **CL-B13 cell 1** |
| --- | --- | --- |
| (a) response ≤ 300 ms, ≤ 300 ms after `session_ended` | 2.19 / 2.00 s (no worker) | **met 4 / 4** (6.6-8.6 ms; 11-13 ms) |
| (b) `restart_fast_done`; the response before the old report | — | **met 4 / 4** |
| (c) the old encoder's last frame ≤ entry + 0.3 s | +0.77 / +0.79 s (B22 §0) | **met 2 / 4; NOT MET at returns 3 and 4** (+0.35 / +0.39; `released_ms` 471 / 421) |
| (d) `fast`, the timings, `_gate_resets`; `via_start` | — | **met 4 / 4** (resets 0 / 1 / 1 / 0) |
| **(e) the picture back ≤ 3.0 s** | 12.0 / 6.8 (≈ 11.5 / 6.3 on one clock) | **met 3 / 4; NOT MET at return 1 (3.12 s)** |
| (f) the first interval ≤ 15 | 0 / 0 | **met 4 / 4** (0 / 0 / 1 / 0) |
| (g) no `restart_fast_failed` | — | **met** |
| (h) the path | `recreate` ×2; surface / process not produced | **`recreate` ×4; surface / process not produced** (the tile / recents return again went through `MainActivity`) |

- **Return 1's 3.12 s:** the worker's old-audio stop ran 2,210 ms (576-824 at the other three), and the ready's
  `status()` waits on the lock until `done` (2,438 ms). The client had released at 573 ms after the response. It is
  B22 §0's ~0.78-s audio teardown, longer once.
- **Returns 3 and 4 came 23 s after return 2 and 30 s after return 3** (`away_ms` 3,876 and 11,937): the user's extra presses. Their
  `released_ms` (471 / 421) is the old encoder's kill-to-exit; the frame rows put its last frame at +0.35 / +0.39 s.
  - **Method, disclosed:** the old encoder's row for the entry's second, at 60 fps from the second's start; the
    per-second log has no per-frame times.
- **Also seen:** one interval of 19 underruns in return 1's new session, at its end. That is the heartbeat as return
  2's Home paused the activity, as CL-B12's 30 was. Not a row.
- **The teardown:** `session_end_bye` 22:51:25.292, `session_ended` .563, `state_save_skipped` `state_ended` (the
  suite's stop first, as CL-B12 cell 1).
- **The events read's clock:** the offset (one clock − the onn's) read −0.06 to +0.33 s across the four returns, not
  B's ~0.5 s. Both columns are given.

## 3. Cell 2 — the same Home returns without the flag (B item 8)

| row | return 1 (22:58:27Z) | return 2 (23:01:27Z) | CL-B12 cell 1 |
| --- | --- | --- | --- |
| no separate `native-stream-stop`; `session_ended` logged by the start | **met** | **met** | met |
| the start's response (entry → response) / the old report after it | 3.97 s / +137 ms | 3.60 s / +78 ms | 2.19 / 2.00 s; +70 / +56 ms |
| `restart_cause` `via_start`, host ended, **`create_to_start_ms` ≤ 1,000**, trigger | **met:** 274, `recreate` | **met:** 81, `recreate` | 280 / 96, `recreate` |
| **no `restart_fast*` row or report key** | **met** (0 rows; no key) | **met** | — |
| **the picture back ~4-12 s** (one clock / events) | **7.52 / 7.48 s** | **6.73 / 6.90 s** | 12.0 / 6.8 |
| the first interval after `session_started` ≤ 15 | **met (2)** | **met (0)** | 0 / 0 |
| the old encoder's last frame after the entry | +0.87 s | +0.89 s | +0.77 / +0.79 |

- **Every row met.** The APK's absent-key path behaves as `20e3e339…` (CL-B12's order). The start's entry → response
  ran 3.6-4.0 s here (CL-B12 2.0-2.2), which is the old teardown inside the start.
- The teardown: bye 23:06:14.505, `state_save_skipped` `state_ended` (the suite's stop first).

**On 5 GHz** (B6's edge rule, UX-R3's reader; each client session to its Home silence; sessions of < 30 s, between the
extra returns, left out):

| span | streaming s | silences ≥ 250 ms / 10 min | hitch s / 10 min |
| --- | --- | --- | --- |
| cell 1 session 1 / 2 / 5 | 195 / 133 / 204 | **0.0 / 0.0 / 0.0** | 0.0 / 3.9 / 5.4 |
| cell 2 session 1 / 2 / 3 | 188 / 138 / 261 | 3.19 / 0.0 / 2.30 (276 and 257 ms) | 17.5 / 0.0 / 6.4 |
| CL-B12 cell 1 | 161 / 124 / 288 | 0.0 | 9.9 / 4.1 / 3.9 |

5180 MHz in every heartbeat.

## 4. Cell 3 — the remote class on the bench (B item 9; the onn on the overlay, direct, on the home 5 GHz Wi-Fi)

**The class rows, both sub-cells:**
- `link_recovery_wan_config` at the wire: `lan` 950 / 400, `remote-direct` 450 / 200, `remote-relayed` /
  `remote-unknown` as wired.
- At each stream's start, `link_recovery_config` `at` `session`, `wan.set` **`remote-unknown`** (`path` `pending`, 950 /
  400). Then **`remote-direct`** (`path` `direct`, 450 / 200) 271 ms (3a) / 269 ms (3b) later.
- **Met in both.**

### 3a — `blackout-4s@both`

| pause at (UTC) | in a blackout? | trigger, age ms | the save (kind, after onset) | via | resume after the return ms | held s | net |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 23:13:12.330 | **no** | `client_stall`, 207 | stall, 207 | `stall_end` (153 ms) | — | — | 12 |
| 23:14:41.982 | yes | `input_hold`, **458** | silence, 403 | `client_ready_hold` | **457** | 4.47 | 24 |
| 23:16:41.985 | yes | `input_hold`, **453** | silence, 405 | `client_ready_hold` | **193** | 4.20 | 24 |
| **23:18:07.353** | **no** | **`input_hold`, 451** | silence, 401 | `stall_end` (216 ms) | — | — | 24 |
| 23:18:42.487 | yes | `input_hold`, 955 (the guard's 950) | silence, 408 | `client_ready_hold` | 396 | 4.41 | 24 |
| 23:20:42.490 | yes | `input_hold`, 950 | silence, 403 | `client_ready_hold` | 461 | 4.47 | 24 |
| 23:22:42.476 | yes | `input_hold`, 953 | silence, 405 | `client_ready_hold` | 448 | 4.46 | 24 |

- **23:18:07.497Z, the guard:** `link_recovery_config` `wan.set` `remote-unknown`, 950 / 400, why = `WHY_GUARD` ("a
  non-drop silence >= 450 ms on the direct path …").
  - The re-read did not bring 450 back, as designed. The last three blackouts held at ~950.
- **A save outside with no pause:** 23:22:28.871Z, a silence save at 401 ms (a non-drop silence ≥ 401 ms; 950 by then).
- 0 `encoder_restart`, 0 `stall_handover_v2`. One session.
- The teardown: bye 23:24:35.866, `state_save_skipped` `client_bye` (402.0 ms), `session_ended`,
  `input_hold_skipped_paused`.

| row (B item 9) | CL-B12 cell 2 (LAN, 950) | **CL-B13 3a** |
| --- | --- | --- |
| `wan.set` `remote-unknown` → `remote-direct` 450 / 200; `link_recovery_wan_config` | — | **met** |
| the save ~400 ms, then the hold at age ≈ 450 | 401-407; 952-959 | **met while on direct** (403 / 405; 458 / 453) |
| resumed via `client_ready_hold` ≤ 1.0 s after the return | 259-349 ms | **met 5 / 5** (193-461 ms) |
| `state`, net ≈ 24 | 24 | **met** (24) |
| **0 false holds outside the blackouts** | 0 | **NOT MET: 1** (23:18:07, age 451) |
| **no `WHY_GUARD` row** | — | **NOT MET: 1** (23:18:07.497) |
| the teardown's bye and `state_save_skipped` | met | **met** |

### 3b — `blackout-4s@down`

| pause at (UTC) | trigger, age ms | the stall save (after the last frame) / before the pause | via | resume after the return ms | held s | net | restart / v2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 23:29:25.967 | `client_stall`, 208 | 208 / 104 ms | `client_ready_stall` | **41** | 4.04 | 12 | 0 / 0 |
| 23:31:25.852 | `client_stall`, 211 | 211 / 103 | `client_ready_stall` | **212** | 4.21 | 13 | 0 / 0 |
| 23:33:25.905 | `client_stall`, 212 | 212 / 104 | `client_ready_stall` | **146** | 4.15 | 13 | 0 / 0 |
| 23:35:25.858 | `client_stall`, 214 | 214 / 105 | `client_ready_stall` | **180** | 4.18 | 13 | 0 / 0 |
| 23:37:25.860 | `client_stall`, 210 | 210 / 104 | `client_ready_stall` | **143** | 4.14 | 13 | 0 / 0 |

| row | CL-B12 cell 3 (LAN, 400) | **CL-B13 3b** |
| --- | --- | --- |
| the class rows | — | **met** |
| the stall pause from ~200 ms, the save before it | 425-440 ms; 104-105 before | **met 5 / 5** (208-214; 103-105 before) |
| resumed via `client_ready_stall` ≤ 1.0 s after the return | 108-182 ms | **met 5 / 5** (41-212 ms) |
| 0 `encoder_restart`, 0 `stall_handover_v2` | 0 / 0 | **met** |
| 0 false holds / pauses outside; no `WHY_GUARD` | 0 | **met** (0 / 0; no row) |
| the teardown | met | **met** (bye 23:39:02.997; `client_bye` 400.8 ms; `input_hold_skipped_ending`) |

- **Net 12-13 per drop on direct**, against CL-B12's 26 at 400: the earlier stall save restores fewer frames. The
  picture held 4.04-4.21 s (CL-B12 4.11-4.18).
- **Disclosed:** 3b's blackouts are placed on the 120-s grid from the first pause's onset (the shim's lines carry
  `t_s`, not a wall time). Five pauses, five spans, all on the grid.

**Against G4-S4:** its replay gave 0 false holds at 950 and at 450 on a friend's Wi-Fi. Here one non-drop silence ≥ 450
ms came in 3a's 10 min (and one ≥ 401 ms), with the onn on the home Wi-Fi. That matches B23 §3's LAN rows (CL-B11 cell
1: 2 at 450), not the off-site ones.

## 5. The reading, as pre-registered

- **G-A5 — `PRIVYHUB_RESTART_FAST=1`: back to B with the rows.**
  - Not met:
    - **return 1's picture back 3.12 s.** The old audio's stop took 2.21 s in the worker, and the ready's `status()`
      waits on the lock until `done`;
    - **returns 3 and 4: the old encoder's last frame at +0.35 / +0.39 s** (`released_ms` 471 / 421);
    - **for B:** whether the ready needs the old audio's stop, or only the new encoder's check.
  - **What it gives:** the start answered in < 9 ms, and the picture back 1.7-2.0 s at three returns of four (cell 2:
    6.7-7.5 s; CL-B12: 6.8-12.0 s).
  - **The cost on the host:**
    - a worker thread per guarded restart;
    - the manager's lock held by it for 1.6-2.4 s, with the ready (and any `status()` poll) waiting on it;
    - the old audio stopped beside the new encoder.
  - **Off:** remove the line; the APK then behaves as `20e3e339…` (cell 2).
- **G-A6 — `PRIVYHUB_LINK_RECOVERY_WAN=1`: back to B with 3a's rows.**
  - Not met: one false hold at 450 ms and the guard's trip.
  - Met: the class rows, every blackout row, all of 3b, and the guard's revert.
  - **For B:** the onn on the home Wi-Fi through the overlay reads `remote-direct`, but its radio path is the LAN's. The
    class cannot tell a direct path that crosses the internet from one that crosses the living room.
  - **The cost:**
    - a daemon thread re-reading the overlay path every 10 s per remote session;
    - one false hold per session before the guard reverts;
    - false stall pauses at 200 ms (one here, 207 ms; 12 frames restored).
  - **Off:** remove the line; the hub then holds at 950 / 400 on every path.
- **Cell 2** (the APK's absent-key path) met every row. It feeds the rule (§6).
- **Not exercised:** the surface / process return paths, and a relayed path.

## 6. The CONFIRMED rule (CL-B7 §6)

- **All four cells valid** (§1; cell 1's capture miss disclosed under §6 of the pre-registration). **The behaviours as
  today where no flag was set** (cell 2: CL-B12's order, no `restart_fast` key).
- **The rule gives CONFIRMED:** `6bddafc0…a927` stays on the onn.
- **The pin moved** (`cl_b13_pin.diff`, `pin_predecessors/`, `pin_predecessor_sha256.txt`, `pin_after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK`;
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`;
  - its test, now `test_the_preflight_expects_the_cl_b13_apk`.
- **Tests** (`pin_tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK; `git
  diff --check` clean.
- **`e3_state` ok on ten, APK CONFIRMED** (`check_end.json`).
- **The APKs, nothing deleted (gitignored):**
  - `PrivyHub/app/build/cl_b13_installed/app-debug.apk` (`6bddafc0…`, on the onn);
  - `PrivyHub/app/build/cl_b12_installed/app-debug.apk` (`20e3e339…`, the previous CONFIRMED one).
- **CONFIRMED is about validity and today's behaviours:** the rows not met above do not block it. Without the host
  flags, the client is CL-B12's.

## 7. State at the end (~00:05Z), and the user's lines

- **The client back on the LAN:** the newest `token_issued` reads lan (23:53:38Z); `hub_host_set` false; no tailnet
  peer online (`client_end.json`).
- **The band 5 GHz** (5180 MHz, RSSI −68; `adb_reads/wifi_stage4.txt`).
- **The seven properties empty** (`adb_reads/properties_stage4.txt`). None was set in this task.
- **The drop-in removed; ten lines;** no `e3_flag.conf`; `flags_absent` true in every cell; `e3_state` ok, CONFIRMED.
- **The onn: `6bddafc0…`, paired.**
- **Units:** the companion and `privyhub-link-n1`. Every CL-B13 unit is closed and collected.
- No sudo, no nft. The Opal was untouched. **No `setprop`.** adb was used for the install, state reads and the two
  events reads.
- No address or identifier in any kept file (`redact_check.txt`). Nothing fetched. Nothing deleted but the
  `__pycache__` (disclosed). **Nothing adopted:** G-A5 and G-A6 are the user's questions. Nothing committed.
  `logs/cl_b13_git_status.txt`.
- **The user's messages, verbatim** (`user_lines.txt`):
  1. "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
  2. "I don't see a game playing" (22:36Z, after cell 1's first attempt had closed)
  3. "Stage 2"
  4. "It returned fine" (22:55Z, the line on cell 1)
  5. "Stage 3. Returned fine" (cell 2)
  6. "Idk what that means" (the hand step, retold plainly)
  7. "Stage 3 go"
  8. "Stage 4"

## 8. Files (`cl_b13_2026-10-25/`, `manifest.sha256` over all of it)

- **The start and the install:** see the launch record §2.
- **The cells:** `cells.jsonl` (cell 1 attempt 1, cell 1, 2, 3a, 3b); `cl_b13_c1_state_attempt1.json`,
  `cl_b13_c1_state.json`, `cl_b13_c2_state.json`, `cl_b13_state.json`; `runs/` (each with `band.jsonl`, `logs_run1/`,
  the journal, the mid-cell e3 read).
- **Stage 4:**
  - `cl_b13_read.py`, `record_read.json`, `record_read_console.txt`, `journal_precise_cell{1,2,3}.txt`;
  - `adb_reads/logcat_events_cell{1,2}.txt`, `cl_b13_events_read.py`;
  - the pin: `cl_b13_pin.diff`, `pin_predecessors/`, `pin_*_sha256.txt`, `pin_tests.txt`;
  - `check_end_before_rule.json`, `check_end.json`, `client_end.json`, `units_end.txt`, `adb_reads/*stage4*`;
  - `user_lines.txt`, `redact_check.txt`.
