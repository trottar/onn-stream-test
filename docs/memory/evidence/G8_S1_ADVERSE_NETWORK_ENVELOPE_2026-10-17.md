---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 1dab25d (the G8-S1 resume, session B's G5-S3 / G5-S4 / G4-P2 work and this record uncommitted beside it; B's files not touched)
supersedes: G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-16.md (the PARTIAL record, 5 of 22 cells)
---

# G8-S1 — the adverse-network envelope (final)

**Classification: MEASURED — 18 of 22 cells valid.** The four cap cells (17-20, `cap-6000` and `cap-4500`, off and
on) are `no_play`: each made three suite attempts and none reached PLAYING (§5). In every valid cell, every host gate
was met.

**Code version (§3):**
- Cells 1-5 ran the pre-registered modules.
- From cell 6's attempt 2 onward, the companion ran session B's edited files, with B's flags absent. Cell 6's counted
  run is its attempt 3.
- That is bounded only by B's in-process flag-absent proofs. Nothing is claimed beyond them.

Everything link-side is reported, not judged: this is the envelope, and it has no pass or fail. Measurement only;
nothing adopted; nothing committed. The driver ended by itself and was not relaunched.

**This record supersedes the PARTIAL record of 2026-10-16** (`G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-16.md`). That
record's five rows reappear here unchanged.

- **Written only from the driver's files:** `cells.jsonl`, `runs/<cell>/` (the suite's `summary.json`,
  `summary_failed_attempt<n>.json`, `suite.log`, `decisions.jsonl`, `status_poll.jsonl`, `recovery.jsonl`,
  `gaps.jsonl`), `wan_poll_run1.jsonl` and `impairment_run1.jsonl`.
  - Plus, for the cap cells only, the companion's journal over their span, reduced by `g8_s1_cap_log_read.py` into
    `cap_cells_companion_log.txt` (masked).
- **Read against `g8_s1_preregistration.txt`** as hashed: sha256 `b2e02fa0…dcf73`, re-read at the close and unchanged.
- **The reading script:** `g8_s1_analysis.py`, extended from the partial pass (the partial's reading,
  `g8_s1_table.md` and `g8_s1_cells_read.json`, stays). Its outputs: `g8_s1_table_final.md` (every table here, in full),
  `g8_s1_cells_read_final.json`, and `validity.json` (replaced).
- **Task:** `handoffs/G8-S1_FINAL_RECORD_TASK.md`. Earlier records: `G8_S1_LAUNCH_2026-10-16.md`, the PARTIAL record,
  `G8_S1_RESUME_2026-10-17.md`. **Baseline `1dab25d`** (`final_baseline_head.txt`).

## 1. The end and the state

- **The driver ended by itself:**
  - `driver closed (all 22 cells done)` at **2026-10-17T04:30:30Z**;
  - `status.txt`: `doing: EXITED (all 22 cells done)` (copied as `final_status_resume.txt`);
  - `g8_s1_state.json`: `closed_by: all 22 cells done`.
- **The unit was collected:** `systemctl --user status privyhub-g8-s1` reads "could not be found".
- `history.csv` (22 rows plus the header) and `driver.log` were copied in, replacing the stop-time copies.
- **`tools/e3_state.py --check`: ok** (`check_final.json`): seven adopted lines, no `e3_flag.conf` or
  `e4_constraint.conf`, no game, no RetroArch or encoder, PS1 files identical, APK CONFIRMED.
  - adb was still connected from the resume.
  - `/session/status`: 1 paired device, 0 sessions.
- **Every cell row:** `flags_absent_after` and `final_flags_absent` true. No `PRIVYHUB_REMOTE*` variable appears in
  any attempt's restart environ.

## 2. The cells

- **Each cell:** E1-PS1-STREAM, `--e2`, a 600-s window, a 120-s gap, the shim `@post-fec,seed=1`. Driver order:
  eleven profiles × off / on.
- **Validity:** 18 valid, 4 `no_play (FAILED)` (17-20). No `busy` and no `profile-not-applied` cell. Every profile
  read **applied** by the pre-registered tolerances, the cap cells included (§5).
- **Suite launch attempts:**
  - **cell 6:** 3 attempts. Two did not reach PLAYING (00:21:54-00:29:27Z, the resume record §4). The third reached
    PLAYING in 10.1 s and is the counted run.
  - **cells 17-20:** 3 attempts each, none reached PLAYING.
  - **every other cell:** 1 attempt.
  - Cell 1's "attempt 2" in the PLAYING column is the suite's launch helper (its second tap), not a replacement.

### 2a. Host side (gates: RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤ 0.2/min, flags absent after)

| cell | suite attempts (failed) | PLAYING (attempt, s) | code version, counted run (§3) | RetroArch | capture | dup+drop /min | gates | host CPU % | companion % of a core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 none off | 1 (0) | 2, 3.0 | pre-registered | 59.999 | 59.988 | 0.10 | all met | 12.85 | 29.55 |
| 02 none on | 1 (0) | 1, 3.1 | pre-registered | 59.999 | 60.038 | 0.10 | all met | 12.61 | 30.17 |
| 03 loss-1 off | 1 (0) | 1, 5.1 | pre-registered | 59.999 | 59.987 | 0.10 | all met | 11.89 | 28.48 |
| 04 loss-1 on | 1 (0) | 1, 3.1 | pre-registered | 59.999 | 59.989 | 0.10 | all met | 12.15 | 29.17 |
| 05 loss-5 off | 1 (0) | 1, 3.1 | pre-registered | 59.999 | 60.039 | 0.10 | all met | 11.87 | 29.19 |
| 06 loss-5 on | 3 (2) | 1, 10.1 | G5-S3 | 59.999 | 59.987 | 0.10 | all met | 13.75 | 26.65 |
| 07 burst-50x20 off | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.999 | 60.040 | 0.10 | all met | 11.85 | 27.46 |
| 08 burst-50x20 on | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.999 | 59.987 | 0.10 | all met | 13.54 | 29.74 |
| 09 delay-50 off | 1 (0) | 1, 8.1 | G5-S3 + G5-S4 | 59.999 | 59.987 | 0.10 | all met | 11.98 | 28.87 |
| 10 delay-50 on | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.999 | 60.038 | 0.10 | all met | 12.04 | 28.83 |
| 11 delay-150 off | 1 (0) | 1, 3.0 | G5-S3 + G5-S4 | 59.999 | 60.037 | 0.10 | all met | 13.06 | 28.53 |
| 12 delay-150 on | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.998 | 59.989 | 0.10 | all met | 12.76 | 29.02 |
| 13 jitter-30 off | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.999 | 59.988 | 0.10 | all met | 12.15 | 29.50 |
| 14 jitter-30 on | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.999 | 59.988 | 0.10 | all met | 11.90 | 28.70 |
| 15 reorder-5 off | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.999 | 59.987 | 0.10 | all met | 13.13 | 29.05 |
| 16 reorder-5 on | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.999 | 59.986 | 0.10 | all met | 13.24 | 29.35 |
| 17 cap-6000 off | 3 (3) | never | G5-S3 + G5-S4 | — | — | — | no window | — | — |
| 18 cap-6000 on | 3 (3) | never | G5-S3 + G5-S4 | — | — | — | no window | — | — |
| 19 cap-4500 off | 3 (3) | never | G5-S3 + G5-S4 | — | — | — | no window | — | — |
| 20 cap-4500 on | 3 (3) | never | G5-S3 + G5-S4 | — | — | — | no window | — | — |
| 21 delay-50+loss-1 off | 1 (0) | 1, 5.1 | G5-S3 + G5-S4 | 59.999 | 59.987 | 0.10 | all met | 13.38 | 29.54 |
| 22 delay-50+loss-1 on | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 | 59.999 | 59.988 | 0.10 | all met | 13.97 | 30.69 |

(For the cap cells, the third attempt is `summary.json` with `status: FAILED`, so all three failed.)

### 2b. The link (reported, not gated)

| cell | loss/min (heartbeat, window) | pre-FEC /min (wan) | post-FEC /min (wan) | FEC recovered packets | unrecoverable groups | rendered | stale /min | spikes ≥ 20 ms /min | resyncs (window) | resyncs (session) | client pauses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 none off | 6.03 | 31.54 | 17.85 | 158 | 23 | 59.959 | 1.03 | 43.28 | 0 | **1** | 0 |
| 02 none on | 3.82 | 8.02 | 4.14 | 45 | 16 | 59.970 | 0.86 | 36.41 | 0 | 0 | 0 |
| 03 loss-1 off | 45.64 | 504.44 | 46.14 | 5,334 | 201 | 59.515 | 3.00 | 45.04 | 0 | 0 | 0 |
| 04 loss-1 on | 68.47 | 524.80 | 65.09 | 5,332 | 212 | 59.440 | 1.55 | 49.49 | 0 | 0 | 0 |
| 05 loss-5 off | 809.49 | 2,511.62 | 809.29 | 19,760 | 3,570 | 52.616 | 1.64 | 39.49 | 0 | 0 | 0 |
| 06 loss-5 on | 700.64 | 4,547.61 | 3,305.42 | 14,476 | 2,669 | 53.802 | 4.68 | 124.38 | **2** | **36** | 0 |
| 07 burst-50x20 off | 940.66 | 843.21 | 829.14 | 163 | 214 | 57.518 | 16.69 | 210.47 | **12** | **11** | 1 |
| 08 burst-50x20 on | 146.24 | 152.20 | 147.88 | 50 | 53 | 59.692 | 1.81 | 90.26 | 0 | 0 | 0 |
| 09 delay-50 off | 18.83 | 29.81 | 19.28 | 123 | 44 | 59.806 | 3.50 | 95.53 | 0 | 0 | 0 |
| 10 delay-50 on | 14.38 | 24.39 | 14.83 | 111 | 39 | 59.908 | 1.29 | 78.15 | 0 | 0 | 0 |
| 11 delay-150 off | 724.80 | 657.04 | 627.85 | 338 | 238 | 58.252 | 7.14 | 186.33 | 10 | 10 | 0 |
| 12 delay-150 on | 356.35 | 331.09 | 308.39 | 263 | 157 | 58.728 | 15.91 | 149.07 | **4** | **3** | 0 |
| 13 jitter-30 off | 337.03 | 356.34 | 286.93 | 804 | 405 | 58.292 | 13.60 | 189.93 | 3 | 3 | 0 |
| 14 jitter-30 on | 91.59 | 148.03 | 95.78 | 606 | 315 | 59.404 | 1.46 | 103.79 | 0 | 0 | 0 |
| 15 reorder-5 off | 19.60 | 393.58 | 18.45 | 4,352 | 28 | 59.770 | 1.12 | 68.81 | 0 | 0 | 0 |
| 16 reorder-5 on | 23.00 | 411.32 | 24.20 | 4,496 | 37 | 59.780 | 2.06 | 74.84 | 0 | 0 | 0 |
| 17 cap-6000 off | — | 13,880.39 | 13,845.89 | 20 | 212 | — | (9.65) | (14.47) | — | (1) | 0 |
| 18 cap-6000 on | — | 11,953.93 | 11,909.02 | 23 | 160 | — | (10.90) | (15.75) | — | (1) | 0 |
| 19 cap-4500 off | — | 17,621.82 | 17,466.49 | 101 | 152 | — | (10.93) | (14.57) | — | (1) | 0 |
| 20 cap-4500 on | — | 17,979.38 | 17,828.88 | 119 | 192 | — | (19.41) | (20.62) | — | (0) | 0 |
| 21 delay-50+loss-1 off | 96.82 | 595.68 | 116.66 | 5,572 | 318 | 59.241 | 1.97 | 62.82 | 0 | **1** | 0 |
| 22 delay-50+loss-1 on | 85.52 | 634.33 | 161.58 | 5,486 | 277 | 59.308 | 1.64 | 64.55 | 0 | **2** | 0 |

**The fields** are as in the PARTIAL record §3b:

- the heartbeat loss covers the 600-s window;
- the pre-FEC, post-FEC and FEC counts come from the last `wan` poll (the session so far);
- stale and spikes come from the client's teardown report.

**The cap rows** have no window. Their `wan` figures are the last poll of the last client session (16-24 reports, §5).
Bracketed figures come from the last attempt's client report.

**The resyncs, both columns:**
- The "window" column is the heartbeat's `stream_resyncs` over the 600-s window. The "session" column is the client's
  `video.sequence_resyncs` over the whole session, warm-up included.
- **They disagree in cells 1 (0 / 1), 6 (2 / 36), 7 (12 / 11), 12 (4 / 3), 21 (0 / 1) and 22 (0 / 2).** In cell 6 the
  session ran through a 52.6-s recovery before the window (§2d), and the 36 are mostly outside the window. The files
  give the two spans, not when each resync happened.
- In cell 7 the window counted one more than the session. The two counters come from different sources, heartbeat and
  teardown report; the files do not reconcile them. Reported, not explained.

### 2c. The ladder, the rules, the classifier, the shim

| cell | rung kbps (status polls) | the ladder's rung path (`decisions.jsonl`, acted transitions) | rules suggestions, by rule (the driver's line count) | `wan` class | windows by primary class (non-zero) | shim in / out | dropped: loss / burst / queue | delayed | reordered | queue max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 none off | 7000 (69) | none | 0 (0), off | lossy | clean 41, lossy 27, starved 1 | 665,785 / 665,785 | 0 / 0 / 0 | 0 | 0 | 48 |
| 02 none on | 7000 (69) | none | **0** (0) | clean | clean 53, lossy 15, starved 1 | 665,626 / 665,626 | 0 / 0 / 0 | 0 | 0 | 41 |
| 03 loss-1 off | 7000 (69) | none | 0 (0), off | lossy | lossy 63, starved 4, clean 2 | 667,286 / 660,672 | 6,614 / 0 / 0 | 0 | 0 | 39 |
| 04 loss-1 on | 7000 (69) | none | **0** (0) | lossy | lossy 64, starved 2, clean 3 | 665,602 / 658,996 | 6,606 / 0 / 0 | 0 | 0 | 42 |
| 05 loss-5 off | 7000 (69) | none | 0 (0), off | lossy | lossy 68, starved 1 | 665,619 / 632,441 | 33,178 / 0 / 0 | 0 | 0 | 37 |
| 06 loss-5 on | 7000 (10), **5000 (59)** | **7000→5000, reason `recovery_escalation`**, class FALLBACK, 00:33:38Z (in window) | **296**: R5.1 206, R1.2 86, R3.1 2, R1.1 2 (297) | path-changed | lossy 59, starved 4, capacity-limited 3, path-changed 1 | 634,606 / 602,889 | 31,717 / 0 / 0 | 0 | 0 | 52 |
| 07 burst-50x20 off | 7000 (19), **6000 (50)** | **7000→6000, reason `capacity_mild`**, class ROUTINE, 00:49:35Z (in window) | 0 (0), off | path-changed | lossy 39, clean 18, starved 8, path-changed 1 | 605,715 / 603,965 | 0 / 1,750 / 0 | 0 | 0 | 42 |
| 08 burst-50x20 on | 7000 (69) | none | **0** (0) | lossy | lossy 49, clean 18, starved 2 | 665,747 / 663,997 | 0 / 1,750 / 0 | 0 | 0 | 42 |
| 09 delay-50 off | 7000 (69) | none | 0 (0), off | lossy | lossy 34, clean 32, starved 3 | 668,991 / 668,974 | 0 / 0 / 0 | 668,991 | 0 | 237 |
| 10 delay-50 on | 7000 (69) | none | **0** (0) | lossy | clean 38, lossy 30, starved 1 | 665,622 / 665,616 | 0 / 0 / 0 | 665,622 | 0 | 245 |
| 11 delay-150 off | 7000 (69) | none | 0 (0), off | lossy | lossy 43, clean 11, starved 8 | 669,637 / 669,483 | 0 / 0 / 0 | 669,637 | 0 | 582 |
| 12 delay-150 on | 7000 (46), **6000 (23)** | **7000→6000, reason `wan_rules`** (R2.1), class ROUTINE, 02:06:05Z (in window) | **112**: R5.1 89, R2.1 23 (133) | path-changed | lossy 34, clean 24, starved 7, path-changed 1 | 637,818 / 637,609 | 0 / 0 / 0 | 637,818 | 0 | 588 |
| 13 jitter-30 off | 7000 (69) | none | 0 (0), off | lossy | lossy 53, starved 9, clean 4 | 664,638 / 664,637 | 0 / 0 / 0 | 664,638 | 0 | 171 |
| 14 jitter-30 on | 7000 (69) | none | **0** (0) | latency-limited | lossy 64, starved 2, clean 2, latency-limited 1 | 665,472 / 665,471 | 0 / 0 / 0 | 665,472 | 0 | 148 |
| 15 reorder-5 off | 7000 (69) | none | 0 (0), off | lossy | lossy 45, clean 23, starved 1 | 666,281 / 666,281 | 0 / 0 / 0 | 0 | 31,657 | 44 |
| 16 reorder-5 on | 7000 (69) | none | **0** (0) | lossy | lossy 47, clean 21, starved 1 | 666,228 / 666,228 | 0 / 0 / 0 | 0 | 31,654 | 41 |
| 17 cap-6000 off | — (no polls) | — (no `decisions.jsonl`) | — | capacity-limited | capacity-limited 2, starved 1 | 304,866 / 219,609 | 0 / 0 / 84,913 | 0 | 0 | 73 |
| 18 cap-6000 on | — | — | — | capacity-limited | capacity-limited 2, starved 1 | 292,555 / 213,949 | 0 / 0 / 78,378 | 0 | 0 | 69 |
| 19 cap-4500 off | — | — | — | capacity-limited | capacity-limited 3, starved 1 | 296,996 / 165,208 | 0 / 0 / 131,524 | 0 | 0 | 56 |
| 20 cap-4500 on | — | — | — | starved | capacity-limited 3, starved 1 | 244,806 / 136,074 | 0 / 0 / 108,547 | 0 | 0 | 56 |
| 21 delay-50+loss-1 off | 7000 (69) | none | 0 (0), off | lossy | lossy 66, starved 2, clean 1 | 666,954 / 660,338 | 6,612 / 0 / 0 | 660,342 | 0 | 239 |
| 22 delay-50+loss-1 on | 7000 (69) | none | **0** (0) | lossy | lossy 67, starved 1, clean 1 | 664,715 / 658,108 | 6,599 / 0 / 0 | 658,116 | 0 | 240 |

- **The two counts of the rules:**
  - The first count is `decisions.jsonl` rows with `event: wan_suggestion` and `source: wan_rules`.
  - The driver's count, in brackets, counts every line containing `"wan_rules"`. That adds:
    - cell 6: 1 `refused` row;
    - cell 12: 19 `refused` rows (`reason: hold_down`, trigger `wan_rules`), the `transition` row and 1 `sample`.
  - Both counts are kept.
- **The cap cells' shim figures** cover all three attempts: six stream starts each, five in cell 20 (§5).
- **The ladder's rung path** is the acted `transition` rows. Each was followed about 1 s later by a `transition_done`
  with `error: null`, and the status polls agree with the path.

### 2d. Session loss and recovery events

| cell | `recovery.jsonl` rows | `key.recovery` pauses (controller / client / other) | `gaps.jsonl` rows | longest gap ms |
| --- | --- | --- | --- | --- |
| 01 / 02 none | 0 / 0 | 0 / 0 / 0 | 0 / 0 | — |
| 03 / 04 loss-1 | 0 / 0 | 0 / 0 / 0 | 1 / 7 | 292 / 953 |
| 05 / 06 loss-5 | 0 / **1** | 0 / 0 / 0 | 0 / 66 | — / 709 |
| 07 / 08 burst-50x20 | **2** / 0 | 0 / **1** / 0, then 0 / 0 / 0 | 134 / 8 | **3,697** / 823 |
| 09 / 10 delay-50 | 0 / 0 | 0 / 0 / 0 | 21 / 7 | 910 / 340 |
| 11 / 12 delay-150 | 0 / 0 | 0 / 0 / 0 | 204 / 82 | 2,426 / 2,485 |
| 13 / 14 jitter-30 | 0 / 0 | 0 / 0 / 0 | 127 / 10 | 1,812 / 749 |
| 15 / 16 reorder-5 | 0 / 0 | 0 / 0 / 0 | 14 / 7 | 416 / 368 |
| 17-20 cap | 0 (no window) | — | 0 | — |
| 21 / 22 delay-50+loss-1 | 0 / 0 | 0 / 0 / 0 | 2 / 11 | 319 / 376 |

- **Cell 6:**
  - `recovery.jsonl` holds one row: `resumed` at 00:33:37.457Z from `PAUSED_RECOVERING`, `recovering_ms` 52,555,
    `restarts` 2. The pause began before the window (00:33:29Z) and is not in the window's rows.
  - 1.1 s later the ladder took 7000→5000 (`recovery_escalation`).
- **Cell 7:**
  - one **client pause**, a `desync_pause` with trigger `client_output_silence`, at 00:48:37Z (in window). It resumed
    after 22.1 s, with 0 restarts.
  - 36 s after the resume, the ladder took 7000→6000 (`capacity_mild`).
- **Gaps:** `gaps.jsonl` is the controller-input gap log (client → host). The shim impairs video only. No gap reached
  a controller pause.
- **No session was lost** in a valid cell.

### 2e. The shim's cost

| cell | stream starts (segments) | shim seconds | shim % of a core (Σ cpu_s / Σ seconds) | the driver's figure |
| --- | --- | --- | --- | --- |
| 01-05 | 1 | 698-700 | 2.89-3.23 | same |
| 06 loss-5 on | 3 | 822 | 2.61 | 3.03 |
| 07-16, 21-22 | 1 | 697-702 | 2.71-3.90 (jitter-30 3.84 / 3.90 the highest) | same (±0.001) |
| 17 / 18 cap-6000 | 6 | 326 / 328 | **5.32 / 5.38** | 27.97 / 28.48 |
| 19 / 20 cap-4500 | 6 / 5 | 324 / 266 | **4.45 / 4.65** | 24.04 / 19.94 |

- **The driver's `shim_cpu_pct_core` divides the summed CPU by the largest `t_s`.** That is right for a single stream
  start, but `t_s` restarts at each stream start, so for the multi-start cap cells (and cell 6) it overstates the cost.
  The corrected figures are in the fourth column.
- With one stream start, the shim cost 2.6-3.9 % of a core against G8-P1's in-process 2.1-7.0 %. The cap stage, under
  sustained tail-drop, cost 4.5-5.4 %.

## 3. The code version, disclosed

- **The version per run** comes from each attempt's `started_utc` against the edit times of B's companion files
  (`G8_S1_RESUME_2026-10-17.md` §5; the mtimes re-read at this close):
  - **pre-registered:** cells 1-5 and cell 6's attempt 1 (00:21:54Z, before B's first edit at 00:22:39Z). These
    modules match `tools_at_preregistration_sha256.txt`.
  - **G5-S3's edits**, loaded from cell 6's attempt 2 onward:
    - `companion/wan_adaptation.py` (00:23:05Z);
    - `companion/adaptive_bitrate_live.py` (00:22:39Z);
    - `companion/plugins/games.py` (00:22:43Z);
    - `companion/diagnostics/c3_linux_actuator_probe.py` (00:22:55Z; the actuator probe, loaded at the first
      transition; B's record lists it);
    - the new `companion/remote_ladder.py` (00:23:10Z).

    Cell 6's attempts 2 and 3 (companion starts 00:25:42Z and 00:29:27Z) ran this version. Attempt 3 is the counted
    run.
  - **G5-S3 + G5-S4's edits**, loaded from cell 7 onward (companion start 00:44:06Z): G5-S4 edited
    `adaptive_bitrate_live.py` and `remote_ladder.py` again (00:39:00Z) and added `companion/remote_cap.py`
    (00:38:38Z). Cells 7-22 ran this version.
- **B's flags were absent all night:** `PRIVYHUB_REMOTE_LADDER` (G5-S3) and `PRIVYHUB_REMOTE_RUNG_CAP` (G5-S4). No
  `PRIVYHUB_REMOTE*` appears in any attempt's restart environ, and in every valid cell the environ under load held 9 lines off and 10
  on (the cap cells never reached that read).
- **G4-P2's `tools/e1_remote.py` edit (00:48Z) was not loaded.** The suite imports it only with `--remote`, and the
  wrapper does not pass it.
- **The pre-registered tool set otherwise held:** the pre-registration, the wrapper, `tools/e1_suite.py`,
  `companion/impairment.py` and `companion/wan_telemetry.py` are unchanged at the close. The driver carries the
  resume's one disclosed CAP change. See `tools_at_record_close_sha256.txt`.
- **The hashes at the close, beside the version the night started on** (full values in `tools_at_record_close_sha256.txt`):

  | file | at the start | at the close |
  | --- | --- | --- |
  | `companion/wan_adaptation.py` | `e28f6b44…` (**pre-registered**) | `9a9fe444…` |
  | `companion/adaptive_bitrate_live.py` | `58f247a5…` (HEAD) | `4868bc44…` |
  | `companion/plugins/games.py` | `d72e5f8e…` (HEAD) | `5cac0d65…` |
  | `companion/diagnostics/c3_linux_actuator_probe.py` | `8f64787c…` (HEAD) | `e9d4bf4e…` |
  | `companion/remote_ladder.py` | (new) | `1094f5de…` |
  | `companion/remote_cap.py` | (new) | `f0584eed…` |

  "HEAD" is `1dab25d`. These files are unchanged between the launch baseline `64d9489` and `1dab25d`.
- **What bounds it:** B's flag-absent proof (`G5_S3_REMOTE_LADDER_2026-10-17.md` §2, `flag_absent_proof.py` →
  `flag_absent_output.md`), re-run by G5-S4 with the cap code present (`G5_S4_REMOTE_RUNG_CAP_2026-10-17.md`). Its
  exact scope:
  - **the actuator:** HEAD's (from git) vs the edited `c3_linux_actuator_probe.py`, 4 entry points × 8 current levels
    × 8 targets (3000…12600, 4000 included). It compares the payload, argv, exception and level after: **200 / 200
    identical**.
  - **the games plugin:** HEAD's vs the edited `handle_post_request("native-stream-start")` with the same stubs, plus
    `_adaptive_bitrate_context`. Three cases (started; game inactive; start fails): **3 / 3 identical**.
  - **the ladder and the rules:** G5-S2's `replay.py`, unchanged, re-run.
    - Four recorded runs' decisions were reproduced **exactly**.
    - HEAD vs the edited controller: **identical** (738 / 780 / 414 / 738 rows).
    - Its WAN-rules tables are equal to G5-S2's recorded ones.
- **What it does not cover:**
  - The proofs are **in process**, on stubs and on replays of earlier recorded sessions (G5-S2's runs).
  - **No live session under the shim's profiles was replayed or compared.** The night's own on-arm decisions were not
    re-run against HEAD.
  - Their timing on the live companion was not compared.
  - The proof does not cover the plugin's other request paths, nor any interaction with the shim.
  - So the on-arm cells' `wan_suggestion` rows (cells 6 and 12 and the zero rows) come from `wan_adaptation.py` as
    edited. By that replay its rules output is equivalent to G5-S2's on G5-S2's inputs. **This record claims nothing
    beyond that.**
  - Cells 7-22's ladder rows (cell 7's `capacity_mild` included) come from the edited `adaptive_bitrate_live.py`, with
    the same bound.
- **No re-run is proposed by this record.** A re-run of the on-arm cells on committed code is the user's option (§8).
- **The lesson, one line:** a measurement that enables a flag must not run while that flag's module is being edited.

## 4. The pre-registered comparisons

### (i) `none` against CL-B3's R1 and W (the shim's cost on the stream)

| run | host CPU % | companion % of a core | shim % of a core | rendered | loss/min (heartbeat) | resyncs (window) | rung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CL-B3 R1 (no shim, no telemetry flag) | 11.569 | 24.80 | — | 59.674 | 80.05 | 0 | 7000 |
| CL-B3 W (no shim, `WAN_TELEMETRY=1`) | 11.593 | 25.44 | — | 59.795 | 60.32 | 3 | 7000 |
| G8-S1 01 none off (shim + telemetry) | 12.847 | 29.55 | 3.14 | 59.959 | 6.03 | 0 | 7000 |
| G8-S1 02 none on (shim + telemetry + rules) | 12.611 | 30.17 | 3.23 | 59.970 | 3.82 | 0 | 7000 |

This is unchanged from the PARTIAL record (both `none` cells ran on 10-16). Against W, host CPU is +1.25 / +1.02
points and the companion +4.11 / +4.73 points of a core, the shim's own 3.1-3.2 included. These are separate runs,
hours apart.

### (ii) Off against on, per profile (stated, not judged)

| profile | rules suggestions (on): rule, suggestion → ladder result | rung path: off / on | rendered: off → on | stale /min | loss/min (heartbeat) | post-FEC /min (wan) |
| --- | --- | --- | --- | --- | --- | --- |
| none | 0 | none / none | 59.959 → 59.970 | 1.03 → 0.86 | 6.03 → 3.82 | 17.85 → 4.14 |
| loss-1 | 0 | none / none | 59.515 → 59.440 | 3.00 → 1.55 | 45.64 → 68.47 | 46.14 → 65.09 |
| loss-5 | R5.1 `no_step_up` 206; R1.2 `no_step_up` 86; R1.1 `hold` 2 (all → none); **R3.1 `step_down` 2**: 1 → `refused:guard`, 1 → `transition` | none / **7000→5000 (`recovery_escalation`)** | 52.616 → 53.802 | 1.64 → 4.68 | 809.49 → 700.64 | 809.29 → 3,305.42 |
| burst-50x20 | 0 | **7000→6000 (`capacity_mild`)** / none | 57.518 → 59.692 | 16.69 → 1.81 | 940.66 → 146.24 | 829.14 → 147.88 |
| delay-50 | 0 | none / none | 59.806 → 59.908 | 3.50 → 1.29 | 18.83 → 14.38 | 19.28 → 14.83 |
| delay-150 | R5.1 `no_step_up` 89 (→ none); **R2.1 `step_down` 23**: 1 → `transition`, 3 → none, 19 → `refused:hold_down` | none / **7000→6000 (`wan_rules`)** | 58.252 → 58.728 | 7.14 → 15.91 | 724.80 → 356.35 | 627.85 → 308.39 |
| jitter-30 | 0 | none / none | 58.292 → 59.404 | 13.60 → 1.46 | 337.03 → 91.59 | 286.93 → 95.78 |
| reorder-5 | 0 | none / none | 59.770 → 59.780 | 1.12 → 2.06 | 19.60 → 23.00 | 18.45 → 24.20 |
| cap-6000 | no window | — / — | — | — | — | 13,845.89 / 11,909.02 (last session) |
| cap-4500 | no window | — / — | — | — | — | 17,466.49 / 17,828.88 (last session) |
| delay-50+loss-1 | 0 | none / none | 59.241 → 59.308 | 1.97 → 1.64 | 96.82 → 85.52 | 116.66 → 161.58 |

**The three transitions, with the trigger the decisions log names:**

- **Cell 6 (loss-5, on):**
  - At 00:33:30.057Z the rules' R3.1 `step_down` (class capacity-limited) was **refused by the guard**: the stream was
    in recovery, with `recovery_playing` and `game_not_paused` false.
  - At 00:33:38.578Z the ladder's own transition, **reason `recovery_escalation`**, class FALLBACK, took **7000→5000**.
    It came 1.1 s after the 52.6-s recovery resumed.
  - The R3.1 row logged 1 ms later records `ladder_result: transition`, the transition already under way. **The
    trigger the log names is `recovery_escalation`, not the rules.**
  - The rung stayed at 5000 for the rest of the window: 59 of 69 polls.
- **Cell 7 (burst-50x20, off):**
  - the plain ladder, with no rules running (the off arm). At 00:49:35.872Z, **reason `capacity_mild`**, class ROUTINE:
    **7000→6000**.
  - This came 58 s after the client pause began and 36 s after it resumed. The rung was at 6000 for 50 of 69 polls.
- **Cell 12 (delay-150, on):**
  - **the rules acted.** At 02:06:05.095Z the transition's **reason is `wan_rules`**, class ROUTINE, **7000→6000**.
  - The paired suggestion was R2.1 `step_down` ("latency-limited / starved on 2 consecutive windows", class starved),
    `ladder_result: transition`.
  - 19 further R2.1 suggestions were refused by the hold-down, and 3 returned none. The rung was at 6000 for 23 of
    69 polls.

**In every other on cell the rules wrote no `step_down`.** Rows written:
- cells 2, 4, 8, 10, 14, 16, 22: no `wan_suggestion` row at all;
- cells 6 and 12: the `no_step_up` and `hold` rows above.

Any movement between the arms in those profiles ran without a rules action. The arms are separate runs: off, then on,
about 14 min apart.

### (iii) The classifier against the profile's intent

| profile | intent | off: class (primary windows) | on: class (primary windows) |
| --- | --- | --- | --- |
| none | (no impairment) | lossy (clean 41, lossy 27) | clean (clean 53, lossy 15) |
| loss-1 | lossy | lossy (63 of 69) | lossy (64 of 69) |
| loss-5 | lossy | **lossy** (68 of 69) | path-changed (lossy 59, capacity-limited 3, path-changed 1) |
| burst-50x20 | lossy | path-changed (lossy 39, path-changed 1) | lossy (49) |
| delay-50 | (none set) | lossy (34; clean 32) | lossy (30; clean 38) |
| delay-150 | latency-limited | **lossy** (43; starved 8; latency-limited 0) | **path-changed** (lossy 34, starved 7, path-changed 1; latency-limited 0) |
| jitter-30 | (none set) | lossy (53) | **latency-limited** (1 window; lossy 64) |
| reorder-5 | (none set) | lossy (45) | lossy (47) |
| cap-6000 | capacity-limited | capacity-limited (2 of 3 windows; starved 1) | capacity-limited (2 of 3) |
| cap-4500 | capacity-limited | capacity-limited (3 of 4; starved 1) | **starved** as the session class (capacity-limited 3 of 4 windows) |
| delay-50+loss-1 | lossy | lossy (66) | lossy (67) |

The class is the session object's `class`, from the last poll; the windows are its `window_primary_counts`.

**The pre-registered questions, answered from the files:**

- **Did `loss-5` read `lossy`?** **Yes, off** (68 of 69 windows). On, the session class at the last poll was
  `path-changed`, while 59 of 69 windows were lossy. The one path-changed window sits in the session that went through
  the 52.6-s recovery and the 7000→5000 restart.
- **Did `delay-150` read `latency-limited`?** **No, in neither arm:** 0 latency-limited windows. It read lossy (off)
  and path-changed (on), with 7-8 starved windows. The files show why the latency measure did not see it:
  - The `rtt_ms` measure's source is `latency.control_round_trip_ms`, "the client's control echo".
  - The shim delays the post-FEC **video** path only; the control echo does not cross it.
  - The RTT p50 was 97 ms (off) and 74 ms (on), against 43-45 ms in the 10-16 `none` cells, and its p95 was 1,328 /
    437 ms. But none of it is the shim's 150 ms on the video path.

  This is stated from the measure's source field; the classifier's thresholds were not re-read here.
- **Did `cap-4500` read `capacity-limited`?**
  - **Off: yes**, as the session class.
  - **On:** the session class was `starved`, with 3 of 4 primary windows capacity-limited.
  - `cap-6000` read capacity-limited in both arms.
  - **What the classifier saw:** not a played window. It saw the last client session of the last attempt, 16-24
    client reports (about 36-48 s), which never reached PLAYING. In that session:
    - delivered goodput was **5,170 / 5,448** kbps (cap-6000) and **4,187 / 4,208** kbps (cap-4500), under the cap;
    - post-FEC loss was 11,900-17,800 /min.
  - It is the impaired stream's start-up, not the setup traffic alone, but it is not a measurement of a stream
    running under the cap.
- **`jitter-30`:** **on** read `latency-limited` as the session class, from 1 latency-limited window of 69 (lossy 64).
  Off read lossy, with no latency-limited window. One window, so reported, not read as a property of the profile.

## 5. The four cap cells (17-20): read, not explained away

**The suite's launch attempts** (`suite.log`, `summary_failed_attempt1/2.json`, `summary.json`):

- each cell made 3 attempts, the run plus 2 retries. All 12 ended with "stream did not reach PLAYING: {'ok': False,
  'recovery': 'ENDED'}".
- Each attempt's `open_stream` makes up to **two client launches**: force-stop, start MainActivity, tap the preview,
  then wait **45 s** for the companion's recovery state to read PLAYING (`tools/e1_suite.py`, `open_stream`).
- So each cell made 6 client sessions, and cell 20 made 5 (its last attempt shows one session). The journal shows
  **23 client sessions** over the four cells (`cap_cells_companion_log.txt`).
- **PLAYING was never reached in any of them.** No `recovery.jsonl` row was written, and no window was opened.

**The client's own last state** (the end-of-session report per attempt, and the heartbeats in the companion's
journal):

| cell | attempt | client session duration ms | rendered frames | lost packets | max output gap ms | resyncs | audio underruns |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17 cap-6000 off | 1 / 2 / 3 | 49,480 / 49,640 / 49,751 | 23 / 25 / 20 | 10,688 / 9,194 / 10,754 | 47,521 / 47,790 / 45,988 | 1 / 1 / 1 | 5,422 / 3,970 / 4,520 |
| 18 cap-6000 on | 1 / 2 / 3 | 49,505 / 49,377 / 49,535 | 20 / 16 / 22 | 9,529 / 9,222 / 9,219 | 47,397 / 45,577 / 45,620 | 1 / 1 / 1 | 4,968 / 5,915 / 5,279 |
| 19 cap-4500 off | 1 / 2 / 3 | 49,534 / 49,459 / 49,416 | 11 / 14 / 14 | 16,922 / 14,378 / 14,339 | 47,753 / 47,699 / 47,234 | 1 / 1 / 1 | 5,903 / 6,091 / 4,582 |
| 20 cap-4500 on | 1 / 2 / 3 | 49,392 / 49,285 / 49,458 | 14 / 15 / 9 | 16,878 / 14,204 / 14,499 | 47,656 / 45,702 / 47,988 | 1 / 1 / 0 | 6,112 / 5,932 / 1 |

- **What the client's heartbeats show** in every one of the 23 sessions (the companion's journal, every 2 s):
  - packets kept arriving at about 600 /s (`rx_packets` 22,900-29,600 by the last heartbeat);
  - `rendered_frames` stopped at **9-27** by the second or third heartbeat (≤ 5.1 s into the session) and never moved again;
  - `queued_frames` held at 21-42, and `last_output_age_ms` grew to 43-47 s;
  - `lost_packets` was 31-71 % of the received count (8,800-16,600);
  - `forward_gap_events` came about 3,000-3,160 per session, about 63 per second, roughly one per frame;
  - FEC recovered 15-142 packets against 172-294 unrecoverable groups.
- **Each session ended after about 49 s** with `decoder-session-log`, then `native-stream-stop`. This matches the
  suite's per-launch timing (7 s + 3 s + the 45-s wait).
- **The companion's log at the attempts:** apart from the HTTP lines (launch, `session/nonce`, `session/setup`,
  `native-stream-start`, the heartbeats, `decoder-session-log`, `native-stream-stop`, `games/stop`), the only lines are
  the overlay status line and the restarts. There is **no error line, no recovery line and no ladder line**, and no
  `decisions.jsonl` was written for these runs.
- **`flags_absent` after:** true in all 12 attempts' teardowns and in each cell row.

**The shim's counters per stream start** (`impairment_run1.jsonl`, per-second deltas; segments split where `t_s`
restarts; "steady" means the seconds after the first 2.5 s):

| cell | cap (kbps) | stream starts | seconds each | steady input kbps | steady output kbps (max second) | tail-dropped fraction (steady) | queue max (packets) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17 cap-6000 off | 6000 | 6 | 47-62 | 8,252-8,259 | 6,000.0-6,000.2 (6,011.5) | 0.269-0.286 | 68-73 |
| 18 cap-6000 on | 6000 | 6 | 46-62 | 8,044-8,253 | 5,859-6,000 (6,009.7) | 0.269-0.271 | 67-69 |
| 19 cap-4500 off | 4500 | 6 | 48-60 | 8,252-8,259 | 4,499.9-4,500.2 (4,510.7) | 0.441-0.449 | 52-56 |
| 20 cap-4500 on | 4500 | 5 | 46-62 | 8,238-8,259 | 4,499.9-4,500.3 (4,509.6) | 0.441-0.449 | 52-56 |

- **The reference:** a valid cell's steady input through the same shim, at the 7000 rung with FEC and audio, was
  8,292-8,298 kbps (cells 1, 2, 9, 10, 15, 16).
- **`send_errors`:** 0 in every cap line. There was one second with zero output after the first 2.5 s (cell 18).
- **The cap as applied** passes the pre-registered check: every second's output is ≤ 1.05 × the cap, and there was no
  random or burst drop. The driver's `seconds_input_over_cap` was 320 of 326 for cell 17.
- **The queue bound:** 100 ms of the cap's bytes is about 75 KB at 6000 and 56 KB at 4500. The queue maxima of 67-73
  and 52-56 packets sit at that bound.

**The candidate readings, listed; none is chosen:**

- **(a) The stream's own rate exceeds the cap, and the bounded queue tail-drops it.**
  - The ladder starts at 7000, which with FEC and audio is about 8.25 Mbit/s on the wire, above 6000 > 4500.
  - **It predicts:** input above the cap for the whole stream, not only at setup. Output pinned at the cap. A steady
    drop fraction near 1 − cap / input, that is 0.27 at 6000 and 0.45 at 4500. Loss spread over every frame. No ladder
    action, since nothing reaches PLAYING.
  - **The files show:** input 8.04-8.26 Mbit/s in every second of every start; output at the cap; drop fractions of
    0.269-0.286 and 0.441-0.449; about one forward gap per frame; rendering stopping after 9-27 frames; no
    `decisions.jsonl`.
- **(b) The shim's cap stage stalls or mis-paces at post-FEC.**
  - **It predicts:** output below the cap or uneven across seconds, zero-output seconds, `send_errors`, or a queue
    depth beyond its bound.
  - **The files show:** output at 6,000.0 ± 0.2 / 4,500.0 ± 0.3 kbps per second; `send_errors` 0; queue maxima at the
    bound; one zero-output second in all four cells.
  - Not visible at this resolution: pacing **within** a second (the lines are 1-s aggregates), and the packet order the
    tail drops leave inside each frame and FEC group.
- **(c) The client's start-up timeout.**
  - **It predicts:** the client ending its session by itself at a fixed time, or giving up with decodable frames still
    arriving.
  - **The files show:**
    - each session lasted about 49 s and ended with `decoder-session-log`, then `native-stream-stop`, matching the
      suite's 45-s wait plus its taps;
    - the client kept receiving and reporting throughout (24 heartbeats);
    - the companion's recovery state read ENDED when the suite polled after the wait.
  - The files do not contain the client's own reason for the end. The client's log is not in these files, and whether
    the suite's force-stop ended each session is not recorded.

**G8-P1's cap proof** (in process, `G8_P1_IMPAIRMENT_SHIM_2026-10-16.md` §2 A) **used a synthetic RTP source at a
steady ~6.9 Mbit/s (60 fps × 12 × 1,200 B)**. It measured the cap's output (6,000.3 / 4,500.3 kbps), its bound and its
tail drop (13.1 % / 34.8 %). It never carried a real stream's start through the cap, nor one at 8.25 Mbit/s, and it
did not test whether a decoder can start under that drop.

**This is the one finding that needs a follow-up task.** It is listed in §8, not designed here.

## 6. The link's own loss across the night

- **There was no control cell on 10-17.** The two `none` cells (1-2) ran on 10-16 evening, 20:13-20:42Z. The resumed
  cells ran 00:21-04:30Z on 10-17, after a 2 h 56 min pause.
- **10-16, the `none` cells** (no shim stage):
  - 6.03 and 3.82 loss/min in the window;
  - post-FEC 17.85 / 4.14 /min (`wan`);
  - classes lossy, then clean.
- **10-17, the lowest-loss cells of the night:**
  - **delay-50:** 18.83 / 14.38 loss/min (heartbeat), post-FEC 19.28 / 14.83. The shim delays only and drops nothing;
    17 and 6 packets were still queued at its end.
  - **reorder-5:** 19.60 / 23.00 loss/min, post-FEC 18.45 / 24.20. The shim reorders about 4.75 % and drops nothing.
    Pre-FEC reads 394-411 /min there, the reordering counted as gaps that FEC then recovers.
- **As a bound, not a control:** on 10-17 the link's own post-FEC loss plus whatever delay-50 and reorder-5 add on the
  client side was at most about 15-24 /min. That is above the 10-16 `none` cells (4-18) and far below the profiles
  that drop. The link's own share in the other cells cannot be separated with these files.

## 7. State and files

- **`tools/e3_state.py --check` ok at the close** (`check_final.json`). Nothing is running: the unit was collected,
  and there is no stream and no game.
- **`g8_s1_2026-10-16/`**, everything earlier plus:
  - `final_baseline_head.txt`, `final_git_status_at_start.txt`, `check_final.json`;
  - `final_status_resume.txt`, and `history.csv` and `driver.log` (replaced; the final copies);
  - `cells.jsonl` (22 rows), `g8_s1_state.json`, `runs/01…22/`;
  - `g8_s1_analysis.py` (extended), `g8_s1_table_final.md`, `g8_s1_cells_read_final.json`, `validity.json` (replaced);
  - `g8_s1_cap_log_read.py`, `cap_cells_companion_log.txt`;
  - `tools_at_record_close_sha256.txt`;
  - `manifest.sha256` (replaced): 534 files, the whole directory with `runs/01…22/`, excluding `__pycache__/` and the
    manifest's own two files. `manifest_check.txt`: 534 OK, rc 0.
  - `redact_check.txt` (replaced): the redactor over the whole directory and this session's other files.
    - 496 text files OK. 23 HITs, all benign by the launch's rule: the 22 `title.txt` carry the core's version string,
      and the old check file named the masked strings.
    - The extension-less files are OK.
    - The two `__pycache__/*.pyc` files (binary, gitignored) are excluded as before and left in place.
- `logs/g8_s1_final_git_status.txt`, written after the manifest. The redactor over it: OK.
- `docs/ROADMAP.md` §G8: the status line. `docs/KNOWN_ISSUES.md`: one entry (the cap cells; delay-150's class).
  `CURRENT.md`: the state line and Next Action.
- The PARTIAL record's header now names this record as superseding it.
- No sudo, no nft, no Opal access. adb was used only to read state. No address, token or identifier was written.
  Nothing fetched, deleted, adopted or committed. Session B's files were not touched.

## 8. For the user (options, not decided here)

- **(a) A cap follow-up (G8-S2).** The cap cells with a stream that starts below the cap (a rung at or under 4500 /
  6000 from the first frame). Or the shim's cap stage re-proved against a bursty, real-rate source, at the rate the
  stream actually sends (~8.25 Mbit/s at 7000).
- **(b) A re-run of the on-arm cells on committed code**, if the user wants the on arm on one code version.
  - The off arms from cell 7 and all on arms from cell 6 ran B's edited (flag-absent) modules.
  - Cells 1-5 ran the pre-registered ones.
- **(c) G5-S3's LAN smoke, then G4-S2 off-site** with G5-S3 + G5-S2 + the cap, with the user judging 4000's picture.
