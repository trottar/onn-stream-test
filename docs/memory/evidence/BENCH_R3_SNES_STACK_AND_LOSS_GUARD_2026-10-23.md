---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 9fd73c7 (the code under test; the record's pin patch uncommitted beside it)
---

# BENCH-R3 — the stack on SNES, the loss guard, the link: MEASURED, 6/6 valid; the stack is NOT a candidate; the loss guard IS a candidate; APK bf5114a2 CONFIRMED

**Classification: MEASURED. All six cells were playing and valid, and the host gates were met in all six.** The
pre-registered reading, applied as hashed (`bench_r3_preregistration.txt`, `620a0ade…5290`):
- **The hold / rewind / stall stack is NOT a candidate on SNES.** A and B missed their bars; C met its bar.
  - **A (`@both`):** every blackout got one hold at 0.95-0.97 s. **But snes9x's rewind is not confirmed:**
    - all 7 hold-path rewinds (59-60 frames each) failed B4's after-check, because the core read PAUSED;
    - the 6 blackouts each left **47.5-48.7 unattended frames** (`--net` the same; bar ≤ 5);
    - only 1 of 5 resumes came via `hold_return_stall`; the other 4 came via the gate's `client_ready_hold`;
    - the resumes came **2.06-3.13 s after the return** (B8's ≤ ~2.3 s in 1 of 5).
  - **B (`@down`):** the stall pause came at 420-428 ms in 4 of 5 blackouts and **484 ms** in the fifth (bar
    0.40-0.46 s in every one).
    - Each blackout's own pause was resumed by recovery v2, with an encoder restart in 3 of 5 and the ladder stepping
      7000→5000 once.
    - It was not resumed by `stall_end` with its own rewind. Only a second, in-gate pause got a 2-3-frame rewind.
  - **C (clean):** 0 false holds, 0 stall pauses (met).
- **D (PS1 savestate fallback) met its bar:**
  - the state was saved 403-408 ms into each blackout;
  - **the load played in all 5 blackouts:** `LOAD_STATE_SLOT 9` acked, RetroArch's "Loading state …state9" with no
    failure line, and the picture advancing at 56.5-60.7 fps;
  - **net 24 frames** per blackout (B9's row; bar ≤ 30).
  - PS1 "joins only if …" the stack is a candidate, and it is not. So no PS1 question arises.
- **The loss guard IS a candidate:**
  - E-on held **3,010 frames = its counter's 3,010**, with **0 timeouts** and a max wait of **501 ms** (cap 600).
  - E-off's counter read **462 per minute**, not ~300; part of that minute-to-minute spread is the house's own loss.
  - Its costs, stated:
    - freezes up to ~0.5 s in place of corrupted frames;
    - hitch seconds 125.7 against 68.8 per 10 min (104.3 outside a house event in the cell);
    - rendered fps 55.2 against 57.8;
    - the keyframe requests force nothing (there is no runtime IDR path).
  - The user's lines on E-off / E-on: **"no watch".**
- **The link (reported for the next task, not read here).** The onn streamed on **2.4 GHz, channel 1 (2412 MHz,
  802.11n)**, at RSSI −70…−66 dBm (−68 median) and tx 108-135 / rx 81-162 Mbps typical, in every cell.
  - **The Opal's `wlan1` (5 GHz) listed no station in any of its 18 rounds,** so the Opal's view of the onn is
    absent.
  - **One coincidence in time:** E-on's cluster of 42 uplink silences (21:42:20-21:43:25Z) coincides with the onn's
    **tx link rate falling to 27-81 Mbps**. 52 % of heartbeats there read ≤ 54 Mbps, against 0.9 % elsewhere in the run.
  - The downlink loss stretches (D's three, E-off's flap at 21:26:53-21:27:08Z) coincide with **no RSSI change beyond
    1 dB**, and with no rx-rate dip above its base rate.
- **The CONFIRMED rule:** every cell was valid, and the property-empty behaviours read as today. So **`bf5114a2…cf73`
  stays on the onn and is CONFIRMED.** The pin moved (§9).
- **Nothing adopted. Nothing committed.**

Task: `handoffs/BENCH-R3_SNES_STACK_AND_LOSS_GUARD_TASK.md` §2, "the record", session A, read-only from
`bench_r3_2026-10-22/`. The run was 20:22:11-21:52:17Z on `9fd73c7` (launch: `BENCH_R3_LAUNCH_2026-10-22.md`). The
driver closed by itself (`all 6 cells done`). The Opal sampler gave 18 rounds and exited 0. The four properties were
cleared and read back empty at the close.

## 0. The read

- **First:** the heartbeat, control-gap and recovery logs over 20:19-21:53Z were copied from the live files into
  `record/logs_whole_run/`, addresses masked (none found), before they rotate: 2,051 / 145 / 199 rows.
- **`record/bench_r3_record_read.py`** is built from `bench_r2_record_read.py`. It reads the driver's per-cell copies
  into `record/logs/<cell>/`, with each cell's client report (core version token masked), and runs the following tools
  unedited:
  - UX-R3's `evening` / `counts` for hitch seconds (sha256 `e9b2b3f7…` = BENCH-R2's pin; **not in R3's tool list,
    disclosed**);
  - B6's `measure` for the silences (= R3's pin);
  - `tools/unattended_frames.py`, plain and `--net` (= R3's pin).
- **Its additions:**
  - the per-blackout carry / handover / resume / release / state rows;
  - the picture after a resume (the client's rendered frames over the next 10 s);
  - the per-minute link table with the shim's drops;
  - the link and the nearest Opal round beside every silence ≥ 500 ms, every blackout and every minute of post-FEC
    loss > 500.
- **`record/outside_reads.py`:** hitch seconds outside the blackouts, and E-on's silences outside its cluster.
- **`record/link_coincidence.txt`:** the link's base rates against the heartbeats within ±10 s of the events.
- **Blackout times:**
  - A and D from the ~4-s control gaps (the start; the return = the gap's end);
  - B (`@down`) from the client's own ≥ 3-s output gaps, R2's c1 method; the return = start + 4.0 s.
  - The shim-offset anchor (11 spans of A and D) has median −6.94 s, range 1.0 s. B's shim-anchored starts sit ~0.8 s
    before the client's last frame; both are kept in `record_read.json`.
- **Disclosed:**
  - **Some heartbeats arrived late and out of order.** In E-off, sequence 127 arrived 67.8 s late and 129 arrived
    19.8 s late, both sent at the start of the 21:27Z flap. Other cells had late arrivals of 2-9 s.
  - The reader therefore takes each cell's heartbeats in sequence order (one client session per cell) and places them
    by the client's elapsed clock (UX-R3's map). A first pass that kept arrival order double-counted the deltas around
    a reorder (E-off's 21:27 minute read 5,256 instead of 1,649); it is superseded.
  - UX-R3's `evening` is exec'd unedited and splits sessions on a sequence step-back. At the 2-3 reorders this may drop
    one interval's row.
- **The Opal:** read-only throughout. Its output went through `o1_redact.py` inside the sampler before it was written.

## 1. Validity and the gates (every cell)

| cell | fixture | the shim (applied) | environ at stream / under load | properties set → after | suite attempt, s to PLAYING | validity | gates |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | SNES (snes9x) | 6 dark spans, 5 s lines, 120.0 s apart; `uplink_dropped` 10,482; no other drop | 16 / 16 | stall_signal=1, link_report=1 → all empty | 2, 4.1 | valid | met |
| B | SNES | 5 spans, 120.0 s apart; `uplink_dropped` 0 | 16 / 16 | the same → empty | 1, 3.1 | valid | met |
| C | SNES | `none`: 0 drops of any kind | 16 / 16 | the same → empty | 1, 3.0 | valid | met |
| D | PS1 (Beetle PSX HW) | 5 spans, 120.0 s apart; `uplink_dropped` 8,596 | 16 / 16 | the same → empty | 1, 2.0 | valid | met |
| E-off | PS1 | `loss-1`: 0.99 % (6,626 of 669,085); no other drop | 12 / 12 | loss_guard=count, link_report=1 → empty | 1, 4.1 | valid | met |
| E-on | PS1 | `loss-1`: 0.99 % (6,633 of 669,901) | 12 / 12 | loss_guard=1, link_report=1 → empty | 1, 8.1 | valid | met |

- **Every cell:**
  - the encoder read back `7000k/7000k/7000k`; B also saw `5000k` after its 20:47:20Z step;
  - `flags_absent` true after;
  - RetroArch 59.999 fps; capture 59.995-59.998; dup + drop 0.0-0.1 / min.
- **A's suite attempt 1 did not play** (no failure file is in the run directory); attempt 2 played. A is valid by the
  rule; disclosed.
- **The config rows read as pre-registered:**
  - A-D: `stall_signal threshold_ms 400`; B6 `hold_ms 950`; B8 `output_fresh_ms 300`, `rewind_cap 72`;
  - A-C: rewind cores `allow` (snes9x, bsnes); D: `mode state`, slot 9, `state_at_ms` 400;
  - E: `loss_guard_config`, `NoRuntimeIdr`, 500-ms minimum interval.

## 2. Per cell: silences, hitches, unattended frames, the client, the host

| cell | silences ≥ 250 ms / 10 min (n, longest ms) [outside the blackouts] | ≥ 500 / 10 min | hitch / 10 min (longest run s) [outside the blackouts] | unattended core-running / 10 min (`--net`) | post-FEC loss / min | rendered fps | max output gap ms | host CPU % | encoder % | RetroArch CPU % / RSS MB mean (max) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 21.4 (24, 4,192) [18.5] | 7.1 [2.9] | 32.0 (3) [20.1] | 386.1 (386.1) | 1,306 | 58.15 | 4,207 | 8.0 | 28.9 | 10.7 / 171 (190) |
| B | 12.5 (14, 691) [11.7] | 0.9 [1.0] | 33.8 (3) [18.6] | 69.2 (64.9) | 1,209 | 57.64 | 4,209 | 7.1 | 26.6 | 5.6 / 160 (169) |
| C | 22.4 (25, 438) | 0.0 | 19.9 (1) | 68.1 (68.1) | 33 | 59.81 | 251 | 8.4 | 26.2 | 9.9 / 172 (192) |
| D | 10.7 (12, 4,067) [6.8] | 4.5 [0.0] | 79.4 (4) [71.2] | 225.4 (225.4) | 2,131 | 56.73 | 4,286 | 11.6 | 36.8 | 35.1 / 308 (345) |
| E-off | 4.5 (5, 322) | 0.0 | 68.8 (4) | 8.0 (8.0) | 800 | 57.80 | 787 | 10.7 | 36.2 | 34.7 / 250 (271) |
| E-on | **54.5** (61, 1,223) [18.8 outside 21:42:20-21:43:25] | 12.5 [1.0] | **125.7** (8) [104.3 outside the cluster] | 473.2 (473.2) | 72 | 55.19 | 597 | 10.9 | 36.7 | 36.3 / 252 (274) |

- **The silence distribution (B6's bins, n):**
  - A: 250-300 9 · 300-400 5 · 400-500 2 · 500-600 1 · 600-800 1 · 1000-1500 1 · ≥ 1500 5 (the blackouts);
  - B: 5 · 8 · 0 · 0 · 1 (691 ms);
  - C: 15 · 7 · 3, none ≥ 500;
  - D: 4 · 3 · 0 … ≥ 1500 5 (the blackouts);
  - E-off: 4 · 1;
  - E-on: 24 · 17 · 6 · 8 · 4 · 0 · 2.
- **The comparison rows (BENCH-R2), silences / hitch per 10 min:**
  - b1 12.5 / 23.4; b2 7.1 / 14.8; c1 125.7 / 115.3;
  - SNES clean f1 15.2 / 15.6, f2 11.6 / 14.7;
  - PS1 clean d1 16.9 / 20.8, d2 15.2 / 14.7, a3 29.5 / 25.2, a1 41.8 / 84.9 (that hour's room).
- **The `--net` reader credits only `input_release` rows that carry `rewound_frames`.** So A's rewinds (all
  `rewind_failed`) and D's `state` releases (`frames_restored`) are not credited. D's net is read from B9's own row and
  by subtraction (§4).
- **RetroArch on SNES with rewind on (A-C)** reads 5.6-10.7 % of a core and 160-172 MB; its log reads "Initializing
  rewind buffer with size: **61 MB**" (pre-registered ~53 MB). PS1 with `state` (D) reads 308 MB against 250-252 MB in
  E's PS1 cells without it.

## 3. The blackout cells against BENCH-R2 (A, B, D)

Rows relative to the blackout's start (`record_read.json` `blackouts[].rows` carries every row).

**A — SNES, `@both`, the stack + B8** (against R2 b1 = PS1, the stack without B8, stall at 150; and b2 = no stall):

| # | start (UTC) / return | hold s (age ms) | carry pre / stall | handover s (held ms) | resume (via, s after return; heartbeats between) | the rewind row | stall_end_late ms (gate stalls ignored) | picture after (first advance s, fps over 10 s) | unattended core-running / --net | link before → after (RSSI, tx/rx) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b1 | 20:26:13.204 / 26:17.396 (4.19 s) | 1.06 (966) | 59 / 0 | 4.23 (3,261) | client_ready_hold +2.57; 2 | rewind_failed (via hold_return_stall), req 59, rew 59, PAUSED after | 325 (6) | 1.79, 59.4 | 48.4 / 48.4 | −67, 162/108 → −67, 162/162 |
| b2 | 20:28:13.388 / 28:17.391 (4.00 s) | 1.04 (951) | 59 / 0 | 4.03 (3,078) | client_ready_hold +2.49; 1 | the same, req 59 | 377 (7) | 0.76, 59.9 | 47.5 / 47.5 | −67, 162/108 → −67, 135/108 |
| b3 | 20:30:13.356 / 30:17.399 (4.04 s) | 1.04 (952) | 59 / 0 | 4.08 (3,128) | **hold_return_stall +3.13**; 1 | rewind_failed (via client_ready_hold), req 59 | 399 (7) | 0.93, 60.2 | 47.6 / 47.6 | −68, 121/108 → −68, 108/108 |
| b4 | 20:32:13.374 / 32:17.395 (4.02 s) | 1.06 (957) | 60 / 0 | 4.06 (3,102) | client_ready_hold +2.06; 1 | rewind_failed (via hold_return_stall), req 60 | 505 (7) | 0.77, 59.2 | 48.7 / 48.7 | −67, 108/81 → −67, 121/216 |
| b5 | 20:34:13.386 / 34:17.404 (4.02 s) | 1.05 (950) | 59 / 0 | 4.02 (3,072) | client_ready_hold +2.72; 1 | rewind_failed (via hold_return_stall), req 59 | 489 (7) | 0.81, 59.6 | 48.0 / 48.0 | −67, 121/108 → −67, 121/108 |
| b6 | 20:36:13.385 / 36:17.410 (4.03 s) | 1.06 (953) | 59 / 0 | 4.03 (3,072) | none (the session ended at +1.1 s) | rewind_failed (via stall_quiet), req 59 | — | — | 48.4 / 48.4 | −68, 108/108 → −68, 108/162 |

- **Every rewind row:**
  - method `unpaused_per_frame`; `rewound_frames` = requested (59-60); `counter_after` 0;
  - `rewind_ms` 967-986, i.e. ~1 s of rewinding before the resume;
  - the reason: "not playing after the rewind: GET_STATUS PAUSED Snes9x,Super Mario Wor…".
- **The sequence in each blackout:**
  1. the rewind (B8's carry);
  2. the after-check reads PAUSED and logs `rewind_failed`;
  3. ~0.1 s later a `resumed` row, via the gate's ready in 4 of 5;
  4. `stall_gate_after_return`, `client_ready_after_hold`, `stall_end_late` 0.3-0.5 s after the resume.
- **No second `desync_pause` and no `session_started` in any blackout.** The picture played after every resume (59-60
  fps).
- **The carry's `stall_frames` read 0 in every blackout** (B8 expected ≈ 4).
- **A seventh hold, outside the blackouts:** at 20:29:18.8Z (age 953 ms), on a 1,295-ms house silence. It was released
  at 1,295 ms (`resumed via input_release`); its rewind (59 frames) also failed the after-check. That is 0.87 false holds
  per 10 min.
- **Against R2:**
  - b1 (PS1, no B8) resumed 1.78-2.59 s after the return, with 42-49 unattended frames per blackout;
  - b2 (no stall) resumed at 1.06-1.11 s, 47-48 frames.
  - A's unattended frames per blackout are the same as b1's / b2's. Its resume is no earlier.

**B — SNES, `@down`, the stack** (the start = the client's last frame before the dark span; the return = start +
4.0 s) against R2 c1 (PS1, the stall at 150):

| # | start (UTC) | stall pause, age ms (s after the start) | encoder restart | resumes (via, s after the return) | the second, in-gate pause and its rewind | picture after the last resume (first advance s, fps) | unattended core-running | link before → after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b1 | 20:41:08.492 | 428 (0.49) | 1 | recovery +2.52, stall_end +2.82 | 1; input_release req 2 rew 2, PLAYING after | 1.12, 60.2 | 5.8 | −67, 108/162 → −67, 108/108 |
| b2 | 20:43:08.488 | 428 (0.39) | 0 | recovery +3.29, stall_end +3.85 | 1; req 3 rew 3, PLAYING | 0.81, 59.7 | 0.0 | −68, 121/81 → −69, 108/40 |
| b3 | 20:45:08.488 | 420 (0.39) | 1 | recovery +1.93, stall_end +2.36 | 1; req 3 rew 3, PLAYING | 0.94, 59.9 | 0.0 | −68, 108/108 → −68, 121/108 |
| b4 | 20:47:08.486 | 426 (0.48) | 1 | recovery +4.07, stall_end +4.68 | 1; req 3 rew 3, PLAYING | 1.29, 58.5 | 0.0 | −69, 121/81 → −69, 121/81 |
| b5 | 20:49:08.491 | **484** (0.55) | 0 | recovery +2.16, stall_end +2.86 | 1; rewind_failed req 2 rew 2, PAUSED | 1.71, 58.5 | 0.8 | −68, 108/108 → −68, 121/81 |

- **The pause's timing is read from the stall row's `age_ms`**, the client's output age when the host paused (R2's
  method). The column in brackets is placed by the client's report and carries ~±0.1 s of placement.
- **Each blackout's own pause (`client_stall`, not in the gate) was resumed by recovery v2** (`resumed`, no `via`,
  5.5-7.7 s `recovering_ms`).
  - Recovery restarted the encoder in b1, b3 and b4. After the third restart the ladder stepped 7000→5000
    (`recovery_escalation`, 20:47:20Z).
  - Then an in-gate stall paused again ~0.1 s later, and *that* pause was released by `stall_end` with a 2-3-frame
    rewind.
  - So the expected "its own rewind, resumed via `stall_end`" did not happen for the blackout's pause. B8 left `@down`
    unchanged by design.
- **Stall pauses outside the blackouts: 0** (R2 c1: 77 per 10 min at 150, on that hour's flapping link).
- **Unattended frames on `@down`:** the uplink is not silenced, so the B2 reader sees almost none (0-5.8). The game ran
  ~0.42 s (~25 frames) without a picture before each pause (R2 c1: 0.15-0.21 s at 150).

**D — PS1, `@both`, the stack with `INPUT_HOLD_REWIND=state`:**

| # | start (UTC) / return | state_saved after onset ms | hold s (age ms) | carry pre / stall | handover s (held ms) | resume (via, s after return) | input_release (method state) | picture after (first advance s, fps over 10 s) | stall_end_late ms (gate stalls ignored) | unattended core-running (tool) | link before → after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| b1 | 21:09:48.216 / 09:52.222 | 404.9 | 1.08 (986) | 61 / 0 | 4.05 (3,068) | hold_return_stall +2.69 | restored 36, net 24, LOAD_STATE_SLOT 9 | 0.79, 59.5 | 3,388 (59) | 49.7 | −68, 108/81 → −68, 121/108 |
| b2 | 21:11:48.218 / 11:52.225 | 408.3 | 1.05 (951) | 59 / 0 | 4.05 (3,099) | hold_return_stall +2.81 | restored 34, net 24 | 0.98, 60.7 | 3,075 (51) | 48.1 | −68, 121/108 → −68, 121/162 |
| b3 | 21:13:48.209 / 13:52.224 | 402.8 | 1.06 (956) | 59 / 0 | 4.01 (3,059) | hold_return_stall +1.93 | restored 35, net 24 | 1.08, 59.4 | 11,787 (101) | 48.4 | −69, 135/121 → −69, 121/108 |
| b4 | 21:15:48.163 / 15:52.220 | 408.0 | 1.06 (962) | 59 / 0 | 4.09 (3,124) | hold_return_stall +1.55 | restored 35, net 24 | 1.70, 60.6 | 1,842 (32) | 48.5 | −68, 121/81 → −69, 121/108 |
| b5 | 21:17:48.152 / 17:52.219 | 404.0 | 1.05 (956) | 59 / 0 | 4.11 (3,149) | hold_return_stall +0.92 | restored 35, net 24 | 2.03, 56.5 | 2,464 (40) | 48.1 | −68, 121/108 → −68, 135/108 |

- **B8's resume worked on PS1:** all five resumes came via `hold_return_stall`, 0.92-2.81 s after the return. There was
  no rewind wait.
- **The load:** RetroArch's log reads "[State] Loading state "…/Tekken 3 (USA).state9", 16777240 bytes." five times
  (each after "Saving state "RAM"", its undo buffer), with no failure line.
  - The pre-registered phrase "Loaded state from slot #9" does not occur. This RetroArch logs "Loading state"; read as
    the load, disclosed.
  - The picture advanced 0.8-2.0 s after each resume and played at 56.5-60.7 fps.
- **Net unattended frames, three readings:**
  - **B9's row: 24** in every blackout (`pre_hold_frames` − `frames_restored`);
  - the B2 reader's core-running minus `frames_restored`: 13.1-14.1;
  - the `--net` reader as written: 48.1-49.7 (it does not read `state` releases).
- **The client's gate stalls continued 1.8-11.8 s after each resume** (`stall_end_late`, 32-101 gate stalls ignored as
  over fresh output). The A blackouts read 0.3-0.5 s.
- **No rewind buffer** in RetroArch's log.
- **A sixth `state_saved`** at 21:19:43.455Z, 38 ms before `session_ended`: a save in the teardown's silence, harmless,
  disclosed.
- **Two stall pauses outside the blackouts** (21:12:23.96Z age 431; 21:16:54.40Z age 429). Both were released by
  `stall_end` after ~0.2 s, `rewind_skipped` ("no scratch state for this pause"): `state` covers only the hold's
  silence.
  - The second coincides with a downlink loss burst (21:16:41-58Z) and a heartbeat 8.7 s late.
- **The saves' hitch cost:**
  - saves happen only inside silences ≥ 400 ms, i.e. in the blackouts (19 hitch seconds over 5 blackouts; A's six:
    17);
  - outside the blackouts D read 71.2 hitch seconds per 10 min, against R2's PS1 clean rows 14.7-25.2 (a1's flapping
    hour 84.9).
  - D's minutes 21:14, 21:16 and 21:19 carry the house's own loss (§7), so this cell does not separate a save cost from
    the room.
- **Against R2 b1** (PS1, rewind, 118 / 123 failing): the state path restores 34-36 frames per blackout, where PSX HW's
  rewind did not.

## 4. The clean cell (C)

- **0 holds and 0 stall pauses** in 11.5 min (bar: false holds ≤ 1 / 10 min, stall pauses 0) — **met.** R2 d2 (PS1,
  400): 0 / 0.
- Silences 22.4 per 10 min, none ≥ 500 (max 438). Hitch 19.9 per 10 min. Post-FEC loss 33 / min; rendered 59.81 fps.

## 5. The loss guard (E-off, E-on)

| | E-off (`loss_guard=count`) | E-on (`loss_guard=1`) |
| --- | --- | --- |
| `frames_after_dropped_reference` (the report) | **5,342** = 462 / min over 11.55 min (full minutes 308-718) | 3,010 = 261 / min |
| `loss_guard_episodes` | 517 | 394 |
| `loss_guard_frames_held` | 0 | **3,010** (= the counter) |
| `loss_guard_timeouts` | 0 | **0** |
| `loss_guard_max_wait_ms` | 2,799 (the counter's own longest run to an IDR; nothing held) | **501** |
| `keyframe_requests_sent` (client) | 0 | 394 (one per episode) |
| the host's `keyframe_requests` rows (cumulative, per minute) | — | 12 rows; final received 376, acted 318, rate-limited 58, **forced 0**, reason "no runtime IDR path: the ffmpeg encoder's GOP (15 frames) is fixed at launch …" |
| AU drops: `sequence_gap_au_drops` / `incomplete_au_drops` / `dropped_frames` | 744 / 162 / 919 | 448 / 26 / 464 |
| `non_idr_aus_dropped_waiting_for_idr`; `max_frames_between_idr` | 36; 177 | 0; 14 |
| post-FEC lost (report); FEC recovered; unrecoverable groups | 5,718; 5,429; 395 | 845; 5,387; 224 |
| hitch seconds / 10 min (longest run) | 68.8 (4) | **125.7** (8); 104.3 outside 21:42:20-21:43:25 |
| rendered fps; max output gap ms | 57.80; 787 | 55.19; 597 |
| the user's line | "no watch" | "no watch" |

- **The counter per minute** (heartbeat deltas, sequence order):
  - E-off: 308, 516, 486, 642, 350, 572, 513, 718, 427, 393, 333;
  - E-on: 151-357 in its full minutes, with held equal to it in every minute.
- **E-off's two loss stretches** (21:27 1,649 lost; 21:30 1,106 lost, against 139-595 in its other full minutes) lie
  above the shim's steady 1 % (540-579 drops per minute pre-FEC).
  - The counter in those minutes: 350 and 718.
  - E-off's report lost 5,718 packets after FEC against E-on's 845 under the same shim line. So **part of E-off's
    counter is the house's loss, not the shim's.**
- The 21:42 cluster in E-on is in §7.

## 6. Every row, with timing

All of them are in `record/record_read.json` (`cells.<cell>.recovery_rows`, with `at_utc`). The per-blackout tables
above carry them relative to each blackout, and `blackouts[].rows` lists them. Outside the blackouts:
- **A:**
  - 20:24:46.33Z `session_started`;
  - 20:29:18.83Z `desync_pause input_hold` (age 953), 20:29:20.13Z `rewind_failed` (req 59), 20:29:20.23Z `resumed via
    input_release` (held 1,295 ms);
  - 20:36:18.49Z `session_ended`; 20:36:19.08Z `input_hold_skipped_paused`.
- **B:** 20:39:14.61Z `session_started`; 20:50:46.25Z `session_ended`; `input_hold_skipped_paused`.
- **C:** `session_started` 20:53:39Z, `session_ended` 21:05:11Z; nothing else.
- **D:**
  - the two stall pauses (§3);
  - 21:14:05.94Z `stall_end_late` (b3, since_resume 11,787 ms, 101 gate stalls ignored);
  - 21:19:43.455Z `state_saved` (teardown); 21:19:43.49Z `session_ended`.
- **E-off:** `loss_guard_config`, `session_started`, `session_ended`.
- **E-on:** `loss_guard_config`, `session_started`, the 12 `keyframe_requests` rows (21:37:49-21:48:53Z, cumulative),
  `session_ended`.

## 7. The link: the client's report per minute, beside the events, and the Opal

**The onn's link, every cell:**
- 2412 MHz (2.4 GHz, channel 1), Wi-Fi standard 4 (802.11n). Every one of 2,030 in-session heartbeats carried all five
  keys.
- **RSSI:** −70 (3 heartbeats), −69 (234), −68 (1,461), −67 (332).
- **tx Mbps:** 108 / 121 / 135 / 162 in 95 %; 27-54 in 35.
- **rx Mbps:** 81 / 108 / 162 in 83 %; **6 in 61 and 27 in 41 heartbeats (5 %)**, spread through every cell.
- In O1 (2026-09-21) the client was on the Opal's 5 GHz `wlan1` at −70 / −71 dBm. The 2412-MHz channel is the Opal's
  `wlan0`'s (2.4 GHz, channel 1, 40 MHz).

**The Opal** (`opal/air.jsonl`, 18 rounds, 20:22:16-21:47:16Z, every 300 s, read-only, redacted):
- `wlan1`, channel 36 / 80 MHz;
- **0 associated stations in every round**;
- utilization 0.0-10.0 % (median 6.6); noise −84…−90 dBm; 0 log events; load 1.04-1.73.
- **The Opal's retries / signal / rate for the onn's station cannot be reported:** the pre-registered sampler reads
  `wlan1`, and the onn was not on it.
- The nearest round sits beside every event in `record_read.json`. None carries a station row.

**Per minute, every cell** (heartbeat deltas in sequence order, placed by the client's clock; the shim's drops placed by
the offset anchor; E adds the guard's counters):

**A** (334 / 334 heartbeats with the link keys):

| min (UTC) | hb | RSSI med / min dBm | tx med / min Mbps | rx med / min Mbps | post-FEC lost | FEC-unrec | shim drops | fps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20:24 | 9 | -67 / -67 | 162 / 121 | 108 / 108 | 0 | 0 | 0 | 64.7 |
| 20:25 | 30 | -67 / -67 | 135 / 108 | 108 / 6 | 16 | 2 | 0 | 59.8 |
| 20:26 | 27 | -67 / -67 | 162 / 108 | 108 / 54 | 3,227 | 3 | 3,754 | 55.6 |
| 20:27 | 30 | -67 / -67 | 121 / 108 | 108 / 6 | 7 | 1 | 0 | 59.8 |
| 20:28 | 28 | -67 / -67 | 121 / 108 | 135 / 81 | 3,201 | 3 | 3,710 | 55.8 |
| 20:29 | 30 | -67 / -68 | 135 / 108 | 108 / 54 | 21 | 6 | 0 | 59.6 |
| 20:30 | 28 | -68 / -68 | 108 / 108 | 108 / 6 | 3,203 | 3 | 3,707 | 55.7 |
| 20:31 | 29 | -68 / -69 | 121 / 108 | 108 / 54 | 21 | 4 | 0 | 59.8 |
| 20:32 | 28 | -67 / -69 | 121 / 108 | 108 / 40 | 3,227 | 6 | 3,715 | 55.7 |
| 20:33 | 30 | -68 / -69 | 108 / 81 | 108 / 27 | 16 | 2 | 0 | 59.9 |
| 20:34 | 28 | -67 / -68 | 121 / 108 | 108 / 81 | 3,211 | 3 | 3,723 | 55.8 |
| 20:35 | 30 | -68 / -68 | 121 / 81 | 108 / 54 | 12 | 2 | 0 | 59.9 |
| 20:36 | 7 | -68 / -68 | 108 / 108 | 108 / 54 | 3,209 | 1 | 3,738 | 46.5 |

**B** (346 / 346):

| min (UTC) | hb | RSSI med / min dBm | tx med / min Mbps | rx med / min Mbps | post-FEC lost | FEC-unrec | shim drops | fps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20:39 | 25 | -67 / -67 | 162 / 108 | 162 / 27 | 15 | 4 | 0 | 60.2 |
| 20:40 | 29 | -67 / -67 | 108 / 27 | 108 / 81 | 19 | 3 | 0 | 59.9 |
| 20:41 | 30 | -67 / -69 | 121 / 108 | 162 / 6 | 3,143 | 1 | 3,637 | 55.2 |
| 20:42 | 30 | -68 / -69 | 135 / 108 | 108 / 54 | 12 | 2 | 0 | 59.9 |
| 20:43 | 30 | -68 / -70 | 121 / 108 | 81 / 6 | 3,264 | 5 | 3,775 | 55.7 |
| 20:44 | 30 | -68 / -68 | 121 / 108 | 108 / 6 | 24 | 5 | 0 | 59.7 |
| 20:45 | 30 | -68 / -68 | 121 / 108 | 108 / 6 | 31 | 3 | 3,539 | 55.6 |
| 20:46 | 29 | -68 / -69 | 121 / 81 | 81 / 6 | 33 | 5 | 0 | 59.9 |
| 20:47 | 30 | -69 / -69 | 121 / 81 | 108 / 54 | 3,180 | 7 | 3,678 | 55.5 |
| 20:48 | 30 | -68 / -68 | 121 / 81 | 108 / 6 | 13 | 2 | 0 | 59.8 |
| 20:49 | 30 | -68 / -68 | 114.5 / 108 | 94.5 / 6 | 2,329 | 7 | 2,745 | 55.4 |
| 20:50 | 23 | -68 / -68 | 121 / 81 | 81 / 54 | 2 | 1 | 0 | 59.7 |

(20:45: the encoder restart's sequence resync carries that blackout's loss outside `lost_packets`.)

**C** (343 / 343):

| min (UTC) | hb | RSSI med / min dBm | tx med / min Mbps | rx med / min Mbps | post-FEC lost | FEC-unrec | shim drops | fps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20:53 | 12 | -68 / -68 | 114.5 / 108 | 108 / 81 | 8 | 3 | 0 | 60.9 |
| 20:54 | 30 | -68 / -68 | 121 / 81 | 108 / 54 | 45 | 5 | 0 | 59.8 |
| 20:55 | 29 | -68 / -68 | 108 / 54 | 81 / 27 | 24 | 2 | 0 | 59.6 |
| 20:56 | 30 | -68 / -68 | 121 / 81 | 108 / 6 | 51 | 5 | 0 | 59.6 |
| 20:57 | 28 | -68 / -68 | 114.5 / 54 | 81 / 6 | 14 | 2 | 0 | 59.9 |
| 20:58 | 30 | -68 / -68 | 121 / 108 | 108 / 6 | 9 | 3 | 0 | 59.9 |
| 20:59 | 28 | -68 / -68 | 121 / 108 | 108 / 6 | 24 | 2 | 0 | 59.9 |
| 21:00 | 30 | -68 / -68 | 121 / 81 | 108 / 40 | 34 | 5 | 0 | 59.7 |
| 21:01 | 30 | -68 / -68 | 121 / 81 | 81 / 6 | 19 | 4 | 0 | 60.0 |
| 21:02 | 29 | -68 / -68 | 121 / 81 | 108 / 40 | 106 | 3 | 0 | 59.8 |
| 21:03 | 30 | -68 / -68 | 121 / 108 | 108 / 40 | 20 | 5 | 0 | 59.9 |
| 21:04 | 30 | -68 / -69 | 121 / 40 | 94.5 / 27 | 16 | 2 | 0 | 59.8 |
| 21:05 | 6 | -68 / -68 | 121 / 108 | 81 / 27 | 15 | 0 | 0 | 59.6 |

**D** (333 / 333):

| min (UTC) | hb | RSSI med / min dBm | tx med / min Mbps | rx med / min Mbps | post-FEC lost | FEC-unrec | shim drops | fps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21:08 | 28 | -68 / -68 | 108 / 81 | 108 / 6 | 6 | 1 | 0 | 59.8 |
| 21:09 | 28 | -68 / -68 | 121 / 81 | 108 / 6 | 3,176 | 2 | 3,678 | 56.0 |
| 21:10 | 29 | -69 / -69 | 121 / 108 | 108 / 6 | 34 | 4 | 0 | 59.1 |
| 21:11 | 27 | -68 / -68 | 121 / 108 | 81 / 6 | 3,377 | 15 | 3,781 | 55.8 |
| 21:12 | 30 | -68 / -68 | 121 / 81 | 108 / 54 | 38 | 6 | 0 | 59.7 |
| 21:13 | 28 | -69 / -69 | 121 / 81 | 108 / 6 | 3,603 | 16 | 3,782 | 54.8 |
| **21:14** | 29 | -68 / -68 | 121 / 108 | 108 / 6 | **2,052** | 41 | **0** | 55.3 |
| 21:15 | 28 | -68 / -69 | 121 / 108 | 94.5 / 81 | 3,351 | 11 | 3,681 | 56.2 |
| **21:16** | 29 | -69 / -69 | 108 / 108 | 108 / 6 | **748** | 38 | **0** | 57.6 |
| 21:17 | 28 | -68 / -69 | 121 / 108 | 108 / 6 | 3,426 | 8 | 3,840 | 56.1 |
| 21:18 | 29 | -68 / -69 | 121 / 54 | 108 / 27 | 115 | 11 | 0 | 59.6 |
| **21:19** | 21 | -69 / -69 | 121 / 81 | 108 / 6 | **1,091** | 37 | **0** | 56.8 |

**E-off** (343 / 343):

| min (UTC) | hb | RSSI med / min dBm | tx med / min Mbps | rx med / min Mbps | post-FEC lost | FEC-unrec | shim drops | fps | frames after a dropped ref | held | episodes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21:22 | 13 | -68 / -68 | 108 / 81 | 81 / 54 | 15 | 5 | 277 | 60.3 | 48 | 0 | 9 |
| 21:23 | 29 | -68 / -68 | 121 / 108 | 108 / 27 | 126 | 19 | 564 | 59.3 | 308 | 0 | 40 |
| 21:24 | 30 | -68 / -68 | 121 / 81 | 108 / 6 | 206 | 38 | 572 | 57.8 | 516 | 0 | 59 |
| 21:25 | 29 | -68 / -69 | 121 / 108 | 81 / 6 | 338 | 35 | 555 | 59.2 | 486 | 0 | 37 |
| 21:26 | 28 | -68 / -69 | 108 / 108 | 108 / 54 | 489 | 39 | 569 | 56.4 | 642 | 0 | 43 |
| **21:27** | 30 | -68 / -69 | 121 / 81 | 108 / 54 | **1,649** | 44 | 540 | 57.1 | 350 | 0 | 37 |
| 21:28 | 30 | -69 / -69 | 121 / 81 | 81 / 6 | 595 | 38 | 570 | 58.2 | 572 | 0 | 41 |
| 21:29 | 29 | -68 / -69 | 121 / 81 | 108 / 81 | 469 | 33 | 579 | 58.4 | 513 | 0 | 38 |
| **21:30** | 30 | -68 / -69 | 121 / 81 | 81 / 6 | **1,106** | 63 | 579 | 57.2 | 718 | 0 | 73 |
| 21:31 | 29 | -68 / -69 | 121 / 81 | 81 / 6 | 291 | 24 | 482 | 58.4 | 427 | 0 | 46 |
| 21:32 | 29 | -68 / -68 | 121 / 108 | 108 / 6 | 139 | 24 | 616 | 59.3 | 393 | 0 | 39 |
| 21:33 | 30 | -68 / -69 | 121 / 108 | 108 / 6 | 286 | 30 | 605 | 58.4 | 333 | 0 | 49 |
| 21:34 | 7 | -68 / -68 | 121 / 121 | 108 / 81 | 4 | 1 | 118 | 59.5 | 18 | 0 | 3 |

**E-on** (345 / 345):

| min (UTC) | hb | RSSI med / min dBm | tx med / min Mbps | rx med / min Mbps | post-FEC lost | FEC-unrec | shim drops | fps | frames after a dropped ref | held | episodes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21:37 | 25 | -68 / -68 | 121 / 108 | 108 / 6 | 43 | 11 | 524 | 55.0 | 216 | 216 | 24 |
| 21:38 | 29 | -68 / -68 | 121 / 108 | 108 / 6 | 83 | 25 | 549 | 53.1 | 357 | 357 | 40 |
| 21:39 | 30 | -68 / -68 | 121 / 81 | 108 / 27 | 75 | 25 | 553 | 55.6 | 223 | 223 | 28 |
| 21:40 | 30 | -68 / -68 | 121 / 108 | 81 / 6 | 64 | 14 | 604 | 56.0 | 204 | 204 | 30 |
| 21:41 | 30 | -68 / -68 | 121 / 81 | 108 / 6 | 83 | 21 | 527 | 54.5 | 286 | 286 | 38 |
| **21:42** | 29 | -68 / -69 | **81 / 27** | 108 / 6 | 97 | 17 | 541 | 55.0 | 244 | 244 | 38 |
| **21:43** | 29 | -68 / -68 | 121 / **27** | 108 / 27 | 93 | 22 | 597 | 53.1 | 344 | 344 | 39 |
| 21:44 | 30 | -68 / -68 | 121 / 81 | 108 / 54 | 49 | 13 | 575 | 57.0 | 151 | 151 | 25 |
| 21:45 | 30 | -68 / -68 | 121 / 108 | 108 / 27 | 73 | 23 | 546 | 54.9 | 269 | 269 | 35 |
| 21:46 | 30 | -68 / -68 | 108 / 81 | 81 / 54 | 77 | 22 | 521 | 54.8 | 274 | 274 | 35 |
| 21:47 | 30 | -68 / -68 | 108 / 54 | 108 / 27 | 69 | 21 | 624 | 54.6 | 276 | 276 | 37 |
| 21:48 | 23 | -68 / -69 | 121 / 108 | 108 / 54 | 30 | 7 | 472 | 56.8 | 127 | 127 | 21 |

**Beside the events** (the heartbeat before → after, and the min over ±10 s; `record/link_coincidence.txt` gives the
base rates):
- **Every blackout (A, B, D; 16):** RSSI unchanged to ±1 dB (−67…−69) before and after. tx and rx before / after are in
  the per-blackout tables, all within their usual 81-216.
- **Every silence ≥ 500 ms outside the blackouts:**
  - A 20:27:56.96Z (569 ms) and 20:29:17.17Z / 20:29:17.78Z (609 / 1,295 ms, the false hold): RSSI −67, tx ≥ 108,
    rx ≥ 40-81 over ±10 s;
  - B 20:41:51.53Z (691 ms): RSSI −69 min, rx 27 once;
  - E-on: 14 silences, **12 of them in 21:42:23-21:43:03Z** (§ below), plus 21:43:21.90Z (612 ms) and 21:47:49.22Z
    (550 ms; tx 54, rx 27 min).
- **The house-flap stretches** (post-FEC loss > 500 / min with no shim drop):
  - **D 21:14 (2,052), 21:16 (748), 21:19 (1,091).** These are bursts inside the minute: 21:14:43-55Z ~1,830 lost
    (one resync); 21:16:41-58Z ~490; 21:19:17-21Z ~870.
  - Beside them: RSSI −68 / −69 (the cell's usual); tx ≥ 108; rx dips to 6 / 27 in single heartbeats (3-16 % of the
    heartbeats within ±10 s, against 5 % run-wide).
  - D 21:16's burst also coincides with a heartbeat 8.7 s late and the 21:16:54Z stall pause.
  - **E-off 21:27** (1,649) and **21:30** (1,106) exceed the shim's 1 % (540-579 drops pre-FEC). The definition's "no
    shim drop" cannot hold under `loss-1`, so they are reported as loss well above the shim's, not as pre-registered
    stretches.
    - 21:27's loss came in 21:26:53-21:27:08Z (lost 1,071 → 2,758). Two heartbeats sent at its start arrived 19.8 s and
      67.8 s late. The control channel logged no silence ≥ 250 ms in that cell before 21:31Z.
    - The link beside it: RSSI −68, tx 108-135, rx 54-135. No dip.
  - **A, B, C, E-on: none.** A's and B's minutes over 500 are all blackout minutes, with the shim's drops.
- **The one coincidence in time.** E-on's uplink-silence cluster, 21:42:20-21:43:25Z (42 of the cell's 61 silences ≥
  250 ms; 36 of its 145 hitch seconds), coincides with the onn's **tx link rate falling**:
  - 121 → 81 → 54 → 27 Mbps, 52 % of its heartbeats ≤ 54 Mbps against 1.0 % in the rest of E-on and 0.9 % outside all
    events;
  - RSSI −67…−69 (unchanged); rx unchanged; downlink loss unchanged (97 / 93 lost per minute);
  - two heartbeats arrived 3.0-4.5 s late. The guard's held frames did not jump.
- **Base rates** (2,030 heartbeats): RSSI ≤ −69 11.7 %, tx ≤ 54 1.7 %, rx ≤ 27 5.0 %. Within ±10 s of all events:
  37.5 % / 6.6 % / 6.2 %, against the rest's 7.4 % / 0.9 % / 4.8 %.
  - The RSSI difference is 1 dB (−68 vs −69), at the report's 1-dB resolution.
  - The tx difference is E-on's cluster.
  - The rx difference is within its base rate.
- **Stated as coincidence in time, not cause.** This run cannot say what moved the tx rate or caused the downlink loss
  bursts. The Opal saw neither (no station on `wlan1`).

## 8. The pre-registered expectations, the reading and the CONFIRMED rule, as hashed

| written beforehand | read | met? |
| --- | --- | --- |
| A: net ≤ 5 per blackout | 47.5-48.7 (core-running; `--net` the same: no rewind credited) | **not met** |
| A: one hold | one per blackout (6 / 6), 0.95-0.97 s | met |
| A: one resume ≤ 1 heartbeat after the return | one resume per blackout (5 / 5; b6 ended with the session); 1 heartbeat between in 4, 2 in 1; **2.06-3.13 s** after the return (B8's ≤ ~2.3 s in 1 of 5); via `hold_return_stall` in 1 of 5 | **not met** |
| A: the rewind's after-check PLAYING in every blackout | PAUSED in 6 / 6 (and the false hold's) | **not met** |
| B: the pause 0.40-0.46 s after the client's last frame in every blackout | 428, 428, 420, 426, **484** ms | **not met** (4 / 5) |
| C: false holds ≤ 1 / 10 min and stall pauses 0 | 0 and 0 | **met** |
| D: the state load plays in every blackout | 5 / 5 (acked, logged "Loading state", no failure, the picture at 56.5-60.7 fps) | **met** |
| D: net ≤ 30 | 24 (B9's row); 13-14 (core-running − restored); the `--net` reader 48-50 does not read `state` | **met** (disclosed) |
| E: the counter ~300 / min off | 462 / min (the house's loss in 2 minutes; 308-718 per minute) | not as stated (1.5×) |
| E: held ≈ the counter on | 3,010 = 3,010 | **met** |
| E: timeouts ≈ 0 | 0 | **met** |
| the link: a silence ≥ 500 ms or a flap coincides with an RSSI dip, a link-rate drop or an Opal retry rise | E-on's silence cluster ↔ a tx-rate drop (27-81 Mbps); D's and E-off's loss stretches ↔ no RSSI dip, no rx dip above base rate; the Opal: no station | reported (coincidence only) |

**The reading, applied:**
- **A, B and C did not all meet their bars (A and B did not).** So **the stack is not a candidate for the user's
  adoption call on SNES.**
  - Its costs would have been: the frozen picture during a hold; ~1 s (59 frames) of unattended game at H 950; snes9x's
    rewind buffer (61 MB, ~+0.3 points per R2's f2); and here a ~1-s rewind before every resume.
- **PS1 joins only if** D's load plays and its hitch cost is acceptable. D's load played, but it would join a stack that
  is not a candidate. **No PS1 question arises.** D's cost is stated for when B returns it:
  - 71.2 hitch s / 10 min outside the blackouts on a cell with the house's own bursts, so not separable here;
  - +56-58 MB RSS against E's PS1 cells; a 16-MB state written per silence ≥ 400 ms;
  - the client's gate stalls 1.8-11.8 s after the load.
- **E-on held the counter's frames with timeouts 0, so the loss guard is a candidate.** Its costs:
  - freezes to the next IDR, up to 501 ms here (B10's ≤ 250 ms by the GOP; the cap 600), instead of corrupted frames;
  - hitch seconds 125.7 against E-off's 68.8 per 10 min (104.3 outside the 21:42 house cluster);
  - rendered 55.2 against 57.8 fps;
  - the keyframe requests force nothing (no runtime IDR path); one 24-byte request per episode;
  - **E-on's uplink silences** 54.5 against 4.5 per 10 min (18.8 outside the cluster), coincident, not attributed;
  - the user has not seen it ("no watch").
- **The link findings are for the next task** (§10), not read here.

**The CONFIRMED APK:** every cell was valid. The property-empty behaviours read as today:
- E-off's guard at `count` counted only: 0 held, 0 requests sent;
- A-D (`loss_guard` empty) reported no loss-guard key;
- E (`stall_signal` empty) reported no stall-signal key.

So **`bf5114a2…cf73` stays and is CONFIRMED** (CL-B7's rule). `cb0935c8…` is preserved at
`PrivyHub/app/build/bench_r3_preserved/app-debug.apk`.

## 9. The pin (patch, uncommitted)

- **`tools/e1_suite.py` `EXPECT_APK`**, **`tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`** and its test now read
  `bf5114a2d257f1246374b05e3d79b24f0382afe1c66b2c6acb3a37fa6e58cf73`, each with a comment naming the predecessor.
  - Patch: `record/bench_r3_hash.diff`, `record/predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`.
  - The predecessor `e1_suite.py` = the pre-registration's hash `d95e7a82…`.
- **Tests** (`record/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `git diff --check` clean.

## 10. What the data hands back (the user's call which; nothing here is built)

- **To B — snes9x's hold-path rewind reads PAUSED after the rewind in 7 / 7.**
  - Yet B's 2-3-frame `stall_end` rewinds on the same core passed the after-check 4 / 5. R2's PSX HW failed the same way
    118 / 123.
  - So the hold path's method or its after-check, not the core, is where to look.
  - The 59-frame per-frame rewind also takes ~0.97 s, which puts A's resume 2-3 s after the return.
  - The carry's `stall_frames` read 0 throughout, and the gate's ready resumed first in 4 / 5.
- **To B — `@down`:** each blackout's pause is resumed by recovery v2 with an encoder restart (3 / 5) and a ladder
  step, not by `stall_end`. The in-gate pause after it is the one that gets the rewind.
- **To B — the PS1 `state` path worked where rewind did not:** 34-36 frames restored and net 24 per blackout, resumed by
  B8. Whether the same path should serve SNES is B's question.
- **To B — the loss guard:** max wait 501 ms (an IDR lost too); E-on's uplink silences and hitch rate. If the user
  adopts, the property resets on a reboot, so the mechanism to make it the default is B's.
- **The link — next task (session A, read-only).** The onn is on 2.4 GHz channel 1, where the Opal's `wlan0` is. The
  sampler read `wlan1`.
  1. One read-only `iw dev wlan0 station dump` through `o1_redact.py` with no stream, to say whether the onn is on the
     Opal at all.
  2. If it is, the O1 sampler on `wlan0` beside one clean stream: retries / signal / rate for the onn's station per 5
     min, beside the link report.
  3. Then the user's call whether to try the onn on 5 GHz (`wlan1`), the band O1 found it on, as a cell.
  - The tx-rate fall in E-on's cluster is the one thing to watch for on the Opal's side (its tx retries to the onn).

## 11. State at the end (the user's checks)

- **`--check`: ok** on the eight lines, **APK CONFIRMED** (`record/check_end.json`); no `e3_flag.conf`, no
  `e4_constraint.conf`; no game, RetroArch or encoder; `adb` true.
- **The onn reads `bf5114a2…cf73`,** paired (identity v2, the device secret present, its id in the hub's store, 1
  device; `record/client_end.json`).
- **The properties read empty:** `wifi_lock`, `stall_signal`, `link_report`, `loss_guard`, `opus_decode`
  (`record/properties_end.json`).
- **Units:** only `privyhub-companion` (the bench unit collected).

## 12. Files

- **`bench_r3_2026-10-22/record/`:**
  - the readers: `bench_r3_record_read.py`, `outside_reads.py`;
  - their output: `record_read.json`, `record_read_console.txt`, `outside_reads.json`, `link_coincidence.txt`;
  - the generated tables: `link_per_minute.md`, `blackouts.md`;
  - `unattended_<cell>[_net].json`;
  - `logs/<cell>/` (the five logs + `decoder_sessions/`), `logs_whole_run/` (heartbeat, control gaps, recovery,
    20:19-21:53Z);
  - the pin: `bench_r3_hash.diff`, `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `tests.txt`;
  - the end state: `check_end.json`, `properties_end.json`, `client_end.json`;
  - `redact_check.txt`, `manifest.sha256`.
- **The driver's files (unchanged):** `cells.jsonl`, `bench_r3_state.json`, `runs/`, `opal/`, and the launch files.
- **`logs/bench_r3_git_status.txt`.**
- **Not done:** no sudo, no nft. The Opal was not touched by the record. adb was used for state reads only.
- **Not written:** no address or identifier.
- **Nothing** fetched, deleted, adopted or committed.
