---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 64d9489 (the G8-S1 launch and the shim's `none` profile uncommitted beside it, not touched)
---

# G8-S1 — the adverse-network envelope (first pass)

**Classification: PARTIAL — 5 of 22 cells, stopped by the user's STOP file at 2026-10-16T21:25:52Z.** All five cells
are valid, and every host gate was met in each. The link-side numbers below are reported, not judged: this is the
envelope, with no pass or fail. Measurement only; nothing adopted; nothing committed. The driver was not relaunched.

- Written only from the driver's files: `cells.jsonl`, `runs/<cell>/` (the suite's output), the `wan` polls
  (`wan_poll_run1.jsonl`) and the shim lines (`impairment_run1.jsonl`).
- Read against `g8_s1_preregistration.txt` as hashed: sha256 `b2e02fa0…dcf73`, re-read at the close and unchanged.
- The reading script is `g8_s1_analysis.py` → `g8_s1_table.md`, `g8_s1_cells_read.json`, `validity.json`.
- Tasks: `handoffs/G8-S1_ADVERSE_NETWORK_ENVELOPE_TASK.md` (the run) and `handoffs/G8-S1_STOP_AND_PARTIAL_RECORD_TASK.md`
  (this close). Launch record: `G8_S1_LAUNCH_2026-10-16.md`. **Baseline `64d9489`** (`stop_baseline_head.txt`).

## 1. The stop

- **`touch ~/privyhub_g8_s1/STOP`** at 21:20:11Z (`stop_touched_at.txt`), with cell 5 (loss-5, off) in flight.
- The cell finished its window and teardown. The driver then logged "the stop file: exiting" and wrote
  **`doing: EXITED (the stop file)`** at 21:25:52Z (`final_status.txt`), about 6 min after the touch.
- There was no kill, no `systemctl --user stop`, and no companion restart beyond the suite's own teardown.
- `systemctl --user status privyhub-g8-s1` read "Unit privyhub-g8-s1.service could not be found": the transient unit
  was collected (`unit_status_after_stop.txt`).
- Copied into this directory: `final_status.txt`, `history.csv`, `driver.log`.
- **The STOP file stays** (`~/privyhub_g8_s1/STOP`; the driver never removes it). **A resume must remove it first**
  (§6).

## 2. The state after the stop (`check_after_stop.json`)

- `tools/e3_state.py`: **ok.** Seven adopted lines, no `e3_flag.conf`, no `e4_constraint.conf`, no game, no RetroArch,
  no encoder, PS1 files identical, APK CONFIRMED. The drop-in directory holds the seven adopted drop-ins only.
- One device paired.
- The last `cells.jsonl` row (cell 5): `flags_absent_after` true, `final_flags_absent` true. All five rows read true.

## 3. The cells

- **Each cell:** E1-PS1-STREAM, `--e2`, a 600-s window and a 120-s gap, with the shim `@post-fec,seed=1`. The flags
  were confirmed in the companion's environ 150 s into each window: 9 lines off, 10 on, `flags_under_load` true in all
  five. The shim ran live with the cell's profile.
- **Validity:** each cell reached PLAYING with no run replacement (no `summary_failed_*`). Each profile was **applied**
  by the pre-registered count tolerances:
  - none: 0 dropped, delayed or reordered;
  - loss-1: 0.991 % and 0.992 % dropped;
  - loss-5: 4.985 % dropped.
- Cell 1's "attempt 2" in the PLAYING column is the suite's launch helper (the stream started on its second try
  within the same run), not a run replacement.

### 3a. Host side (gates: RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤ 0.2/min, flags absent after)

| cell | PLAYING (attempt, s) | RetroArch | capture | dup+drop /min | gates | host CPU % | companion % of a core | shim % of a core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 none off | 2, 3.0 | 59.999 | 59.988 | 0.10 | all met | 12.85 | 29.55 | 3.14 |
| 02 none on | 1, 3.1 | 59.999 | 60.038 | 0.10 | all met | 12.61 | 30.17 | 3.23 |
| 03 loss-1 off | 1, 5.1 | 59.999 | 59.987 | 0.10 | all met | 11.89 | 28.48 | 2.89 |
| 04 loss-1 on | 1, 3.1 | 59.999 | 59.989 | 0.10 | all met | 12.15 | 29.17 | 2.89 |
| 05 loss-5 off | 1, 3.1 | 59.999 | 60.039 | 0.10 | all met | 11.87 | 29.19 | 2.92 |

The shim's cost is `cpu_s / duration` from its own lines over the whole stream. That matches G8-P1's in-process
2.1-7.0 % (the no-stage profiles, 2.05-2.09 there).

### 3b. The link (reported, not gated)

| cell | loss/min (heartbeat, window) | pre-FEC /min (wan) | post-FEC /min (wan) | FEC recovered packets | unrecoverable groups | rendered | stale /min | spikes ≥ 20 ms /min | resyncs (window) | resyncs (session) | client pauses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 none off | 6.03 | 31.54 | 17.85 | 158 | 23 | 59.959 | 1.03 | 43.28 | 0 | **1** | 0 |
| 02 none on | 3.82 | 8.02 | 4.14 | 45 | 16 | 59.970 | 0.86 | 36.41 | 0 | 0 | 0 |
| 03 loss-1 off | 45.64 | 504.44 | 46.14 | 5,334 | 201 | 59.515 | 3.00 | 45.04 | 0 | 0 | 0 |
| 04 loss-1 on | 68.47 | 524.80 | 65.09 | 5,332 | 212 | 59.440 | 1.55 | 49.49 | 0 | 0 | 0 |
| 05 loss-5 off | 809.49 | 2,511.62 | 809.29 | 19,760 | 3,570 | 52.616 | 1.64 | 39.49 | 0 | 0 | 0 |

**The fields:**

- `loss/min (heartbeat)` is the suite's `key.heartbeat.video_loss_per_min` over the 600-s window.
- The pre- and post-FEC rates and the FEC counts come from the **last `wan` poll** of each run (`measures.packet_loss_per_min`,
  `measures.fec_groups`). That is G5-S1's per-session object, the session so far: 345-348 client reports, warm-up
  included, last polled within 8 s of the window's end (2 s before to 8 s after, `g8_s1_cells_read.json` `wan_poll_at`).
- So the heartbeat and the `wan` post-FEC rates cover different spans and do not agree exactly (cell 1: 6.03 against
  17.85).
- Stale and spikes come from the client's teardown report, per minute of its duration.

**The resyncs, both columns, and cell 1's discrepancy:**

- The driver's field `resyncs` reads `key.heartbeat.stream_resyncs`, the heartbeat **over the 600-s window**: the
  "window" column.
- The client's end-of-session report has `teardown.report_fields["video.sequence_resyncs"]`, the **whole session,
  warm-up included**: the "session" column.
- **In cell 1 they disagree: 0 in the window, 1 in the session.** The files show only the two spans: one resync was
  counted by the client in its session and none by the heartbeat in the window. When or why it happened outside the
  window is not in these files.
- In cells 2-5 the two columns agree (0 and 0).

### 3c. The ladder, the rules, the classifier, the shim

| cell | rung kbps (status polls) | ladder acted | rules suggestions (`source: wan_rules`) | `wan` class | windows by primary class | shim in / out | dropped: loss / burst / queue | delayed | reordered | queue max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 none off | 7000-7000 (69) | 0 | 0 (off) | lossy | clean 41, lossy 27, starved 1 | 665,785 / 665,785 | 0 / 0 / 0 | 0 | 0 | 48 |
| 02 none on | 7000-7000 (69) | 0 | **0** | clean | clean 53, lossy 15, starved 1 | 665,626 / 665,626 | 0 / 0 / 0 | 0 | 0 | 41 |
| 03 loss-1 off | 7000-7000 (69) | 0 | 0 (off) | lossy | lossy 63, starved 4, clean 2 | 667,286 / 660,672 | 6,614 / 0 / 0 | 0 | 0 | 39 |
| 04 loss-1 on | 7000-7000 (69) | 0 | **0** | lossy | lossy 64, starved 2, clean 3 | 665,602 / 658,996 | 6,606 / 0 / 0 | 0 | 0 | 42 |
| 05 loss-5 off | 7000-7000 (69) | 0 | 0 (off) | lossy | lossy 68, starved 1, clean 0 | 665,619 / 632,441 | 33,178 / 0 / 0 | 0 | 0 | 37 |

(path-changed, latency-limited and capacity-limited windows: 0 in every cell.)

- **The ladder** held 7000 for every poll in all five cells, with no acted decision, including loss-5 at 809 loss/min
  and rendered 52.6.
- **The rules in the two on cells: no `wan_suggestion` row.** `decisions.jsonl` has 0 rows with `source: wan_rules`,
  and a grep of `logs/` found none. From the code (`companion/wan_adaptation.py`, `tick`):
  - a row is written only when the suggestion is not `none`;
  - at the top rung (7000) the rules return `none` unless the window is capacity-limited (R3), or latency-limited /
    starved on 2 consecutive windows (R2);
  - in the two on cells there were no capacity-limited or latency-limited windows. The starved windows (1 and 2) are
    counted in the per-window primary counts; the files do not show whether any two fell on consecutive windows, and
    no R2 row was written.

  Read from the code; not otherwise verified.

### 3d. Session loss and recovery events

- `recovery.jsonl`: 0 rows in every cell. `key.recovery`: no controller, client or other pauses, nothing saved.
- `gaps.jsonl` (the controller-input gap log, recovery v2):
  - cells 1, 2 and 5: 0;
  - cell 3: 1 gap of 292 ms;
  - cell 4: 7 gaps of 251-953 ms.

  None reached a pause. These are the controller return path (client → host); the shim impairs video only.
- No session was lost.

## 4. The pre-registered comparisons, as far as five cells allow

**(i) `none` against CL-B3's R1 and W** (the shim's cost on the stream; CL-B3 had no shim):

| run | host CPU % | companion % of a core | shim % of a core | rendered | loss/min (heartbeat) | resyncs (window) | rung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CL-B3 R1 (no shim, no telemetry flag) | 11.569 | 24.80 | — | 59.674 | 80.05 | 0 | 7000-7000 |
| CL-B3 W (no shim, `WAN_TELEMETRY=1`) | 11.593 | 25.44 | — | 59.795 | 60.32 | 3 | 7000-7000 |
| G8-S1 01 none off (shim + telemetry) | 12.847 | 29.55 | 3.14 | 59.959 | 6.03 | 0 | 7000-7000 |
| G8-S1 02 none on (shim + telemetry + rules) | 12.611 | 30.17 | 3.23 | 59.970 | 3.82 | 0 | 7000-7000 |

- Host CPU: +1.25 / +1.02 points against W.
- The companion: +4.11 / +4.73 points of a core against W. The shim thread runs in the companion, and its own 3.1-3.2
  is part of that.
- These are separate runs, hours apart (CL-B3 17:30-17:59Z, G8-S1 20:17-20:42Z), at the same rung. The link tonight
  was cleaner than at CL-B3 (6.03 and 3.82 against 60-80 loss/min).

**(ii) Off against on, per profile done** (stated, not judged):

- **none:** the rules suggested nothing (0 rows). Off then on, each with the link's own loss:
  - rendered 59.959 → 59.970;
  - stale 1.03 → 0.86 /min;
  - loss 6.03 → 3.82 /min (heartbeat), 17.85 → 4.14 (`wan` post-FEC);
  - class lossy → clean.
- **loss-1:** the rules suggested nothing (0 rows). Off then on:
  - rendered 59.515 → 59.440;
  - stale 3.00 → 1.55 /min;
  - loss 45.64 → 68.47 /min (heartbeat), 46.14 → 65.09 (`wan` post-FEC);
  - FEC recovered 5,334 → 5,332, unrecoverable 201 → 212;
  - both lossy.

  The shim dropped 6,614 and 6,606 packets (0.991 % and 0.992 %).
- With no suggestion in either on cell, the ladder had nothing from the rules to act on. Any movement between the arms
  ran without a rules action.
- **loss-5:** only the off cell ran; the on cell is not run.

**(iii) The classifier against the profile's intent:**

| profile | intent | off | on |
| --- | --- | --- | --- |
| none | (no impairment) | lossy (clean 41 / lossy 27 / starved 1 windows) | clean (53 / 15 / 1) |
| loss-1 | lossy | lossy (lossy 63 of 69) | lossy (64 of 69) |
| loss-5 | lossy | lossy (68 of 69) | not run |

The pre-registered questions about `cap-4500` (capacity-limited?) and `delay-150` (latency-limited?) are **not
answered**: those cells did not run.

**Reported:**

- **The link's own loss tonight** (the `none` cells, no shim stage): 6.03 and 3.82 loss/min in the window; pre-FEC
  31.5 and 8.0 /min, post-FEC 17.9 and 4.1 /min (`wan`). Classes lossy, then clean.
- **The ladder under a cap cell:** none ran.

## 5. Not run — resume

| n | profile | arm |
| --- | --- | --- |
| 6 | loss-5 | on |
| 7 / 8 | burst-50x20 | off / on |
| 9 / 10 | delay-50 | off / on |
| 11 / 12 | delay-150 | off / on |
| 13 / 14 | jitter-30 | off / on |
| 15 / 16 | reorder-5 | off / on |
| 17 / 18 | cap-6000 | off / on |
| 19 / 20 | cap-4500 | off / on |
| 21 / 22 | delay-50+loss-1 | off / on |

All 17 are "not run — resume".

## 6. Resume (from the code; not relaunched)

- **Does a relaunch skip the done cells? Yes.**
  - `main()` loads `g8_s1_state.json` if it exists (`st = json.loads(STATE_P.read_text()) if STATE_P.exists()`).
  - The cell loop starts with `if cell["cell"] in st["done"]: continue`.
  - `done` holds `01_none_off` … `05_loss-5_off`, all `valid`, so a relaunch starts at cell 6 (loss-5 on). A
    `busy` or `profile-not-applied` cell would also be in `done` and skipped.
  - `cells.jsonl`, `history.csv` and `driver.log` are appended. The suite numbers runs inside each cell's own
    directory.
- **What a resume needs:**
  1. **Remove `~/privyhub_g8_s1/STOP`.** The loop checks it before every cell; present, the driver exits at once with
     "the stop file".
  2. **A new cap.** `CAP` is a constant in `g8_s1_driver.py` (2026-10-17T06:00:00Z). After it, no cell starts. A resume
     after that needs the constant changed. That edits a file whose hash is in `tools_at_preregistration_sha256.txt`,
     so it is a disclosed change, the user's.
  3. **The same unit name.** `privyhub-g8-s1` is free: the transient unit was collected. Use
     `systemd-run --user --unit=privyhub-g8-s1 --collect -p WorkingDirectory=<repo> /usr/bin/python3 -B …/g8_s1_driver.py`.
  - The pre-registration is unchanged, so the wrapper's hash check still passes.
  - The remaining 17 cells take about 4.2 h at about 14.6 min each.

## 7. Files

- **`g8_s1_2026-10-16/`, now complete** (the launch's files, plus):
  - `stop_baseline_head.txt`, `stop_touched_at.txt`;
  - `final_status.txt`, `history.csv`, `driver.log`, `unit_status_after_stop.txt`, `check_after_stop.json`;
  - `cells.jsonl`, `g8_s1_state.json`, `runs/01…05/`;
  - `g8_s1_analysis.py`, `g8_s1_table.md`, `g8_s1_cells_read.json`, `validity.json`;
  - `redact_check.txt`: replaced, over the whole directory including `runs/`. 142 text files OK; 6 HITs, all benign by
    the launch's rule (the core's version string in `title.txt`; the old check file).
  - Two binary `__pycache__/*.pyc` files (from the launch's `py_compile`, gitignored) match the patterns on raw bytes.
    They were left in place and are excluded from the manifest.
  - `manifest.sha256`: 148 files; `manifest_check.txt`: 148 OK, rc 0.
- `docs/ROADMAP.md` §G8: the status line. `logs/g8_s1_stop_git_status.txt`.
- No sudo, no nft, no Opal access. No address, token or identifier. Nothing fetched, deleted, adopted or committed.
