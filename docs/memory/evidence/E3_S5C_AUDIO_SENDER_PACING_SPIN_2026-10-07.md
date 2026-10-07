---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: ccee2f5
---

# E3-S5C — the audio sender's pacing: one timed wait plus the final spin

**Classification: ACCEPTED by the pre-registered bar.** Every clause
holds in every flagged run, and the controls are comparable
(`e3_s5c_verdict.json`).

- **The clause this variant exists to meet holds:** the flagged runs had
  **13 / 9 / 5** underruns. The limit was ≤ max(controls 17, 14) + 5 and
  ≤ 20, so 20. E3-S5B's `=frame` had 15 / 18 / 8.
- **The CPU saving is partial, as designed.** The sender used **5.9-6.1 %**
  of a core (today 12.9-13.4 %, `=frame` 2.0-2.35 %). The companion used
  **17.5-17.6 %** (today 24.3-24.9 %). Socket power was 0.5-3.7 W below the controls.
- **The probe put the hypothesis in doubt before the runs**, by the
  task's own rule: the tick sd was 0.102 ms, against ≤ 0.10. The runs
  decided anyway, as the task said they would.
- One change, behind the new value `PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`.
  **NOT ADOPTED** (the user's decision); nothing committed. The flag is
  absent at the end, and the adopted state is restored.

**Context:**

- Task: `handoffs/E3-S5C_AUDIO_SENDER_PACING_SPIN_TASK.md`, item 2 of
  `handoffs/QUEUE_2026-10-07.md`.
- **Baseline commit: `ccee2f5`.** This ran on the adopted state (E3-S6A:
  the environ is live + the guide index).
- Files: `e3_s5c_2026-10-07/`.
- Timeline (UTC, 2026-10-07):

  | time | what |
  | --- | --- |
  | 05:32:06 | preconditions held (the adopted state; `precondition.json`) |
  | 05:32-05:38 | the change applied; the three-way probe |
  | **05:39:33** | **pre-registration hashed** (`a836a527…7148`) |
  | 05:39:33-07:40:16 | C1, F1, C2, F2, F3, each OK on its first attempt |

## 1. The change (`patches/E3-S5C_AUDIO_SENDER_FRAME_SPIN.md`)

`companion/native_session_io.py`, +7 lines (diff `e3_s5c_frame_spin.diff`):

- `_linux_sender_loop` reads `=frame_spin` once, beside E3-S5's `=frame`.
- `_linux_wait_until`, when it is set: one `Event.wait` to
  (deadline − 250 µs), then loop. Under 250 µs the loop spins to the
  deadline, as today's final spin does.
- `=frame` keeps its E3-S5 behaviour. **Absent = today's wait.**
- Packetization, redundancy 2/4, `SCHED_RR`/1 and the relay are
  unchanged.

## 2. The probe (`probe.md`, `probe_stats.json`)

60-s send traces, three ways, one session each:

| | no flag | `=frame` | **`=frame_spin`** |
| --- | --- | --- | --- |
| tick gap p99 / max ms | 5.24 / 5.74 | 5.53 / 6.77 | 5.31 / 5.98 |
| min ms | 4.23 | 2.64 | 4.06 |
| **sd ms** | 0.076 | 0.181 | **0.102** |
| gaps > 10 ms; bunches ≥ 4 | 0; 0 | 0; 0 | 0; 0 |
| voluntary switches/s; **wake-ups per packet** | 16,875; 84.4 | 272; 1.36 | 302; **1.51** |
| sender thread CPU % (schedstat) | 13.2 | 2.0 | **6.3** |

- **What the spin restored:** the early ticks (min 4.06 vs 2.64 ms) and
  most of the late tail (p99 5.31 vs 5.53).
- **What it did not:** the sd sits between today's and `=frame`'s. Some
  timed waits still overshoot their 0.25-ms margin.

## 3. The runs and the bar

From `e3_s5c_table.md`, `e3_s5c_verdict.json` and `loss_per_minute.txt`
(`e3_s5c_analysis.py`, which is E3-S5B's analysis with clause (a)'s two
limits set to 8 and 20). The runs are in run order.

| | C1 | F1 | C2 | F2 | F3 | E2 PS1-STREAM |
| --- | --- | --- | --- | --- | --- | --- |
| audio sender, % of a core | 13.4 | **6.0** | 12.9 | **6.1** | **5.9** | 12.8 |
| companion, % of a core | 24.9 | **17.6** | 24.3 | **17.6** | **17.5** | 24.3 |
| socket W | 20.3 | 17.5 | 21.2 | 19.8 | 19.1 | 20.4 |
| host CPU % | 11.5 | 10.3 | 11.5 | 10.8 | 11.6 | 11.7 |
| rendered fps | 59.98 | 59.95 | 59.95 | 59.94 | 59.95 | 59.81 |
| **audio underruns (window)** | 17 | **13** | 14 | **9** | **5** | 11 |
| video loss/min (window) | 7.5 | 21.1 | 16.8 | 9.4 | 20.1 | 32.3 |
| per-minute median; minutes > 100 | 2; 0 | 3.5; **2** | 4.5; **2** | 6; 0 | 3; **1** | — |
| spikes ≥ 20 ms/min; stale drops/min | 31.2; 0.83 | 31.5; 0.69 | 28.2; 0.46 | 30.9; 0.74 | 30.3; 0.46 | 59.8; — |
| max output gap ms (report; C2) | 178; 71 | 305; 87 | 342; 65 | 117; 69 | 383; 67 | 378; 280 |
| ladder decisions: rows, transitions | 649, 0 | 675, 0 | 653, 0 | 668, 0 | 650, 0 | — |

| clause | needed | got | holds |
| --- | --- | --- | --- |
| comparability | C1, C2 in 11.69 ± 2 and 59.81 ± 0.5; \|C1 − C2\| ≤ 0.5 fps | 11.50 / 11.53; 59.98 / 59.95 | yes |
| a. sender ≤ 8 %, companion ≤ 20 % | every F | 5.9-6.1; 17.5-17.6 | yes |
| b. underruns ≤ max(C) + 5 = 22 and ≤ 20 | every F | 13 / 9 / 5 | yes |
| c. rendered ≥ 59.5; RetroArch 60 ± 0.5 | every F | 59.94-59.95; 60.0 | yes |
| d. pooled minutes | median F ≤ 3 × median C; share > 100: F ≤ C + 0.10 | **4.0 vs 2.5** (limit 7.5); **0.05 vs 0.05** | yes |
| e. spikes < 200/min; stale < 20/min | every F | ≤ 31.5; ≤ 0.74 | yes |

**Verdict: ACCEPTED.**

**Read beside the bar:**

- **Underruns.** The three flagged runs average **9.0** per 20 min
  (13 / 9 / 5), and tonight's controls 15.5 (17 / 14). Every unflagged
  E3 session so far, E3-S5 / S5B / S5C, averages 12.6. E3-S5B's `=frame`
  sessions averaged 13.0 (S5's 9 / 15 included).
  - So the spin did what the hypothesis said for underruns.
  - **The probe's sd (0.102) did not quite reach today's.** The
    underrun count does not need it to.
- **Loss.** Burst minutes (> 100 lost) appeared on both sides tonight:
  F1 2, C2 2, F3 1, so the shares are equal at 0.05. The pooled median
  is 4.0 against 2.5.
  - These bursts are the link's episodes, as E3-S5B concluded: the
    controls have them too.
  - The flagged runs' mean loss/min (21.1 / 9.4 / 20.1) sits above the
    controls' (7.5 / 16.8). F1's and F3's means are each lifted by one or
    two burst minutes.
- **Beside `=frame`** (E3-S5B, same row):
  - `frame_spin` gives up ~4 points of a core: sender 6.0 vs 2.0-2.35 %,
    companion 17.6 vs 13.3-14.3 %;
  - it removes the underrun excess: 9.0 vs 13.0 mean (`=frame`'s five
    sessions across E3-S5 / S5B), and no flagged run above its controls;
  - socket W is about the same (0.5-3.7 W below the controls; `=frame`
    2-2.7 W).

## 4. What the user would be adopting, and the revert

- **Adoption:** one drop-in line,
  `Environment=PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`.
  - The natural form is a separate drop-in, as E3-S6A did, e.g.
    `audio-pacing.conf`. The state check's `ADOPTED` would then gain
    that name.
  - **Gain:** the sender goes from ~13 % to ~6 % of a core, the
    companion from ~24.5 % to ~17.6 %, ~0.5-3.7 W while streaming. No
    measured cost in underruns, fps, spikes or loss shares.
  - Against `=frame`: ~4 points of a core less saving, without its
    underrun excess.
- **Revert:** delete the line (or the file), `systemctl --user
  daemon-reload`, restart the unit. The code may stay; absent = today's
  wait.

## 5. State at the end; files

- **Final state** (`runs/final_state.json`, 07:40:16Z):
  - manager none;
  - environ exactly the adopted two lines (live, the guide index);
  - the e3 drop-in absent;
  - no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- The trace hook was used only in the probe.
- No `nft`, no real `sudo`, the Opal untouched.
- Files (`e3_s5c_2026-10-07/`):
  - `precondition.json`, `e3_s5c_frame_spin.diff`;
  - `probe.md`, `e3_s5c_probe.py`, `probe_console.log`,
    `trace_{noflag,frame,frame_spin}.txt`, `probe_*_run.json`,
    `probe_stats.json`;
  - the pre-registration and its `.sha256`;
  - `runs/` (5 runs, `manifest.sha256`, `--check` OK in `runs/check.txt`),
    `runs_console.log`;
  - `e3_s5c_analysis.py`, `e3_s5c_table.md/.json`,
    `e3_s5c_verdict.json`, `loss_per_minute.txt`, `redact_check.txt`.
- Git status: `logs/e3_s5c_git_status.txt`.
